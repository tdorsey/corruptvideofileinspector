"""
Command handlers for CLI operations.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import click

from ..config.settings import AppConfig
from ..core.models import ScanMode, ScanProgress
from ..core.scanner import VideoScanner
from ..integrations.trakt.sync import TraktSyncService
from ..utils.output import OutputFormatter

logger = logging.getLogger(__name__)


class BaseHandler:
    """Base class for CLI command handlers."""

    def __init__(self, config: AppConfig):
        """Initialize the handler with configuration."""
        self.config = config
        self.output_formatter = OutputFormatter(config)

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
        resume: bool = True,
        output_file: Optional[Path] = None,
        output_format: str = "json",
        pretty_print: bool = True,
        sync_corrupt_to_trakt: bool = False,
        trakt_token: Optional[str] = None,
        trakt_interactive: bool = False,
    ) -> None:
        """
        Run a video corruption scan.

        Args:
            directory: Directory to scan
            scan_mode: Type of scan to perform
            recursive: Whether to scan subdirectories
            resume: Whether to resume from previous scan
            output_file: Optional output file path
            output_format: Output format (json, yaml, csv)
            pretty_print: Whether to pretty-print output
            sync_corrupt_to_trakt: Whether to sync corrupted files to Trakt.tv after scan
            trakt_token: Trakt.tv access token for API access
            trakt_interactive: Whether to use interactive mode for Trakt sync
        """
        try:
            # Show initial information
            if not self.config.logging.level == "QUIET":
                self._show_scan_info(directory, scan_mode, recursive)

            # Check if directory has video files
            video_files = self.scanner.get_video_files(directory, recursive)
            if not video_files:
                click.echo("No video files found to scan.")
                if self.config.scanner.extensions:
                    ext_list = ", ".join(self.config.scanner.extensions)
                    click.echo(f"Searched for extensions: {ext_list}")
                return

            click.echo(f"Found {len(video_files)} video files to scan.")

            # Run the scan
            summary = self.scanner.scan_directory(
                directory=directory,
                scan_mode=scan_mode,
                recursive=recursive,
                resume=resume,
                progress_callback=(
                    self._progress_callback
                    if not self.config.logging.level == "QUIET"
                    else None
                ),
            )

            # Show results
            self._show_scan_results(summary)

            # Generate output file if requested
            actual_output_file = output_file
            if output_file or self.config.output.default_json:
                actual_output_file = self._generate_output(
                    summary=summary,
                    directory=directory,
                    output_file=output_file,
                    output_format=output_format,
                    pretty_print=pretty_print,
                )

            # Sync corrupted files to Trakt.tv if requested
            if sync_corrupt_to_trakt and summary.corrupt_files > 0:
                self._sync_corrupt_to_trakt(
                    output_file=actual_output_file,
                    trakt_token=trakt_token,
                    interactive=trakt_interactive,
                )

        except KeyboardInterrupt:
            click.echo("\nScan interrupted by user.", err=True)
            sys.exit(130)
        except Exception as e:
            self._handle_error(e, "Scan failed")

    def _show_scan_info(
        self, directory: Path, scan_mode: ScanMode, recursive: bool
    ) -> None:
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

        click.echo(f"Max workers: {self.config.scanner.max_workers}")
        click.echo(f"Recursive: {'enabled' if recursive else 'disabled'}")

        if self.config.scanner.extensions:
            ext_str = ", ".join(self.config.scanner.extensions)
            click.echo(f"File extensions: {ext_str}")

        click.echo()

    def _progress_callback(self, progress: ScanProgress) -> None:
        """Handle progress updates."""
        current_time = time.time()

        # Throttle progress updates
        if (
            current_time - self._last_progress_update
            < self.config.ui.progress_update_interval
        ):
            return

        self._last_progress_update = current_time

        # Show progress
        if self.config.ui.show_progress_bar:
            self._show_progress_bar(progress)
        else:
            self._show_progress_text(progress)

    def _show_progress_bar(self, progress: ScanProgress) -> None:
        """Show progress as a progress bar."""
        try:
            import click

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

    def _show_scan_results(self, summary) -> None:
        """Show scan completion results."""
        if not self.config.logging.level == "QUIET":
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
        summary,
        directory: Path,
        output_file: Optional[Path],
        output_format: str,
        pretty_print: bool,
    ) -> Path:
        """Generate output file with scan results and return the actual file path."""
        try:
            if not output_file:
                output_file = directory / f"scan_results.{output_format}"

            # Use output formatter to create the file
            self.output_formatter.write_scan_results(
                summary=summary,
                output_file=output_file,
                format=output_format,
                pretty_print=pretty_print,
            )

            click.echo(f"\nDetailed results saved to: {output_file}")
            return output_file

        except Exception as e:
            logger.warning(f"Failed to generate output file: {e}")
            click.echo(f"Warning: Could not save results to file: {e}", err=True)
            # Return a fallback path
            return directory / f"scan_results.{output_format}"

    def _sync_corrupt_to_trakt(
        self,
        output_file: Optional[Path],
        trakt_token: Optional[str],
        interactive: bool = False,
    ) -> None:
        """Sync corrupted files to Trakt.tv watchlist."""
        if not output_file or not output_file.exists():
            click.echo("Warning: Cannot sync to Trakt - no scan results file available", err=True)
            return

        if not trakt_token:
            click.echo("Warning: Cannot sync to Trakt - no access token provided", err=True)
            click.echo("Use --trakt-token option or set TRAKT_ACCESS_TOKEN environment variable")
            return

        try:
            # Import TraktSyncService here to avoid circular imports
            from ..integrations.trakt.sync import TraktSyncService
            
            click.echo("\n" + "=" * 50)
            click.echo("SYNCING CORRUPTED FILES TO TRAKT.TV")
            click.echo("=" * 50)
            
            trakt_service = TraktSyncService(self.config)
            
            results = trakt_service.sync_corrupt_files(
                scan_file=output_file,
                access_token=trakt_token,
                interactive=interactive,
                dry_run=False,
            )
            
            # Show sync results
            total = results.get("total", 0)
            movies_added = results.get("movies_added", 0)
            shows_added = results.get("shows_added", 0)
            failed = results.get("failed", 0)
            
            click.echo(f"Total corrupted files processed: {total}")
            click.echo(f"Movies added to watchlist: {movies_added}")
            click.echo(f"Shows added to watchlist: {shows_added}")
            click.echo(f"Failed/Not found: {failed}")
            
            if total > 0:
                success_rate = ((movies_added + shows_added) / total) * 100
                click.echo(f"Success rate: {success_rate:.1f}%")
            
            click.echo("Trakt.tv sync completed!")
            
        except ImportError:
            click.echo("Warning: Trakt.py not available. Install with: pip install 'corrupt-video-inspector[trakt]'", err=True)
        except Exception as e:
            logger.exception("Failed to sync corrupted files to Trakt.tv")
            click.echo(f"Error syncing to Trakt.tv: {e}", err=True)


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
            video_files = self.scanner.get_video_files(directory, recursive)

            if not video_files:
                click.echo("No video files found in the specified directory.")
                if self.config.scanner.extensions:
                    ext_list = ", ".join(self.config.scanner.extensions)
                    click.echo(f"Searched for extensions: {ext_list}")
                return

            # Show or save file list
            if output_file:
                self._save_file_list(video_files, directory, output_file, output_format)
            else:
                self._show_file_list(video_files, directory)

        except Exception as e:
            self._handle_error(e, "Failed to list files")

    def _show_file_list(self, video_files, directory: Path) -> None:
        """Show file list to console."""
        click.echo(f"\nFound {len(video_files)} video files:")

        for i, video_file in enumerate(video_files, 1):
            rel_path = video_file.path.relative_to(directory)
            size_mb = video_file.size / (1024 * 1024) if video_file.size > 0 else 0
            click.echo(f"  {i:3d}: {rel_path} ({size_mb:.1f} MB)")

    def _save_file_list(
        self, video_files, directory: Path, output_file: Path, output_format: str
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
        self.trakt_service = TraktSyncService(config)

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

            # Perform the sync
            results = self.trakt_service.sync_scan_results(
                scan_file=scan_file,
                access_token=access_token,
                interactive=interactive,
                dry_run=dry_run,
                filter_corrupt=filter_corrupt,
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
        click.echo(
            f"Movies {'would be' if dry_run else ''} added: {results['movies_added']}"
        )
        click.echo(
            f"Shows {'would be' if dry_run else ''} added: {results['shows_added']}"
        )
        click.echo(f"Failed/Not found: {results['failed']}")

        if results["total"] > 0:
            success_count = results["movies_added"] + results["shows_added"]
            success_rate = (success_count / results["total"]) * 100
            click.echo(f"Success rate: {success_rate:.1f}%")

        # Show failed items if any
        if results.get("results"):
            failed_items = [
                r
                for r in results["results"]
                if r["status"] in ["failed", "not_found", "error"]
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
