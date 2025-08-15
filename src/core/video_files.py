"""
Video file operations and utilities.
"""

import logging
from pathlib import Path

from src.config.video_formats import get_video_extensions

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
        extensions: List of file extensions to include (defaults to config extensions)

    Returns:
        int: Number of video files found

    Raises:
        Exception: If directory scanning fails
    """
def count_all_video_files(
    directory: str, 
    recursive: bool = True, 
    extensions: list[str] | None = None,
    use_content_detection: bool = False,
    ffprobe_timeout: int = 30
) -> int:
    """
    Count all video files in a directory.

    Args:
        directory: Path to directory to scan
        recursive: Whether to scan subdirectories recursively
        extensions: List of file extensions to include (defaults to config extensions)
        use_content_detection: Use FFprobe content analysis instead of extensions
        ffprobe_timeout: Timeout for FFprobe analysis when using content detection

    Returns:
        int: Number of video files found

    Raises:
        Exception: If directory scanning fails
    """
    if extensions is None:
        # Use same default extensions as config for consistency
        extensions = get_video_extensions()

    logger.debug(f"Counting video files in {directory}, recursive={recursive}")
    if use_content_detection:
        logger.debug("Using FFprobe content detection")
    else:
        logger.debug(f"Looking for extensions: {extensions}")

    ext_set = {ext.lower() for ext in extensions}
    count = 0

    # Initialize FFmpeg client for content detection if needed
    ffmpeg_client = None
    if use_content_detection:
        try:
            from src.config.config import load_config
            from src.ffmpeg.ffmpeg_client import FFmpegClient
            config = load_config()
            ffmpeg_client = FFmpegClient(config.ffmpeg)
            logger.debug("FFmpeg client initialized for content detection")
        except Exception as e:
            logger.warning(f"Failed to initialize FFmpeg client for content detection: {e}")
            logger.warning("Falling back to extension-based detection")
            use_content_detection = False

    try:
        path = Path(directory)

        pattern = "**/*" if recursive else "*"

        for file_path in path.glob(pattern):
            if not file_path.is_file():
                continue
                
            is_video = False
            if use_content_detection and ffmpeg_client:
                # Use FFprobe content analysis
                try:
                    is_video = ffmpeg_client.is_video_file(file_path, timeout=ffprobe_timeout)
                    logger.debug(f"Content analysis result for {file_path}: {is_video}")
                except Exception as e:
                    logger.debug(f"Content analysis failed for {file_path}: {e}, using extension fallback")
                    # Fall back to extension check for this file
                    is_video = file_path.suffix.lower() in ext_set
            else:
                # Use extension-based detection
                is_video = file_path.suffix.lower() in ext_set
                
            if is_video:
                count += 1
                logger.debug(f"Found video file: {file_path}")

        logger.info(f"Counted {count} video files in {directory}")
        return count

    except Exception:
        logger.exception(f"Error counting video files in {directory}")
        raise
