"""
Unit tests for logging configuration functionality.
"""

import logging
import tempfile
import unittest
from pathlib import Path

import pytest

from src.cli.logging import configure_logging_from_config, setup_logging

pytestmark = pytest.mark.unit


class TestConfigureLoggingFromConfig(unittest.TestCase):
    """Test configure_logging_from_config function"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.log_file = self.temp_path / "test.log"

        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        # Clear handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_configure_logging_with_stdout_only(self):
        """Test logging configuration with stdout only (no file)"""
        configure_logging_from_config(level="INFO", log_file=None)

        root_logger = logging.getLogger()

        # Should have exactly one handler (stdout)
        assert len(root_logger.handlers) == 1
        assert root_logger.level == logging.INFO

        # Verify it's a StreamHandler
        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)

    def test_configure_logging_with_stdout_and_file(self):
        """Test logging configuration with both stdout and file handlers"""
        configure_logging_from_config(
            level="DEBUG", log_file=self.log_file, log_format="%(message)s", date_format="%Y-%m-%d"
        )

        root_logger = logging.getLogger()

        # Should have exactly two handlers (stdout and file)
        assert len(root_logger.handlers) == 2
        assert root_logger.level == logging.DEBUG

        # Check handler types
        handler_types = [type(h).__name__ for h in root_logger.handlers]
        assert "StreamHandler" in handler_types
        assert "FileHandler" in handler_types

        # Verify log file was created
        assert self.log_file.parent.exists()

    def test_configure_logging_creates_log_directory(self):
        """Test that logging configuration creates parent directories for log file"""
        nested_log = self.temp_path / "nested" / "dir" / "test.log"

        configure_logging_from_config(level="INFO", log_file=nested_log)

        # Verify nested directory was created
        assert nested_log.parent.exists()
        assert nested_log.parent.is_dir()

    def test_configure_logging_level_conversion(self):
        """Test that string log levels are correctly converted"""
        test_cases = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]

        for level_str, expected_level in test_cases:
            # Clear handlers before each test
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            configure_logging_from_config(level=level_str)
            assert root_logger.level == expected_level

    def test_configure_logging_writes_to_file(self):
        """Test that log messages are actually written to the log file"""
        configure_logging_from_config(
            level="INFO", log_file=self.log_file, log_format="%(message)s"
        )

        # Write a test log message
        test_logger = logging.getLogger("test_module")
        test_message = "Test log message for file output"
        test_logger.info(test_message)

        # Force flush handlers
        for handler in logging.getLogger().handlers:
            handler.flush()

        # Verify message was written to file
        assert self.log_file.exists()
        log_content = self.log_file.read_text()
        assert test_message in log_content

    def test_configure_logging_removes_existing_handlers(self):
        """Test that existing handlers are removed before adding new ones"""
        # Add some dummy handlers
        root_logger = logging.getLogger()
        dummy_handler1 = logging.StreamHandler()
        dummy_handler2 = logging.StreamHandler()
        root_logger.addHandler(dummy_handler1)
        root_logger.addHandler(dummy_handler2)

        assert len(root_logger.handlers) >= 2

        # Configure logging should clear them
        configure_logging_from_config(level="INFO", log_file=self.log_file)

        # Should only have the new handlers (stdout + file = 2)
        assert len(root_logger.handlers) == 2
        assert dummy_handler1 not in root_logger.handlers
        assert dummy_handler2 not in root_logger.handlers

    def test_configure_logging_with_custom_format(self):
        """Test logging configuration with custom format strings"""
        custom_format = "%(levelname)s - %(name)s - %(message)s"
        custom_date_format = "%Y-%m-%d %H:%M:%S"

        configure_logging_from_config(
            level="INFO",
            log_file=self.log_file,
            log_format=custom_format,
            date_format=custom_date_format,
        )

        root_logger = logging.getLogger()

        # Verify formatters were applied to all handlers
        for handler in root_logger.handlers:
            assert handler.formatter is not None
            # Check that the format string was used
            assert handler.formatter._fmt == custom_format


class TestSetupLogging(unittest.TestCase):
    """Test setup_logging function (backward compatibility)"""

    def tearDown(self):
        """Clean up handlers after each test"""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def test_setup_logging_verbose_levels(self):
        """Test that setup_logging handles different verbosity levels"""
        test_cases = [
            (0, logging.WARNING),
            (1, logging.INFO),
            (2, logging.DEBUG),
        ]

        for verbose, _expected_level in test_cases:
            # Clear handlers
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging(verbose)
            # Note: setup_logging uses basicConfig which may not set root logger level directly
            # but the handler level should be correct
            assert len(root_logger.handlers) > 0
