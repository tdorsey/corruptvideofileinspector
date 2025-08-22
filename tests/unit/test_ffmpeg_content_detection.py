"""
Unit tests for FFmpeg content-based video detection.
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.config.config import FFmpegConfig
from src.core.errors.errors import FFmpegError
from src.ffmpeg.ffmpeg_client import FFmpegClient

pytestmark = pytest.mark.unit


class TestFFmpegContentDetection(unittest.TestCase):
    """Test FFmpeg content-based video detection"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create test files
        self.video_file = self.temp_path / "test.mp4"
        self.text_file = self.temp_path / "test.txt"
        self.video_file.touch()
        self.text_file.touch()

        # Mock config
        self.mock_config = FFmpegConfig(
            command=Path("/usr/bin/ffmpeg"), quick_timeout=30, deep_timeout=900
        )

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("subprocess.run")
    def test_analyze_streams_success(self, mock_run):
        """Test successful stream analysis"""
        # Mock FFprobe success response
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {
                "streams": [
                    {"codec_type": "video", "codec_name": "h264"},
                    {"codec_type": "audio", "codec_name": "aac"},
                ]
            }
        )
        mock_run.return_value = mock_result

        with patch.object(FFmpegClient, "_validate_ffmpeg_command", return_value=True):
            client = FFmpegClient(self.mock_config)
            result = client.analyze_streams(self.video_file)

        assert "streams" in result
        assert len(result["streams"]) == 2
        assert result["streams"][0]["codec_type"] == "video"

    @patch("subprocess.run")
    def test_analyze_streams_failure(self, mock_run):
        """Test stream analysis when FFprobe fails"""
        # Mock FFprobe failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid data found"
        mock_run.return_value = mock_result

        with patch.object(FFmpegClient, "_validate_ffmpeg_command", return_value=True):
            client = FFmpegClient(self.mock_config)
            result = client.analyze_streams(self.video_file)

        assert result == {"streams": []}

    @patch("subprocess.run")
    def test_analyze_streams_timeout(self, mock_run):
        """Test stream analysis timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=30)

        with patch.object(FFmpegClient, "_validate_ffmpeg_command", return_value=True):
            client = FFmpegClient(self.mock_config)

            with pytest.raises(FFmpegError, match="FFprobe timeout"):
                client.analyze_streams(self.video_file, timeout=30)

    @patch("subprocess.run")
    def test_analyze_streams_invalid_json(self, mock_run):
        """Test stream analysis with invalid JSON response"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result

        with patch.object(FFmpegClient, "_validate_ffmpeg_command", return_value=True):
            client = FFmpegClient(self.mock_config)
            result = client.analyze_streams(self.video_file)

        assert result == {"streams": []}

    @patch.object(FFmpegClient, "analyze_streams")
    def test_is_video_file_true(self, mock_analyze):
        """Test is_video_file returns True for video files"""
        mock_analyze.return_value = {
            "streams": [
                {"codec_type": "video", "codec_name": "h264"},
                {"codec_type": "audio", "codec_name": "aac"},
            ]
        }

        with patch.object(FFmpegClient, "_validate_ffmpeg_command", return_value=True):
            client = FFmpegClient(self.mock_config)
            result = client.is_video_file(self.video_file)

        assert result is True

    @patch.object(FFmpegClient, "analyze_streams")
    def test_is_video_file_false_no_video_stream(self, mock_analyze):
        """Test is_video_file returns False when no video streams"""
        mock_analyze.return_value = {"streams": [{"codec_type": "audio", "codec_name": "aac"}]}

        with patch.object(FFmpegClient, "_validate_ffmpeg_command", return_value=True):
            client = FFmpegClient(self.mock_config)
            result = client.is_video_file(self.video_file)

        assert result is False

    @patch.object(FFmpegClient, "analyze_streams")
    def test_is_video_file_false_no_streams(self, mock_analyze):
        """Test is_video_file returns False when no streams"""
        mock_analyze.return_value = {"streams": []}

        with patch.object(FFmpegClient, "_validate_ffmpeg_command", return_value=True):
            client = FFmpegClient(self.mock_config)
            result = client.is_video_file(self.video_file)

        assert result is False

    @patch.object(FFmpegClient, "analyze_streams")
    def test_is_video_file_error_handling(self, mock_analyze):
        """Test is_video_file handles errors gracefully"""
        mock_analyze.side_effect = FFmpegError("Analysis failed")

        with patch.object(FFmpegClient, "_validate_ffmpeg_command", return_value=True):
            client = FFmpegClient(self.mock_config)
            result = client.is_video_file(self.video_file)

        assert result is False

    def test_get_ffprobe_command_with_ffmpeg_path(self):
        """Test FFprobe command derivation from FFmpeg path"""
        with patch.object(FFmpegClient, "_validate_ffmpeg_command", return_value=True):
            client = FFmpegClient(self.mock_config)
            client._ffmpeg_path = "/usr/bin/ffmpeg"

            ffprobe_cmd = client._get_ffprobe_command()
            assert ffprobe_cmd == "/usr/bin/ffprobe"

    def test_get_ffprobe_command_fallback(self):
        """Test FFprobe command fallback when no FFmpeg path"""
        with patch.object(FFmpegClient, "_validate_ffmpeg_command", return_value=True):
            client = FFmpegClient(self.mock_config)
            client._ffmpeg_path = None

            ffprobe_cmd = client._get_ffprobe_command()
            assert ffprobe_cmd == "ffprobe"
