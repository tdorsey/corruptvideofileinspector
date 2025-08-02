import logging
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
import typer


from cli_handler import (
    check_system_requirements,
    list_video_files,
    main,
    setup_logging,
    validate_arguments,
)

from src.utils import count_all_video_files, format_file_size, get_video_extensions

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestSetupLogging(unittest.TestCase):
    """Test setup_logging function"""

    @patch("logging.basicConfig")
    def test_setup_logging_not_verbose(self, mock_basic_config):
        """Test setup_logging with verbose=False"""
        setup_logging(verbose=False)

        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.INFO


class TestValidateDirectory(unittest.TestCase):
    """Test validate_directory function"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = str(Path(self.temp_dir) / "test.txt")
        Path(self.temp_file).write_text("test")

    def tearDown(self):
        """Clean up test fixtures"""


class TestValidateArguments(unittest.TestCase):
    """Test validate_arguments function"""

    def test_validate_normal_arguments(self):
        """Test validating normal arguments"""
        # Should not raise any exception
        validate_arguments(
            verbose=False,
            quiet=False,
            max_workers=4,
            json_output=False,
            output=None,
        )

    def test_validate_verbose_and_quiet(self):
        """Test validating conflicting verbose and quiet flags"""
        with pytest.raises(typer.Exit) as context:
            validate_arguments(
                verbose=True,
                quiet=True,
                max_workers=4,
                json_output=False,
                output=None,
            )

        assert context.value.exit_code == 1

    def test_validate_zero_workers(self):
        """Test validating zero max workers"""
        with pytest.raises(typer.Exit) as context:
            validate_arguments(
                verbose=False,
                quiet=False,
                max_workers=0,
                json_output=False,
                output=None,
            )

        assert context.value.exit_code == 1

    def test_validate_output_without_json(self):
        """Test validating output argument without json flag"""
        # This should not raise an exception, just log a warning
        validate_arguments(
            verbose=False,
            quiet=False,
            max_workers=4,
            json_output=False,
            output="/test/output.json",
        )


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

    @patch("cli_handler.get_all_video_object_files")
    @patch("typer.echo")
    def test_list_video_files_found(self, mock_echo, mock_get_files):
        """Test listing video files when files are found"""
        from video_inspector import VideoFile
        from pathlib import Path

        # Mock video files
        video_files = [
            VideoFile(Path(self.temp_path) / "video1.mp4"),
            VideoFile(Path(self.temp_path) / "video2.avi"),
        ]
        mock_get_files.return_value = video_files

        list_video_files(self.temp_path, recursive=True, extensions=None)

        # Verify function was called
        mock_get_files.assert_called_once()
        mock_echo.assert_called()

    @patch("cli_handler.get_all_video_object_files")
    @patch("typer.echo")
    def test_list_video_files_none_found(self, mock_echo, mock_get_files):
        """Test listing video files when no files are found"""
        mock_get_files.return_value = []

        list_video_files(self.temp_path, recursive=True, extensions=None)

        # Verify appropriate message is printed
        mock_get_files.assert_called_once()
        mock_echo.assert_called()

    @patch("cli_handler.get_all_video_object_files")
    @patch("logging.error")
    def test_list_video_files_exception(self, mock_log_error, mock_get_files):
        """Test listing video files when exception occurs"""
        mock_get_files.side_effect = Exception("Test exception")

        with pytest.raises(SystemExit):
            list_video_files(self.temp_path)

        mock_log_error.assert_called()


class TestCheckSystemRequirements(unittest.TestCase):
    """Test check_system_requirements function"""

    @patch("cli_handler.get_ffmpeg_command")
    def test_ffmpeg_found(self, mock_get_ffmpeg):
        """Test when ffmpeg is found"""
        mock_get_ffmpeg.return_value = "/usr/bin/ffmpeg"

        result = check_system_requirements()

        assert result == "/usr/bin/ffmpeg"

    @patch("cli_handler.get_ffmpeg_command")
    @patch("typer.echo")
    def test_ffmpeg_not_found(self, mock_echo, mock_get_ffmpeg):
        """Test when ffmpeg is not found"""
        mock_get_ffmpeg.return_value = None

        with pytest.raises(typer.Exit) as context:
            check_system_requirements()

        assert context.value.exit_code == 1
        mock_echo.assert_called()


class TestMain(unittest.TestCase):
    """Test main function"""

    def test_main_function_exists(self):
        """Test that main function exists and is callable"""
        assert callable(main)

    @patch("cli_handler.app")
    def test_main_calls_app(self, mock_app):
        """Test that main function calls the typer app"""
