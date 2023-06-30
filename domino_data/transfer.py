from typing import BinaryIO, Generator, Optional

import io
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor

import urllib3

MB = 2**20


def split_range(start: int, end: int, step: int) -> Generator[tuple[int, int], None, None]:
    """Yield all steps from start to end as tuple of integers.

    All returned block are inclusive to ensure every integer is covered from start to end.

    Example:
        start: 0, end: 10, step: 3 -> (0, 2), (3, 6), (7, 10)
        start: 0, end: 10, step: 4 -> (0, 3), (4, 8), (9, 10)

    Args:
        start: start of the range to split
        end: end of the range to split
        step: step size

    Returns: Iterator[tuple[int, int]]
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
        max_workers: int = 10,
        chunk_size: int = 16 * MB,
        http: Optional[urllib3.PoolManager] = None,
    ):
        self.url = url
        self.http = http or urllib3.PoolManager()
        self.destination = destination
        self.content_size = self._get_content_size()

        self._lock = threading.Lock()

        with ThreadPoolExecutor(max_workers) as pool:
            pool.map(self.get_part, split_range(0, self.content_size, chunk_size))

    def _get_content_size(self) -> int:
        res = self.http.request("GET", self.url, headers={"Range": "bytes=0-0"})
        return int(res.headers["Content-Range"].partition("/")[-1])

    def get_part(self, block: tuple[int, int]) -> None:
        """Download specific block of data from blob and writes it into destination.

        Args:
            block: block of bytes to download
        """
        headers = {"Range": f"bytes={block[0]}-{block[1]}"}
        res = self.http.request("GET", self.url, headers=headers, preload_content=False)

        buffer = io.BytesIO()
        # https://github.com/python/mypy/issues/15031
        shutil.copyfileobj(res, buffer)  # type: ignore[misc]
        res.release_connection()

        buffer.seek(0)
        with self._lock:
            self.destination.seek(block[0])
            shutil.copyfileobj(buffer, self.destination)
        buffer.close()
