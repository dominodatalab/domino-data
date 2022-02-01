"""Domino Data API for interacting with Access Data features"""

from importlib import metadata as importlib_metadata


def get_version() -> str:
    """Get installed packaged version."""
    try:
        return importlib_metadata.version("dominodatalab-data")
    except importlib_metadata.PackageNotFoundError:
        return "unknown"


version: str = get_version()
