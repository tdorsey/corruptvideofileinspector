"""Report generation functionality for video corruption scans.

This module provides comprehensive reporting capabilities for scan results,
supporting multiple output formats and detailed analytics.
"""

import csv
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.config.config import AppConfig
from src.core.models.reporting import ReportConfiguration
from src.core.models.scanning import ScanResult, ScanSummary

logger = logging.getLogger(__name__)


@dataclass
class ReportMetadata:
    """Metadata for generated reports.

    Attributes:
        generated_at: Timestamp when report was generated
        tool_version: Version of the corruption inspector tool
        config_snapshot: Configuration used for the scan
        report_format: Format of the generated report
        total_results: Total number of scan results included
    """

    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tool_version: str = "2.0.0"
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    report_format: str = "json"
    total_results: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "tool_version": self.tool_version,
            "config_snapshot": self.config_snapshot,
            "report_format": self.report_format,
            "total_results": self.total_results,
        }


@dataclass
class ScanReport:
    """Complete scan report with results and analytics.

    Attributes:
        summary: Scan operation summary
        results: Individual scan results
        metadata: Report generation metadata
        analytics: Additional analytics and statistics
    """

    summary: ScanSummary
    results: List[ScanResult]
    metadata: ReportMetadata = field(default_factory=ReportMetadata)
    analytics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize analytics and metadata."""
        self.metadata.total_results = len(self.results)
        self._calculate_analytics()

    def _calculate_analytics(self) -> None:
        """Calculate additional analytics from scan results."""
        if not self.results:
            return

        # File size analytics
        sizes = [result.file_size for result in self.results]
        self.analytics["file_sizes"] = {
            "total_bytes": sum(sizes),
            "average_bytes": sum(sizes) / len(sizes),
            "min_bytes": min(sizes),
            "max_bytes": max(sizes),
            "total_gb": sum(sizes) / (1024**3),
        }

        # Scan time analytics
        scan_times = [result.inspection_time for result in self.results]
        self.analytics["scan_times"] = {
            "total_seconds": sum(scan_times),
            "average_seconds": sum(scan_times) / len(scan_times),
            "min_seconds": min(scan_times),
            "max_seconds": max(scan_times),
        }

        # Corruption confidence analytics
        corrupt_results = [r for r in self.results if r.is_corrupt]
        if corrupt_results:
            confidences = [r.confidence for r in corrupt_results]
            self.analytics["corruption_confidence"] = {
                "average": sum(confidences) / len(confidences),
                "min": min(confidences),
                "max": max(confidences),
                "high_confidence_count": len([c for c in confidences if c > 0.8]),
                "medium_confidence_count": len([c for c in confidences if 0.5 <= c <= 0.8]),
                "low_confidence_count": len([c for c in confidences if c < 0.5]),
            }

        # Extension analytics
        extensions = {}
        for result in self.results:
            ext = result.video_file.path.suffix.lower()
            if ext not in extensions:
                extensions[ext] = {"total": 0, "corrupt": 0, "healthy": 0}
            extensions[ext]["total"] += 1
            if result.is_corrupt:
                extensions[ext]["corrupt"] += 1
            else:
                extensions[ext]["healthy"] += 1

        self.analytics["file_extensions"] = extensions

        # Directory analytics
        directories = {}
        for result in self.results:
            parent = str(result.video_file.path.parent)
            if parent not in directories:
                directories[parent] = {"total": 0, "corrupt": 0, "healthy": 0}
            directories[parent]["total"] += 1
            if result.is_corrupt:
                directories[parent]["corrupt"] += 1
            else:
                directories[parent]["healthy"] += 1

        self.analytics["directories"] = directories

    def get_corrupt_files(self) -> List[ScanResult]:
        """Get only corrupt files from results."""
        return [result for result in self.results if result.is_corrupt]

    def get_healthy_files(self) -> List[ScanResult]:
        """Get only healthy files from results."""
        return [result for result in self.results if not result.is_corrupt]

    def get_suspicious_files(self) -> List[ScanResult]:
        """Get files that need deep scanning."""
        return [result for result in self.results if result.needs_deep_scan]

    def filter_by_confidence(self, min_confidence: float = 0.0) -> List[ScanResult]:
        """Filter results by minimum confidence level."""
        return [result for result in self.results if result.confidence >= min_confidence]

    def group_by_directory(self) -> Dict[str, List[ScanResult]]:
        """Group results by parent directory."""
        groups = {}
        for result in self.results:
            parent = str(result.video_file.path.parent)
            if parent not in groups:
                groups[parent] = []
            groups[parent].append(result)
        return groups

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return {
            "metadata": self.metadata.to_dict(),
            "summary": self.summary.to_dict(),
            "analytics": self.analytics,
            "results": [result.to_dict() for result in self.results],
        }


class ReportGenerator(ABC):
    """Abstract base class for report generators."""

    @abstractmethod
    def generate(self, report: ScanReport, config: ReportConfiguration) -> None:
        """Generate a report in the specific format.

        Args:
            report: The scan report to generate
            config: Report configuration
        """

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this report format."""


class JSONReportGenerator(ReportGenerator):
    """Generate JSON format reports."""

    def generate(self, report: ScanReport, config: ReportConfiguration) -> None:
        """Generate JSON report."""
        logger.info(f"Generating JSON report: {config.output_path}")

        report_data = report.to_dict()

        # Filter results based on configuration
        if not config.include_healthy:
            report_data["results"] = [r for r in report_data["results"] if r["is_corrupt"]]

        if not config.include_ffmpeg_output:
            for result in report_data["results"]:
                result.pop("ffmpeg_output", None)

        # Ensure output directory exists
        config.output_path.parent.mkdir(parents=True, exist_ok=True)

        with config.output_path.open("w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON report saved to: {config.output_path}")

    def get_file_extension(self) -> str:
        """Get JSON file extension."""
        return ".json"


class CSVReportGenerator(ReportGenerator):
    """Generate CSV format reports."""

    def generate(self, report: ScanReport, config: ReportConfiguration) -> None:
        """Generate CSV report."""
        logger.info(f"Generating CSV report: {config.output_path}")

        # Filter results
        results = report.results
        if not config.include_healthy:
            results = [r for r in results if r.is_corrupt]

        # Ensure output directory exists
        config.output_path.parent.mkdir(parents=True, exist_ok=True)

        with config.output_path.open("w", newline="", encoding="utf-8") as f:
            if not results:
                f.write("No results to export\n")
                return

            # Define CSV fields
            fieldnames = [
                "filename",
                "is_corrupt",
                "status",
                "confidence",
                "confidence_percentage",
                "file_size",
                "inspection_time",
                "scan_mode",
                "needs_deep_scan",
                "deep_scan_completed",
                "error_message",
                "timestamp",
            ]

            if config.include_ffmpeg_output:
                fieldnames.append("ffmpeg_output")

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                row = {
                    "filename": str(result.video_file.path),
                    "is_corrupt": result.is_corrupt,
                    "status": result.status,
                    "confidence": result.confidence,
                    "confidence_percentage": result.confidence_percentage,
                    "file_size": result.file_size,
                    "inspection_time": result.inspection_time,
                    "scan_mode": result.scan_mode.value,
                    "needs_deep_scan": result.needs_deep_scan,
                    "deep_scan_completed": result.deep_scan_completed,
                    "error_message": result.error_message,
                    "timestamp": datetime.fromtimestamp(result.timestamp).isoformat(),
                }

                if config.include_ffmpeg_output:
                    row["ffmpeg_output"] = result.ffmpeg_output

                writer.writerow(row)

        logger.info(f"CSV report saved to: {config.output_path}")

    def get_file_extension(self) -> str:
        """Get CSV file extension."""
        return ".csv"


class YAMLReportGenerator(ReportGenerator):
    """Generate YAML format reports."""

    def generate(self, report: ScanReport, config: ReportConfiguration) -> None:
        """Generate YAML report."""
        logger.info(f"Generating YAML report: {config.output_path}")

        report_data = report.to_dict()

        # Filter results based on configuration
        if not config.include_healthy:
            report_data["results"] = [r for r in report_data["results"] if r["is_corrupt"]]

        if not config.include_ffmpeg_output:
            for result in report_data["results"]:
                result.pop("ffmpeg_output", None)

        # Ensure output directory exists
        config.output_path.parent.mkdir(parents=True, exist_ok=True)

        with config.output_path.open("w", encoding="utf-8") as f:
            yaml.dump(report_data, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"YAML report saved to: {config.output_path}")

    def get_file_extension(self) -> str:
        """Get YAML file extension."""
        return ".yaml"


class TextReportGenerator(ReportGenerator):
    """Generate human-readable text format reports."""

    def generate(self, report: ScanReport, config: ReportConfiguration) -> None:
        """Generate text report."""
        logger.info(f"Generating text report: {config.output_path}")

        # Ensure output directory exists
        config.output_path.parent.mkdir(parents=True, exist_ok=True)

        with config.output_path.open("w", encoding="utf-8") as f:
            self._write_header(f, report)
            self._write_summary(f, report)
            self._write_analytics(f, report)
            self._write_results(f, report, config)

        logger.info(f"Text report saved to: {config.output_path}")

    def _write_header(self, f, report: ScanReport) -> None:
        """Write report header."""
        f.write("=" * 60 + "\n")
        f.write("CORRUPT VIDEO INSPECTOR - SCAN REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Generated: {report.metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Tool Version: {report.metadata.tool_version}\n")
        f.write(f"Total Results: {report.metadata.total_results}\n\n")

    def _write_summary(self, f, report: ScanReport) -> None:
        """Write scan summary."""
        f.write("SCAN SUMMARY\n")
        f.write("-" * 20 + "\n")
        f.write(f"Directory: {report.summary.directory}\n")
        f.write(f"Scan Mode: {report.summary.scan_mode.value.upper()}\n")
        f.write(f"Total Files: {report.summary.total_files}\n")
        f.write(f"Processed: {report.summary.processed_files}\n")
        f.write(f"Corrupt: {report.summary.corrupt_files}\n")
        f.write(f"Healthy: {report.summary.healthy_files}\n")
        f.write(f"Success Rate: {report.summary.success_rate:.1f}%\n")
        f.write(f"Scan Time: {report.summary.scan_time:.2f} seconds\n")
        f.write(f"Processing Rate: {report.summary.files_per_second:.1f} files/sec\n")

        if report.summary.deep_scans_needed > 0:
            f.write(f"Deep Scans Needed: {report.summary.deep_scans_needed}\n")
            f.write(f"Deep Scans Completed: {report.summary.deep_scans_completed}\n")

        if report.summary.was_resumed:
            f.write("Note: This scan was resumed from a previous session\n")

        f.write("\n")

    def _write_analytics(self, f, report: ScanReport) -> None:
        """Write analytics section."""
        f.write("ANALYTICS\n")
        f.write("-" * 20 + "\n")

        # File size analytics
        if "file_sizes" in report.analytics:
            sizes = report.analytics["file_sizes"]
            f.write(f"Total Data: {sizes['total_gb']:.2f} GB\n")
            f.write(f"Average File Size: {sizes['average_bytes'] / (1024**2):.1f} MB\n")

        # Extension breakdown
        if "file_extensions" in report.analytics:
            f.write("\nFile Extensions:\n")
            for ext, stats in report.analytics["file_extensions"].items():
                corruption_rate = (
                    (stats["corrupt"] / stats["total"]) * 100 if stats["total"] > 0 else 0
                )
                f.write(f"  {ext}: {stats['total']} files ({corruption_rate:.1f}% corrupt)\n")

        # Corruption confidence
        if "corruption_confidence" in report.analytics:
            conf = report.analytics["corruption_confidence"]
            f.write("\nCorruption Confidence:\n")
            f.write(f"  High (>80%): {conf['high_confidence_count']} files\n")
            f.write(f"  Medium (50-80%): {conf['medium_confidence_count']} files\n")
            f.write(f"  Low (<50%): {conf['low_confidence_count']} files\n")

        f.write("\n")

    def _write_results(self, f, report: ScanReport, config: ReportConfiguration) -> None:
        """Write detailed results."""
        # Filter results
        results = report.results
        if not config.include_healthy:
            results = [r for r in results if r.is_corrupt]

        if not results:
            f.write("No results to display\n")
            return

        f.write("DETAILED RESULTS\n")
        f.write("-" * 20 + "\n")

        # Sort results
        if config.sort_by == "path":
            results.sort(key=lambda r: str(r.video_file.path))
        elif config.sort_by == "size":
            results.sort(key=lambda r: r.file_size, reverse=True)
        elif config.sort_by == "corruption":
            results.sort(key=lambda r: r.is_corrupt, reverse=True)
        elif config.sort_by == "confidence":
            results.sort(key=lambda r: r.confidence, reverse=True)
        elif config.sort_by == "scan_time":
            results.sort(key=lambda r: r.inspection_time, reverse=True)

        for i, result in enumerate(results, 1):
            f.write(f"\n{i}. {result.video_file.path}\n")
            f.write(f"   Status: {result.status}\n")
            f.write(f"   Size: {result.file_size / (1024**2):.1f} MB\n")
            f.write(f"   Scan Time: {result.inspection_time:.2f}s\n")
            f.write(f"   Mode: {result.scan_mode.value}\n")

            if result.is_corrupt:
                f.write(f"   Confidence: {result.confidence_percentage:.1f}%\n")
                if result.error_message:
                    f.write(f"   Error: {result.error_message}\n")

            if result.needs_deep_scan:
                f.write(
                    f"   Deep Scan: {'Completed' if result.deep_scan_completed else 'Needed'}\n"
                )

    def get_file_extension(self) -> str:
        """Get text file extension."""
        return ".txt"


class ReportService:
    """Service for generating various types of corruption scan reports."""

    def __init__(self, config: AppConfig):
        """Initialize the report service.

        Args:
            config: Application configuration
        """
        self.config = config
        self._generators: Dict[str, ReportGenerator] = {
            "json": JSONReportGenerator(),
            "csv": CSVReportGenerator(),
            "yaml": YAMLReportGenerator(),
            "text": TextReportGenerator(),
        }

    def generate_report(
        self,
        summary: ScanSummary,
        results: List[ScanResult],
        output_path: Optional[Path] = None,
        format: str = "json",
        include_healthy: bool = False,
        include_metadata: bool = True,
        include_ffmpeg_output: bool = False,
        sort_by: str = "path",
    ) -> Path:
        """Generate a comprehensive scan report.

        Args:
            summary: Scan operation summary
            results: List of individual scan results
            output_path: Where to save the report (auto-generated if None)
            format: Report format (json, csv, yaml, text)
            include_healthy: Include healthy files in report
            include_metadata: Include file metadata
            include_ffmpeg_output: Include raw FFmpeg output
            sort_by: Field to sort results by

        Returns:
            Path to the generated report file

        Raises:
            ValueError: If format is not supported
            IOError: If report cannot be written
        """
        if format not in self._generators:
            raise ValueError(
                f"Unsupported format: {format}. Must be one of {list(self._generators.keys())}"
            )

        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"corruption_scan_{timestamp}{self._generators[format].get_file_extension()}"
            output_path = self.config.output.default_output_dir / filename

        # Create report data
        metadata = ReportMetadata(
            report_format=format,
            config_snapshot=self._get_config_snapshot(),
        )

        report = ScanReport(
            summary=summary,
            results=results,
            metadata=metadata,
        )

        # Create report configuration
        report_config = ReportConfiguration(
            output_path=output_path,
            format=format,
            include_healthy=include_healthy,
            include_metadata=include_metadata,
            include_ffmpeg_output=include_ffmpeg_output,
            sort_by=sort_by,
        )

        # Generate the report
        try:
            generator = self._generators[format]
            generator.generate(report, report_config)
            logger.info(f"Report generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.exception(f"Failed to generate {format} report")
            raise OSError(f"Failed to generate report: {e}") from e

    def generate_multiple_formats(
        self,
        summary: ScanSummary,
        results: List[ScanResult],
        formats: List[str],
        output_dir: Optional[Path] = None,
        **kwargs,
    ) -> Dict[str, Path]:
        """Generate reports in multiple formats.

        Args:
            summary: Scan operation summary
            results: List of individual scan results
            formats: List of formats to generate
            output_dir: Directory to save reports (uses config default if None)
            **kwargs: Additional arguments passed to generate_report

        Returns:
            Dictionary mapping format names to output file paths
        """
        if output_dir is None:
            output_dir = self.config.output.default_output_dir

        generated_reports = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for format in formats:
            if format not in self._generators:
                logger.warning(f"Skipping unsupported format: {format}")
                continue

            try:
                filename = (
                    f"corruption_scan_{timestamp}{self._generators[format].get_file_extension()}"
                )
                output_path = output_dir / filename

                generated_path = self.generate_report(
                    summary=summary,
                    results=results,
                    output_path=output_path,
                    format=format,
                    **kwargs,
                )

                generated_reports[format] = generated_path

            except Exception:
                logger.exception(f"Failed to generate {format} report")

        return generated_reports

    def _get_config_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of relevant configuration for the report."""
        return {
            "ffmpeg_command": str(self.config.ffmpeg.command),
            "quick_timeout": self.config.ffmpeg.quick_timeout,
            "deep_timeout": self.config.ffmpeg.deep_timeout,
            "max_workers": self.config.processing.max_workers,
            "default_mode": self.config.processing.default_mode,
            "extensions": self.config.scan.extensions,
            "recursive": self.config.scan.recursive,
        }

    def get_supported_formats(self) -> List[str]:
        """Get list of supported report formats."""
        return list(self._generators.keys())

    def validate_format(self, format: str) -> bool:
        """Check if a format is supported."""
        return format in self._generators


# Convenience functions for common report operations


def generate_json_report(
    summary: ScanSummary,
    results: List[ScanResult],
    output_path: Path,
    include_healthy: bool = False,
) -> None:
    """Generate a JSON report quickly.

    Args:
        summary: Scan summary
        results: Scan results
        output_path: Output file path
        include_healthy: Whether to include healthy files
    """
    generator = JSONReportGenerator()
    config = ReportConfiguration(
        output_path=output_path,
        format="json",
        include_healthy=include_healthy,
    )

    metadata = ReportMetadata(report_format="json")
    report = ScanReport(summary=summary, results=results, metadata=metadata)

    generator.generate(report, config)


def generate_csv_summary(
    summary: ScanSummary,
    results: List[ScanResult],
    output_path: Path,
) -> None:
    """Generate a CSV summary report (corrupt files only).

    Args:
        summary: Scan summary
        results: Scan results
        output_path: Output file path
    """
    generator = CSVReportGenerator()
    config = ReportConfiguration(
        output_path=output_path,
        format="csv",
        include_healthy=False,  # CSV summaries typically only show issues
    )

    metadata = ReportMetadata(report_format="csv")
    report = ScanReport(summary=summary, results=results, metadata=metadata)

    generator.generate(report, config)
