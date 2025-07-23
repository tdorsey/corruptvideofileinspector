#!/usr/bin/env python3
"""
Tests for new signal handling and progress reporting functionality
"""

import os
import signal

# Add parent directory to path for imports
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import video_inspector


class TestSignalHandling(unittest.TestCase):
    """Test signal handling functionality"""

    def test_setup_signal_handlers(self):
        """Test that signal handlers can be set up"""
        video_inspector.setup_signal_handlers()
        # Just test that it doesn't crash
        assert video_inspector.signal_handler is not None

    def test_signal_handler_function(self):
        """Test signal handler function"""
        # Setup test progress data
        video_inspector._current_progress.update(
            {
                "current_file": "/test/file.mp4",
                "total_files": 100,
                "processed_count": 50,
                "corrupt_count": 5,
                "remaining_count": 50,
                "scan_mode": "hybrid",
                "start_time": time.time() - 60.0,
            }
        )

        # Mock the print function to capture output
        with patch("builtins.print") as mock_print:
            # Call signal handler directly (simulate SIGUSR1)
            video_inspector.signal_handler(signal.SIGUSR1, None)

            # Check that print was called (progress was reported)
            assert mock_print.called

            # Check that progress report header was printed
            calls = [str(call) for call in mock_print.call_args_list]
            progress_calls = [call for call in calls if "PROGRESS REPORT" in call]
            assert len(progress_calls) > 0, "Progress report should be printed"


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

    def test_progress_reporter_output(self):
        """Test progress reporter output"""
        reporter = video_inspector.ProgressReporter(100, "deep")
        reporter.update(current_file="/test/video.mp4", processed_count=75, corrupt_count=2)

        with patch("builtins.print") as mock_print:
            reporter.report_progress(force_output=True)
            assert mock_print.called

            # Check that progress information was printed
            calls = [str(call) for call in mock_print.call_args_list]
            progress_calls = [call for call in calls if "Files Processed: 75/100" in call]
            assert len(progress_calls) > 0, "Progress info should be printed"


class TestEnhancedWAL(unittest.TestCase):
    """Test enhanced WAL functionality with results file"""

    def test_wal_with_results_file(self):
        """Test that WAL creates both WAL and results files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            wal = video_inspector.WriteAheadLog(
                directory=temp_dir, scan_mode=video_inspector.ScanMode.HYBRID, extensions=[".mp4"]
            )

            # Check that both file paths are set
            assert str(wal.wal_path).endswith(".json")
            assert str(wal.results_path).endswith(".json")
            assert wal.wal_path != wal.results_path

    def test_wal_append_result_creates_both_files(self):
        """Test that appending results creates both WAL and results files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            wal = video_inspector.WriteAheadLog(
                directory=temp_dir, scan_mode=video_inspector.ScanMode.QUICK, extensions=[".mp4"]
            )

            # Create a test result
            result = video_inspector.VideoInspectionResult("/test/video.mp4")
            result.is_corrupt = False
            result.inspection_time = 3.5
            result.file_size = 1024000

            # Append result
            wal.append_result(result)

            # Check that both files exist
            assert wal.wal_path.exists(), "WAL file should exist"
            assert wal.results_path.exists(), "Results file should exist"

            # Check that result is in processed files
            assert wal.is_processed("/test/video.mp4")

    def test_wal_resume_functionality(self):
        """Test that WAL can be resumed from existing files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first WAL and add result
            wal1 = video_inspector.WriteAheadLog(
                directory=temp_dir,
                scan_mode=video_inspector.ScanMode.HYBRID,
                extensions=[".mp4", ".avi"],
            )

            result = video_inspector.VideoInspectionResult("/test/video1.mp4")
            result.is_corrupt = True
            result.error_message = "Test corruption"

            wal1.create_wal_file()
            wal1.append_result(result)

            # Create second WAL instance and try to resume
            wal2 = video_inspector.WriteAheadLog(
                directory=temp_dir,
                scan_mode=video_inspector.ScanMode.HYBRID,
                extensions=[".mp4", ".avi"],
            )

            resumed = wal2.load_existing_wal()
            assert resumed, "Should be able to resume"
            assert len(wal2.results) == 1, "Should have one result"
            assert wal2.is_processed("/test/video1.mp4"), "File should be marked as processed"

    def test_wal_cleanup_preserves_results(self):
        """Test that cleanup removes WAL but preserves results file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            wal = video_inspector.WriteAheadLog(
                directory=temp_dir, scan_mode=video_inspector.ScanMode.DEEP, extensions=[".mp4"]
            )

            # Create files
            wal.create_wal_file()
            result = video_inspector.VideoInspectionResult("/test/video.mp4")
            wal.append_result(result)

            # Verify both files exist
            assert wal.wal_path.exists()
            assert wal.results_path.exists()

            # Cleanup
            wal.cleanup()

            # WAL should be removed, results should remain
            assert not wal.wal_path.exists(), "WAL file should be removed"
            assert wal.results_path.exists(), "Results file should be preserved"


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
        assert video_inspector._current_progress["current_file"] == "/test/file.mp4"
        assert video_inspector._current_progress["processed_count"] == 10
        assert video_inspector._current_progress["corrupt_count"] == 1
        assert video_inspector._current_progress["remaining_count"] == 40


if __name__ == "__main__":
    unittest.main()
