"""
Logging configuration utilities.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    logging_config: Optional[object] = None, 
    verbose: bool = False, 
    quiet: bool = False
) -> None:
    """
    Setup logging configuration.
    
    Args:
        logging_config: Logging configuration object (if available)
        verbose: Enable verbose logging
        quiet: Enable quiet mode (errors only)
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    # If we have a logging config object, try to use its level
    if logging_config and hasattr(logging_config, 'level'):
        level = getattr(logging, logging_config.level.upper(), level)
    
    # Configure basic logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    # Set root logger level
    logging.getLogger().setLevel(level)