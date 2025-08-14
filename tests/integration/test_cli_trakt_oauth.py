"""Tests for Trakt OAuth authentication functionality."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner

from src.cli.commands import auth as trakt_auth_command

pytestmark = pytest.mark.integration


class TestTraktOAuthAuthentication(unittest.TestCase):
    """Test Trakt OAuth authentication functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

        # Create a temporary config file
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "config.yaml"

        # Create a test config
        test_config = {
            "trakt": {"client_id": "test_client_id", "client_secret": "test_client_secret"},
            "logging": {"level": "WARNING"},
            "ffmpeg": {"command": "/usr/bin/ffmpeg"},
            "processing": {"max_workers": 8},
            "output": {"default_output_dir": "/tmp/output"},
            "scan": {"default_input_dir": "/tmp/input"},
        }

        with open(self.config_file, "w") as f:
            yaml.dump(test_config, f)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("importlib.util.find_spec")
    def test_auth_missing_pytrakt_library(self, mock_find_spec):
        """Test handling of missing PyTrakt library."""
        # Mock PyTrakt library not available
        mock_find_spec.return_value = None

        result = self.runner.invoke(
            trakt_auth_command, ["--test-only", "--config", str(self.config_file)]
        )

        assert result.exit_code == 1
        assert "PyTrakt library not found" in result.output
        assert "pip install trakt>=3.4.0" in result.output

    @patch("importlib.util.find_spec")
    def test_auth_missing_client_credentials(self, mock_find_spec):
        """Test handling of missing client credentials."""
        # Mock PyTrakt library availability
        mock_find_spec.return_value = MagicMock()

        # Create config without credentials
        no_creds_config = {
            "logging": {"level": "WARNING"},
            "ffmpeg": {"command": "/usr/bin/ffmpeg"},
            "processing": {"max_workers": 8},
            "output": {"default_output_dir": "/tmp/output"},
            "scan": {"default_input_dir": "/tmp/input"},
            "trakt": {"client_id": "", "client_secret": ""},
        }

        no_creds_file = self.temp_dir / "no_creds_config.yaml"
        with open(no_creds_file, "w") as f:
            yaml.dump(no_creds_config, f)

        result = self.runner.invoke(
            trakt_auth_command, ["--test-only", "--config", str(no_creds_file)]
        )

        assert result.exit_code == 1
        assert "Trakt client credentials not found" in result.output
        assert "https://trakt.tv/oauth/applications" in result.output

    @patch("sys.modules")
    @patch("importlib.util.find_spec")
    def test_auth_config_loading_and_display(self, mock_find_spec, mock_sys_modules):
        """Test that auth command loads config and displays correct information."""
        # Mock PyTrakt library availability
        mock_find_spec.return_value = MagicMock()

        # Mock the trakt module to prevent import errors
        mock_trakt = MagicMock()
        mock_sys_modules.__getitem__.side_effect = lambda x: (
            mock_trakt if "trakt" in x else sys.modules.get(x)
        )

        result = self.runner.invoke(
            trakt_auth_command, ["--test-only", "--config", str(self.config_file)]
        )

        # Should show the setup header and client credentials found
        assert "Trakt.tv OAuth Authentication Setup" in result.output
        assert "Client credentials found" in result.output
        assert "Client ID: test_cli..." in result.output


if __name__ == "__main__":
    unittest.main()
