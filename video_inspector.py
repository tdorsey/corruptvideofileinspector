"""
Video inspection functionality using FFmpeg with hybrid detection mode
"""

import hashlib
import json
import logging
import os
import signal
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Configure module logger
logger = logging.getLogger(__name__)

# Global progress tracking for signal handlers
_current_progress = {
    "current_file": "",
    "total_files": 0,
    "processed_count": 0,
    "corrupt_count": 0,
    "remaining_count": 0,
    "scan_mode": "unknown",
    "start_time": 0.0,
}


class ProgressReporter:
    """Handles progress reporting and signal management"""

    def __init__(self, total_files: int, scan_mode: str):
        self.total_files = total_files
        self.scan_mode = scan_mode
        self.processed_count = 0
        self.corrupt_count = 0
        self.current_file = ""
        self.start_time = time.time()

        # Update global progress for signal handlers
        global _current_progress
        _current_progress.update(
            {"total_files": total_files, "scan_mode": scan_mode, "start_time": self.start_time}
        )

    def update(
        self, current_file: str = "", processed_count: int = None, corrupt_count: int = None
    ):
        """Update progress counters"""
        if current_file:
            self.current_file = current_file
        if processed_count is not None:
            self.processed_count = processed_count
        if corrupt_count is not None:
            self.corrupt_count = corrupt_count

        # Update global progress for signal handlers
        global _current_progress
        _current_progress.update(
            {
                "current_file": self.current_file,
                "processed_count": self.processed_count,
                "corrupt_count": self.corrupt_count,
                "remaining_count": self.total_files - self.processed_count,
            }
        )

    def report_progress(self, force_output: bool = False):
        """Report current progress"""
        elapsed_time = time.time() - self.start_time
        remaining = self.total_files - self.processed_count
        healthy = self.processed_count - self.corrupt_count

        if force_output:
            print(f"\n{'='*60}")
            print("PROGRESS REPORT")
            print(f"{'='*60}")
            print(f"Scan Mode: {self.scan_mode.upper()}")
            print(f"Current File: {Path(self.current_file).name if self.current_file else 'None'}")
            print(f"Files Processed: {self.processed_count}/{self.total_files}")
            print(f"Corrupt Files Found: {self.corrupt_count}")
            print(f"Healthy Files: {healthy}")
            print(f"Files Remaining: {remaining}")
            print(f"Elapsed Time: {elapsed_time:.1f} seconds")
            if self.processed_count > 0:
                avg_time = elapsed_time / self.processed_count
                estimated_remaining = avg_time * remaining
                print(f"Estimated Time Remaining: {estimated_remaining:.1f} seconds")
            print(f"{'='*60}")

        logger.info(
            f"Progress: {self.processed_count}/{self.total_files}, "
            f"corrupt: {self.corrupt_count}, remaining: {remaining}"
        )


def signal_handler(signum, frame):
    """Handle POSIX signals and report progress"""
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name} ({signum}), reporting progress")

    # Create a temporary progress reporter from global state
    progress = _current_progress
    elapsed_time = time.time() - progress["start_time"]
    remaining = progress["total_files"] - progress["processed_count"]
    healthy = progress["processed_count"] - progress["corrupt_count"]

    print(f"\n{'='*60}")
    print(f"PROGRESS REPORT (Signal {signal_name})")
    print(f"{'='*60}")
    print(f"Scan Mode: {progress['scan_mode'].upper()}")
    print(
        f"Current File: {Path(progress['current_file']).name if progress['current_file'] else 'None'}"
    )
    print(f"Files Processed: {progress['processed_count']}/{progress['total_files']}")
    print(f"Corrupt Files Found: {progress['corrupt_count']}")
    print(f"Healthy Files: {healthy}")
    print(f"Files Remaining: {remaining}")
    print(f"Elapsed Time: {elapsed_time:.1f} seconds")
    if progress["processed_count"] > 0:
        avg_time = elapsed_time / progress["processed_count"]
        estimated_remaining = avg_time * remaining
        print(f"Estimated Time Remaining: {estimated_remaining:.1f} seconds")
    print(f"{'='*60}")


def setup_signal_handlers():
    """Setup signal handlers for progress reporting"""
    try:
        # Handle common POSIX signals
        signal.signal(signal.SIGUSR1, signal_handler)
        signal.signal(signal.SIGUSR2, signal_handler)
        # Also handle SIGTERM for graceful progress reporting before termination
        original_sigterm = signal.signal(signal.SIGTERM, signal_handler)
        logger.info("Signal handlers registered for SIGUSR1, SIGUSR2, and SIGTERM")
        return original_sigterm
    except (AttributeError, OSError) as e:
        # Some signals might not be available on all platforms
        logger.warning(f"Could not setup all signal handlers: {e}")
        return None


class ScanMode(Enum):
    """Scan modes for video inspection"""

    QUICK = "quick"
    DEEP = "deep"
    HYBRID = "hybrid"


@dataclass
class VideoFile:
    """
    Represents a video file with its properties.

    Attributes:
        filename: Path to the video file
        size: File size in bytes
        duration: Video duration in seconds
    """

    filename: str
    size: int = 0
    duration: float = 0.0

    def __post_init__(self) -> None:
        """Initialize file size if file exists."""
        if os.path.exists(self.filename):
            self.size = os.path.getsize(self.filename)
            logger.debug(f"VideoFile created: {self.filename} ({self.size} bytes)")


class VideoInspectionResult:
    """
    Results of video file inspection.

    Attributes:
        filename: Path to the inspected video file
        is_corrupt: Whether the file is determined to be corrupt
        error_message: Description of any errors found
        ffmpeg_output: Raw output from ffmpeg
        inspection_time: Time taken for inspection in seconds
        file_size: Size of the file in bytes
        scan_mode: Mode used for scanning
        needs_deep_scan: Whether file needs deeper analysis
        deep_scan_completed: Whether deep scan was performed
    """

    def __init__(self, filename: str):
        """
        Initialize inspection result.

        Args:
            filename: Path to the video file
        """
        self.filename = filename
        self.is_corrupt = False
        self.error_message = ""
        self.ffmpeg_output = ""
        self.inspection_time = 0.0
        self.file_size = 0
        self.scan_mode = ScanMode.QUICK
        self.needs_deep_scan = False
        self.deep_scan_completed = False
        logger.debug(f"VideoInspectionResult initialized for: {filename}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary for JSON output.

        Returns:
            Dict[str, Any]: Dictionary representation of the result
        """
        return {
            "filename": self.filename,
            "is_corrupt": self.is_corrupt,
            "error_message": self.error_message,
            "inspection_time": self.inspection_time,
            "file_size": self.file_size,
            "scan_mode": self.scan_mode.value,
            "needs_deep_scan": self.needs_deep_scan,
            "deep_scan_completed": self.deep_scan_completed,
        }


@dataclass
class WALEntry:
    """Write-ahead log entry for tracking scan progress"""

    filename: str
    result: Dict[str, Any]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {"filename": self.filename, "result": self.result, "timestamp": self.timestamp}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WALEntry":
        return cls(filename=data["filename"], result=data["result"], timestamp=data["timestamp"])


class WriteAheadLog:
    """Write-ahead log for resuming interrupted directory scans"""

    def __init__(self, directory: str, scan_mode: ScanMode, extensions: Optional[List[str]] = None):
        self.directory = directory
        self.scan_mode = scan_mode
        # Use the same default extensions as get_all_video_object_files
        if extensions is None:
            self.extensions = [
                ".mp4",
                ".avi",
                ".mkv",
                ".mov",
                ".wmv",
                ".flv",
                ".webm",
                ".m4v",
                ".mpg",
                ".mpeg",
            ]
        else:
            self.extensions = extensions

        # Generate unique WAL filename based on directory and scan parameters
        dir_hash = hashlib.md5(directory.encode()).hexdigest()[:8]
        mode_hash = hashlib.md5(
            f"{scan_mode.value}-{'-'.join(sorted(self.extensions))}".encode()
        ).hexdigest()[:8]
        wal_filename = f"corrupt_video_inspector_wal_{dir_hash}_{mode_hash}.json"
        results_filename = f"corrupt_video_inspector_results_{dir_hash}_{mode_hash}.json"

        self.wal_path = Path(tempfile.gettempdir()) / wal_filename
        self.results_path = Path(tempfile.gettempdir()) / results_filename
        self.lock = threading.Lock()
        self.processed_files: Set[str] = set()
        self.results: List[WALEntry] = []

        logger.debug(f"WAL file: {self.wal_path}")
        logger.debug(f"Results file: {self.results_path}")

    def load_existing_wal(self) -> bool:
        """Load existing WAL file if it exists. Returns True if resuming."""
        if not self.wal_path.exists():
            return False

        try:
            with open(self.wal_path, "r") as f:
                data = json.load(f)

            # Verify WAL is for the same directory and scan mode
            if (
                data.get("directory") != self.directory
                or data.get("scan_mode") != self.scan_mode.value
                or data.get("extensions") != sorted(self.extensions)
            ):
                # Different scan parameters, ignore existing WAL
                return False

            # Load processed entries
            for entry_data in data.get("entries", []):
                entry = WALEntry.from_dict(entry_data)
                self.results.append(entry)
                self.processed_files.add(entry.filename)

            return True

        except (json.JSONDecodeError, KeyError, Exception):
            # Corrupted WAL file, start fresh
            return False

    def create_wal_file(self) -> None:
        """Create a new WAL file with metadata"""
        wal_data = {
            "directory": self.directory,
            "scan_mode": self.scan_mode.value,
            "extensions": sorted(self.extensions),
            "created_at": time.time(),
            "entries": [],
        }

        with self.lock:
            try:
                with open(self.wal_path, "w") as f:
                    json.dump(wal_data, f, indent=2)
            except Exception as e:
                # If we can't create WAL file, continue without it
                logger.warning(f"Could not create WAL file: {e}")

    def append_result(self, result: VideoInspectionResult) -> None:
        """Append a scan result to both WAL and results files"""
        entry = WALEntry(filename=result.filename, result=result.to_dict(), timestamp=time.time())

        with self.lock:
            self.results.append(entry)
            self.processed_files.add(result.filename)

            try:
                # Update WAL file
                if self.wal_path.exists():
                    with open(self.wal_path, "r") as f:
                        wal_data = json.load(f)
                else:
                    wal_data = {
                        "directory": self.directory,
                        "scan_mode": self.scan_mode.value,
                        "extensions": sorted(self.extensions),
                        "created_at": time.time(),
                        "entries": [],
                    }

                # Append new entry to WAL
                wal_data["entries"].append(entry.to_dict())

                # Write back to WAL file
                with open(self.wal_path, "w") as f:
                    json.dump(wal_data, f, indent=2)

                # Update durable results file
                self._update_results_file(result)

            except Exception as e:
                # If we can't write to WAL file, continue without it
                logger.warning(f"Could not update WAL file: {e}")

    def _update_results_file(self, result: VideoInspectionResult) -> None:
        """Update the durable results file with a new result"""
        try:
            # Load existing results file if it exists
            if self.results_path.exists():
                with open(self.results_path, "r") as f:
                    results_data = json.load(f)
            else:
                results_data = {
                    "directory": self.directory,
                    "scan_mode": self.scan_mode.value,
                    "extensions": sorted(self.extensions),
                    "created_at": time.time(),
                    "last_updated": time.time(),
                    "results": [],
                }

            # Update metadata
            results_data["last_updated"] = time.time()

            # Add new result (avoid duplicates)
            result_dict = result.to_dict()
            result_dict["timestamp"] = time.time()

            # Remove any existing result for this file
            results_data["results"] = [
                r for r in results_data["results"] if r.get("filename") != result.filename
            ]

            # Add the new result
            results_data["results"].append(result_dict)

            # Write back to results file
            with open(self.results_path, "w") as f:
                json.dump(results_data, f, indent=2)

        except Exception as e:
            logger.warning(f"Could not update results file: {e}")

    def is_processed(self, filename: str) -> bool:
        """Check if a file has already been processed"""
        return filename in self.processed_files

    def get_completed_results(self) -> List[VideoInspectionResult]:
        """Get all completed results from WAL"""
        results = []
        for entry in self.results:
            # Reconstruct VideoInspectionResult from stored data
            result = VideoInspectionResult(entry.filename)
            data = entry.result
            result.is_corrupt = data.get("is_corrupt", False)
            result.error_message = data.get("error_message", "")
            result.inspection_time = data.get("inspection_time", 0.0)
            result.file_size = data.get("file_size", 0)
            result.scan_mode = ScanMode(data.get("scan_mode", "quick"))
            result.needs_deep_scan = data.get("needs_deep_scan", False)
            result.deep_scan_completed = data.get("deep_scan_completed", False)
            results.append(result)
        return results

    def cleanup(self) -> None:
        """Remove the WAL and results files after successful completion"""
        try:
            if self.wal_path.exists():
                self.wal_path.unlink()
                logger.info(f"Removed WAL file: {self.wal_path}")
        except Exception as e:
            logger.warning(f"Could not remove WAL file: {e}")

        # Keep the results file as it's a durable record
        # Only remove it if explicitly requested
        logger.info(f"Results file preserved: {self.results_path}")

    def get_resume_info(self) -> Dict[str, Any]:
        """Get information about what can be resumed"""
        return {
            "total_completed": len(self.results),
            "wal_file": str(self.wal_path),
            "results_file": str(self.results_path),
            "last_processed": self.results[-1].timestamp if self.results else None,
        }


def get_ffmpeg_command() -> Optional[str]:
    """
    Find ffmpeg command on system.

    Returns:
        Optional[str]: Path to ffmpeg command if found, None otherwise
    """
    logger.debug("Searching for ffmpeg command")
    for cmd in ["ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        try:
            logger.debug(f"Trying ffmpeg command: {cmd}")
            subprocess.run([cmd, "-version"], capture_output=True, check=True, timeout=5)
            logger.info(f"Found ffmpeg command: {cmd}")
            return cmd
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.debug(f"Failed to find ffmpeg at {cmd}: {e}")
            continue

    logger.warning("ffmpeg command not found")
    return None


def get_all_video_object_files(
    directory: str, recursive: bool = True, extensions: Optional[List[str]] = None
) -> List[VideoFile]:
    """
    Get all video files in directory as VideoFile objects.

    Args:
        directory: Path to directory to scan
        recursive: Whether to scan subdirectories recursively
        extensions: List of file extensions to include

    Returns:
        List[VideoFile]: List of VideoFile objects found
    """
    if extensions is None:
        extensions = [
            ".mp4",
            ".avi",
            ".mkv",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".m4v",
            ".mpg",
            ".mpeg",
        ]

    logger.debug(f"Scanning for video files in {directory}, recursive={recursive}")
    logger.debug(f"Looking for extensions: {extensions}")

    ext_set = {ext.lower() for ext in extensions}
    video_files = []

    path = Path(directory)

    pattern = "**/*" if recursive else "*"

    for file_path in path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in ext_set:
            video_file = VideoFile(str(file_path))
            video_files.append(video_file)
            logger.debug(f"Found video file: {file_path}")

    result = sorted(video_files, key=lambda x: x.filename)
    logger.info(f"Found {len(result)} video files in {directory}")
    return result


def inspect_single_video_quick(
    video_file: VideoFile, ffmpeg_cmd: str, verbose: bool = False
) -> VideoInspectionResult:
    """
    Quick inspection of a single video file (1 minute timeout).

    Args:
        video_file: VideoFile object to inspect
        ffmpeg_cmd: Path to ffmpeg command
        verbose: Whether to enable verbose output

    Returns:
        VideoInspectionResult: Results of the inspection
    """
    result = VideoInspectionResult(video_file.filename)
    result.file_size = video_file.size
    result.scan_mode = ScanMode.QUICK

    logger.debug(f"Starting quick scan of {video_file.filename}")
    start_time = time.time()

    try:
        # Quick scan - just check file headers and basic structure
        cmd = [
            ffmpeg_cmd,
            "-v",
            "error",
            "-i",
            video_file.filename,
            "-t",
            "10",  # Only process first 10 seconds for quick check
            "-f",
            "null",
            "-",
        ]

        logger.debug(f"Running ffmpeg command: {' '.join(cmd)}")
        process = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout for quick scan
        )

        result.ffmpeg_output = process.stderr
        logger.debug(f"FFmpeg exit code: {process.returncode}")

        # Quick corruption indicators
        quick_error_indicators = [
            "Invalid data found",
            "Error while decoding",
            "corrupt",
            "damaged",
            "incomplete",
            "truncated",
            "malformed",
            "moov atom not found",
            "Invalid NAL unit size",
        ]

        # Warning indicators that suggest need for deeper scan
        warning_indicators = [
            "Non-monotonous DTS",
            "PTS discontinuity",
            "Frame rate very high",
            "DTS out of order",
            "B-frame after EOS",
        ]

        if process.returncode != 0:
            stderr_lower = process.stderr.lower()

            # Check for definitive corruption
            if any(indicator in stderr_lower for indicator in quick_error_indicators):
                result.is_corrupt = True
                result.error_message = "Video file appears to be corrupt (quick scan)"
                logger.warning(f"Quick scan detected corruption in {video_file.filename}")
            # Check for warning signs that need deeper analysis
            elif any(indicator in stderr_lower for indicator in warning_indicators):
                result.needs_deep_scan = True
                result.error_message = "Potential issues detected - needs deep scan"
                logger.info(f"Quick scan flagged {video_file.filename} for deep scan")
            else:
                result.needs_deep_scan = True
                result.error_message = (
                    f"FFmpeg returned error code {process.returncode} - needs verification"
                )
                logger.info(f"Quick scan inconclusive for {video_file.filename}, needs deep scan")
        else:
            logger.debug(f"Quick scan completed successfully for {video_file.filename}")

    except subprocess.TimeoutExpired:
        result.needs_deep_scan = True
        result.error_message = "Quick scan timed out - needs deep scan"
        logger.warning(f"Quick scan timed out for {video_file.filename}")
    except Exception as e:
        result.needs_deep_scan = True
        result.error_message = f"Quick scan failed: {e!s} - needs deep scan"
        logger.exception(f"Quick scan failed for {video_file.filename}")

    result.inspection_time = time.time() - start_time

    if verbose:
        if result.is_corrupt:
            status = "CORRUPT"
        elif result.needs_deep_scan:
            status = "NEEDS_DEEP_SCAN"
        else:
            status = "OK"
        logger.debug(
            f"Quick scan result: [QUICK-{status}] {Path(video_file.filename).name} ({result.inspection_time:.2f}s)"
        )
        print(
            f"  [QUICK-{status}] {Path(video_file.filename).name} ({result.inspection_time:.2f}s)"
        )

    logger.debug(f"Quick scan completed for {video_file.filename} in {result.inspection_time:.2f}s")
    return result


def inspect_single_video_deep(
    video_file: VideoFile, ffmpeg_cmd: str, verbose: bool = False
) -> VideoInspectionResult:
    """
    Deep inspection of a single video file (full file analysis).

    Args:
        video_file: VideoFile object to inspect
        ffmpeg_cmd: Path to ffmpeg command
        verbose: Whether to enable verbose output

    Returns:
        VideoInspectionResult: Results of the inspection
    """
    result = VideoInspectionResult(video_file.filename)
    result.file_size = video_file.size
    result.scan_mode = ScanMode.DEEP
    result.deep_scan_completed = True

    logger.debug(f"Starting deep scan of {video_file.filename}")
    start_time = time.time()

    try:
        # Deep scan - analyze entire file
        cmd = [ffmpeg_cmd, "-v", "error", "-i", video_file.filename, "-f", "null", "-"]

        logger.debug(f"Running ffmpeg deep scan command: {' '.join(cmd)}")
        process = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=900,  # 15 minute timeout for deep scan
        )

        result.ffmpeg_output = process.stderr
        logger.debug(f"Deep scan ffmpeg exit code: {process.returncode}")

        # All error indicators for deep scan
        error_indicators = [
            "Invalid data found",
            "Error while decoding",
            "corrupt",
            "damaged",
            "incomplete",
            "truncated",
            "malformed",
            "moov atom not found",
            "Invalid NAL unit size",
            "decode_slice_header error",
            "concealing errors",
            "missing reference picture",
        ]

        if process.returncode != 0:
            stderr_lower = process.stderr.lower()
            if any(indicator in stderr_lower for indicator in error_indicators):
                result.is_corrupt = True
                result.error_message = "Video file is corrupt (deep scan confirmed)"
                logger.error(f"Deep scan confirmed corruption in {video_file.filename}")
            else:
                result.error_message = (
                    f"FFmpeg exited with code {process.returncode}: {process.stderr}"
                )
                logger.warning(f"Deep scan completed with warnings for {video_file.filename}")
        else:
            logger.debug(f"Deep scan completed successfully for {video_file.filename}")

    except subprocess.TimeoutExpired:
        result.is_corrupt = True
        result.error_message = "Deep scan timed out - file may be severely corrupted"
        logger.exception(f"Deep scan timed out for {video_file.filename}")
    except Exception as e:
        result.error_message = f"Deep scan failed: {e!s}"
        logger.exception(f"Deep scan failed for {video_file.filename}")

    result.inspection_time = time.time() - start_time

    if verbose:
        status = "CORRUPT" if result.is_corrupt else "OK"
        status_msg = (
            f"[DEEP-{status}] {Path(video_file.filename).name} ({result.inspection_time:.2f}s)"
        )
        logger.debug(f"Deep scan result: {status_msg}")
        print(f"  {status_msg}")

    logger.debug(f"Deep scan completed for {video_file.filename} in {result.inspection_time:.2f}s")
    return result


def inspect_single_video(
    video_file: VideoFile,
    ffmpeg_cmd: str,
    verbose: bool = False,
    scan_mode: ScanMode = ScanMode.QUICK,
) -> VideoInspectionResult:
    """
    Inspect a single video file based on scan mode.

    Args:
        video_file: VideoFile object to inspect
        ffmpeg_cmd: Path to ffmpeg command
        verbose: Whether to enable verbose output
        scan_mode: Mode of scanning to use

    Returns:
        VideoInspectionResult: Results of the inspection
    """
    logger.debug(f"Inspecting {video_file.filename} with {scan_mode.value} mode")

    if scan_mode == ScanMode.QUICK:
        return inspect_single_video_quick(video_file, ffmpeg_cmd, verbose)
    if scan_mode == ScanMode.DEEP:
        return inspect_single_video_deep(video_file, ffmpeg_cmd, verbose)
    # For hybrid mode, start with quick scan
    return inspect_single_video_quick(video_file, ffmpeg_cmd, verbose)


def inspect_video_files_cli(
    directory: str,
    resume: bool = True,
    verbose: bool = False,
    json_output: bool = False,
    output_file: Optional[str] = None,
    recursive: bool = True,
    extensions: Optional[List[str]] = None,
    max_workers: int = 4,
    scan_mode: ScanMode = ScanMode.HYBRID,
) -> None:
    """
    CLI interface for video inspection with hybrid detection mode.

    Args:
        directory: Directory to scan for video files
        resume: Whether to resume from previous scan
        verbose: Enable verbose output
        json_output: Generate JSON output file
        output_file: Custom output file path
        recursive: Scan subdirectories recursively
        extensions: List of file extensions to scan
        max_workers: Number of worker threads
        scan_mode: Scanning mode to use

    Raises:
        RuntimeError: If ffmpeg is not found
    """

    logger.info(f"Starting video inspection in {directory}")
    logger.info(f"Scan mode: {scan_mode.value}, workers: {max_workers}, recursive: {recursive}")

    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        logger.critical("FFmpeg not found - cannot proceed")
        raise RuntimeError("FFmpeg not found")

    # Initialize Write-Ahead Log for resume functionality
    wal = None
    resuming_scan = False
    if resume:
        wal = WriteAheadLog(directory, scan_mode, extensions)
        resuming_scan = wal.load_existing_wal()
        if resuming_scan:
            logger.info(
                f"Resuming scan from previous session with {len(wal.results)} already processed files"
            )
            logger.info(f"Resuming scan from WAL with {len(wal.results)} completed files")
        else:
            wal.create_wal_file()
            logger.info("Created new WAL file for this scan")

    # Get video files
    video_files = get_all_video_object_files(directory, recursive, extensions)
    total_files = len(video_files)

    if total_files == 0:
        logger.warning("No video files found to inspect")
        print("No video files found to inspect")
        return

    logger.info(f"Found {total_files} video files to inspect")
    print(f"Found {total_files} video files to inspect")
    logger.info(f"Scan mode: {scan_mode.value.upper()}")
    print(f"Scan mode: {scan_mode.value.upper()}")
    logger.info(f"Using {max_workers} worker threads")
    print(f"Using {max_workers} worker threads")

    # Setup signal handlers for progress reporting
    original_sigterm = setup_signal_handlers()

    # Initialize progress reporter
    progress_reporter = ProgressReporter(total_files, scan_mode.value)

    # Load completed results from WAL if resuming
    results = []
    corrupt_count = 0
    processed_count = 0
    deep_scan_needed = 0

    if resuming_scan and wal:
        results = wal.get_completed_results()
        processed_count = len(results)
        corrupt_count = sum(1 for r in results if r.is_corrupt)
        deep_scan_needed = sum(
            1
            for r in results
            if r.needs_deep_scan and not r.is_corrupt and not r.deep_scan_completed
        )

        # Filter out already processed files
        video_files = [vf for vf in video_files if not wal.is_processed(vf.filename)]
        remaining_files = len(video_files)

        logger.info(
            f"Resume: Already processed {processed_count} files, {remaining_files} remaining"
        )
        logger.info(f"Resume: {processed_count} already processed, {remaining_files} remaining")

    files_to_process = len(video_files)

    # Progress tracking
    def update_progress(phase=""):
        if not verbose:
            percent = (processed_count / total_files) * 100
            print(
                f"\r{phase}Progress: {processed_count}/{total_files} ({percent:.1f}%)",
                end="",
                flush=True,
            )

    start_time = time.time()
    logger.info(f"Starting scan at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Phase 1: Quick scan (for HYBRID mode) or single scan (for QUICK/DEEP modes)
        if scan_mode == ScanMode.HYBRID:
            logger.info("Starting Phase 1: Quick scan")
            print("\n=== PHASE 1: QUICK SCAN ===")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks for first phase
            future_to_video = {
                executor.submit(
                    inspect_single_video,
                    video,
                    ffmpeg_cmd,
                    verbose,
                    ScanMode.QUICK if scan_mode == ScanMode.HYBRID else scan_mode,
                ): video
                for video in video_files
            }

            logger.debug(f"Submitted {len(future_to_video)} inspection tasks")

            # Process completed tasks
            for future in future_to_video:
                try:
                    result = future.result()
                    results.append(result)

                    # Update WAL with new result
                    if wal:
                        wal.append_result(result)

                    if result.is_corrupt:
                        corrupt_count += 1
                        logger.warning(f"Corrupt file found: {result.filename}")
                        if not verbose:
                            print(f"\nCORRUPT: {Path(result.filename).name}")
                    elif result.needs_deep_scan:
                        deep_scan_needed += 1
                        logger.info(f"File needs deep scan: {result.filename}")
                        if not verbose and scan_mode == ScanMode.HYBRID:
                            print(f"\nNEEDS DEEP SCAN: {Path(result.filename).name}")

                    processed_count += 1

                    # Update progress reporter
                    progress_reporter.update(
                        current_file=result.filename,
                        processed_count=processed_count,
                        corrupt_count=corrupt_count,
                    )

                    # Update progress display
                    phase_label = "Quick Scan " if scan_mode == ScanMode.HYBRID else ""
                    update_progress(phase_label)

                except Exception as e:
                    logger.exception(f"Error processing file: {e}")
                    processed_count += 1

                    # Update progress reporter for error case
                    progress_reporter.update(
                        processed_count=processed_count, corrupt_count=corrupt_count
                    )
                    update_progress()

        # Phase 2: Deep scan for flagged files (HYBRID mode only)
        if scan_mode == ScanMode.HYBRID and deep_scan_needed > 0:
            logger.info(f"Starting Phase 2: Deep scan for {deep_scan_needed} files")
            print(f"\n\n=== PHASE 2: DEEP SCAN ({deep_scan_needed} files) ===")

            # Get files that need deep scanning (including those from resumed session)
            files_for_deep_scan = []
            for i, result in enumerate(results):
                if (
                    result.needs_deep_scan
                    and not result.is_corrupt
                    and not result.deep_scan_completed
                ):
                    # Find the corresponding video file
                    video_file = None
                    for vf in get_all_video_object_files(directory, recursive, extensions):
                        if vf.filename == result.filename:
                            video_file = vf
                            break
                    if video_file:
                        files_for_deep_scan.append((video_file, result, i))

            processed_deep = 0

            def update_deep_progress():
                if not verbose:
                    percent = (processed_deep / deep_scan_needed) * 100
                    print(
                        f"\rDeep Scan Progress: {processed_deep}/{deep_scan_needed} ({percent:.1f}%)",
                        end="",
                        flush=True,
                    )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit deep scan tasks
                future_to_index = {}
                for video_file, old_result, result_index in files_for_deep_scan:
                    future = executor.submit(
                        inspect_single_video_deep, video_file, ffmpeg_cmd, verbose
                    )
                    future_to_index[future] = result_index

                logger.debug(f"Submitted {len(future_to_index)} deep scan tasks")

                # Process deep scan results
                for future, original_index in future_to_index.items():
                    try:
                        deep_result = future.result()
                        result_index = future_to_index[future]

                        # Update the original result with deep scan findings
                        results[result_index] = deep_result

                        # Update WAL with deep scan result
                        if wal:
                            wal.append_result(deep_result)

                        if deep_result.is_corrupt:
                            corrupt_count += 1
                            logger.warning(
                                f"Deep scan confirmed corruption: {deep_result.filename}"
                            )
                            if not verbose:
                                print(f"\nDEEP SCAN CORRUPT: {Path(deep_result.filename).name}")
                        else:
                            logger.info(f"Deep scan cleared: {deep_result.filename}")

                        processed_deep += 1

                        # Update progress reporter for deep scan
                        progress_reporter.update(
                            current_file=deep_result.filename, corrupt_count=corrupt_count
                        )

                        update_deep_progress()

                    except Exception as e:
                        logger.exception(f"Error in deep scan: {e}")
                        processed_deep += 1

                        # Update progress reporter for deep scan error
                        progress_reporter.update(corrupt_count=corrupt_count)

                        update_deep_progress()

    except KeyboardInterrupt:
        logger.warning(
            f"Scan interrupted by user after processing {processed_count}/{total_files} files"
        )
        print(
            f"\n\nScan interrupted by user after processing {processed_count}/{total_files} files"
        )
        if wal:
            logger.info(f"Progress saved to WAL file: {wal.wal_path}")
            print(f"Progress saved to WAL file. Use same command to resume from: {wal.wal_path}")
        raise  # Re-raise to maintain exit code

    total_time = time.time() - start_time
    logger.info(f"Scan completed in {total_time:.2f} seconds")

    if not verbose:
        print()  # New line after progress

    # Clean up WAL file on successful completion
    if wal:
        wal.cleanup()

    # Print summary
    logger.info("Scan completed - generating summary")
    print("\n" + "=" * 50)
    print("SCAN COMPLETE")
    print("=" * 50)
    logger.info(f"Scan mode: {scan_mode.value.upper()}")
    print(f"Scan mode: {scan_mode.value.upper()}")
    logger.info(f"Total files scanned: {processed_count}")
    print(f"Total files scanned: {processed_count}")
    logger.info(f"Corrupt files found: {corrupt_count}")
    print(f"Corrupt files found: {corrupt_count}")
    healthy_count = processed_count - corrupt_count
    logger.info(f"Healthy files: {healthy_count}")
    print(f"Healthy files: {healthy_count}")
    if scan_mode == ScanMode.HYBRID:
        logger.info(f"Files requiring deep scan: {deep_scan_needed}")
        print(f"Files requiring deep scan: {deep_scan_needed}")
    logger.info(f"Total scan time: {total_time:.2f} seconds")
    print(f"Total scan time: {total_time:.2f} seconds")
    avg_time = total_time / processed_count if processed_count > 0 else 0
    logger.info(f"Average time per file: {avg_time:.2f} seconds")
    print(f"Average time per file: {avg_time:.2f} seconds")

    logger.info(
        f"Scan summary - Total: {processed_count}, Corrupt: {corrupt_count}, "
        f"Healthy: {processed_count - corrupt_count}, Time: {total_time:.2f}s"
    )

    # Show corrupt files
    if corrupt_count > 0:
        logger.warning(f"Found {corrupt_count} corrupt files")
        print("\nCORRUPT FILES:")
        for result in results:
            if result.is_corrupt:
                scan_type = (
                    f" ({result.scan_mode.value} scan)" if scan_mode == ScanMode.HYBRID else ""
                )
                print(f"  - {result.filename}{scan_type}")
                logger.error(f"Corrupt file: {result.filename}")
                if result.error_message and verbose:
                    print(f"    Error: {result.error_message}")
    else:
        logger.info("No corrupt files found")

    # Generate JSON output if requested
    if json_output:
        output_path = output_file or str(Path(directory) / "corruption_scan_results.json")

        logger.info(f"Generating JSON output to {output_path}")
        json_data = {
            "scan_summary": {
                "total_files": processed_count,
                "corrupt_files": corrupt_count,
                "healthy_files": processed_count - corrupt_count,
                "deep_scans_needed": deep_scan_needed if scan_mode == ScanMode.HYBRID else 0,
                "scan_mode": scan_mode.value,
                "scan_time": total_time,
                "directory": directory,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "resumed_scan": resuming_scan,
            },
            "results": [result.to_dict() for result in results],
        }

        try:
            with Path(output_path).open("w") as f:
                json.dump(json_data, f, indent=2)
            logger.info(f"JSON results saved successfully to {output_path}")
            print(f"\nDetailed results saved to: {output_path}")
        except Exception as e:
            logger.exception(f"Could not save JSON results: {e}")

    logger.info("Video inspection process completed")
