"""
Integration tests for the refactored handlers module.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from src.cli.handlers import (
    UtilityHandler,
    get_ffmpeg_command,
    list_video_files,
    setup_logging,
)
from src.config import load_config

pytestmark = pytest.mark.integration


class TestHandlersIntegration(unittest.TestCase):
    """Test the integration of refactored handler functionality."""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

        # Create some test files
        (self.test_path / "video1.mp4").touch()
        (self.test_path / "video2.avi").touch()
        (self.test_path / "document.txt").touch()

    def tearDown(self):
        """Clean up test environment"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_utility_handler_class_works(self):
        """Test that the new UtilityHandler class works correctly."""
        config = load_config()
        handler = UtilityHandler(config)

        # Test that the handler can be instantiated and has the expected methods
        assert hasattr(handler, "get_ffmpeg_command")
        assert hasattr(handler, "check_system_requirements")
        assert hasattr(handler, "get_all_video_object_files")
        assert hasattr(handler, "list_video_files_simple")

    @patch("src.cli.handlers.which")
    def test_backward_compatibility_functions(self, mock_which):
        """Test that the standalone functions still work for backward compatibility."""
        mock_which.return_value = "/usr/bin/ffmpeg"

        # Test standalone function
        result = get_ffmpeg_command()
        assert result == "/usr/bin/ffmpeg"

    def test_setup_logging_function(self):
        """Test that setup_logging function is available and callable."""
        # This should not raise an exception
        setup_logging(verbose=False)
        setup_logging(verbose=True)

    @patch("src.cli.handlers.get_all_video_object_files")
    @patch("click.echo")
    def test_list_video_files_function(self, mock_echo, mock_get_files):
        """Test that list_video_files function works correctly."""
        from src.core.models.inspection import VideoFile

        mock_get_files.return_value = [VideoFile(path=Path(self.test_path / "video1.mp4"))]

        # This should not raise an exception
        list_video_files(self.test_path)

        # Verify the function was called
        mock_get_files.assert_called_once()
        mock_echo.assert_called()


if __name__ == "__main__":
    unittest.main()
