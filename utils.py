"""
Utility functions for Corrupt Video Inspector
"""
import os
import logging
from pathlib import Path
from typing import List, Optional

# Configure module logger
logger = logging.getLogger(__name__)


def count_all_video_files(directory: str, recursive: bool = True, extensions: Optional[List[str]] = None) -> int:
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
        extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg']
    
    logger.debug(f"Counting video files in {directory}, recursive={recursive}")
    logger.debug(f"Looking for extensions: {extensions}")
    
    ext_set = {ext.lower() for ext in extensions}
    count = 0
    
    try:
        path = Path(directory)
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in ext_set:
                count += 1
                logger.debug(f"Found video file: {file_path}")
        
        logger.info(f"Counted {count} video files in {directory}")
        return count
        
    except Exception as e:
        logger.error(f"Error counting video files in {directory}: {e}")
        raise


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        str: Formatted size string (e.g., "1.5 MB")
    """
    logger.debug(f"Formatting file size: {size_bytes} bytes")
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            formatted = f"{size_bytes:.1f} {unit}"
            logger.debug(f"Formatted size: {formatted}")
            return formatted
        size_bytes /= 1024
    
    formatted = f"{size_bytes:.1f} TB"
    logger.debug(f"Formatted size: {formatted}")
    return formatted


def get_video_extensions() -> List[str]:
    """
    Get list of supported video file extensions.
    
    Returns:
        List[str]: List of video file extensions including the dot
    """
    extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.asf']
    logger.debug(f"Returning {len(extensions)} supported video extensions")
    return extensions
