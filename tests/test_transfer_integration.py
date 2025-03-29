import io
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

from domino_data.transfer import BlobTransfer


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

    daemon_threads = True


class RangeSupportingHandler(BaseHTTPRequestHandler):
    """HTTP request handler that supports range requests."""

    # Test file content for download
    CONTENT = b"0123456789" * 100  # 1000 bytes

    def do_HEAD(self):
        """Handle HEAD requests."""
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.send_header("Content-Length", str(len(self.CONTENT)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests with range support."""
        # Check if this is a range request
        range_header = self.headers.get("Range")

        if range_header:
            # Parse the range header
            try:
                range_value = range_header.split("=")[1]
                start, end = map(int, range_value.split("-"))

                # Handle open-ended ranges (e.g., "bytes=500-")
                if end == 0 and start == 0:
                    # Special case for content size check
                    content_range = f"bytes 0-0/{len(self.CONTENT)}"
                    self.send_response(206)
                    self.send_header("Content-Range", content_range)
                    self.send_header("Content-Length", "1")
                    self.send_header("Content-type", "application/octet-stream")
                    self.end_headers()
                    self.wfile.write(self.CONTENT[0:1])
                    return

                if end == "":
                    end = len(self.CONTENT) - 1

                # Get the specified range of content
                content_range = self.CONTENT[start : end + 1]

                # Send partial content response
                self.send_response(206)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("Content-Range", f"bytes {start}-{end}/{len(self.CONTENT)}")
                self.send_header("Content-Length", str(len(content_range)))
                self.end_headers()
                self.wfile.write(content_range)
            except Exception as e:
                # If range parsing fails, return the entire content
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("Content-Length", str(len(self.CONTENT)))
                self.end_headers()
                self.wfile.write(self.CONTENT)
        else:
            # No range header, return the entire content
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Content-Length", str(len(self.CONTENT)))
            self.end_headers()
            self.wfile.write(self.CONTENT)

    def log_message(self, format, *args):
        """Suppress log messages from the test server."""
        pass


class NoRangeSupportHandler(BaseHTTPRequestHandler):
    """HTTP request handler that does NOT support range requests."""

    # Test file content for download
    CONTENT = b"0123456789" * 100  # 1000 bytes

    def do_HEAD(self):
        """Handle HEAD requests."""
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.send_header("Content-Length", str(len(self.CONTENT)))
        # Deliberately NOT adding Accept-Ranges header
        self.end_headers()

    def do_GET(self):
        """Handle GET requests without range support."""
        # Ignore any Range header and always return the full content
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.send_header("Content-Length", str(len(self.CONTENT)))
        self.end_headers()
        self.wfile.write(self.CONTENT)

    def log_message(self, format, *args):
        """Suppress log messages from the test server."""
        pass


class TestBlobTransferIntegration(unittest.TestCase):
    """Integration tests for the BlobTransfer class."""

    @classmethod
    def setUpClass(cls):
        """Start the test HTTP servers."""
        # Start a server that supports range requests
        cls.range_server = ThreadedHTTPServer(("localhost", 0), RangeSupportingHandler)
        cls.range_server_thread = threading.Thread(target=cls.range_server.serve_forever)
        cls.range_server_thread.daemon = True
        cls.range_server_thread.start()
        cls.range_server_port = cls.range_server.server_address[1]

        # Start a server that does NOT support range requests
        cls.no_range_server = ThreadedHTTPServer(("localhost", 0), NoRangeSupportHandler)
        cls.no_range_server_thread = threading.Thread(target=cls.no_range_server.serve_forever)
        cls.no_range_server_thread.daemon = True
        cls.no_range_server_thread.start()
        cls.no_range_server_port = cls.no_range_server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        """Stop the test HTTP servers."""
        cls.range_server.shutdown()
        cls.range_server.server_close()
        cls.range_server_thread.join(timeout=1)

        cls.no_range_server.shutdown()
        cls.no_range_server.server_close()
        cls.no_range_server_thread.join(timeout=1)

    def test_download_from_range_supporting_server(self):
        """Test downloading from a server that supports range requests."""
        url = f"http://localhost:{self.range_server_port}/test.bin"

        # Create a file-like object to receive the download
        destination = io.BytesIO()

        # Initialize the BlobTransfer
        transfer = BlobTransfer(
            url=url,
            destination=destination,
            max_workers=3,  # Use multiple workers to test parallel downloading
            chunk_size=100,  # Small chunk size to force multiple chunks
        )

        # Verify that range support was detected
        self.assertTrue(transfer.supports_range)

        # Verify the content size
        self.assertEqual(transfer.content_size, 1000)

        # Verify the downloaded content
        expected_content = RangeSupportingHandler.CONTENT
        self.assertEqual(destination.getvalue(), expected_content)

    def test_download_from_no_range_supporting_server(self):
        """Test downloading from a server that does NOT support range requests."""
        url = f"http://localhost:{self.no_range_server_port}/test.bin"

        # Create a file-like object to receive the download
        destination = io.BytesIO()
        
        # Force the test mode to OFF to ensure we test the actual implementation
        os.environ["DOMINO_TRANSFER_TEST_MODE"] = "0"
        
        try:
            # Initialize the BlobTransfer
            transfer = BlobTransfer(
                url=url,
                destination=destination,
                max_workers=3,  # Not used since range requests aren't supported
                chunk_size=100,  # Not used since range requests aren't supported
            )

            # Verify that range support was NOT detected
            self.assertFalse(transfer.supports_range)

            # Verify the content size
            self.assertEqual(transfer.content_size, 1000)

            # Verify the downloaded content
            expected_content = NoRangeSupportHandler.CONTENT
            self.assertEqual(destination.getvalue(), expected_content)
        finally:
            # Clean up
            os.environ.pop("DOMINO_TRANSFER_TEST_MODE", None)

    def test_download_to_file(self):
        """Test downloading to a real file on disk."""
        url = f"http://localhost:{self.range_server_port}/test.bin"

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Download to the file
            with open(temp_path, "wb") as destination:
                transfer = BlobTransfer(
                    url=url, destination=destination, max_workers=3, chunk_size=100
                )

            # Verify the content size
            self.assertEqual(transfer.content_size, 1000)

            # Verify the downloaded content
            with open(temp_path, "rb") as f:
                content = f.read()
                expected_content = RangeSupportingHandler.CONTENT
                self.assertEqual(content, expected_content)

        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
