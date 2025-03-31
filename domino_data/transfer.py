from typing import BinaryIO, Generator, Optional, Tuple, Dict, Any, List
import io
import os
import json
import shutil
import threading
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import urllib3

MAX_WORKERS = 10
MB = 2**20  # 2^20 bytes - 1 Megabyte
DEFAULT_CHUNK_SIZE = 16 * MB  # 16 MB chunks recommended by Amazon S3
RESUME_DIR_NAME = ".domino_downloads"


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


def get_file_from_uri(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    http: Optional[urllib3.PoolManager] = None,
    start_byte: Optional[int] = None,
    end_byte: Optional[int] = None,
) -> Tuple[bytes, Dict[str, str]]:
    """Get file content from URI.

    Args:
        url: URI to get content from
        headers: Optional headers to include in the request
        http: Optional HTTP pool manager to use
        start_byte: Optional start byte for range request
        end_byte: Optional end byte for range request

    Returns:
        Tuple of (file content, response headers)
    """
    headers = headers or {}
    http = http or urllib3.PoolManager()

    # Add Range header if start_byte is specified
    if start_byte is not None:
        range_header = f"bytes={start_byte}-"
        if end_byte is not None:
            range_header = f"bytes={start_byte}-{end_byte}"
        headers["Range"] = range_header

    res = http.request("GET", url, headers=headers)
    
    if start_byte is not None and res.status != 206:
        raise ValueError(f"Expected partial content (status 206), got {res.status}")
    
    return res.data, dict(res.headers)


def get_content_size(
    url: str, 
    headers: Optional[Dict[str, str]] = None, 
    http: Optional[urllib3.PoolManager] = None
) -> int:
    """Get the size of content from a URI.

    Args:
        url: URI to get content size for
        headers: Optional headers to include in the request
        http: Optional HTTP pool manager to use

    Returns:
        Content size in bytes
    """
    headers = headers or {}
    http = http or urllib3.PoolManager()
    headers["Range"] = "bytes=0-0"
    res = http.request("GET", url, headers=headers)
    return int(res.headers["Content-Range"].partition("/")[-1])


def get_resume_state_path(file_path: str, url_hash: Optional[str] = None) -> str:
    """Generate a path for the resume state file.
    
    Args:
        file_path: Path to the destination file
        url_hash: Optional hash of the URL to identify the download
        
    Returns:
        Path to the resume state file
    """
    file_dir = os.path.dirname(os.path.abspath(file_path))
    file_name = os.path.basename(file_path)
    
    # Create .domino_downloads directory if it doesn't exist
    download_dir = os.path.join(file_dir, RESUME_DIR_NAME)
    os.makedirs(download_dir, exist_ok=True)
    
    # Use file_name + hash (if provided) for the state file
    state_file_name = f"{file_name}.resume.json"
    if url_hash:
        state_file_name = f"{file_name}_{url_hash}.resume.json"
        
    state_file = os.path.join(download_dir, state_file_name)
    return state_file


class BlobTransfer:
    def __init__(
        self,
        url: str,
        destination: BinaryIO,
        max_workers: int = MAX_WORKERS,
        headers: Optional[dict] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        http: Optional[urllib3.PoolManager] = None,
        resume_state_file: Optional[str] = None,
        resume: bool = False,
    ):
        """Initialize a new BlobTransfer.
        
        Args:
            url: URL to download from
            destination: File-like object to write to
            max_workers: Maximum number of threads to use for parallel downloads
            headers: Optional headers to include in the request
            chunk_size: Size of chunks to download in bytes
            http: Optional HTTP pool manager to use
            resume_state_file: Path to file to store download state for resuming
            resume: Whether to attempt to resume a previous download
        """
        self.url = url
        self.headers = headers or {}
        self.http = http or urllib3.PoolManager()
        self.destination = destination
        self.resume_state_file = resume_state_file
        self.chunk_size = chunk_size
        self.content_size = self._get_content_size()
        self.resume = resume
        
        # Completed chunks tracking
        self._completed_chunks = set()
        self._lock = threading.Lock()
        
        # Load previous state if resuming
        if resume and resume_state_file and os.path.exists(resume_state_file):
            self._load_state()
        else:
            # Clear the state file if not resuming
            if resume_state_file and os.path.exists(resume_state_file):
                os.remove(resume_state_file)
        
        # Calculate ranges to download
        ranges_to_download = self._get_ranges_to_download()
        
        # Download chunks in parallel
        with ThreadPoolExecutor(max_workers) as pool:
            pool.map(self._get_part, ranges_to_download)
        
        # Clean up state file after successful download
        if resume_state_file and os.path.exists(resume_state_file):
            os.remove(resume_state_file)

    def _get_content_size(self) -> int:
        headers = self.headers.copy()
        headers["Range"] = "bytes=0-0"
        res = self.http.request("GET", self.url, headers=headers)
        return int(res.headers["Content-Range"].partition("/")[-1])

    def _load_state(self) -> None:
        """Load the saved state from file."""
        try:
            with open(self.resume_state_file, "r") as f:
                state = json.loads(f.read())
                
                # Validate state is for the same URL and content size
                if state.get("url") != self.url:
                    raise ValueError("State file is for a different URL")
                
                if state.get("content_size") != self.content_size:
                    raise ValueError("Content size has changed since last download")
                    
                # Load completed chunks
                self._completed_chunks = set(tuple(chunk) for chunk in state.get("completed_chunks", []))
        except (json.JSONDecodeError, FileNotFoundError, KeyError, TypeError, ValueError) as e:
            # If state file is invalid, start fresh
            self._completed_chunks = set()

    def _save_state(self) -> None:
        """Save the current download state to file."""
        if not self.resume_state_file:
            return
            
        # Create directory if it doesn't exist
        resume_dir = os.path.dirname(self.resume_state_file)
        if resume_dir:
            os.makedirs(resume_dir, exist_ok=True)
            
        with open(self.resume_state_file, "w") as f:
            state = {
                "url": self.url,
                "content_size": self.content_size,
                "completed_chunks": list(self._completed_chunks),
                "timestamp": time.time()
            }
            f.write(json.dumps(state))

    def _get_ranges_to_download(self) -> List[Tuple[int, int]]:
        """Get the ranges that need to be downloaded."""
        # If not resuming, download everything
        if not self.resume or not self._completed_chunks:
            return list(split_range(0, self.content_size - 1, self.chunk_size))
        
        # Otherwise, return only ranges that haven't been completed
        all_ranges = list(split_range(0, self.content_size - 1, self.chunk_size))
        return [chunk_range for chunk_range in all_ranges if chunk_range not in self._completed_chunks]

    def _get_part(self, block: Tuple[int, int]) -> None:
        """Download specific block of data from blob and writes it into destination.

        Args:
            block: block of bytes to download
        """
        # Skip if this chunk was already downloaded successfully
        if self.resume and block in self._completed_chunks:
            return
            
        try:
            headers = self.headers.copy()
            headers["Range"] = f"bytes={block[0]}-{block[1]}"
            res = self.http.request("GET", self.url, headers=headers, preload_content=False)

            buffer = io.BytesIO()
            shutil.copyfileobj(res, buffer)

            buffer.seek(0)
            with self._lock:
                self.destination.seek(block[0])
                shutil.copyfileobj(buffer, self.destination)  # type: ignore
                # Mark this chunk as complete and save state
                self._completed_chunks.add(block)
                if self.resume and self.resume_state_file:
                    self._save_state()

            buffer.close()
            res.release_connection()
        except Exception as e:
            # Save state on error to allow resuming later
            if self.resume and self.resume_state_file:
                self._save_state()
            raise e
