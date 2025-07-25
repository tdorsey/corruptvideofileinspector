"""
Corrupt Video Inspector - A comprehensive tool for detecting corrupted video files.

This package provides functionality to:
- Scan directories for video files using FFmpeg
- Detect corruption using multiple scan modes (quick, deep, hybrid)
- Resume interrupted scans with Write-Ahead Logging
- Sync healthy files to Trakt.tv watchlist
- Generate detailed reports

Main Components:
- Scanner: Core video scanning engine
- FFmpeg Integration: Video analysis and corruption detection
- Trakt Integration: Watchlist synchronization
- CLI: Command-line interface
- Configuration: Flexible configuration management
"""

__version__ = "2.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Public API exports
from .config import AppConfig, load_config

# Exception exports
from .core.models import (
    ConfigurationError,
    CorruptVideoInspectorError,
    FFmpegError,
    MediaInfo,
    MediaType,
    ScanError,
    ScanMode,
    ScanResult,
    ScanSummary,
    StorageError,
    TraktError,
    VideoFile,
)
from .core.scanner import VideoScanner

# Version info
__version_info__ = tuple(map(int, __version__.split(".")))

# Package metadata
__title__ = "corrupt-video-inspector"
__description__ = "A comprehensive tool for detecting corrupted video files and syncing to Trakt.tv"
__url__ = "https://github.com/yourusername/corrupt-video-inspector"
__license__ = "MIT"
__copyright__ = "Copyright 2024"

# Public API
__all__ = [
    "AppConfig",
    "ConfigurationError",
    # Exceptions
    "CorruptVideoInspectorError",
    "FFmpegError",
    "MediaInfo",
    "MediaType",
    "ScanError",
    # Models
    "ScanMode",
    "ScanResult",
    "ScanSummary",
    "StorageError",
    "TraktError",
    "VideoFile",
    # Core classes
    "VideoScanner",
    # Version info
    "__version__",
    "__version_info__",
    "load_config",
]
