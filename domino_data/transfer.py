from typing import BinaryIO, Generator, Optional, Tuple

import io
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor

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

        with ThreadPoolExecutor(max_workers) as pool:
            pool.map(self._get_part, split_range(0, self.content_size, chunk_size))

    def _get_content_size(self) -> int:
        headers = self.headers.copy()
        headers["Range"] = "bytes=0-0"
        res = self.http.request("GET", self.url, headers=headers)
        return int(res.headers["Content-Range"].partition("/")[-1])

    def _get_part(self, block: Tuple[int, int]) -> None:
        """Download specific block of data from blob and writes it into destination.

        Args:
            block: block of bytes to download
        """
        headers = self.headers.copy()
        headers["Range"] = f"bytes={block[0]}-{block[1]}"
        res = self.http.request("GET", self.url, headers=headers, preload_content=False)

        buffer = io.BytesIO()
        shutil.copyfileobj(res, buffer)

        buffer.seek(0)
        with self._lock:
            self.destination.seek(block[0])
            shutil.copyfileobj(buffer, self.destination)  # type: ignore

        buffer.close()
        res.release_connection()
