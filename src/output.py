"""Database storage utilities for CLI results."""

import logging
from typing import Any

from src.config.config import AppConfig

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Handles database storage for CLI commands."""

    def __init__(self, config: AppConfig):
        """Initialize output formatter with database storage."""
        self.config = config
        self._database_service = None

        # Initialize database service - database is now required
        if config.database.enabled:
            try:
                from src.database.service import DatabaseService

                self._database_service = DatabaseService(
                    config.database.path, config.database.auto_cleanup_days
                )
                logger.info(f"Database storage enabled at {config.database.path}")
            except ImportError as e:
                logger.error(f"Database dependencies not available: {e}")
                raise RuntimeError("Database storage is required but dependencies are missing") from e
            except Exception as e:
                logger.exception("Failed to initialize database service")
                raise RuntimeError("Failed to initialize database storage") from e
        else:
            logger.warning("Database storage is disabled - no scan results will be stored")
            # Still create service in case configuration is updated later

    def store_scan_results(
        self,
        summary: Any,
        scan_results: list[Any] | None = None,
    ) -> int | None:
        """
        Store scan results in database.

        Args:
            summary: Scan summary object with results
            scan_results: Optional list of individual scan results

        Returns:
            Scan ID if successfully stored, None otherwise
        """
        try:
            if not self._database_service:
                if self.config.database.enabled:
                    logger.error("Database service not available despite being enabled")
                else:
                    logger.warning("Database storage is disabled - scan results will not be stored")
                return None

            return self._store_scan_in_database(summary, scan_results)

        except Exception:
            logger.exception("Failed to store scan results")
            raise

    def _store_scan_in_database(
        self, summary: Any, scan_results: list[Any] | None = None
    ) -> int | None:
        """Store scan summary and results in database.

        Args:
            summary: Scan summary object
            scan_results: Optional list of individual scan results

        Returns:
            Scan ID if successfully stored, None otherwise
        """
        if not self._database_service:
            return None

        try:
            from src.database.models import ScanDatabaseModel, ScanResultDatabaseModel

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
            return None
