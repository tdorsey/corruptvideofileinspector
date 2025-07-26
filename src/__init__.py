"""
Corrupt Video Inspector - A comprehensive tool for detecting corrupted video files.

This package provides functionality to:
- Scan directories for video files using FFmpeg
- Detect corruption using multiple scan modes (quick, deep, hybrid)
- Resume interrupted scans with Write-Ahead Logging
- Sync healthy files to Trakt.tv watchlist
- Generate detailed reports

Example:
    >>> from corrupt_video_inspector import VideoScanner, ScanMode
    >>> from pathlib import Path
    >>>
    >>> scanner = VideoScanner()
    >>> results = scanner.scan_directory(
    ...     Path("/path/to/videos"),
    ...     scan_mode=ScanMode.HYBRID
    ... )
    >>> print(f"Found {results.corrupt_files} corrupt files")
"""

from __future__ import annotations

import sys

from src.version import __version__

from .cli.main import main
from .core.errors.errors import (
    ConfigurationError,
    FFmpegError,
    ScanError,
    StorageError,
    TraktError,
)
from .core.models.inspection import (
    CorruptVideoInspectorError,
    MediaInfo,
    MediaType,
    VideoFile,
)
from .core.models.scanning import (
    ScanMode,
    ScanProgress,
    ScanResult,
    ScanSummary,
)
from .core.scanner import VideoScanner

# Package metadata
__title__ = "corrupt-video-inspector"
__description__ = "A comprehensive tool for detecting corrupted video files and syncing to Trakt.tv"
__url__ = "https://github.com/tdorsey/corruptvideoinspector"
__author__ = "tdorsey"
__author_email__ = "contact@example.com"
__license__ = "MIT"
__copyright__ = "Copyright 2024 tdorsey"

# Explicit public API
__all__ = [
    "AppConfig",
    "ConfigurationError",
    # Exceptions
    "CorruptVideoInspectorError",
    "FFmpegError",
    "MediaInfo",
    "MediaType",
    "ScanError",
    # Enums
    "ScanMode",
    "ScanProgress",
    "ScanResult",
    "ScanSummary",
    "StorageError",
    "TraktError",
    # Data models
    "VideoFile",
    # Core functionality
    "VideoScanner",
    # Version info
    "__version__",
    "__version_info__",
    "load_config",
]


def get_version() -> str:
    """Get the current version of the package.

    Returns:
        The version string.
    """
    return __version__


if __name__ == "__main__":
    sys.exit(main())
