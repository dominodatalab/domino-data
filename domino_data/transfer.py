from typing import BinaryIO, Generator, Optional, Tuple

import io
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor

import urllib3
from urllib3.exceptions import HTTPError

from .logging import logger

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

        # Check if the server supports range requests
        self.supports_range = self._check_range_support()

        if self.supports_range:
            # If range requests are supported, get the content size and use parallel download
            self.content_size = self._get_content_size()
            self._lock = threading.Lock()

            with ThreadPoolExecutor(max_workers) as pool:
                pool.map(self._get_part, split_range(0, self.content_size, chunk_size))
        else:
            # Fallback to standard download if range requests are not supported
            logger.info("Server does not support range requests, falling back to standard download")
            self.content_size = self._download_full_file()

    def _check_range_support(self) -> bool:
        """Check if the server supports range requests.

        Returns:
            bool: True if the server supports range requests, False otherwise
        """
        try:
            # First try with a HEAD request to check Accept-Ranges header
            head_response = self.http.request(
                "HEAD",
                self.url,
                headers=self.headers,
                retries=urllib3.util.Retry(total=3, backoff_factor=0.5),
            )

            # Check if the server explicitly supports ranges
            if head_response.headers.get("Accept-Ranges") == "bytes":
                return True

            # If no explicit Accept-Ranges header, try a small range request
            headers = self.headers.copy()
            headers["Range"] = "bytes=0-1"
            res = self.http.request(
                "GET",
                self.url,
                headers=headers,
                retries=urllib3.util.Retry(total=3, backoff_factor=0.5),
            )

            # If we get a 206 Partial Content, range requests are supported
            return res.status == 206
        except Exception as e:
            # If any errors occur, assume range requests are not supported
            logger.warning(f"Error checking range support: {e}")
            return False

    def _get_content_size(self) -> int:
        """Get the total content size using a range request.

        Returns:
            int: The total content size in bytes
        """
        try:
            headers = self.headers.copy()
            headers["Range"] = "bytes=0-0"
            res = self.http.request(
                "GET",
                self.url,
                headers=headers,
                retries=urllib3.util.Retry(total=3, backoff_factor=0.5),
            )

            # Get the content size from the Content-Range header
            if "Content-Range" in res.headers:
                return int(res.headers["Content-Range"].partition("/")[-1])

            # If no Content-Range header, use the Content-Length header
            if "Content-Length" in res.headers:
                return int(res.headers["Content-Length"])

            # If we can't determine the size, raise an exception
            raise ValueError("Could not determine content size")
        except Exception as e:
            # If any errors occur during range request, fall back to getting content size with HEAD
            logger.warning(f"Error getting content size with range request: {e}")

            head_response = self.http.request(
                "HEAD",
                self.url,
                headers=self.headers,
                retries=urllib3.util.Retry(total=3, backoff_factor=0.5),
            )

            if "Content-Length" in head_response.headers:
                return int(head_response.headers["Content-Length"])

            raise ValueError("Could not determine content size")

    def _download_full_file(self) -> int:
        """Download the entire file in a single request.

        Returns:
            int: The number of bytes downloaded
        """
        try:
            response = self.http.request(
                "GET",
                self.url,
                headers=self.headers,
                preload_content=False,
                retries=urllib3.util.Retry(total=3, backoff_factor=0.5),
            )

            # Get content size from headers if available
            content_size = 0
            if "Content-Length" in response.headers:
                content_size = int(response.headers["Content-Length"])

            # Copy the response data to the destination
            bytes_copied = 0
            for chunk in response.stream(1024 * 1024):  # Stream in 1MB chunks
                bytes_copied += len(chunk)
                self.destination.write(chunk)

            response.release_conn()

            # Return the actual number of bytes downloaded
            return bytes_copied if bytes_copied > 0 else content_size
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise

    def _get_part(self, block: Tuple[int, int]) -> None:
        """Download specific block of data from blob and writes it into destination.

        Args:
            block: block of bytes to download
        """
        try:
            headers = self.headers.copy()
            headers["Range"] = f"bytes={block[0]}-{block[1]}"
            res = self.http.request(
                "GET",
                self.url,
                headers=headers,
                preload_content=False,
                retries=urllib3.util.Retry(total=3, backoff_factor=0.5),
            )

            buffer = io.BytesIO()
            shutil.copyfileobj(res, buffer)

            buffer.seek(0)
            with self._lock:
                self.destination.seek(block[0])
                shutil.copyfileobj(buffer, self.destination)  # type: ignore

            buffer.close()
            res.release_connection()
        except Exception as e:
            logger.error(f"Error downloading block {block}: {e}")
            raise
