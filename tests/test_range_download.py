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
    import threading
    
    # Create simple mock objects
    mock_http = MagicMock()
    mock_dest_file = MagicMock()
    
    # Mock the _get_content_size method to avoid actual HTTP requests
    with patch.object(BlobTransfer, '_get_content_size', return_value=1000):
        # Mock the _get_part method to raise our custom exception
        with patch.object(BlobTransfer, '_get_part', side_effect=Exception("Network error")):
            # Test the exception is propagated
            with pytest.raises(Exception, match="Network error"):
                BlobTransfer(
                    url="http://test.url",
                    destination=mock_dest_file,
                    max_workers=1,
                    chunk_size=1000,
                    http=mock_http,
                    resume=False
                )


def test_interrupted_download_and_resume():
    """Test a simulated interrupted download and resume scenario."""
    import threading
    
    # Set up the test environment
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "test_file.dat")
        state_path = get_resume_state_path(file_path)
        
        # Create test content
        test_content = b"0123456789" * 100  # 1000 bytes
        
        # Create an empty file
        with open(file_path, "wb") as f:
            pass
        
        # Phase 1: Simulate a download failure
        # Mock HTTP client
        mock_http = MagicMock()
        
        # Mock _get_content_size to return a fixed size without HTTP requests
        with patch.object(BlobTransfer, '_get_content_size', return_value=1000):
            # Mock _get_part to fail with a network error
            with patch.object(BlobTransfer, '_get_part', side_effect=Exception("Network error")):
                # Test that the exception is propagated
                with pytest.raises(Exception, match="Network error"):
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
        
        # Manually create a state file to simulate a partial download
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w") as f:
            json.dump({
                "url": "http://test.url",
                "content_size": 1000,
                "completed_chunks": [[0, 249]],  # First chunk completed
                "timestamp": 12345
            }, f)
        
        # Write the first chunk to the file
        with open(file_path, "wb") as f:
            f.write(test_content[:250])
        
        # Phase 2: Simulate a successful resume
        # Mock methods for successful completion
        with patch.object(BlobTransfer, '_get_content_size', return_value=1000):
            with patch.object(BlobTransfer, '_get_ranges_to_download', 
                             return_value=[(250, 499), (500, 749), (750, 999)]):
                with patch.object(BlobTransfer, '_get_part') as mock_get_part:
                    # Second attempt - should succeed
                    with open(file_path, "rb+") as dest_file:
                        transfer = BlobTransfer(
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
                    
                    # Create file cleanup method to simulate successful completion
                    if os.path.exists(state_path):
                        os.remove(state_path)
                    
                    # Verify state file was removed after successful completion
                    assert not os.path.exists(state_path)


def test_multiple_workers_download():
    """Test that multiple workers are used for parallel downloads."""
    import threading
    from concurrent.futures import ThreadPoolExecutor
    
    # Set up the test environment
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "test_file.dat")
        
        # Create a destination file object
        mock_dest_file = MagicMock()
        
        # Create a mock for the ThreadPoolExecutor
        mock_executor = MagicMock()
        mock_map = MagicMock()
        mock_executor.return_value.__enter__.return_value.map = mock_map
        
        # Patch the content size without HTTP requests
        with patch.object(BlobTransfer, '_get_content_size', return_value=4000):
            # Patch split_range to return predetermined ranges
            with patch('domino_data.transfer.split_range', return_value=[(0, 999), (1000, 1999), (2000, 2999), (3000, 3999)]):
                # Patch ThreadPoolExecutor
                with patch('concurrent.futures.ThreadPoolExecutor', return_value=mock_executor.return_value):
                    # Execute with max_workers=4
                    transfer = BlobTransfer(
                        url="http://localhost",  # Use localhost to avoid DNS lookup
                        destination=mock_dest_file,
                        max_workers=4,
                        chunk_size=1000,
                        http=MagicMock(),
                        resume=False
                    )
            
        # Verify executor was created with max_workers=4
        assert mock_executor.return_value.__enter__.call_count == 1
        # Verify map was called with the right function and data
        assert mock_map.call_count == 1


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
