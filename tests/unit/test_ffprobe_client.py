"""
Unit tests for FFprobe client functionality.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from src.config.config import FFmpegConfig
from src.core.models.inspection import VideoFile
from src.core.models.probe import ProbeResult
from src.ffmpeg.ffprobe_client import FFprobeClient


class TestFFprobeClient:
    """Test FFprobe client functionality."""

    def test_ffprobe_client_initialization(self):
        """Test FFprobe client initialization."""
        config = FFmpegConfig(command=Path("/usr/bin/ffmpeg"))

        with patch.object(FFprobeClient, "_find_ffprobe_command"):
            client = FFprobeClient(config)
            assert client.config == config

    def test_validate_ffprobe_command_success(self):
        """Test successful FFprobe command validation."""
        config = FFmpegConfig()
        client = FFprobeClient.__new__(FFprobeClient)
        client.config = config

        mock_result = Mock()
        mock_result.stdout = "ffprobe version 4.4.0"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            result = client._validate_ffprobe_command("ffprobe")
            assert result is True

    def test_validate_ffprobe_command_failure(self):
        """Test failed FFprobe command validation."""
        config = FFmpegConfig()
        client = FFprobeClient.__new__(FFprobeClient)
        client.config = config

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = client._validate_ffprobe_command("nonexistent")
            assert result is False

    def test_build_probe_command(self):
        """Test FFprobe command building."""
        config = FFmpegConfig()
        client = FFprobeClient.__new__(FFprobeClient)
        client.config = config
        client._ffprobe_path = "/usr/bin/ffprobe"

        video_file = VideoFile(path=Path("/test/video.mp4"))
        cmd = client._build_probe_command(video_file)

        expected = [
            "/usr/bin/ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            "/test/video.mp4",
        ]
        assert cmd == expected

    def test_process_probe_result_success(self):
        """Test successful probe result processing."""
        config = FFmpegConfig()
        client = FFprobeClient.__new__(FFprobeClient)
        client.config = config

        video_file = VideoFile(path=Path("/test/video.mp4"))

        # Mock successful FFprobe output
        probe_output = {
            "streams": [
                {
                    "index": 0,
                    "codec_name": "h264",
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "duration": "120.5",
                },
                {
                    "index": 1,
                    "codec_name": "aac",
                    "codec_type": "audio",
                    "duration": "120.5",
                },
            ],
            "format": {
                "filename": "/test/video.mp4",
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                "duration": "120.500000",
                "size": "50000000",
            },
        }

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(probe_output)
        mock_result.stderr = ""

        result = client._process_probe_result(video_file, mock_result)

        assert isinstance(result, ProbeResult)
        assert result.success is True
        assert result.file_path == video_file.path
        assert len(result.streams) == 2
        assert result.has_video_streams is True
        assert result.has_audio_streams is True
        assert result.duration == 120.5
        assert result.is_valid_video_file is True

    def test_process_probe_result_failure(self):
        """Test failed probe result processing."""
        config = FFmpegConfig()
        client = FFprobeClient.__new__(FFprobeClient)
        client.config = config

        video_file = VideoFile(path=Path("/test/invalid.mp4"))

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Invalid data found when processing input"

        result = client._process_probe_result(video_file, mock_result)

        assert isinstance(result, ProbeResult)
        assert result.success is False
        assert result.file_path == video_file.path
        assert result.is_valid_video_file is False
        # Ensure error_message is present before using 'in'
        assert result.error_message is not None
        assert "Invalid data found" in result.error_message

    def test_process_probe_result_invalid_json(self):
        """Test probe result processing with invalid JSON."""
        config = FFmpegConfig()
        client = FFprobeClient.__new__(FFprobeClient)
        client.config = config

        video_file = VideoFile(path=Path("/test/video.mp4"))

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json content"
        mock_result.stderr = ""

        result = client._process_probe_result(video_file, mock_result)

        assert isinstance(result, ProbeResult)
        assert result.success is False
        assert "Failed to parse probe output" in result.error_message

    def test_probe_file_timeout(self):
        """Test probe file with timeout."""
        config = FFmpegConfig(probe_timeout=5)

        with patch.object(FFprobeClient, "_find_ffprobe_command"):
            client = FFprobeClient(config)
            client._ffprobe_path = "/usr/bin/ffprobe"

        video_file = VideoFile(path=Path("/test/video.mp4"))

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ffprobe", 5)):
            result = client.probe_file(video_file, timeout=1)

            assert isinstance(result, ProbeResult)
            assert result.success is False
            assert result.error_message is not None
            assert "timed out" in result.error_message

    def test_probe_file_no_ffprobe_available(self):
        """Test probe file when FFprobe is not available."""
        config = FFmpegConfig()

        with patch.object(FFprobeClient, "_find_ffprobe_command"):
            client = FFprobeClient(config)
            client._ffprobe_path = None

        video_file = VideoFile(path=Path("/test/video.mp4"))
        result = client.probe_file(video_file)

        assert isinstance(result, ProbeResult)
        assert result.success is False
        assert "FFprobe command not available" in result.error_message

    def test_test_installation(self):
        """Test installation testing functionality."""
        config = FFmpegConfig()

        with patch.object(FFprobeClient, "_find_ffprobe_command"):
            client = FFprobeClient(config)
            client._ffprobe_path = "/usr/bin/ffprobe"

        # Mock version check
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "ffprobe version 4.4.0"

        # Mock JSON test
        json_result = Mock()
        json_result.returncode = 0
        json_result.stdout = '{"streams": []}'

        with patch("subprocess.run", side_effect=[version_result, json_result]):
            results = client.test_installation()

            assert results["ffprobe_available"] is True
            assert results["ffprobe_path"] == "/usr/bin/ffprobe"
            # Ensure version_info is a string before using 'in'
            assert results["version_info"] is not None
            assert "version 4.4.0" in results["version_info"]
            assert results["can_parse_json"] is True
