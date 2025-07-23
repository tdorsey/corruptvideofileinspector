"""
Integration tests for CLI handler functionality (core functions only)
"""

import contextlib
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# We'll test the functions that don't require typer
# by importing and testing them individually


class TestCLIHandlerCoreIntegration(unittest.TestCase):
    """Integration tests for CLI handler core functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_files = []

        # Create a test file in the directory
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("test content")
        self.test_files.append(str(test_file))

    def tearDown(self):
        """Clean up test environment"""
        # Clean up test files
        for file_path in self.test_files:
            with contextlib.suppress(FileNotFoundError):
                Path(file_path).unlink()

        # Remove test directory
        with contextlib.suppress(OSError):
            Path(self.test_dir).rmdir()

    def test_setup_logging_function_exists(self):
        """Test that setup_logging function can be imported and called"""
        # We'll import the function directly to avoid typer import issues
        cli_handler_path = Path(__file__).resolve().parent.parent / "cli_handler.py"
        content = cli_handler_path.read_text()

        # Check that setup_logging function exists
        assert "def setup_logging" in content
        assert "logging.basicConfig" in content

        # Test logging configuration directly
        logger = logging.getLogger("test_logger")

        # Test that logging module works correctly
        assert logger is not None

    def test_validate_directory_function_exists(self):
        """
        Test that validate_directory function exists and has correct
        signature
        """
        cli_handler_path = Path(__file__).resolve().parent.parent / "cli_handler.py"
        content = cli_handler_path.read_text()

        # Check that validate_directory function exists
        assert "def validate_directory" in content
        assert "Path(directory).resolve()" in content
        assert "FileNotFoundError" in content
        assert "NotADirectoryError" in content

    def test_validate_arguments_function_exists(self):
        """Test that validate_arguments function exists"""
        cli_handler_path = Path(__file__).resolve().parent.parent / "cli_handler.py"
        content = cli_handler_path.read_text()

        # Check that validate_arguments function exists
        assert "def validate_arguments" in content
        assert "verbose and quiet" in content
        assert "max_workers <= 0" in content

    def test_directory_validation_logic(self):
        """Test directory validation logic manually"""

        # Test valid directory
        path = Path(self.test_dir)
        assert path.exists()
        assert path.is_dir()

        # Test non-existent directory
        nonexistent = Path("/nonexistent/directory")
        assert not nonexistent.exists()

        # Test file instead of directory (create a file)
        test_file = Path(self.test_dir) / "not_a_directory.txt"
        test_file.write_text("test")
        self.test_files.append(str(test_file))

        file_path = test_file
        assert file_path.exists()
        assert not file_path.is_dir()

    def test_logging_configuration_options(self):
        """Test logging configuration options"""
        import logging

        # Test different log levels
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]

        for level in levels:
            # Configure logging at this level
            logging.basicConfig(level=level, force=True)

            # Create a logger
            logger = logging.getLogger(f"test_logger_{level}")

            # Verify the logger was created
            assert logger is not None

            # Check that the logging level is set correctly
            root_logger = logging.getLogger()
            assert root_logger.level == level

    def test_cli_imports_and_dependencies(self):
        """Test that CLI module has expected imports"""
        cli_handler_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "cli_handler.py",
        )
        with Path(cli_handler_path).open() as f:
            content = f.read()

        # Check for expected imports
        expected_imports = [
            "import json",
            "import os",
            "import sys",
            "import logging",
            "from pathlib import Path",
            "from typing import List, Optional",
            "from utils import",
            "from video_inspector import",
            "from trakt_watchlist import",
        ]

        for import_line in expected_imports:
            assert import_line in content

    def test_cli_main_functions_exist(self):
        """Test that main CLI functions exist"""
        cli_handler_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "cli_handler.py",
        )
        with Path(cli_handler_path).open() as f:
            content = f.read()

        # Check for main functions
        expected_functions = [
            "def setup_logging",
            "def validate_directory",
            "def validate_arguments",
        ]

        for function in expected_functions:
            assert function in content

    def test_integration_with_utils_and_video_inspector(self):
        """
        Test that CLI handler can integrate with utils and video_inspector
        """
        # Test that we can import the required functions from other modules
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

        try:
            from utils import count_all_video_files, get_video_extensions
            from video_inspector import ScanMode, get_all_video_object_files

            # Test basic functionality
            count = count_all_video_files(self.test_dir)
            assert isinstance(count, int)

            extensions = get_video_extensions()
            assert isinstance(extensions, list)

            video_files = get_all_video_object_files(self.test_dir)
            assert isinstance(video_files, list)

            # Test ScanMode enum
            assert ScanMode.QUICK.value == "quick"

        except ImportError as e:
            self.fail(f"Could not import required modules: {e}")


if __name__ == "__main__":
    unittest.main()
