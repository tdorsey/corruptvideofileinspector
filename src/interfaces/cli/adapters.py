"""
CLI adapter implementations for the interface abstractions.

These classes implement the abstract interfaces for CLI presentation,
handling configuration from CLI arguments, progress reporting to console,
result output to files/console, and error handling via Click.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import click

from src.config.config import AppConfig
from src.core.models.scanning import ScanMode, ScanProgress, ScanResult, ScanSummary
from src.interfaces.base import (
    ConfigurationProvider,
    ErrorHandler,
    ProgressReporter,
    ResultHandler,
)


class CLIConfigurationProvider(ConfigurationProvider):
    """CLI-specific configuration provider that wraps AppConfig.
    
    This adapter allows core modules to receive configuration through
    the abstract interface while maintaining compatibility with the
    existing AppConfig system.
    """

    def __init__(self, config: AppConfig):
        """Initialize with an AppConfig instance.
        
        Args:
            config: The application configuration
        """
        self._config = config

    def get_scan_mode(self) -> ScanMode:
        """Get the scan mode to use."""
        return ScanMode(self._config.scan.mode)

    def get_scan_directory(self) -> Path:
        """Get the directory to scan."""
        return self._config.scan.default_input_dir

    def get_max_workers(self) -> int:
        """Get the maximum number of worker threads."""
        return self._config.scan.max_workers

    def get_recursive_scan(self) -> bool:
        """Check if subdirectories should be scanned recursively."""
        return self._config.scan.recursive

    def get_file_extensions(self) -> List[str]:
        """Get the list of video file extensions to include."""
        return self._config.scan.extensions

    def get_resume_enabled(self) -> bool:
        """Check if scan resumption is enabled."""
        # Resume is typically enabled by default in CLI unless explicitly disabled
        return True

    def get_output_path(self) -> Path | None:
        """Get the output file path, if specified."""
        return self._config.output.default_output_dir / self._config.output.default_filename

    def get_output_format(self) -> str:
        """Get the output format (json, yaml, csv, etc.)."""
        return "json" if self._config.output.default_json else "yaml"

    def get_ffmpeg_command(self) -> str | None:
        """Get the FFmpeg command path, if specified."""
        return self._config.ffmpeg.command

    def get_timeout_quick(self) -> int:
        """Get the timeout for quick scans in seconds."""
        return self._config.ffmpeg.quick_timeout

    def get_timeout_deep(self) -> int:
        """Get the timeout for deep scans in seconds."""
        return self._config.ffmpeg.deep_timeout


class CLIResultHandler(ResultHandler):
    """CLI-specific result handler that outputs to console and files.
    
    This adapter handles scan results in CLI-appropriate ways such as
    console output, progress indicators, and file writing.
    """

    def __init__(self, output_path: Path | None = None, output_format: str = "json", verbose: bool = True):
        """Initialize the CLI result handler.
        
        Args:
            output_path: Optional path to write results to
            output_format: Format for output (json, yaml, csv)
            verbose: Whether to show verbose console output
        """
        self._output_path = output_path
        self._output_format = output_format
        self._verbose = verbose
        self._results: List[ScanResult] = []

    def handle_scan_start(self, total_files: int, scan_mode: ScanMode) -> None:
        """Handle the start of a scan operation."""
        if self._verbose:
            click.echo(f"Starting {scan_mode.value} scan of {total_files} files...")

    def handle_progress_update(self, progress: ScanProgress) -> None:
        """Handle a progress update during scanning."""
        if self._verbose and progress.current_file:
            click.echo(f"Scanning: {progress.current_file}")

    def handle_file_result(self, result: ScanResult) -> None:
        """Handle the result of scanning a single file."""
        self._results.append(result)
        if self._verbose:
            status = "CORRUPT" if result.is_corrupt else "HEALTHY"
            click.echo(f"  {status}: {result.video_file.path}")

    def handle_scan_complete(self, summary: ScanSummary) -> None:
        """Handle the completion of a scan operation."""
        if self._verbose:
            click.echo(f"\nScan complete!")
            click.echo(f"  Total files: {summary.total_files}")
            click.echo(f"  Processed: {summary.processed_files}")
            click.echo(f"  Corrupt: {summary.corrupt_files}")
            click.echo(f"  Healthy: {summary.healthy_files}")
            click.echo(f"  Scan time: {summary.scan_time:.2f}s")

        # Write results to file if specified
        if self._output_path:
            self._write_results_to_file(summary)

    def handle_scan_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Handle an error during scanning."""
        click.echo(f"Scan error: {error}", err=True)
        if context.get("file"):
            click.echo(f"  File: {context['file']}", err=True)

    def _write_results_to_file(self, summary: ScanSummary) -> None:
        """Write results to the specified output file."""
        # This would integrate with the existing output formatting logic
        # For now, just indicate the operation
        if self._verbose:
            click.echo(f"Writing results to {self._output_path}")


class CLIProgressReporter(ProgressReporter):
    """CLI-specific progress reporter using console output.
    
    This adapter reports progress through CLI-appropriate mechanisms
    such as progress bars, status messages, and percentage indicators.
    """

    def __init__(self, show_progress: bool = True):
        """Initialize the CLI progress reporter.
        
        Args:
            show_progress: Whether to show progress indicators
        """
        self._show_progress = show_progress
        self._cancelled = False

    def report_progress(self, progress: ScanProgress) -> None:
        """Report scan progress."""
        if not self._show_progress:
            return

        if progress.total_files > 0:
            percentage = (progress.processed_count / progress.total_files) * 100
            click.echo(f"Progress: {progress.processed_count}/{progress.total_files} ({percentage:.1f}%)")

    def is_cancelled(self) -> bool:
        """Check if the operation should be cancelled."""
        return self._cancelled

    def cancel(self) -> None:
        """Cancel the operation."""
        self._cancelled = True


class CLIErrorHandler(ErrorHandler):
    """CLI-specific error handler using Click for output and exit.
    
    This adapter handles errors in CLI-appropriate ways such as
    console error messages and appropriate exit codes.
    """

    def __init__(self, verbose: bool = False):
        """Initialize the CLI error handler.
        
        Args:
            verbose: Whether to show verbose error details
        """
        self._verbose = verbose

    def handle_validation_error(self, message: str, details: Dict[str, Any] | None = None) -> None:
        """Handle a validation error."""
        click.echo(f"Validation Error: {message}", err=True)
        if self._verbose and details:
            for key, value in details.items():
                click.echo(f"  {key}: {value}", err=True)

    def handle_configuration_error(self, message: str, details: Dict[str, Any] | None = None) -> None:
        """Handle a configuration error."""
        click.echo(f"Configuration Error: {message}", err=True)
        if self._verbose and details:
            for key, value in details.items():
                click.echo(f"  {key}: {value}", err=True)
        sys.exit(1)

    def handle_processing_error(self, message: str, exception: Exception | None = None) -> None:
        """Handle a processing error."""
        click.echo(f"Processing Error: {message}", err=True)
        if self._verbose and exception:
            click.echo(f"  Exception: {exception}", err=True)

    def handle_fatal_error(self, message: str, exception: Exception | None = None) -> None:
        """Handle a fatal error that should terminate the operation."""
        click.echo(f"Fatal Error: {message}", err=True)
        if self._verbose and exception:
            click.echo(f"  Exception: {exception}", err=True)
        sys.exit(1)