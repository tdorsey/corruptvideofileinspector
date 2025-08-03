"""
Tests for the FULL scan mode functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.config.config import (
    AppConfig,
    FFmpegConfig,
    LoggingConfig,
    OutputConfig,
    ProcessingConfig,
    ScanConfig,
    TraktConfig,
)
from src.core.models.inspection import VideoFile
from src.core.models.scanning import ScanMode, ScanResult, ScanSummary
from src.core.scanner import VideoScanner
from src.ffmpeg.ffmpeg_client import FFmpegClient


class TestFullScanMode:
    """Test cases for FULL scan mode functionality."""

    def setup_method(self):
        """Setup test configuration."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = AppConfig(
            logging=LoggingConfig(),
            ffmpeg=FFmpegConfig(),
            processing=ProcessingConfig(),
            output=OutputConfig(default_output_dir=self.temp_dir),
            scan=ScanConfig(default_input_dir=self.temp_dir),
            trakt=TraktConfig(),
        )

    def test_scan_mode_enum_has_full(self):
        """Test that FULL scan mode exists in ScanMode enum."""
        assert hasattr(ScanMode, "FULL")
        assert ScanMode.FULL.value == "full"

    def test_full_scan_mode_in_choices(self):
        """Test that FULL mode is included in scan mode choices."""
        scan_modes = [mode.value for mode in ScanMode]
        assert "full" in scan_modes
        assert len(scan_modes) == 4  # QUICK, DEEP, HYBRID, FULL

    @patch("src.ffmpeg.ffmpeg_client.shutil.which")
    @patch("subprocess.run")
    def test_ffmpeg_client_inspect_full_no_timeout(self, mock_run, mock_which):
        """Test that FFmpegClient.inspect_full runs without timeout."""
        # Mock ffmpeg availability
        mock_which.return_value = "/usr/bin/ffmpeg"

        # Setup mock for both validation and inspection calls
        def side_effect(*args, **kwargs):
            mock_process = Mock()
            if "-version" in args[0]:
                mock_process.returncode = 0
                mock_process.stdout = "ffmpeg version 4.4.0"
            else:
                mock_process.returncode = 0
                mock_process.stderr = ""
            return mock_process

        mock_run.side_effect = side_effect

        # Create test video file
        test_file = self.temp_dir / "test.mp4"
        test_file.touch()
        video_file = VideoFile(path=test_file)

        # Test full scan
        client = FFmpegClient(self.config.ffmpeg)
        result = client.inspect_full(video_file)

        # Verify the inspect_full call used timeout=None
        # Skip the validation calls and find the actual scan call
        scan_calls = [call for call in mock_run.call_args_list if "-version" not in str(call)]

        assert len(scan_calls) >= 1
        args, kwargs = scan_calls[0]
        assert kwargs.get("timeout") is None

        # Verify result
        assert isinstance(result, ScanResult)
        assert result.video_file == video_file

    @patch("src.ffmpeg.ffmpeg_client.shutil.which")
    @patch("subprocess.run")
    def test_ffmpeg_client_inspect_full_handles_exceptions(self, mock_run, mock_which):
        """Test that inspect_full handles exceptions gracefully."""
        # Mock ffmpeg availability for initialization
        mock_which.return_value = "/usr/bin/ffmpeg"

        # Setup mock to pass validation but fail on actual scan
        def side_effect(*args, **kwargs):
            if "-version" in args[0]:
                mock_process = Mock()
                mock_process.returncode = 0
                mock_process.stdout = "ffmpeg version 4.4.0"
                return mock_process
            raise RuntimeError("Test error")

        mock_run.side_effect = side_effect

        # Create test video file
        test_file = self.temp_dir / "test.mp4"
        test_file.touch()
        video_file = VideoFile(path=test_file)

        # Test full scan
        client = FFmpegClient(self.config.ffmpeg)
        result = client.inspect_full(video_file)

        # Verify error handling
        assert isinstance(result, ScanResult)
        assert result.video_file == video_file
        assert "Full scan failed: Test error" in result.error_message

    @patch("src.core.scanner.subprocess.run")
    def test_video_scanner_full_mode_no_timeout(self, mock_run):
        """Test that VideoScanner uses no timeout for FULL mode."""
        # Setup mock
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Create test video files
        test_file1 = self.temp_dir / "test1.mp4"
        test_file1.touch()
        test_file2 = self.temp_dir / "test2.mp4"
        test_file2.touch()

        # Mock get_video_files to return our test files
        scanner = VideoScanner(self.config)

        with patch.object(scanner, "get_video_files") as mock_get_files:
            mock_get_files.return_value = [
                VideoFile(path=test_file1),
                VideoFile(path=test_file2),
            ]

            # Run full scan
            summary = scanner.scan_directory(
                directory=self.temp_dir,
                scan_mode=ScanMode.FULL,
                recursive=True,
                resume=False,
            )

            # Verify subprocess.run calls used timeout=None for FULL mode
            for call in mock_run.call_args_list:
                args, kwargs = call
                assert kwargs.get("timeout") is None

            # Verify summary
            assert isinstance(summary, ScanSummary)
            assert summary.scan_mode == ScanMode.FULL
            assert summary.total_files == 2

    def test_scan_summary_full_mode_serialization(self):
        """Test that ScanSummary correctly serializes FULL mode."""
        summary = ScanSummary(
            directory=self.temp_dir,
            total_files=5,
            processed_files=5,
            corrupt_files=1,
            healthy_files=4,
            scan_mode=ScanMode.FULL,
            scan_time=120.5,
        )

        # Test serialization
        data = summary.model_dump()
        assert data["scan_mode"] == "full"

        # Test deserialization
        loaded = ScanSummary.model_validate(data)
        assert loaded.scan_mode == ScanMode.FULL

    @patch("src.core.scanner.subprocess.run")
    def test_full_scan_mode_processes_all_files(self, mock_run):
        """Test that FULL mode processes all files directly (not just suspicious ones)."""
        # Setup mock
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Create test video files
        test_files = []
        for i in range(3):
            test_file = self.temp_dir / f"test{i}.mp4"
            test_file.touch()
            test_files.append(VideoFile(path=test_file))

        # Mock get_video_files
        scanner = VideoScanner(self.config)

        with patch.object(scanner, "get_video_files") as mock_get_files:
            mock_get_files.return_value = test_files

            # Run full scan
            summary = scanner.scan_directory(
                directory=self.temp_dir,
                scan_mode=ScanMode.FULL,
                recursive=True,
                resume=False,
            )

            # For FULL mode, all files should be processed directly
            # Should have calls for each file (no quick scan phase)
            assert mock_run.call_count >= len(test_files)
            assert summary.processed_files == len(test_files)

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


class TestFullScanModeIntegration:
    """Integration tests for FULL scan mode."""

    def setup_method(self):
        """Setup test configuration."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = AppConfig(
            logging=LoggingConfig(),
            ffmpeg=FFmpegConfig(),
            processing=ProcessingConfig(),
            output=OutputConfig(default_output_dir=self.temp_dir),
            scan=ScanConfig(default_input_dir=self.temp_dir),
            trakt=TraktConfig(),
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_full_scan_integration_with_timeout_none(self, mock_run, mock_which):
        """Integration test to ensure FULL scan mode works end-to-end."""
        # Mock ffmpeg availability
        mock_which.return_value = "/usr/bin/ffmpeg"

        # Mock ffmpeg execution for validation and scanning
        def side_effect(*args, **kwargs):
            mock_process = Mock()
            if "-version" in args[0]:
                mock_process.returncode = 0
                mock_process.stdout = "ffmpeg version 4.4.0"
            else:
                mock_process.returncode = 0
                mock_process.stderr = ""
            return mock_process

        mock_run.side_effect = side_effect

        # Create test video file
        test_file = self.temp_dir / "integration_test.mp4"
        test_file.touch()

        # Test full scan
        scanner = VideoScanner(self.config)

        with patch.object(scanner, "get_video_files") as mock_get_files:
            mock_get_files.return_value = [VideoFile(path=test_file)]

            summary = scanner.scan_directory(
                directory=self.temp_dir,
                scan_mode=ScanMode.FULL,
                recursive=True,
                resume=False,
            )

            # Verify that subprocess calls for scanning used timeout=None
            scan_calls = [call for call in mock_run.call_args_list if "-version" not in str(call)]

            for call in scan_calls:
                args, kwargs = call
                # For FULL mode, timeout should be None
                assert kwargs.get("timeout") is None

            assert summary.scan_mode == ScanMode.FULL
            assert summary.total_files == 1

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
