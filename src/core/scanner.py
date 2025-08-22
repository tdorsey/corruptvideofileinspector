"""Core video scanning service with support for different scan modes."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from src.config import load_config
from src.core.models.inspection import VideoFile
from src.core.models.probe import ProbeResult, ScanPrerequisites
from src.core.models.scanning import (
    ScanMode,
    ScanPhase,
    ScanProgress,
    ScanResult,
    ScanSummary,
)

from src.core.prober import VideoProber
from src.ffmpeg.corruption_detector import CorruptionDetector
from src.ffmpeg.ffmpeg_client import FFmpegClient
from src.ffmpeg.ffprobe_client import FFprobeClient

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from src.config.config import AppConfig

logger = logging.getLogger(__name__)


class VideoScanner:
    def _get_resume_path(self, directory: Path) -> Path:
        """Return the path to the resume (WAL) file for a scan directory, always in the output directory."""
        output_dir = self.config.output.default_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        if not os.access(output_dir, os.W_OK):
            msg = f"Output directory is not writable: {output_dir}"
            raise OSError(msg)
        # Use a unique name for each scan directory
        safe_dir = directory.resolve().as_posix().replace("/", "_").lstrip("_")
        return output_dir / f".scan_resume_{safe_dir}.json"

    def _save_resume_state(self, resume_path: Path, processed_files: set[str]) -> None:
        with resume_path.open("w", encoding="utf-8") as f:
            json.dump({"processed_files": list(processed_files)}, f)

    def _load_resume_state(self, resume_path: Path) -> set[str]:
        if not resume_path.exists():
            return set()
        with resume_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("processed_files", []))

    def __init__(self, config: AppConfig | None = None) -> None:
        """Initialize the video scanner.

        Args:
            config: Application configuration. If None, will load default config.
        """
        if config is None:
            config = load_config()

        self.config = config
        self._shutdown_requested = False
        self._current_scan_summary: ScanSummary | None = None
        self.corruption_detector = CorruptionDetector()

        # Initialize probe-related components
        self._ffprobe_client: FFprobeClient | None = None
        self._scan_prerequisites = ScanPrerequisites()

        if config.ffmpeg.require_probe_before_scan:
            try:
                self._ffprobe_client = FFprobeClient(config.ffmpeg)
                logger.info("FFprobe client initialized for probe-before-scan workflow")
            except Exception as e:
                logger.warning(f"Failed to initialize FFprobe client: {e}")
                if config.ffmpeg.require_probe_before_scan:
                    logger.exception("Probe-before-scan is required but FFprobe unavailable")

        logger.info("VideoScanner initialized with config: %s", config.scan)
        # Initialize prober used to create VideoFile objects with hashes
        self.prober = VideoProber()

    def _probe_file(self, video_file: VideoFile) -> ProbeResult | None:
        """
        Probe a video file to extract metadata and validate it for scanning.

        Args:
            video_file: Video file to probe

        Returns:
            ProbeResult if probing is enabled, None otherwise
        """
        if not self._ffprobe_client:
            return None

        # Perform probe
        logger.debug(f"Probing file: {video_file.path}")
        probe_result = self._ffprobe_client.probe_file(
            video_file, timeout=self.config.ffmpeg.probe_timeout
        )

        return probe_result

    def _can_scan_file(
        self, video_file: VideoFile, probe_result: ProbeResult | None = None
    ) -> tuple[bool, str]:
        """
        Check if a file can be scanned based on probe results and prerequisites.

        Args:
            video_file: Video file to check
            probe_result: Probe result (will probe if None and probing enabled)

        Returns:
            Tuple of (can_scan, reason)
        """
        # If probe-before-scan is disabled, allow all files
        if not self.config.ffmpeg.require_probe_before_scan:
            return True, "Probe requirement disabled"

        # Get probe result if not provided
        if probe_result is None:
            probe_result = self._probe_file(video_file)

        # Check prerequisites
        if self._scan_prerequisites.can_scan(probe_result):
            return True, "Prerequisites met"
        reason = self._scan_prerequisites.get_rejection_reason(probe_result)
        return False, reason

    async def locate_video_files_async(
        self,
        directory: Path,
        *,
        recursive: bool = True,
        extensions: list[str] | None = None,
        progress_callback: Callable[[ScanProgress], None] | None = None,
    ) -> list[VideoFile]:
        """Locate video files in a directory asynchronously, tracking progress.

        Args:
            directory: Directory to search
            recursive: Whether to search subdirectories
            extensions: Deprecated parameter, kept for compatibility
            progress_callback: Optional callback for progress updates

        Returns:
            List of found potential video files (all files, probed to determine if video)
        """
        logger.info("Locating video files in: %s", directory)
        video_files = await self._find_video_files_async(directory, recursive, extensions)
        progress = ScanProgress(
            total_files=len(video_files),
            processed_count=0,
            scan_mode="locate",
        )
        for idx, video_file in enumerate(video_files, 1):
            progress.processed_count = idx
            progress.current_file = str(video_file.path)
            if progress_callback:
                progress_callback(progress)
        logger.info("Located %d video files", len(video_files))
        return video_files

    def locate_video_files(
        self,
        directory: Path,
        *,
        recursive: bool = True,
        extensions: list[str] | None = None,
        progress_callback: Callable[[ScanProgress], None] | None = None,
    ) -> list[VideoFile]:
        """Synchronous wrapper for locating video files.

        Args:
            directory: Directory to search
            recursive: Whether to search subdirectories
            extensions: Deprecated parameter, kept for compatibility
            progress_callback: Optional callback for progress updates

        Returns:
            List of found potential video files (all files, probed to determine if video)
        """
        try:
            try:
                loop = asyncio.get_running_loop()
                # If already running, create a new loop in a new thread
                result = []

                def run():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result.append(
                        new_loop.run_until_complete(
                            self.locate_video_files_async(
                                directory,
                                recursive=recursive,
                                extensions=extensions,
                                progress_callback=progress_callback,
                            )
                        )
                    )
                    new_loop.close()

                t = threading.Thread(target=run)
                t.start()
                t.join()
                return result[0]
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self.locate_video_files_async(
                            directory,
                            recursive=recursive,
                            extensions=extensions,
                            progress_callback=progress_callback,
                        )
                    )
                finally:
                    loop.close()
        except Exception:
            logger.exception("Error in locate_video_files")
            raise

    async def locate_files_async(
        self,
        file_paths: list[Path],
        progress_callback: Callable[[ScanProgress], None] | None = None,
    ) -> list[VideoFile]:
        """Locate specific video files asynchronously, tracking progress.

        Args:
            file_paths: List of video file paths to check
            progress_callback: Optional progress callback

        Returns:
            List of found video files
        """
        video_files = [
            self.prober.create_video_file_with_hash(path) for path in file_paths if path.exists()
        ]
        progress = ScanProgress(
            total_files=len(video_files),
            scan_mode="locate",
        )
        for idx, video_file in enumerate(video_files, 1):
            progress.processed_count = idx
            progress.current_file = str(video_file.path)
            if progress_callback:
                progress_callback(progress)
        return video_files

    def get_video_files(
        self,
        directory: Path,
        *,
        recursive: bool = True,
        extensions: list[str] | None = None,
    ) -> list[VideoFile]:
        """Get list of video files in a directory (sync, no progress).

        Args:
            directory: Directory to search
            recursive: Whether to search subdirectories
            extensions: Deprecated parameter, kept for compatibility

        Returns:
            List of potential video files found (all files, probed to determine if video)
        """
        try:
            try:
                loop = asyncio.get_running_loop()
                # If already running, create a new loop in a new thread

                result = []

                def run():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result.append(
                        new_loop.run_until_complete(
                            self._find_video_files_async(directory, recursive, extensions)
                        )
                    )
                    new_loop.close()

                t = threading.Thread(target=run)
                t.start()
                t.join()
                return result[0]
            except RuntimeError:
                # No running event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self._find_video_files_async(directory, recursive, extensions)
                    )
                finally:
                    loop.close()
        except Exception:
            logger.exception("Error in get_video_files")
            raise

    def request_shutdown(self) -> None:
        """Request graceful shutdown of current scan operation."""
        logger.info("Shutdown requested")
        self._shutdown_requested = True

    @property
    def is_shutdown_requested(self) -> bool:
        """Check if graceful shutdown was requested."""
        return self._shutdown_requested

    def scan_directory(
        self,
        directory: Path,
        scan_mode: ScanMode,
        recursive: bool = True,
        resume: bool = True,
        progress_callback: Callable[[ScanProgress], None] | None = None,
    ) -> ScanSummary:
        """Scan a directory for corrupt video files.

        Args:
            directory: Directory to scan
            scan_mode: Type of scan to perform
            recursive: Whether to scan subdirectories
            resume: Whether to resume from previous scan state
            progress_callback: Optional callback for progress updates

        Returns:
            ScanSummary: Summary of the scan operation
        """
        logger.info("Starting directory scan: %s", directory)
        logger.info("Scan mode: %s, recursive: %s", scan_mode.value, recursive)

        # Get video files
        video_files = self.get_video_files(directory, recursive=recursive)
        if not video_files:
            logger.warning("No video files found to scan")
            return ScanSummary(
                directory=directory,
                total_files=0,
                processed_files=0,
                corrupt_files=0,
                healthy_files=0,
                scan_mode=scan_mode,
                scan_time=0.0,
            )

        logger.info("Found %d video files to scan", len(video_files))

        # Phase 0: Probe files (if probe-before-scan is enabled)
        probe_results: dict[str, ProbeResult] = {}
        eligible_files: list[VideoFile] = []

        if self.config.ffmpeg.require_probe_before_scan and self._ffprobe_client:
            logger.info("Starting probe phase for %d files", len(video_files))

            for i, video_file in enumerate(video_files):
                if self._shutdown_requested:
                    break

                # Update progress for probe phase
                if progress_callback:
                    probe_progress = ScanProgress(
                        current_file=str(video_file.path),
                        total_files=len(video_files),
                        processed_count=i,
                        phase=ScanPhase.SCANNING,
                        scan_mode=scan_mode,
                    )
                    progress_callback(probe_progress)

                # Probe the file
                probe_result = self._probe_file(video_file)
                if probe_result:
                    probe_results[str(video_file.path)] = probe_result

                # Check if file can be scanned
                can_scan, reason = self._can_scan_file(video_file, probe_result)
                if can_scan:
                    eligible_files.append(video_file)
                    logger.debug(f"File eligible for scanning: {video_file.path}")
                else:
                    logger.info(f"Skipping file (not eligible): {video_file.path} - {reason}")

            logger.info(
                f"Probe phase complete: {len(eligible_files)}/{len(video_files)} files eligible for scanning"
            )
        else:
            # If probing disabled, all files are eligible
            eligible_files = video_files
            logger.info("Probe-before-scan disabled, all files eligible")

        # Use eligible files for scanning
        video_files = eligible_files
        if not video_files:
            logger.warning("No eligible video files found after probe phase")
            start_time = time.time()
            return ScanSummary(
                directory=directory,
                total_files=len(eligible_files),
                processed_files=0,
                corrupt_files=0,
                healthy_files=0,
                scan_mode=scan_mode,
                scan_time=time.time() - start_time,
                was_resumed=False,  # No files to resume
            )

        start_time = time.time()
        resume_path = self._get_resume_path(directory)
        processed_files: set[str] = set()
        was_resumed = False

        if resume and resume_path.exists():
            processed_files = self._load_resume_state(resume_path)
            if processed_files:
                logger.info(f"Resuming scan, skipping {len(processed_files)} files.")
                was_resumed = True

        # Initialize tracking variables
        suspicious_files: list[VideoFile] = []
        progress: ScanProgress = ScanProgress(
            total_files=len(video_files),
            processed_count=0,
            corrupt_count=0,
            scan_mode=scan_mode.value,
        )
        detector: CorruptionDetector = CorruptionDetector()
        deep_scans_needed: int = 0
        deep_scans_completed: int = 0

        # Phase 1: Quick scan (for HYBRID or QUICK modes only)
        if scan_mode in (ScanMode.QUICK, ScanMode.HYBRID):
            for video_file in video_files:
                if self._shutdown_requested:
                    break
                video_file_str: str = str(video_file.path)
                if resume and video_file_str in processed_files:
                    continue
                progress.processed_count += 1
                progress.current_file = video_file_str
                # Run FFmpeg to analyze file (quick scan)
                # Only analyze first 10 seconds for quick scan
                ffmpeg_cmd: list[str] = [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-t",
                    "10",
                    "-i",
                    video_file_str,
                    "-f",
                    "null",
                    "-",
                ]
                try:
                    proc = subprocess.run(
                        ffmpeg_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False,
                    )
                    stderr = proc.stderr
                    exit_code = proc.returncode
                except Exception as e:
                    stderr = str(e)
                    exit_code = 1
                analysis = detector.analyze_ffmpeg_output(stderr, exit_code, is_quick_scan=True)
                if analysis.is_corrupt:
                    progress.corrupt_count += 1
                elif analysis.needs_deep_scan and scan_mode == ScanMode.HYBRID:
                    suspicious_files.append(video_file)
                processed_files.add(video_file_str)
                self._save_resume_state(resume_path, processed_files)
                if progress_callback:
                    progress_callback(progress)

        # Phase 2: Deep/Full scan (for HYBRID, DEEP, or FULL modes)
        if scan_mode == ScanMode.HYBRID and suspicious_files:
            deep_scans_needed = len(suspicious_files)
            for video_file in suspicious_files:
                if self._shutdown_requested:
                    break
                video_file_str = str(video_file.path)
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    video_file_str,
                    "-f",
                    "null",
                    "-",
                ]
                try:
                    proc = subprocess.run(
                        ffmpeg_cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        check=False,
                    )
                    stderr = proc.stderr
                    exit_code = proc.returncode
                except Exception as e:
                    stderr = str(e)
                    exit_code = 1
                analysis = detector.analyze_ffmpeg_output(stderr, exit_code, is_quick_scan=False)
                deep_scans_completed += 1
                if analysis.is_corrupt:
                    progress.corrupt_count += 1
                if progress_callback:
                    progress_callback(progress)
        elif scan_mode == ScanMode.DEEP:
            deep_scans_needed = len(video_files)
            for video_file in video_files:
                if self._shutdown_requested:
                    break
                video_file_str = str(video_file.path)
                if resume and video_file_str in processed_files:
                    continue
                progress.processed_count += 1
                progress.current_file = video_file_str
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    video_file_str,
                    "-f",
                    "null",
                    "-",
                ]
                try:
                    proc = subprocess.run(
                        ffmpeg_cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        check=False,
                    )
                    stderr = proc.stderr
                    exit_code = proc.returncode
                except Exception as e:
                    stderr = str(e)
                    exit_code = 1
                analysis = detector.analyze_ffmpeg_output(stderr, exit_code, is_quick_scan=False)
                deep_scans_completed += 1
                if analysis.is_corrupt:
                    progress.corrupt_count += 1
                processed_files.add(video_file_str)
                self._save_resume_state(resume_path, processed_files)
                if progress_callback:
                    progress_callback(progress)
        elif scan_mode == ScanMode.FULL:
            deep_scans_needed = len(video_files)
            for video_file in video_files:
                if self._shutdown_requested:
                    break
                video_file_str = str(video_file.path)
                if resume and video_file_str in processed_files:
                    continue
                progress.processed_count += 1
                progress.current_file = video_file_str
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    video_file_str,
                    "-f",
                    "null",
                    "-",
                ]
                try:
                    # No timeout for FULL scan mode
                    proc = subprocess.run(
                        ffmpeg_cmd,
                        capture_output=True,
                        text=True,
                        timeout=None,
                        check=False,
                    )
                    stderr = proc.stderr
                    exit_code = proc.returncode
                except Exception as e:
                    stderr = str(e)
                    exit_code = 1
                analysis = detector.analyze_ffmpeg_output(stderr, exit_code, is_quick_scan=False)
                deep_scans_completed += 1
                if analysis.is_corrupt:
                    progress.corrupt_count += 1
                processed_files.add(video_file_str)
                self._save_resume_state(resume_path, processed_files)
                if progress_callback:
                    progress_callback(progress)
        # Remove resume file if scan completed or was interrupted
        if resume_path.exists():
            try:
                resume_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove resume file: {e}")
        # Create summary
        summary: ScanSummary = ScanSummary(
            directory=directory,
            total_files=len(video_files),
            processed_files=progress.processed_count,
            corrupt_files=progress.corrupt_count,
            healthy_files=progress.processed_count - progress.corrupt_count,
            scan_mode=scan_mode,
            scan_time=time.time() - start_time,
        )
        summary.was_resumed = was_resumed
        summary.deep_scans_needed = deep_scans_needed
        summary.deep_scans_completed = deep_scans_completed
        logger.info(
            "Scan completed: %d files, %d corrupt, %.2fs",
            summary.processed_files,
            summary.corrupt_files,
            summary.scan_time,
        )
        return summary

    def scan(
        self,
        file_paths: list[str],
        mode: ScanMode,
        progress_callback: Callable[[ScanProgress], None] | None = None,
    ) -> list[ScanResult]:
        """Scan specific video files.

        Args:
            file_paths: List of file paths to scan
            mode: Type of scan to perform
            progress_callback: Optional callback for progress updates

        Returns:
            List of scan results for each file
        """
        # Create video files from paths and probe if enabled
        video_files = []
        probe_results: dict[str, ProbeResult] = {}

        for path_str in file_paths:
            path = Path(path_str)
            if path.exists() and path.is_file():
                video_file = VideoFile(path=path)

                # Probe the file if probe-before-scan is enabled
                if self.config.ffmpeg.require_probe_before_scan:
                    can_scan, reason = self._can_scan_file(video_file)
                    if can_scan:
                        # Get probe result for later use
                        probe_result = self._probe_file(video_file)
                        if probe_result:
                            probe_results[path_str] = probe_result
                        video_files.append(video_file)
                        logger.debug(f"File eligible for scanning: {path}")
                    else:
                        logger.info(f"Skipping file (not eligible): {path} - {reason}")
                else:
                    video_files.append(video_file)

        if not video_files:
            logger.warning("No valid video files found in provided paths")
            return []

        # Initialize FFmpeg client
        ffmpeg_client = FFmpegClient(self.config.ffmpeg)

        # Scan each file
        results: list[ScanResult] = []
        for i, video_file in enumerate(video_files):
            if self.is_shutdown_requested:
                logger.info("Scan cancelled by user request")
                break

            logger.debug("Scanning file %d/%d: %s", i + 1, len(video_files), video_file.path)

            # Create progress update
            if progress_callback:
                corrupt_count = sum(1 for r in results if r.is_corrupt)
                progress = ScanProgress(
                    current_file=str(video_file.path),
                    processed_files=i,
                    total_files=len(video_files),
                    corrupt_files=corrupt_count,
                    scan_mode=mode,
                )
                progress_callback(progress)

            # Get probe result for this file
            file_path_str = str(video_file.path)
            probe_result = probe_results.get(file_path_str)

            # Perform scan based on mode
            result = None
            if mode == ScanMode.QUICK:
                result = ffmpeg_client.inspect_quick(video_file, probe_result)
            elif mode == ScanMode.DEEP:
                result = ffmpeg_client.inspect_deep(video_file, probe_result=probe_result)
            elif mode == ScanMode.HYBRID:
                # First try quick scan
                result = ffmpeg_client.inspect_quick(video_file, probe_result)
                if result.needs_deep_scan:
                    result = ffmpeg_client.inspect_deep(video_file, probe_result=probe_result)
            elif mode == ScanMode.FULL:
                result = ffmpeg_client.inspect_full(video_file, probe_result)
            else:  # pragma: no cover
                logger.error("Unknown scan mode: %s", mode)  # type: ignore[unreachable]
                # Skip this file if unknown mode
                continue

            if result is not None:
                results.append(result)

        logger.info(
            "File scan completed: %d files, %d corrupt",
            len(results),
            sum(1 for r in results if r.is_corrupt),
        )
        return results

    # Private methods

    async def _find_video_files_async(
        self,
        directory: Path,
        recursive: bool,
        extensions: list[str] | None = None,  # Deprecated parameter, kept for compatibility
    ) -> list[VideoFile]:
        """Find all potential video files in directory using probe-based detection."""
        logger.debug("Scanning directory for all files (probe-based video detection)")

        use_content_detection = self.config.scan.use_content_detection
        logger.debug(f"Scanning for video files, content_detection={use_content_detection}")

        # Use asyncio to make file system operations non-blocking
        def _scan_directory() -> Iterator[VideoFile]:
            pattern = "**/*" if recursive else "*"
            logger.debug(f"Scanning directory: {directory}, pattern: {pattern}")

            # Make a local mutable flag to avoid touching outer scope
            local_use_content = use_content_detection

            # Initialize FFmpeg client for content detection if needed
            ffmpeg_client = None
            if local_use_content:
                try:
                    ffmpeg_client = FFmpegClient(self.config.ffmpeg)
                    logger.debug("FFmpeg client initialized for content detection")
                except Exception as e:
                    logger.warning(f"Failed to initialize FFmpeg client for content detection: {e}")
                    logger.warning("Falling back to extension-based detection")
                    local_use_content = False

            for file_path in directory.glob(pattern):
                if not file_path.is_file():
                    continue

                logger.debug(f"Checking file: {file_path}")

                # Apply extension pre-filter if configured (performance optimization)
                if (
                    local_use_content
                    and self.config.scan.extension_filter
                    and file_path.suffix.lower() not in self.config.scan.extension_filter
                ):
                    logger.debug(f"Skipped by extension filter: {file_path}")
                    continue

                is_video = False
                if local_use_content and ffmpeg_client:
                    # Use FFprobe content analysis
                    try:
                        is_video = ffmpeg_client.is_video_file(
                            file_path, timeout=self.config.scan.ffprobe_timeout
                        )
                        logger.debug(f"Content analysis result for {file_path}: {is_video}")
                    except Exception as e:
                        logger.debug(
                            f"Content analysis failed for {file_path}: {e}, using extension fallback"
                        )
                        # Fall back to extension check for this file
                        ext_list = extensions or []
                        is_video = file_path.suffix.lower() in [ext.lower() for ext in ext_list]
                else:
                    # Use extension-based detection as fallback
                    ext_list = extensions or []
                    is_video = file_path.suffix.lower() in [ext.lower() for ext in ext_list]

                if is_video:
                    logger.debug(f"Accepted as video file: {file_path}")
                    yield self.prober.create_video_file_with_hash(file_path)
                else:
                    logger.debug(f"Skipped: {file_path}")

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        potential_files = await loop.run_in_executor(None, lambda: list(_scan_directory()))

        logger.debug(f"Found {len(potential_files)} files to probe")
        return potential_files


def validate_scan_results(results: list[ScanResult]) -> list[str]:
    issues: list[str] = []
    if not results:
        return issues
    for i, result in enumerate(results):
        if not result.video_file:
            issues.append(f"Result {i}: Missing video file")
            continue
        if not result.video_file.path:
            issues.append(f"Result {i}: Invalid file path")
        if result.inspection_time < 0:
            issues.append(f"Result {i}: Negative inspection time: {result.inspection_time}")
        if result.confidence < 0 or result.confidence > 1:
            issues.append(f"Result {i}: Invalid confidence value: {result.confidence}")
        if result.is_corrupt and result.needs_deep_scan:
            issues.append(f"Result {i}: File marked as both corrupt and needing deep scan")
        if (
            result.deep_scan_completed
            and not result.needs_deep_scan
            and result.scan_mode == ScanMode.QUICK
        ):
            issues.append(f"Result {i}: Deep scan completed but not needed and mode is quick")
    return issues
