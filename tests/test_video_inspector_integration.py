"""
Integration tests for video_inspector module
"""
import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_inspector import (
    VideoFile, VideoInspectionResult, ScanMode, 
    get_ffmpeg_command, get_all_video_object_files
)


class TestVideoInspectorIntegration(unittest.TestCase):
    """Integration tests for video inspector functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_files = []
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up test files
        for file_path in self.test_files:
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass
        
        # Remove test directory
        try:
            os.rmdir(self.test_dir)
        except OSError:
            pass
    
    def create_test_file(self, filename: str, content: str = "test content") -> str:
        """Create a test file and return its path"""
        file_path = os.path.join(self.test_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        self.test_files.append(file_path)
        return file_path
    
    def test_video_file_creation(self):
        """Test VideoFile object creation"""
        # Create a test file
        test_file = self.create_test_file("test.mp4", "fake video content")
        
        # Create VideoFile object
        video_file = VideoFile(test_file)
        
        # Verify properties
        self.assertEqual(video_file.filename, test_file)
        self.assertGreater(video_file.size, 0)  # Should have file size
        self.assertEqual(video_file.duration, 0.0)  # Default duration
    
    def test_video_file_nonexistent(self):
        """Test VideoFile with non-existent file"""
        nonexistent_path = "/nonexistent/file.mp4"
        video_file = VideoFile(nonexistent_path)
        
        self.assertEqual(video_file.filename, nonexistent_path)
        self.assertEqual(video_file.size, 0)  # No size for non-existent file
        self.assertEqual(video_file.duration, 0.0)
    
    def test_video_inspection_result_creation(self):
        """Test VideoInspectionResult object creation"""
        filename = "test.mp4"
        result = VideoInspectionResult(filename)
        
        # Check default values
        self.assertEqual(result.filename, filename)
        self.assertFalse(result.is_corrupt)
        self.assertEqual(result.file_size, 0)
        self.assertEqual(result.inspection_time, 0.0)
        self.assertEqual(result.error_message, "")
        self.assertEqual(result.ffmpeg_output, "")
        self.assertEqual(result.scan_mode, ScanMode.QUICK)
        self.assertFalse(result.needs_deep_scan)
        self.assertFalse(result.deep_scan_completed)
    
    def test_video_inspection_result_to_dict(self):
        """Test VideoInspectionResult to_dict method"""
        result = VideoInspectionResult("test.mp4")
        result.is_corrupt = True
        result.file_size = 1024
        result.error_message = "Test error"
        result.scan_mode = ScanMode.QUICK
        
        result_dict = result.to_dict()
        
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['filename'], "test.mp4")
        self.assertTrue(result_dict['is_corrupt'])
        self.assertEqual(result_dict['file_size'], 1024)
        self.assertEqual(result_dict['error_message'], "Test error")
        self.assertEqual(result_dict['scan_mode'], "quick")
    
    def test_scan_mode_enum(self):
        """Test ScanMode enum values"""
        self.assertEqual(ScanMode.QUICK.value, "quick")
        self.assertEqual(ScanMode.DEEP.value, "deep")
        self.assertEqual(ScanMode.HYBRID.value, "hybrid")
    
    def test_get_ffmpeg_command(self):
        """Test ffmpeg command detection"""
        # This test may fail in environments without ffmpeg
        # but it should not raise an exception
        ffmpeg_cmd = get_ffmpeg_command()
        
        # Should return either a string (if ffmpeg found) or None
        self.assertTrue(ffmpeg_cmd is None or isinstance(ffmpeg_cmd, str))
        
        if ffmpeg_cmd:
            # If found, should be a valid path
            self.assertTrue(len(ffmpeg_cmd) > 0)
    
    def test_get_all_video_object_files_empty_directory(self):
        """Test getting video files from empty directory"""
        video_files = get_all_video_object_files(self.test_dir)
        self.assertEqual(len(video_files), 0)
        self.assertIsInstance(video_files, list)
    
    def test_get_all_video_object_files_with_videos(self):
        """Test getting video files from directory with video files"""
        # Create test video files
        self.create_test_file("video1.mp4")
        self.create_test_file("video2.avi")
        self.create_test_file("video3.mkv")
        self.create_test_file("not_video.txt")
        
        video_files = get_all_video_object_files(self.test_dir)
        
        # Should find 3 video files
        self.assertEqual(len(video_files), 3)
        
        # All should be VideoFile objects
        for vf in video_files:
            self.assertIsInstance(vf, VideoFile)
        
        # Should be sorted by filename
        filenames = [vf.filename for vf in video_files]
        self.assertEqual(filenames, sorted(filenames))
    
    def test_get_all_video_object_files_recursive(self):
        """Test recursive scanning for video files"""
        # Create files in root
        self.create_test_file("root.mp4")
        
        # Create subdirectory and files
        subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(subdir)
        
        subfile = os.path.join(subdir, "sub.avi")
        with open(subfile, 'w') as f:
            f.write("test")
        self.test_files.append(subfile)
        
        # Test recursive (default)
        video_files = get_all_video_object_files(self.test_dir, recursive=True)
        self.assertEqual(len(video_files), 2)
        
        # Test non-recursive
        video_files = get_all_video_object_files(self.test_dir, recursive=False)
        self.assertEqual(len(video_files), 1)
    
    def test_get_all_video_object_files_custom_extensions(self):
        """Test getting video files with custom extensions"""
        self.create_test_file("test.mp4")
        self.create_test_file("test.avi")
        self.create_test_file("test.custom")
        
        # Default extensions (should find mp4 and avi)
        video_files = get_all_video_object_files(self.test_dir)
        self.assertEqual(len(video_files), 2)
        
        # Custom extensions (should find only mp4)
        video_files = get_all_video_object_files(self.test_dir, extensions=['.mp4'])
        self.assertEqual(len(video_files), 1)
        self.assertTrue(video_files[0].filename.endswith('.mp4'))
        
        # Include custom extension
        video_files = get_all_video_object_files(self.test_dir, extensions=['.mp4', '.custom'])
        self.assertEqual(len(video_files), 2)
    
    def test_get_all_video_object_files_case_insensitive(self):
        """Test case insensitive file extension matching"""
        self.create_test_file("VIDEO.MP4")
        self.create_test_file("movie.AVI")
        self.create_test_file("film.MkV")
        
        video_files = get_all_video_object_files(self.test_dir)
        self.assertEqual(len(video_files), 3)
    
    def test_integration_with_test_videos_directory(self):
        """Test integration with actual test-videos directory"""
        test_videos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test-videos")
        
        if os.path.exists(test_videos_dir):
            # This should not raise an exception
            video_files = get_all_video_object_files(test_videos_dir)
            
            # Should return a list
            self.assertIsInstance(video_files, list)
            
            # All items should be VideoFile objects
            for vf in video_files:
                self.assertIsInstance(vf, VideoFile)
                self.assertTrue(os.path.exists(vf.filename) or vf.size == 0)


if __name__ == '__main__':
    unittest.main()