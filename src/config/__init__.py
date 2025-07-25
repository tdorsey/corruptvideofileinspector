# Export AppConfig and load_config for public API
from .config_loader import ConfigLoader
from .config_settings import AppConfig


def load_config(*args, **kwargs):
    """Load configuration using ConfigLoader."""
    loader = ConfigLoader()
    return loader.load(*args, **kwargs)


__all__ = ["AppConfig", "load_config"]
