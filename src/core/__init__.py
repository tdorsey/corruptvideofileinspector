"""
Core functionality for video scanning and corruption detection.
"""

from .models import (
    ScanMode,
    ScanResult,
    ScanSummary,
    VideoFile,
    MediaInfo,
    MediaType,
    CorruptVideoInspectorError,
    ConfigurationError,
    ScanError,
    FFmpegError,
    TraktError,
    StorageError,
)
from .scanner import VideoScanner
from .detector import CorruptionDetector, CorruptionAnalysis

__all__ = [
    # Models
    "ScanMode",
    "ScanResult", 
    "ScanSummary",
    "VideoFile",
    "MediaInfo",
    "MediaType",
    # Scanner
    "VideoScanner",
    # Detector
    "CorruptionDetector",
    "CorruptionAnalysis",
    # Exceptions
    "CorruptVideoInspectorError",
    "ConfigurationError",
    "ScanError",
    "FFmpegError",
    "TraktError",
    "StorageError",
]