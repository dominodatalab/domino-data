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


def _response(status, data=b"", headers=None):
    res = MagicMock()
    res.status = status
    res.data = data
    res.headers = headers or {}
    res.read = io.BytesIO(data).read
    return res


def _range_http(content, fail_from=None):
    """Fake urllib3 pool serving range requests over content; records each chunk response.

    Args:
        content: bytes served by the fake blob
        fail_from: start offset of a chunk that answers with HTTP 500 instead

    Returns:
        Tuple of the mock pool manager and the list of chunk responses it returned.
    """
    chunk_responses = []

    def request(method, url, headers=None, preload_content=True):
        if headers["Range"] == "bytes=0-0":
            return _response(206, headers={"Content-Range": f"bytes 0-0/{len(content)}"})
        start, end = map(int, headers["Range"].replace("bytes=", "").split("-"))
        if start == fail_from:
            res = _response(500, b"boom")
        else:
            res = _response(206, content[start : end + 1])
        chunk_responses.append(res)
        return res

    mock_http = MagicMock(spec=urllib3.PoolManager)
    mock_http.request = request
    return mock_http, chunk_responses


def test_blob_transfer():
    """Every chunk lands at its own offset and every chunk connection is released."""
    # Distinct bytes, so a chunk written at the wrong offset changes the result.
    content = bytes(i % 251 for i in range(21821))
    mock_http, chunk_responses = _range_http(content)

    with io.BytesIO() as dest:
        transfer.BlobTransfer(
            "http://blob/url", dest, chunk_size=1024, max_workers=4, http=mock_http
        )

        assert dest.getvalue() == content

    assert len(chunk_responses) == 22
    for res in chunk_responses:
        res.release_connection.assert_called_once()


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
    """A failed chunk propagates out of the worker pool and its connection is still released."""
    mock_http, chunk_responses = _range_http(b"x" * 4096, fail_from=2048)

    with io.BytesIO() as dest:
        with pytest.raises(httpx.HTTPStatusError) as err:
            transfer.BlobTransfer("http://blob/url", dest, chunk_size=1024, http=mock_http)

        assert err.value.response.status_code == 500

    for res in chunk_responses:
        res.release_connection.assert_called_once()


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


@pytest.mark.parametrize(
    "body,expected",
    [
        (b'{"message":"file x.csv does not exist","success":false}', "file x.csv does not exist"),
        (b"<Error><Code>NoSuchKey</Code></Error>", "<Error><Code>NoSuchKey</Code></Error>"),
        (b"", ""),
        (b"<html>" + b"x" * 500, "<html>" + "x" * 194 + "..."),
    ],
)
def test_error_detail(body, expected):
    """The server's reason is taken from a JSON message, else the start of the raw body."""
    assert transfer._error_detail(body) == expected  # pylint: disable=protected-access


def test_raise_for_status_without_body_keeps_httpx_message():
    """With no body to add, the plain httpx error is raised unchanged."""
    response = httpx.Response(500, request=httpx.Request("GET", "http://blob/url"))

    with pytest.raises(httpx.HTTPStatusError) as err:
        transfer.raise_for_status(response)

    assert "Server response" not in str(err.value)
