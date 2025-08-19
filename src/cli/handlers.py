"""
Command handlers for CLI operations.
"""

import importlib.util
import json
import logging
import os
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from shutil import which
from typing import Any

import click
import typer
from pydantic import BaseModel, Field

from src.cli.credential_utils import handle_credential_error
from src.config import load_config
from src.config.config import AppConfig
from src.core.credential_validator import validate_trakt_secrets
from src.core.models.inspection import VideoFile
from src.core.models.scanning import (
    FileStatus,
    ScanMode,
    ScanProgress,
    ScanResult,
    ScanSummary,
)
from src.core.reporter import ReportService
from src.core.scanner import VideoScanner
from src.core.watchlist import (
    TraktAPI,
    authenticate_trakt_oauth,
    sync_to_trakt_watchlist,
    test_trakt_authentication,
)
from src.output import OutputFormatter

logger = logging.getLogger(__name__)


class BaseHandler:
    """Base class for CLI command handlers."""

    def __init__(self, config: AppConfig):
        """Initialize the handler with configuration."""
        self.config = config
        self.output_formatter = OutputFormatter(config)
        self.report_service = ReportService(config)

    def _handle_error(self, error: Exception, message: str) -> None:
        """Handle errors consistently across handlers."""
        logger.error(f"{message}: {error}")
        click.echo(f"Error: {message}: {error}", err=True)

        # In test environments, raise the error instead of exiting
        # This allows tests to catch and validate exceptions
        if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
            if isinstance(error, ValueError | KeyError | FileNotFoundError):
                raise error
            msg = f"{message}: {error}"
            raise RuntimeError(msg)

        sys.exit(1)


class ScanHandler(BaseHandler):
    def __init__(self, config: AppConfig):
        """Initialize scan handler."""
        super().__init__(config)
        self.scanner = VideoScanner(config)
        self._last_progress_update = 0.0
        self._scan_message_printed: bool = False

    def run_scan(
        self,
        directory: Path,
        scan_mode: ScanMode,
        recursive: bool = True,
        resume: bool = True,
        output_file: Path | None = None,
        output_format: str = "json",
        pretty_print: bool = True,
    ) -> ScanSummary | None:
        """
        Run a video corruption scan and return ScanSummary.
        Results are automatically stored in the database if enabled.
        
        Args:
            directory: Directory to scan
            scan_mode: Scan mode to use
            recursive: Whether to scan recursively
            resume: Whether to resume interrupted scans
            output_file: Optional output file path
            output_format: Output file format (json, yaml, csv)
            pretty_print: Whether to pretty-print output files
        """
        try:
            video_files = self.scanner.get_video_files(directory, recursive=recursive)
            if not video_files:
                logger.info("No video files found to scan.")
                return None
            logger.info(f"Found {len(video_files)} video files to scan.")
            
            summary = self.scanner.scan_directory(
                directory=directory,
                scan_mode=scan_mode,
                recursive=recursive,
                resume=resume,
                progress_callback=(
                    self._progress_callback if self.config.logging.level != "QUIET" else None
                ),
            )
            
            # Store results using OutputFormatter (handles both database and file output)
            if output_file or self.config.database.enabled:
                self.output_formatter.write_scan_results(
                    summary=summary,
                    output_file=output_file,
                    format=output_format,
                    pretty_print=pretty_print,
                    store_in_database=self.config.database.enabled,
                )
                
                if self.config.database.enabled:
                    logger.info("Scan results stored in database")
                if output_file:
                    logger.info(f"Scan results written to {output_file}")
            else:
                logger.warning("No storage configured - scan results will not be persisted")
            
            return summary
        except KeyboardInterrupt:
            logger.warning("Scan interrupted by user.")
            sys.exit(130)
        except Exception as e:
            self._handle_error(e, "Scan failed")
            return None

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
        self._show_progress_bar(progress)

    def _show_progress_bar(self, progress: ScanProgress) -> None:
        """Show progress as a progress bar."""
        bar: Any = click.progressbar(
            length=progress.total_files,
            show_eta=True,
            show_percent=True,
            show_pos=True,
        )
        with bar:
            bar.update(progress.processed_count)

    def _show_scan_results(self, summary: ScanSummary) -> None:
        """Show scan completion results, only once per scan.

        Args:
            summary: ScanSummary Pydantic model containing scan results.
        """
        if self._scan_message_printed:
            return
        self._scan_message_printed = True
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

    def generate_comprehensive_report(
        self,
        summary: ScanSummary,
        results: list[ScanResult],
        output_file: Path | None = None,
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
    ) -> list[VideoFile]:
        """
        List all video files in directory and return list of VideoFile Pydantic models.
        """
        try:
            video_files = self.scanner.get_video_files(directory, recursive=recursive)
            if not video_files:
                logger.info("No video files found in the specified directory.")
                return []
            logger.info(f"Found {len(video_files)} video files in directory {directory}.")
            # Convert to VideoFile Pydantic models if not already
            video_file_models = [
                vf if isinstance(vf, VideoFile) else VideoFile(path=vf) for vf in video_files
            ]
            return video_file_models
        except Exception as e:
            self._handle_error(e, "Failed to list files")
            return []


class TraktSyncResult(BaseModel):
    total: int = Field(...)
    movies_added: int = Field(...)
    shows_added: int = Field(...)
    failed: int = Field(...)
    watchlist: str | None = Field(default=None)
    results: list = Field(default_factory=list)


class TraktHandler(BaseHandler):
    """Handler for Trakt.tv integration commands."""

    def __init__(self, config: AppConfig):
        """Initialize Trakt handler."""
        super().__init__(config)

    def sync_to_watchlist(
        self,
        scan_file: Path,
        interactive: bool = False,
        watchlist: str | None = None,
        include_statuses: list[FileStatus] | None = None,
    ) -> TraktSyncResult | None:
        """
        Sync scan results to Trakt.tv watchlist and return TraktSyncResult Pydantic model.

        Args:
            scan_file: Path to scan results JSON file
            interactive: Enable interactive mode for ambiguous matches
            watchlist: Optional watchlist name/slug to sync to
            include_statuses: Optional list of file statuses to include
        """
        # Validate Trakt credentials early
        validation_result = validate_trakt_secrets()
        if not validation_result.is_valid:
            handle_credential_error(validation_result)

        try:
            logger.info(f"Syncing scan results from {scan_file} to Trakt.tv watchlist.")

            # Use config default include_statuses if not provided
            if include_statuses is None:
                include_statuses = self.config.trakt.include_statuses

            result_summary = sync_to_trakt_watchlist(
                scan_file=str(scan_file),
                config=self.config,
                interactive=interactive,
                watchlist=watchlist,
                include_statuses=include_statuses,
            )
            # Convert TraktSyncSummary to TraktSyncResult
            result = TraktSyncResult(
                total=getattr(result_summary, "total", 0),
                movies_added=getattr(result_summary, "movies_added", 0),
                shows_added=getattr(result_summary, "shows_added", 0),
                failed=getattr(result_summary, "failed", 0),
                watchlist=getattr(result_summary, "watchlist", None),
                results=getattr(result_summary, "results", []),
            )
            logger.info(
                f"Trakt sync complete. Movies added: {result.movies_added}, "
                f"Shows added: {result.shows_added}."
            )
            return result
        except Exception as e:
            self._handle_error(e, "Trakt sync failed")
            return None

    def _show_sync_results(self, results: TraktSyncResult, dry_run: bool = False) -> None:
        """Show sync operation results."""
        click.echo("\n" + "=" * 50)
        if dry_run:
            click.echo("DRY RUN RESULTS")
        else:
            click.echo("TRAKT SYNC SUMMARY")
        click.echo("=" * 50)

        click.echo(f"Total items processed: {results.total}")
        click.echo(f"Movies {'would be' if dry_run else ''} added: {results.movies_added}")
        click.echo(f"Shows {'would be' if dry_run else ''} added: {results.shows_added}")
        click.echo(f"Failed/Not found: {results.failed}")

        if results.total > 0:
            success_count = results.movies_added + results.shows_added
            success_rate = (success_count / results.total) * 100
            click.echo(f"Success rate: {success_rate:.1f}%")

        # Show failed items if any
        if results.results:
            failed_items = [
                r for r in results.results if r.get("status") in ["failed", "not_found", "error"]
            ]
            if failed_items:
                click.echo(f"\nFailed items ({len(failed_items)}):")
                for item in failed_items[:10]:  # Show first 10
                    click.echo(
                        f"  - {item.get('title', 'Unknown')} ({item.get('year', 'no year')})"
                    )
                if len(failed_items) > 10:
                    click.echo(f"  ... and {len(failed_items) - 10} more")

    def list_watchlists(self, _access_token: str | None = None) -> list | None:
        """
        List all available watchlists for the authenticated user.

        Args:
            access_token: Trakt.tv OAuth access token

        Returns:
            List of watchlist information or None if failed

        Raises:
            ValueError: If Trakt credentials are not configured
        """
        # Validate client credentials from config
        secrets_validation = validate_trakt_secrets()
        if not secrets_validation.is_valid:
            handle_credential_error(secrets_validation)

        # Also validate that config has actual values
        if not self.config.trakt.client_id or not self.config.trakt.client_secret:
            error_msg = (
                "Trakt credentials not configured: client_id and client_secret must be provided "
                "via configuration file, environment variables (CVI_TRAKT_CLIENT_ID, CVI_TRAKT_CLIENT_SECRET), or Docker secrets"
            )
            if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
                raise ValueError(error_msg)
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)

        try:
            logger.info("Fetching user's watchlists from Trakt")
            api = TraktAPI(self.config)
            watchlists = api.list_watchlists()

            return [w.model_dump() for w in watchlists]

        except Exception as e:
            self._handle_error(e, "Failed to fetch watchlists")
            return None

    def view_watchlist(
        self, watchlist: str | None = None, _access_token: str | None = None
    ) -> list | None:
        """
        View items in a specific watchlist.

        Args:
            watchlist: Watchlist name/slug to view (None for main watchlist)
            access_token: Trakt.tv OAuth access token

        Returns:
            List of watchlist items or None if failed

        Raises:
            ValueError: If Trakt credentials are not configured
        """
        # Validate client credentials from config
        secrets_validation = validate_trakt_secrets()
        if not secrets_validation.is_valid:
            handle_credential_error(secrets_validation)

        # Also validate that config has actual values
        if not self.config.trakt.client_id or not self.config.trakt.client_secret:
            error_msg = (
                "Trakt credentials not configured: client_id and client_secret must be provided "
                "via configuration file, environment variables (CVI_TRAKT_CLIENT_ID, CVI_TRAKT_CLIENT_SECRET), or Docker secrets"
            )
            if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
                raise ValueError(error_msg)
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)

        try:
            watchlist_name = watchlist or "Main Watchlist"
            logger.info(f"Fetching items from watchlist: {watchlist_name}")

            api = TraktAPI(self.config)
            items = api.get_watchlist_items(watchlist)

            return [item.model_dump() for item in items]

        except Exception as e:
            self._handle_error(e, f"Failed to fetch watchlist items for '{watchlist}'")
            return None

    def _get_access_token_from_config(self) -> str:
        """Get access token from configuration (config file, env vars, or Docker secrets)."""
        # For now, this would need to be implemented based on the actual auth flow
        # This is a placeholder - in practice, this might involve OAuth flow or stored tokens
        client_id = self.config.trakt.client_id
        client_secret = self.config.trakt.client_secret

        if not client_id or not client_secret:
            msg = "Trakt client_id and client_secret must be configured. Use 'make secrets-init' or set in config file."
            raise ValueError(msg)

        # TODO: Implement actual OAuth token retrieval/refresh logic
        # For now, raise an error indicating the limitation
        msg = (
            "Config-based authentication not fully implemented yet. "
            "Please ensure you have valid OAuth tokens configured."
        )
        raise NotImplementedError(msg)

    def authenticate_oauth(self, username: str, store: bool = True) -> bool:
        """
        Handle OAuth authentication for Trakt.tv.

        Args:
            username: Trakt username for authentication
            store: Whether to store credentials for future use

        Returns:
            True if authentication successful, False otherwise
        """
        client_id = self.config.trakt.client_id
        client_secret = self.config.trakt.client_secret

        if not client_id or not client_secret:
            return False

        try:
            authenticate_trakt_oauth(username, client_id, client_secret, store=store)
            return True

        except Exception:
            logger.exception("OAuth authentication failed")
            return False

    def test_authentication(self) -> tuple[bool, str | None]:
        """
        Test if current Trakt authentication is working.

        Returns:
            Tuple of (success, username) where success is True/False
            and username is the authenticated user or None
        """
        try:
            return test_trakt_authentication()

        except Exception:
            logger.exception("Authentication test failed")
            return False, None

    def check_library_availability(self) -> bool:
        """
        Check if the PyTrakt library is available.

        Returns:
            True if library is available, False otherwise
        """
        try:
            return importlib.util.find_spec("trakt") is not None
        except ImportError:
            return False


class UtilityHandler(BaseHandler):
    """Handler for utility CLI operations."""

    def __init__(self, config: AppConfig):
        """Initialize utility handler."""
        super().__init__(config)
        self.scanner = VideoScanner(config)

    def get_ffmpeg_command(self) -> str | None:
        """
        Detects ffmpeg command in PATH.

        Returns path or None.
        """
        return which("ffmpeg")

    def check_system_requirements(self) -> str:
        """
        Ensure FFmpeg is available, returning its command or exiting.
        """
        cmd = self.get_ffmpeg_command()
        if not cmd:
            click.echo("FFmpeg not found", err=True)
            sys.exit(1)
        return cmd

    def get_all_video_object_files(
        self,
        directory: Path | str,
        recursive: bool = True,
        extensions: Sequence[str] | None = None,
    ) -> list[VideoFile]:
        """
        Return list of video file objects.
        Accepts Path for directory.
        """
        # Ensure directory is a Path
        directory_path = Path(directory)
        # Pass extensions directly to get_video_files instead of mutating config
        return self.scanner.get_video_files(
            directory_path, recursive=recursive, extensions=list(extensions) if extensions else None
        )

    def list_video_files_simple(
        self,
        directory: Path,
        recursive: bool = True,
        extensions: list[str] | None = None,
    ) -> None:
        """
        List video files in directory and echo results.

        Exits on errors.
        """
        try:
            files = self.get_all_video_object_files(directory, recursive, extensions)
            if files:
                for f in files:
                    click.echo(f.path)
            else:
                click.echo("No video files found")
        except Exception:
            logger.exception("Error listing video files")
            sys.exit(1)


# Typer app for CLI entry point
app = typer.Typer()


def main() -> None:
    """Main entry point: invokes the Typer app."""
    app()


def setup_logging(verbose: bool) -> None:
    """
    Configure basic logging.

    Args:
        verbose: verbosity flag (False=INFO, True=DEBUG)
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)


# Legacy standalone functions for backward compatibility
def get_ffmpeg_command() -> str | None:
    """
    Detects ffmpeg command in PATH.

    Returns path or None.
    """
    return which("ffmpeg")


def check_system_requirements() -> str:
    """
    Ensure FFmpeg is available, returning its command or exiting.
    """
    cmd = get_ffmpeg_command()
    if not cmd:
        click.echo("FFmpeg not found", err=True)
        sys.exit(1)
    return cmd


def get_all_video_object_files(
    directory: Path | str,
    recursive: bool = True,
    extensions: Sequence[str] | None = None,
) -> list[VideoFile]:
    """
    Return list of video file objects.
    Accepts Path for directory.
    """
    # Ensure directory is a Path
    directory_path = Path(directory)
    config = load_config()
    scanner = VideoScanner(config)
    # Pass extensions directly to get_video_files instead of mutating config
    return scanner.get_video_files(
        directory_path, recursive=recursive, extensions=list(extensions) if extensions else None
    )


def list_video_files(
    directory: Path,
    recursive: bool = True,
    extensions: list[str] | None = None,
) -> None:
    """
    List video files in directory and echo results.

    Exits on errors.
    """
    try:
        files = get_all_video_object_files(directory, recursive, extensions)
        if files:
            for f in files:
                click.echo(f.path)
        else:
            click.echo("No video files found")
    except Exception:
        logger.exception("Error listing video files")
        sys.exit(1)
