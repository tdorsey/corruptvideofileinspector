"""
FFmpeg client for video file inspection and corruption detection.
"""

import logging
import shutil
import subprocess
from typing import Optional

from ...config.settings import FFmpegConfig
from ...core.models import FFmpegError, ScanResult, VideoFile
from ...core.detector import CorruptionDetector

logger = logging.getLogger(__name__)


class FFmpegClient:
    """Client for interacting with FFmpeg to inspect video files."""

    def __init__(self, config: FFmpegConfig):
        """Initialize FFmpeg client."""
        self.config = config
        self.detector = CorruptionDetector()
        self._ffmpeg_path: Optional[str] = None

        # Find FFmpeg command
        self._find_ffmpeg_command()

        logger.info(f"FFmpegClient initialized with command: {self._ffmpeg_path}")

    def _find_ffmpeg_command(self) -> None:
        """Find and validate FFmpeg command."""
        if self.config.command:
            # Use configured command
            if self._validate_ffmpeg_command(self.config.command):
                self._ffmpeg_path = self.config.command
                return
            else:
                logger.warning(
                    f"Configured FFmpeg command not found: {self.config.command}"
                )

        # Try common locations
        common_paths = ["ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]

        for cmd in common_paths:
            if self._validate_ffmpeg_command(cmd):
                self._ffmpeg_path = cmd
                logger.info(f"Found FFmpeg at: {cmd}")
                return

        # Try using shutil.which
        which_result = shutil.which("ffmpeg")
        if which_result and self._validate_ffmpeg_command(which_result):
            self._ffmpeg_path = which_result
            logger.info(f"Found FFmpeg via which: {which_result}")
            return

        raise FFmpegError(
            "FFmpeg command not found. Please install FFmpeg or configure the path."
        )

    def _validate_ffmpeg_command(self, command: str) -> bool:
        """Validate that a command is a working FFmpeg installation."""
        try:
            result = subprocess.run(
                [command, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            return "ffmpeg version" in result.stdout.lower()
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False

    def inspect_quick(self, video_file: VideoFile) -> ScanResult:
        """
        Perform quick inspection of video file (limited time scan).

        Args:
            video_file: Video file to inspect

        Returns:
            ScanResult: Quick inspection results
        """
        logger.debug(f"Quick scan: {video_file.path}")

        # Build FFmpeg command for quick scan
        cmd = self._build_quick_scan_command(video_file)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.quick_timeout,
                check=False,  # Don't raise on non-zero exit
            )

            return self._process_ffmpeg_result(video_file, result, is_quick=True)

        except subprocess.TimeoutExpired:
            logger.warning(f"Quick scan timeout: {video_file.path}")
            return ScanResult(
                video_file=video_file,
                needs_deep_scan=True,
                error_message="Quick scan timed out - needs deep scan",
            )
        except Exception as e:
            logger.exception(f"Quick scan failed: {video_file.path}")
            return ScanResult(
                video_file=video_file,
                needs_deep_scan=True,
                error_message=f"Quick scan failed: {e}",
            )

    def inspect_deep(self, video_file: VideoFile) -> ScanResult:
        """
        Perform deep inspection of video file (full scan).

        Args:
            video_file: Video file to inspect

        Returns:
            ScanResult: Deep inspection results
        """
        logger.debug(f"Deep scan: {video_file.path}")

        # Build FFmpeg command for deep scan
        cmd = self._build_
