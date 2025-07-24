"""
Unit tests for configuration module
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from config import Config, ConfigLoader, load_config


class TestConfigDataClasses(unittest.TestCase):
    """Test configuration data classes"""

    def test_config_defaults(self):
        """Test default configuration values"""
        cfg = Config()

        # Test logging defaults
        assert cfg.logging.level == "INFO"
        assert "%(asctime)s" in cfg.logging.format

        # Test processing defaults
        assert cfg.processing.max_workers == 4
        assert cfg.processing.default_mode == "hybrid"

        # Test scan defaults
        assert cfg.scan.recursive
        assert cfg.scan.default_input_dir is None  # Should be None by default
        assert ".mp4" in cfg.scan.extensions
        assert ".mkv" in cfg.scan.extensions


class TestConfigLoader(unittest.TestCase):
    """Test configuration loader functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.loader = ConfigLoader()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up any environment variables we might have set
        env_vars = [
            "CVI_LOG_LEVEL",
            "CVI_MAX_WORKERS",
            "CVI_DEFAULT_MODE",
            "CVI_RECURSIVE",
            "CVI_EXTENSIONS",
            "CVI_INPUT_DIR",
            "CVI_OUTPUT_DIR",
        ]
        for var in env_vars:
            os.environ.pop(var, None)

    def test_load_from_yaml_valid(self):
        """Test loading valid YAML configuration"""
        config_data = {
            "logging": {"level": "DEBUG"},
            "processing": {"max_workers": 8},
            "scan": {"recursive": False},
        }

        config_file = Path(self.temp_dir) / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        self.loader.load_from_yaml(config_file)

        assert self.loader.config.logging.level == "DEBUG"
        assert self.loader.config.processing.max_workers == 8
        assert not self.loader.config.scan.recursive

    def test_load_from_yaml_nonexistent(self):
        """Test loading from non-existent YAML file"""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.yaml"

        # Should not raise exception, just log warning
        self.loader.load_from_yaml(nonexistent_file)

        # Config should remain at defaults
        assert self.loader.config.logging.level == "INFO"

    def test_load_from_yaml_invalid(self):
        """Test loading invalid YAML file"""
        config_file = Path(self.temp_dir) / "invalid.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [\n")

        with pytest.raises(yaml.YAMLError):
            self.loader.load_from_yaml(config_file)

    def test_load_from_environment(self):
        """Test loading configuration from environment variables"""
        os.environ["CVI_LOG_LEVEL"] = "ERROR"
        os.environ["CVI_MAX_WORKERS"] = "12"
        os.environ["CVI_DEFAULT_MODE"] = "quick"
        os.environ["CVI_RECURSIVE"] = "false"
        os.environ["CVI_EXTENSIONS"] = ".mp4,.avi,.mkv"

        self.loader.load_from_environment()

        assert self.loader.config.logging.level == "ERROR"
        assert self.loader.config.processing.max_workers == 12
        assert self.loader.config.processing.default_mode == "quick"
        assert not self.loader.config.scan.recursive
        assert self.loader.config.scan.extensions == [".mp4", ".avi", ".mkv"]

    def test_type_conversion(self):
        """Test automatic type conversion"""
        # Test boolean conversion
        self.loader._set_config_value("scan", "recursive", "true")
        assert self.loader.config.scan.recursive

        self.loader._set_config_value("scan", "recursive", "false")
        assert not self.loader.config.scan.recursive

        # Test integer conversion
        self.loader._set_config_value("processing", "max_workers", "16")
        assert self.loader.config.processing.max_workers == 16

        # Test list conversion
        self.loader._set_config_value("scan", "extensions", ".mp4,.mkv,.avi")
        assert self.loader.config.scan.extensions == [".mp4", ".mkv", ".avi"]

    def test_unknown_config_section(self):
        """Test handling of unknown configuration section"""
        # Should log warning but not crash
        self.loader._set_config_value("unknown_section", "key", "value")

        # Config should remain unchanged
        assert self.loader.config.logging.level == "INFO"

    def test_unknown_config_key(self):
        """Test handling of unknown configuration key"""
        # Should log warning but not crash
        self.loader._set_config_value("logging", "unknown_key", "value")

        # Config should remain unchanged for known keys
        assert self.loader.config.logging.level == "INFO"

    @patch("pathlib.Path.exists")
    def test_load_docker_secrets_missing_path(self, mock_exists):
        """Test Docker secrets loading when path doesn't exist"""
        mock_exists.return_value = False

        # Should not raise exception
        self.loader.load_docker_secrets()

        # Config should remain at defaults
        assert self.loader.config.logging.level == "INFO"

    def test_load_docker_secrets_with_files(self):
        """Test Docker secrets loading with actual files"""
        secrets_dir = Path(self.temp_dir) / "secrets"
        secrets_dir.mkdir()

        # Create secret files
        (secrets_dir / "cvi_log_level").write_text("WARNING")
        (secrets_dir / "cvi_max_workers").write_text("6")

        # Update config to use our test secrets path
        self.loader.config.secrets.docker_secrets_path = str(secrets_dir)

        self.loader.load_docker_secrets()

        assert self.loader.config.logging.level == "WARNING"
        assert self.loader.config.processing.max_workers == 6


class TestLoadConfig(unittest.TestCase):
    """Test the main load_config function"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up environment variables
        env_vars = ["CVI_LOG_LEVEL", "CVI_MAX_WORKERS", "CVI_DEFAULT_MODE"]
        for var in env_vars:
            os.environ.pop(var, None)

    def test_load_config_with_file(self):
        """Test loading configuration with specific file"""
        config_data = {
            "logging": {"level": "WARNING"},
            "processing": {"max_workers": 10},
        }

        config_file = Path(self.temp_dir) / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        cfg = load_config(config_file)

        assert cfg.logging.level == "WARNING"
        assert cfg.processing.max_workers == 10

    def test_load_config_precedence(self):
        """Test configuration precedence: env vars > config file"""
        # Create config file
        config_data = {
            "logging": {"level": "WARNING"},
            "processing": {"max_workers": 10},
        }

        config_file = Path(self.temp_dir) / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Set environment variable (should override)
        os.environ["CVI_LOG_LEVEL"] = "ERROR"

        cfg = load_config(config_file)

        # Environment variable should override config file
        assert cfg.logging.level == "ERROR"
        # Config file value should still be used for non-overridden values
        assert cfg.processing.max_workers == 10

    def test_load_config_defaults_only(self):
        """Test loading configuration with defaults only"""
        cfg = load_config()

        # Should have default values
        assert cfg.logging.level == "INFO"
        assert cfg.processing.max_workers == 4
        assert cfg.processing.default_mode == "hybrid"
        assert cfg.scan.default_input_dir is None  # Should be None by default


class TestInputOutputDirectoryConfiguration(unittest.TestCase):
    """Test input and output directory configuration functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.loader = ConfigLoader()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up any environment variables we might have set
        env_vars = ["CVI_INPUT_DIR", "CVI_OUTPUT_DIR"]
        for var in env_vars:
            os.environ.pop(var, None)

    def test_input_output_directory_configuration(self):
        """Test input and output directory configuration via YAML and environment"""
        # Test YAML configuration
        config_data = {
            "scan": {"default_input_dir": "/test/input/directory", "recursive": True},
            "output": {
                "default_output_dir": "/test/output/directory",
                "default_filename": "custom_results.json",
            },
        }

        config_file = Path(self.temp_dir) / "test_dirs.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        self.loader.load_from_yaml(config_file)

        # Verify YAML values are loaded
        assert self.loader.config.scan.default_input_dir == "/test/input/directory"
        assert self.loader.config.output.default_output_dir == "/test/output/directory"
        assert self.loader.config.output.default_filename == "custom_results.json"

        # Test environment variable override
        os.environ["CVI_INPUT_DIR"] = "/env/input/override"
        os.environ["CVI_OUTPUT_DIR"] = "/env/output/override"

        self.loader.load_from_environment()

        # Environment should override YAML
        assert self.loader.config.scan.default_input_dir == "/env/input/override"
        assert self.loader.config.output.default_output_dir == "/env/output/override"
        # Non-overridden value should remain from YAML
        assert self.loader.config.output.default_filename == "custom_results.json"


class TestNonSecretConfigValues(unittest.TestCase):
    """Test non-secret configuration values"""

    def setUp(self):
        """Set up test fixtures"""
        self.loader = ConfigLoader()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up any environment variables we might have set
        env_vars = ["CVI_INPUT_DIR", "CVI_OUTPUT_DIR", "CVI_TRAKT_CLIENT_ID"]
        for var in env_vars:
            os.environ.pop(var, None)

    def test_trakt_client_id(self):
        """Test Trakt client ID configuration value"""
        # Test YAML configuration
        config_data = {"trakt_client_id": "test_client_id"}

        config_file = Path(self.temp_dir) / "test_trakt.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        self.loader.load_from_yaml(config_file)

        # Verify YAML value is loaded
        assert self.loader.config.trakt_client_id == "test_client_id"

        # Test environment variable override
        os.environ["CVI_TRAKT_CLIENT_ID"] = "env_client_id"

        self.loader.load_from_environment()

        # Environment should override YAML
        assert self.loader.config.trakt_client_id == "env_client_id"
