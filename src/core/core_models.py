"""
Core data models for the Corrupt Video Inspector application.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class ScanMode(Enum):
    """Scan modes for video inspection."""

    QUICK = "quick"
    DEEP = "deep"
    HYBRID = "hybrid"


class MediaType(Enum):
    """Types of media content."""

    MOVIE = "movie"
    TV_SHOW = "show"
    UNKNOWN = "unknown"


@dataclass
class VideoFile:
    """Represents a video file with its properties."""

    path: Path
    size: int = 0
    duration: float = 0.0

    def __post_init__(self) -> None:
        """Initialize file size if file exists."""
        if self.path.exists():
            self.size = self.path.stat().st_size

    @property
    def filename(self) -> str:
        """Get the filename as string for backward compatibility."""
        return str(self.path)

    @property
    def name(self) -> str:
        """Get just the filename without path."""
        return self.path.name

    @property
    def stem(self) -> str:
        """Get filename without extension."""
        return self.path.stem


@dataclass
class MediaInfo:
    """Parsed media information from filename."""

    title: str
    year: Optional[int] = None
    media_type: MediaType = MediaType.MOVIE
    season: Optional[int] = None
    episode: Optional[int] = None
    quality: Optional[str] = None
    source: Optional[str] = None  # BluRay, WEB-DL, etc.
    codec: Optional[str] = None  # x264, H.265, etc.
    original_filename: str = ""

    def __post_init__(self) -> None:
        """Clean up and validate media info."""
        # Clean up title
        self.title = self._clean_title(self.title)

        # Validate year
        if self.year and (self.year < 1900 or self.year > 2100):
            self.year = None

    def _clean_title(self, title: str) -> str:
        """Clean up title by removing dots, underscores, etc."""
        import re

        # Replace dots and underscores with spaces
        title = re.sub(r"[._]", " ", title)
        # Normalize whitespace
        title = re.sub(r"\s+", " ", title)
        return title.strip()

    @property
    def display_name(self) -> str:
        """Get display name with year if available."""
        if self.year:
            return f"{self.title} ({self.year})"
        return self.title


@dataclass
class ScanResult:
    """Results of video file inspection."""

    video_file: VideoFile
    is_corrupt: bool = False
    error_message: str = ""
    ffmpeg_output: str = ""
    inspection_time: float = 0.0
    scan_mode: ScanMode = ScanMode.QUICK
    needs_deep_scan: bool = False
    deep_scan_completed: bool = False
    timestamp: float = field(default_factory=time.time)

    @property
    def filename(self) -> str:
        """Get filename for backward compatibility."""
        return str(self.video_file.path)

    @property
    def file_size(self) -> int:
        """Get file size for backward compatibility."""
        return self.video_file.size

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "filename": str(self.video_file.path),
            "is_corrupt": self.is_corrupt,
            "error_message": self.error_message,
            "inspection_time": self.inspection_time,
            "file_size": self.video_file.size,
            "scan_mode": self.scan_mode.value,
            "needs_deep_scan": self.needs_deep_scan,
            "deep_scan_completed": self.deep_scan_completed,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanResult":
        """Create ScanResult from dictionary."""
        video_file = VideoFile(Path(data["filename"]))
        return cls(
            video_file=video_file,
            is_corrupt=data.get("is_corrupt", False),
            error_message=data.get("error_message", ""),
            inspection_time=data.get("inspection_time", 0.0),
            scan_mode=ScanMode(data.get("scan_mode", "quick")),
            needs_deep_scan=data.get("needs_deep_scan", False),
            deep_scan_completed=data.get("deep_scan_completed", False),
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class ScanSummary:
    """Summary of a complete scan operation."""

    directory: Path
    total_files: int
    processed_files: int
    corrupt_files: int
    healthy_files: int
    scan_mode: ScanMode
    scan_time: float
    deep_scans_needed: int = 0
    deep_scans_completed: int = 0
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    was_resumed: bool = False

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.processed_files == 0:
            return 0.0
        return (self.healthy_files / self.processed_files) * 100.0

    @property
    def is_complete(self) -> bool:
        """Check if scan was completed."""
        return self.completed_at is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            "directory": str(self.directory),
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "corrupt_files": self.corrupt_files,
            "healthy_files": self.healthy_files,
            "scan_mode": self.scan_mode.value,
            "scan_time": self.scan_time,
            "deep_scans_needed": self.deep_scans_needed,
            "deep_scans_completed": self.deep_scans_completed,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "was_resumed": self.was_resumed,
            "success_rate": self.success_rate,
        }


@dataclass
class ScanProgress:
    """Real-time scan progress information."""

    current_file: Optional[str] = None
    total_files: int = 0
    processed_count: int = 0
    corrupt_count: int = 0
    phase: str = "scanning"
    scan_mode: str = "unknown"
    start_time: float = field(default_factory=time.time)

    @property
    def remaining_count(self) -> int:
        """Get number of remaining files."""
        return self.total_files - self.processed_count

    @property
    def healthy_count(self) -> int:
        """Get number of healthy files."""
        return self.processed_count - self.corrupt_count

    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_count / self.total_files) * 100.0

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def estimated_remaining_time(self) -> Optional[float]:
        """Estimate remaining time in seconds."""
        if self.processed_count == 0:
            return None

        avg_time_per_file = self.elapsed_time / self.processed_count
        return avg_time_per_file * self.remaining_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert progress to dictionary."""
        return {
            "current_file": self.current_file,
            "total_files": self.total_files,
            "processed_count": self.processed_count,
            "corrupt_count": self.corrupt_count,
            "healthy_count": self.healthy_count,
            "remaining_count": self.remaining_count,
            "progress_percentage": self.progress_percentage,
            "phase": self.phase,
            "scan_mode": self.scan_mode,
            "elapsed_time": self.elapsed_time,
            "estimated_remaining_time": self.estimated_remaining_time,
        }


# Exception classes
class CorruptVideoInspectorError(Exception):
    """Base exception for all application errors."""

    pass


class ConfigurationError(CorruptVideoInspectorError):
    """Configuration-related errors."""

    pass


class ScanError(CorruptVideoInspectorError):
    """Scanning-related errors."""

    pass


class FFmpegError(ScanError):
    """FFmpeg-related errors."""

    pass


class TraktError(CorruptVideoInspectorError):
    """Trakt integration errors."""

    pass


class StorageError(CorruptVideoInspectorError):
    """Storage and persistence errors."""

    pass
