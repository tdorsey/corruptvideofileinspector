"""
Main entry point for the Corrupt Video Inspector application.

This module allows the package to be executed as:
    python -m src.main
    python src/main.py
"""

import logging

from .cli.main import cli
from .config.config import load_config

if __name__ == "__main__":
    config = load_config()
    logging.basicConfig(
        level=getattr(logging, config.logging.level.upper(), logging.WARNING),
        filename=str(config.logging.file),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt=config.logging.date_format,
    )
    logging.info("Starting Corrupt Video Inspector...")
    cli()
