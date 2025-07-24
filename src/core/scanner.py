"""Core video scanning service with support for different scan modes."""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import AsyncIterator, Callable, Iterator

from corrupt_video_inspector.config.settings import AppConfig
from corrupt_video_inspector.core.models import (
    ScanProgress,
    VideoFile,
)

logger = logging.getLogger(__name__)


    """Service for locating video files and tracking scan progress."""

    def __init__(self, config: AppConfig | None = None) -> None:
        """Initialize the video scanner.
        
        Args:
            config: Application configuration. If None, will load default config.
        """
        if config is None:
            from corrupt_video_inspector.config.settings import load_config
            config = load_config()
            
        self.config = config
        self._shutdown_requested = False
        self._current_scan_summary: ScanSummary | None = None
        
        logger.info("VideoScanner initialized with config: %s", config.scanner)

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
        self._validate_directory(directory)
        video_files = await self._find_video_files_async(
            directory, recursive, extensions
        )
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
            loop = asyncio.get_event_loop()
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
            if loop.is_running():
                loop.close()

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
        video_files = [VideoFile(path) for path in file_paths if path.exists()]
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
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            self._find_video_files_async(directory, recursive, extensions)
        )

    def request_shutdown(self) -> None:
        """Request graceful shutdown of current scan operation."""
        logger.info("Shutdown requested")
        self._shutdown_requested = True

    @property
    def is_shutdown_requested(self) -> bool:
        """Check if graceful shutdown was requested."""
        return self._shutdown_requested

    # Private methods

    def _validate_directory(self, directory: Path) -> None:
        """Validate that directory exists and is accessible."""
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not directory.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {directory}")

    async def _find_video_files_async(
        self, 
        directory: Path, 
        recursive: bool, 
        extensions: list[str] | None,
    ) -> list[VideoFile]:
        """Find all video files in directory asynchronously."""
        if extensions is None:
            extensions = self.config.scanner.extensions

        logger.debug("Scanning for video files with extensions: %s", extensions)

        video_files: list[VideoFile] = []
        
        # Use asyncio to make file system operations non-blocking
        def _scan_directory() -> Iterator[VideoFile]:
            pattern = "**/*" if recursive else "*"
            for file_path in directory.glob(pattern):
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in extensions
                    and file_path.stat().st_size <= self.config.security.max_file_size
                ):
                    yield VideoFile(file_path)

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        video_files = await loop.run_in_executor(
            None, lambda: list(_scan_directory())
        )

        return sorted(video_files, key=lambda x: x.path)

    # ...existing code for _validate_directory and _find_video_files_async...
"""Validation logic for scan results."""
from .models import ScanResult, ScanMode
from typing import List

def validate_scan_results(results: List[ScanResult]) -> List[str]:
    issues: List[str] = []
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
        if result.deep_scan_completed and not result.needs_deep_scan and result.scan_mode == ScanMode.QUICK:
            issues.append(f"Result {i}: Deep scan completed but not needed and mode is quick")
    return issues
