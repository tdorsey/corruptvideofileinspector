"""
Tests for Trakt credential validation in CLI commands.
"""

import pytest

from src.cli.handlers import TraktHandler
from src.config.config import (
    AppConfig,
    FFmpegConfig,
    LoggingConfig,
    OutputConfig,
    ProcessingConfig,
    ScanConfig,
    TraktConfig,
)
from src.core.models.scanning import ScanMode
from pathlib import Path

pytestmark = pytest.mark.unit


class TestTraktCredentialValidation:
    """Test credential validation for Trakt commands."""

    @pytest.fixture
    def mock_config_missing_credentials(self):
        """Mock AppConfig with missing Trakt credentials."""
        return AppConfig(
            logging=LoggingConfig(level="INFO"),
            ffmpeg=FFmpegConfig(command=Path("/usr/bin/ffmpeg")),
            processing=ProcessingConfig(max_workers=2),
            output=OutputConfig(default_output_dir=Path("/tmp")),
            scan=ScanConfig(
                mode=ScanMode.QUICK, 
                default_input_dir=Path("/tmp"), 
                extensions=[".mp4", ".mkv"]
            ),
            trakt=TraktConfig(
                client_id="",  # Empty client_id
                client_secret="",  # Empty client_secret
            ),
        )

    @pytest.fixture
    def mock_config_partial_credentials(self):
        """Mock AppConfig with partial Trakt credentials."""
        return AppConfig(
            logging=LoggingConfig(level="INFO"),
            ffmpeg=FFmpegConfig(command=Path("/usr/bin/ffmpeg")),
            processing=ProcessingConfig(max_workers=2),
            output=OutputConfig(default_output_dir=Path("/tmp")),
            scan=ScanConfig(
                mode=ScanMode.QUICK, 
                default_input_dir=Path("/tmp"), 
                extensions=[".mp4", ".mkv"]
            ),
            trakt=TraktConfig(
                client_id="test_client_id",  # Valid client_id
                client_secret="",  # Missing client_secret
            ),
        )

    @pytest.fixture
    def mock_config_valid_credentials(self):
        """Mock AppConfig with valid Trakt credentials."""
        return AppConfig(
            logging=LoggingConfig(level="INFO"),
            ffmpeg=FFmpegConfig(command=Path("/usr/bin/ffmpeg")),
            processing=ProcessingConfig(max_workers=2),
            output=OutputConfig(default_output_dir=Path("/tmp")),
            scan=ScanConfig(
                mode=ScanMode.QUICK, 
                default_input_dir=Path("/tmp"), 
                extensions=[".mp4", ".mkv"]
            ),
            trakt=TraktConfig(
                client_id="test_client_id",
                client_secret="test_client_secret",
            ),
        )

    def test_list_watchlists_missing_credentials(self, mock_config_missing_credentials):
        """Test that list_watchlists raises ValueError when credentials are missing."""
        handler = TraktHandler(mock_config_missing_credentials)
        
        with pytest.raises(ValueError) as exc_info:
            handler.list_watchlists()
        
        error_message = str(exc_info.value)
        assert "Trakt credentials not configured" in error_message
        assert "client_id and client_secret" in error_message
        assert "environment variables" in error_message

    def test_list_watchlists_partial_credentials(self, mock_config_partial_credentials):
        """Test that list_watchlists raises ValueError when only partial credentials provided."""
        handler = TraktHandler(mock_config_partial_credentials)
        
        with pytest.raises(ValueError) as exc_info:
            handler.list_watchlists()
        
        error_message = str(exc_info.value)
        assert "Trakt credentials not configured" in error_message

    def test_view_watchlist_missing_credentials(self, mock_config_missing_credentials):
        """Test that view_watchlist raises ValueError when credentials are missing."""
        handler = TraktHandler(mock_config_missing_credentials)
        
        with pytest.raises(ValueError) as exc_info:
            handler.view_watchlist()
        
        error_message = str(exc_info.value)
        assert "Trakt credentials not configured" in error_message
        assert "client_id and client_secret" in error_message

    def test_view_watchlist_partial_credentials(self, mock_config_partial_credentials):
        """Test that view_watchlist raises ValueError when only partial credentials provided."""
        handler = TraktHandler(mock_config_partial_credentials)
        
        with pytest.raises(ValueError) as exc_info:
            handler.view_watchlist()
        
        error_message = str(exc_info.value)
        assert "Trakt credentials not configured" in error_message

    def test_credentials_validation_error_message_completeness(self, mock_config_missing_credentials):
        """Test that error message includes all configuration options."""
        handler = TraktHandler(mock_config_missing_credentials)
        
        with pytest.raises(ValueError) as exc_info:
            handler.list_watchlists()
        
        error_message = str(exc_info.value)
        # Check that the error message mentions all configuration methods
        assert "configuration file" in error_message
        assert "environment variables" in error_message
        assert "Docker secrets" in error_message
        assert "CVI_TRAKT_CLIENT_ID" in error_message
        assert "CVI_TRAKT_CLIENT_SECRET" in error_message