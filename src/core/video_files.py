"""
Video file operations and utilities.
"""

import logging
from pathlib import Path

# Configure module logger
logger = logging.getLogger(__name__)


def count_all_video_files(
    directory: str, recursive: bool = True, extensions: list[str] | None = None
) -> int:
    """
    Count all video files in a directory.

    Args:
        directory: Path to directory to scan
        recursive: Whether to scan subdirectories recursively
        extensions: List of file extensions to include (defaults to common video formats)

    Returns:
        int: Number of video files found

    Raises:
        Exception: If directory scanning fails
    """
    if extensions is None:
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
        ]

    logger.debug(f"Counting video files in {directory}, recursive={recursive}")
    logger.debug(f"Looking for extensions: {extensions}")

    ext_set = {ext.lower() for ext in extensions}
    count = 0

    try:
        path = Path(directory)

        pattern = "**/*" if recursive else "*"

        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in ext_set:
                count += 1
                logger.debug(f"Found video file: {file_path}")

        logger.info(f"Counted {count} video files in {directory}")
        return count

    except Exception:
        logger.exception(f"Error counting video files in {directory}")
        raise
