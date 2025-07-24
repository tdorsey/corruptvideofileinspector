"""
Core video scanning service with support for different scan modes.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, List, Optional

from ..config.settings import AppConfig
from ..integrations.ffmpeg.client import FFmpegClient
from ..storage.wal import WriteAheadLog
from ..utils.progress import ProgressReporter
from ..utils.signals import SignalManager
from .models import ScanMode, ScanProgress, ScanResult, ScanSummary, VideoFile

logger = logging.getLogger(__name__)


class VideoScanner:
    """Core video scanning service."""

    def __init__(self, config: AppConfig):
        """Initialize the video scanner."""
        self.config = config
        self.ffmpeg = FFmpegClient(config.ffmpeg)
        self.signal_manager = SignalManager()
        self.progress_reporter = ProgressReporter(config.ui)

        # State tracking
        self._shutdown_requested = False
        self._current_scan_summary: Optional[ScanSummary] = None

        logger.info("VideoScanner initialized")

    def scan_directory(
        self,
        directory: Path,
        scan_mode: ScanMode = ScanMode.HYBRID,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
        resume: bool = True,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None,
    ) -> ScanSummary:
        """
        Scan a directory for corrupt video files.

        Args:
            directory: Directory to scan
            scan_mode: Type of scan to perform
            recursive: Whether to scan subdirectories
            extensions: File extensions to include
            resume: Whether to resume from previous scan
            progress_callback: Optional callback for progress updates

        Returns:
            ScanSummary: Summary of the scan operation
        """
        logger.info(f"Starting directory scan: {directory}")
        logger.info(f"Scan mode: {scan_mode.value}, recursive: {recursive}")

        # Validate directory
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not directory.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {directory}")

        # Get video files
        video_files = self._find_video_files(directory, recursive, extensions)
        if not video_files:
            logger.warning("No video files found to scan")
            return self._create_empty_summary(directory, scan_mode)

        logger.info(f"Found {len(video_files)} video files to scan")

        # Initialize WAL for resume functionality
        wal = None
        resuming = False
        if resume and self.config.storage.wal_enabled:
            wal = WriteAheadLog(
                directory=str(directory),
                scan_mode=scan_mode,
                extensions=extensions or self.config.scanner.extensions,
                config=self.config.storage,
            )
            resuming = wal.load_existing()
            if resuming:
                logger.info(
                    f"Resuming scan with {len(wal.get_completed_results())} existing results"
                )

        # Filter out already processed files if resuming
        if resuming and wal:
            completed_files = {r.video_file.path for r in wal.get_completed_results()}
            video_files = [vf for vf in video_files if vf.path not in completed_files]
            logger.info(f"Resuming: {len(video_files)} files remaining to process")

        # Initialize progress tracking
        total_files = len(video_files) + (
            len(wal.get_completed_results()) if wal else 0
        )
        progress = ScanProgress(
            total_files=total_files,
            scan_mode=scan_mode.value,
        )

        # Initialize summary
        summary = ScanSummary(
            directory=directory,
            total_files=total_files,
            processed_files=len(wal.get_completed_results()) if wal else 0,
            corrupt_files=(
                sum(1 for r in wal.get_completed_results() if r.is_corrupt)
                if wal
                else 0
            ),
            healthy_files=0,
            scan_mode=scan_mode,
            scan_time=0.0,
            was_resumed=resuming,
        )
        summary.healthy_files = summary.processed_files - summary.corrupt_files
        self._current_scan_summary = summary

        # Setup signal handling for progress reporting
        self.signal_manager.setup_handlers(self._signal_handler)

        start_time = time.time()

        try:
            # Perform the scan based on mode
            results = []
            if wal:
                results.extend(wal.get_completed_results())

            if scan_mode == ScanMode.HYBRID:
                new_results = self._scan_hybrid(
                    video_files, progress, progress_callback, wal
                )
            elif scan_mode == ScanMode.QUICK:
                new_results = self._scan_mode(
                    video_files, ScanMode.QUICK, progress, progress_callback, wal
                )
            else:  # DEEP
                new_results = self._scan_mode(
                    video_files, ScanMode.DEEP, progress, progress_callback, wal
                )

            results.extend(new_results)

            # Update final summary
            summary.processed_files = len(results)
            summary.corrupt_files = sum(1 for r in results if r.is_corrupt)
            summary.healthy_files = summary.processed_files - summary.corrupt_files
            summary.scan_time = time.time() - start_time
            summary.completed_at = time.time()

            # Clean up WAL if scan completed successfully
            if wal and not self._shutdown_requested:
                wal.cleanup()

            logger.info(
                f"Scan completed: {summary.processed_files} files, "
                f"{summary.corrupt_files} corrupt, {summary.scan_time:.2f}s"
            )

            return summary

        except KeyboardInterrupt:
            logger.warning("Scan interrupted by user")
            summary.scan_time = time.time() - start_time
            raise
        except Exception:
            logger.exception("Scan failed with unexpected error")
            summary.scan_time = time.time() - start_time
            raise
        finally:
            self.signal_manager.restore_handlers()

    def _find_video_files(
        self, directory: Path, recursive: bool, extensions: Optional[List[str]]
    ) -> List[VideoFile]:
        """Find all video files in directory."""
        if extensions is None:
            extensions = self.config.scanner.extensions

        logger.debug(f"Scanning for video files with extensions: {extensions}")

        video_files = []
        pattern = "**/*" if recursive else "*"

        for file_path in directory.glob(pattern):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in extensions
                and file_path.stat().st_size <= self.config.security.max_file_size
            ):
                video_files.append(VideoFile(file_path))

        return sorted(video_files, key=lambda x: x.path)

    def _scan_hybrid(
        self,
        video_files: List[VideoFile],
        progress: ScanProgress,
        progress_callback: Optional[Callable[[ScanProgress], None]],
        wal: Optional[WriteAheadLog],
    ) -> List[ScanResult]:
        """Perform hybrid scan (quick first, then deep for suspicious files)."""
        logger.info("Starting hybrid scan - Phase 1: Quick scan")
        progress.phase = "quick_scan"

        # Phase 1: Quick scan all files
        quick_results = self._scan_mode(
            video_files, ScanMode.QUICK, progress, progress_callback, wal
        )

        if self._shutdown_requested:
            return quick_results

        # Phase 2: Deep scan files that need it
        files_needing_deep_scan = [
            result.video_file
            for result in quick_results
            if result.needs_deep_scan and not result.is_corrupt
        ]

        if not files_needing_deep_scan:
            logger.info("Hybrid scan complete - no files needed deep scanning")
            return quick_results

        logger.info(
            f"Starting hybrid scan - Phase 2: Deep scan {len(files_needing_deep_scan)} files"
        )
        progress.phase = "deep_scan"

        # Reset progress for deep scan phase
        progress.processed_count = len(quick_results)
        progress.total_files = len(quick_results) + len(files_needing_deep_scan)

        deep_results = self._scan_mode(
            files_needing_deep_scan, ScanMode.DEEP, progress, progress_callback, wal
        )

        # Replace quick results with deep results for files that were deep scanned
        final_results = []
        deep_results_map = {r.video_file.path: r for r in deep_results}

        for quick_result in quick_results:
            if quick_result.video_file.path in deep_results_map:
                final_results.append(deep_results_map[quick_result.video_file.path])
            else:
                final_results.append(quick_result)

        return final_results

    def _scan_mode(
        self,
        video_files: List[VideoFile],
        scan_mode: ScanMode,
        progress: ScanProgress,
        progress_callback: Optional[Callable[[ScanProgress], None]],
        wal: Optional[WriteAheadLog],
    ) -> List[ScanResult]:
        """Perform scan with specified mode."""
        results = []

        with ThreadPoolExecutor(
            max_workers=self.config.scanner.max_workers
        ) as executor:
            # Submit all scan tasks
            future_to_file = {
                executor.submit(
                    self._scan_single_file, video_file, scan_mode
                ): video_file
                for video_file in video_files
            }

            # Process completed scans
            for future in as_completed(future_to_file):
                if self._shutdown_requested:
                    # Cancel remaining futures
                    for f in future_to_file:
                        if not f.done():
                            f.cancel()
                    break

                try:
                    result = future.result()
                    results.append(result)

                    # Update progress
                    progress.processed_count += 1
                    progress.current_file = str(result.video_file.path)
                    if result.is_corrupt:
                        progress.corrupt_count += 1

                    # Update WAL
                    if wal:
                        wal.append_result(result)

                    # Update summary
                    if self._current_scan_summary:
                        self._current_scan_summary.processed_files = (
                            progress.processed_count
                        )
                        self._current_scan_summary.corrupt_files = (
                            progress.corrupt_count
                        )
                        self._current_scan_summary.healthy_files = (
                            progress.processed_count - progress.corrupt_count
                        )

                    # Call progress callback
                    if progress_callback:
                        progress_callback(progress)

                    # Update progress reporter
                    self.progress_reporter.update(progress)

                except Exception as e:
                    video_file = future_to_file[future]
                    logger.error(f"Error scanning {video_file.path}: {e}")
                    # Create error result
                    error_result = ScanResult(
                        video_file=video_file,
                        is_corrupt=False,
                        error_message=f"Scan failed: {e}",
                        scan_mode=scan_mode,
                    )
                    results.append(error_result)

                    if wal:
                        wal.append_result(error_result)

        return results

    def _scan_single_file(
        self, video_file: VideoFile, scan_mode: ScanMode
    ) -> ScanResult:
        """Scan a single video file."""
        logger.debug(f"Scanning {video_file.path} with {scan_mode.value} mode")

        start_time = time.time()

        try:
            if scan_mode == ScanMode.QUICK:
                result = self.ffmpeg.inspect_quick(video_file)
            else:  # DEEP
                result = self.ffmpeg.inspect_deep(video_file)

            result.inspection_time = time.time() - start_time
            result.scan_mode = scan_mode

            return result

        except Exception as e:
            logger.exception(f"Failed to scan {video_file.path}")
            return ScanResult(
                video_file=video_file,
                is_corrupt=False,
                error_message=f"Scan failed: {e}",
                inspection_time=time.time() - start_time,
                scan_mode=scan_mode,
            )

    def _create_empty_summary(
        self, directory: Path, scan_mode: ScanMode
    ) -> ScanSummary:
        """Create an empty scan summary."""
        return ScanSummary(
            directory=directory,
            total_files=0,
            processed_files=0,
            corrupt_files=0,
            healthy_files=0,
            scan_mode=scan_mode,
            scan_time=0.0,
            completed_at=time.time(),
        )

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle signals for progress reporting and graceful shutdown."""
        import signal

        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name}")

        # Report current progress
        if self._current_scan_summary:
            self.progress_reporter.report_signal_progress(self._current_scan_summary)

        # Handle shutdown signals
        if signum in (signal.SIGTERM, signal.SIGINT):
            logger.info("Graceful shutdown requested")
            self._shutdown_requested = True

    def get_video_files(
        self,
        directory: Path,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
    ) -> List[VideoFile]:
        """Get list of video files without scanning them."""
        return self._find_video_files(directory, recursive, extensions)

    def is_shutdown_requested(self) -> bool:
        """Check if graceful shutdown was requested."""
        return self._shutdown_requested
