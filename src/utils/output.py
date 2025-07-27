"""
Output formatting utilities for scan results and file lists.
"""

import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..config.settings import AppConfig
from ..core.models import ScanSummary, VideoFile


class OutputFormatter:
    """Handles formatting and writing output files for scan results."""

    def __init__(self, config: AppConfig):
        """Initialize the output formatter with configuration."""
        self.config = config

    def write_scan_results(
        self,
        summary: ScanSummary,
        output_file: Path,
        format: str = "json",
        pretty_print: bool = True,
    ) -> None:
        """
        Write scan results to output file.

        Args:
            summary: Scan summary with results
            output_file: Path to output file
            format: Output format (json, yaml, csv)
            pretty_print: Whether to format output nicely
        """
        # Convert summary to dictionary
        results_data = {
            "summary": summary.to_dict(),
            "results": [
                result.to_dict() for result in getattr(summary, "_scan_results", [])
            ],
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "json":
            self._write_json(results_data, output_file, pretty_print)
        elif format.lower() == "yaml":
            self._write_yaml(results_data, output_file)
        elif format.lower() == "csv":
            self._write_csv(results_data, output_file)
        else:
            raise ValueError(f"Unsupported output format: {format}")

    def write_file_list(
        self,
        video_files: List[VideoFile],
        directory: Path,
        output_file: Path,
        format: str = "text",
    ) -> None:
        """
        Write file list to output file.

        Args:
            video_files: List of video files
            directory: Base directory for relative paths
            output_file: Path to output file
            format: Output format (text, json, csv)
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "text":
            self._write_file_list_text(video_files, directory, output_file)
        elif format.lower() == "json":
            self._write_file_list_json(video_files, directory, output_file)
        elif format.lower() == "csv":
            self._write_file_list_csv(video_files, directory, output_file)
        else:
            raise ValueError(f"Unsupported file list format: {format}")

    def _write_json(self, data: Dict[str, Any], output_file: Path, pretty_print: bool) -> None:
        """Write data as JSON."""
        with output_file.open("w", encoding="utf-8") as f:
            if pretty_print:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)

    def _write_yaml(self, data: Dict[str, Any], output_file: Path) -> None:
        """Write data as YAML."""
        with output_file.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def _write_csv(self, data: Dict[str, Any], output_file: Path) -> None:
        """Write scan results as CSV."""
        results = data.get("results", [])
        if not results:
            # Write empty CSV with headers
            with output_file.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "is_corrupt", "error_message", "inspection_time", "file_size"])
            return

        with output_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    def _write_file_list_text(self, video_files: List[VideoFile], directory: Path, output_file: Path) -> None:
        """Write file list as plain text."""
        with output_file.open("w", encoding="utf-8") as f:
            for video_file in video_files:
                rel_path = video_file.path.relative_to(directory)
                f.write(f"{rel_path}\n")

    def _write_file_list_json(self, video_files: List[VideoFile], directory: Path, output_file: Path) -> None:
        """Write file list as JSON."""
        files_data = []
        for video_file in video_files:
            rel_path = video_file.path.relative_to(directory)
            files_data.append({
                "path": str(rel_path),
                "full_path": str(video_file.path),
                "size": video_file.size,
                "duration": video_file.duration,
            })

        data = {
            "directory": str(directory),
            "total_files": len(video_files),
            "files": files_data,
        }

        with output_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _write_file_list_csv(self, video_files: List[VideoFile], directory: Path, output_file: Path) -> None:
        """Write file list as CSV."""
        with output_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["relative_path", "full_path", "size_bytes", "duration_seconds"])
            
            for video_file in video_files:
                rel_path = video_file.path.relative_to(directory)
                writer.writerow([
                    str(rel_path),
                    str(video_file.path),
                    video_file.size,
                    video_file.duration,
                ])