"""
CLI logging configuration and setup utilities.
"""

import logging

from rich.console import Console  # type: ignore
from rich.logging import RichHandler  # type: ignore

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
