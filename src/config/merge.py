"""
Centralized configuration loading and merge pipeline.

Implements ordered layering with explicit precedence:
1. Model defaults (Pydantic)
2. Configuration file (YAML)
3. Docker secrets files
4. Environment variables
5. CLI arguments (future)
6. Post-processing validation

Environment variables override secrets files for the same setting.
Provides debug logging for all overrides and configuration inspection.
"""

import logging
import os
from pathlib import Path
from typing import Any

from src.config.secrets import read_docker_secret
from src.core.models.scanning import FileStatus, ScanMode

logger = logging.getLogger(__name__)


class ConfigurationMerger:
    """Handles configuration loading and merging with explicit precedence."""

    def __init__(self, debug: bool = False):
        """Initialize the configuration merger.

        Args:
            debug: Enable debug logging for configuration overrides
        """
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)

    def merge_configurations(
        self, file_config: dict[str, Any], secrets_dir: str = "/run/secrets"
    ) -> dict[str, Any]:
        """Merge configuration from all sources with explicit precedence.

        Args:
            file_config: Configuration loaded from YAML file
            secrets_dir: Directory containing Docker secrets

        Returns:
            Merged configuration dictionary ready for Pydantic validation
        """
        # Start with file config as base
        merged_config = file_config.copy()

        # Apply secrets layer
        merged_config = self._apply_secrets_layer(merged_config, secrets_dir)

        # Apply environment variables layer (overrides secrets)
        merged_config = self._apply_environment_layer(merged_config)

        # Validate and post-process
        return self._post_process_configuration(merged_config)

    def _apply_secrets_layer(self, config: dict[str, Any], secrets_dir: str) -> dict[str, Any]:
        """Apply Docker secrets to configuration.

        Secrets are applied before environment variables, so env vars take precedence.

        Args:
            config: Current configuration dictionary
            secrets_dir: Path to Docker secrets directory

        Returns:
            Configuration with secrets applied
        """
        merged = config.copy()

        # Trakt client secret
        trakt_client_secret = read_docker_secret("trakt_client_secret", secrets_dir)
        if trakt_client_secret is not None:
            if "trakt" not in merged:
                merged["trakt"] = {}
            old_value = merged["trakt"].get("client_secret", "<not set>")
            merged["trakt"]["client_secret"] = trakt_client_secret
            self._log_override("docker_secret", "trakt.client_secret", old_value, "<secret>")

        # Trakt client ID (if provided via secret)
        trakt_client_id = read_docker_secret("trakt_client_id", secrets_dir)
        if trakt_client_id is not None:
            if "trakt" not in merged:
                merged["trakt"] = {}
            old_value = merged["trakt"].get("client_id", "<not set>")
            merged["trakt"]["client_id"] = trakt_client_id
            self._log_override("docker_secret", "trakt.client_id", old_value, "<secret>")

        return merged

    def _apply_environment_layer(self, config: dict[str, Any]) -> dict[str, Any]:
        """Apply environment variables to configuration.

        Environment variables override secrets and file configuration.
        Supports CVI_ and TRKT_ prefixes.

        Args:
            config: Current configuration dictionary

        Returns:
            Configuration with environment variables applied
        """
        merged = config.copy()

        # CVI_ prefixed environment variables
        env_mappings = {
            # Logging configuration
            "CVI_LOG_LEVEL": ("logging", "level"),
            "CVI_LOG_FILE": ("logging", "file"),
            "CVI_LOG_FORMAT": ("logging", "format"),
            "CVI_LOG_DATE_FORMAT": ("logging", "date_format"),
            # FFmpeg configuration
            "CVI_FFMPEG_COMMAND": ("ffmpeg", "command"),
            "CVI_FFMPEG_QUICK_TIMEOUT": ("ffmpeg", "quick_timeout"),
            "CVI_FFMPEG_DEEP_TIMEOUT": ("ffmpeg", "deep_timeout"),
            # Processing configuration
            "CVI_MAX_WORKERS": ("processing", "max_workers"),
            "CVI_DEFAULT_MODE": ("processing", "default_mode"),
            # Output configuration
            "CVI_OUTPUT_DIR": ("output", "default_output_dir"),
            # Scan configuration
            "CVI_RECURSIVE": ("scan", "recursive"),
            "CVI_VIDEO_DIR": ("scan", "default_input_dir"),
            "CVI_SCAN_MODE": ("scan", "mode"),
            "CVI_EXTENSIONS": ("scan", "extensions"),
            # Trakt configuration
            "TRKT_CLIENT_ID": ("trakt", "client_id"),
            "TRKT_CLIENT_SECRET": ("trakt", "client_secret"),
            "TRKT_DEFAULT_WATCHLIST": ("trakt", "default_watchlist"),
            "TRKT_INCLUDE_STATUSES": ("trakt", "include_statuses"),
        }

        for env_var, (section, key) in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                merged = self._apply_env_override(merged, section, key, env_value)

        return merged

    def _apply_env_override(
        self, config: dict[str, Any], section: str, key: str, env_value: str
    ) -> dict[str, Any]:
        """Apply a single environment variable override.

        Args:
            config: Configuration dictionary to modify
            section: Configuration section name
            key: Configuration key name
            env_value: Environment variable value

        Returns:
            Modified configuration dictionary
        """
        if section not in config:
            config[section] = {}

        old_value = config[section].get(key, "<not set>")

        # Type conversion based on key patterns and expected types
        converted_value = self._convert_env_value(key, env_value)

        config[section][key] = converted_value

        # Log the override (mask secrets)
        display_value = "<secret>" if "secret" in key.lower() else str(converted_value)
        self._log_override("environment", f"{section}.{key}", old_value, display_value)

        return config

    def _convert_env_value(self, key: str, value: str) -> Any:  # noqa: PLR0911
        """Convert environment variable string to appropriate type.

        Args:
            key: Configuration key name
            value: Environment variable string value

        Returns:
            Converted value with appropriate type
        """
        # Define conversion mapping
        conversion_map = {
            # Boolean keys
            **{
                k: lambda v: v.lower() in ("true", "1", "yes", "on")
                for k in ("recursive",)
            },
            # Path keys
            **{
                k: lambda v: Path(v) if v else None
                for k in ("command", "file", "default_output_dir", "default_input_dir")
            },
        }

        # Check if we have a direct mapping
        if key in conversion_map:
            return conversion_map[key](value)

        # Handle complex conversions that need special logic
        if key in ("max_workers", "quick_timeout", "deep_timeout"):
            # Integer conversions
            try:
                return int(value)
            except ValueError:
                logger.warning(f"Invalid integer value for {key}: {value}, using as string")
                return value
        elif key == "mode":
            # Scan mode conversion
            try:
                return ScanMode(value.lower())
            except ValueError:
                logger.warning(f"Invalid scan mode: {value}, using as string")
                return value
        elif key in ("extensions", "include_statuses"):
            # List conversions (comma-separated)
            if not value.strip():
                return []  # Explicit empty list
            if key == "include_statuses":
                statuses = []
                for status_str in value.split(","):
                    try:
                        statuses.append(FileStatus(status_str.strip().lower()))
                    except ValueError:
                        logger.warning(f"Invalid file status: {status_str}")
                return statuses
            return [ext.strip() for ext in value.split(",") if ext.strip()]
        else:
            # Default: return as string
            return value

    def _post_process_configuration(self, config: dict[str, Any]) -> dict[str, Any]:
        """Post-process configuration after all merges.

        Performs validation and cleanup that requires the complete configuration.

        Args:
            config: Merged configuration dictionary

        Returns:
            Post-processed configuration

        Raises:
            ValueError: For invalid configuration combinations
        """
        # Validate Trakt credentials - must have both or neither
        trakt_config = config.get("trakt", {})
        client_id = trakt_config.get("client_id", "")
        client_secret = trakt_config.get("client_secret", "")

        has_id = bool(client_id and client_id.strip())
        has_secret = bool(client_secret and client_secret.strip())

        if has_id != has_secret:
            missing = "client_secret" if has_id else "client_id"
            provided = "client_id" if has_id else "client_secret"
            msg = (
                f"Partial Trakt credentials detected: {provided} provided but {missing} missing. "
                "Both client_id and client_secret must be provided together, or neither."
            )
            raise ValueError(msg)

        if has_id and has_secret:
            self._log_override("post_process", "trakt.credentials", "partial", "complete")

        return config

    def _log_override(self, source: str, key: str, old_value: Any, new_value: Any) -> None:
        """Log a configuration override.

        Args:
            source: Source of the override (file, environment, docker_secret, etc.)
            key: Configuration key being overridden
            old_value: Previous value
            new_value: New value
        """
        # List of fully qualified sensitive keys to always mask
        SENSITIVE_KEYS = {
            "trakt.client_secret",
            "trakt.client_id",
            # Add more fully qualified sensitive keys here as needed
        }

        def mask_if_secret(k, v):
            # Always mask if the key is in the sensitive set, or contains secret/password
            if k.lower() in SENSITIVE_KEYS or "secret" in k.lower() or "password" in k.lower():
                return "<secret>"
            return v

        if self.debug:
            logger.debug(
                f"Config override [{source}]: {key} = {mask_if_secret(key, new_value)} (was: {mask_if_secret(key, old_value)})"
            )


def load_configuration_with_merge(
    file_config: dict[str, Any], secrets_dir: str = "/run/secrets", debug: bool = False
) -> dict[str, Any]:
    """Load and merge configuration using the centralized pipeline.

    Args:
        file_config: Configuration loaded from YAML file
        secrets_dir: Directory containing Docker secrets
        debug: Enable debug logging for configuration overrides

    Returns:
        Merged configuration dictionary ready for Pydantic validation
    """
    merger = ConfigurationMerger(debug=debug)
    return merger.merge_configurations(file_config, secrets_dir)
