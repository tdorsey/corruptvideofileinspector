"""Database-only output storage for CLI results."""

import logging
from typing import Any

from src.config.config import AppConfig

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Handles database-only storage for CLI commands."""

    def __init__(self, config: AppConfig):
        """Initialize output formatter with configuration."""
        self.config = config
        self._database_service = None

        # Initialize database service (always required)
        try:
            from src.database.service import DatabaseService

            self._database_service = DatabaseService(
                config.database.path, config.database.auto_cleanup_days
            )
            logger.info(f"Database storage initialized at {config.database.path}")
        except ImportError as e:
            msg = f"Database dependencies not available: {e}"
            logger.exception(msg)
            raise RuntimeError(msg) from e
        except Exception:
            logger.exception("Failed to initialize database service")
            raise

    def store_scan_results(
        self,
        summary: Any,
        scan_results: list[Any] | None = None,
    ) -> int:
        """
        Store scan results in database.

        Args:
            summary: Scan summary object with results
            scan_results: Optional list of individual scan results

        Returns:
            Scan ID in database
        """
        if not self._database_service:
            msg = "Database service not initialized"
            logger.error(msg)
            raise RuntimeError(msg)

        return self._store_scan_in_database(summary, scan_results)

    def _store_scan_in_database(self, summary: Any, scan_results: list[Any] | None = None) -> int:
        """Store scan summary and results in database.

        Args:
            summary: Scan summary object
            scan_results: Optional list of individual scan results

        Returns:
            Scan ID
        """
        if not self._database_service:
            msg = "Database service not initialized"
            raise RuntimeError(msg)

        try:
            from src.database.models import (
                ScanDatabaseModel,
                ScanResultDatabaseModel,
            )

            # Convert summary to database model
            db_scan = ScanDatabaseModel.from_scan_summary(summary)
            scan_id = self._database_service.store_scan(db_scan)

            # Store individual results if provided
            if scan_results:
                db_results = []
                for result in scan_results:
                    db_result = ScanResultDatabaseModel.from_scan_result(result, scan_id)
                    db_results.append(db_result)

                self._database_service.store_scan_results(scan_id, db_results)
                logger.info(f"Stored {len(db_results)} scan results in database")

            # Perform auto-cleanup if configured
            if self.config.database.auto_cleanup_days > 0:
                deleted_count = self._database_service.cleanup_old_scans(
                    self.config.database.auto_cleanup_days
                )
                if deleted_count > 0:
                    logger.info(f"Auto-cleanup removed {deleted_count} old scans")

            return scan_id

        except Exception:
            logger.exception("Failed to store scan results in database")
            raise

    def get_database_service(self):
        """Get the database service instance.

        Returns:
            DatabaseService instance
        """
        if not self._database_service:
            msg = "Database service not initialized"
            raise RuntimeError(msg)
        return self._database_service

    def write_file_list(
        self,
        video_files: list[Any],
        directory: Any,
        output_file: Any,
        format: str = "text",
    ) -> None:
        """Write file list to output file (for list-files command only).

        Note: This is kept for the list-files command which lists video files
        without scanning. Scan results are stored in database only.
        """
        import contextlib
        import json
        from pathlib import Path

        output_file = Path(output_file)
        directory = Path(directory)

        if format.lower() == "json":
            file_data = []
            for video_file in video_files:
                rel_path = getattr(video_file, "path", video_file)
                with contextlib.suppress(ValueError):
                    rel_path = rel_path.relative_to(directory)

                file_info = {
                    "path": str(rel_path),
                    "size": getattr(video_file, "size", 0),
                }
                file_data.append(file_info)

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w", encoding="utf-8") as f:
                json.dump({"directory": str(directory), "files": file_data}, f, indent=2)
        else:
            # Text format
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w", encoding="utf-8") as f:
                f.write(f"Video files in: {directory}\n")
                f.write("=" * 50 + "\n\n")

                for i, video_file in enumerate(video_files, 1):
                    rel_path = getattr(video_file, "path", video_file)
                    if hasattr(rel_path, "relative_to"):
                        with contextlib.suppress(ValueError):
                            rel_path = rel_path.relative_to(directory)

                    size_mb = (
                        getattr(video_file, "size", 0) / (1024 * 1024)
                        if getattr(video_file, "size", 0) > 0
                        else 0
                    )
                    f.write(f"{i:3d}: {rel_path} ({size_mb:.1f} MB)\n")

        logger.info(f"File list written to {output_file}")
