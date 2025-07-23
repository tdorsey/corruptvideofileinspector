"""
Configuration management for Corrupt Video Inspector.

Supports secure configuration loading with strict security boundaries for sensitive data.
Sensitive values (API keys, passwords, tokens) MUST only be loaded from Docker secrets.

Configuration Precedence (lowest to highest):
1. Configuration File - Base configuration from YAML files
2. CLI Flags - Command line arguments
3. Docker Secrets - Sensitive values ONLY (at /run/secrets/)
4. Environment Variables - Non-sensitive configuration overrides
5. Defaults - Final fallback for non-sensitive values only
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import yaml

# Configure module logger
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration values are missing or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# Sensitive keys that MUST only be loaded from Docker secrets
SENSITIVE_KEYS: Set[str] = {
    'secret_key',
    'api_key',
    'database_password',
    'client_secret'
}

# Additional sensitive keys can be added at runtime
_additional_sensitive_keys: Set[str] = set()


def add_sensitive_key(key: str) -> None:
    """
    Add a custom sensitive key that must be loaded from Docker secrets only.
    
    Args:
        key: Configuration key name to treat as sensitive
    """
    _additional_sensitive_keys.add(key)
    logger.debug(f"Added sensitive key: {key}")


def get_all_sensitive_keys() -> Set[str]:
    """Get all sensitive keys including custom ones."""
    return SENSITIVE_KEYS | _additional_sensitive_keys


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
    extensions: List[str] = field(default_factory=lambda: [
        ".mp4", ".avi", ".mkv", ".mov", ".wmv",
        ".flv", ".webm", ".m4v", ".mpg", ".mpeg"
    ])


@dataclass
class SecretsConfig:
    """Secrets configuration for Docker and external services."""
    docker_secrets_path: str = "/run/secrets"


@dataclass
class Config:
    """Main configuration container."""
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ffmpeg: FFmpegConfig = field(default_factory=FFmpegConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    scan: ScanConfig = field(default_factory=ScanConfig)
    secrets: SecretsConfig = field(default_factory=SecretsConfig)


class ConfigLoader:
    """Configuration loader with strict security and precedence handling."""

    def __init__(self) -> None:
        self.config = Config()
        self._loaded_files: List[str] = []
        self._sensitive_values: Dict[str, str] = {}
        self._non_sensitive_values: Dict[str, Any] = {}

    def load_from_yaml(self, config_path: Union[str, Path]) -> None:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        config_path = Path(config_path)

        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return

        try:
            with config_path.open(encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                logger.warning(f"Empty configuration file: {config_path}")
                return

            self._apply_config_dict(data, source="YAML file")
            self._loaded_files.append(str(config_path))
            logger.info(f"Loaded configuration from: {config_path}")

        except yaml.YAMLError:
            logger.exception(f"Failed to parse YAML config {config_path}")
            raise
        except Exception:
            logger.exception(f"Failed to load config {config_path}")
            raise

    def load_from_cli_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Load configuration from CLI arguments.
        
        Args:
            args: Optional list of arguments to parse (defaults to sys.argv)
            
        Returns:
            Parsed command line arguments namespace
        """
        parser = argparse.ArgumentParser(description="Corrupt Video Inspector")

        # Configuration file
        parser.add_argument(
            '--config-file',
            type=str,
            help='Path to YAML configuration file'
        )

        # Non-sensitive operational settings
        parser.add_argument('--debug', action='store_true', help='Enable debug mode')
        parser.add_argument('--host', type=str, help='Host to bind to')
        parser.add_argument('--port', type=int, help='Port to bind to')
        parser.add_argument('--log-level', type=str, help='Logging level')
        parser.add_argument('--max-workers', type=int, help='Maximum worker threads')
        parser.add_argument('--mode', type=str, help='Processing mode')

        # OAuth settings (client_id is public, client_secret is sensitive)
        parser.add_argument('--client-id', type=str, help='OAuth client ID (public)')
        parser.add_argument('--redirect-url', type=str, help='OAuth redirect URL')

        # Only parse CLI args if we're not in a test environment
        if args is None and 'pytest' in sys.modules:
            # Return empty args in test environment to avoid conflicts
            parsed_args = argparse.Namespace()
            for action in parser._actions:
                if action.dest != 'help':
                    setattr(parsed_args, action.dest, action.default)
        else:
            parsed_args = parser.parse_args(args)

        # Apply CLI args to configuration (non-sensitive only)
        cli_config = {}
        if getattr(parsed_args, 'debug', False):
            cli_config.setdefault('logging', {})['level'] = 'DEBUG'
        if getattr(parsed_args, 'host', None):
            cli_config['host'] = parsed_args.host
        if getattr(parsed_args, 'port', None):
            cli_config['port'] = parsed_args.port
        if getattr(parsed_args, 'log_level', None):
            cli_config.setdefault('logging', {})['level'] = parsed_args.log_level
        if getattr(parsed_args, 'max_workers', None):
            cli_config.setdefault('processing', {})['max_workers'] = parsed_args.max_workers
        if getattr(parsed_args, 'mode', None):
            cli_config.setdefault('processing', {})['default_mode'] = parsed_args.mode
        if getattr(parsed_args, 'client_id', None):
            cli_config['client_id'] = parsed_args.client_id
        if getattr(parsed_args, 'redirect_url', None):
            cli_config['redirect_url'] = parsed_args.redirect_url

        if cli_config:
            self._apply_config_dict(cli_config, source="CLI arguments")

        return parsed_args

    def load_docker_secrets(self) -> None:
        """Load sensitive configuration from Docker secrets ONLY."""
        secrets_path = Path(self.config.secrets.docker_secrets_path)

        if not secrets_path.exists():
            logger.debug(f"Docker secrets path not found: {secrets_path}")
            logger.warning("No sensitive values loaded - ensure Docker secrets are properly mounted")
            return

        logger.debug(f"Loading Docker secrets from: {secrets_path}")

        # Legacy mapping for backward compatibility with tests
        legacy_secret_mappings = {
            'cvi_log_level': ('logging', 'level'),
            'cvi_ffmpeg_command': ('ffmpeg', 'command'),
            'cvi_max_workers': ('processing', 'max_workers'),
            'cvi_input_dir': ('scan', 'default_input_dir'),
            'cvi_output_dir': ('output', 'default_output_dir'),
        }

        # Load ALL files from secrets directory as potential sensitive values
        for secret_file in secrets_path.iterdir():
            if secret_file.is_file():
                try:
                    value = secret_file.read_text().strip()
                    if value:  # Only store non-empty values
                        secret_name = secret_file.name
                        self._sensitive_values[secret_name] = value
                        logger.debug(f"Loaded Docker secret: {secret_name}")

                        # Also apply legacy mappings for backward compatibility
                        if secret_name in legacy_secret_mappings:
                            section, key = legacy_secret_mappings[secret_name]
                            self._set_config_value(section, key, value, source="Docker secrets")
                    else:
                        logger.warning(f"Empty Docker secret file: {secret_name}")
                except Exception as e:
                    logger.warning(f"Failed to read secret {secret_file.name}: {e}")


    def load_from_environment(self) -> None:
        """Load non-sensitive configuration overrides from environment variables."""
        env_mappings = {
            # New APP_ prefix
            'APP_LOG_LEVEL': ('logging', 'level'),
            'APP_LOG_FORMAT': ('logging', 'format'),
            'APP_LOG_FILE': ('logging', 'file'),
            'APP_DEBUG': 'debug',
            'APP_HOST': 'host',
            'APP_PORT': 'port',
            'APP_FFMPEG_COMMAND': ('ffmpeg', 'command'),
            'APP_FFMPEG_QUICK_TIMEOUT': ('ffmpeg', 'quick_timeout'),
            'APP_FFMPEG_DEEP_TIMEOUT': ('ffmpeg', 'deep_timeout'),
            'APP_MAX_WORKERS': ('processing', 'max_workers'),
            'APP_DEFAULT_MODE': ('processing', 'default_mode'),
            'APP_DEFAULT_JSON': ('output', 'default_json'),
            'APP_OUTPUT_DIR': ('output', 'default_output_dir'),
            'APP_OUTPUT_FILENAME': ('output', 'default_filename'),
            'APP_RECURSIVE': ('scan', 'recursive'),
            'APP_INPUT_DIR': ('scan', 'default_input_dir'),
            'APP_EXTENSIONS': ('scan', 'extensions'),
            'CLIENT_ID': 'client_id',
            'REDIRECT_URL': 'redirect_url',

            # Legacy CVI_ prefix for backward compatibility
            'CVI_LOG_LEVEL': ('logging', 'level'),
            'CVI_LOG_FORMAT': ('logging', 'format'),
            'CVI_LOG_FILE': ('logging', 'file'),
            'CVI_FFMPEG_COMMAND': ('ffmpeg', 'command'),
            'CVI_FFMPEG_QUICK_TIMEOUT': ('ffmpeg', 'quick_timeout'),
            'CVI_FFMPEG_DEEP_TIMEOUT': ('ffmpeg', 'deep_timeout'),
            'CVI_MAX_WORKERS': ('processing', 'max_workers'),
            'CVI_DEFAULT_MODE': ('processing', 'default_mode'),
            'CVI_DEFAULT_JSON': ('output', 'default_json'),
            'CVI_OUTPUT_DIR': ('output', 'default_output_dir'),
            'CVI_OUTPUT_FILENAME': ('output', 'default_filename'),
            'CVI_RECURSIVE': ('scan', 'recursive'),
            'CVI_INPUT_DIR': ('scan', 'default_input_dir'),
            'CVI_EXTENSIONS': ('scan', 'extensions'),
            'CVI_SECRETS_PATH': ('secrets', 'docker_secrets_path'),
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if isinstance(config_path, tuple):
                    section, key = config_path
                    self._set_config_value(section, key, value, source="environment variable")
                else:
                    # Store flat configuration values
                    self._non_sensitive_values[config_path] = self._convert_type(value)
                logger.debug(f"Set configuration from environment: {env_var}")


    def apply_defaults(self) -> None:
        """Apply default values for non-sensitive configuration."""
        # Default values for non-sensitive configuration
        defaults = {
            'debug': False,
            'host': '127.0.0.1',
            'port': 8000,
            'client_id': None,  # Should be set via other sources
            'redirect_url': None,  # Should be set via other sources
        }

        for key, default_value in defaults.items():
            if key not in self._non_sensitive_values and default_value is not None:
                self._non_sensitive_values[key] = default_value
                logger.debug(f"Applied default value for {key}: {default_value}")

    def validate_configuration(self) -> None:
        """
        Validate that all required sensitive values are present.
        
        Raises:
            ConfigurationError: If any required sensitive values are missing
        """
        all_sensitive_keys = get_all_sensitive_keys()
        missing_keys = []

        for key in all_sensitive_keys:
            if key not in self._sensitive_values:
                missing_keys.append(key)

        if missing_keys:
            missing_str = ", ".join(missing_keys)
            raise ConfigurationError(
                f"Required sensitive configuration values are missing or empty: {missing_str}. "
                f"These must be provided via Docker secrets at {self.config.secrets.docker_secrets_path}"
            )

    def _apply_config_dict(self, data: Dict[str, Any], source: str) -> None:
        """Apply configuration dictionary to config object."""
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    self._set_config_value(section_name, key, value, source)
            else:
                # Handle flat configuration
                self._non_sensitive_values[section_name] = self._convert_type(section_data)

    def _set_config_value(self, section: str, key: str, value: Any, source: str) -> None:
        """Set a configuration value with type conversion and security validation."""
        try:
            config_section = getattr(self.config, section, None)
            if config_section is None:
                logger.warning(f"Unknown config section: {section}")
                return

            if not hasattr(config_section, key):
                logger.warning(f"Unknown config key: {section}.{key}")
                return

            # Security check: reject sensitive values from non-Docker sources
            if key in get_all_sensitive_keys() and source != "Docker secrets":
                logger.warning(
                    f"Sensitive key '{key}' cannot be set via {source}. "
                    "Sensitive values must only be provided via Docker secrets."
                )
                return

            converted_value = self._convert_type(value, getattr(config_section, key))
            setattr(config_section, key, converted_value)
            logger.debug(f"Set {section}.{key} from {source}")

        except (ValueError, AttributeError):
            logger.exception(f"Failed to set {section}.{key} = {value}")

    def _convert_type(self, value: Any, current_value: Any = None) -> Any:
        """Convert string values to appropriate type."""
        if current_value is None or not isinstance(value, str):
            return value

        if isinstance(current_value, bool):
            return value.lower() in ('true', '1', 'yes', 'on')
        if isinstance(current_value, int):
            return int(value)
        if isinstance(current_value, list):
            # Handle comma-separated lists
            return [item.strip() for item in value.split(',') if item.strip()]
        return value

    def get_loaded_files(self) -> List[str]:
        """Get list of successfully loaded configuration files."""
        return self._loaded_files.copy()

    def get_sensitive_value(self, key: str) -> Optional[str]:
        """Get a sensitive value (Docker secrets only)."""
        return self._sensitive_values.get(key)

    def get_non_sensitive_value(self, key: str, default: Any = None) -> Any:
        """Get a non-sensitive configuration value."""
        return self._non_sensitive_values.get(key, default)


# Module-level configuration loader
_config_loader: Optional[ConfigLoader] = None


def load_config(
    config_file: Optional[Union[str, Path]] = None,
    cli_args: Optional[List[str]] = None,
    validate_secrets: bool = True
) -> Config:
    """
    Load configuration with proper precedence handling and security validation.
    
    Precedence (lowest to highest):
    1. Configuration File - Base configuration from YAML files
    2. CLI Flags - Command line arguments  
    3. Docker Secrets - Sensitive values ONLY (at /run/secrets/)
    4. Environment Variables - Non-sensitive configuration overrides
    5. Defaults - Final fallback for non-sensitive values only
    
    Args:
        config_file: Optional path to specific configuration file
        cli_args: Optional CLI arguments to parse
        validate_secrets: Whether to validate that all required secrets are present
        
    Returns:
        Config: Loaded configuration object
        
    Raises:
        ConfigurationError: If required sensitive values are missing and validate_secrets=True
    """
    global _config_loader

    loader = ConfigLoader()

    # 1. Load from configuration file (lowest precedence)
    if config_file is not None:
        loader.load_from_yaml(config_file)

    # 2. Load from CLI arguments
    parsed_args = loader.load_from_cli_args(cli_args)
    if hasattr(parsed_args, 'config_file') and parsed_args.config_file and config_file is None:
        loader.load_from_yaml(parsed_args.config_file)

    # 3. Load Docker secrets (sensitive values only)
    loader.load_docker_secrets()

    # 4. Load environment variables (highest precedence for non-sensitive)
    loader.load_from_environment()

    # 5. Apply defaults for missing non-sensitive values
    loader.apply_defaults()

    # Validate that all required sensitive values are present (if requested)
    if validate_secrets:
        loader.validate_configuration()

    logger.info(f"Configuration loaded from: {loader.get_loaded_files()}")

    # Store loader for module-level access
    _config_loader = loader

    # Update module-level variables
    _update_module_variables()

    return loader.config


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value by key.
    
    Args:
        key: Configuration key name
        default: Default value if key is not found
        
    Returns:
        Configuration value or default
        
    Raises:
        RuntimeError: If configuration has not been loaded
    """
    if _config_loader is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")

    # Check sensitive values first
    if key in get_all_sensitive_keys():
        value = _config_loader.get_sensitive_value(key)
        if value is None and default is None:
            raise ConfigurationError(f"Required sensitive value '{key}' not found in Docker secrets")
        return value or default

    # Check non-sensitive values
    return _config_loader.get_non_sensitive_value(key, default)


# Module-level variables for direct access (lazy-loaded)
def _get_sensitive_value(key: str) -> Optional[str]:
    """Get a sensitive value, ensuring it exists."""
    try:
        value = get_config(key)
        return value
    except (RuntimeError, ConfigurationError):
        return None


def _get_non_sensitive_value(key: str, default: Any = None) -> Any:
    """Get a non-sensitive value safely."""
    try:
        return get_config(key, default)
    except RuntimeError:
        return default


# Module-level variables - these are dynamically populated
SECRET_KEY: Optional[str] = None
API_KEY: Optional[str] = None
DATABASE_PASSWORD: Optional[str] = None
CLIENT_SECRET: Optional[str] = None
CLIENT_ID: Optional[str] = None
REDIRECT_URL: Optional[str] = None
HOST: str = "127.0.0.1"
PORT: int = 8000
DEBUG: bool = False


def _update_module_variables() -> None:
    """Update module-level variables after configuration is loaded."""
    global SECRET_KEY, API_KEY, DATABASE_PASSWORD, CLIENT_SECRET
    global CLIENT_ID, REDIRECT_URL, HOST, PORT, DEBUG

    if _config_loader is None:
        return

    # Update sensitive values (will be None if not provided via Docker secrets)
    SECRET_KEY = _get_sensitive_value('secret_key')
    API_KEY = _get_sensitive_value('api_key')
    DATABASE_PASSWORD = _get_sensitive_value('database_password')
    CLIENT_SECRET = _get_sensitive_value('client_secret')

    # Update non-sensitive values with proper type conversion
    CLIENT_ID = _get_non_sensitive_value('client_id')
    REDIRECT_URL = _get_non_sensitive_value('redirect_url')
    HOST = _get_non_sensitive_value('host', '127.0.0.1')

    # Convert PORT to int
    port_value = _get_non_sensitive_value('port', 8000)
    PORT = int(port_value) if isinstance(port_value, str) else port_value

    # Convert DEBUG to bool
    debug_value = _get_non_sensitive_value('debug', False)
    if isinstance(debug_value, str):
        DEBUG = debug_value.lower() in ('true', '1', 'yes', 'on')
    else:
        DEBUG = bool(debug_value)
