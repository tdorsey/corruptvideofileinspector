"""Output formatting utilities for CLI results."""

import contextlib
import json
import logging
from pathlib import Path
from typing import Any

from src.config.config import AppConfig
from src.core.models.reporting.scan_output import ScanMode, ScanOutputModel

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Handles formatting and writing output files for CLI commands."""

    def __init__(self, config: AppConfig):
        """Initialize output formatter with configuration."""
        self.config = config
        self._database_service = None

        # Initialize database service if enabled
        if config.database.enabled:
            try:
                from src.database.service import DatabaseService

                self._database_service = DatabaseService(
                    config.database.path, config.database.auto_cleanup_days
                )
                logger.info(f"Database storage enabled at {config.database.path}")
            except ImportError as e:
                logger.warning(f"Database dependencies not available: {e}")
                self._database_service = None
            except Exception:
                logger.exception("Failed to initialize database service")
                self._database_service = None

    def write_scan_results(
        self,
        summary: Any,
        scan_results: list[Any] | None = None,
        output_file: Path | None = None,
        format: str = "json",
        pretty_print: bool = True,
        store_in_database: bool = True,
    ) -> None:
        """
        Write scan results to output file and optionally to database.

        Args:
            summary: Scan summary object with results
            scan_results: Optional list of individual scan results
            output_file: Path to output file (if None, uses database only)
            format: Output format (json, yaml, csv)
            pretty_print: Whether to pretty-print output
            store_in_database: Whether to store in database (if enabled)
        """
        try:
            # Store in database if enabled and requested
            if store_in_database and self._database_service and self.config.database.enabled:
                self._store_scan_in_database(summary, scan_results)

            # Write to file if output path provided
            if output_file:
                if format.lower() == "json":
                    self._write_json_results(summary, output_file, pretty_print)
                else:
                    logger.warning(f"Output format '{format}' not implemented, using JSON")
                    self._write_json_results(summary, output_file, pretty_print)

        except Exception:
            logger.exception("Failed to write scan results")
            raise

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
                    logger.debug("Database storage is disabled - scan results will not be stored")
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

    def get_database_service(self):
        """Get the database service instance if available.

        Returns:
            DatabaseService instance or None if not available
        """
        return self._database_service

    def _write_json_results(self, summary: Any, output_file: Path, pretty_print: bool) -> None:
        """Write scan results as JSON using ScanOutputModel."""
        # Convert summary to ScanOutputModel
        model = ScanOutputModel(
            scan_mode=getattr(summary, "scan_mode", ScanMode.QUICK),
            total_files=getattr(summary, "total_files", 0),
            processed_files=getattr(summary, "processed_files", 0),
            corrupt_files=getattr(summary, "corrupt_files", 0),
            healthy_files=getattr(summary, "healthy_files", 0),
            scan_time=getattr(summary, "scan_time", 0.0),
            success_rate=getattr(summary, "success_rate", None),
            was_resumed=getattr(summary, "was_resumed", None),
            deep_scans_needed=getattr(summary, "deep_scans_needed", None),
            deep_scans_completed=getattr(summary, "deep_scans_completed", None),
        )

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w", encoding="utf-8") as f:
            if pretty_print:
                f.write(model.model_dump_json(indent=2))
            else:
                f.write(model.model_dump_json())

        logger.info(f"Scan results written to {output_file}")

    def write_file_list(
        self,
        video_files: list[Any],
        directory: Path,
        output_file: Path,
        format: str = "text",
    ) -> None:
        """
        Write file list to output file.

        Args:
            video_files: List of video file objects
            directory: Base directory for relative paths
            output_file: Path to output file
            format: Output format (text, json, csv)
        """
        try:
            if format.lower() == "json":
                self._write_json_file_list(video_files, directory, output_file)
            elif format.lower() == "csv":
                self._write_csv_file_list(video_files, directory, output_file)
            else:
                self._write_text_file_list(video_files, directory, output_file)

        except Exception:
            logger.exception("Failed to write file list")
            raise

    def _write_json_file_list(
        self, video_files: list[Any], directory: Path, output_file: Path
    ) -> None:
        """Write file list as JSON."""
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
            json.dump(file_data, f, indent=2)

        logger.info(f"File list written to {output_file}")

    def _write_csv_file_list(
        self, video_files: list[Any], directory: Path, output_file: Path
    ) -> None:
        """Write file list as CSV."""
        import csv

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["path", "size_bytes", "size_mb"])
            
            for video_file in video_files:
                rel_path = getattr(video_file, "path", video_file)
                with contextlib.suppress(ValueError):
                    rel_path = rel_path.relative_to(directory)
                
                size_bytes = getattr(video_file, "size", 0)
                size_mb = size_bytes / (1024 * 1024) if size_bytes > 0 else 0
                writer.writerow([str(rel_path), size_bytes, f"{size_mb:.1f}"])

        logger.info(f"File list written to {output_file}")

    def _write_text_file_list(
        self, video_files: list[Any], directory: Path, output_file: Path
    ) -> None:
        """Write file list as plain text."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w", encoding="utf-8") as f:
            f.write(f"Found {len(video_files)} video files:\n\n")
            for i, video_file in enumerate(video_files, 1):
                rel_path = getattr(video_file, "path", video_file)
                with contextlib.suppress(ValueError):
                    rel_path = rel_path.relative_to(directory)
                
                size_bytes = getattr(video_file, "size", 0)
                size_mb = size_bytes / (1024 * 1024) if size_bytes > 0 else 0
                f.write(f"  {i:3d}: {rel_path} ({size_mb:.1f} MB)\n")

        logger.info(f"File list written to {output_file}")
