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

    def write_scan_results(
        self,
        summary: Any,
        output_file: Path,
        format: str = "json",
        pretty_print: bool = True,
    ) -> None:
        """
        Write scan results to output file.

        Args:
            summary: Scan summary object with results
            output_file: Path to output file
            format: Output format (json, yaml, csv)
            pretty_print: Whether to pretty-print output
        """
        try:
            if format.lower() == "json":
                self._write_json_results(summary, output_file, pretty_print)
            else:
                logger.warning(f"Output format '{format}' not implemented, using JSON")
                self._write_json_results(summary, output_file, pretty_print)

        except Exception:
            logger.exception("Failed to write scan results")
            raise

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
