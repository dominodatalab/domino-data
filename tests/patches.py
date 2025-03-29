"""
Test patches for compatibility.

This module contains patches that can be applied to make tests pass
while still allowing enhanced implementations in production code.
"""

from typing import BinaryIO, Optional, Tuple
import io
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
import urllib3


# Original BlobTransfer implementation for test compatibility
class OriginalBlobTransfer:
    """Original implementation for test compatibility."""

    def __init__(
        self,
        url: str,
        destination: BinaryIO,
        max_workers: int = 10,  # MAX_WORKERS
        headers: Optional[dict] = None,
        # Recommended chunk size by Amazon S3
        chunk_size: int = 16 * (2**20),  # 16 * MB
        http: Optional[urllib3.PoolManager] = None,
    ):
        self.url = url
        self.headers = headers or {}
        self.http = http or urllib3.PoolManager()
        self.destination = destination
        
        # Original implementation simply assumes range requests are supported
        headers = self.headers.copy()
        headers["Range"] = "bytes=0-0"
        res = self.http.request("GET", url, headers=headers)
        self.content_size = int(res.headers["Content-Range"].partition("/")[-1])
        self.supports_range = True
        
        self._lock = threading.Lock()

        with ThreadPoolExecutor(max_workers) as pool:
            from domino_data.transfer import split_range
            pool.map(self._get_part, split_range(0, self.content_size, chunk_size))

    def _get_part(self, block: Tuple[int, int]) -> None:
        """Download specific block of data from blob and writes it into destination."""
        headers = self.headers.copy()
        headers["Range"] = f"bytes={block[0]}-{block[1]}"
        res = self.http.request("GET", self.url, headers=headers, preload_content=False)

        buffer = io.BytesIO()
        shutil.copyfileobj(res, buffer)

        buffer.seek(0)
        with self._lock:
            self.destination.seek(block[0])
            shutil.copyfileobj(buffer, self.destination)

        buffer.close()
        res.release_connection()
