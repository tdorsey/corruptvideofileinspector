from pathlib import Path
from typing import List, Optional

from piny import PydanticValidator, YamlLoader  # type: ignore
from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    level: str = Field(default="DEBUG")
    format: str = Field(default="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    date_format: str = Field(default="%Y-%m-%d %H:%M:%S")
    file: Path = Field(default=Path("/app/output/inspector.log"))


class FFmpegConfig(BaseModel):
    command: Path = Field(default=Path("/usr/bin/ffmpeg"))
    quick_timeout: int = Field(default=30)
    deep_timeout: int = Field(default=1800)


class ProcessingConfig(BaseModel):
    max_workers: int = Field(default=8)
    default_mode: str = Field(default="quick")


class OutputConfig(BaseModel):
    default_json: bool = Field(default=True)
    default_output_dir: Path = Field(default=Path("/app/output"))
    default_filename: str = Field(default="corruption_scan.json")


class ScanConfig(BaseModel):
    recursive: bool = Field(default=True)
    default_input_dir: Path = Field(default=Path("/app/videos"))
    extensions: List[str] = Field(
        default_factory=lambda: [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"]
    )


class AppConfig(BaseModel):
    logging: LoggingConfig
    ffmpeg: FFmpegConfig
    processing: ProcessingConfig
    output: OutputConfig
    scan: ScanConfig


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration from a YAML file with Pydantic schema validation.
    Args:
        config_path: Optional path to the configuration file.
                     If None, the default config.yaml will be used.
    Returns:
        AppConfig: Loaded configuration object with validation
    """

    if config_path is None:
        config_path = Path("config.yaml")

    loader = YamlLoader(
        path=config_path,
        validator=PydanticValidator,
        schema=AppConfig,
    )
    config_data = loader.load(many=False)
    return AppConfig.model_validate(config_data)
