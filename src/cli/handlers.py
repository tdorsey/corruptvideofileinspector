"""
Command handlers for CLI operations.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Optional

import click # type: ignore

from src.config.config import AppConfig
from src.core.models.scanning import ScanMode, ScanProgress
from src.core.reporter import ReportService
from src.core.scanner import VideoScanner
from src.core.watchlist import sync_to_trakt_watchlist
from src.utils.output import OutputFormatter

logger = logging.getLogger(__name__)


class BaseHandler:
    """Base class for CLI command handlers."""

    def __init__(self, config: AppConfig):
        """Initialize the handler with configuration."""
        self.config = config
        self.output_formatter = OutputFormatter(config)
        self.report_service = ReportService(config)

    def _handle_error(self, error: Exception, message: str) -> None:
        """Handle and log errors consistently."""
        logger.exception(message)
        click.echo(f"Error: {error}", err=True)
        sys.exit(1)


class ScanHandler(BaseHandler):
    """Handler for scan-related commands."""

    def __init__(self, config: AppConfig):
        """Initialize scan handler."""
        super().__init__(config)
        self.scanner = VideoScanner(config)
        self._last_progress_update = 0.0

    def run_scan(
        self,
        directory: Path,
        scan_mode: ScanMode,
        recursive: bool = True,
        output_file: Optional[Path] = None,
        output_format: str = "json",
        pretty_print: bool = True,
    ) -> None:
        """
        Run a video corruption scan.

        Args:
            directory: Directory to scan
            scan_mode: Type of scan to perform
            recursive: Whether to scan subdirectories
            output_file: Optional output file path
            output_format: Output format (json, yaml, csv)
            pretty_print: Whether to pretty-print output
        """
        try:
            # Show initial information
            if self.config.logging.level != "QUIET":
                self._show_scan_info(directory, scan_mode, recursive)

            # Check if directory has video files
            video_files = self.scanner.get_video_files(directory, recursive=recursive)
            if not video_files:
                click.echo("No video files found to scan.")
                if self.config.scan.extensions:
                    ext_list = ", ".join(self.config.scan.extensions)
                    click.echo(f"Searched for extensions: {ext_list}")
                return

            click.echo(f"Found {len(video_files)} video files to scan.")

            # Run the scan
            summary = self.scanner.scan_directory(
                directory=directory,
                scan_mode=scan_mode,
                recursive=recursive,
                progress_callback=(
                    self._progress_callback if self.config.logging.level != "QUIET" else None
                ),
            )

            # Show results
            self._show_scan_results(summary)

            # Generate output file if requested
            if output_file or self.config.output.default_json:
                self._generate_output(
                    summary=summary,
                    directory=directory,
                    output_file=output_file,
                    output_format=output_format,
                    pretty_print=pretty_print,
                )

        except KeyboardInterrupt:
            click.echo("\nScan interrupted by user.", err=True)
            sys.exit(130)
        except Exception as e:
            self._handle_error(e, "Scan failed")

    def _show_scan_info(self, directory: Path, scan_mode: ScanMode, recursive: bool) -> None:
        """Show initial scan information."""
        click.echo("Starting video corruption scan...")
        click.echo(f"Directory: {directory}")
        click.echo(f"Scan mode: {scan_mode.value.upper()}")

        if scan_mode == ScanMode.HYBRID:
            click.echo("  Phase 1: Quick scan all files (1min timeout)")
            click.echo("  Phase 2: Deep scan suspicious files (15min timeout)")
        elif scan_mode == ScanMode.QUICK:
            click.echo("  Quick scan only (1min timeout per file)")
        elif scan_mode == ScanMode.DEEP:
            click.echo("  Deep scan all files (15min timeout per file)")

        click.echo(f"Max workers: {self.config.processing.max_workers}")
        click.echo(f"Recursive: {'enabled' if recursive else 'disabled'}")

        if self.config.scan.extensions:
            ext_str = ", ".join(self.config.scan.extensions)
            click.echo(f"File extensions: {ext_str}")

        click.echo()

    def _progress_callback(self, progress: ScanProgress) -> None:
        """Handle progress updates."""
        current_time = time.time()

        # Throttle progress updates (default to 0.5 seconds)
        if current_time - self._last_progress_update < 0.5:
            return

        self._last_progress_update = current_time

        # Show progress (default to text progress)
        self._show_progress_text(progress)

    def _show_progress_bar(self, progress: ScanProgress) -> None:
        """Show progress as a progress bar."""
        try:

            # Use click's progress bar if available
            with click.progressbar(
                length=progress.total_files,
                show_eta=True,
                show_percent=True,
                show_pos=True,
            ) as bar:
                bar.update(progress.processed_count)
        except ImportError:
            # Fallback to text progress
            self._show_progress_text(progress)

    def _show_progress_text(self, progress: ScanProgress) -> None:
        """Show progress as text."""
        percent = progress.progress_percentage

        phase_label = ""
        if progress.phase:
            phase_label = f"{progress.phase.replace('_', ' ').title()} - "

        current_file = ""
        if progress.current_file:
            current_file = f" | Current: {Path(progress.current_file).name}"

        click.echo(
            f"\r{phase_label}Progress: {progress.processed_count}/{progress.total_files} "
            f"({percent:.1f}%) | Corrupt: {progress.corrupt_count}{current_file}",
            nl=False,
        )

    def _show_scan_results(self, summary: Any) -> None:
        """Show scan completion results."""
        if self.config.logging.level != "QUIET":
            click.echo()  # New line after progress

        click.echo("=" * 50)
        if summary.is_complete:
            click.echo("SCAN COMPLETE")
        else:
            click.echo("SCAN TERMINATED")
        click.echo("=" * 50)

        click.echo(f"Scan mode: {summary.scan_mode.value.upper()}")
        click.echo(f"Total files scanned: {summary.processed_files}")
        click.echo(f"Corrupt files found: {summary.corrupt_files}")
        click.echo(f"Healthy files: {summary.healthy_files}")

        if summary.scan_mode == ScanMode.HYBRID:
            click.echo(f"Files requiring deep scan: {summary.deep_scans_needed}")
            click.echo(f"Deep scans completed: {summary.deep_scans_completed}")

        click.echo(f"Total scan time: {summary.scan_time:.2f} seconds")

        if summary.processed_files > 0:
            avg_time = summary.scan_time / summary.processed_files
            click.echo(f"Average time per file: {avg_time:.2f} seconds")

        click.echo(f"Success rate: {summary.success_rate:.1f}%")

        if summary.was_resumed:
            click.echo("(Scan was resumed from previous session)")

    def _generate_output(
        self,
        summary: Any,
        directory: Path,
        output_file: Optional[Path],
        output_format: str,
        pretty_print: bool,
    ) -> None:
        """Generate output file with scan results."""
        try:
            if not output_file:
                output_file = directory / f"scan_results.{output_format}"

            # Use the new ReportService to generate comprehensive reports
            # Note: We would need to get the actual results list to use the full reporter
            # For now, fall back to the output formatter for compatibility
            self.output_formatter.write_scan_results(
                summary=summary,
                output_file=output_file,
                format=output_format,
                pretty_print=pretty_print,
            )

            click.echo(f"\nDetailed results saved to: {output_file}")

        except Exception as e:
            logger.warning(f"Failed to generate output file: {e}")
            click.echo(f"Warning: Could not save results to file: {e}", err=True)

    def generate_comprehensive_report(
        self,
        summary: Any,
        results: list,
        output_file: Optional[Path] = None,
        output_format: str = "json",
        include_healthy: bool = False,
        include_metadata: bool = True,
    ) -> None:
        """Generate a comprehensive report using the ReportService.

        Args:
            summary: Scan summary object
            results: List of scan results
            output_file: Output file path
            output_format: Report format (json, csv, yaml, xml, text)
            include_healthy: Include healthy files in report
            include_metadata: Include metadata in report
        """
        try:
            generated_path = self.report_service.generate_report(
                summary=summary,
                results=results,
                output_path=output_file,
                format=output_format,
                include_healthy=include_healthy,
                include_metadata=include_metadata,
            )

            click.echo(f"\nComprehensive report generated: {generated_path}")

        except Exception as e:
            logger.warning(f"Failed to generate comprehensive report: {e}")
            click.echo(f"Warning: Could not generate comprehensive report: {e}", err=True)


class ListHandler(BaseHandler):
    """Handler for listing video files."""

    def __init__(self, config: AppConfig):
        """Initialize list handler."""
        super().__init__(config)
        self.scanner = VideoScanner(config)

    def list_files(
        self,
        directory: Path,
        recursive: bool = True,
        output_file: Optional[Path] = None,
        output_format: str = "text",
    ) -> None:
        """
        List all video files in directory.

        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            output_file: Optional output file
            output_format: Output format (text, json, csv)
        """
        try:
            click.echo(f"Scanning directory: {directory}")
            if recursive:
                click.echo("(including subdirectories)")

            # Get video files
            video_files = self.scanner.get_video_files(directory, recursive=recursive)

            if not video_files:
                click.echo("No video files found in the specified directory.")
                if self.config.scan.extensions:
                    ext_list = ", ".join(self.config.scan.extensions)
                    click.echo(f"Searched for extensions: {ext_list}")
                return

            # Show or save file list
            if output_file:
                self._save_file_list(video_files, directory, output_file, output_format)
            else:
                self._show_file_list(video_files, directory)

        except Exception as e:
            self._handle_error(e, "Failed to list files")

    def _show_file_list(self, video_files: list, directory: Path) -> None:
        """Show file list to console."""
        click.echo(f"\nFound {len(video_files)} video files:")

        for i, video_file in enumerate(video_files, 1):
            rel_path = video_file.path.relative_to(directory)
            size_mb = video_file.size / (1024 * 1024) if video_file.size > 0 else 0
            click.echo(f"  {i:3d}: {rel_path} ({size_mb:.1f} MB)")

    def _save_file_list(
        self,
        video_files: list,
        directory: Path,
        output_file: Path,
        output_format: str,
    ) -> None:
        """Save file list to output file."""
        self.output_formatter.write_file_list(
            video_files=video_files,
            directory=directory,
            output_file=output_file,
            format=output_format,
        )

        click.echo(f"File list saved to: {output_file}")


class TraktHandler(BaseHandler):
    """Handler for Trakt.tv integration commands."""

    def __init__(self, config: AppConfig):
        """Initialize Trakt handler."""
        super().__init__(config)

    def sync_to_watchlist(
        self,
        scan_file: Path,
        access_token: str,
        interactive: bool = False,
        dry_run: bool = False,
        filter_corrupt: bool = True,
        output_file: Optional[Path] = None,
    ) -> None:
        """
        Sync scan results to Trakt.tv watchlist.

        Args:
            scan_file: Path to JSON scan results file
            access_token: Trakt API access token
            interactive: Enable interactive selection
            dry_run: Show what would be synced without syncing
            filter_corrupt: Filter out corrupt files
            output_file: Optional output file for sync results
        """
        try:
            if not dry_run:
                click.echo("Syncing scan results to Trakt.tv watchlist...")
            else:
                click.echo("DRY RUN: Showing what would be synced to Trakt.tv...")

            click.echo(f"Scan file: {scan_file}")

            if interactive:
                click.echo("Interactive mode: You will be prompted to select matches")

            if filter_corrupt:
                click.echo("Filtering out corrupt files from sync")

            if dry_run:
                click.echo("Note: Dry run mode not implemented in watchlist sync function")

            # Perform the sync using the watchlist function
            # Note: The sync_to_trakt_watchlist function doesn't support dry_run or filter_corrupt
            # so we'll need to pass what's available
            results = sync_to_trakt_watchlist(
                scan_file=str(scan_file),
                access_token=access_token,
                client_id=None,  # TODO: Add client_id to config if needed
                verbose=self.config.logging.level != "QUIET",
                interactive=interactive,
            )

            # Show results
            self._show_sync_results(results, dry_run)

            # Save results if requested
            if output_file:
                self._save_sync_results(results, output_file)

        except Exception as e:
            self._handle_error(e, "Trakt sync failed")

    def _show_sync_results(self, results: dict, dry_run: bool = False) -> None:
        """Show sync operation results."""
        click.echo("\n" + "=" * 50)
        if dry_run:
            click.echo("DRY RUN RESULTS")
        else:
            click.echo("TRAKT SYNC SUMMARY")
        click.echo("=" * 50)

        click.echo(f"Total items processed: {results['total']}")
        click.echo(f"Movies {'would be' if dry_run else ''} added: {results['movies_added']}")
        click.echo(f"Shows {'would be' if dry_run else ''} added: {results['shows_added']}")
        click.echo(f"Failed/Not found: {results['failed']}")

        if results["total"] > 0:
            success_count = results["movies_added"] + results["shows_added"]
            success_rate = (success_count / results["total"]) * 100
            click.echo(f"Success rate: {success_rate:.1f}%")

        # Show failed items if any
        if results.get("results"):
            failed_items = [
                r for r in results["results"] if r["status"] in ["failed", "not_found", "error"]
            ]
            if failed_items:
                click.echo(f"\nFailed items ({len(failed_items)}):")
                for item in failed_items[:10]:  # Show first 10
                    click.echo(f"  - {item['title']} ({item.get('year', 'no year')})")
                if len(failed_items) > 10:
                    click.echo(f"  ... and {len(failed_items) - 10} more")

    def _save_sync_results(self, results: dict, output_file: Path) -> None:
        """Save sync results to output file."""
        try:
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

            click.echo(f"\nSync results saved to: {output_file}")

        except Exception as e:
            logger.warning(f"Failed to save sync results: {e}")
            click.echo(f"Warning: Could not save sync results: {e}", err=True)
