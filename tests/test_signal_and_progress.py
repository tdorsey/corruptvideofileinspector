#!/usr/bin/env python3
"""
Combined tests for signal handling and progress reporting functionality
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import inspector as video_inspector


class TestSignalHandling(unittest.TestCase):
    """Test signal handling functionality"""

    def test_setup_signal_handlers(self):
        """Test that signal handlers can be set up"""
        video_inspector.setup_signal_handlers()
        # Just test that it doesn't crash
        assert video_inspector.signal_handler is not None


class TestProgressReporter(unittest.TestCase):
    """Test progress reporting functionality"""

    def test_progress_reporter_creation(self):
        """Test creating a progress reporter"""
        reporter = video_inspector.ProgressReporter(100, "hybrid")
        assert reporter.total_files == 100
        assert reporter.scan_mode == "hybrid"
        assert reporter.processed_count == 0
        assert reporter.corrupt_count == 0

    def test_progress_reporter_update(self):
        """Test updating progress"""
        reporter = video_inspector.ProgressReporter(100, "quick")
        reporter.update(current_file="/test/file.mp4", processed_count=25, corrupt_count=3)

        assert reporter.current_file == "/test/file.mp4"
        assert reporter.processed_count == 25
        assert reporter.corrupt_count == 3


class TestGlobalProgressTracking(unittest.TestCase):
    """Test global progress tracking for signal handlers"""

    def test_global_progress_initialization(self):
        """Test that global progress tracking is properly initialized"""
        # Check that global progress dict exists
        assert isinstance(video_inspector._current_progress, dict)
        assert "current_file" in video_inspector._current_progress
        assert "total_files" in video_inspector._current_progress

    def test_progress_reporter_updates_global(self):
        """Test that ProgressReporter updates global progress"""
        reporter = video_inspector.ProgressReporter(50, "hybrid")
        reporter.update(current_file="/test/file.mp4", processed_count=10, corrupt_count=1)

        # Check that global progress was updated
        progress = video_inspector._current_progress
        assert progress["current_file"] == "/test/file.mp4"
        assert progress["processed_count"] == 10
        assert progress["corrupt_count"] == 1
        assert progress["remaining_count"] == 40


class TestEnhancedWAL(unittest.TestCase):
    """Test enhanced WAL functionality with results file"""


if __name__ == "__main__":
    unittest.main()
