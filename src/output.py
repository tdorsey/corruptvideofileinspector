"""Output formatting utilities for CLI results."""

import contextlib
import json
import logging
from pathlib import Path
from typing import Any

from src.config.config import AppConfig
from src.core.database import DatabaseManager
from src.core.models.reporting.scan_output import ScanMode, ScanOutputModel
from src.core.models.scanning import ScanResult, ScanSummary

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Handles formatting and writing output files for CLI commands."""

    def __init__(self, config: AppConfig):
        """Initialize output formatter with configuration."""
        self.config = config
        self.db_manager = None
        if config.database.enabled:
            try:
                self.db_manager = DatabaseManager(config.database)
                logger.info("Database storage enabled")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                logger.warning("Continuing with file-only output")

    def write_scan_results(
        self,
        summary: Any,
        output_file: Path,
        format: str = "json",
        pretty_print: bool = True,
        scan_results: list[ScanResult] | None = None,
    ) -> None:
        """
        Write scan results to output file and optionally to database.

        Args:
            summary: Scan summary object with results
            output_file: Path to output file
            format: Output format (json, yaml, csv)
            pretty_print: Whether to pretty-print output
            scan_results: Optional list of individual scan results for database storage
        """
        try:
            # Always write to file (backward compatibility)
            if format.lower() == "json":
                self._write_json_results(summary, output_file, pretty_print)
            else:
                logger.warning(f"Output format '{format}' not implemented, using JSON")
                self._write_json_results(summary, output_file, pretty_print)

            # Optionally store in database
            if self.db_manager and isinstance(summary, ScanSummary):
                self._store_to_database(summary, scan_results)

        except Exception:
            logger.exception("Failed to write scan results")
            raise

    def _store_to_database(
        self, 
        summary: ScanSummary, 
        scan_results: list[ScanResult] | None = None
    ) -> None:
        """Store scan results to database."""
        try:
            # Store summary and get ID
            summary_id = self.db_manager.store_scan_summary(summary)
            
            # Store individual results if provided
            if scan_results:
                self.db_manager.store_scan_results(scan_results, summary_id)
                
            logger.info(f"Stored scan data to database (summary ID: {summary_id})")
        except Exception as e:
            logger.error(f"Failed to store scan data to database: {e}")
            # Don't re-raise - database storage is optional

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
            else:
                self._write_text_file_list(video_files, directory, output_file)

        except Exception:
            logger.exception("Failed to write file list")
            raise

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
            json.dump({"directory": str(directory), "files": file_data}, f, indent=2)

        logger.info(f"File list written to {output_file}")

    def _write_text_file_list(
        self, video_files: list[Any], directory: Path, output_file: Path
    ) -> None:
        """Write file list as text."""
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

    def get_scan_history(
        self, 
        directory: Path | None = None, 
        limit: int | None = None
    ) -> list[ScanSummary]:
        """Get scan history from database."""
        if not self.db_manager:
            logger.warning("Database not enabled, cannot retrieve scan history")
            return []
        
        return self.db_manager.get_scan_summaries(directory, limit)

    def get_scan_results_from_db(
        self,
        summary_id: int | None = None,
        directory: Path | None = None,
        is_corrupt: bool | None = None
    ) -> list[ScanResult]:
        """Get scan results from database."""
        if not self.db_manager:
            logger.warning("Database not enabled, cannot retrieve scan results")
            return []
        
        return self.db_manager.get_scan_results(summary_id, directory, is_corrupt)

    def get_incomplete_scan(self, directory: Path) -> ScanSummary | None:
        """Get incomplete scan for resume functionality."""
        if not self.db_manager:
            logger.warning("Database not enabled, cannot check for incomplete scans")
            return None
        
        return self.db_manager.get_latest_incomplete_scan(directory)

    def get_database_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        if not self.db_manager:
            return {"enabled": False, "message": "Database not enabled"}
        
        stats = self.db_manager.get_database_stats()
        stats["enabled"] = True
        return stats
