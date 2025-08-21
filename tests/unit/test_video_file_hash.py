"""Unit tests for VideoFile model with SHA-256 hash support"""

import tempfile
import unittest
from pathlib import Path

import pytest

from src.core.models.inspection import VideoFile

pytestmark = pytest.mark.unit


class TestVideoFileWithHash(unittest.TestCase):
    """Test VideoFile model with SHA-256 hash functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create a test video file
        self.test_file = self.temp_path / "test_video.mp4"
        self.test_file.write_bytes(b"fake video content")

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_video_file_with_hash(self):
        """Test VideoFile creation with SHA-256 hash"""
        test_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

        video_file = VideoFile(path=self.test_file, sha256_hash=test_hash)

        assert video_file.path == self.test_file
        assert video_file.sha256_hash == test_hash
        assert video_file.short_hash == "abcdef12...7890"

    def test_video_file_without_hash(self):
        """Test VideoFile creation without SHA-256 hash"""
        video_file = VideoFile(path=self.test_file)

        assert video_file.path == self.test_file
        assert video_file.sha256_hash == ""
        assert video_file.short_hash == "no-hash"

    def test_video_file_empty_hash(self):
        """Test VideoFile with empty SHA-256 hash"""
        video_file = VideoFile(path=self.test_file, sha256_hash="")

        assert video_file.sha256_hash == ""
        assert video_file.short_hash == "no-hash"

    def test_short_hash_property_with_short_input(self):
        """Test short_hash property with short hash input"""
        short_hash = "abcd1234"
        video_file = VideoFile(path=self.test_file, sha256_hash=short_hash)

        # Should return the full hash if it's too short
        assert video_file.short_hash == short_hash

    def test_short_hash_property_with_medium_input(self):
        """Test short_hash property with medium-length hash input"""
        medium_hash = "abcdef1234567890abc"  # 19 chars
        video_file = VideoFile(path=self.test_file, sha256_hash=medium_hash)

        # Construct a medium-length hash based on the threshold
        medium_hash_length = 12
        prefix = "abcdef12"
        suffix = "0abc"
        medium_hash = prefix + "x" * (medium_hash_length - len(prefix) - len(suffix)) + suffix
        video_file = VideoFile(path=self.test_file, sha256_hash=medium_hash)

        expected_short = f"{prefix}...{suffix}"
        assert video_file.short_hash == expected_short

    def test_video_file_backwards_compatibility(self):
        """Test that existing VideoFile functionality still works"""
        video_file = VideoFile(path=self.test_file, sha256_hash="testhash")

        # Test existing properties
        assert video_file.filename == str(self.test_file)
        assert video_file.name == "test_video.mp4"
        assert video_file.stem == "test_video"
        assert video_file.suffix == ".mp4"
        assert video_file.size > 0


if __name__ == "__main__":
    unittest.main()
