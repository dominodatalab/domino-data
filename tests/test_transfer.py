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

    # Track request count to handle initial size check vs data chunks
    request_count = [0]

    def mock_request(method, url, headers=None, preload_content=True):
        request_count[0] += 1

        # First request is to get content size (Range: bytes=0-0)
        if request_count[0] == 1:
            mock_response = MagicMock()
            mock_response.headers = {"Content-Range": "bytes 0-0/21821"}
            return mock_response

        # Subsequent requests are for actual data chunks
        mock_response = MagicMock()
        if headers and "Range" in headers:
            # Parse the range to determine how much data to return
            range_header = headers["Range"].replace("bytes=", "")
            start, end = map(int, range_header.split("-"))
            size = end - start + 1
            mock_response.read = MagicMock(return_value=b"x" * size)
        else:
            mock_response.read = MagicMock(return_value=b"x" * 1024)

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
