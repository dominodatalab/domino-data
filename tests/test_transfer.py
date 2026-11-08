import io
from unittest.mock import MagicMock

import httpx
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
            mock_response.status = 206
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
            mock_response.status = 206
            mock_response.read = data.read
            mock_response.__iter__ = lambda self: iter(data)
            mock_response.release_connection = MagicMock()
            return mock_response

        # Fallback
        mock_response = MagicMock()
        mock_response.status = 200
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


def _response(status, data=b"", headers=None):
    res = MagicMock()
    res.status = status
    res.data = data
    res.headers = headers or {}
    res.read = io.BytesIO(data).read
    return res


def test_blob_transfer_raises_when_size_request_fails():
    """A failed size request raises HTTPStatusError instead of KeyError: 'Content-Range'."""
    mock_http = MagicMock(spec=urllib3.PoolManager)
    mock_http.request = MagicMock(return_value=_response(404, b'{"message":"nope"}'))

    with io.BytesIO() as dest:
        with pytest.raises(httpx.HTTPStatusError) as err:
            transfer.BlobTransfer("http://blob/url", dest, http=mock_http)

        assert err.value.response.status_code == 404
        assert dest.getvalue() == b""


def test_blob_transfer_raises_when_a_part_fails():
    """A failed range request propagates out of the worker pool instead of being swallowed."""
    mock_http = MagicMock(spec=urllib3.PoolManager)

    def mock_request(method, url, headers=None, preload_content=True):
        if headers["Range"] == "bytes=0-0":
            return _response(206, headers={"Content-Range": "bytes 0-0/4096"})
        if headers["Range"].startswith("bytes=2048-"):
            return _response(500, b"boom")
        start, end = map(int, headers["Range"].replace("bytes=", "").split("-"))
        return _response(206, b"x" * (end - start + 1))

    mock_http.request = mock_request

    with io.BytesIO() as dest:
        with pytest.raises(httpx.HTTPStatusError) as err:
            transfer.BlobTransfer("http://blob/url", dest, chunk_size=1024, http=mock_http)

        assert err.value.response.status_code == 500


def test_atomic_open_keeps_existing_file_on_failure(tmp_path):
    """atomic_open leaves an existing file untouched and removes its temp file on error."""
    target = tmp_path / "out.csv"
    target.write_bytes(b"original")

    with pytest.raises(RuntimeError):
        with transfer.atomic_open(target) as file:
            file.write(b"partial")
            raise RuntimeError("download failed")

    assert target.read_bytes() == b"original"
    assert [p.name for p in tmp_path.iterdir()] == ["out.csv"]
