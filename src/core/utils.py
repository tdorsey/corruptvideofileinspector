"""Core utility functions for video file processing."""

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192


def calculate_sha256_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash for a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal string representation of the SHA-256 hash

    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()

    try:
        with file_path.open("rb") as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256_hash.update(chunk)
    except OSError as e:
        raise OSError(f"Error reading file {file_path}: {e}") from e

    return sha256_hash.hexdigest()


def format_hash_for_logging(sha256_hash: str, short: bool = True) -> str:
    """Format SHA-256 hash for logging display.

    Args:
        sha256_hash: Full SHA-256 hash string
        short: If True, return shortened version for readability

    Returns:
        Formatted hash string suitable for logging
    """
    if short and len(sha256_hash) >= 12:
        return f"{sha256_hash[:8]}...{sha256_hash[-4:]}"
    return sha256_hash
