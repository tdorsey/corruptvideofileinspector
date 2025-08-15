import os
from pathlib import Path

import toml
import yaml
from pydantic import BaseModel, Field

from src.config.merge import load_configuration_with_merge
from src.core.models.scanning import FileStatus, ScanMode


class LoggingConfig(BaseModel):
    level: str = Field(default="WARNING")
    file: Path = Field(default=Path("/app/output/inspector.log"))
    date_format: str = Field(default="%Y-%m-%dT%H:%M:%S%z")
    format: str = Field(default="%(asctime)s %(levelname)s %(name)s %(message)s")


class FFmpegConfig(BaseModel):
    command: Path = Field(default=Path("/usr/bin/ffmpeg"))
    quick_timeout: int = Field(default=30)
    deep_timeout: int = Field(default=1800)


class ProcessingConfig(BaseModel):
    max_workers: int = Field(default=8)
    default_mode: str = Field(default="quick")


class OutputConfig(BaseModel):
    default_json: bool = Field(default=True)
    default_output_dir: Path = Field(...)
    # Default filename for scan results output
    default_filename: str = Field(default="scan_results.json")


class DatabaseConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable SQLite database storage")
    path: Path = Field(
        default=Path.home() / ".corrupt-video-inspector" / "scans.db",
        description="Database file location"
    )
    auto_cleanup_days: int = Field(
        default=0, 
        description="Auto-delete scans older than X days (0 = disabled)"
    )
    create_backup: bool = Field(
        default=True, 
        description="Create backups before schema changes"
    )


class TraktConfig(BaseModel):
    client_id: str = Field(default="")
    client_secret: str = Field(default="")
    default_watchlist: str | None = Field(
        default=None,
        description="Default watchlist name or slug for sync operations. If None, uses main watchlist.",
    )
    include_statuses: list[FileStatus] = Field(default_factory=lambda: [FileStatus.HEALTHY])


class ScanConfig(BaseModel):
    recursive: bool = Field(default=True)
    max_workers: int = Field(default=8)
    mode: ScanMode = Field(default=ScanMode.QUICK)
    default_input_dir: Path = Field(...)
    extensions: list[str] = Field(
        default_factory=lambda: [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"]
    )


class AppConfig(BaseModel):
    logging: LoggingConfig
    ffmpeg: FFmpegConfig
    processing: ProcessingConfig
    output: OutputConfig
    scan: ScanConfig
    trakt: TraktConfig
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)


_CONFIG_SINGLETON: AppConfig | None = None


def load_config(config_path: Path | None = None, debug: bool = False) -> AppConfig:
    """
    Load configuration from a YAML file with centralized merge pipeline.
    Loads once and caches the result as a singleton.

    Configuration precedence (highest to lowest):
    1. Environment variables (CVI_*, TRKT_*)
    2. Docker secrets files
    3. Configuration file (YAML)
    4. Model defaults (Pydantic)

    Args:
        config_path: Optional path to the configuration file.
                     If None, the default config.yaml will be used.
        debug: Enable debug logging for configuration overrides

    Returns:
        AppConfig: Loaded configuration object with validation

    Raises:
        FileNotFoundError: If no configuration file can be found
        ValueError: For invalid configuration (e.g., partial Trakt credentials)
    """
    global _CONFIG_SINGLETON
    if config_path is None and _CONFIG_SINGLETON is not None and not debug:
        return _CONFIG_SINGLETON

    if config_path is not None:
        config_path = Path(config_path)
    else:
        # 1. Try config.yaml at the same level as pyproject.toml
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.is_file():
            project_root = pyproject_path.parent
            project_config = project_root / "config.yaml"
            if project_config.is_file():
                config_path = project_config
            else:
                pyproject = toml.load(pyproject_path)
                app_name = pyproject.get("project", {}).get("name", "corruptvideofileinspector")
                # 3. Try XDG config home
                xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
                if xdg_config_home:
                    xdg_path = Path(xdg_config_home) / app_name / "config.yaml"
                    if xdg_path.is_file():
                        config_path = xdg_path
                    else:
                        raise FileNotFoundError(
                            f"No config file found at /app/config.yaml, {project_config}, or {xdg_path}. "
                            "Please provide a config file."
                        )
                else:
                    raise FileNotFoundError(
                        f"No config file found at /app/config.yaml or {project_config}, and XDG_CONFIG_HOME is not set. "
                        "Please provide a config file."
                    )
        else:
            raise FileNotFoundError(
                "No config file found at /app/config.yaml and no pyproject.toml found to locate project root. "
                "Please provide a config file."
            )

    # Load YAML configuration file
    with config_path.open("r", encoding="utf-8") as f:
        file_config = yaml.safe_load(f)

    # Use centralized merge pipeline
    secrets_dir = os.environ.get("CVI_SECRETS_DIR", "/run/secrets")
    merged_config = load_configuration_with_merge(
        file_config=file_config, secrets_dir=secrets_dir, debug=debug
    )

    # Environment overrides for Trakt credentials
    env_trakt_client_id = os.environ.get("CVI_TRAKT_CLIENT_ID")
    if env_trakt_client_id:
        merged_config.setdefault("trakt", {})["client_id"] = env_trakt_client_id
    env_trakt_client_secret = os.environ.get("CVI_TRAKT_CLIENT_SECRET")
    if env_trakt_client_secret:
        merged_config.setdefault("trakt", {})["client_secret"] = env_trakt_client_secret

    # Validate and create config object using Pydantic
    _CONFIG_SINGLETON = AppConfig.model_validate(merged_config)
    return _CONFIG_SINGLETON
