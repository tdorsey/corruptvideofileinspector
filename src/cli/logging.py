"""
CLI logging configuration and setup utilities.
"""

import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

# Setup rich console for beautiful output
console = Console()


def setup_logging(verbose: int) -> None:
    """Setup logging configuration based on verbosity level.

    Args:
        verbose: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG).
    """
    level_map = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }

    level = level_map.get(verbose, logging.DEBUG)

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_path=verbose >= 2,
            )
        ],
    )

    # Suppress noisy third-party loggers in production
    if verbose < 2:
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


def configure_logging_from_config(
    level: str = "INFO",
    log_file: Path | None = None,
    log_format: str | None = None,
    date_format: str | None = None,
) -> None:
    """Configure logging with both console (stdout) and file handlers.

    This function configures logging to output to both stdout and a log file,
    making logs visible in Docker containers while also preserving them to disk.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Path to log file. If None, only console logging is configured.
        log_format: Log message format string.
        date_format: Date format string for log timestamps.
    """
    # Convert string level to logging level constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Default format strings
    if log_format is None:
        log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
    if date_format is None:
        date_format = "%Y-%m-%dT%H:%M:%S%z"

    # Get root logger and clear existing handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Always add console handler (stdout) for Docker visibility
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if log file is specified
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
