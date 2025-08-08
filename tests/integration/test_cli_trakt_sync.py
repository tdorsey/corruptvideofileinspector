"""Tests for CLI trakt sync command scan file parameter requirement."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.commands import sync as trakt_sync_command
from src.core.models.inspection import VideoFile
from src.core.models.scanning import ScanMode, ScanResult, ScanSummary

pytestmark = pytest.mark.integration


class TestTraktSyncScanFileRequirement(unittest.TestCase):
    """Test that trakt sync command requires scan file parameter."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create a valid scan results file
        self.scan_file = self.temp_path / "scan_results.json"
        self._create_test_scan_file()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_scan_file(self) -> None:
        """Create a test scan results JSON file."""
        # Create test scan results
        video_file = VideoFile(path=Path("/test/video.mp4"))
        scan_result = ScanResult(
            video_file=video_file,
            is_corrupt=False,
            confidence=0.0,
            file_size=1024 * 1024,
            inspection_time=1.5,
            scan_mode=ScanMode.QUICK,
            needs_deep_scan=False,
            deep_scan_completed=False,
            timestamp=1609459200.0,  # 2021-01-01 00:00:00 UTC
        )

        scan_summary = ScanSummary(
            directory=Path("/test"),
            total_files=1,
            processed_files=1,
            corrupt_files=0,
            healthy_files=1,
            scan_time=1.5,
            scan_mode=ScanMode.QUICK,
            deep_scans_needed=0,
            deep_scans_completed=0,
            was_resumed=False,
        )

        # Create the JSON structure
        scan_data = {
            "summary": scan_summary.model_dump(),
            "results": [scan_result.model_dump()],
        }

        # Write to file
        with self.scan_file.open("w", encoding="utf-8") as f:
            json.dump(scan_data, f, indent=2, default=str)

    def test_trakt_sync_requires_scan_file_argument(self) -> None:
        """Test that trakt sync command requires scan_file as positional argument."""
        # Test the sync command directly (without scan_file argument)
        result = self.runner.invoke(trakt_sync_command, [])

        # Should show help or error about missing argument
        assert result.exit_code != 0, "Command should fail without scan_file"
        assert "missing argument" in result.output.lower()

    def test_trakt_sync_with_nonexistent_scan_file(self) -> None:
        """Test that trakt sync command fails with non-existent scan file."""
        nonexistent_file = self.temp_path / "nonexistent.json"

        result = self.runner.invoke(trakt_sync_command, [str(nonexistent_file)])

        # Should fail because file doesn't exist
        assert result.exit_code != 0, "Command should fail with non-existent file"
        assert "does not exist" in result.output.lower()

    @patch("src.cli.handlers.TraktHandler.sync_to_watchlist")
    @patch("src.cli.commands.load_config")
    def test_trakt_sync_with_valid_scan_file(
        self, mock_load_config: MagicMock, mock_sync: MagicMock
    ) -> None:
        """Test that trakt sync command works with valid scan file."""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.trakt.client_id = "test_client_id"
        mock_load_config.return_value = mock_config

        # Mock sync result
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "total": 1,
            "movies_added": 0,
            "shows_added": 1,
            "failed": 0,
        }
        mock_sync.return_value = mock_result

        result = self.runner.invoke(trakt_sync_command, [str(self.scan_file)])

        # Should succeed
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify sync was called with correct scan_file
        mock_sync.assert_called_once()
        call_kwargs = mock_sync.call_args.kwargs
        assert call_kwargs["scan_file"] == self.scan_file

    def test_trakt_sync_scan_file_is_positional_not_option(self) -> None:
        """Test that scan_file is a positional argument, not an option."""
        # Test with --scan-file (should not work as it's not an option)
        result = self.runner.invoke(trakt_sync_command, ["--scan-file", str(self.scan_file)])

        # Should fail because --scan-file is not a valid option
        assert result.exit_code != 0, "Should fail with --scan-file option"
        assert "no such option" in result.output.lower()

    @patch("src.cli.handlers.TraktHandler.sync_to_watchlist")
    @patch("src.cli.commands.load_config")
    def test_trakt_sync_scan_file_path_validation(
        self, mock_load_config: MagicMock, mock_sync: MagicMock
    ) -> None:
        """Test that scan_file path is properly validated."""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.trakt.client_id = "test_client_id"
        mock_load_config.return_value = mock_config

        # Mock sync result
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"total": 0}
        mock_sync.return_value = mock_result

        # Test with valid file path
        result = self.runner.invoke(trakt_sync_command, [str(self.scan_file)])
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify the scan_file parameter is passed correctly
        mock_sync.assert_called_once()
        call_kwargs = mock_sync.call_args.kwargs
        assert call_kwargs["scan_file"] == self.scan_file
        assert isinstance(call_kwargs["scan_file"], Path)

    def test_trakt_sync_help_shows_scan_file_requirement(self) -> None:
        """Test that help output shows scan_file as required argument."""
        result = self.runner.invoke(trakt_sync_command, ["--help"])

        assert result.exit_code == 0, "Help command should succeed"

        # Check that help shows scan_file as required argument
        help_text = result.output.lower()
        assert "scan_file" in help_text, "Help should mention scan_file"
        # The help shows it in the usage line, not necessarily with the word "argument"
        assert "usage:" in help_text, "Help should show usage information"

    @patch("src.cli.handlers.TraktHandler.sync_to_watchlist")
    @patch("src.cli.commands.load_config")
    def test_trakt_sync_with_additional_options(
        self, mock_load_config: MagicMock, mock_sync: MagicMock
    ) -> None:
        """Test trakt sync with scan_file plus additional options."""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.trakt.client_id = "test_client_id"
        mock_load_config.return_value = mock_config

        # Mock sync result
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"total": 0}
        mock_sync.return_value = mock_result

        # Test with scan_file and interactive option (which is implemented)
        result = self.runner.invoke(
            trakt_sync_command,
            [
                str(self.scan_file),
                "--interactive",
                "--include-status",
                "healthy",
                "--include-status",
                "corrupt",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify sync was called with correct parameters
        mock_sync.assert_called_once()
        call_kwargs = mock_sync.call_args.kwargs
        assert call_kwargs["scan_file"] == self.scan_file
        assert call_kwargs["interactive"] is True
        # Check that include_statuses contains the expected FileStatus enums
        from src.core.models.scanning import FileStatus

        expected_statuses = [FileStatus.HEALTHY, FileStatus.CORRUPT]
        assert call_kwargs["include_statuses"] == expected_statuses

    @patch("src.cli.handlers.TraktHandler.sync_to_watchlist")
    @patch("src.cli.commands.load_config")
    def test_trakt_sync_include_status_filtering(
        self, mock_load_config: MagicMock, mock_sync: MagicMock
    ) -> None:
        """Test that include_status parameter filters files correctly."""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.trakt.client_id = "test_client_id"
        mock_load_config.return_value = mock_config

        # Mock sync result
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"total": 0}
        mock_sync.return_value = mock_result

        # Test with only corrupt files
        result = self.runner.invoke(
            trakt_sync_command,
            [
                str(self.scan_file),
                "--include-status",
                "corrupt",
                "--include-status",
                "suspicious",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify the include_statuses parameter is passed correctly
        mock_sync.assert_called_once()
        call_kwargs = mock_sync.call_args.kwargs
        from src.core.models.scanning import FileStatus

        expected_statuses = [FileStatus.CORRUPT, FileStatus.SUSPICIOUS]
        assert call_kwargs["include_statuses"] == expected_statuses

    def test_trakt_sync_order_of_arguments_matters(self) -> None:
        """Test that scan_file must be provided as first argument after sync."""
        # Test with options before scan_file (should fail)
        result = self.runner.invoke(trakt_sync_command, ["--interactive", str(self.scan_file)])

        # Should fail because scan_file should come first
        assert result.exit_code != 0, "Should fail when scan_file is not first argument"


if __name__ == "__main__":
    unittest.main()
