"""
Integration tests for utils module
"""

import contextlib
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from src.core.video_files import count_all_video_files
from src.core.formatting import format_file_size
from src.config.video_formats import get_video_extensions

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytestmark = pytest.mark.integration


class TestUtilsIntegration(unittest.TestCase):
    """Integration tests for utility functions"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_files = []

    def tearDown(self):
        """Clean up test environment"""
        # Clean up test files
        for file_path in self.test_files:
            with contextlib.suppress(FileNotFoundError):
                Path(file_path).unlink()

        # Remove test directory
        with contextlib.suppress(OSError):
            Path(self.test_dir).rmdir()

    def create_test_file(self, filename: str, content: str = "test content") -> str:
        """Create a test file and return its path"""
        file_path = Path(self.test_dir) / filename
        file_path.write_text(content)
        self.test_files.append(str(file_path))
        return str(file_path)

    def test_count_video_files_empty_directory(self):
        """Test counting video files in an empty directory"""
        count = count_all_video_files(self.test_dir)
        assert count == 0

    def test_count_video_files_with_video_files(self):
        """Test counting video files in directory with video files"""
        # Create some video files
        self.create_test_file("test1.mp4")
        self.create_test_file("test2.avi")
        self.create_test_file("test3.mkv")
        self.create_test_file("not_video.txt")

        count = count_all_video_files(self.test_dir)
        assert count == 3

    def test_count_video_files_case_insensitive(self):
        """Test that file counting is case insensitive"""
        self.create_test_file("TEST.MP4")
        self.create_test_file("video.AVI")
        self.create_test_file("movie.MkV")

        count = count_all_video_files(self.test_dir)
        assert count == 3

    def test_count_video_files_custom_extensions(self):
        """Test counting with custom extensions"""
        self.create_test_file("test.mp4")
        self.create_test_file("test.avi")
        self.create_test_file("test.custom")

        # Count only mp4 files
        count = count_all_video_files(self.test_dir, extensions=[".mp4"])
        assert count == 1

        # Count mp4 and custom files
        count = count_all_video_files(self.test_dir, extensions=[".mp4", ".custom"])
        assert count == 2

    def test_count_video_files_recursive(self):
        """Test recursive directory scanning"""
        # Create files in root
        self.create_test_file("root.mp4")

        # Create subdirectory and files
        subdir = Path(self.test_dir) / "subdir"
        subdir.mkdir(parents=True, exist_ok=True)

        subfile = subdir / "sub.avi"
        subfile.write_text("test")
        self.test_files.append(str(subfile))

        # Test recursive (default)
        count = count_all_video_files(self.test_dir, recursive=True)
        assert count == 2

        # Test non-recursive
        count = count_all_video_files(self.test_dir, recursive=False)
        assert count == 1

    def test_count_video_files_invalid_directory(self):
        """Test behavior with invalid directory"""
        # The function actually returns 0 for non-existent directories
        # instead of raising an exception (it catches and re-raises exceptions)
        count = count_all_video_files("/nonexistent/directory")
        assert count == 0

    def test_format_file_size(self):
        """Test file size formatting with default trim_trailing_zero=True"""
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512 B"
        assert format_file_size(1024) == "1 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(1024 * 1024) == "1 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1 GB"

    def test_format_file_size_backward_compatibility(self):
        """Test file size formatting with trim_trailing_zero=False for backward compatibility"""
        assert format_file_size(0, trim_trailing_zero=False) == "0.0 B"
        assert format_file_size(512, trim_trailing_zero=False) == "512.0 B"
        assert format_file_size(1024, trim_trailing_zero=False) == "1.0 KB"
        assert format_file_size(1536, trim_trailing_zero=False) == "1.5 KB"
        assert format_file_size(1024 * 1024, trim_trailing_zero=False) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024, trim_trailing_zero=False) == "1.0 GB"

    def test_get_video_extensions(self):
        """Test getting video extensions list"""
        extensions = get_video_extensions()

        # Should return a list
        assert isinstance(extensions, list)

        # Should contain common video formats
        expected_extensions = [".mp4", ".avi", ".mkv", ".mov", ".wmv"]
        for ext in expected_extensions:
            assert ext in extensions

        # All extensions should start with a dot
        for ext in extensions:
            assert ext.startswith(".")

    def test_integration_with_test_videos_directory(self):
        """Test integration with actual test-videos directory"""
        test_videos_dir = Path(__file__).resolve().parent.parent / "test-videos"

        if test_videos_dir.exists():
            # This should not raise an exception
            count = count_all_video_files(str(test_videos_dir))
            # The count depends on what's in the test-videos directory
            assert isinstance(count, int)
            assert count >= 0


if __name__ == "__main__":
    unittest.main()
