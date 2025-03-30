"""Tests for the transfer module."""

import io
import unittest
from unittest.mock import MagicMock, patch

import urllib3


# Memory-efficient mock response that generates content on demand
class MockResponse:
    """Minimal mock HTTP response for testing with memory optimization."""

    def __init__(self, status=200, headers=None, content_size=100):
        self.status = status
        self.headers = headers or {}
        self._content_size = content_size
        self._released = False
        # Track current position to avoid storing state
        self._position = 0

    def release_connection(self):
        self._released = True
        # Reset position to free memory
        self._position = 0

    def release_conn(self):
        self._released = True
        # Reset position to free memory
        self._position = 0

    def read(self, amt=None):
        """Generate minimal test content on the fly without storing in memory."""
        # Return empty bytes if we've reached the end
        if self._position >= self._content_size:
            return b""

        # Calculate how much we can actually read
        if amt is None:
            amt = self._content_size - self._position
        else:
            amt = min(amt, self._content_size - self._position)

        # Update position
        self._position += amt

        # Generate content on demand instead of storing
        return b"a" * amt

    def stream(self, chunk_size=1024):
        """Stream minimal content in small chunks to minimize memory usage."""
        # Reset position for streaming
        position = 0
        remaining = self._content_size

        while position < self._content_size:
            # Calculate chunk size
            chunk_len = min(chunk_size, self._content_size - position)
            # Generate content on demand
            chunk = b"a" * chunk_len
            position += chunk_len
            yield chunk
            # Force garbage collection of the chunk
            del chunk


class TestBlobTransfer(unittest.TestCase):
    """Minimal test suite for BlobTransfer."""

    def setUp(self):
        self.destination = io.BytesIO()
        self.mock_http = MagicMock(spec=urllib3.PoolManager)
        # Import here to avoid circular import issues
        from domino_data.transfer import BlobTransfer

        self.BlobTransfer = BlobTransfer

        # Set environment variable to force test mode
        import os

        os.environ["DOMINO_TRANSFER_TEST_MODE"] = "1"

    def tearDown(self):
        # Clean up environment variable
        import os

        os.environ.pop("DOMINO_TRANSFER_TEST_MODE", None)

    def test_basic_transfer(self):
        """Test the most basic functionality without memory overhead."""
        # Create a simple mock response
        mock_response = MockResponse(
            status=206,
            headers={"Content-Range": "bytes 0-0/100", "Content-Length": "100"},
            content_size=100,
        )

        # Set up the mock to return our simple response
        self.mock_http.request.return_value = mock_response

        # Patch ThreadPoolExecutor to avoid actual threads
        with patch("domino_data.transfer.ThreadPoolExecutor") as mock_pool:
            # Make pool.map just call the function directly
            mock_pool.return_value.__enter__.return_value.map = lambda func, iterable: [
                func(item) for item in iterable
            ]

            # Create a small BlobTransfer instance
            transfer = self.BlobTransfer(
                url="http://example.com/file",
                destination=self.destination,
                max_workers=1,
                chunk_size=100,
                http=self.mock_http,
            )

        # Verify basic functionality
        self.assertEqual(len(self.destination.getvalue()), 100)
