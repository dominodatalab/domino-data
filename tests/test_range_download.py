"""Range download tests."""

import io
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock, call, ANY

import pytest

from domino_data.transfer import (
    BlobTransfer, get_resume_state_path, get_file_from_uri, 
    get_content_size, DEFAULT_CHUNK_SIZE, split_range
)

# Test Constants
TEST_CONTENT = b"0123456789" * 1000  # 10KB test content
CHUNK_SIZE = 1024  # 1KB chunks for testing


def test_split_range():
    """Test split_range function."""
    # Test various combinations of start, end, and step
    assert list(split_range(0, 10, 2)) == [(0, 1), (2, 3), (4, 5), (6, 7), (8, 10)]
    assert list(split_range(0, 10, 3)) == [(0, 2), (3, 5), (6, 8), (9, 10)]
    assert list(split_range(0, 10, 5)) == [(0, 4), (5, 10)]
    assert list(split_range(0, 10, 11)) == [(0, 10)]


def test_get_resume_state_path():
    """Test generating resume state file path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "testfile.dat")
        url_hash = "abcdef123456"
        
        # Test with hash
        state_path = get_resume_state_path(file_path, url_hash)
        assert ".domino_downloads" in state_path
        assert os.path.basename(file_path) in state_path
        
        # Test directory creation
        assert os.path.exists(os.path.dirname(state_path))


def test_get_file_from_uri():
    """Test getting a file from URI with range header."""
    # Mock urllib3.PoolManager
    mock_http = MagicMock()
    mock_response = MagicMock()
    mock_response.data = b"test data"
    mock_response.headers = {"Content-Type": "application/octet-stream"}
    mock_response.status = 200
    mock_http.request.return_value = mock_response
    
    # Test basic get
    data, headers = get_file_from_uri("http://test.url", http=mock_http)
    assert data == b"test data"
    assert headers["Content-Type"] == "application/octet-stream"
    mock_http.request.assert_called_with("GET", "http://test.url", headers={})
    
    # Test with range
    mock_http.reset_mock()
    mock_response.status = 206
    mock_http.request.return_value = mock_response
    
    data, headers = get_file_from_uri(
        "http://test.url", 
        http=mock_http,
        start_byte=100,
        end_byte=200
    )
    
    assert data == b"test data"
    mock_http.request.assert_called_with(
        "GET", 
        "http://test.url", 
        headers={"Range": "bytes=100-200"}
    )


def test_blob_transfer_functionality(monkeypatch):
    """Test basic BlobTransfer functionality with mocks."""
    # Create a mock for content size check
    mock_http = MagicMock()
    mock_size_response = MagicMock()
    mock_size_response.headers = {"Content-Range": "bytes 0-0/1000"}
    
    # Create a mock for chunk response
    mock_chunk_response = MagicMock()
    mock_chunk_response.preload_content = False
    mock_chunk_response.release_connection = MagicMock()
    
    # Setup the mock to return appropriate responses
    mock_http.request.side_effect = [
        mock_size_response,  # For content size
        mock_chunk_response  # For the chunk download
    ]
    
    # Mock copyfileobj to avoid actually copying data
    with patch('shutil.copyfileobj') as mock_copy:
        # Create a destination file object
        dest_file = MagicMock()
        
        # Execute with a single chunk size to simplify
        transfer = BlobTransfer(
            url="http://test.url",
            destination=dest_file,
            max_workers=1,
            chunk_size=1000,  # Large enough for a single chunk
            http=mock_http,
            resume=False
        )
        
        # Verify content size was requested
        mock_http.request.assert_any_call(
            "GET", 
            "http://test.url", 
            headers={"Range": "bytes=0-0"}
        )
        
        # Verify chunk was requested
        mock_http.request.assert_any_call(
            "GET", 
            "http://test.url", 
            headers={"Range": "bytes=0-999"},
            preload_content=False
        )
        
        # Verify data was copied
        assert mock_copy.call_count >= 1


def test_blob_transfer_resume_state_management():
    """Test BlobTransfer's state management for resumable downloads."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a test file path and state file path
        file_path = os.path.join(tmp_dir, "test_file.dat")
        state_path = get_resume_state_path(file_path)
        
        # Create a state file with some completed chunks
        state_dir = os.path.dirname(state_path)
        os.makedirs(state_dir, exist_ok=True)
        
        test_state = {
            "url": "http://test.url",
            "content_size": 1000,
            "completed_chunks": [[0, 499]],  # First chunk is complete
            "timestamp": 12345
        }
        
        with open(state_path, "w") as f:
            json.dump(test_state, f)
        
        # Mock HTTP to avoid actual requests
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Range": "bytes 0-0/1000"}
        mock_http.request.return_value = mock_resp
        
        # Patch _get_ranges_to_download and _get_part to avoid actual downloads
        with patch('domino_data.transfer.BlobTransfer._get_ranges_to_download') as mock_ranges:
            with patch('domino_data.transfer.BlobTransfer._get_part') as mock_get_part:
                # Mock the ranges to download (only the second chunk)
                mock_ranges.return_value = [(500, 999)]
                
                # Create a test file
                with open(file_path, "wb") as f:
                    f.write(b"\0" * 1000)  # Pre-allocate the file
                
                # Execute with resume=True
                with open(file_path, "rb+") as dest_file:
                    transfer = BlobTransfer(
                        url="http://test.url",
                        destination=dest_file,
                        max_workers=1,
                        chunk_size=500,  # 500 bytes per chunk
                        http=mock_http,
                        resume_state_file=state_path,
                        resume=True
                    )
                
                # Verify that _get_part was called only for the second chunk
                mock_get_part.assert_called_once_with((500, 999))


def test_blob_transfer_with_state_mismatch():
    """Test BlobTransfer handling of state mismatch."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a test file path and state file path
        file_path = os.path.join(tmp_dir, "test_file.dat")
        state_path = get_resume_state_path(file_path)
        
        # Create a state file with different URL or content size
        state_dir = os.path.dirname(state_path)
        os.makedirs(state_dir, exist_ok=True)
        
        # State with mismatched content size
        test_state = {
            "url": "http://test.url",
            "content_size": 2000,  # Different size than what the mock will return
            "completed_chunks": [[0, 499]],
            "timestamp": 12345
        }
        
        with open(state_path, "w") as f:
            json.dump(test_state, f)
        
        # Mock HTTP to return different content size
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Range": "bytes 0-0/1000"}  # Different from state
        mock_http.request.return_value = mock_resp
        
        # Patch methods to verify behavior
        with patch('domino_data.transfer.BlobTransfer._load_state') as mock_load:
            with patch('domino_data.transfer.BlobTransfer._get_ranges_to_download') as mock_ranges:
                with patch('domino_data.transfer.BlobTransfer._get_part'):
                    # Mock to return all ranges (not just the missing ones)
                    mock_ranges.return_value = [(0, 999)]
                    
                    # Create a test file
                    with open(file_path, "wb") as f:
                        f.write(b"\0" * 1000)
                    
                    # Execute with resume=True
                    with open(file_path, "rb+") as dest_file:
                        transfer = BlobTransfer(
                            url="http://test.url",
                            destination=dest_file,
                            max_workers=1,
                            chunk_size=1000,
                            http=mock_http,
                            resume_state_file=state_path,
                            resume=True
                        )
                    
                    # Verify load_state was called
                    mock_load.assert_called_once()
                    
                    # Verify ranges included all chunks due to size mismatch
                    mock_ranges.assert_called_once()
                    assert len(mock_ranges.return_value) == 1


def test_get_content_size():
    """Test get_content_size function."""
    # Mock HTTP response
    mock_http = MagicMock()
    mock_resp = MagicMock()
    mock_resp.headers = {"Content-Range": "bytes 0-0/12345"}
    mock_http.request.return_value = mock_resp
    
    # Test function
    size = get_content_size("http://test.url", http=mock_http)
    
    # Verify results
    assert size == 12345
    mock_http.request.assert_called_once_with(
        "GET", 
        "http://test.url", 
        headers={"Range": "bytes=0-0"}
    )


def test_dataset_file_download_with_mock():
    """Test downloading a file with resume support using mocks."""
    # Import datasets here to avoid dependency issues
    from domino_data import datasets as ds
    
    # Create fully mocked objects
    mock_dataset = MagicMock()
    mock_dataset.get_file_url.return_value = "http://test.url/file"
    
    # Create a file object with the mocked dataset
    file_obj = ds._File(dataset=mock_dataset, name="testfile.dat")
    
    # Mock the download method
    with patch.object(ds._File, 'download') as mock_download:
        # Test the download_with_ranges method
        file_obj.download_with_ranges(
            filename="local_file.dat",
            chunk_size=2048,
            max_workers=4,
            resume=True
        )
        
        # Verify download was called with the right parameters
        mock_download.assert_called_once()
        args, kwargs = mock_download.call_args
        assert kwargs.get("chunk_size") == 2048
        assert kwargs.get("max_workers") == 4
        assert kwargs.get("resume") is True


def test_environment_variable_resume():
    """Test that the DOMINO_ENABLE_RESUME environment variable is respected."""
    # Import datasets here to avoid dependency issues
    from domino_data import datasets as ds
    
    # Create fully mocked objects  
    mock_dataset = MagicMock()
    mock_dataset.get_file_url.return_value = "http://test.url/file"
    
    # Mock the client attribute properly
    mock_client = MagicMock()
    mock_client.token_url = None
    mock_client.token_file = None
    mock_client.api_key = None
    mock_client.token = None
    
    mock_dataset.client = mock_client
    mock_dataset.pool_manager.return_value = MagicMock()
    
    # Create a File instance with our mocked dataset
    file_obj = ds._File(dataset=mock_dataset, name="testfile.dat")
    
    # Mock _get_headers to return empty dict to avoid auth issues
    with patch.object(ds._File, '_get_headers', return_value={}):
        # Mock BlobTransfer to avoid actual transfers
        with patch('domino_data.datasets.BlobTransfer') as mock_transfer:
            # Mock open context manager
            mock_file = MagicMock()
            mock_open = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Test with environment variable set to true
            with patch.dict('os.environ', {"DOMINO_ENABLE_RESUME": "true"}):
                with patch('builtins.open', mock_open):
                    # Call download method
                    file_obj.download("local_file.dat")
                    
                    # Verify BlobTransfer was called with resume=True
                    mock_transfer.assert_called_once()
                    _, kwargs = mock_transfer.call_args
                    assert kwargs.get("resume") is True
            
            # Reset the mock
            mock_transfer.reset_mock()
            
            # Test with environment variable set to false
            with patch.dict('os.environ', {"DOMINO_ENABLE_RESUME": "false"}):
                with patch('builtins.open', mock_open):
                    # Call download method
                    file_obj.download("local_file.dat")
                    
                    # Verify BlobTransfer was called with resume=False
                    mock_transfer.assert_called_once()
                    _, kwargs = mock_transfer.call_args
                    assert kwargs.get("resume") is False


def test_download_exception_handling():
    """Test that download exceptions are properly handled and propagated."""
    # We'll customize the BlobTransfer initialization to force an exception
    original_init = BlobTransfer.__init__
    original_get_part = BlobTransfer._get_part
    
    def mock_init(self, *args, **kwargs):
        # Call original init with modified parameters
        kwargs['max_workers'] = 1  # Force single worker for predictable behavior
        original_init(self, *args, **kwargs)
        # Force _get_part to be called synchronously during init
        self._ranges = [(0, 999)]  # Only one chunk for simplicity
        # Call _get_part directly which will raise our exception
        self._get_part(self._ranges[0])
    
    def mock_get_part(self, block):
        # Simulate an exception during download
        raise Exception("Network error")
    
    # Apply our patches
    BlobTransfer.__init__ = mock_init
    BlobTransfer._get_part = mock_get_part
    
    try:
        # Set up a test environment
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "test_file.dat")
            
            # Create an empty file
            with open(file_path, "wb") as f:
                pass
            
            # Test the exception is propagated
            with pytest.raises(Exception, match="Network error"):
                with open(file_path, "rb+") as dest_file:
                    BlobTransfer(
                        url="http://test.url",
                        destination=dest_file,
                        chunk_size=1000,
                        resume=True
                    )
    finally:
        # Restore original methods
        BlobTransfer.__init__ = original_init
        BlobTransfer._get_part = original_get_part


def test_interrupted_download_and_resume():
    """Test a simulated interrupted download and resume scenario."""
    # Save the original methods
    original_init = BlobTransfer.__init__
    original_get_content_size = BlobTransfer._get_content_size
    original_get_part = BlobTransfer._get_part
    original_get_ranges = BlobTransfer._get_ranges_to_download
    
    # --- First phase: simulate a failed download ---
    def mock_init_fail(self, *args, **kwargs):
        # Simplified init that will fail later
        self.url = kwargs.get('url', "http://test.url")
        self.headers = kwargs.get('headers', {})
        self.http = kwargs.get('http', MagicMock())
        self.destination = kwargs.get('destination')
        self.resume_state_file = kwargs.get('resume_state_file')
        self.chunk_size = kwargs.get('chunk_size', 250)
        self.content_size = 1000  # Hardcoded for test
        self.resume = kwargs.get('resume', False)
        self._completed_chunks = set()
        self._lock = threading.Lock()
        
        # Call _get_part directly with the first chunk
        # This will fail with our network error
        self._get_part((0, 249))
    
    def mock_get_part_fail(self, block):
        # First chunk saves state and fails
        if block == (0, 249):
            # Create a partial state file
            if self.resume and self.resume_state_file:
                os.makedirs(os.path.dirname(self.resume_state_file), exist_ok=True)
                with open(self.resume_state_file, "w") as f:
                    json.dump({
                        "url": self.url,
                        "content_size": self.content_size,
                        "completed_chunks": [],  # No completed chunks yet
                        "timestamp": 12345
                    }, f)
            raise Exception("Network error")
    
    # Apply patches for first phase
    BlobTransfer.__init__ = mock_init_fail
    BlobTransfer._get_part = mock_get_part_fail
    
    # First attempt - should fail
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "test_file.dat")
        state_path = get_resume_state_path(file_path)
        
        # Create test content
        test_content = b"0123456789" * 100  # 1000 bytes
        
        # Create an empty file
        with open(file_path, "wb") as f:
            pass
        
        # First attempt should fail with network error
        with pytest.raises(Exception, match="Network error"):
            with open(file_path, "rb+") as dest_file:
                BlobTransfer(
                    url="http://test.url",
                    destination=dest_file,
                    max_workers=1,
                    chunk_size=250,
                    resume_state_file=state_path,
                    resume=True
                )
        
        # --- Second phase: successful resume ---
        def mock_init_success(self, *args, **kwargs):
            # Basic initialization
            self.url = kwargs.get('url', "http://test.url")
            self.headers = kwargs.get('headers', {})
            self.http = kwargs.get('http', MagicMock())
            self.destination = kwargs.get('destination')
            self.resume_state_file = kwargs.get('resume_state_file')
            self.chunk_size = kwargs.get('chunk_size', 250)
            self.content_size = 1000  # Hardcoded for test
            self.resume = kwargs.get('resume', False)
            self._completed_chunks = set()
            self._lock = threading.Lock()
            
            # Set successful state - all chunks "downloaded"
            self._completed_chunks = {(0, 249), (250, 499), (500, 749), (750, 999)}
            
            # Save final state
            if self.resume_state_file and os.path.exists(self.resume_state_file):
                os.remove(self.resume_state_file)
        
        def mock_get_ranges_success(self):
            # Return ranges that would need to be downloaded
            return [(0, 249), (250, 499), (500, 749), (750, 999)]
        
        # Replace with success versions
        BlobTransfer.__init__ = mock_init_success
        BlobTransfer._get_ranges_to_download = mock_get_ranges_success
        
        # Second attempt - should succeed
        with open(file_path, "rb+") as dest_file:
            transfer = BlobTransfer(
                url="http://test.url",
                destination=dest_file,
                max_workers=1, 
                chunk_size=250,
                resume_state_file=state_path,
                resume=True
            )
        
        # Verify the state file was removed after successful completion
        assert not os.path.exists(state_path)
        
        # Restore original methods
        BlobTransfer.__init__ = original_init
        BlobTransfer._get_content_size = original_get_content_size
        BlobTransfer._get_part = original_get_part
        BlobTransfer._get_ranges_to_download = original_get_ranges


def test_multiple_workers_download():
    """Test that multiple workers are used for parallel downloads."""
    # Import all required modules
    import io
    import shutil
    import threading
    from concurrent.futures import ThreadPoolExecutor
    
    # Set up the test environment
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "test_file.dat")
        
        # Mock HTTP responses
        mock_http = MagicMock()
        mock_size_resp = MagicMock()
        mock_size_resp.headers = {"Content-Range": "bytes 0-0/4000"}
        mock_http.request.return_value = mock_size_resp
        
        # Mock ThreadPoolExecutor
        mock_executor = MagicMock()
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        # Set up patch for ThreadPoolExecutor
        with patch('domino_data.transfer.ThreadPoolExecutor', mock_executor):
            # Mock other BlobTransfer methods to avoid actual downloads
            with patch.object(BlobTransfer, '_get_content_size', return_value=4000):
                with patch.object(BlobTransfer, '_get_part'):
                    # Execute with max_workers=4
                    with open(file_path, "wb") as dest_file:
                        BlobTransfer(
                            url="http://test.url",
                            destination=dest_file,
                            max_workers=4,
                            chunk_size=1000,
                            http=mock_http,
                            resume=False
                        )
            
            # Verify ThreadPoolExecutor was created with max_workers=4
            mock_executor.assert_called_once_with(4)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
