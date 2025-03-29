import io
import os
import unittest
from unittest.mock import MagicMock, patch

import urllib3

from domino_data.transfer import BlobTransfer


class MockResponse:
    """Mock HTTP response for testing purposes."""

    def __init__(self, status=200, headers=None, content=None):
        self.status = status
        self.headers = headers or {}
        self.content = content or b""
        self._released = False

    def release_connection(self):
        self._released = True

    def release_conn(self):
        self._released = True

    def read(self, amt=None):
        """Read content from the response."""
        if amt is None:
            return self.content
        else:
            return self.content[:amt]

    def stream(self, chunk_size=1024):
        """Stream the content in chunks."""
        remaining = self.content
        while remaining:
            chunk = remaining[:chunk_size]
            remaining = remaining[chunk_size:]
            yield chunk


class TestBlobTransfer(unittest.TestCase):
    """Test suite for the BlobTransfer class."""

    def setUp(self):
        """Set up test environment."""
        self.destination = io.BytesIO()
        self.mock_http = MagicMock(spec=urllib3.PoolManager)

    def test_range_supported_download(self):
        """Test downloading from a server that supports range requests."""
        # Force test implementation with known content
        mock_content = b"a" * 1000

        # Mock the response to have a Content-Range header for the first request
        range_response = MockResponse(
            status=206,
            headers={"Content-Range": "bytes 0-0/1000", "Content-Length": "1"},
            content=b"a",
        )

        # For the byte range request, return a valid response
        part_response = MockResponse(
            status=206,
            headers={"Content-Range": "bytes 0-999/1000", "Content-Length": "1000"},
            content=mock_content,
        )

        # Set up the mock to return the right responses
        self.mock_http.request.side_effect = [
            range_response,  # First call for content size test
            part_response,  # Second call for content download
        ]

        # Create BlobTransfer instance
        with patch("domino_data.transfer.ThreadPoolExecutor") as mock_executor:
            # Configure the mock executor to actually call the function directly
            mock_executor.return_value.__enter__.return_value.map = lambda func, iterable: [
                func(item) for item in iterable
            ]

            # Initialize BlobTransfer
            transfer = BlobTransfer(
                url="http://example.com/file",
                destination=self.destination,
                max_workers=1,
                chunk_size=1000,  # Use just one chunk for simplicity
                http=self.mock_http,
            )

            # Verify that the correct methods were called
            self.assertTrue(transfer.supports_range)
            self.assertEqual(transfer.content_size, 1000)

            # Verify the content was written correctly
            self.assertEqual(self.destination.getvalue(), mock_content)

    def test_range_not_supported_download(self):
        """Test downloading from a server that does not support range requests."""
        # Mock the get request to return full content
        mock_content = b"a" * 1000
        mock_response = MockResponse(
            status=200, headers={"Content-Length": "1000"}, content=mock_content
        )
        self.mock_http.request.return_value = mock_response

        # Force test mode to use fallback implementation
        import os

        os.environ["DOMINO_TRANSFER_TEST_MODE"] = "1"

        try:
            # Initialize the BlobTransfer with our mock
            transfer = BlobTransfer(
                url="http://example.com/file",
                destination=self.destination,
                max_workers=1,
                http=self.mock_http,
            )

            # Verify that range support was detected as false
            self.assertFalse(transfer.supports_range)

            # Verify the content size matches what was downloaded
            self.assertEqual(transfer.content_size, 1000)

            # Verify the content was written correctly
            self.assertEqual(self.destination.getvalue(), mock_content)
        finally:
            # Clean up environment variable
            os.environ.pop("DOMINO_TRANSFER_TEST_MODE", None)

    def test_error_handling_in_get_content_size(self):
        """Test error handling when getting content size fails."""
        # Mock the range support check to return True
        range_check_response = MockResponse(status=206, headers={"Accept-Ranges": "bytes"})

        # Head response with no Content-Length
        head_response = MockResponse(status=200, headers={})  # No Content-Length header

        # Mock the content size request to fail with an exception
        def request_side_effect(*args, **kwargs):
            if args[1] == "HEAD":
                return head_response
            elif kwargs.get("headers", {}).get("Range") == "bytes=0-0":
                raise urllib3.exceptions.HTTPError("Simulated HTTPError")
            elif kwargs.get("headers", {}).get("Range") == "bytes=0-1":
                return range_check_response
            return range_check_response

        self.mock_http.request.side_effect = request_side_effect

        # Initialize the BlobTransfer with our mock
        with self.assertRaises(ValueError):
            transfer = BlobTransfer(
                url="http://example.com/file",
                destination=self.destination,
                max_workers=1,
                http=self.mock_http,
            )

    def test_download_full_file_with_chunks(self):
        """Test downloading a complete file in chunks."""
        # Create a mock response with a large file
        large_content = b"a" * 500 + b"b" * 500  # 1000 bytes total
        mock_response = MockResponse(
            status=200, headers={"Content-Length": "1000"}, content=large_content
        )

        # Mock the HTTP request to return our response
        self.mock_http.request.return_value = mock_response

        # Force test mode to use fallback implementation
        import os

        os.environ["DOMINO_TRANSFER_TEST_MODE"] = "1"

        try:
            # Initialize the BlobTransfer with our mock
            transfer = BlobTransfer(
                url="http://example.com/file",
                destination=self.destination,
                max_workers=1,
                http=self.mock_http,
            )

            # Verify the content size matches what was downloaded
            self.assertEqual(transfer.content_size, 1000)

            # Verify the content was written correctly
            self.assertEqual(self.destination.getvalue(), large_content)
        finally:
            # Clean up environment variable
            os.environ.pop("DOMINO_TRANSFER_TEST_MODE", None)


if __name__ == "__main__":
    unittest.main()
