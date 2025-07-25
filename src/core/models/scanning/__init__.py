import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.models.inspection import VideoFile


class ScanMode(Enum):
    """Scan modes for video inspection.

    Attributes:
        QUICK: Fast scan using basic FFmpeg checks
        DEEP: Thorough scan analyzing entire video stream
        HYBRID: Smart scan - quick first, then deep for suspicious files
    """

    QUICK = "quick"
    DEEP = "deep"
    HYBRID = "hybrid"


@dataclass
class ScanResult:
    """Results of video file inspection.

    Attributes:
        video_file: The video file that was scanned
        is_corrupt: Whether corruption was detected
        error_message: Human-readable error description
        ffmpeg_output: Raw FFmpeg output for debugging
        inspection_time: Time taken to scan this file (seconds)
        scan_mode: Scan mode used for this file
        needs_deep_scan: Whether file needs deeper analysis
        deep_scan_completed: Whether deep scan was performed
        timestamp: When the scan was performed
        confidence: Confidence level of corruption detection (0.0-1.0)
    """

    video_file: VideoFile
    is_corrupt: bool = False
    error_message: str = ""
    ffmpeg_output: str = ""
    inspection_time: float = 0.0
    scan_mode: ScanMode = ScanMode.QUICK
    needs_deep_scan: bool = False
    deep_scan_completed: bool = False
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.0

    @property
    def filename(self) -> str:
        """Get filename for backward compatibility."""
        return str(self.video_file.path)

    @property
    def file_size(self) -> int:
        """Get file size for backward compatibility."""
        return self.video_file.size

    @property
    def status(self) -> str:
        """Get human-readable status."""
        if self.is_corrupt:
            return "CORRUPT"
        if self.needs_deep_scan:
            return "SUSPICIOUS"
        return "HEALTHY"

    @property
    def confidence_percentage(self) -> float:
        """Get confidence as percentage."""
        return self.confidence * 100.0

    def to_dict(self) -> dict[str, Any]:
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
            "confidence": self.confidence,
            "status": self.status,
            "confidence_percentage": self.confidence_percentage,
            "video_file": self.video_file.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanResult":
        """Create ScanResult from dictionary.

        Args:
            data: Dictionary containing scan result data

        Returns:
            ScanResult instance
        """
        # Handle both old and new data formats
        if "video_file" in data and isinstance(data["video_file"], dict):
            video_file = VideoFile.from_dict(data["video_file"])
        else:
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
            confidence=data.get("confidence", 0.0),
        )

    def is_healthy(self) -> bool:
        """Check if file is healthy (not corrupt and doesn't need deep scan)."""
        return not self.is_corrupt and not self.needs_deep_scan

    def get_severity_level(self) -> str:
        """Get severity level as string."""
        if self.is_corrupt:
            if self.confidence > 0.8:
                return "HIGH"
            if self.confidence > 0.5:
                return "MEDIUM"
            return "LOW"
        if self.needs_deep_scan:
            return "SUSPICIOUS"
        return "NONE"


@dataclass
class ScanSummary:
    """Summary of a complete scan operation.

    Attributes:
        directory: Directory that was scanned
        total_files: Total number of video files found
        processed_files: Number of files actually processed
        corrupt_files: Number of files identified as corrupt
        healthy_files: Number of files identified as healthy
        scan_mode: Primary scan mode used
        scan_time: Total time taken for scan (seconds)
        deep_scans_needed: Number of files that needed deep scanning
        deep_scans_completed: Number of deep scans actually performed
        started_at: Timestamp when scan started
        completed_at: Timestamp when scan completed (None if incomplete)
        was_resumed: Whether this scan was resumed from previous state
    """

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
    completed_at: float | None = None
    was_resumed: bool = False

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.processed_files == 0:
            return 0.0
        return (self.healthy_files / self.processed_files) * 100.0

    @property
    def corruption_rate(self) -> float:
        """Calculate corruption rate as percentage."""
        if self.processed_files == 0:
            return 0.0
        return (self.corrupt_files / self.processed_files) * 100.0

    @property
    def is_complete(self) -> bool:
        """Check if scan was completed."""
        return self.completed_at is not None

    @property
    def files_per_second(self) -> float:
        """Calculate processing rate."""
        if self.scan_time <= 0:
            return 0.0
        return self.processed_files / self.scan_time

    @property
    def suspicious_files(self) -> int:
        """Get number of suspicious files (needs deep scan)."""
        return self.deep_scans_needed

    def to_dict(self) -> dict[str, Any]:
        """Convert summary to dictionary for JSON serialization."""
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
            "corruption_rate": self.corruption_rate,
            "files_per_second": self.files_per_second,
            "is_complete": self.is_complete,
            "suspicious_files": self.suspicious_files,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanSummary":
        """Create ScanSummary from dictionary.

        Args:
            data: Dictionary containing summary data

        Returns:
            ScanSummary instance
        """
        return cls(
            directory=Path(data["directory"]),
            total_files=data["total_files"],
            processed_files=data["processed_files"],
            corrupt_files=data["corrupt_files"],
            healthy_files=data["healthy_files"],
            scan_mode=ScanMode(data["scan_mode"]),
            scan_time=data["scan_time"],
            deep_scans_needed=data.get("deep_scans_needed", 0),
            deep_scans_completed=data.get("deep_scans_completed", 0),
            started_at=data.get("started_at", time.time()),
            completed_at=data.get("completed_at"),
            was_resumed=data.get("was_resumed", False),
        )

    def get_status_summary(self) -> str:
        """Get a human-readable status summary.

        Returns:
            Status summary string
        """
        if not self.is_complete:
            return f"In progress: {self.processed_files}/" f"{self.total_files} files processed"

        status_parts = [
            f"{self.total_files} files scanned",
            f"{self.corrupt_files} corrupt",
            f"{self.healthy_files} healthy",
        ]

        if self.deep_scans_needed > 0:
            status_parts.append(f"{self.deep_scans_needed} needed deep scan")

        return ", ".join(status_parts)

    def get_performance_summary(self) -> str:
        """Get performance statistics summary.

        Returns:
            Performance summary string
        """
        return f"Completed in {self.scan_time:.2f}s " f"({self.files_per_second:.1f} files/sec)"

    def get_detailed_summary(self) -> str:
        """Get detailed summary with all statistics.

        Returns:
            Detailed summary string
        """
        lines = [
            f"Directory: {self.directory}",
            f"Status: {'Complete' if self.is_complete else 'In Progress'}",
            f"Files: {self.processed_files}/{self.total_files} processed",
            f"Results: {self.healthy_files} healthy, " f"{self.corrupt_files} corrupt",
            f"Performance: {self.files_per_second:.1f} files/sec",
            f"Success Rate: {self.success_rate:.1f}%",
        ]

        if self.deep_scans_needed > 0:
            lines.append(f"Deep Scans: {self.deep_scans_completed}/" f"{self.deep_scans_needed}")

        if self.was_resumed:
            lines.append("Note: This scan was resumed from a previous session")

        return "\n".join(lines)


@dataclass
class ScanProgress:
    """Real-time scan progress information.

    Attributes:
        current_file: Path of currently processing file
        total_files: Total number of files to process
        processed_count: Number of files already processed
        corrupt_count: Number of corrupt files found so far
        phase: Current scan phase (scanning, deep_scan, etc.)
        scan_mode: Current scan mode being used
        start_time: When the scan started
    """

    current_file: str | None = None
    total_files: int = 0
    processed_count: int = 0
    corrupt_count: int = 0
    phase: str = "scanning"
    scan_mode: str = "unknown"
    start_time: float = field(default_factory=time.time)

    @property
    def remaining_count(self) -> int:
        """Get number of remaining files."""
        return max(0, self.total_files - self.processed_count)

    @property
    def healthy_count(self) -> int:
        """Get number of healthy files."""
        return max(0, self.processed_count - self.corrupt_count)

    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage (0-100)."""
        if self.total_files == 0:
            return 0.0
        return min(100.0, (self.processed_count / self.total_files) * 100.0)

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def estimated_remaining_time(self) -> float | None:
        """Estimate remaining time in seconds."""
        if self.processed_count == 0 or self.remaining_count == 0:
            return None

        avg_time_per_file = self.elapsed_time / self.processed_count
        return avg_time_per_file * self.remaining_count

    @property
    def processing_rate(self) -> float:
        """Get files processed per second."""
        if self.elapsed_time <= 0:
            return 0.0
        return self.processed_count / self.elapsed_time

    def to_dict(self) -> dict[str, Any]:
        """Convert progress to dictionary for JSON serialization."""
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
            "processing_rate": self.processing_rate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanProgress":
        """Create ScanProgress from dictionary.

        Args:
            data: Dictionary containing progress data

        Returns:
            ScanProgress instance
        """
        return cls(
            current_file=data.get("current_file"),
            total_files=data.get("total_files", 0),
            processed_count=data.get("processed_count", 0),
            corrupt_count=data.get("corrupt_count", 0),
            phase=data.get("phase", "scanning"),
            scan_mode=data.get("scan_mode", "unknown"),
            start_time=data.get("start_time", time.time()),
        )

    def get_eta_string(self) -> str:
        """Get estimated time remaining as human-readable string.

        Returns:
            ETA string (e.g., "2m 30s" or "Unknown")
        """
        eta = self.estimated_remaining_time
        if eta is None:
            return "Unknown"

        if eta < 60:
            return f"{int(eta)}s"
        if eta < 3600:
            minutes = int(eta // 60)
            seconds = int(eta % 60)
            return f"{minutes}m {seconds}s"
        hours = int(eta // 3600)
        minutes = int((eta % 3600) // 60)
        return f"{hours}h {minutes}m"

    def get_progress_bar_string(self, width: int = 20) -> str:
        """Get ASCII progress bar representation.

        Args:
            width: Width of progress bar in characters

        Returns:
            Progress bar string
        """
        if self.total_files == 0:
            return "█" * width

        filled = int((self.processed_count / self.total_files) * width)
        bar = "█" * filled + "░" * (width - filled)
        percentage = self.progress_percentage
        return f"{bar} {percentage:5.1f}%"

    def get_status_line(self) -> str:
        """Get single-line status summary.

        Returns:
            Status line string
        """
        return (
            f"[{self.phase.upper()}] {self.processed_count}/"
            f"{self.total_files} ({self.progress_percentage:.1f}%) - "
            f"{self.corrupt_count} corrupt, "
            f"{self.healthy_count} healthy - "
            f"ETA: {self.get_eta_string()}"
        )


@dataclass
class BatchScanRequest:
    """Request for batch scanning multiple directories.

    Attributes:
        directories: List of directories to scan
        scan_mode: Scan mode to use for all directories
        recursive: Whether to scan subdirectories
        extensions: File extensions to include
        max_parallel: Maximum parallel scans
        output_format: Output format for results
    """

    directories: list[Path]
    scan_mode: ScanMode = ScanMode.HYBRID
    recursive: bool = True
    extensions: list[str] | None = None
    max_parallel: int = 2
    output_format: str = "json"

    def __post_init__(self) -> None:
        """Validate batch scan request."""
        if not self.directories:
            raise ValueError("At least one directory must be specified")

        for directory in self.directories:
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory}")
            if not directory.is_dir():
                raise NotADirectoryError(f"Path is not a directory: {directory}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "directories": [str(d) for d in self.directories],
            "scan_mode": self.scan_mode.value,
            "recursive": self.recursive,
            "extensions": self.extensions,
            "max_parallel": self.max_parallel,
            "output_format": self.output_format,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BatchScanRequest":
        """Create BatchScanRequest from dictionary."""
        return cls(
            directories=[Path(d) for d in data["directories"]],
            scan_mode=ScanMode(data.get("scan_mode", "hybrid")),
            recursive=data.get("recursive", True),
            extensions=data.get("extensions"),
            max_parallel=data.get("max_parallel", 2),
            output_format=data.get("output_format", "json"),
        )


@dataclass
class ScanFilter:
    """Filtering options for scan results.

    Attributes:
        include_corrupt: Include corrupt files in results
        include_healthy: Include healthy files in results
        include_suspicious: Include suspicious files in results
        min_file_size: Minimum file size in bytes
        max_file_size: Maximum file size in bytes
        file_extensions: Only include these extensions
        exclude_paths: Exclude files matching these path patterns
    """

    include_corrupt: bool = True
    include_healthy: bool = True
    include_suspicious: bool = True
    min_file_size: int = 0
    max_file_size: int | None = None
    file_extensions: list[str] | None = None
    exclude_paths: list[str] | None = None

    def matches(self, result: "ScanResult") -> bool:
        """Check if scan result matches this filter.

        Args:
            result: Scan result to check

        Returns:
            True if result matches filter criteria
        """
        # Check corruption status
        if result.is_corrupt and not self.include_corrupt:
            return False
        if not result.is_corrupt and result.needs_deep_scan and not self.include_suspicious:
            return False
        if not result.is_corrupt and not result.needs_deep_scan and not self.include_healthy:
            return False

        # Check file size
        if result.video_file.size < self.min_file_size:
            return False
        if self.max_file_size and result.video_file.size > self.max_file_size:
            return False

        # Check file extension
        if self.file_extensions:
            ext = result.video_file.suffix.lower()
            if ext not in self.file_extensions:
                return False

        # Check exclude paths
        if self.exclude_paths:
            file_path_str = str(result.video_file.path)
            for exclude_pattern in self.exclude_paths:
                if exclude_pattern in file_path_str:
                    return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "include_corrupt": self.include_corrupt,
            "include_healthy": self.include_healthy,
            "include_suspicious": self.include_suspicious,
            "min_file_size": self.min_file_size,
            "max_file_size": self.max_file_size,
            "file_extensions": self.file_extensions,
            "exclude_paths": self.exclude_paths,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanFilter":
        """Create ScanFilter from dictionary."""
        return cls(
            include_corrupt=data.get("include_corrupt", True),
            include_healthy=data.get("include_healthy", True),
            include_suspicious=data.get("include_suspicious", True),
            min_file_size=data.get("min_file_size", 0),
            max_file_size=data.get("max_file_size"),
            file_extensions=data.get("file_extensions"),
            exclude_paths=data.get("exclude_paths"),
        )
