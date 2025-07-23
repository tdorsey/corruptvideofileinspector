"""
Unit tests for secure configuration module features
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from config import (
    SENSITIVE_KEYS,
    ConfigLoader,
    ConfigurationError,
    add_sensitive_key,
    get_all_sensitive_keys,
    get_config,
    load_config,
)


class TestConfigurationSecurity(unittest.TestCase):
    """Test security features of configuration module"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = ConfigLoader()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up any environment variables we might have set
        env_vars = [
            'APP_LOG_LEVEL', 'APP_MAX_WORKERS', 'CLIENT_ID',
            'CVI_LOG_LEVEL', 'CVI_MAX_WORKERS', 'APP_HOST', 'APP_PORT', 'APP_DEBUG'
        ]
        for var in env_vars:
            os.environ.pop(var, None)

        # Clear any custom sensitive keys added during tests
        import config
        config._additional_sensitive_keys.clear()

    def test_sensitive_keys_definition(self):
        """Test that sensitive keys are properly defined"""
        expected_keys = {'secret_key', 'api_key', 'database_password', 'client_secret'}
        assert expected_keys == SENSITIVE_KEYS

    def test_add_sensitive_key(self):
        """Test adding custom sensitive keys"""
        original_keys = get_all_sensitive_keys()

        add_sensitive_key('custom_secret')
        new_keys = get_all_sensitive_keys()

        assert 'custom_secret' in new_keys
        assert len(new_keys) == len(original_keys) + 1

    def test_docker_secrets_only_for_sensitive_values(self):
        """Test that sensitive values can only be loaded from Docker secrets"""
        # Create a temporary secrets directory
        secrets_dir = Path(self.temp_dir) / "secrets"
        secrets_dir.mkdir()

        # Create a secret file
        (secrets_dir / "secret_key").write_text("super-secret-value")

        # Update config to use our test secrets path
        self.loader.config.secrets.docker_secrets_path = str(secrets_dir)

        # Load secrets
        self.loader.load_docker_secrets()

        # Verify sensitive value was loaded
        assert self.loader.get_sensitive_value('secret_key') == "super-secret-value"

    def test_sensitive_values_rejected_from_environment(self):
        """Test that sensitive values from environment variables are rejected"""
        # Try to set a sensitive value via environment
        os.environ['APP_SECRET_KEY'] = 'should-be-rejected'

        # Load environment configuration
        self.loader.load_from_environment()

        # Verify sensitive value was NOT loaded from environment
        assert self.loader.get_sensitive_value('secret_key') is None

    def test_sensitive_values_rejected_from_yaml(self):
        """Test that sensitive values from YAML files are rejected"""
        config_data = {
            'secret_key': 'should-be-rejected',
            'logging': {'level': 'DEBUG'}
        }

        config_file = Path(self.temp_dir) / "test_config.yaml"
        with config_file.open('w') as f:
            yaml.dump(config_data, f)

        self.loader.load_from_yaml(config_file)

        # Verify sensitive value was NOT loaded from YAML
        assert self.loader.get_sensitive_value('secret_key') is None
        # But non-sensitive values should be loaded
        assert self.loader.config.logging.level == 'DEBUG'

    def test_missing_sensitive_values_validation(self):
        """Test that missing sensitive values trigger validation error"""
        # Don't provide any Docker secrets
        self.loader.config.secrets.docker_secrets_path = "/nonexistent/path"

        # Validation should fail with missing sensitive values
        with pytest.raises(ConfigurationError) as exc_info:
            self.loader.validate_configuration()

        error_message = str(exc_info.value)
        assert "Required sensitive configuration values are missing" in error_message
        assert "secret_key" in error_message
        assert "api_key" in error_message
        assert "database_password" in error_message
        assert "client_secret" in error_message

    def test_configuration_precedence_order(self):
        """Test correct configuration precedence order"""
        # 1. Set base value in YAML (lowest precedence)
        config_data = {
            'logging': {'level': 'WARNING'},
            'processing': {'max_workers': 2}
        }

        config_file = Path(self.temp_dir) / "config.yaml"
        with config_file.open('w') as f:
            yaml.dump(config_data, f)

        self.loader.load_from_yaml(config_file)

        # 2. Override with environment variable (higher precedence)
        os.environ['CVI_LOG_LEVEL'] = 'ERROR'
        self.loader.load_from_environment()

        # Environment should override YAML
        assert self.loader.config.logging.level == 'ERROR'
        # Non-overridden value should remain from YAML
        assert self.loader.config.processing.max_workers == 2

    def test_get_config_function(self):
        """Test the get_config function"""
        # Setup some test values
        secrets_dir = Path(self.temp_dir) / "secrets"
        secrets_dir.mkdir()
        (secrets_dir / "api_key").write_text("test-api-key")

        self.loader.config.secrets.docker_secrets_path = str(secrets_dir)
        self.loader.load_docker_secrets()
        self.loader._non_sensitive_values['client_id'] = 'test-client-id'

        # Store loader globally for get_config to access
        import config
        config._config_loader = self.loader

        # Test getting sensitive value
        assert get_config('api_key') == 'test-api-key'

        # Test getting non-sensitive value
        assert get_config('client_id') == 'test-client-id'

        # Test getting value with default
        assert get_config('nonexistent', 'default') == 'default'

    def test_get_config_without_loader_raises_error(self):
        """Test that get_config raises error when loader not initialized"""
        # Clear the global loader
        import config
        config._config_loader = None

        with pytest.raises(RuntimeError) as exc_info:
            get_config('some_key')

        assert "Configuration not loaded" in str(exc_info.value)

    def test_module_level_variables_populated(self):
        """Test that module-level variables are populated after load_config"""
        # Create a complete configuration with Docker secrets
        secrets_dir = Path(self.temp_dir) / "secrets"
        secrets_dir.mkdir()
        (secrets_dir / "secret_key").write_text("test-secret")
        (secrets_dir / "api_key").write_text("test-api-key")
        (secrets_dir / "database_password").write_text("test-db-pass")
        (secrets_dir / "client_secret").write_text("test-client-secret")

        # Set non-sensitive environment variables
        os.environ['CLIENT_ID'] = 'test-client-id'
        os.environ['APP_HOST'] = '0.0.0.0'
        os.environ['APP_PORT'] = '9000'
        os.environ['APP_DEBUG'] = 'true'

        # Load configuration with custom secrets path
        loader = ConfigLoader()
        loader.config.secrets.docker_secrets_path = str(secrets_dir)
        loader.load_docker_secrets()
        loader.load_from_environment()
        loader.apply_defaults()

        # Store the loader globally
        import config as config_module
        config_module._config_loader = loader
        config_module._update_module_variables()

        # Test module-level variables
        assert config_module.SECRET_KEY == "test-secret"
        assert config_module.API_KEY == "test-api-key"
        assert config_module.DATABASE_PASSWORD == "test-db-pass"
        assert config_module.CLIENT_SECRET == "test-client-secret"
        assert config_module.CLIENT_ID == "test-client-id"
        assert config_module.HOST == "0.0.0.0"
        assert config_module.PORT == 9000
        assert config_module.DEBUG is True


class TestConfigurationIntegration(unittest.TestCase):
    """Test end-to-end configuration loading scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up environment variables
        env_vars = [
            'APP_LOG_LEVEL', 'APP_HOST', 'APP_PORT', 'CLIENT_ID', 'REDIRECT_URL'
        ]
        for var in env_vars:
            os.environ.pop(var, None)

    @patch('config.ConfigLoader.validate_configuration')
    def test_load_config_with_all_sources(self, mock_validate):
        """Test loading configuration from all sources"""
        # 1. Create YAML config file
        config_data = {
            'logging': {'level': 'WARNING'},
            'processing': {'max_workers': 4},
        }

        config_file = Path(self.temp_dir) / "config.yaml"
        with config_file.open('w') as f:
            yaml.dump(config_data, f)

        # 2. Set environment variables
        os.environ['APP_LOG_LEVEL'] = 'INFO'
        os.environ['CLIENT_ID'] = 'env-client-id'

        # 3. Mock CLI arguments
        cli_args = ['--host', '192.168.1.1', '--port', '3000']

        # Load configuration
        config = load_config(config_file=config_file, cli_args=cli_args)

        # Verify precedence: CLI > Env > YAML
        # CLI args should have been applied to non-sensitive values
        # Environment should override YAML
        assert config.logging.level == 'INFO'  # From environment
        assert config.processing.max_workers == 4  # From YAML

    def test_fail_fast_on_missing_secrets(self):
        """Test that application fails fast when required secrets are missing"""
        # Don't provide any Docker secrets
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(cli_args=[])

        error_message = str(exc_info.value)
        assert "Required sensitive configuration values are missing" in error_message


if __name__ == '__main__':
    unittest.main()
