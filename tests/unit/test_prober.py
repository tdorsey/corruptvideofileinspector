"""
Unit tests for video prober module.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.models.inspection import VideoFile
from src.core.prober import VideoProber

pytestmark = pytest.mark.unit


class TestVideoProber(unittest.TestCase):
    """Test VideoProber class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.prober = VideoProber()

        # Create a test file
        self.test_file = self.temp_path / "test_video.mp4"
        self.test_file.write_bytes(b"fake video content for testing")

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_prober_initialization(self):
        """Test prober initialization"""
        prober = VideoProber()
        assert isinstance(prober, VideoProber)

    @patch("src.core.prober.calculate_sha256_hash")
    def test_create_video_file_with_hash_success(self, mock_calculate_hash):
        """Test successful video file creation with hash"""
        mock_calculate_hash.return_value = "abcd1234567890abcdef"

        result = self.prober.create_video_file_with_hash(self.test_file)

        assert isinstance(result, VideoFile)
        assert result.path == self.test_file
        assert result.sha256_hash == "abcd1234567890abcdef"
        mock_calculate_hash.assert_called_once_with(self.test_file)

    @patch("src.core.prober.calculate_sha256_hash")
    def test_create_video_file_with_hash_failure(self, mock_calculate_hash):
        """Test video file creation when hash calculation fails"""
        mock_calculate_hash.side_effect = Exception("Hash calculation failed")

        result = self.prober.create_video_file_with_hash(self.test_file)

        assert isinstance(result, VideoFile)
        assert result.path == self.test_file
        assert result.sha256_hash == ""
        mock_calculate_hash.assert_called_once_with(self.test_file)

    @patch("src.core.prober.calculate_sha256_hash")
    def test_probe_video_file(self, mock_calculate_hash):
        """Test probing video file"""
        mock_calculate_hash.return_value = "test_hash_123"

        result = self.prober.probe_video_file(self.test_file)

        assert isinstance(result, VideoFile)
        assert result.path == self.test_file
        assert result.sha256_hash == "test_hash_123"

    @patch("src.core.prober.calculate_sha256_hash")
    def test_calculate_file_hash_success(self, mock_calculate_hash):
        """Test successful hash calculation"""
        mock_calculate_hash.return_value = "successful_hash"

        result = self.prober.calculate_file_hash(self.test_file)

        assert result == "successful_hash"
        mock_calculate_hash.assert_called_once_with(self.test_file)

    @patch("src.core.prober.calculate_sha256_hash")
    def test_calculate_file_hash_failure(self, mock_calculate_hash):
        """Test hash calculation when it fails"""
        mock_calculate_hash.side_effect = Exception("Hash failed")

        result = self.prober.calculate_file_hash(self.test_file)

        assert result == ""
        mock_calculate_hash.assert_called_once_with(self.test_file)

    def test_short_hash_property(self):
        """Test that VideoFile short_hash property works correctly"""
        with patch("src.core.prober.calculate_sha256_hash") as mock_hash:
            mock_hash.return_value = "abcd1234567890abcdef1234567890abcdef123456"

            result = self.prober.create_video_file_with_hash(self.test_file)

            # Should return shortened version
            expected_short = "abcd1234...3456"
            assert result.short_hash == expected_short
