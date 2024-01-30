"""Domino Data API for interacting with Access Data features"""

from importlib import metadata as importlib_metadata

# Pyarrow CVE hotfix https://lists.apache.org/thread/4notgcj3y7j5z4vxcr6o966g52jqxpdt
import pyarrow_hotfix  # noqa: F401


def get_version() -> str:
    """Get installed packaged version."""
    try:
        return importlib_metadata.version("dominodatalab-data")
    except importlib_metadata.PackageNotFoundError:
        return "unknown"


version: str = get_version()
