"""
Utility functions for Corrupt Video Inspector
"""
import os
from pathlib import Path
from typing import List


def count_all_video_files(directory: str, recursive: bool = True, extensions: List[str] = None) -> int:
    """Count all video files in a directory"""
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg']
    
    ext_set = {ext.lower() for ext in extensions}
    count = 0
    
    path = Path(directory)
    
    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"
    
    for file_path in path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in ext_set:
            count += 1
    
    return count


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_video_extensions() -> List[str]:
    """Get list of supported video file extensions"""
    return ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.asf']
