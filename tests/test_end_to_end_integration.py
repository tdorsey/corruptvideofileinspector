"""
End-to-end integration tests for the entire application
"""
import unittest
import tempfile
import os
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import count_all_video_files, format_file_size, get_video_extensions
from video_inspector import (
    VideoFile, VideoInspectionResult, ScanMode, 
    get_ffmpeg_command, get_all_video_object_files
)


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests for the complete application workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_files = []
        
        # Create a more complex directory structure
        self.create_test_video_files()
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up test files
        for file_path in self.test_files:
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass
        
        # Remove test directories
        try:
            import shutil
            shutil.rmtree(self.test_dir)
        except OSError:
            pass
    
    def create_test_video_files(self):
        """Create a realistic test directory structure with video files"""
        # Root level video files
        self.create_test_file("movie1.mp4", "fake mp4 content")
        self.create_test_file("documentary.avi", "fake avi content")
        self.create_test_file("series_episode.mkv", "fake mkv content")
        
        # Mixed file types
        self.create_test_file("readme.txt", "not a video file")
        self.create_test_file("image.jpg", "fake image")
        
        # Subdirectory with videos
        subdir1 = os.path.join(self.test_dir, "movies")
        os.makedirs(subdir1)
        
        subfile1 = os.path.join(subdir1, "action_movie.mp4")
        with open(subfile1, 'w') as f:
            f.write("fake action movie content")
        self.test_files.append(subfile1)
        
        subfile2 = os.path.join(subdir1, "comedy.avi")
        with open(subfile2, 'w') as f:
            f.write("fake comedy content")
        self.test_files.append(subfile2)
        
        # Nested subdirectory
        subdir2 = os.path.join(subdir1, "classics")
        os.makedirs(subdir2)
        
        subfile3 = os.path.join(subdir2, "old_movie.mov")
        with open(subfile3, 'w') as f:
            f.write("fake old movie content")
        self.test_files.append(subfile3)
        
        # Empty subdirectory
        empty_dir = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_dir)
    
    def create_test_file(self, filename: str, content: str = "test content") -> str:
        """Create a test file and return its path"""
        file_path = os.path.join(self.test_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        self.test_files.append(file_path)
        return file_path
    
    def test_complete_video_discovery_workflow(self):
        """Test complete video file discovery workflow"""
        # Step 1: Count video files using utils
        total_count = count_all_video_files(self.test_dir, recursive=True)
        self.assertEqual(total_count, 6)  # All video files including subdirs
        
        non_recursive_count = count_all_video_files(self.test_dir, recursive=False)
        self.assertEqual(non_recursive_count, 3)  # Only root level videos
        
        # Step 2: Get video file objects using video_inspector
        video_files = get_all_video_object_files(self.test_dir, recursive=True)
        self.assertEqual(len(video_files), 6)
        
        # Verify all are VideoFile objects
        for vf in video_files:
            self.assertIsInstance(vf, VideoFile)
            self.assertGreater(vf.size, 0)  # Should have content
        
        # Step 3: Verify file extensions are handled correctly
        extensions = get_video_extensions()
        found_extensions = set()
        for vf in video_files:
            ext = Path(vf.filename).suffix.lower()
            found_extensions.add(ext)
            self.assertIn(ext, extensions)
        
        # Should find multiple different extensions
        self.assertGreaterEqual(len(found_extensions), 3)
    
    def test_video_inspection_result_workflow(self):
        """Test video inspection result creation and processing"""
        video_files = get_all_video_object_files(self.test_dir, recursive=False)  # Only root level
        
        results = []
        for vf in video_files:
            result = VideoInspectionResult(vf.filename)
            result.file_size = vf.size
            result.scan_mode = ScanMode.QUICK
            
            # Simulate some results
            if "movie1" in vf.filename:
                result.is_corrupt = True
                result.error_message = "Simulated corruption"
            
            results.append(result)
        
        # Verify results
        self.assertEqual(len(results), 3)  # Root level files only
        
        # Check for the corrupt file we simulated
        corrupt_files = [r for r in results if r.is_corrupt]
        self.assertEqual(len(corrupt_files), 1)
        self.assertIn("movie1", corrupt_files[0].filename)
        
        # Test JSON conversion
        for result in results:
            result_dict = result.to_dict()
            self.assertIsInstance(result_dict, dict)
            self.assertIn('filename', result_dict)
            self.assertIn('is_corrupt', result_dict)
            self.assertIn('scan_mode', result_dict)
    
    def test_file_size_formatting_workflow(self):
        """Test file size formatting across different file sizes"""
        video_files = get_all_video_object_files(self.test_dir)
        
        for vf in video_files:
            formatted_size = format_file_size(vf.size)
            
            # Should be a valid format
            self.assertIsInstance(formatted_size, str)
            self.assertTrue(any(unit in formatted_size for unit in ['B', 'KB', 'MB', 'GB']))
            
            # Should be parseable (contains a number)
            self.assertTrue(any(char.isdigit() for char in formatted_size))
    
    def test_recursive_vs_non_recursive_consistency(self):
        """Test consistency between recursive and non-recursive scanning"""
        # Get all files recursively
        all_recursive_count = count_all_video_files(self.test_dir, recursive=True)
        all_recursive_objects = get_all_video_object_files(self.test_dir, recursive=True)
        
        # Get root files only
        root_count = count_all_video_files(self.test_dir, recursive=False)
        root_objects = get_all_video_object_files(self.test_dir, recursive=False)
        
        # Consistency checks
        self.assertEqual(all_recursive_count, len(all_recursive_objects))
        self.assertEqual(root_count, len(root_objects))
        
        # Recursive should find more files than non-recursive
        self.assertGreater(all_recursive_count, root_count)
        self.assertGreater(len(all_recursive_objects), len(root_objects))
        
        # All root files should be included in recursive results
        root_filenames = {vf.filename for vf in root_objects}
        all_filenames = {vf.filename for vf in all_recursive_objects}
        
        self.assertTrue(root_filenames.issubset(all_filenames))
    
    def test_extension_filtering_workflow(self):
        """Test custom extension filtering across the workflow"""
        # Test with only MP4 files
        mp4_count = count_all_video_files(self.test_dir, extensions=['.mp4'])
        mp4_objects = get_all_video_object_files(self.test_dir, extensions=['.mp4'])
        
        self.assertEqual(mp4_count, len(mp4_objects))
        
        # Verify all found files are MP4
        for vf in mp4_objects:
            self.assertTrue(vf.filename.lower().endswith('.mp4'))
        
        # Test with multiple extensions
        multi_count = count_all_video_files(self.test_dir, extensions=['.mp4', '.avi'])
        multi_objects = get_all_video_object_files(self.test_dir, extensions=['.mp4', '.avi'])
        
        self.assertEqual(multi_count, len(multi_objects))
        self.assertGreater(multi_count, mp4_count)  # Should find more files
    
    def test_empty_directory_handling(self):
        """Test handling of empty directories"""
        empty_dir = os.path.join(self.test_dir, "empty")
        
        # Should handle empty directory gracefully
        count = count_all_video_files(empty_dir)
        self.assertEqual(count, 0)
        
        objects = get_all_video_object_files(empty_dir)
        self.assertEqual(len(objects), 0)
        self.assertIsInstance(objects, list)
    
    def test_large_directory_structure_simulation(self):
        """Test performance with a simulated large directory structure"""
        # Create many subdirectories and files
        large_test_dir = os.path.join(self.test_dir, "large_test")
        os.makedirs(large_test_dir)
        
        created_files = []
        expected_video_count = 0
        
        # Create nested structure
        for i in range(5):  # 5 subdirectories
            subdir = os.path.join(large_test_dir, f"subdir_{i}")
            os.makedirs(subdir)
            
            for j in range(3):  # 3 files per directory
                video_file = os.path.join(subdir, f"video_{i}_{j}.mp4")
                with open(video_file, 'w') as f:
                    f.write(f"fake video content {i}_{j}")
                created_files.append(video_file)
                expected_video_count += 1
                
                # Add some non-video files
                text_file = os.path.join(subdir, f"readme_{i}_{j}.txt")
                with open(text_file, 'w') as f:
                    f.write("not a video")
                created_files.append(text_file)
        
        try:
            # Test counting
            count = count_all_video_files(large_test_dir, recursive=True)
            self.assertEqual(count, expected_video_count)
            
            # Test object creation
            objects = get_all_video_object_files(large_test_dir, recursive=True)
            self.assertEqual(len(objects), expected_video_count)
            
            # Verify all objects are valid
            for obj in objects:
                self.assertIsInstance(obj, VideoFile)
                self.assertGreater(obj.size, 0)
                self.assertTrue(obj.filename.endswith('.mp4'))
            
        finally:
            # Clean up created files
            for file_path in created_files:
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass
    
    def test_integration_with_actual_test_videos(self):
        """Test integration with the actual test-videos directory"""
        test_videos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test-videos")
        
        if os.path.exists(test_videos_dir):
            # Test that all functions work with the real test directory
            count = count_all_video_files(test_videos_dir)
            objects = get_all_video_object_files(test_videos_dir)
            
            # Basic consistency checks
            self.assertEqual(count, len(objects))
            self.assertIsInstance(count, int)
            self.assertIsInstance(objects, list)
            
            # If there are files, they should be valid VideoFile objects
            for obj in objects:
                self.assertIsInstance(obj, VideoFile)
                # Note: test video files might be empty (0 bytes)
                self.assertGreaterEqual(obj.size, 0)
        else:
            # If test-videos directory doesn't exist, that's ok for this test
            self.skipTest("test-videos directory not found")


if __name__ == '__main__':
    unittest.main()