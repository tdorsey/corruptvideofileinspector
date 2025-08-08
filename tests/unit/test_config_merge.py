"""
Unit tests for configuration merge functionality.

Tests the centralized configuration loading and merge pipeline including:
- Environment variable overrides  
- Docker secrets integration
- Configuration precedence
- Type conversions
- Validation and error handling
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.merge import ConfigurationMerger, load_configuration_with_merge
from src.core.models.scanning import FileStatus, ScanMode

pytestmark = pytest.mark.unit


class TestConfigurationMerger(unittest.TestCase):
    """Test the ConfigurationMerger class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.secrets_dir = os.path.join(self.temp_dir, "secrets")
        os.makedirs(self.secrets_dir, exist_ok=True)
        
        # Base configuration for testing
        self.base_config = {
            "logging": {"level": "INFO"},
            "ffmpeg": {"command": "/usr/bin/ffmpeg", "quick_timeout": 60},
            "processing": {"max_workers": 4, "default_mode": "quick"},
            "output": {"default_json": True, "default_output_dir": "/app/output"},
            "scan": {"recursive": True, "default_input_dir": "/app/videos", "extensions": [".mp4", ".mkv"]},
            "trakt": {"client_id": "", "client_secret": ""}
        }

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_merge_configurations_basic(self):
        """Test basic configuration merging without overrides."""
        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        # Should return the base config unchanged
        self.assertEqual(result["logging"]["level"], "INFO")
        self.assertEqual(result["processing"]["max_workers"], 4)
        self.assertEqual(result["scan"]["extensions"], [".mp4", ".mkv"])

    @patch.dict(os.environ, {"CVI_LOG_LEVEL": "DEBUG", "CVI_MAX_WORKERS": "8"})
    def test_environment_variable_overrides(self):
        """Test that environment variables override configuration."""
        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        # Environment variables should override config
        self.assertEqual(result["logging"]["level"], "DEBUG")
        self.assertEqual(result["processing"]["max_workers"], 8)
        
        # Other values should remain unchanged
        self.assertEqual(result["ffmpeg"]["quick_timeout"], 60)

    @patch.dict(os.environ, {"CVI_RECURSIVE": "false", "CVI_DEFAULT_JSON": "true"})
    def test_boolean_conversions(self):
        """Test boolean environment variable conversions."""
        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        self.assertFalse(result["scan"]["recursive"])
        self.assertTrue(result["output"]["default_json"])

    @patch.dict(os.environ, {"CVI_EXTENSIONS": "mp4,avi,mkv", "CVI_OUTPUT_DIR": "/custom/output"})
    def test_list_and_path_conversions(self):
        """Test list and path environment variable conversions."""
        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        self.assertEqual(result["scan"]["extensions"], ["mp4", "avi", "mkv"])
        self.assertEqual(result["output"]["default_output_dir"], Path("/custom/output"))

    @patch.dict(os.environ, {"CVI_EXTENSIONS": ""})
    def test_empty_list_conversion(self):
        """Test that empty string creates empty list (explicit override)."""
        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        # Empty string should create empty list, not None
        self.assertEqual(result["scan"]["extensions"], [])

    @patch.dict(os.environ, {"CVI_SCAN_MODE": "deep"})
    def test_scan_mode_conversion(self):
        """Test ScanMode enum conversion."""
        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        self.assertEqual(result["scan"]["mode"], ScanMode.DEEP)

    @patch.dict(os.environ, {"TRKT_INCLUDE_STATUSES": "healthy,corrupt"})
    def test_file_status_list_conversion(self):
        """Test FileStatus enum list conversion."""
        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        expected = [FileStatus.HEALTHY, FileStatus.CORRUPT]
        self.assertEqual(result["trakt"]["include_statuses"], expected)

    def test_docker_secrets_override(self):
        """Test Docker secrets override configuration."""
        # Create secret files
        secret_file = os.path.join(self.secrets_dir, "trakt_client_secret")
        with open(secret_file, "w") as f:
            f.write("secret123")
        
        id_file = os.path.join(self.secrets_dir, "trakt_client_id")
        with open(id_file, "w") as f:
            f.write("client456")

        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        self.assertEqual(result["trakt"]["client_secret"], "secret123")
        self.assertEqual(result["trakt"]["client_id"], "client456")

    @patch.dict(os.environ, {"TRKT_CLIENT_SECRET": "env_secret", "TRKT_CLIENT_ID": "env_id"})
    def test_env_overrides_secrets(self):
        """Test that environment variables override Docker secrets."""
        # Create secret files
        secret_file = os.path.join(self.secrets_dir, "trakt_client_secret")
        with open(secret_file, "w") as f:
            f.write("file_secret")
        
        id_file = os.path.join(self.secrets_dir, "trakt_client_id")
        with open(id_file, "w") as f:
            f.write("file_id")

        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        # Environment variables should win
        self.assertEqual(result["trakt"]["client_secret"], "env_secret")
        self.assertEqual(result["trakt"]["client_id"], "env_id")

    def test_partial_trakt_credentials_failure(self):
        """Test that partial Trakt credentials cause validation failure."""
        config = self.base_config.copy()
        config["trakt"]["client_id"] = "test_id"
        # client_secret remains empty
        
        merger = ConfigurationMerger()
        
        with self.assertRaises(ValueError) as context:
            merger.merge_configurations(config, self.secrets_dir)
        
        self.assertIn("Partial Trakt credentials", str(context.exception))

    @patch.dict(os.environ, {"TRKT_CLIENT_ID": "env_id", "TRKT_CLIENT_SECRET": "env_secret"})
    def test_complete_trakt_credentials_success(self):
        """Test that complete Trakt credentials pass validation."""
        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        # Should not raise an exception
        self.assertEqual(result["trakt"]["client_id"], "env_id")
        self.assertEqual(result["trakt"]["client_secret"], "env_secret")

    def test_debug_logging_enabled(self):
        """Test that debug logging can be enabled."""
        merger = ConfigurationMerger(debug=True)
        
        # This should not raise an exception
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        self.assertIsNotNone(result)

    @patch.dict(os.environ, {"CVI_MAX_WORKERS": "invalid"})
    def test_invalid_integer_conversion(self):
        """Test handling of invalid integer values."""
        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        # Invalid integer should be kept as string and let Pydantic handle validation
        self.assertEqual(result["processing"]["max_workers"], "invalid")

    @patch.dict(os.environ, {"CVI_SCAN_MODE": "invalid_mode"})
    def test_invalid_scan_mode_conversion(self):
        """Test handling of invalid scan mode values."""
        merger = ConfigurationMerger()
        result = merger.merge_configurations(self.base_config.copy(), self.secrets_dir)
        
        # Invalid scan mode should be kept as string
        self.assertEqual(result["scan"]["mode"], "invalid_mode")

    def test_deep_merge_nested_objects(self):
        """Test that nested objects are properly merged."""
        config = {
            "logging": {"level": "INFO"},
            "ffmpeg": {"command": "/usr/bin/ffmpeg"}
        }
        
        merger = ConfigurationMerger()
        
        with patch.dict(os.environ, {"CVI_LOG_LEVEL": "DEBUG", "CVI_FFMPEG_QUICK_TIMEOUT": "30"}):
            result = merger.merge_configurations(config, self.secrets_dir)
        
        # Both original and new values should be present
        self.assertEqual(result["logging"]["level"], "DEBUG")
        self.assertEqual(result["ffmpeg"]["command"], "/usr/bin/ffmpeg")
        self.assertEqual(result["ffmpeg"]["quick_timeout"], 30)

    def test_none_vs_empty_list_handling(self):
        """Test distinction between None and empty list values."""
        config = {
            "scan": {
                "extensions": None  # None means use default
            }
        }
        
        merger = ConfigurationMerger()
        
        # No environment override - None should be preserved
        result = merger.merge_configurations(config, self.secrets_dir)
        self.assertIsNone(result["scan"]["extensions"])
        
        # Empty string environment override - should become empty list
        with patch.dict(os.environ, {"CVI_EXTENSIONS": ""}):
            result = merger.merge_configurations(config, self.secrets_dir)
            self.assertEqual(result["scan"]["extensions"], [])

    def test_load_configuration_with_merge_function(self):
        """Test the convenience function load_configuration_with_merge."""
        result = load_configuration_with_merge(self.base_config.copy(), self.secrets_dir)
        
        self.assertEqual(result["logging"]["level"], "INFO")
        self.assertEqual(result["processing"]["max_workers"], 4)

    @patch.dict(os.environ, {"CVI_LOG_LEVEL": "ERROR"})
    def test_load_configuration_with_merge_debug(self):
        """Test the convenience function with debug enabled."""
        result = load_configuration_with_merge(
            self.base_config.copy(), 
            self.secrets_dir, 
            debug=True
        )
        
        # Environment override should be applied
        self.assertEqual(result["logging"]["level"], "ERROR")


if __name__ == "__main__":
    unittest.main()