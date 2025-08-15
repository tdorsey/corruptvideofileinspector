"""
FFprobe client for video file metadata extraction and analysis.
"""

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from src.config.config import FFmpegConfig
from src.core.errors.errors import FFmpegError
from src.core.models.inspection import VideoFile
from src.core.models.probe import FormatInfo, ProbeResult, StreamInfo

logger = logging.getLogger(__name__)


class FFprobeClient:
    """Client for interacting with FFprobe to extract video file metadata."""
    
    def __init__(self, config: FFmpegConfig) -> None:
        """Initialize FFprobe client."""
        self.config = config
        self._ffprobe_path: Optional[str] = None
        
        # Find FFprobe command
        self._find_ffprobe_command()
        
        logger.info(f"FFprobeClient initialized with command: {self._ffprobe_path}")
    
    def _find_ffprobe_command(self) -> None:
        """Find and validate FFprobe command."""
        # Try deriving from FFmpeg path first
        if self.config.command:
            ffprobe_from_ffmpeg = str(self.config.command).replace("ffmpeg", "ffprobe")
            if self._validate_ffprobe_command(ffprobe_from_ffmpeg):
                self._ffprobe_path = ffprobe_from_ffmpeg
                return
        
        # Try common locations
        common_paths = ["ffprobe", "/usr/bin/ffprobe", "/usr/local/bin/ffprobe"]
        
        for cmd in common_paths:
            if self._validate_ffprobe_command(cmd):
                self._ffprobe_path = cmd
                logger.info(f"Found FFprobe at: {cmd}")
                return
        
        # Try using shutil.which
        which_result = shutil.which("ffprobe")
        if which_result and self._validate_ffprobe_command(which_result):
            self._ffprobe_path = which_result
            logger.info(f"Found FFprobe via which: {which_result}")
            return
        
        raise FFmpegError("FFprobe command not found. Please install FFmpeg/FFprobe or configure the path.")
    
    def _validate_ffprobe_command(self, command: str) -> bool:
        """Validate that a command is a working FFprobe installation."""
        try:
            result = subprocess.run(
                [command, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            return "ffprobe version" in result.stdout.lower()
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False
    
    def probe_file(self, video_file: VideoFile, timeout: Optional[int] = None) -> ProbeResult:
        """
        Probe video file to extract metadata and stream information.
        
        Args:
            video_file: Video file to probe
            timeout: Timeout in seconds. If None, uses quick_timeout from config.
        
        Returns:
            ProbeResult: Probe analysis results
        """
        if self._ffprobe_path is None:
            return ProbeResult(
                file_path=video_file.path,
                success=False,
                error_message="FFprobe command not available",
                file_size=video_file.size,
            )
        
        if timeout is None:
            timeout = self.config.quick_timeout
        
        logger.debug(f"Probing file: {video_file.path}")
        
        # Build FFprobe command for JSON output
        cmd = self._build_probe_command(video_file)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            
            return self._process_probe_result(video_file, result)
            
        except subprocess.TimeoutExpired:
            logger.warning(f"FFprobe timeout: {video_file.path}")
            return ProbeResult(
                file_path=video_file.path,
                success=False,
                error_message=f"Probe timed out after {timeout}s",
                file_size=video_file.size,
            )
        except Exception as e:
            logger.exception(f"FFprobe failed: {video_file.path}")
            return ProbeResult(
                file_path=video_file.path,
                success=False,
                error_message=f"Probe failed: {e}",
                file_size=video_file.size,
            )
    
    def _build_probe_command(self, video_file: VideoFile) -> list[str]:
        """
        Build FFprobe command for metadata extraction.
        
        Args:
            video_file: Video file to probe
        
        Returns:
            list[str]: FFprobe command as list
        """
        return [
            str(self._ffprobe_path),
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_file.path),
        ]
    
    def _process_probe_result(self, video_file: VideoFile, result: subprocess.CompletedProcess) -> ProbeResult:
        """
        Process FFprobe result and create ProbeResult.
        
        Args:
            video_file: Video file that was probed
            result: Subprocess result from FFprobe
        
        Returns:
            ProbeResult: Processed probe result
        """
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown FFprobe error"
            logger.warning(f"FFprobe failed for {video_file.path}: {error_msg}")
            return ProbeResult(
                file_path=video_file.path,
                success=False,
                error_message=error_msg,
                file_size=video_file.size,
                raw_output=result.stderr,
            )
        
        try:
            # Parse JSON output
            probe_data = json.loads(result.stdout)
            
            # Extract streams
            streams = []
            if "streams" in probe_data:
                for stream_data in probe_data["streams"]:
                    stream = StreamInfo.from_ffprobe_stream(stream_data)
                    streams.append(stream)
            
            # Extract format info
            format_info = None
            if "format" in probe_data:
                format_info = FormatInfo.from_ffprobe_format(probe_data["format"])
            
            # Determine overall duration
            duration = None
            if format_info and format_info.duration:
                duration = format_info.duration
            elif streams:
                # Use longest stream duration if format duration not available
                stream_durations = [s.duration for s in streams if s.duration]
                if stream_durations:
                    duration = max(stream_durations)
            
            return ProbeResult(
                file_path=video_file.path,
                success=True,
                streams=streams,
                format_info=format_info,
                duration=duration,
                file_size=video_file.size,
                raw_output=result.stdout,
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse FFprobe JSON output for {video_file.path}: {e}")
            return ProbeResult(
                file_path=video_file.path,
                success=False,
                error_message=f"Failed to parse probe output: {e}",
                file_size=video_file.size,
                raw_output=result.stdout,
            )
        except Exception as e:
            logger.exception(f"Error processing probe result for {video_file.path}")
            return ProbeResult(
                file_path=video_file.path,
                success=False,
                error_message=f"Error processing probe result: {e}",
                file_size=video_file.size,
                raw_output=result.stdout,
            )
    
    def test_installation(self) -> Dict[str, Any]:
        """
        Test FFprobe installation and return diagnostic information.
        
        Returns:
            dict: Dictionary containing test results
        """
        results: Dict[str, Any] = {
            "ffprobe_available": False,
            "ffprobe_path": None,
            "version_info": None,
            "can_parse_json": False,
        }
        
        if self._ffprobe_path:
            results["ffprobe_path"] = self._ffprobe_path
            results["ffprobe_available"] = True
            
            # Get version info
            try:
                version_result = subprocess.run(
                    [self._ffprobe_path, "-version"],
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
            
            # Test JSON output capability
            try:
                json_test = subprocess.run(
                    [self._ffprobe_path, "-print_format", "json", "-f", "lavfi", "-i", "testsrc2=duration=0.1:size=320x240:rate=1"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if json_test.returncode == 0:
                    # Try to parse output as JSON
                    json.loads(json_test.stdout)
                    results["can_parse_json"] = True
            except Exception:
                pass
        
        return results