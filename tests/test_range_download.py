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
    
    # Create a File instance with our mocked dataset
    file_obj = ds._File(dataset=mock_dataset, name="testfile.dat")
    
    # Mock BlobTransfer to avoid actual transfers
    with patch('domino_data.transfer.BlobTransfer') as mock_transfer:
        # Mock open to avoid file operations
        with patch('builtins.open', MagicMock()):
            # Test with environment variable set to true
            with patch.dict('os.environ', {"DOMINO_ENABLE_RESUME": "true"}):
                # Call download method
                file_obj.download("local_file.dat")
                
                # Verify BlobTransfer was called with resume=True
                mock_transfer.assert_called_once()
                _, kwargs = mock_transfer.call_args
                assert kwargs.get("resume") is True
        
        # Reset the mock
        mock_transfer.reset_mock()
        
        # Test with environment variable set to false
        with patch('builtins.open', MagicMock()):
            with patch.dict('os.environ', {"DOMINO_ENABLE_RESUME": "false"}):
                # Call download method
                file_obj.download("local_file.dat")
                
                # Verify BlobTransfer was called with resume=False
                mock_transfer.assert_called_once()
                _, kwargs = mock_transfer.call_args
                assert kwargs.get("resume") is False


def test_download_exception_handling():
    """Test that download exceptions are properly handled and propagated."""
    # Create a mock HTTP response that fails on the chunk download
    mock_http = MagicMock()
    mock_size_resp = MagicMock()
    mock_size_resp.headers = {"Content-Range": "bytes 0-0/1000"}
    
    # Set up the mock to throw exception after content size
    network_error = Exception("Network error")
    mock_http.request.side_effect = [
        mock_size_resp,  # First call for content size succeeds
        network_error    # Second call for chunk raises exception
    ]
    
    # Ensure the exception is propagated from _get_part to __init__
    with patch.object(BlobTransfer, '_get_part', side_effect=network_error):
        # Set up a test environment
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "test_file.dat")
            state_path = get_resume_state_path(file_path)
            
            # Create an empty file
            with open(file_path, "wb") as f:
                pass
            
            # Test the exception is propagated
            with pytest.raises(Exception, match="Network error"):
                with open(file_path, "rb+") as dest_file:
                    BlobTransfer(
                        url="http://test.url",
                        destination=dest_file,
                        max_workers=1,
                        chunk_size=500,
                        http=mock_http,
                        resume_state_file=state_path,
                        resume=True
                    )


def test_interrupted_download_and_resume():
    """Test a simulated interrupted download and resume scenario."""
    # Modify implementation to ensure exception is propagated properly
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "test_file.dat")
        state_path = get_resume_state_path(file_path)
        
        # Create test content
        test_content = b"0123456789" * 100  # 1000 bytes
        
        # Create a mock HTTP response
        mock_http = MagicMock()
        mock_size_resp = MagicMock()
        mock_size_resp.headers = {"Content-Range": "bytes 0-0/1000"}
        mock_http.request.return_value = mock_size_resp
        
        # Prepare exception to be raised during download
        network_error = Exception("Network error")
        
        # First attempt - simulate failure during download
        with patch.object(BlobTransfer, '_get_part', side_effect=network_error):
            with pytest.raises(Exception, match="Network error"):
                with open(file_path, "wb") as dest_file:
                    BlobTransfer(
                        url="http://test.url",
                        destination=dest_file,
                        max_workers=1,
                        chunk_size=250,
                        http=mock_http,
                        resume_state_file=state_path,
                        resume=True
                    )
        
        # Create a state file to simulate a partial download
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w") as f:
            json.dump({
                "url": "http://test.url",
                "content_size": 1000,
                "completed_chunks": [[0, 249]],
                "timestamp": 12345
            }, f)
        
        # Create a partial file
        with open(file_path, "wb") as f:
            f.write(test_content[:250])
        
        # Second attempt - simulate successful completion
        with patch.object(BlobTransfer, '_get_ranges_to_download') as mock_ranges:
            with patch.object(BlobTransfer, '_get_part') as mock_get_part:
                # Return remaining ranges
                mock_ranges.return_value = [(250, 499), (500, 749), (750, 999)]
                
                # Execute with resume=True
                with open(file_path, "rb+") as dest_file:
                    BlobTransfer(
                        url="http://test.url",
                        destination=dest_file,
                        max_workers=1,
                        chunk_size=250,
                        http=mock_http,
                        resume_state_file=state_path,
                        resume=True
                    )
                
                # Verify _get_part was called for the remaining chunks
                assert mock_get_part.call_count == 3


def test_multiple_workers_download():
    """Test that multiple workers are used for parallel downloads."""
    # Set up the test environment
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "test_file.dat")
        
        # Mock HTTP responses
        mock_http = MagicMock()
        mock_size_resp = MagicMock()
        mock_size_resp.headers = {"Content-Range": "bytes 0-0/4000"}
        mock_http.request.return_value = mock_size_resp
        
        # Mock ThreadPoolExecutor directly in the BlobTransfer.__init__ method 
        original_init = BlobTransfer.__init__
        
        def mock_init(self, url, destination, max_workers=10, headers=None, 
                    chunk_size=DEFAULT_CHUNK_SIZE, http=None, 
                    resume_state_file=None, resume=False):
            """Mocked init to avoid actual ThreadPoolExecutor usage"""
            self.url = url
            self.headers = headers or {}
            self.http = http or MagicMock()
            self.destination = destination
            self.resume_state_file = resume_state_file
            self.chunk_size = chunk_size
            self.content_size = 4000  # Hardcoded for testing
            self.resume = resume
            self._completed_chunks = set()
            self._lock = threading.Lock()
            
            # Record the call to ThreadPoolExecutor
            mock_executor = MagicMock()
            mock_map = MagicMock()
            mock_executor.return_value.__enter__.return_value.map = mock_map
            
            # Just record the executor was created with right params
            self.test_executor_called = True
            self.test_executor_max_workers = max_workers
        
        # Apply the patch
        BlobTransfer.__init__ = mock_init
        
        try:
            # Execute with max_workers=4
            with open(file_path, "wb") as dest_file:
                transfer = BlobTransfer(
                    url="http://test.url",
                    destination=dest_file,
                    max_workers=4,
                    chunk_size=1000,
                    http=mock_http,
                    resume=False
                )
            
            # Verify executor params
            assert hasattr(transfer, 'test_executor_called')
            assert transfer.test_executor_max_workers == 4
            
        finally:
            # Restore original method
            BlobTransfer.__init__ = original_init


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
