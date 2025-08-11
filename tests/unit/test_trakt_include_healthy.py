"""Tests for Trakt sync functionality with include_statuses parameter."""

import contextlib
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cli.handlers import TraktHandler
from src.config.config import (
    AppConfig,
    LoggingConfig,
    OutputConfig,
    ProcessingConfig,
    ScanConfig,
    TraktConfig,
)
from src.core.credential_validator import CredentialValidationResult
from src.core.models.scanning import FileStatus, ScanMode
from src.core.watchlist import process_scan_file, sync_to_trakt_watchlist


class TestTraktIncludeStatuses:
    """Test Trakt sync functionality with include_statuses parameter."""

    @pytest.fixture
    def sample_scan_data(self):
        """Sample scan data with mixed file statuses."""
        return {
            "results": [
                {
                    "filename": "/movies/The Matrix (1999).mp4",
                    "is_corrupt": False,
                    "needs_deep_scan": False,
                },
                {
                    "filename": "/movies/Blade Runner (1982).mkv",
                    "is_corrupt": True,
                    "needs_deep_scan": False,
                },
                {
                    "filename": "/tv/Breaking Bad S01E01.mp4",
                    "is_corrupt": False,
                    "needs_deep_scan": True,
                },
                {
                    "filename": "/movies/Inception (2010).mp4",
                    "is_corrupt": False,
                    "needs_deep_scan": False,
                },
            ]
        }

    @pytest.fixture
    def temp_scan_file(self, sample_scan_data):
        """Create a temporary scan file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_scan_data, f)
            return Path(f.name)

    @pytest.fixture
    def mock_config(self):
        """Mock AppConfig for testing."""
        return AppConfig(
            logging=LoggingConfig(level="INFO"),
            output=OutputConfig(default_output_dir=Path("/tmp")),
            processing=ProcessingConfig(max_workers=2),
            scan=ScanConfig(
                mode=ScanMode.QUICK, default_input_dir=Path("/tmp"), extensions=[".mp4", ".mkv"]
            ),
            trakt=TraktConfig(
                client_id="test_client",
                client_secret="test_secret",
                # Use default include_statuses (HEALTHY) instead of overriding
            ),
            ffmpeg={"command": "ffmpeg", "quick_timeout": 60, "deep_timeout": 900},
        )

    def test_process_scan_file_exclude_healthy(self, temp_scan_file):
        """Test that process_scan_file excludes healthy files by default."""
        media_items = process_scan_file(
            str(temp_scan_file), include_statuses=[FileStatus.CORRUPT, FileStatus.SUSPICIOUS]
        )

        # Should only include corrupt and suspicious files
        assert len(media_items) == 2
        filenames = [item.title for item in media_items]
        assert "Blade Runner" in str(filenames)
        assert "Breaking Bad" in str(filenames)

    def test_process_scan_file_include_healthy(self, temp_scan_file):
        """Test that process_scan_file includes all files when all statuses specified."""
        media_items = process_scan_file(
            str(temp_scan_file),
            include_statuses=[FileStatus.HEALTHY, FileStatus.CORRUPT, FileStatus.SUSPICIOUS],
        )

        # Should include all files
        assert len(media_items) == 4
        filenames = [item.title for item in media_items]
        assert "The Matrix" in str(filenames)
        assert "Blade Runner" in str(filenames)
        assert "Breaking Bad" in str(filenames)
        assert "Inception" in str(filenames)

    def test_process_scan_file_only_healthy(self, temp_scan_file):
        """Test that process_scan_file can include only healthy files."""
        media_items = process_scan_file(str(temp_scan_file), include_statuses=[FileStatus.HEALTHY])

        # Should include only healthy files
        assert len(media_items) == 2
        filenames = [item.title for item in media_items]
        assert "The Matrix" in str(filenames)
        assert "Inception" in str(filenames)

    @patch("src.core.watchlist.TraktAPI")
    @patch("src.core.watchlist.FilenameParser")
    def test_sync_to_trakt_watchlist_exclude_healthy(
        self, mock_parser, mock_api, temp_scan_file, mock_config
    ):
        """Test sync_to_trakt_watchlist excludes healthy files by default."""
        # Mock the parser to return predictable media items
        mock_media_item = MagicMock()
        mock_media_item.title = "Test Movie"
        mock_media_item.media_type = "movie"
        mock_media_item.year = 2023
        mock_media_item.original_filename = "test_movie.mp4"
        mock_parser.parse_filename.return_value = mock_media_item

        # Mock API to fail gracefully
        mock_api_instance = MagicMock()
        mock_api_instance.search_movie.return_value = []  # No results found
        mock_api.return_value = mock_api_instance

        result = sync_to_trakt_watchlist(
            scan_file=str(temp_scan_file),
            config=mock_config,
        )

        # Should process only corrupt/suspicious files (2)
        assert mock_parser.parse_filename.call_count == 2
        assert result.failed == 2  # Both files not found on Trakt

    @patch("src.core.watchlist.TraktAPI")
    @patch("src.core.watchlist.FilenameParser")
    def test_sync_to_trakt_watchlist_include_all(
        self, mock_parser, mock_api, temp_scan_file, mock_config
    ):
        """Test sync_to_trakt_watchlist includes all files when all statuses specified."""
        # Mock the parser to return predictable media items
        mock_media_item = MagicMock()
        mock_media_item.title = "Test Movie"
        mock_media_item.media_type = "movie"
        mock_media_item.year = 2023
        mock_media_item.original_filename = "test_movie.mp4"
        mock_parser.parse_filename.return_value = mock_media_item

        # Mock API to fail gracefully
        mock_api_instance = MagicMock()
        mock_api_instance.search_movie.return_value = []  # No results found
        mock_api.return_value = mock_api_instance

        result = sync_to_trakt_watchlist(
            scan_file=str(temp_scan_file),
            config=mock_config,
            include_statuses=[FileStatus.HEALTHY, FileStatus.CORRUPT, FileStatus.SUSPICIOUS],
        )

        # Should process all files (4)
        assert mock_parser.parse_filename.call_count == 4
        assert result.failed == 4  # All files not found on Trakt

    @patch("src.core.credential_validator.validate_trakt_secrets")
    @patch("src.core.watchlist.sync_to_trakt_watchlist")
    def test_trakt_handler_passes_include_statuses(self, mock_sync, mock_validate, mock_config, temp_scan_file):
        """Test that TraktHandler correctly passes include_statuses parameter."""
        # Configure mock result with proper attributes
        mock_result = MagicMock()
        mock_result.total = 0
        mock_result.movies_added = 0
        mock_result.shows_added = 0
        mock_result.failed = 0
        mock_result.watchlist = None
        mock_result.results = []
        mock_sync.return_value = mock_result

        handler = TraktHandler(mock_config)

        # Test with config's default statuses (should use config's include_statuses)
        handler.sync_to_watchlist(
            scan_file=temp_scan_file,
        )

        mock_sync.assert_called_with(
            scan_file=str(temp_scan_file),
            config=mock_config,
            interactive=False,
            watchlist=None,
            include_statuses=[FileStatus.CORRUPT, FileStatus.SUSPICIOUS],  # From mock_config
        )

        # Test with custom statuses
        custom_statuses = [FileStatus.HEALTHY, FileStatus.CORRUPT]
        handler.sync_to_watchlist(scan_file=temp_scan_file, include_statuses=custom_statuses)

        mock_sync.assert_called_with(
            scan_file=str(temp_scan_file),
            config=mock_config,
            interactive=False,
            watchlist=None,
            include_statuses=custom_statuses,
        )

    def test_config_include_statuses_default(self):
        """Test that TraktConfig has include_statuses defaulting to [HEALTHY]."""
        config = TraktConfig()
        assert config.include_statuses == [FileStatus.HEALTHY]

    def test_config_include_statuses_can_be_set(self):
        """Test that TraktConfig include_statuses can be customized."""
        config = TraktConfig(include_statuses=[FileStatus.HEALTHY, FileStatus.CORRUPT])
        assert config.include_statuses == [FileStatus.HEALTHY, FileStatus.CORRUPT]

    def teardown_method(self, method):
        """Clean up temp files after each test."""
        # Clean up any temporary files
        for file_attr in dir(self):
            if hasattr(self, file_attr):
                attr_value = getattr(self, file_attr)
                if isinstance(attr_value, Path) and attr_value.exists():
                    with contextlib.suppress(OSError, AttributeError):
                        attr_value.unlink()
