"""
Formatting utilities for display and output.
"""

import logging

# Configure module logger
logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        str: Formatted size string (e.g., "1.5 MB", "500 B")
    """
    logger.debug(f"Formatting file size: {size_bytes} bytes")

    size_float = float(size_bytes)  # Convert to float for calculations

    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024:
            # For bytes, show as integer; for larger units, show one decimal place
            if unit == "B":
                formatted = f"{int(size_float)} {unit}"
            else:
                formatted = f"{size_float:.1f} {unit}"
            logger.debug(f"Formatted size: {formatted}")
            return formatted
        size_float /= 1024

    formatted = f"{size_float:.1f} TB"
    logger.debug(f"Formatted size: {formatted}")
    return formatted
