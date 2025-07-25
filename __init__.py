"""Corrupt Video Inspector - A comprehensive tool for detecting corrupted video files.

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

# Version information
__version__ = "2.0.0"
__version_info__ = tuple(map(int, __version__.split(".")))

# Package metadata
__title__ = "corrupt-video-inspector"
__description__ = "A comprehensive tool for detecting corrupted video files and syncing to Trakt.tv"
__url__ = "https://github.com/tdorsey/corruptvideoinspector"
__author__ = "tdorsey"
__author_email__ = "contact@example.com"
__license__ = "MIT"
__copyright__ = "Copyright 2024 tdorsey"

# Public API - Core Models
# Public API - Configuration
from corrupt_video_inspector.config.settings import AppConfig, load_config

# Public API - Exceptions
from corrupt_video_inspector.core.models import (
    ConfigurationError,
    CorruptVideoInspectorError,
    FFmpegError,
    MediaInfo,
    MediaType,
    ScanError,
    ScanMode,
    ScanProgress,
    ScanResult,
    ScanSummary,
    StorageError,
    TraktError,
    VideoFile,
)

# Public API - Core Scanner
from corrupt_video_inspector.core.scanner import VideoScanner

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


def get_version_info() -> tuple[int, ...]:
    """Get version information as a tuple.

    Returns:
        Version tuple (major, minor, patch).
    """
    return __version_info__
