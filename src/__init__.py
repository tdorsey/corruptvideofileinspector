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
from .core.models import (
    ScanMode,
    ScanResult,
    ScanSummary,
    VideoFile,
    MediaInfo,
    MediaType,
)
from .core.scanner import VideoScanner
from .config.loader import load_config
from .config.settings import AppConfig

# Exception exports
from .core.models import (
    CorruptVideoInspectorError,
    ConfigurationError,
    ScanError,
    FFmpegError,
    TraktError,
    StorageError,
)

# Version info
__version_info__ = tuple(map(int, __version__.split(".")))

# Package metadata
__title__ = "corrupt-video-inspector"
__description__ = (
    "A comprehensive tool for detecting corrupted video files and syncing to Trakt.tv"
)
__url__ = "https://github.com/yourusername/corrupt-video-inspector"
__license__ = "MIT"
__copyright__ = "Copyright 2024"

# Public API
__all__ = [
    # Core classes
    "VideoScanner",
    "AppConfig",
    "load_config",
    # Models
    "ScanMode",
    "ScanResult",
    "ScanSummary",
    "VideoFile",
    "MediaInfo",
    "MediaType",
    # Exceptions
    "CorruptVideoInspectorError",
    "ConfigurationError",
    "ScanError",
    "FFmpegError",
    "TraktError",
    "StorageError",
    # Version info
    "__version__",
    "__version_info__",
]
