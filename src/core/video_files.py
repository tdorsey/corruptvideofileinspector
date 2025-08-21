"""
Video file operations and utilities.
"""

import importlib
import logging
from pathlib import Path

from src.config.video_formats import get_video_extensions

# Configure module logger
logger = logging.getLogger(__name__)


def count_all_video_files(
    directory: str,
    recursive: bool = True,
    extensions: list[str] | None = None,
    use_content_detection: bool = False,
    ffprobe_timeout: int = 30,
) -> int:
    """
    Count all potential video files in a directory using probe-based detection.

    Args:
        directory: Path to directory to scan
        recursive: Whether to scan subdirectories recursively
        extensions: Deprecated parameter, kept for compatibility
        use_content_detection: Use FFprobe content analysis instead of extensions
        ffprobe_timeout: Timeout for FFprobe analysis when using content detection

    Returns:
        int: Number of files found (all files, to be probed later)

    Raises:
        Exception: If directory scanning fails
    """
    logger.debug(
        f"Counting all files in {directory}, recursive={recursive} (probe-based detection)"
    )

    count = 0

    # Initialize FFmpeg client for content detection if needed
    ffmpeg_client = None
    if use_content_detection:
        try:
            # Import heavy dependencies at runtime to avoid import errors during static analysis
            load_config = importlib.import_module("src.config.config").load_config
            FFmpegClient = importlib.import_module("src.ffmpeg.ffmpeg_client").FFmpegClient

            config = load_config()
            ffmpeg_client = FFmpegClient(config.ffmpeg)
            logger.debug("FFmpeg client initialized for content detection")
        except Exception as e:
            logger.warning("FFmpeg client unavailable; falling back to extension-based detection")
            logger.debug(f"FFmpeg initialization error: {e}")
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
                    logger.debug(
                        f"Content analysis failed for {file_path}: {e}, using extension fallback"
                    )
                    # Fall back to extension check for this file
                    ext_list = extensions or get_video_extensions()
                    is_video = file_path.suffix.lower() in {ext.lower() for ext in ext_list}
            else:
                # Use extension-based detection as fallback
                ext_list = extensions or get_video_extensions()
                is_video = file_path.suffix.lower() in {ext.lower() for ext in ext_list}

            if is_video:
                count += 1
                logger.debug(f"Found file: {file_path}")

        logger.info(f"Found {count} files in {directory} (probe-based detection)")
        return count

    except Exception:
        logger.exception(f"Error counting files in {directory}")
        raise
