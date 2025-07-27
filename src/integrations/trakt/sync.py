"""
Trakt.tv sync service for integrating scan results with Trakt.tv watchlist.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...config.settings import AppConfig
from ...core.models import ScanResult
from .client import (
    TRAKT_AVAILABLE,
    FilenameParser,
    MediaItem,
    TraktAPI,
    sync_to_trakt_watchlist,
)

logger = logging.getLogger(__name__)


class TraktSyncService:
    """Service for syncing scan results to Trakt.tv."""

    def __init__(self, config: AppConfig):
        """Initialize the Trakt sync service."""
        self.config = config

    def sync_scan_results(
        self,
        scan_file: Path,
        access_token: str,
        interactive: bool = False,
        dry_run: bool = False,
        filter_corrupt: bool = True,
        sync_corrupt_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Sync scan results to Trakt.tv watchlist.

        Args:
            scan_file: Path to JSON scan results file
            access_token: Trakt API access token
            interactive: Enable interactive selection
            dry_run: Show what would be synced without syncing
            filter_corrupt: Filter out corrupt files (ignored if sync_corrupt_only is True)
            sync_corrupt_only: Only sync corrupted files to watchlist

        Returns:
            Dict containing sync results and statistics
        """
        if not TRAKT_AVAILABLE:
            raise RuntimeError(
                "Trakt.py is not available. Install with: pip install 'corrupt-video-inspector[trakt]'"
            )

        logger.info(f"Syncing scan results to Trakt.tv: {scan_file}")

        # Load scan results
        try:
            with scan_file.open(encoding="utf-8") as f:
                scan_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load scan file {scan_file}: {e}")

        # Process scan results
        results = scan_data.get("results", [])
        media_items: List[MediaItem] = []

        logger.info(f"Processing {len(results)} scan results")

        for result in results:
            filename = result.get("filename", "")
            is_corrupt = result.get("is_corrupt", False)

            if not filename:
                logger.warning("Skipping result with missing filename")
                continue

            # Filter based on corruption status
            if sync_corrupt_only:
                # Only sync corrupted files
                if not is_corrupt:
                    logger.debug(f"Skipping healthy file: {filename}")
                    continue
            elif filter_corrupt:
                # Filter out corrupted files (sync only healthy)
                if is_corrupt:
                    logger.debug(f"Skipping corrupted file: {filename}")
                    continue

            # Parse filename to media item
            try:
                media_item = FilenameParser.parse_filename(filename)
                media_items.append(media_item)
                logger.debug(
                    f"Added {'corrupt' if is_corrupt else 'healthy'} media item: {media_item.title}"
                )
            except Exception as e:
                logger.warning(f"Failed to parse filename {filename}: {e}")
                continue

        if not media_items:
            logger.warning("No media items to sync")
            return {
                "total": 0,
                "movies_added": 0,
                "shows_added": 0,
                "failed": 0,
                "skipped": 0,
                "results": [],
            }

        if dry_run:
            logger.info(f"DRY RUN: Would sync {len(media_items)} media items")
            return {
                "total": len(media_items),
                "movies_added": 0,
                "shows_added": 0,
                "failed": 0,
                "skipped": 0,
                "dry_run": True,
                "results": [
                    {
                        "title": item.title,
                        "year": item.year,
                        "type": item.media_type,
                        "status": "would_sync",
                        "filename": item.original_filename,
                    }
                    for item in media_items
                ],
            }

        # Perform actual sync
        try:
            # Use the existing sync function from client.py
            # Create a temporary scan file with filtered results for the sync function
            temp_scan_data = {
                "results": [
                    {"filename": item.original_filename}
                    for item in media_items
                ]
            }

            # Write temporary file
            temp_file = scan_file.parent / f".temp_sync_{scan_file.name}"
            try:
                with temp_file.open("w", encoding="utf-8") as f:
                    json.dump(temp_scan_data, f)

                # Call the existing sync function
                sync_results = sync_to_trakt_watchlist(
                    scan_file=str(temp_file),
                    access_token=access_token,
                    interactive=interactive,
                    verbose=True,
                )

                return sync_results

            finally:
                # Clean up temp file
                if temp_file.exists():
                    temp_file.unlink()

        except Exception as e:
            logger.exception("Failed to sync to Trakt.tv")
            raise RuntimeError(f"Trakt sync failed: {e}")

    def sync_corrupt_files(
        self,
        scan_file: Path,
        access_token: str,
        interactive: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Sync only corrupted files to Trakt.tv watchlist.

        This is a convenience method for syncing corrupted files after a scan is complete.

        Args:
            scan_file: Path to JSON scan results file
            access_token: Trakt API access token
            interactive: Enable interactive selection
            dry_run: Show what would be synced without syncing

        Returns:
            Dict containing sync results and statistics
        """
        logger.info("Syncing only corrupted files to Trakt.tv")
        return self.sync_scan_results(
            scan_file=scan_file,
            access_token=access_token,
            interactive=interactive,
            dry_run=dry_run,
            filter_corrupt=False,
            sync_corrupt_only=True,
        )