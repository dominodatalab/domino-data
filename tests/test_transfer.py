import io
from unittest.mock import MagicMock

import pytest
import urllib3

from domino_data import transfer


@pytest.mark.parametrize(
    "start,end,step,expected",
    [
        (0, 10, 2, [(0, 1), (2, 3), (4, 5), (6, 7), (8, 10)]),
        (0, 10, 3, [(0, 2), (3, 5), (6, 8), (9, 10)]),
        (0, 10, 5, [(0, 4), (5, 10)]),
        (0, 10, 6, [(0, 5), (6, 10)]),
        (0, 10, 11, [(0, 10)]),
    ],
)
def test_split_range(start, end, step, expected):
    assert expected == list(transfer.split_range(start, end, step))


def test_blob_transfer():
    # Mock the HTTP client to avoid real network calls
    mock_http = MagicMock(spec=urllib3.PoolManager)

    def mock_request(method, url, headers=None, preload_content=True):
        # Check if this is the initial size check request
        if headers and headers.get("Range") == "bytes=0-0":
            mock_response = MagicMock()
            mock_response.headers = {"Content-Range": "bytes 0-0/21821"}
            return mock_response

        # For actual data chunk requests, return a file-like object
        # that shutil.copyfileobj can read from
        if headers and "Range" in headers:
            # Parse the range to determine how much data to return
            range_header = headers["Range"].replace("bytes=", "")
            start, end = map(int, range_header.split("-"))
            size = end - start + 1
            # Create a BytesIO object that acts as a file-like response
            data = io.BytesIO(b"x" * size)
            # Mock the response object with the necessary methods
            mock_response = MagicMock()
            mock_response.read = data.read
            mock_response.__iter__ = lambda self: iter(data)
            mock_response.release_connection = MagicMock()
            return mock_response

        # Fallback
        mock_response = MagicMock()
        mock_response.read = MagicMock(return_value=b"")
        mock_response.release_connection = MagicMock()
        return mock_response

    mock_http.request = mock_request

    with io.BytesIO() as dest:
        transfer.BlobTransfer(
            "https://murat-secure-test.s3.us-west-2.amazonaws.com/9095835.png",
            dest,
            chunk_size=1024,
            http=mock_http,
        )

        assert 21821 == len(dest.getvalue())
