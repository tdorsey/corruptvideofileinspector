"""
FFmpeg client for video file inspection and corruption detection.
"""

import logging
import shutil
import subprocess
from typing import Any

from src.config.config import FFmpegConfig
from src.core.errors.errors import FFmpegError
from src.core.models.inspection import VideoFile
from src.core.models.scanning import ScanResult
from src.ffmpeg.corruption_detector import CorruptionDetector

logger = logging.getLogger(__name__)


class FFmpegClient:
    """Client for interacting with FFmpeg to inspect video files."""

    config: FFmpegConfig
    detector: CorruptionDetector
    _ffmpeg_path: str | None

    def __init__(self, config: FFmpegConfig) -> None:
        """Initialize FFmpeg client."""
        self.config = config
        self.detector = CorruptionDetector()
        self._ffmpeg_path = None

        # Find FFmpeg command
        self._find_ffmpeg_command()

        logger.info(f"FFmpegClient initialized with command: {self._ffmpeg_path}")

    def _find_ffmpeg_command(self) -> None:
        """Find and validate FFmpeg command."""
        if self.config.command:
            # Use configured command
            if self._validate_ffmpeg_command(str(self.config.command)):
                self._ffmpeg_path = str(self.config.command)
                return
            logger.warning(f"Configured FFmpeg command not found: {self.config.command}")

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

        msg = "FFmpeg command not found. Please install FFmpeg or configure the path."
        raise FFmpegError(msg)

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

    def _build_quick_scan_command(self, video_file: VideoFile) -> list[str]:
        """
        Build FFmpeg command for quick scan.

        Args:
            video_file: Video file to inspect

        Returns:
            list[str]: FFmpeg command as list
        """
        # Assumption: Quick scan reads first 10 seconds, disables audio, minimal output
        if self._ffmpeg_path is None:
            msg = "FFmpeg path is not set."
            raise FFmpegError(msg)
        return [
            str(self._ffmpeg_path),
            "-v",
            "error",
            "-t",
            (
                str(self.config.quick_scan_duration)
                if hasattr(self.config, "quick_scan_duration")
                else "10"
            ),
            "-i",
            str(video_file.path),
            "-f",
            "null",
            "-",
        ]

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

    def inspect_deep(self, video_file: VideoFile, timeout: int | None = None) -> ScanResult:
        """
        Perform deep inspection of video file (full scan).

        Args:
            video_file: Video file to inspect
            timeout: Timeout in seconds. If None, no timeout is applied.

        Returns:
            ScanResult: Deep inspection results
        """
        logger.debug(f"Deep scan: {video_file.path}")

        # Build FFmpeg command for deep scan
        cmd = self._build_deep_scan_command(video_file)

        # Use configured timeout if none provided
        if timeout is None:
            timeout = self.config.deep_timeout

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return self._process_ffmpeg_result(video_file, result, is_quick=False)
        except subprocess.TimeoutExpired:
            logger.warning(f"Deep scan timeout: {video_file.path}")
            return ScanResult(
                video_file=video_file,
                needs_deep_scan=False,
                error_message="Deep scan timed out",
            )
        except Exception as e:
            logger.exception(f"Deep scan failed: {video_file.path}")
            return ScanResult(
                video_file=video_file,
                needs_deep_scan=False,
                error_message=f"Deep scan failed: {e}",
            )

    def _build_deep_scan_command(self, video_file: VideoFile) -> list[str]:
        """
        Build FFmpeg command for deep scan (full file scan).

        Args:
            video_file: Video file to inspect

        Returns:
            list[str]: FFmpeg command as list
        """
        if self._ffmpeg_path is None:
            msg = "FFmpeg path is not set."
            raise FFmpegError(msg)
        return [
            str(self._ffmpeg_path),
            "-v",
            "error",
            "-i",
            str(video_file.path),
            "-f",
            "null",
            "-",
        ]

    def inspect_full(self, video_file: VideoFile) -> ScanResult:
        """
        Perform full inspection of video file without timeout.

        Args:
            video_file: Video file to inspect

        Returns:
            ScanResult: Full inspection results
        """
        logger.debug(f"Full scan (no timeout): {video_file.path}")

        # Build FFmpeg command for full scan (same as deep scan)
        cmd = self._build_deep_scan_command(video_file)

        try:
            # Run without timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=None,
                check=False,
            )
            return self._process_ffmpeg_result(video_file, result, is_quick=False)
        except Exception as e:
            logger.exception(f"Full scan failed: {video_file.path}")
            return ScanResult(
                video_file=video_file,
                needs_deep_scan=False,
                error_message=f"Full scan failed: {e}",
            )

    def test_installation(self) -> dict[str, Any]:
        """Test FFmpeg installation and return diagnostic information.

        Returns:
            dict: Dictionary containing test results with keys:
                - ffmpeg_available: bool
                - ffprobe_available: bool
                - ffmpeg_path: str | None
                - version_info: str | None
                - supported_formats: list[str] | None
        """
        results: dict[str, bool | str | None | list[str]] = {
            "ffmpeg_available": False,
            "ffprobe_available": False,
            "ffmpeg_path": None,
            "version_info": None,
            "supported_formats": None,
        }

        # Test FFmpeg availability
        if self._ffmpeg_path:
            results["ffmpeg_path"] = self._ffmpeg_path
            results["ffmpeg_available"] = self._validate_ffmpeg_command(self._ffmpeg_path)

            # Get version info
            if results["ffmpeg_available"]:
                try:
                    version_result = subprocess.run(
                        [self._ffmpeg_path, "-version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False,
                    )
                    if version_result.returncode == 0:
                        # Extract first line which contains version
                        first_line = version_result.stdout.split("\n")[0]
                        results["version_info"] = first_line.strip()
                except Exception:
                    pass

                # Get supported formats (basic list)
                try:
                    formats_result = subprocess.run(
                        [self._ffmpeg_path, "-formats"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False,
                    )
                    if formats_result.returncode == 0:
                        # Extract common video formats
                        common_formats = ["mp4", "mkv", "avi", "mov", "wmv", "flv"]
                        supported = []
                        output_lower = formats_result.stdout.lower()
                        for fmt in common_formats:
                            if fmt in output_lower:
                                supported.append(fmt)
                        results["supported_formats"] = supported
                except Exception:
                    pass

        # Test FFprobe (usually comes with FFmpeg)
        ffprobe_cmd = (
            self._ffmpeg_path.replace("ffmpeg", "ffprobe") if self._ffmpeg_path else "ffprobe"
        )
        try:
            probe_result = subprocess.run(
                [ffprobe_cmd, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            results["ffprobe_available"] = probe_result.returncode == 0
        except Exception:
            results["ffprobe_available"] = False

        return results

    def _process_ffmpeg_result(
        self,
        video_file: VideoFile,
        result: subprocess.CompletedProcess[str],
        is_quick: bool,
    ) -> ScanResult:
        """
        Process the result of an FFmpeg subprocess run.

        Args:
            video_file: Video file that was scanned
            result: CompletedProcess from subprocess.run
            is_quick: Whether this was a quick scan

        Returns:
            ScanResult: The scan result object
        """
        error_output: str = result.stderr or ""

        # Use detector to analyze FFmpeg output for corruption
        analysis = self.detector.analyze_ffmpeg_output(error_output, result.returncode, is_quick)

        error_message: str | None = analysis.error_message or None
        if result.returncode != 0 and not error_message:
            error_message = error_output.strip() or "FFmpeg reported errors"

        return ScanResult(
            video_file=video_file,
            needs_deep_scan=analysis.needs_deep_scan,
            error_message=error_message or "",
        )
