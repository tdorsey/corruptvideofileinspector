"""
Configuration loader with support for multiple sources and precedence handling.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .settings import ENV_MAPPINGS, SECRETS_MAPPINGS, AppConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Configuration loader with precedence handling."""

    def __init__(self):
        self.config = AppConfig()
        self.loaded_sources: List[str] = []

    def load(
        self,
        config_file: Optional[Union[str, Path]] = None,
        load_env: bool = True,
        load_secrets: bool = True,
        profile: Optional[str] = None,
    ) -> AppConfig:
        """
        Load configuration from multiple sources with proper precedence.

        Precedence (highest to lowest):
        1. Environment variables
        2. Configuration file
        3. Docker secrets
        4. Defaults

        Args:
            config_file: Path to configuration file (JSON or YAML)
            load_env: Whether to load environment variables
            load_secrets: Whether to load Docker secrets
            profile: Configuration profile to use

        Returns:
            AppConfig: Loaded configuration
        """
        logger.info("Loading configuration...")

        # Set profile first if provided
        if profile:
            self.config.profile = profile
            if profile == "development":
                self.config = AppConfig.development()
            elif profile == "production":
                self.config = AppConfig.production()

        # Load from Docker secrets (lowest precedence after defaults)
        if load_secrets:
            self._load_docker_secrets()

        # Load from configuration file
        if config_file:
            self._load_config_file(config_file)

        # Load from environment variables (highest precedence)
        if load_env:
            self._load_environment_variables()

        logger.info(f"Configuration loaded from sources: {', '.join(self.loaded_sources)}")
        return self.config

    def _load_config_file(self, config_file: Union[str, Path]) -> None:
        """Load configuration from JSON or YAML file."""
        file_path = Path(config_file)

        if not file_path.exists():
            logger.warning(f"Configuration file not found: {file_path}")
            return

        try:
            with file_path.open("r", encoding="utf-8") as f:
                if file_path.suffix.lower() in [".yml", ".yaml"]:
                    try:
                        import yaml

                        data = yaml.safe_load(f)
                    except ImportError:
                        logger.exception("PyYAML not installed, cannot load YAML config")
                        return
                elif file_path.suffix.lower() == ".json":
                    data = json.load(f)
                else:
                    logger.warning(f"Unsupported config file format: {file_path.suffix}")
                    return

            if data:
                self._apply_config_dict(data)
                self.loaded_sources.append(f"file:{file_path}")
                logger.info(f"Loaded configuration from: {file_path}")

        except Exception as e:
            logger.exception(f"Failed to load configuration file {file_path}: {e}")

    def _load_environment_variables(self) -> None:
        """Load configuration from environment variables."""
        loaded_vars = []

        for env_var, config_path in ENV_MAPPINGS.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    self._set_config_value(config_path, value)
                    loaded_vars.append(env_var)
                    logger.debug(f"Set config from env var: {env_var}")
                except Exception as e:
                    logger.warning(f"Failed to set config from {env_var}: {e}")

        if loaded_vars:
            self.loaded_sources.append(f"env:{len(loaded_vars)}_vars")
            logger.info(f"Loaded {len(loaded_vars)} environment variables")

    def _load_docker_secrets(self) -> None:
        """Load configuration from Docker secrets."""
        secrets_path = Path(self.config.security.secrets_dir)

        if not secrets_path.exists():
            logger.debug(f"Docker secrets path not found: {secrets_path}")
            return

        loaded_secrets = []

        for secret_name, config_path in SECRETS_MAPPINGS.items():
            secret_file = secrets_path / secret_name
            if secret_file.exists():
                try:
                    value = secret_file.read_text().strip()
                    self._set_config_value(config_path, value)
                    loaded_secrets.append(secret_name)
                    logger.debug(f"Set config from Docker secret: {secret_name}")
                except Exception as e:
                    logger.warning(f"Failed to read secret {secret_name}: {e}")

        if loaded_secrets:
            self.loaded_sources.append(f"secrets:{len(loaded_secrets)}_files")
            logger.info(f"Loaded {len(loaded_secrets)} Docker secrets")

    def _apply_config_dict(self, data: Dict[str, Any]) -> None:
        """Apply configuration dictionary to config object."""
        for section_name, section_data in data.items():
            if not isinstance(section_data, dict):
                # Handle top-level settings
                if hasattr(self.config, section_name):
                    setattr(self.config, section_name, section_data)
                continue

            # Handle nested configuration sections
            if not hasattr(self.config, section_name):
                logger.warning(f"Unknown config section: {section_name}")
                continue

            config_section = getattr(self.config, section_name)
            for key, value in section_data.items():
                if hasattr(config_section, key):
                    setattr(config_section, key, value)
                else:
                    logger.warning(f"Unknown config key: {section_name}.{key}")

    def _set_config_value(self, config_path: tuple, value: str) -> None:
        """Set a configuration value from string with type conversion."""
        try:
            if len(config_path) == 1:
                # Top-level config attribute
                attr_name = config_path[0]
                current_value = getattr(self.config, attr_name)
                converted_value = self._convert_value(value, current_value)
                setattr(self.config, attr_name, converted_value)
            else:
                # Nested config attribute
                section_name, attr_name = config_path
                config_section = getattr(self.config, section_name)
                current_value = getattr(config_section, attr_name)
                converted_value = self._convert_value(value, current_value)
                setattr(config_section, attr_name, converted_value)

            logger.debug(f"Set config {'.'.join(config_path)} = {converted_value}")

        except Exception as e:
            logger.exception(f"Failed to set config {'.'.join(config_path)} = {value}: {e}")

    def _convert_value(self, value: str, current_value: Any) -> Any:
        """Convert string value to appropriate type based on current value."""
        if current_value is None:
            return value

        target_type = type(current_value)

        if target_type == bool:
            return value.lower() in ("true", "1", "yes", "on", "enabled")
        if target_type == int:
            return int(value)
        if target_type == float:
            return float(value)
        if target_type == list:
            # Handle comma-separated lists
            if (
                isinstance(current_value, list)
                and current_value
                and isinstance(current_value[0], str)
            ):
                return [item.strip() for item in value.split(",") if item.strip()]
            return [value]  # Single item list
        return value

    def save_config(self, file_path: Union[str, Path], format: str = "yaml") -> None:
        """Save current configuration to file."""
        file_path = Path(file_path)
        config_dict = self.config.to_dict()

        try:
            with file_path.open("w", encoding="utf-8") as f:
                if format.lower() == "yaml":
                    try:
                        import yaml

                        yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                    except ImportError:
                        logger.exception("PyYAML not installed, cannot save YAML config")
                        return
                else:  # JSON
                    json.dump(config_dict, f, indent=2)

            logger.info(f"Configuration saved to: {file_path}")

        except Exception as e:
            logger.exception(f"Failed to save configuration to {file_path}: {e}")

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Check required Trakt settings if Trakt features are used
        if not self.config.trakt.client_id:
            issues.append("Trakt client_id is required for Trakt integration")

        # Check FFmpeg command availability
        if self.config.ffmpeg.command:
            ffmpeg_path = Path(self.config.ffmpeg.command)
            if not ffmpeg_path.exists() and not self._command_exists(self.config.ffmpeg.command):
                issues.append(f"FFmpeg command not found: {self.config.ffmpeg.command}")

        # Check temp directory permissions
        try:
            temp_dir = self.config.get_temp_dir()
            temp_dir.mkdir(parents=True, exist_ok=True)
            # Try to create a test file
            test_file = temp_dir / "test_write"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            issues.append(f"Cannot write to temp directory: {e}")

        return issues

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        import shutil

        return shutil.which(command) is not None


def load_config(
    config_file: Optional[Union[str, Path]] = None,
    profile: Optional[str] = None,
    **kwargs,
) -> AppConfig:
    """
    Convenience function to load configuration.

    Args:
        config_file: Path to configuration file
        profile: Configuration profile (development, production)
        **kwargs: Additional arguments for ConfigLoader.load()

    Returns:
        AppConfig: Loaded configuration
    """
    loader = ConfigLoader()
    return loader.load(config_file=config_file, profile=profile, **kwargs)


def create_example_config(file_path: Union[str, Path], format: str = "yaml") -> None:
    """Create an example configuration file."""
    config = AppConfig()
    loader = ConfigLoader()
    loader.config = config
    loader.save_config(file_path, format)
