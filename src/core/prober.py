"""Video file probing functionality for metadata and hash calculation."""

import logging
from pathlib import Path

from src.core.models.inspection import VideoFile
from src.core.utils import calculate_sha256_hash

logger = logging.getLogger(__name__)


class VideoProber:
    """Handles video file probing operations including hash calculation and metadata extraction."""

    def __init__(self) -> None:
        """Initialize the video prober."""
        logger.debug("VideoProber initialized")

    def create_video_file_with_hash(self, path: Path) -> VideoFile:
        """Create a VideoFile object with SHA-256 hash calculated.

        Args:
            path: Path to the video file

        Returns:
            VideoFile with hash calculated

        Raises:
            IOError: If hash calculation fails critically
        """
        try:
            sha256_hash = calculate_sha256_hash(path)
            video_file = VideoFile(path=path, sha256_hash=sha256_hash)
            logger.debug(
                f"Created VideoFile with hash [SHA256: {video_file.short_hash}]: {path.name}"
            )
            return video_file
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {path}: {e}")
            # Create VideoFile without hash if calculation fails
            return VideoFile(path=path, sha256_hash="")

    def probe_video_file(self, path: Path) -> VideoFile:
        """Probe a video file and extract basic information including hash.

        This is the main entry point for video file probing. Currently focuses
        on hash calculation, but can be extended for other metadata extraction.

        Args:
            path: Path to the video file

        Returns:
            VideoFile with probing information populated
        """
        return self.create_video_file_with_hash(path)

    def calculate_file_hash(self, path: Path) -> str:
        """Calculate SHA-256 hash for a video file.

        Args:
            path: Path to the file

        Returns:
            SHA-256 hash as hexadecimal string, empty string if calculation fails
        """
        try:
            return calculate_sha256_hash(path)
        except Exception as e:
            logger.warning(f"Hash calculation failed for {path}: {e}")
            return ""
