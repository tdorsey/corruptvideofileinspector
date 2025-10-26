"""Unit tests for API configuration."""


import pytest

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


def test_api_config_default_values():
    """Test that APIConfig has proper default values."""
    from src.config.config import APIConfig

    config = APIConfig()
    assert config.enabled is False
    assert config.host == "0.0.0.0"
    assert config.port == 8000
    assert config.oidc_enabled is False


def test_api_config_with_values():
    """Test that APIConfig accepts custom values."""
    from src.config.config import APIConfig

    config = APIConfig(
        enabled=True,
        host="127.0.0.1",
        port=9000,
        oidc_enabled=True,
        oidc_issuer="https://auth.example.com",
        oidc_client_id="test-client",
        oidc_client_secret="test-secret",
        oidc_audience="test-audience",
    )
    assert config.enabled is True
    assert config.host == "127.0.0.1"
    assert config.port == 9000
    assert config.oidc_enabled is True
    assert config.oidc_issuer == "https://auth.example.com"


def test_app_config_includes_api_config():
    """Test that AppConfig includes api field."""
    from src.config.config import APIConfig, AppConfig

    # Create minimal valid AppConfig
    config_dict = {
        "logging": {"level": "INFO", "file": "/tmp/test.log"},
        "ffmpeg": {"command": "/usr/bin/ffmpeg"},
        "processing": {"max_workers": 4},
        "output": {"default_output_dir": "/tmp/output"},
        "scan": {"default_input_dir": "/tmp/videos"},
        "trakt": {"client_id": "", "client_secret": ""},
    }

    config = AppConfig.model_validate(config_dict)
    assert hasattr(config, "api")
    assert isinstance(config.api, APIConfig)
    assert config.api.enabled is False  # Default value


def test_api_config_from_yaml_dict():
    """Test API config parsing from YAML-like dict."""
    from src.config.config import APIConfig

    yaml_dict = {
        "enabled": True,
        "host": "0.0.0.0",
        "port": 8000,
        "oidc_enabled": True,
        "oidc_issuer": "https://auth.example.com",
        "oidc_client_id": "client-123",
        "oidc_client_secret": "secret-456",
        "oidc_audience": "api-audience",
    }

    config = APIConfig.model_validate(yaml_dict)
    assert config.enabled is True
    assert config.oidc_enabled is True
    assert config.oidc_issuer == "https://auth.example.com"
