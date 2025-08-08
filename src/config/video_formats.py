"""
Video format configuration and supported file extensions.
"""

import logging

# Configure module logger
logger = logging.getLogger(__name__)


def get_video_extensions() -> list[str]:
    """
    Get list of supported video file extensions.

    Returns:
        List[str]: List of video file extensions including the dot
    """
    extensions = [
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".mpg",
        ".mpeg",
        ".3gp",
        ".asf",
    ]
    logger.debug(f"Returning {len(extensions)} supported video extensions")
    return extensions
