"""
Video corruption detection logic for analyzing FFmpeg output.
"""

from __future__ import annotations

import json
import logging
import signal
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.core.models.scanning import ScanMode

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Global progress tracking for signal handlers
_current_progress: dict[str, Any] = {
    "current_file": "",
    "total_files": 0,
    "processed_count": 0,
    "corrupt_count": 0,
    "remaining_count": 0,
    "scan_mode": "",
    "start_time": 0.0,
}


def setup_signal_handlers() -> None:
    """Set up signal handlers for progress reporting."""
    signal.signal(signal.SIGUSR1, signal_handler)


def signal_handler(signum: int, _frame: Any) -> None:
    """Handle signals for progress reporting."""
    if signum == signal.SIGUSR1:
        # Log current progress
        progress = _current_progress
        elapsed_time = time.time() - progress.get("start_time", 0)

        logger.info(
            f"PROGRESS REPORT - File: {progress.get('current_file', 'N/A')} | "
            f"Progress: {progress.get('processed_count', 0)}/{progress.get('total_files', 0)} | "
            f"Corrupt: {progress.get('corrupt_count', 0)} | "
            f"Mode: {progress.get('scan_mode', 'N/A')} | "
            f"Elapsed: {elapsed_time:.1f}s"
        )


class ProgressReporter:
    """Progress reporter for video scanning operations."""

    def __init__(self, total_files: int, scan_mode: str) -> None:
        """Initialize progress reporter.

        Args:
            total_files: Total number of files to process
            scan_mode: Scanning mode being used
        """
        self.total_files = total_files
        self.scan_mode = scan_mode
        self.processed_count = 0
        self.corrupt_count = 0
        self.current_file = ""
        self.start_time = time.time()

        # Initialize global progress
        _current_progress.update(
            {
                "total_files": total_files,
                "scan_mode": scan_mode,
                "start_time": self.start_time,
                "processed_count": 0,
                "corrupt_count": 0,
                "current_file": "",
                "remaining_count": total_files,
            }
        )

    def update(
        self, current_file: str = "", processed_count: int = 0, corrupt_count: int = 0
    ) -> None:
        """Update progress information.

        Args:
            current_file: Currently processing file
            processed_count: Number of files processed
            corrupt_count: Number of corrupt files found
        """
        if current_file:
            self.current_file = current_file
        if processed_count > 0:
            self.processed_count = processed_count
        if corrupt_count > 0:
            self.corrupt_count = corrupt_count

        # Update global progress
        _current_progress.update(
            {
                "current_file": self.current_file,
                "processed_count": self.processed_count,
                "corrupt_count": self.corrupt_count,
                "remaining_count": self.total_files - self.processed_count,
            }
        )

    def report_progress(self, force_output: bool = False) -> None:
        """Report current progress.

        Args:
            force_output: Force output even if not time for regular update
        """
        if force_output:
            elapsed_time = time.time() - self.start_time
            logger.info(
                f"Progress: {self.processed_count}/{self.total_files} files | "
                f"Corrupt: {self.corrupt_count} | "
                f"Mode: {self.scan_mode} | "
                f"Elapsed: {elapsed_time:.1f}s | "
                f"Current: {self.current_file}"
            )


class WriteAheadLog:
    """Write-ahead log for scan operations."""

    def __init__(self, directory: str, scan_mode: ScanMode, extensions: list[str]) -> None:
        """Initialize write-ahead log.

        Args:
            directory: Directory for log files
            scan_mode: Scanning mode
            extensions: File extensions to scan
        """
        self.directory = Path(directory)
        self.scan_mode = scan_mode
        self.extensions = extensions

        # Create WAL and results file paths
        timestamp = int(time.time())
        self.wal_path = self.directory / f"scan_wal_{timestamp}.json"
        self.results_path = self.directory / f"scan_results_{timestamp}.json"

    def write_entry(self, entry: dict[str, Any]) -> None:
        """Write an entry to the WAL.

        Args:
            entry: Log entry to write
        """
        with self.wal_path.open("a") as f:
            json.dump(entry, f)
            f.write("\n")

    def write_results(self, results: dict[str, Any]) -> None:
        """Write final results.

        Args:
            results: Results to write
        """
        with self.results_path.open("w") as f:
            json.dump(results, f, indent=2)


class CorruptionSeverity(Enum):
    """Severity levels for detected corruption."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CorruptionAnalysis:
    """Results of corruption analysis.

    Attributes:
        is_corrupt: Whether definitive corruption was detected
        needs_deep_scan: Whether file needs deeper analysis
        error_message: Human-readable error description
        confidence: Confidence level (0.0-1.0)
        detected_issues: List of specific issues found
        severity: Overall corruption severity level
        suggested_action: Recommended action based on analysis
    """

    is_corrupt: bool = False
    needs_deep_scan: bool = False
    error_message: str = ""
    confidence: float = 0.0
    detected_issues: list[str] = field(default_factory=list)
    severity: CorruptionSeverity = CorruptionSeverity.NONE
    suggested_action: str = ""

    def __post_init__(self: CorruptionAnalysis) -> None:
        """Set suggested action based on analysis results."""
        if not self.suggested_action:
            self.suggested_action = self._determine_suggested_action()

    def _determine_suggested_action(self: CorruptionAnalysis) -> str:
        """Determine suggested action based on corruption analysis."""
        if self.is_corrupt:
            if self.severity == CorruptionSeverity.CRITICAL:
                return "File is severely corrupted and should be deleted or restored from backup"
            if self.severity == CorruptionSeverity.HIGH:
                return "File has significant corruption and may be unusable"
            return "File has corruption but may still be playable"
        if self.needs_deep_scan:
            return "Run deep scan to determine if file is corrupt"
        return "File appears to be healthy"


class Inspector:
    """Inspector for analyzing video file health using FFmpegClient."""

    def __init__(self: Inspector, ffmpeg_client: Any) -> None:
        self.ffmpeg_client: Any = ffmpeg_client

    def inspect_quick(self: Inspector, video_file: Any) -> CorruptionAnalysis:
        """Perform quick inspection using FFmpegClient."""
        scan_result: Any = self.ffmpeg_client.inspect_quick(video_file)
        return self._analyze_scan_result(scan_result)

    def inspect_deep(self: Inspector, video_file: Any) -> CorruptionAnalysis:
        """Perform deep inspection using FFmpegClient."""
        scan_result: Any = self.ffmpeg_client.inspect_deep(video_file)
        return self._analyze_scan_result(scan_result)

    def _analyze_scan_result(self: Inspector, scan_result: Any) -> CorruptionAnalysis:
        """Convert ScanResult to CorruptionAnalysis."""
        severity: CorruptionSeverity = CorruptionSeverity.NONE
        if scan_result.is_corrupt:
            if scan_result.confidence > 0.8:
                severity = CorruptionSeverity.CRITICAL
            elif scan_result.confidence > 0.5:
                severity = CorruptionSeverity.HIGH
            elif scan_result.confidence > 0.2:
                severity = CorruptionSeverity.MEDIUM
            else:
                severity = CorruptionSeverity.LOW

        return CorruptionAnalysis(
            is_corrupt=scan_result.is_corrupt,
            needs_deep_scan=scan_result.needs_deep_scan,
            error_message=scan_result.error_message,
            confidence=scan_result.confidence,
            detected_issues=[],
            severity=severity,
            suggested_action="",
        )
