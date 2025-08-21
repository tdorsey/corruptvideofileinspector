"""
Unit tests for scanner content-based video detection.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.core.scanner import VideoScanner

pytestmark = pytest.mark.unit


class TestScannerContentDetection(unittest.TestCase):
    """Test VideoScanner content-based detection"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create test files
        self.video_file = self.temp_path / "real_video.unknown"
        self.fake_video = self.temp_path / "fake_video.mp4"
        self.text_file = self.temp_path / "document.txt"

        for f in [self.video_file, self.fake_video, self.text_file]:
            f.touch()

        # Mock config
        self.mock_config = Mock()
        self.mock_config.output.default_output_dir = self.temp_path / "output"
        self.mock_config.scan.extensions = [".mp4", ".avi", ".mkv"]
        self.mock_config.scan.recursive = True
        self.mock_config.scan.use_content_detection = True
        self.mock_config.scan.ffprobe_timeout = 30
        self.mock_config.scan.extension_filter = []
        self.mock_config.ffmpeg.command = Path("/usr/bin/ffmpeg")
        self.mock_config.ffmpeg.quick_timeout = 30
        self.mock_config.ffmpeg.deep_timeout = 900
        self.mock_config.processing.max_workers = 2

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("src.core.scanner.FFmpegClient")
    def test_content_detection_enabled(self, mock_ffmpeg_client_class):
        """Test scanner with content detection enabled"""
        # Mock FFmpeg client behavior
        mock_client = Mock()
        mock_client.is_video_file.side_effect = lambda path, timeout: {
            self.video_file: True,  # Real video file detected
            self.fake_video: False,  # Fake video file rejected
            self.text_file: False,  # Text file rejected
        }.get(path, False)
        mock_ffmpeg_client_class.return_value = mock_client

        with patch("src.core.scanner.load_config", return_value=self.mock_config):
            scanner = VideoScanner()
            video_files = scanner.locate_video_files(self.temp_path, recursive=False)

        # Should only find the real video file
        assert len(video_files) == 1
        assert video_files[0].path == self.video_file

        # Verify FFprobe was called for all files
        assert mock_client.is_video_file.call_count == 3

    def test_content_detection_disabled(self):
        """Test scanner with content detection disabled (extension-based)"""
        self.mock_config.scan.use_content_detection = False

        with patch("src.core.scanner.load_config", return_value=self.mock_config):
            scanner = VideoScanner()
            video_files = scanner.locate_video_files(self.temp_path, recursive=False)

        # Should only find files with video extensions
        assert len(video_files) == 1
        assert video_files[0].path == self.fake_video  # Only .mp4 file

    @patch("src.core.scanner.FFmpegClient")
    def test_content_detection_with_extension_filter(self, mock_ffmpeg_client_class):
        """Test content detection with extension pre-filter"""
        self.mock_config.scan.extension_filter = [".mp4", ".mkv"]

        mock_client = Mock()
        mock_client.is_video_file.return_value = True
        mock_ffmpeg_client_class.return_value = mock_client

        with patch("src.core.scanner.load_config", return_value=self.mock_config):
            scanner = VideoScanner()
            video_files = scanner.locate_video_files(self.temp_path, recursive=False)

        # Should only analyze files matching extension filter
        assert len(video_files) == 1
        assert video_files[0].path == self.fake_video

        # Should only call FFprobe for the .mp4 file (matches filter)
        mock_client.is_video_file.assert_called_once_with(self.fake_video, timeout=30)

    @patch("src.core.scanner.FFmpegClient")
    def test_content_detection_fallback_on_client_init_failure(self, mock_ffmpeg_client_class):
        """Test fallback to extension-based when FFmpeg client init fails"""
        mock_ffmpeg_client_class.side_effect = Exception("FFmpeg not found")

        with patch("src.core.scanner.load_config", return_value=self.mock_config):
            scanner = VideoScanner()
            video_files = scanner.locate_video_files(self.temp_path, recursive=False)

        # Should fall back to extension-based detection
        assert len(video_files) == 1
        assert video_files[0].path == self.fake_video  # Only .mp4 file

    @patch("src.core.scanner.FFmpegClient")
    def test_content_detection_fallback_on_analysis_failure(self, mock_ffmpeg_client_class):
        """Test fallback to extension check when content analysis fails for a file"""
        mock_client = Mock()

        # Simulate FFprobe failure for one file, success for others
        def mock_analysis(path, timeout):
            class AnalysisError(Exception):
                pass

            if path == self.fake_video:
                raise AnalysisError("Analysis failed")
            return path == self.video_file  # Only real video returns True

        mock_client.is_video_file.side_effect = mock_analysis
        mock_ffmpeg_client_class.return_value = mock_client

        with patch("src.core.scanner.load_config", return_value=self.mock_config):
            scanner = VideoScanner()
            video_files = scanner.locate_video_files(self.temp_path, recursive=False)

        # Should find both files: real_video via content detection, fake_video via extension fallback
        assert len(video_files) == 2
        found_paths = {vf.path for vf in video_files}
        assert self.video_file in found_paths
        assert self.fake_video in found_paths

    def test_recursive_scanning_content_detection(self):
        """Test recursive scanning with content detection"""
        # Create subdirectory with video file
        subdir = self.temp_path / "subdir"
        subdir.mkdir()
        sub_video = subdir / "sub_video.unknown"
        sub_video.touch()

        with patch("src.core.scanner.FFmpegClient") as mock_ffmpeg_client_class:
            mock_client = Mock()
            mock_client.is_video_file.side_effect = lambda path, timeout: path.name.startswith(
                "sub_video"
            )
            mock_ffmpeg_client_class.return_value = mock_client

            with patch("src.core.scanner.load_config", return_value=self.mock_config):
                scanner = VideoScanner()
                video_files = scanner.locate_video_files(self.temp_path, recursive=True)

        # Should find the video in subdirectory
        found_paths = {vf.path for vf in video_files}
        assert sub_video in found_paths
