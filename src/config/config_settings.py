"""
Configuration settings for the Corrupt Video Inspector application.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file: Optional[str] = None
    console: bool = True

    def __post_init__(self) -> None:
        """Validate logging configuration."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}")
        self.level = self.level.upper()


@dataclass
class FFmpegConfig:
    """FFmpeg-related configuration settings."""

    command: Optional[str] = None  # Auto-detect if not specified
    quick_timeout: int = 60  # 1 minute for quick scans
    deep_timeout: int = 900  # 15 minutes for deep scans
    extra_args: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate FFmpeg configuration."""
        if self.quick_timeout <= 0:
            raise ValueError("quick_timeout must be positive")
        if self.deep_timeout <= 0:
            raise ValueError("deep_timeout must be positive")
        if self.deep_timeout < self.quick_timeout:
            raise ValueError("deep_timeout must be >= quick_timeout")


@dataclass
class ScannerConfig:
    """Scanner configuration settings."""

    max_workers: int = 4
    default_mode: str = "hybrid"  # quick, deep, hybrid
    recursive: bool = True
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
    chunk_size: int = 100  # Files to process in each chunk

    def __post_init__(self) -> None:
        """Validate scanner configuration."""
        if self.max_workers <= 0:
            raise ValueError("max_workers must be positive")
        if self.default_mode not in {"quick", "deep", "hybrid"}:
            raise ValueError(f"Invalid default_mode: {self.default_mode}")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        # Normalize extensions
        self.extensions = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in self.extensions
        ]


@dataclass
class StorageConfig:
    """Storage configuration settings."""

    temp_dir: Optional[str] = None  # Use system temp if None
    wal_enabled: bool = True
    results_retention_days: int = 30
    compression_enabled: bool = True

    def __post_init__(self) -> None:
        """Validate storage configuration."""
        if self.results_retention_days < 0:
            raise ValueError("results_retention_days must be non-negative")

        if self.temp_dir:
            temp_path = Path(self.temp_dir)
            if not temp_path.exists():
                try:
                    temp_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise ValueError(f"Cannot create temp directory: {e}") from e


@dataclass
class OutputConfig:
    """Output configuration settings."""

    default_json: bool = False
    default_format: str = "json"  # json, yaml, csv
    pretty_print: bool = True
    include_ffmpeg_output: bool = False

    def __post_init__(self) -> None:
        """Validate output configuration."""
        valid_formats = {"json", "yaml", "csv"}
        if self.default_format not in valid_formats:
            raise ValueError(f"Invalid default_format: {self.default_format}")


@dataclass
class TraktConfig:
    """Trakt.tv configuration settings."""

    client_id: str = ""
    client_secret: str = ""
    base_url: str = "https://api.trakt.tv"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0

    def __post_init__(self) -> None:
        """Validate Trakt configuration."""
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")


@dataclass
class UIConfig:
    """User interface configuration."""

    progress_update_interval: float = 1.0  # seconds
    show_progress_bar: bool = True
    verbose_by_default: bool = False
    interactive_by_default: bool = False

    def __post_init__(self) -> None:
        """Validate UI configuration."""
        if self.progress_update_interval <= 0:
            raise ValueError("progress_update_interval must be positive")


@dataclass
class SecurityConfig:
    """Security-related configuration."""

    secrets_dir: str = "/run/secrets"
    max_file_size: int = 100 * 1024 * 1024 * 1024  # 100GB
    allowed_extensions: Optional[List[str]] = None
    # None = use scanner extensions

    def __post_init__(self) -> None:
        """Validate security configuration."""
        if self.max_file_size <= 0:
            raise ValueError("max_file_size must be positive")


@dataclass
class AppConfig:
    """Main application configuration container."""

    # Core configuration sections
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ffmpeg: FFmpegConfig = field(default_factory=FFmpegConfig)
    scanner: ScannerConfig = field(default_factory=ScannerConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    trakt: TraktConfig = field(default_factory=TraktConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    # Global settings
    debug: bool = False
    profile: str = "default"  # default, development, production
    version: str = "2.0.0"

    def __post_init__(self) -> None:
        """Post-initialization validation and setup."""
        # Set debug logging if debug mode is enabled
        if self.debug and self.logging.level != "DEBUG":
            self.logging.level = "DEBUG"

        # Validate profile
        valid_profiles = {"default", "development", "production"}
        if self.profile not in valid_profiles:
            raise ValueError(f"Invalid profile: {self.profile}")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.profile == "development" or self.debug

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.profile == "production"

    def get_temp_dir(self) -> Path:
        """Get the temporary directory path."""
        if self.storage.temp_dir:
            return Path(self.storage.temp_dir)
        return Path.cwd() / "temp"

    def get_log_level(self) -> str:
        """Get the effective log level."""
        return self.logging.level

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "date_format": self.logging.date_format,
                "file": self.logging.file,
                "console": self.logging.console,
            },
            "ffmpeg": {
                "command": self.ffmpeg.command,
                "quick_timeout": self.ffmpeg.quick_timeout,
                "deep_timeout": self.ffmpeg.deep_timeout,
                "extra_args": self.ffmpeg.extra_args,
            },
            "scanner": {
                "max_workers": self.scanner.max_workers,
                "default_mode": self.scanner.default_mode,
                "recursive": self.scanner.recursive,
                "extensions": self.scanner.extensions,
                "chunk_size": self.scanner.chunk_size,
            },
            "storage": {
                "temp_dir": self.storage.temp_dir,
                "wal_enabled": self.storage.wal_enabled,
                "results_retention_days": self.storage.results_retention_days,
                "compression_enabled": self.storage.compression_enabled,
            },
            "output": {
                "default_json": self.output.default_json,
                "default_format": self.output.default_format,
                "pretty_print": self.output.pretty_print,
                "include_ffmpeg_output": self.output.include_ffmpeg_output,
            },
            "trakt": {
                "client_id": self.trakt.client_id,
                "base_url": self.trakt.base_url,
                "timeout": self.trakt.timeout,
                "retry_attempts": self.trakt.retry_attempts,
                "retry_delay": self.trakt.retry_delay,
            },
            "ui": {
                "progress_update_interval": self.ui.progress_update_interval,
                "show_progress_bar": self.ui.show_progress_bar,
                "verbose_by_default": self.ui.verbose_by_default,
                "interactive_by_default": self.ui.interactive_by_default,
            },
            "security": {
                "secrets_dir": self.security.secrets_dir,
                "max_file_size": self.security.max_file_size,
                "allowed_extensions": self.security.allowed_extensions,
            },
            "debug": self.debug,
            "profile": self.profile,
            "version": self.version,
        }

    @classmethod
    def development(cls) -> "AppConfig":
        """Create development configuration."""
        config = cls()
        config.profile = "development"
        config.debug = True
        config.logging.level = "DEBUG"
        config.ui.verbose_by_default = True
        return config

    @classmethod
    def production(cls) -> "AppConfig":
        """Create production configuration."""
        config = cls()
        config.profile = "production"
        config.debug = False
        config.logging.level = "INFO"
        config.storage.compression_enabled = True
        return config


# Environment variable mappings
ENV_MAPPINGS = {
    # Logging
    "CVI_LOG_LEVEL": ("logging", "level"),
    "CVI_LOG_FORMAT": ("logging", "format"),
    "CVI_LOG_FILE": ("logging", "file"),
    "CVI_LOG_CONSOLE": ("logging", "console"),
    # FFmpeg
    "CVI_FFMPEG_COMMAND": ("ffmpeg", "command"),
    "CVI_FFMPEG_QUICK_TIMEOUT": ("ffmpeg", "quick_timeout"),
    "CVI_FFMPEG_DEEP_TIMEOUT": ("ffmpeg", "deep_timeout"),
    # Scanner
    "CVI_MAX_WORKERS": ("scanner", "max_workers"),
    "CVI_DEFAULT_MODE": ("scanner", "default_mode"),
    "CVI_RECURSIVE": ("scanner", "recursive"),
    "CVI_EXTENSIONS": ("scanner", "extensions"),
    "CVI_CHUNK_SIZE": ("scanner", "chunk_size"),
    # Storage
    "CVI_TEMP_DIR": ("storage", "temp_dir"),
    "CVI_WAL_ENABLED": ("storage", "wal_enabled"),
    "CVI_RESULTS_RETENTION_DAYS": ("storage", "results_retention_days"),
    "CVI_COMPRESSION_ENABLED": ("storage", "compression_enabled"),
    # Output
    "CVI_DEFAULT_JSON": ("output", "default_json"),
    "CVI_DEFAULT_FORMAT": ("output", "default_format"),
    "CVI_PRETTY_PRINT": ("output", "pretty_print"),
    "CVI_INCLUDE_FFMPEG_OUTPUT": ("output", "include_ffmpeg_output"),
    # Trakt
    "TRAKT_CLIENT_ID": ("trakt", "client_id"),
    "TRAKT_CLIENT_SECRET": ("trakt", "client_secret"),
    "TRAKT_BASE_URL": ("trakt", "base_url"),
    "TRAKT_TIMEOUT": ("trakt", "timeout"),
    "TRAKT_RETRY_ATTEMPTS": ("trakt", "retry_attempts"),
    "TRAKT_RETRY_DELAY": ("trakt", "retry_delay"),
    # Global
    "CVI_DEBUG": ("debug",),
    "CVI_PROFILE": ("profile",),
}

# Docker secrets mappings
SECRETS_MAPPINGS = {
    "cvi_log_level": ("logging", "level"),
    "cvi_ffmpeg_command": ("ffmpeg", "command"),
    "cvi_max_workers": ("scanner", "max_workers"),
    "cvi_temp_dir": ("storage", "temp_dir"),
    "trakt_client_id": ("trakt", "client_id"),
    "trakt_client_secret": ("trakt", "client_secret"),
}
