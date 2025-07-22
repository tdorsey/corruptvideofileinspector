"""
Unit tests for utils.py module
"""
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

# Add parent directory to path for importing
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import count_all_video_files, format_file_size, get_video_extensions


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
        self.assertEqual(count, 5)  # mp4, avi, mkv, mov, wmv
    
    def test_count_non_recursive_default_extensions(self):
        """Test counting video files non-recursively with default extensions"""
        count = count_all_video_files(str(self.temp_path), recursive=False)
        self.assertEqual(count, 3)  # mp4, avi, mkv only (not subdirectory files)
    
    def test_count_custom_extensions(self):
        """Test counting with custom extensions"""
        extensions = ['.mp4', '.avi']
        count = count_all_video_files(str(self.temp_path), recursive=True, extensions=extensions)
        self.assertEqual(count, 2)  # Only mp4 and avi
    
    def test_count_no_matching_files(self):
        """Test counting when no files match"""
        extensions = ['.xyz']
        count = count_all_video_files(str(self.temp_path), recursive=True, extensions=extensions)
        self.assertEqual(count, 0)
    
    def test_count_empty_directory(self):
        """Test counting in empty directory"""
        empty_dir = tempfile.mkdtemp()
        try:
            count = count_all_video_files(empty_dir, recursive=True)
            self.assertEqual(count, 0)
        finally:
            os.rmdir(empty_dir)
    
    def test_count_case_insensitive_extensions(self):
        """Test that extensions are case insensitive"""
        # Create files with uppercase extensions
        (self.temp_path / "video_upper.MP4").touch()
        (self.temp_path / "video_mixed.Avi").touch()
        
        count = count_all_video_files(str(self.temp_path), recursive=False)
        self.assertEqual(count, 5)  # 3 original + 2 new files
    
    def test_count_nonexistent_directory(self):
        """Test behavior with non-existent directory"""
        # The function returns 0 for non-existent directories (Path.glob handles this gracefully)
        count = count_all_video_files("/nonexistent/directory")
        self.assertEqual(count, 0)


class TestFormatFileSize(unittest.TestCase):
    """Test format_file_size function"""
    
    def test_format_bytes(self):
        """Test formatting bytes"""
        self.assertEqual(format_file_size(500), "500.0 B")
        self.assertEqual(format_file_size(0), "0.0 B")
        self.assertEqual(format_file_size(1), "1.0 B")
    
    def test_format_kilobytes(self):
        """Test formatting kilobytes"""
        self.assertEqual(format_file_size(1024), "1.0 KB")
        self.assertEqual(format_file_size(1536), "1.5 KB")
        self.assertEqual(format_file_size(2048), "2.0 KB")
    
    def test_format_megabytes(self):
        """Test formatting megabytes"""
        self.assertEqual(format_file_size(1024 * 1024), "1.0 MB")
        self.assertEqual(format_file_size(1024 * 1024 * 2.5), "2.5 MB")
        self.assertEqual(format_file_size(1024 * 1024 * 100), "100.0 MB")
    
    def test_format_gigabytes(self):
        """Test formatting gigabytes"""
        self.assertEqual(format_file_size(1024 * 1024 * 1024), "1.0 GB")
        self.assertEqual(format_file_size(1024 * 1024 * 1024 * 4.7), "4.7 GB")
    
    def test_format_terabytes(self):
        """Test formatting terabytes"""
        self.assertEqual(format_file_size(1024 * 1024 * 1024 * 1024), "1.0 TB")
        self.assertEqual(format_file_size(1024 * 1024 * 1024 * 1024 * 2.3), "2.3 TB")
    
    def test_format_negative_size(self):
        """Test formatting negative size (edge case)"""
        # The function doesn't explicitly handle negative numbers,
        # but let's test the behavior
        result = format_file_size(-1024)
        self.assertIn("-", result)


class TestGetVideoExtensions(unittest.TestCase):
    """Test get_video_extensions function"""
    
    def test_returns_list(self):
        """Test that function returns a list"""
        extensions = get_video_extensions()
        self.assertIsInstance(extensions, list)
    
    def test_contains_common_extensions(self):
        """Test that common video extensions are included"""
        extensions = get_video_extensions()
        expected_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        
        for ext in expected_extensions:
            self.assertIn(ext, extensions)
    
    def test_extensions_are_lowercase(self):
        """Test that all extensions are lowercase"""
        extensions = get_video_extensions()
        for ext in extensions:
            self.assertEqual(ext, ext.lower())
    
    def test_extensions_start_with_dot(self):
        """Test that all extensions start with a dot"""
        extensions = get_video_extensions()
        for ext in extensions:
            self.assertTrue(ext.startswith('.'))
    
    def test_no_duplicate_extensions(self):
        """Test that there are no duplicate extensions"""
        extensions = get_video_extensions()
        self.assertEqual(len(extensions), len(set(extensions)))
    
    def test_consistent_return(self):
        """Test that function returns consistent results"""
        extensions1 = get_video_extensions()
        extensions2 = get_video_extensions()
        self.assertEqual(extensions1, extensions2)


if __name__ == '__main__':
    unittest.main()