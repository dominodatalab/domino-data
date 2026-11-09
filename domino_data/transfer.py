from typing import BinaryIO, Generator, Iterator, Optional, Tuple, Union

import contextlib
import json
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import urllib3

MAX_WORKERS = 10
MB = 2**20  # 2^20 bytes - 1 Megabyte


def split_range(start: int, end: int, step: int) -> Generator[Tuple[int, int], None, None]:
    """Yield all steps from start to end as tuple of integers.

    All returned block are inclusive to ensure every integer is covered from start to end.

    Example:
        start: 0, end: 10, step: 3 -> (0, 2), (3, 5), (6, 8), (9, 10)
        start: 0, end: 10, step: 4 -> (0, 3), (4, 8), (9, 10)

    Args:
        start: start of the range to split
        end: end of the range to split
        step: step size

    Yields:
        tuple[int, int]
    """
    r = range(start, end, step)
    max_block = start

    for min_block, max_block in zip(r[:-1], r[1:]):
        yield (min_block, max_block - 1)

    yield (max_block, end)


MAX_ERROR_DETAIL = 200


def _error_detail(body: bytes) -> str:
    """Extract a short, readable reason from an error response body.

    Prefers the "message" field of a JSON body (what Domino returns), and falls back
    to the start of the raw text, e.g. an XML error from object storage.
    """
    text = body.decode("utf-8", errors="replace").strip()
    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = None
    if isinstance(parsed, dict):
        for key in ("message", "error", "detail"):
            if isinstance(parsed.get(key), str):
                text = parsed[key]
                break
    text = " ".join(text.split())
    return text if len(text) <= MAX_ERROR_DETAIL else text[:MAX_ERROR_DETAIL] + "..."


def raise_for_status(response: httpx.Response) -> None:
    """Raise httpx.HTTPStatusError for a non-2xx response, including the server's reason.

    httpx's own message only has the status and URL; the reason (for example
    "file x.csv does not exist") is in the body, so read it and append it.
    """
    if response.is_success:
        return
    response.read()
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as err:
        detail = _error_detail(response.content)
        if not detail:
            raise
        raise httpx.HTTPStatusError(
            f"{err}\nServer response: {detail}", request=err.request, response=err.response
        ) from None


def raise_for_urllib3_status(res: urllib3.BaseHTTPResponse, url: str) -> None:
    """Raise httpx.HTTPStatusError for a non-2xx urllib3 response.

    Uses the same exception type and message as the httpx-based download methods so
    callers can handle every download failure the same way.
    """
    if 200 <= res.status < 300:
        return
    raise_for_status(
        httpx.Response(res.status, content=res.data, request=httpx.Request("GET", url))
    )


@contextlib.contextmanager
def atomic_open(filename: Union[str, "os.PathLike[str]"]) -> Iterator[BinaryIO]:
    """Write to a temp file next to filename and move it into place only on success.

    A failed download leaves no partial or error-page file behind and does not
    overwrite an existing file at filename.
    """
    path = os.fspath(filename)
    tmp_path = f"{path}.{uuid.uuid4().hex}.part"
    try:
        with open(tmp_path, "xb") as file:
            yield file
        os.replace(tmp_path, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.remove(tmp_path)
        raise


class BlobTransfer:
    def __init__(
        self,
        url: str,
        destination: BinaryIO,
        max_workers: int = MAX_WORKERS,
        headers: Optional[dict] = None,
        # Recommended chunk size by Amazon S3
        # See https://docs.aws.amazon.com/whitepapers/latest/s3-optimizing-performance-best-practices/use-byte-range-fetches.html  # noqa
        chunk_size: int = 16 * MB,
        http: Optional[urllib3.PoolManager] = None,
    ):
        self.url = url
        self.headers = headers or {}
        self.http = http or urllib3.PoolManager()
        self.destination = destination
        self.content_size = self._get_content_size()

        self._lock = threading.Lock()

        # Use content_size - 1 because HTTP byte ranges are inclusive (0-indexed)
        # Consume the results so an exception raised in any worker propagates.
        with ThreadPoolExecutor(max_workers) as pool:
            list(pool.map(self._get_part, split_range(0, self.content_size - 1, chunk_size)))

    def _get_content_size(self) -> int:
        headers = self.headers.copy()
        headers["Range"] = "bytes=0-0"
        res = self.http.request("GET", self.url, headers=headers)
        raise_for_urllib3_status(res, self.url)
        return int(res.headers["Content-Range"].partition("/")[-1])

    def _get_part(self, block: Tuple[int, int]) -> None:
        """Download specific block of data from blob and writes it into destination.

        Args:
            block: block of bytes to download
        """
        headers = self.headers.copy()
        headers["Range"] = f"bytes={block[0]}-{block[1]}"
        res = self.http.request("GET", self.url, headers=headers, preload_content=False)
        try:
            raise_for_urllib3_status(res, self.url)
            data = res.read()
        finally:
            res.release_conn()

        with self._lock:
            self.destination.seek(block[0])
            self.destination.write(data)
