"""Version information for corrupt-video-inspector."""

from __future__ import annotations

import sys

if sys.version_info >= (3, 8):
    from importlib.metadata import PackageNotFoundError, version
else:
    from importlib_metadata import PackageNotFoundError, version


def get_version() -> str:
    """Get the version of the package."""
    try:
        return version("corrupt-video-inspector")
    except PackageNotFoundError:
        # Fallback for development environments or when package is not installed
        return "0.0.0+dev"


__version__ = get_version()
