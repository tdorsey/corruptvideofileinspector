"""
Formatting utilities for display and output.
"""

import logging

# Configure module logger
logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int, trim_trailing_zero: bool = True) -> str:
    """
    Format file size in human readable format.

    Args:
        size_bytes: File size in bytes
        trim_trailing_zero: If True, remove trailing .0 for whole numbers (e.g., "12 MB" instead of "12.0 MB")

    Returns:
        str: Formatted size string (e.g., "1.5 MB", "12 MB", "500 B")
    """
    logger.debug(
        f"Formatting file size: {size_bytes} bytes, trim_trailing_zero: {trim_trailing_zero}"
    )

    size_float = float(size_bytes)  # Convert to float for calculations

    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024:
            # Show one decimal place for all units except bytes
            if unit == "B":
                formatted = f"{int(size_float)} {unit}"
            else:
                formatted = f"{size_float:.1f} {unit}"
                # Optionally trim trailing .0 for whole numbers
                if trim_trailing_zero and formatted.endswith(f'.0 {unit}'):
                    formatted = f"{int(size_float)} {unit}"
            logger.debug(f"Formatted size: {formatted}")
            return formatted
        size_float /= 1024

    # Handle TB
    formatted = f"{size_float:.1f} TB"
    if trim_trailing_zero and formatted.endswith(".0 TB"):
        formatted = f"{int(size_float)} TB"

    logger.debug(f"Formatted size: {formatted}")
    return formatted
