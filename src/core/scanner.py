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
from collections.abc import Callable, Iterator

from src.config import load_config
from src.config.config import AppConfig
from src.core.models.inspection import VideoFile
from src.core.models.scanning import (
    ScanMode,
    ScanProgress,
    ScanResult,
    ScanSummary,
)
from src.ffmpeg.corruption_detector import CorruptionDetector

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class VideoScanner:
    def _get_resume_path(self, directory: Path) -> Path:
        """Return the path to the resume (WAL) file for a scan directory, always in the output directory."""
        output_dir = self.config.output.default_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        if not os.access(output_dir, os.W_OK):
            raise OSError(f"Output directory is not writable: {output_dir}")
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

        logger.info("VideoScanner initialized with config: %s", config.scan)

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
            extensions: File extensions to include (defaults to config)
            progress_callback: Optional callback for progress updates

        Returns:
            List of found video files
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
            extensions: File extensions to include
            progress_callback: Optional callback for progress updates

        Returns:
            List of found video files
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
        video_files = [VideoFile(path=path) for path in file_paths if path.exists()]
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
            extensions: File extensions to include

        Returns:
            List of video files found
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
        start_time: float = time.time()
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
        from src.ffmpeg.ffmpeg_client import FFmpegClient
        
        # Create video files from paths
        video_files = []
        for path_str in file_paths:
            path = Path(path_str)
            if path.exists() and path.is_file():
                video_files.append(VideoFile(path=path))
        
        if not video_files:
            logger.warning("No valid video files found in provided paths")
            return []
        
        # Initialize FFmpeg client
        ffmpeg_client = FFmpegClient(self.config.ffmpeg)
        
        # Scan each file
        results = []
        for i, video_file in enumerate(video_files):
            if self.is_shutdown_requested:
                logger.info("Scan cancelled by user request")
                break
                
            logger.debug("Scanning file %d/%d: %s", i + 1, len(video_files), video_file.path)
            
            # Create progress update
            if progress_callback:
                progress = ScanProgress(
                    current_file=str(video_file.path),
                    processed_files=i,
                    total_files=len(video_files),
                    corrupt_files=sum(1 for r in results if r.is_corrupt),
                    scan_mode=mode,
                )
                progress_callback(progress)
            
            # Perform scan based on mode
            if mode == ScanMode.QUICK:
                result = ffmpeg_client.inspect_quick(video_file)
            elif mode == ScanMode.DEEP:
                result = ffmpeg_client.inspect_deep(video_file)
            elif mode == ScanMode.HYBRID:
                # First try quick scan
                result = ffmpeg_client.inspect_quick(video_file)
                if result.needs_deep_scan:
                    result = ffmpeg_client.inspect_deep(video_file)
            elif mode == ScanMode.FULL:
                result = ffmpeg_client.inspect_full(video_file)
            else:
                logger.error("Unknown scan mode: %s", mode)
                continue
                
            results.append(result)
        
        logger.info("File scan completed: %d files, %d corrupt", len(results), 
                   sum(1 for r in results if r.is_corrupt))
        return results

    # Private methods

    async def _find_video_files_async(
        self,
        directory: Path,
        recursive: bool,
        extensions: list[str] | None,
    ) -> list[VideoFile]:
        """Find all video files in directory asynchronously."""
        if extensions is None:
            extensions = self.config.scan.extensions

        logger.debug("Scanning for video files with extensions: %s", extensions)

        video_files: list[VideoFile] = []

        # Use asyncio to make file system operations non-blocking
        def _scan_directory() -> Iterator[VideoFile]:
            pattern = "**/*" if recursive else "*"
            logger.debug(f"Scanning directory: {directory}, pattern: {pattern}")
            logger.debug(f"Using extensions: {extensions}")
            for file_path in directory.glob(pattern):
                logger.debug(f"Found file: {file_path} (suffix: {file_path.suffix.lower()})")
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    logger.debug(f"Accepted as video file: {file_path}")
                    yield VideoFile(path=file_path)
                else:
                    logger.debug(f"Skipped: {file_path}")

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        video_files = await loop.run_in_executor(None, lambda: list(_scan_directory()))

        return sorted(video_files, key=lambda x: x.path)


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
            issues.append(f"Result {i}: Negative inspection time: " f"{result.inspection_time}")
        if result.confidence < 0 or result.confidence > 1:
            issues.append(f"Result {i}: Invalid confidence value: " f"{result.confidence}")
        if result.is_corrupt and result.needs_deep_scan:
            issues.append(f"Result {i}: File marked as both corrupt " f"and needing deep scan")
        if (
            result.deep_scan_completed
            and not result.needs_deep_scan
            and result.scan_mode == ScanMode.QUICK
        ):
            issues.append(f"Result {i}: Deep scan completed but not needed " f"and mode is quick")
    return issues
