import os
from pathlib import Path
from typing import List, Optional

import toml
from piny import PydanticValidator, YamlLoader  # type: ignore
from pydantic import BaseModel, Field

from src.config.secrets import read_docker_secret
from src.core.models.scanning import ScanMode


class LoggingConfig(BaseModel):
    level: str = Field(default="WARNING")
    file: Path = Field(default=Path("/app/output/inspector.log"))
    date_format: str = Field(default="%Y-%m-%dT%H:%M:%S%z")


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
    default_filename: str = Field(default="corruption_scan.json")


class TraktConfig(BaseModel):
    client_id: str = Field(default="")
    client_secret: str = Field(default="")


class ScanConfig(BaseModel):
    recursive: bool = Field(default=True)
    max_workers: int = Field(default=8)
    mode: ScanMode = Field(default=ScanMode.QUICK)
    default_input_dir: Path = Field(...)
    extensions: List[str] = Field(
        default_factory=lambda: [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"]
    )


class AppConfig(BaseModel):
    logging: LoggingConfig
    ffmpeg: FFmpegConfig
    processing: ProcessingConfig
    output: OutputConfig
    scan: ScanConfig
    trakt: TraktConfig


_CONFIG_SINGLETON: Optional[AppConfig] = None

def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration from a YAML file with Pydantic schema validation.
    Loads once and caches the result as a singleton.
    Args:
        config_path: Optional path to the configuration file.
                     If None, the default config.yaml will be used.
    Returns:
        AppConfig: Loaded configuration object with validation
    """
    global _CONFIG_SINGLETON
    if config_path is None and _CONFIG_SINGLETON is not None:
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
    loader = YamlLoader(
        path=config_path,
        validator=PydanticValidator,
        schema=AppConfig,
    )
    config_data = loader.load(many=False)

    # If a Docker secret exists for trakt_client_secret, override config value
    docker_secret = read_docker_secret("trakt_client_secret")
    if docker_secret is not None:
        if "trakt" in config_data:
            config_data["trakt"]["client_secret"] = docker_secret
        elif hasattr(config_data, "trakt"):
            config_data.trakt["client_secret"] = docker_secret

    _CONFIG_SINGLETON = AppConfig.model_validate(config_data)
    return _CONFIG_SINGLETON
    docker_secret = read_docker_secret("trakt_client_secret")
    if docker_secret is not None:
        if "trakt" in config_data:
            config_data["trakt"]["client_secret"] = docker_secret
        elif hasattr(config_data, "trakt"):
            config_data.trakt["client_secret"] = docker_secret

    _CONFIG_SINGLETON = AppConfig.model_validate(config_data)
    return _CONFIG_SINGLETON
