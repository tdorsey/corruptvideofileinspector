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
        extensions = get_video_extensions()
    # Ensure all extensions are lowercase for comparison
    extensions = [ext.lower() for ext in extensions]
    count = 0
    directory_path = Path(directory)
    if recursive:
        for path in directory_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in extensions:
                count += 1
    else:
        for path in directory_path.iterdir():
            if path.is_file() and path.suffix.lower() in extensions:
                count += 1
    return count


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes as a human-readable string.
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024**3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    return f"{size_bytes / (1024 ** 3):.1f} GB"


def get_video_extensions() -> list[str]:
    """
    Return a list of supported video file extensions.
    """
    return [
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".mpg",
    ]
