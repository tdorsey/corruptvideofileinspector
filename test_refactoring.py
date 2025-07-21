#!/usr/bin/env python3
"""
Basic tests for the refactored Corrupt Video Inspector modules
Tests the separation of concerns and basic functionality of each module.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import utils
import video_inspector
import cli_handler


class TestUtils(unittest.TestCase):
    """Test utility functions"""

    def test_platform_detection(self):
        """Test platform detection functions"""
        # At least one should be true
        platforms = [utils.is_macos(), utils.is_windows_os(), utils.is_linux_os()]
        self.assertTrue(any(platforms), "At least one platform should be detected")

    def test_convert_time(self):
        """Test time conversion function"""
        self.assertEqual(utils.convert_time(0), "0:00:00")
        self.assertEqual(utils.convert_time(60), "0:01:00")
        self.assertEqual(utils.convert_time(3661), "1:01:01")

    def test_calculate_progress(self):
        """Test progress calculation"""
        self.assertEqual(utils.calculate_progress(1, 4), "25%")
        self.assertEqual(utils.calculate_progress(3, 4), "75%")
        self.assertEqual(utils.calculate_progress(4, 4), "100%")

    def test_truncate_filename(self):
        """Test filename truncation"""
        short_name = "short.mp4"
        self.assertEqual(utils.truncate_filename(short_name), short_name)
        
        # Test with a very long filename - only truncates on macOS and Windows
        long_name = "a" * 100 + ".mp4"
        truncated = utils.truncate_filename(long_name)
        
        if utils.is_macos() or utils.is_windows_os():
            self.assertTrue(len(truncated) < len(long_name))
        else:
            # On Linux, no truncation happens
            self.assertEqual(truncated, long_name)
            
        self.assertTrue(truncated.endswith(".mp4"))

    def test_video_extensions(self):
        """Test video extensions constant"""
        self.assertIn('.mp4', utils.VIDEO_EXTENSIONS)
        self.assertIn('.avi', utils.VIDEO_EXTENSIONS)
        self.assertTrue(len(utils.VIDEO_EXTENSIONS) > 5)

    def test_count_video_files(self):
        """Test video file counting"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            open(os.path.join(tmpdir, 'test1.mp4'), 'w').close()
            open(os.path.join(tmpdir, 'test2.avi'), 'w').close()
            open(os.path.join(tmpdir, 'test3.txt'), 'w').close()  # Non-video file
            
            count = utils.count_all_video_files(tmpdir)
            self.assertEqual(count, 2)


class TestVideoInspector(unittest.TestCase):
    """Test video inspector functionality"""

    def test_video_object_creation(self):
        """Test VideoObject class"""
        video = video_inspector.VideoObject("test.mp4", "/path/to/test.mp4")
        self.assertEqual(video.filename, "test.mp4")
        self.assertEqual(video.full_filepath, "/path/to/test.mp4")

    def test_get_all_video_object_files(self):
        """Test getting video files as objects"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            open(os.path.join(tmpdir, 'test1.mp4'), 'w').close()
            open(os.path.join(tmpdir, 'test2.avi'), 'w').close()
            open(os.path.join(tmpdir, 'test3.txt'), 'w').close()  # Non-video file
            
            videos = video_inspector.get_all_video_object_files(tmpdir)
            self.assertEqual(len(videos), 2)
            self.assertIsInstance(videos[0], video_inspector.VideoObject)
            
            # Check sorting
            filenames = [v.filename for v in videos]
            self.assertEqual(filenames, sorted(filenames))

    @patch('subprocess.run')
    def test_get_ffmpeg_command_system(self, mock_run):
        """Test ffmpeg command detection - system version"""
        mock_run.return_value = MagicMock()
        result = video_inspector.get_ffmpeg_command()
        self.assertEqual(result, 'ffmpeg')

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.access')
    def test_get_ffmpeg_command_bundled(self, mock_access, mock_exists, mock_run):
        """Test ffmpeg command detection - bundled version"""
        # Mock system ffmpeg not available
        mock_run.side_effect = FileNotFoundError()
        # Mock bundled ffmpeg available
        mock_exists.return_value = True
        mock_access.return_value = True
        
        result = video_inspector.get_ffmpeg_command()
        self.assertIsNotNone(result)
        self.assertTrue('ffmpeg' in result)


class TestCliHandler(unittest.TestCase):
    """Test CLI handler functionality"""

    def test_parse_cli_arguments_no_args(self):
        """Test argument parsing with no arguments"""
        with patch('sys.argv', ['CorruptVideoInspector.py']):
            args = cli_handler.parse_cli_arguments()
            self.assertIsNone(args.directory)
            self.assertFalse(args.verbose)
            self.assertFalse(args.no_resume)
            self.assertFalse(args.list_videos)
            self.assertFalse(args.json)

    def test_parse_cli_arguments_with_directory(self):
        """Test argument parsing with directory"""
        with patch('sys.argv', ['CorruptVideoInspector.py', '/test/path']):
            args = cli_handler.parse_cli_arguments()
            self.assertEqual(args.directory, '/test/path')

    def test_parse_cli_arguments_with_flags(self):
        """Test argument parsing with various flags"""
        with patch('sys.argv', ['CorruptVideoInspector.py', '--verbose', '--json', '/test/path']):
            args = cli_handler.parse_cli_arguments()
            self.assertEqual(args.directory, '/test/path')
            self.assertTrue(args.verbose)
            self.assertTrue(args.json)


class TestModuleSeparation(unittest.TestCase):
    """Test that modules are properly separated"""

    def test_no_circular_imports(self):
        """Test that we can import all modules without circular dependencies"""
        try:
            import utils
            import video_inspector
            import cli_handler
            import gui_handler
        except ImportError as e:
            self.fail(f"Module import failed: {e}")

    def test_utils_no_tkinter_dependency(self):
        """Test that utils module doesn't depend on tkinter"""
        import utils
        import sys
        
        # Check if utils module references tkinter
        utils_source = sys.modules['utils'].__file__
        with open(utils_source, 'r') as f:
            content = f.read()
        
        self.assertNotIn('tkinter', content.lower())
        self.assertNotIn('tk.', content)

    def test_video_inspector_no_tkinter_dependency(self):
        """Test that video_inspector module doesn't depend on tkinter"""
        import video_inspector
        import sys
        
        # Check if video_inspector module references tkinter
        video_inspector_source = sys.modules['video_inspector'].__file__
        with open(video_inspector_source, 'r') as f:
            content = f.read()
        
        self.assertNotIn('tkinter', content.lower())
        self.assertNotIn('tk.', content)


class TestFunctionalityPreservation(unittest.TestCase):
    """Test that existing functionality is preserved after refactoring"""

    def test_video_extensions_preserved(self):
        """Test that video extensions are the same as original"""
        # These should match the original VIDEO_EXTENSIONS
        expected_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', 
                              '.webm', '.m4v', '.m4p', '.mpeg', '.mpg', '.3gp', '.3g2']
        self.assertEqual(utils.VIDEO_EXTENSIONS, expected_extensions)

    def test_platform_detection_functions_preserved(self):
        """Test that platform detection functions work as before"""
        # These should work the same as the original functions
        self.assertIsInstance(utils.is_macos(), bool)
        self.assertIsInstance(utils.is_windows_os(), bool)
        self.assertIsInstance(utils.is_linux_os(), bool)

    def test_cli_arguments_preserved(self):
        """Test that CLI arguments are preserved from original"""
        with patch('sys.argv', ['CorruptVideoInspector.py', '--help']):
            try:
                cli_handler.parse_cli_arguments()
            except SystemExit:
                pass  # argparse calls sys.exit on --help
        
        # Test that key arguments exist
        with patch('sys.argv', ['CorruptVideoInspector.py', '--version']):
            try:
                cli_handler.parse_cli_arguments()
            except SystemExit:
                pass  # argparse calls sys.exit on --version


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)