"""
Interface-agnostic video scanning service with dependency injection.

This service provides the core video scanning functionality while being
completely decoupled from any specific presentation layer (CLI, web, GUI).
It uses dependency injection to receive configuration and output handlers.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from src.interfaces.base import ConfigurationProvider, ProgressReporter, ResultHandler
    from src.core.models.inspection import VideoFile
    from src.core.models.scanning import ScanMode, ScanProgress, ScanResult, ScanSummary

logger = logging.getLogger(__name__)


class VideoScanService:
    """
    Interface-agnostic video scanning service.
    
    This class provides the core video scanning functionality using dependency
    injection to receive configuration and output handling. It can be used by
    any presentation layer (CLI, web API, GUI) without modification.
    """

    def __init__(
        self,
        config_provider: "ConfigurationProvider",
        result_handler: "ResultHandler",
        progress_reporter: "ProgressReporter | None" = None,
    ):
        """Initialize the video scan service.
        
        Args:
            config_provider: Interface for accessing configuration
            result_handler: Interface for handling scan results
            progress_reporter: Optional interface for progress reporting
        """
        self._config_provider = config_provider
        self._result_handler = result_handler
        self._progress_reporter = progress_reporter
        self._shutdown_requested = False
        
        logger.info("VideoScanService initialized with dependency injection")

    def scan_directory(self, directory: Path | None = None) -> "ScanSummary":
        """
        Scan a directory for corrupt video files.
        
        Uses the injected configuration provider to get scan parameters
        and the injected result handler to output results.
        
        Args:
            directory: Directory to scan (if None, uses config provider)
            
        Returns:
            Summary of the scan operation
        """
        from src.core.models.scanning import ScanSummary
        
        # Get configuration from provider
        scan_directory = directory or self._config_provider.get_scan_directory()
        scan_mode = self._config_provider.get_scan_mode()
        recursive = self._config_provider.get_recursive_scan()
        extensions = self._config_provider.get_file_extensions()
        
        logger.info("Starting directory scan: %s", scan_directory)
        logger.info("Scan mode: %s, recursive: %s", scan_mode.value, recursive)
        
        # Notify result handler of scan start
        video_files = self._find_video_files(scan_directory, recursive, extensions)
        total_files = len(video_files)
        
        if total_files == 0:
            logger.warning("No video files found to scan")
            summary = ScanSummary(
                directory=scan_directory,
                total_files=0,
                processed_files=0,
                corrupt_files=0,
                healthy_files=0,
                scan_mode=scan_mode,
                scan_time=0.0,
            )
            self._result_handler.handle_scan_complete(summary)
            return summary
        
        self._result_handler.handle_scan_start(total_files, scan_mode)
        
        # Perform the scan
        try:
            summary = self._perform_scan(video_files, scan_mode)
            self._result_handler.handle_scan_complete(summary)
            return summary
        except Exception as e:
            self._result_handler.handle_scan_error(e, {"directory": str(scan_directory)})
            raise

    def request_shutdown(self) -> None:
        """Request graceful shutdown of current scan operation."""
        logger.info("Shutdown requested")
        self._shutdown_requested = True

    @property
    def is_shutdown_requested(self) -> bool:
        """Check if graceful shutdown was requested."""
        return self._shutdown_requested

    def _find_video_files(
        self, 
        directory: Path, 
        recursive: bool, 
        extensions: list[str]
    ) -> list["VideoFile"]:
        """Find all video files in the directory."""
        from src.core.models.inspection import VideoFile
        
        logger.debug("Scanning for video files with extensions: %s", extensions)
        
        video_files: list[VideoFile] = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                video_files.append(VideoFile(path=file_path))
        
        return sorted(video_files, key=lambda x: x.path)

    def _perform_scan(self, video_files: list["VideoFile"], scan_mode: "ScanMode") -> "ScanSummary":
        """Perform the actual video file scanning."""
        from src.core.models.scanning import ScanProgress, ScanResult, ScanSummary
        from src.ffmpeg.corruption_detector import CorruptionDetector
        
        start_time = time.time()
        detector = CorruptionDetector()
        
        progress = ScanProgress(
            total_files=len(video_files),
            processed_count=0,
            corrupt_count=0,
            scan_mode=scan_mode.value,
        )
        
        for i, video_file in enumerate(video_files):
            if self._shutdown_requested:
                break
                
            if self._progress_reporter and self._progress_reporter.is_cancelled():
                break
            
            progress.processed_count = i + 1
            progress.current_file = str(video_file.path)
            
            # Report progress
            if self._progress_reporter:
                self._progress_reporter.report_progress(progress)
            self._result_handler.handle_progress_update(progress)
            
            # Scan the file
            try:
                result = self._scan_single_file(video_file, scan_mode, detector)
                if result.is_corrupt:
                    progress.corrupt_count += 1
                    
                self._result_handler.handle_file_result(result)
                
            except Exception as e:
                self._result_handler.handle_scan_error(e, {"file": str(video_file.path)})
                # Continue with next file
                continue
        
        # Create summary
        scan_time = time.time() - start_time
        summary = ScanSummary(
            directory=self._config_provider.get_scan_directory(),
            total_files=len(video_files),
            processed_files=progress.processed_count,
            corrupt_files=progress.corrupt_count,
            healthy_files=progress.processed_count - progress.corrupt_count,
            scan_mode=scan_mode,
            scan_time=scan_time,
        )
        
        logger.info(
            "Scan completed: %d files, %d corrupt, %.2fs",
            summary.processed_files,
            summary.corrupt_files,
            summary.scan_time,
        )
        
        return summary

    def _scan_single_file(
        self, 
        video_file: "VideoFile", 
        scan_mode: "ScanMode", 
        detector
    ) -> "ScanResult":
        """Scan a single video file for corruption."""
        import subprocess
        from src.core.models.scanning import ScanMode, ScanResult
        
        video_file_str = str(video_file.path)
        
        # Get timeout from configuration
        if scan_mode == ScanMode.QUICK:
            timeout = self._config_provider.get_timeout_quick()
            ffmpeg_cmd = [
                "ffmpeg", "-v", "error", "-t", "10", 
                "-i", video_file_str, "-f", "null", "-"
            ]
        else:
            timeout = self._config_provider.get_timeout_deep()
            ffmpeg_cmd = [
                "ffmpeg", "-v", "error", 
                "-i", video_file_str, "-f", "null", "-"
            ]
            if scan_mode == ScanMode.FULL:
                timeout = None  # No timeout for full scan
        
        try:
            proc = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            stderr = proc.stderr
            exit_code = proc.returncode
        except Exception as e:
            stderr = str(e)
            exit_code = 1
        
        # Analyze the FFmpeg output
        is_quick_scan = scan_mode == ScanMode.QUICK
        analysis = detector.analyze_ffmpeg_output(stderr, exit_code, is_quick_scan=is_quick_scan)
        
        return ScanResult(
            video_file=video_file,
            is_corrupt=analysis.is_corrupt,
            needs_deep_scan=analysis.needs_deep_scan,
            error_message=stderr if analysis.is_corrupt else "",
        )