"""Unit tests for utils.py module"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from src.config.video_formats import get_video_extensions
from src.core.formatting import format_file_size
from src.core.video_files import count_all_video_files

pytestmark = pytest.mark.unit

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestCountAllVideoFiles(unittest.TestCase):
    """Test count_all_video_files function"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create test directory structure
        self.sub_dir = self.temp_path / "subdir"
        self.sub_dir.mkdir()

        # Create test files
        (self.temp_path / "video1.mp4").touch()
        (self.temp_path / "video2.avi").touch()
        (self.temp_path / "video3.mkv").touch()
        (self.temp_path / "document.txt").touch()
        (self.temp_path / "image.jpg").touch()

        # Create files in subdirectory
        (self.sub_dir / "video4.mov").touch()
        (self.sub_dir / "video5.wmv").touch()
        (self.sub_dir / "README.md").touch()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_count_recursive_default_extensions(self):
        """Test counting video files recursively with default extensions"""
        count = count_all_video_files(str(self.temp_path), recursive=True)
        assert count == 5  # mp4, avi, mkv, mov, wmv

    def test_count_non_recursive_default_extensions(self):
        """Test counting video files non-recursively with default extensions"""
        count = count_all_video_files(str(self.temp_path), recursive=False)
        assert count == 3  # mp4, avi, mkv only (not subdirectory files)

    def test_count_custom_extensions(self):
        """Test counting with custom extensions"""
        extensions = [".mp4", ".avi"]
        count = count_all_video_files(str(self.temp_path), recursive=True, extensions=extensions)
        assert count == 2  # Only mp4 and avi

    def test_count_no_matching_files(self):
        """Test counting when no files match"""
        extensions = [".xyz"]
        count = count_all_video_files(str(self.temp_path), recursive=True, extensions=extensions)
        assert count == 0

    def test_count_empty_directory(self):
        """Test counting in empty directory"""
        empty_dir = tempfile.mkdtemp()
        try:
            count = count_all_video_files(empty_dir, recursive=True)
            assert count == 0
        finally:
            Path(empty_dir).rmdir()

    def test_count_case_insensitive_extensions(self):
        """Test that extensions are case insensitive"""
        # Create files with uppercase extensions
        (self.temp_path / "video_upper.MP4").touch()
        (self.temp_path / "video_mixed.Avi").touch()

        count = count_all_video_files(str(self.temp_path), recursive=False)
        assert count == 5  # 3 original + 2 new files

    def test_count_nonexistent_directory(self):
        """Test behavior with non-existent directory"""
        # The function returns 0 for non-existent directories
        # (Path.glob handles this gracefully)
        count = count_all_video_files("/nonexistent/directory")
        assert count == 0


class TestFormatFileSize(unittest.TestCase):
    """Test format_file_size function"""

    def test_format_bytes(self):
        """Test formatting bytes with default trim_trailing_zero=True"""
        assert format_file_size(500) == "500 B"
        assert format_file_size(0) == "0 B"
        assert format_file_size(1) == "1 B"

    def test_format_bytes_no_trim(self):
        """Test formatting bytes with trim_trailing_zero=False"""
        assert format_file_size(500, trim_trailing_zero=False) == "500.0 B"
        assert format_file_size(0, trim_trailing_zero=False) == "0.0 B"
        assert format_file_size(1, trim_trailing_zero=False) == "1.0 B"

    def test_format_kilobytes(self):
        """Test formatting kilobytes with default trim_trailing_zero=True"""
        assert format_file_size(1024) == "1 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(2048) == "2 KB"

    def test_format_megabytes(self):
        """Test formatting megabytes with default trim_trailing_zero=True"""
        assert format_file_size(1024 * 1024) == "1 MB"
        assert format_file_size(int(1024 * 1024 * 2.5)) == "2.5 MB"
        assert format_file_size(1024 * 1024 * 100) == "100 MB"

    def test_format_gigabytes(self):
        """Test formatting gigabytes with default trim_trailing_zero=True"""
        assert format_file_size(1024 * 1024 * 1024) == "1 GB"
        assert format_file_size(int(1024 * 1024 * 1024 * 2.5)) == "2.5 GB"

    def test_format_backward_compatibility(self):
        """Test formatting with trim_trailing_zero=False for backward compatibility"""
        assert format_file_size(500, trim_trailing_zero=False) == "500.0 B"
        assert format_file_size(1024, trim_trailing_zero=False) == "1.0 KB"
        assert format_file_size(1024 * 1024, trim_trailing_zero=False) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024, trim_trailing_zero=False) == "1.0 GB"


class TestGetVideoExtensions(unittest.TestCase):
    """Test get_video_extensions function"""

    def test_returns_list(self):
        """Test that function returns a list"""
        extensions = get_video_extensions()
        assert isinstance(extensions, list)

    def test_contains_common_extensions(self):
        """Test that common video extensions are included"""
        extensions = get_video_extensions()
        expected_extensions = [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"]

        for ext in expected_extensions:
            assert ext in extensions

    def test_extensions_are_lowercase(self):
        """Test that all extensions are lowercase"""
        extensions = get_video_extensions()
        for ext in extensions:
            assert ext == ext.lower()

    def test_extensions_start_with_dot(self):
        """Test that all extensions start with a dot"""
        extensions = get_video_extensions()
        for ext in extensions:
            assert ext.startswith(".")

    def test_no_duplicate_extensions(self):
        """Test that there are no duplicate extensions"""
        extensions = get_video_extensions()
        assert len(extensions) == len(set(extensions))

    def test_consistent_return(self):
        """Test that function returns consistent results"""
        extensions1 = get_video_extensions()
        extensions2 = get_video_extensions()
        assert extensions1 == extensions2


if __name__ == "__main__":
    unittest.main()
