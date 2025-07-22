"""
Unit tests for cli_handler.py module
"""
import unittest
import tempfile
import os
import sys
import argparse
import logging
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, call
from unittest.mock import mock_open
from io import StringIO

# Add parent directory to path for importing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cli_handler
from cli_handler import (
    setup_logging, validate_directory, parse_cli_arguments, validate_arguments,
    list_video_files, check_system_requirements, main
)
from video_inspector import ScanMode


class TestSetupLogging(unittest.TestCase):
    """Test setup_logging function"""
    
    @patch('logging.basicConfig')
    def test_setup_logging_verbose(self, mock_basic_config):
        """Test setup_logging with verbose=True"""
        setup_logging(verbose=True)
        
        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        self.assertEqual(kwargs['level'], logging.DEBUG)
        self.assertIn('%(asctime)s', kwargs['format'])
        self.assertIn('%(levelname)s', kwargs['format'])
        self.assertIn('%(message)s', kwargs['format'])
    
    @patch('logging.basicConfig')
    def test_setup_logging_not_verbose(self, mock_basic_config):
        """Test setup_logging with verbose=False"""
        setup_logging(verbose=False)
        
        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        self.assertEqual(kwargs['level'], logging.INFO)


class TestValidateDirectory(unittest.TestCase):
    """Test validate_directory function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.temp_file, 'w') as f:
            f.write("test")
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_existing_directory(self):
        """Test validating existing directory"""
        result = validate_directory(self.temp_dir)
        self.assertIsInstance(result, Path)
        self.assertEqual(str(result), str(Path(self.temp_dir).resolve()))
    
    def test_validate_nonexistent_directory(self):
        """Test validating non-existent directory"""
        with self.assertRaises(FileNotFoundError):
            validate_directory("/nonexistent/directory")
    
    def test_validate_file_not_directory(self):
        """Test validating file instead of directory"""
        with self.assertRaises(NotADirectoryError):
            validate_directory(self.temp_file)


class TestParseCliArguments(unittest.TestCase):
    """Test parse_cli_arguments function"""
    
    def test_parse_minimal_arguments(self):
        """Test parsing minimal arguments"""
        with patch.object(sys, 'argv', ['cli_handler.py', '/test/path']):
            args = parse_cli_arguments()
            self.assertEqual(args.directory, '/test/path')
            self.assertEqual(args.mode, 'hybrid')
            self.assertFalse(args.verbose)
            self.assertFalse(args.no_resume)
            self.assertFalse(args.list_videos)
            self.assertFalse(args.json)
            self.assertEqual(args.max_workers, 4)
    
    def test_parse_all_arguments(self):
        """Test parsing all arguments"""
        test_args = [
            'cli_handler.py', '/test/path',
            '--mode', 'deep',
            '--verbose',
            '--no-resume',
            '--list-videos',
            '--json',
            '--output', '/output/file.json',
            '--extensions', 'mp4', 'avi', 'mkv',
            '--max-workers', '8',
            '--quiet'
        ]
        
        with patch.object(sys, 'argv', test_args):
            args = parse_cli_arguments()
            self.assertEqual(args.directory, '/test/path')
            self.assertEqual(args.mode, 'deep')
            self.assertTrue(args.verbose)
            self.assertTrue(args.no_resume)
            self.assertTrue(args.list_videos)
            self.assertTrue(args.json)
            self.assertEqual(args.output, '/output/file.json')
            self.assertEqual(args.extensions, ['mp4', 'avi', 'mkv'])
            self.assertEqual(args.max_workers, 8)
            self.assertTrue(args.quiet)
    
    def test_parse_no_directory(self):
        """Test parsing with no directory argument"""
        with patch.object(sys, 'argv', ['cli_handler.py']):
            args = parse_cli_arguments()
            self.assertIsNone(args.directory)


class TestValidateArguments(unittest.TestCase):
    """Test validate_arguments function"""
    
    def test_validate_normal_arguments(self):
        """Test validating normal arguments"""
        args = argparse.Namespace()
        args.verbose = False
        args.quiet = False
        args.max_workers = 4
        args.output = None
        args.json = False
        
        # Should not raise any exception
        validate_arguments(args)
    
    def test_validate_verbose_and_quiet(self):
        """Test validating conflicting verbose and quiet flags"""
        args = argparse.Namespace()
        args.verbose = True
        args.quiet = True
        args.max_workers = 4
        args.output = None
        args.json = False
        
        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        
        self.assertIn("Cannot use --verbose and --quiet together", str(context.exception))
    
    def test_validate_zero_workers(self):
        """Test validating zero max workers"""
        args = argparse.Namespace()
        args.verbose = False
        args.quiet = False
        args.max_workers = 0
        args.output = None
        args.json = False
        
        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        
        self.assertIn("positive integer", str(context.exception))
    
    def test_validate_output_without_json(self):
        """Test validating output argument without json flag"""
        args = argparse.Namespace()
        args.verbose = False
        args.quiet = False
        args.max_workers = 4
        args.output = "/test/output.json"
        args.json = False
        
        # Should enable JSON output automatically
        validate_arguments(args)
        self.assertTrue(args.json)


class TestListVideoFiles(unittest.TestCase):
    """Test list_video_files function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test files
        (self.temp_path / "video1.mp4").touch()
        (self.temp_path / "video2.avi").touch()
        (self.temp_path / "document.txt").touch()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('cli_handler.get_all_video_object_files')
    @patch('builtins.print')
    def test_list_video_files_found(self, mock_print, mock_get_files):
        """Test listing video files when files are found"""
        from video_inspector import VideoFile
        
        # Mock video files
        video_files = [
            VideoFile(str(self.temp_path / "video1.mp4")),
            VideoFile(str(self.temp_path / "video2.avi"))
        ]
        mock_get_files.return_value = video_files
        
        list_video_files(self.temp_path, recursive=True, extensions=None)
        
        # Verify function was called
        mock_get_files.assert_called_once()
        mock_print.assert_called()
    
    @patch('cli_handler.get_all_video_object_files')
    @patch('builtins.print')
    def test_list_video_files_none_found(self, mock_print, mock_get_files):
        """Test listing video files when no files are found"""
        mock_get_files.return_value = []
        
        list_video_files(self.temp_path, recursive=True, extensions=None)
        
        # Verify appropriate message is printed
        mock_get_files.assert_called_once()
        mock_print.assert_called()
    
    @patch('cli_handler.get_all_video_object_files')
    @patch('logging.error')
    def test_list_video_files_exception(self, mock_log_error, mock_get_files):
        """Test listing video files when exception occurs"""
        mock_get_files.side_effect = Exception("Test exception")
        
        with self.assertRaises(SystemExit):
            list_video_files(self.temp_path)
        
        mock_log_error.assert_called()


class TestCheckSystemRequirements(unittest.TestCase):
    """Test check_system_requirements function"""
    
    @patch('cli_handler.get_ffmpeg_command')
    def test_ffmpeg_found(self, mock_get_ffmpeg):
        """Test when ffmpeg is found"""
        mock_get_ffmpeg.return_value = "/usr/bin/ffmpeg"
        
        result = check_system_requirements()
        
        self.assertEqual(result, "/usr/bin/ffmpeg")
    
    @patch('cli_handler.get_ffmpeg_command')
    @patch('builtins.print')
    def test_ffmpeg_not_found(self, mock_print, mock_get_ffmpeg):
        """Test when ffmpeg is not found"""
        mock_get_ffmpeg.return_value = None
        
        with self.assertRaises(SystemExit):
            check_system_requirements()
        
        mock_print.assert_called()


class TestMain(unittest.TestCase):
    """Test main function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        # Create a test video file
        test_video = os.path.join(self.temp_dir, "test.mp4")
        with open(test_video, 'wb') as f:
            f.write(b'0' * 1024)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('cli_handler.parse_cli_arguments')
    @patch('builtins.print')
    def test_main_no_directory(self, mock_print, mock_parse):
        """Test main with no directory argument"""
        args = argparse.Namespace()
        args.directory = None
        args.verbose = False
        args.quiet = False
        args.max_workers = 4
        args.output = None
        args.json = False
        mock_parse.return_value = args
        
        with self.assertRaises(SystemExit):
            main()
    
    @patch('cli_handler.parse_cli_arguments')
    @patch('cli_handler.validate_directory')
    @patch('builtins.print')
    def test_main_invalid_directory(self, mock_print, mock_validate_dir, mock_parse):
        """Test main with invalid directory"""
        args = argparse.Namespace()
        args.directory = "/nonexistent"
        args.verbose = False
        args.quiet = False
        args.max_workers = 4
        args.output = None
        args.json = False
        mock_parse.return_value = args
        mock_validate_dir.side_effect = FileNotFoundError("Directory not found")
        
        with self.assertRaises(SystemExit):
            main()
    
    @patch('cli_handler.parse_cli_arguments')
    @patch('cli_handler.validate_directory')
    @patch('cli_handler.count_all_video_files')
    @patch('cli_handler.list_video_files')
    def test_main_list_videos(self, mock_list, mock_count, mock_validate_dir, mock_parse):
        """Test main with list-videos option"""
        args = argparse.Namespace()
        args.directory = self.temp_dir
        args.verbose = False
        args.quiet = False
        args.list_videos = True
        args.recursive = True
        args.extensions = None
        args.max_workers = 4
        args.output = None
        args.json = False
        mock_parse.return_value = args
        mock_validate_dir.return_value = Path(self.temp_dir)
        
        main()
        
        mock_list.assert_called_once()
    
    @patch('cli_handler.parse_cli_arguments')
    @patch('cli_handler.validate_directory')
    @patch('cli_handler.count_all_video_files')
    @patch('builtins.print')
    def test_main_no_video_files(self, mock_print, mock_count, mock_validate_dir, mock_parse):
        """Test main when no video files found"""
        args = argparse.Namespace()
        args.directory = self.temp_dir
        args.verbose = False
        args.quiet = False
        args.list_videos = False
        args.extensions = None
        args.max_workers = 4
        args.output = None
        args.json = False
        mock_parse.return_value = args
        mock_validate_dir.return_value = Path(self.temp_dir)
        mock_count.return_value = 0
        
        with self.assertRaises(SystemExit):
            main()
    
    @patch('cli_handler.parse_cli_arguments')
    @patch('cli_handler.validate_directory')
    @patch('cli_handler.count_all_video_files')
    @patch('cli_handler.check_system_requirements')
    @patch('cli_handler.inspect_video_files_cli')
    @patch('builtins.print')
    def test_main_successful_scan(self, mock_print, mock_inspect, mock_check_sys, 
                                  mock_count, mock_validate_dir, mock_parse):
        """Test main with successful scan"""
        args = argparse.Namespace()
        args.directory = self.temp_dir
        args.verbose = False
        args.quiet = False
        args.list_videos = False
        args.mode = 'hybrid'
        args.no_resume = False
        args.json = False
        args.output = None
        args.recursive = True
        args.extensions = None
        args.max_workers = 4
        mock_parse.return_value = args
        mock_validate_dir.return_value = Path(self.temp_dir)
        mock_count.return_value = 1
        mock_check_sys.return_value = "/usr/bin/ffmpeg"
        
        main()
        
        mock_inspect.assert_called_once()
        
        # Verify the arguments passed to inspect_video_files_cli
        call_args = mock_inspect.call_args
        kwargs = call_args[1]
        self.assertEqual(kwargs['directory'], str(Path(self.temp_dir)))
        self.assertEqual(kwargs['resume'], True)  # not args.no_resume
        self.assertEqual(kwargs['verbose'], False)
        self.assertEqual(kwargs['json_output'], False)
        self.assertEqual(kwargs['output_file'], None)
        self.assertEqual(kwargs['recursive'], True)
        self.assertEqual(kwargs['extensions'], None)
        self.assertEqual(kwargs['max_workers'], 4)
        self.assertEqual(kwargs['scan_mode'], ScanMode.HYBRID)
    
    @patch('cli_handler.parse_cli_arguments')
    def test_main_keyboard_interrupt(self, mock_parse):
        """Test main with keyboard interrupt"""
        mock_parse.side_effect = KeyboardInterrupt()
        
        with self.assertRaises(SystemExit) as context:
            main()
        
        self.assertEqual(context.exception.code, 130)  # Standard Ctrl+C exit code
    
    @patch('cli_handler.parse_cli_arguments')
    @patch('logging.error')
    def test_main_unexpected_exception(self, mock_log_error, mock_parse):
        """Test main with unexpected exception"""
        mock_parse.side_effect = Exception("Unexpected error")
        
        with self.assertRaises(SystemExit):
            main()
        
        mock_log_error.assert_called()


if __name__ == '__main__':
    unittest.main()