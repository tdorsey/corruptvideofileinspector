"""
Configuration management for Corrupt Video Inspector.

Supports configuration loading from environment variables,
and Docker secrets with proper precedence handling.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file: Optional[str] = None


@dataclass
class FFmpegConfig:
    """FFmpeg-related configuration settings."""

    command: Optional[str] = None  # Auto-detect if not specified
    quick_timeout: int = 60  # 1 minute for quick scans
    deep_timeout: int = 900  # 15 minutes for deep scans


@dataclass
class ProcessingConfig:
    """Processing configuration settings."""

    max_workers: int = 4
    default_mode: str = "hybrid"  # quick, deep, hybrid


@dataclass
class OutputConfig:
    """Output configuration settings."""

    default_json: bool = False
    default_output_dir: Optional[str] = None
    default_filename: str = "scan_results.json"


@dataclass
class ScanConfig:
    """File scanning configuration settings."""

    recursive: bool = True
    default_input_dir: Optional[str] = None  # Default directory to scan
    extensions: List[str] = field(
        default_factory=lambda: [
            ".mp4",
            ".avi",
            ".mkv",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".m4v",
            ".mpg",
            ".mpeg",
        ]
    )


@dataclass
class SecretsConfig:
    """Secrets configuration for Docker and external services."""

    docker_secrets_path: str = "/run/secrets"
    # Future: API keys, database connections, etc.


@dataclass
class TraktConfig:
    """Trakt.tv configuration settings."""

    client_id: str


@dataclass
class Config:
    """Main configuration container."""

    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ffmpeg: FFmpegConfig = field(default_factory=FFmpegConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    scan: ScanConfig = field(default_factory=ScanConfig)
    secrets: SecretsConfig = field(default_factory=SecretsConfig)
    trakt: TraktConfig = field(default_factory=TraktConfig)


class ConfigLoader:
    """Configuration loader with precedence handling."""

    def __init__(self):
        self.config = Config()
        self._loaded_files: List[str] = []

    def load_from_environment(self) -> None:
        """Load configuration overrides from environment variables."""
        env_mappings = {
            # Logging
            "CVI_LOG_LEVEL": ("logging", "level"),
            "CVI_LOG_FORMAT": ("logging", "format"),
            "CVI_LOG_FILE": ("logging", "file"),
            # FFmpeg
            "CVI_FFMPEG_COMMAND": ("ffmpeg", "command"),
            "CVI_FFMPEG_QUICK_TIMEOUT": ("ffmpeg", "quick_timeout"),
            "CVI_FFMPEG_DEEP_TIMEOUT": ("ffmpeg", "deep_timeout"),
            # Processing
            "CVI_MAX_WORKERS": ("processing", "max_workers"),
            "CVI_DEFAULT_MODE": ("processing", "default_mode"),
            # Output
            "CVI_DEFAULT_JSON": ("output", "default_json"),
            "CVI_OUTPUT_DIR": ("output", "default_output_dir"),
            "CVI_OUTPUT_FILENAME": ("output", "default_filename"),
            # Scan
            "CVI_RECURSIVE": ("scan", "recursive"),
            "CVI_INPUT_DIR": ("scan", "default_input_dir"),
            "CVI_EXTENSIONS": ("scan", "extensions"),
            # Trakt
            "TRAKT_CLIENT_ID": ("trakt", "client_id"),
            # Secrets
            "CVI_SECRETS_PATH": ("secrets", "docker_secrets_path"),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_config_value(section, key, value)
                logger.debug(f"Set {section}.{key} from environment: {env_var}")

    def load_docker_secrets(self) -> None:
        """Load configuration from Docker secrets."""
        secrets_path = Path(self.config.secrets.docker_secrets_path)

        if not secrets_path.exists():
            logger.debug(f"Docker secrets path not found: {secrets_path}")
            return

        # Docker secrets mapping
        secret_mappings = {
            "cvi_log_level": ("logging", "level"),
            "cvi_ffmpeg_command": ("ffmpeg", "command"),
            "cvi_max_workers": ("processing", "max_workers"),
            "cvi_input_dir": ("scan", "default_input_dir"),
            "cvi_output_dir": ("output", "default_output_dir"),
            # Add more secrets as needed
        }

        for secret_name, (section, key) in secret_mappings.items():
            secret_file = secrets_path / secret_name
            if secret_file.exists():
                try:
                    value = secret_file.read_text().strip()
                    self._set_config_value(section, key, value)
                    logger.debug(
                        f"Set {section}.{key} from Docker secret: " f"{secret_name}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to read secret {secret_name}: {e}")

    def _apply_config_dict(self, data: Dict) -> None:
        """Apply configuration dictionary to config object."""
        for section_name, section_data in data.items():
            if not isinstance(section_data, dict):
                logger.warning(f"Invalid config section: {section_name}")
                continue

            for key, value in section_data.items():
                self._set_config_value(section_name, key, value)

    def _set_config_value(self, section: str, key: str, value: object) -> None:
        """Set a configuration value with type conversion."""
        try:
            config_section = getattr(self.config, section, None)
            if config_section is None:
                logger.warning(f"Unknown config section: {section}")
                return

            if not hasattr(config_section, key):
                logger.warning(f"Unknown config key: {section}.{key}")
                return

            # Get the current value to determine the expected type
            current_value = getattr(config_section, key)

            # If value is already the correct type (from YAML), use it directly
            if isinstance(value, type(current_value)) or current_value is None:
                converted_value = value
            # Convert string values to appropriate type (from env vars)
            elif isinstance(value, str):
                if isinstance(current_value, bool):
                    valid_true = ("true", "1", "yes", "on")
                    valid_false = ("false", "0", "no", "off")
                    if value.lower() in valid_true:
                        converted_value = True
                    elif value.lower() in valid_false:
                        converted_value = False
                    else:
                        raise ValueError(f"Invalid boolean value: {value}")

                elif isinstance(current_value, int):
                    converted_value = int(value)
                elif isinstance(current_value, list):
                    # Handle comma-separated lists
                    converted_value = [
                        item.strip() for item in value.split(",") if item.strip()
                    ]
                else:
                    converted_value = value
            else:
                converted_value = value

            setattr(config_section, key, converted_value)
            logger.debug(f"Set {section}.{key} = {converted_value}")

        except (ValueError, AttributeError):
            logger.exception(f"Failed to set {section}.{key} = {value}")

    def get_loaded_files(self) -> List[str]:
        """Get list of successfully loaded configuration files."""
        return self._loaded_files.copy()


def load_config(config_file: Optional[Union[str, Path]] = None) -> Config:
    """
    Load configuration with proper precedence handling.

    Precedence (highest to lowest):
    1. Environment variables
    2. Docker secrets (if available)
    3. Built-in defaults

    Returns:
        Config: Loaded configuration object
    """
    loader = ConfigLoader()

    # Load Docker secrets (higher precedence)
    loader.load_docker_secrets()

    # Load environment variables (highest precedence)
    loader.load_from_environment()

    logger.info(f"Configuration loaded from: {loader.get_loaded_files()}")
    return loader.config
