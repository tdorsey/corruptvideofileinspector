from pathlib import Path
from typing import Optional

from .config import Config
from .config import load_config as _load_config

__all__ = ["Config", "load_config"]


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from a YAML file with Pydantic schema validation.

    Args:
        config_path: Optional path to the configuration file.
                   If None, the default config.yaml will be used.

    Returns:
        Config: Loaded configuration object with validation
    """
    return _load_config(config_path)
