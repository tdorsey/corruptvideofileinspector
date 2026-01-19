"""
CLI command definitions using Click framework.
"""

import csv
import importlib.util
import io
import json
import logging
import sys
from pathlib import Path

import click

from src.cli.handlers import ListHandler, ScanHandler, TraktHandler
from src.cli.logging import configure_logging_from_config, setup_logging
from src.config import load_config
from src.core.models.scanning import FileStatus, ScanMode
from src.core.reporter import ReportService
from src.ffmpeg.ffmpeg_client import FFmpegClient


# Database imports - only import when available
def get_database_imports():
    """Dynamically import database modules when needed."""
    try:
        from src.database.models import DatabaseQueryFilter
        from src.database.service import DatabaseService

        return DatabaseQueryFilter, DatabaseService
    except ImportError:
        return None, None


logger = logging.getLogger(__name__)


# Custom Click types
class ScanModeChoice(click.Choice):
    """Custom choice type for scan modes."""

    def __init__(self):
        super().__init__(["quick", "deep", "hybrid"], case_sensitive=False)

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)
        return ScanMode(value.lower())


class PathType(click.Path):
    """Custom path type that returns Path objects."""

    def convert(self, value, param, ctx):
        path_str = super().convert(value, param, ctx)
        if isinstance(path_str, bytes):
            path_str = path_str.decode("utf-8")
        return Path(path_str)


# Global options that can be shared across commands
def global_options(f):
    """Decorator to add global options to commands."""
    return click.option(
        "--config",
        "-c",
        type=PathType(exists=True),
        help="Path to configuration file (JSON or YAML)",
    )(f)


# Main CLI group moved from main.py
@click.group(invoke_without_command=True)
@click.version_option(
    version=None,  # Will be set from src.version.__version__ in main.py
    prog_name="corrupt-video-inspector",
    message="%(prog)s %(version)s",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.pass_context
def cli(
    ctx: click.Context,
    config: Path | None = None,
) -> None:
    """Corrupt Video Inspector - Detect and manage corrupted video files.

    A comprehensive tool for scanning video directories, detecting corruption
    using FFmpeg, and optionally syncing healthy files to Trakt.tv.

    Examples:
        corrupt-video-inspector scan /path/to/videos
        corrupt-video-inspector scan /movies --mode deep --recursive
        corrupt-video-inspector scan /tv-shows --trakt-sync
    """
    # Setup basic logging first
    setup_logging(0)

    # Load configuration
    try:
        app_config = load_config(config_path=config) if config else load_config()
        ctx.ensure_object(dict)
        ctx.obj["config"] = app_config

        # Reconfigure logging with settings from AppConfig
        # This ensures logs are written to both stdout and the configured file
        configure_logging_from_config(
            level=app_config.logging.level,
            log_file=app_config.logging.file,
            log_format=app_config.logging.format,
            date_format=app_config.logging.date_format,
        )
    except Exception as e:
        logging.exception("Configuration error")
        raise click.Abort from e

    # If no command specified, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@global_options
@click.option(
    "--directory",
    "-d",
    required=True,
    type=PathType(exists=True, file_okay=False),
    help="Directory to scan for video files.",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice([e.value for e in ScanMode], case_sensitive=False),
    default="hybrid",
    help="Scan mode: quick (1min timeout), deep (full scan), hybrid (quick then deep for suspicious), full (complete scan without timeout)",
    show_default=True,
)
@click.option(
    "--max-workers",
    "-w",
    type=click.IntRange(1, 32),
    help="Maximum number of worker threads for parallel processing",
)
@click.option(
    "--recursive/--no-recursive",
    "-r",
    default=True,
    help="Recursively scan subdirectories",
    show_default=True,
)
@click.option(
    "--extensions",
    multiple=True,
    help="Video file extensions to scan (e.g., --extensions mp4 --extensions mkv)",
)
@click.option(
    "--resume/--no-resume",
    default=True,
    help="Enable/disable resume functionality",
    show_default=True,
)
@click.option(
    "--incremental/--full-scan",
    default=False,
    help="Skip files that were recently scanned and found healthy",
    show_default=True,
)
@click.option(
    "--max-age",
    type=int,
    default=7,
    help="Maximum age in days for incremental scans (default: 7 days)",
    show_default=True,
)
@click.pass_context
def scan(
    ctx,
    directory,
    mode,
    max_workers,
    recursive,
    extensions,
    resume,
    incremental,
    max_age,
    config,
):
    # If no arguments are provided, show the help for the scan subcommand
    if ctx.args == [] and directory is None:
        click.echo(ctx.get_help())
        ctx.exit(0)
    """
    Scan a directory for corrupt video files.

    Uses FFmpeg to analyze video files and detect corruption. Supports four scan modes:

    \b
    - quick: Fast scan with 1-minute timeout per file
    - deep: Full scan with 15-minute timeout per file
    - hybrid: Quick scan first, then deep scan for suspicious files
    - full: Complete scan of entire video stream without timeout

    - All scan results are stored in the SQLite database.

    \b
    - Use --incremental to skip files recently scanned and found healthy

    Examples:

    \b
    # Basic hybrid scan
    corrupt-video-inspector scan /path/to/videos

    \b
    # Quick scan
    corrupt-video-inspector scan --mode quick /path/to/videos

    \b
    # Incremental scan (skip recently healthy files)
    corrupt-video-inspector scan --incremental /path/to/videos

    \b
    # Full scan without timeout (for thorough analysis)
    corrupt-video-inspector scan --mode full /path/to/videos

    \b
    # Deep scan with custom extensions
    corrupt-video-inspector scan --mode deep --extensions mp4 --extensions mkv /videos
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Override config with CLI options
        if max_workers:
            app_config.scan.max_workers = max_workers
        if extensions:
            app_config.scan.extensions = [
                f".{ext}" if not ext.startswith(".") else ext for ext in extensions
            ]

        # Convert mode string to ScanMode enum
        scan_mode = ScanMode(mode.lower())

        # Create and run scan handler
        handler = ScanHandler(app_config)
        summary = handler.run_scan(
            directory=directory,
            scan_mode=scan_mode,
            recursive=recursive,
            resume=resume,
            incremental=incremental,
            max_age_days=max_age,
        )
        if summary is not None:
            click.echo("\nScan Summary:")
            click.echo(json.dumps(summary.model_dump(), indent=2))
            click.echo(f"\nResults stored in database at: {app_config.database.path}")
        else:
            click.echo("No video files found to scan.")

    except Exception as e:
        logger.exception("Scan command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@global_options
@click.argument("directory", type=PathType(exists=True, file_okay=False))
@click.option(
    "--recursive/--no-recursive",
    "-r",
    default=True,
    help="Recursively scan subdirectories",
    show_default=True,
)
@click.option("--extensions", multiple=True, help="Video file extensions to include")
@click.option("--output", "-o", type=PathType(), help="Output file path for file list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default="text",
    help="Output format",
    show_default=True,
)
@click.pass_context
def list_files(
    ctx,
    directory,
    recursive,
    extensions,
    output,
    output_format,
    config,
):
    # If no arguments are provided, show the help for the list-files subcommand
    if ctx.args == [] and directory is None:
        click.echo(ctx.get_help())
        ctx.exit(0)
    """
    List all video files in a directory without scanning.

    Useful for previewing what files would be scanned or generating
    file inventories.

    Examples:

    \b
    # List all video files
    corrupt-video-inspector list-files /path/to/videos

    \b
    # List specific extensions to JSON
    corrupt-video-inspector list-files --extensions mp4 --format json /videos
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Override config with CLI options
        if extensions:
            app_config.scan.extensions = [
                f".{ext}" if not ext.startswith(".") else ext for ext in extensions
            ]

        # Setup logging

        # Create and run list handler
        handler = ListHandler(app_config)
        video_files = handler.list_files(
            directory=directory,
            recursive=recursive,
            output_file=output,
            output_format=output_format,
        )
        if not video_files:
            click.echo("No video files found in the specified directory.")
        elif output_format == "json":
            click.echo(json.dumps([vf.model_dump() for vf in video_files], indent=2))
        elif output_format == "csv":
            output_str = io.StringIO()
            writer = csv.DictWriter(output_str, fieldnames=video_files[0].model_dump().keys())
            writer.writeheader()
            for vf in video_files:
                writer.writerow(vf.model_dump())
            click.echo(output_str.getvalue())
        else:
            click.echo(f"\nFound {len(video_files)} video files:")
            for i, vf in enumerate(video_files, 1):
                rel_path = vf.path.relative_to(directory)
                size_mb = vf.size / (1024 * 1024) if vf.size > 0 else 0
                click.echo(f"  {i:3d}: {rel_path} ({size_mb:.1f} MB)")

    except Exception as e:
        logger.exception("List command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
@click.pass_context
def trakt(ctx):
    """
    Trakt.tv integration commands.

    Sync scan results to your Trakt.tv watchlist by parsing filenames
    and matching them against Trakt's database.
    """
    # If no subcommand is provided, show the help for the trakt group
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


@trakt.command()
@click.option(
    "--scan-id",
    "-s",
    type=int,
    help="Scan ID from database (use latest scan if not specified)",
)
@click.option("--client-id", help="Trakt.tv API client ID (overrides config setting)")
@click.option(
    "--interactive/--no-interactive",
    "-i",
    default=False,
    help="Enable interactive selection of search results",
    show_default=True,
)
@click.option("--dry-run", is_flag=True, help="Show what would be synced without actually syncing")
@click.option(
    "--watchlist",
    "-w",
    help="Watchlist name or slug to sync to (default: main watchlist)",
)
@click.option(
    "--include-status",
    multiple=True,
    type=click.Choice(["healthy", "corrupt", "suspicious"], case_sensitive=False),
    default=["healthy"],
    help="Include files with these statuses (default: healthy only)",
    show_default=True,
)
@global_options
@click.pass_context
def sync(
    ctx,
    scan_id,
    client_id,
    interactive,
    dry_run,
    watchlist,
    include_status,
    config,
):
    """
    Sync scan results to Trakt.tv watchlist.

    Reads scan results from database and adds discovered movies and TV shows
    to your Trakt.tv watchlist using filename parsing and search matching.
    Authentication is handled through configuration (config file, environment variables, or Docker secrets).

    Examples:

    \b
    # Basic sync from latest scan to main watchlist
    corrupt-video-inspector trakt sync

    \b
    # Sync specific scan to a specific watchlist
    corrupt-video-inspector trakt sync --scan-id 42 --watchlist "my-custom-list"

    \b
    # Interactive sync
    corrupt-video-inspector trakt sync --interactive

    \b
    # Dry run to see what would be synced
    corrupt-video-inspector trakt sync --dry-run
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Override config with CLI options
        if client_id:
            app_config.trakt.client_id = client_id

        # Get database service
        from src.database.service import DatabaseService

        db_service = DatabaseService(
            app_config.database.path, app_config.database.auto_cleanup_days
        )

        # Get scan from database
        if scan_id is None:
            # Get latest scan
            recent_scans = db_service.get_recent_scans(limit=1)
            if not recent_scans:
                click.echo("No scans found in database", err=True)
                sys.exit(1)
            scan_model = recent_scans[0]
            click.echo(f"Using latest scan (ID: {scan_model.id})")
        else:
            scan_model_or_none = db_service.get_scan(scan_id)
            if scan_model_or_none is None:
                click.echo(f"Scan ID {scan_id} not found in database", err=True)
                sys.exit(1)
            scan_model = scan_model_or_none

        # Get scan results
        scan_results_db = db_service.get_scan_results(scan_model.id or 0)

        # Convert status strings to FileStatus enums
        include_statuses = [FileStatus(status) for status in include_status]

        # Filter results by status
        filtered_results = [
            result
            for result in scan_results_db
            if FileStatus(result.status.upper()) in include_statuses
        ]

        click.echo(f"Found {len(filtered_results)} files matching status filter")

        # Handle dry-run mode
        if dry_run:
            click.echo("DRY RUN MODE: No actual syncing will be performed")
            click.echo("\nFiles to sync:")
            for result in filtered_results[:10]:  # Show first 10
                click.echo(f"  - {result.filename} ({result.status})")
            if len(filtered_results) > 10:
                click.echo(f"  ... and {len(filtered_results) - 10} more")
            return

        # Create and run Trakt handler
        handler = TraktHandler(app_config)

        sync_result = handler.sync_to_watchlist_from_results(
            scan_results=filtered_results,
            interactive=interactive,
            watchlist=watchlist,
        )

        click.echo("\nTrakt Sync Result:")
        if sync_result is not None:
            click.echo(json.dumps(sync_result.model_dump(), indent=2))
        else:
            click.echo("No sync result returned.")

    except Exception as e:
        logger.exception("Trakt sync command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@trakt.command()
@click.option("--output", "-o", type=PathType(), help="Save watchlist info to file")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table"], case_sensitive=False),
    default="table",
    help="Output format",
    show_default=True,
)
@global_options
def list_watchlists(output, output_format, config):
    """
    List all available watchlists for the authenticated user.

    Shows all custom lists and the main watchlist that the user has access to.
    Authentication is handled through configuration (config file, environment variables, or Docker secrets).

    Examples:

    \b
    # List watchlists in table format
    corrupt-video-inspector trakt list-watchlists

    \b
    # List watchlists in JSON format
    corrupt-video-inspector trakt list-watchlists --format json
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)
        # Create and run Trakt handler
        handler = TraktHandler(app_config)
        watchlists = handler.list_watchlists()

        if not watchlists:
            click.echo("No watchlists found or failed to fetch watchlists.")
            return

        if output_format == "json":
            output_data = {"watchlists": watchlists}
            click.echo(json.dumps(output_data, indent=2))
        else:
            # Table format
            click.echo(f"\nFound {len(watchlists)} watchlists:\n")
            click.echo(f"{'Name':<30} {'Slug':<20} {'Items':<8} {'Privacy':<10}")
            click.echo("-" * 70)
            for wl in watchlists:
                name = wl.get("name", "Unknown")[:29]
                slug = wl.get("slug", "")[:19]
                items = wl.get("item_count", 0)
                privacy = wl.get("privacy", "private")[:9]
                click.echo(f"{name:<30} {slug:<20} {items:<8} {privacy:<10}")

        if output:
            with output.open("w", encoding="utf-8") as f:
                json.dump({"watchlists": watchlists}, f, indent=2)
            click.echo(f"\nWatchlist data saved to: {output}")

    except ValueError as e:
        # Handle credential validation errors with user-friendly message
        click.echo(f"Configuration Error: {e}", err=True)
        click.echo("\nTo configure Trakt credentials:", err=True)
        click.echo(
            "1. Get your client ID and secret from https://trakt.tv/oauth/applications", err=True
        )
        click.echo("2. Set them in your config file:", err=True)
        click.echo("   trakt:", err=True)
        click.echo("     client_id: your_client_id", err=True)
        click.echo("     client_secret: your_client_secret", err=True)
        click.echo(
            "3. Or set environment variables: CVI_TRAKT_CLIENT_ID and CVI_TRAKT_CLIENT_SECRET",
            err=True,
        )
        sys.exit(1)
    except Exception as e:
        logger.exception("List watchlists command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@trakt.command()
@click.option(
    "--watchlist",
    "-w",
    help="Watchlist name or slug to view (leave empty for main watchlist)",
)
@click.option("--output", "-o", type=PathType(), help="Save watchlist contents to file")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table"], case_sensitive=False),
    default="table",
    help="Output format",
    show_default=True,
)
@global_options
def view(watchlist, output, output_format, config):
    """
    View items in a specific watchlist.

    Shows all movies and TV shows in the specified watchlist.
    If no watchlist is specified, shows items from the main watchlist.
    Authentication is handled through configuration (config file, environment variables, or Docker secrets).

    Examples:

    \b
    # View main watchlist
    corrupt-video-inspector trakt view

    \b
    # View a specific custom list
    corrupt-video-inspector trakt view --watchlist "my-list"

    \b
    # View watchlist in JSON format
    corrupt-video-inspector trakt view --format json
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)
        # Create and run Trakt handler
        handler = TraktHandler(app_config)
        items = handler.view_watchlist(watchlist=watchlist)

        if not items:
            watchlist_name = watchlist or "Main Watchlist"
            click.echo(f"No items found in '{watchlist_name}' or failed to fetch items.")
            return

        watchlist_name = watchlist or "Main Watchlist"

        if output_format == "json":
            output_data = {"watchlist": watchlist_name, "items": items}
            click.echo(json.dumps(output_data, indent=2))
        else:
            # Table format
            click.echo(f"\nItems in '{watchlist_name}' ({len(items)} total):\n")
            click.echo(f"{'#':<4} {'Title':<40} {'Year':<6} {'Type':<6}")
            click.echo("-" * 58)
            for item in items:
                rank = item.get("rank", "")
                rank_str = str(rank) if rank else ""

                trakt_item = item.get("trakt_item", {})
                title = trakt_item.get("title", "Unknown")[:39]
                year = trakt_item.get("year", "")
                year_str = str(year) if year else ""
                media_type = trakt_item.get("media_type", "unknown")[:5]

                click.echo(f"{rank_str:<4} {title:<40} {year_str:<6} {media_type:<6}")

        if output:
            with output.open("w", encoding="utf-8") as f:
                json.dump({"watchlist": watchlist_name, "items": items}, f, indent=2)
            click.echo(f"\nWatchlist contents saved to: {output}")

    except ValueError as e:
        # Handle credential validation errors with user-friendly message
        click.echo(f"Configuration Error: {e}", err=True)
        click.echo("\nTo configure Trakt credentials:", err=True)
        click.echo(
            "1. Get your client ID and secret from https://trakt.tv/oauth/applications", err=True
        )
        click.echo("2. Set them in your config file:", err=True)
        click.echo("   trakt:", err=True)
        click.echo("     client_id: your_client_id", err=True)
        click.echo("     client_secret: your_client_secret", err=True)
        click.echo(
            "3. Or set environment variables: CVI_TRAKT_CLIENT_ID and CVI_TRAKT_CLIENT_SECRET",
            err=True,
        )
        sys.exit(1)
    except Exception as e:
        logger.exception("View watchlist command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@trakt.command()
@click.option("--username", help="Trakt username (required for OAuth authentication)")
@click.option(
    "--store/--no-store",
    default=True,
    help="Store credentials in ~/.pytrakt.json for automatic loading",
    show_default=True,
)
@click.option("--test-only", is_flag=True, help="Only test existing authentication")
@global_options
def auth(username, store, test_only, config):
    """
    Set up or test Trakt.tv OAuth authentication.

    This command helps you authenticate with Trakt.tv using OAuth authentication.
    You must provide your Trakt username for the OAuth flow.

    \\b
    Prerequisites:
    1. Create a Trakt API application at: https://trakt.tv/oauth/applications
    2. Store your client_id in: docker/secrets/trakt_client_id.txt
    3. Store your client_secret in: docker/secrets/trakt_client_secret.txt

    \\b
    Examples:

    \\b
    # Test existing authentication
    corrupt-video-inspector trakt auth --test-only

    \\b
    # Set up OAuth authentication
    corrupt-video-inspector trakt auth --username=yourusername --store

    \\b
    # Set up without storing credentials (re-auth needed each time)
    corrupt-video-inspector trakt auth --username=yourusername --no-store
    """
    # Check if PyTrakt library is available
    if importlib.util.find_spec("trakt") is None:
        click.echo("❌ PyTrakt library not found. Install with: pip install trakt>=3.4.0", err=True)
        sys.exit(1)

    click.echo("🎬 Trakt.tv OAuth Authentication Setup")
    click.echo("=" * 40)

    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Create TraktHandler for authentication operations
        trakt_handler = TraktHandler(app_config)

        # Validate that client credentials are configured
        client_id = app_config.trakt.client_id
        client_secret = app_config.trakt.client_secret

        if not client_id or not client_secret:
            click.echo("❌ Trakt client credentials not found in configuration", err=True)
            click.echo("\n💡 To fix this:")
            click.echo("   1. Visit: https://trakt.tv/oauth/applications")
            click.echo("   2. Create a new application")
            click.echo("   3. Copy the Client ID to: docker/secrets/trakt_client_id.txt")
            click.echo("   4. Copy the Client Secret to: docker/secrets/trakt_client_secret.txt")
            sys.exit(1)

        click.echo("✅ Client credentials found")
        click.echo(f"   Client ID: {client_id[:8]}...")

        # Check if stored credentials exist
        config_path = Path.home() / ".pytrakt.json"
        if config_path.exists():
            click.echo("✅ Stored credentials found at ~/.pytrakt.json")
        else:
            click.echo("i No stored credentials found")

        # Test existing authentication if requested
        if test_only:
            click.echo("\n🧪 Testing existing authentication...")
            try:
                success, username = trakt_handler.test_authentication()
                if success:
                    click.echo(f"✅ Authentication test successful! Logged in as: {username}")
                    return
                click.echo("❌ Authentication test failed")
                click.echo("Run without --test-only to authenticate.")
                sys.exit(1)
            except Exception as e:
                click.echo(f"❌ Authentication test failed: {e}")
                click.echo("Run without --test-only to authenticate.")
                sys.exit(1)

        # Perform OAuth authentication
        if not username:
            username = click.prompt("Enter your Trakt username", type=str)

        click.echo(f"\n🔐 Starting OAuth authentication for user: {username}")

        try:
            success = trakt_handler.authenticate_oauth(username, store=store)

            if not success:
                click.echo("❌ OAuth authentication failed")
                sys.exit(1)

            # Test the authentication
            click.echo("\n🧪 Testing authentication...")
            success, authenticated_username = trakt_handler.test_authentication()
            if success:
                click.echo(f"✅ Authentication successful! Logged in as: {authenticated_username}")

                if store:
                    click.echo("✅ Credentials stored in ~/.pytrakt.json for automatic loading")
                    click.echo("   Future commands will automatically use these credentials")
                else:
                    click.echo(
                        "i Credentials not stored - you'll need to re-authenticate for each session"
                    )

                click.echo("\n🎉 Trakt authentication setup complete!")
                click.echo("You can now use 'trakt sync' and other Trakt commands.")
            else:
                click.echo("❌ Authentication verification failed")
                sys.exit(1)

        except Exception as e:
            click.echo(f"❌ OAuth authentication failed: {e}")
            click.echo("\n💡 Troubleshooting:")
            click.echo("   1. Verify your client credentials are correct")
            click.echo("   2. Check your internet connection")
            click.echo("   3. Ensure your Trakt username is correct")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Configuration error: {e}")
        sys.exit(1)


@cli.command()
@global_options
@click.pass_context
def test_ffmpeg(ctx, config):
    # If no arguments are provided, show the help for the test-ffmpeg subcommand
    if ctx.args == []:
        click.echo(ctx.get_help())
        ctx.exit(0)
    """
    Test FFmpeg installation and show diagnostic information.

    Validates that FFmpeg is properly installed and accessible,
    showing version information and supported formats.
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Setup logging
        setup_logging(0)
        # Test FFmpeg
        ffmpeg = FFmpegClient(app_config.ffmpeg)
        test_results = ffmpeg.test_installation()

        click.echo("FFmpeg Installation Test")
        click.echo("=" * 40)

        click.echo(f"FFmpeg Path: {test_results['ffmpeg_path'] or 'Not found'}")
        click.echo(f"FFmpeg Available: {'✓' if test_results['ffmpeg_available'] else '✗'}")
        click.echo(f"FFprobe Available: {'✓' if test_results['ffprobe_available'] else '✗'}")

        if test_results["version_info"]:
            click.echo(f"Version: {test_results['version_info']}")

        if test_results["supported_formats"]:
            click.echo(f"Supported Formats: {', '.join(test_results['supported_formats'])}")

        if not test_results["ffmpeg_available"]:
            click.echo("\nFFmpeg is not available. Please install it:")
            click.echo("  - Ubuntu/Debian: sudo apt install ffmpeg")
            click.echo("  - CentOS/RHEL: sudo yum install ffmpeg")
            click.echo("  - macOS: brew install ffmpeg")
            click.echo("  - Windows: Download from https://ffmpeg.org/download.html")
            sys.exit(1)
        else:
            click.echo("\nFFmpeg is working correctly! ✓")

    except Exception as e:
        logger.exception("FFmpeg test command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@global_options
@click.option(
    "--scan-id",
    "-s",
    type=int,
    help="Scan ID from database (use latest scan if not specified)",
)
@click.option(
    "--compare",
    nargs=2,
    type=int,
    help="Compare two scans by ID (e.g., --compare 41 42)",
)
@click.option(
    "--trend",
    is_flag=True,
    help="Show corruption trend analysis over time",
)
@click.option(
    "--directory",
    "-d",
    help="Directory for trend analysis (required with --trend)",
)
@click.option(
    "--days",
    type=click.IntRange(1, 365),
    default=30,
    help="Days to analyze for trend report",
    show_default=True,
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "csv", "html", "pdf"], case_sensitive=False),
    default="text",
    help="Report format",
    show_default=True,
)
@click.option(
    "--include-healthy/--corrupt-only",
    default=True,
    help="Include healthy files in report",
    show_default=True,
)
@click.pass_context
def report(
    ctx,
    scan_id,
    compare,
    trend,
    directory,
    days,
    output_format,
    include_healthy,
    config,
):
    """
    Generate detailed reports from scan results stored in database.

    Creates formatted reports with statistics, file lists, and analysis
    from database scan results. Supports single scan reports, comparison
    between two scans, and trend analysis over time.

    Examples:

    \b
    # Generate text report from latest scan
    corrupt-video-inspector report

    \b
    # Generate report from specific scan ID
    corrupt-video-inspector report --scan-id 42

    \b
    # Compare two scans
    corrupt-video-inspector report --compare 41 42

    \b
    # Show corruption trend for directory
    corrupt-video-inspector report --trend --directory /media/movies --days 30

    """
    try:
        # Load configuration
        app_config = load_config(config_path=config) if config else load_config()

        # Setup logging
        setup_logging(0)

        # Get database service
        from src.database.service import DatabaseService

        db_service = DatabaseService(
            app_config.database.path, app_config.database.auto_cleanup_days
        )

        # Handle trend report
        if trend:
            if not directory:
                click.echo("Error: --directory is required with --trend", err=True)
                sys.exit(1)

            trend_data = db_service.get_corruption_trend(directory, days)

            if not trend_data:
                click.echo(f"No scan data found for directory: {directory}")
                return

            if output_format == "json":
                click.echo(json.dumps({"directory": directory, "days": days, "trend": trend_data}, indent=2))
            elif output_format == "csv":
                import csv as csv_module
                import io

                output_io = io.StringIO()
                writer = csv_module.DictWriter(output_io, fieldnames=trend_data[0].keys())
                writer.writeheader()
                for row in trend_data:
                    writer.writerow(row)
                click.echo(output_io.getvalue())
            else:  # text format
                from datetime import datetime

                click.echo(f"\n=== Corruption Trend Report ===")
                click.echo(f"Directory: {directory}")
                click.echo(f"Period: Last {days} days")
                click.echo(f"Data Points: {len(trend_data)}\n")
                click.echo(f"{'Date':<12} {'Files':<8} {'Corrupt':<8} {'Rate':<10}")
                click.echo("-" * 50)

                for point in trend_data:
                    date_str = datetime.fromtimestamp(point["timestamp"]).strftime("%Y-%m-%d")
                    total = point.get("total_files", 0)
                    corrupt = point.get("corrupt_files", 0)
                    rate = point.get("corruption_rate", 0.0)
                    click.echo(f"{date_str:<12} {total:<8} {corrupt:<8} {rate:<10.1f}%")
            return

        # Handle comparison report
        if compare:
            scan1_id, scan2_id = compare
            scan1 = db_service.get_scan(scan1_id)
            scan2 = db_service.get_scan(scan2_id)

            if not scan1:
                click.echo(f"Error: Scan ID {scan1_id} not found", err=True)
                sys.exit(1)
            if not scan2:
                click.echo(f"Error: Scan ID {scan2_id} not found", err=True)
                sys.exit(1)

            results1 = db_service.get_scan_results(scan1_id)
            results2 = db_service.get_scan_results(scan2_id)

            if output_format == "json":
                comparison = {
                    "scan1": {"id": scan1_id, "summary": scan1.to_scan_summary().model_dump()},
                    "scan2": {"id": scan2_id, "summary": scan2.to_scan_summary().model_dump()},
                    "changes": {
                        "files_change": scan2.total_files - scan1.total_files,
                        "corrupt_change": scan2.corrupt_files - scan1.corrupt_files,
                        "rate_change": (scan2.corrupt_files / max(scan2.total_files, 1) * 100) - (scan1.corrupt_files / max(scan1.total_files, 1) * 100),
                    },
                }
                click.echo(json.dumps(comparison, indent=2, default=str))
            else:  # text format
                from datetime import datetime

                click.echo(f"\n=== Scan Comparison Report ===\n")
                click.echo(f"Scan 1 (ID: {scan1_id})")
                click.echo(f"  Date: {datetime.fromtimestamp(scan1.started_at).strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo(f"  Directory: {scan1.directory}")
                click.echo(f"  Files: {scan1.total_files}")
                click.echo(f"  Corrupt: {scan1.corrupt_files}")
                click.echo(f"  Rate: {scan1.corrupt_files / max(scan1.total_files, 1) * 100:.1f}%\n")

                click.echo(f"Scan 2 (ID: {scan2_id})")
                click.echo(f"  Date: {datetime.fromtimestamp(scan2.started_at).strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo(f"  Directory: {scan2.directory}")
                click.echo(f"  Files: {scan2.total_files}")
                click.echo(f"  Corrupt: {scan2.corrupt_files}")
                click.echo(f"  Rate: {scan2.corrupt_files / max(scan2.total_files, 1) * 100:.1f}%\n")

                click.echo("Changes:")
                files_delta = scan2.total_files - scan1.total_files
                corrupt_delta = scan2.corrupt_files - scan1.corrupt_files
                rate_delta = (scan2.corrupt_files / max(scan2.total_files, 1) * 100) - (scan1.corrupt_files / max(scan1.total_files, 1) * 100)

                click.echo(f"  Files: {files_delta:+d}")
                click.echo(f"  Corrupt: {corrupt_delta:+d}")
                click.echo(f"  Rate: {rate_delta:+.1f}%\n")
            return

        # Handle single scan report
        if scan_id is None:
            # Get latest scan
            recent_scans = db_service.get_recent_scans(limit=1)
            if not recent_scans:
                click.echo("No scans found in database", err=True)
                sys.exit(1)
            scan_model = recent_scans[0]
            click.echo(f"Using latest scan (ID: {scan_model.id})")
        else:
            scan_model_or_none = db_service.get_scan(scan_id)
            if scan_model_or_none is None:
                click.echo(f"Scan ID {scan_id} not found in database", err=True)
                sys.exit(1)
            scan_model = scan_model_or_none

        # Convert database model to ScanSummary
        summary = scan_model.to_scan_summary()

        # Get scan results
        scan_results_db = db_service.get_scan_results(scan_model.id or 0)
        results = [result.to_scan_result() for result in scan_results_db]

        # Filter results if needed
        if not include_healthy:
            results = [r for r in results if r.is_corrupt]

        # Display report based on format
        if output_format == "json":
            report_data = {
                "scan_id": scan_model.id,
                "summary": summary.model_dump(),
                "results": [r.model_dump() for r in results],
            }
            click.echo(json.dumps(report_data, indent=2, default=str))

        elif output_format == "csv":
            import csv as csv_module
            import io

            output_io = io.StringIO()
            if results:
                writer = csv_module.DictWriter(output_io, fieldnames=results[0].model_dump().keys())
                writer.writeheader()
                for result in results:
                    writer.writerow(result.model_dump())
            click.echo(output_io.getvalue())

        elif output_format == "text":
            from datetime import datetime

            click.echo(f"\n=== Scan Report ===")
            click.echo(f"Scan ID: {scan_model.id}")
            click.echo(f"Directory: {scan_model.directory}")
            click.echo(f"Mode: {scan_model.scan_mode}")
            click.echo(f"Started: {datetime.fromtimestamp(scan_model.started_at).strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"Duration: {scan_model.scan_time:.1f}s\n")

            click.echo("Summary:")
            click.echo(f"  Total Files: {scan_model.total_files}")
            click.echo(f"  Processed: {scan_model.processed_files}")
            click.echo(f"  Corrupt: {scan_model.corrupt_files}")
            click.echo(f"  Healthy: {scan_model.healthy_files}")
            click.echo(f"  Corruption Rate: {scan_model.corrupt_files / max(scan_model.total_files, 1) * 100:.1f}%\n")

            if results:
                click.echo("Files:")
                click.echo(f"{'Filename':<50} {'Status':<10} {'Confidence':<12}")
                click.echo("-" * 80)
                for result in results:
                    filename = result.filename
                    if len(filename) > 47:
                        filename = "..." + filename[-44:]
                    status = "CORRUPT" if result.is_corrupt else "HEALTHY"
                    confidence = f"{result.confidence:.2f}"
                    click.echo(f"{filename:<50} {status:<10} {confidence:<12}")

        else:  # html, pdf - try ReportService
            try:
                service = ReportService(app_config)
                report_path = service.generate_report(
                    summary=summary,
                    results=results,
                    format=output_format,
                    include_healthy=include_healthy,
                )
                click.echo(f"Report generated: {report_path}")
            except Exception as e:
                logger.warning(f"Report generation not available for format {output_format}: {e}")
                # Fallback to JSON
                report_data = {
                    "scan_id": scan_model.id,
                    "summary": summary.model_dump(),
                    "results": [r.model_dump() for r in results],
                }
                click.echo(json.dumps(report_data, indent=2, default=str))

    except Exception as e:
        logger.exception("Report command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@global_options
@click.option("--all-configs", is_flag=True, help="Show all configuration sources and values")
@click.option("--debug", is_flag=True, help="Enable debug logging to see configuration overrides")
@click.pass_context
def show_config(all_configs, debug, config):
    """
    Show current configuration settings.

    Displays the effective configuration after loading from all sources
    (defaults, files, environment variables, etc.).

    Use --debug to see detailed information about configuration overrides
    from environment variables and Docker secrets.
    """
    try:
        # Enable debug logging if requested
        if debug:
            logging.getLogger("src.config.merge").setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            logging.getLogger("src.config.merge").addHandler(handler)
            click.echo("Configuration Override Debug Log:")
            click.echo("-" * 50)

        # Load configuration with debug option
        app_config = load_config(config_path=config, debug=debug)

        if debug:
            click.echo("-" * 50)
            click.echo()

        if all_configs:
            # Show detailed configuration
            config_dict = app_config.model_dump()
            # Mask sensitive information in output
            if (
                "trakt" in config_dict
                and "client_secret" in config_dict["trakt"]
                and config_dict["trakt"]["client_secret"]
            ):
                config_dict["trakt"]["client_secret"] = "***MASKED***"
            click.echo(json.dumps(config_dict, indent=2, default=str))
        else:
            # Show key settings
            click.echo("Effective Configuration")
            click.echo("=" * 30)
            click.echo(f"Log Level: {app_config.logging.level}")
            click.echo(f"Max Workers: {app_config.processing.max_workers}")
            click.echo(f"Default Scan Mode: {app_config.scan.mode}")
            click.echo(f"FFmpeg Command: {app_config.ffmpeg.command or 'auto-detect'}")
            click.echo(f"Quick Timeout: {app_config.ffmpeg.quick_timeout}s")
            click.echo(f"Deep Timeout: {app_config.ffmpeg.deep_timeout}s")
            click.echo(f"Recursive Scan: {app_config.scan.recursive}")
            click.echo(f"Extensions: {', '.join(app_config.scan.extensions)}")

            if app_config.trakt.client_id:
                click.echo(f"Trakt Client ID: {app_config.trakt.client_id[:8]}...")
                click.echo(
                    f"Trakt Client Secret: {'***SET***' if app_config.trakt.client_secret else 'Not set'}"
                )
                if app_config.trakt.default_watchlist:
                    click.echo(f"Trakt Default Watchlist: {app_config.trakt.default_watchlist}")
                click.echo(
                    f"Trakt Include Statuses: {[status.value for status in app_config.trakt.include_statuses]}"
                )
            else:
                click.echo("Trakt: Not configured")

            click.echo(f"Output Directory: {app_config.output.default_output_dir}")
            if hasattr(app_config.scan, "default_input_dir"):
                click.echo(f"Input Directory: {app_config.scan.default_input_dir}")

    except Exception as e:
        logger.exception("Show config command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# Add command aliases for backward compatibility
@cli.command(hidden=True)
@click.pass_context
def main_command(ctx):
    """Backward compatibility alias for scan command."""
    click.echo("Note: 'main_command' is deprecated. Use 'scan' instead.", err=True)
    ctx.invoke(scan)


# Database command group
@cli.group()
@click.pass_context
def database(ctx):
    """Database operations for scan results.

    Manage persistent storage of scan results in SQLite database.
    Requires database to be enabled in configuration.
    """
    # If no arguments are provided, show the help for the database group
    if ctx.args == []:
        click.echo(ctx.get_help())
        ctx.exit(0)


@database.command()
@global_options
@click.option(
    "--directory",
    "-d",
    help="Filter by directory path",
)
@click.option(
    "--corrupt/--healthy/--all",
    default=None,
    help="Filter by corruption status (default: all)",
)
@click.option(
    "--scan-mode",
    type=click.Choice(["quick", "deep", "hybrid"], case_sensitive=False),
    help="Filter by scan mode",
)
@click.option(
    "--min-confidence",
    type=click.FloatRange(0.0, 1.0),
    help="Minimum confidence level (0.0-1.0)",
)
@click.option(
    "--since",
    help="Show results since date (e.g., '2024-01-01', '7 days ago')",
)
@click.option(
    "--limit",
    type=click.IntRange(1, 10000),
    default=100,
    help="Maximum number of results to show",
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    type=PathType(),
    help="Save query results to file (JSON format)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv"], case_sensitive=False),
    default="table",
    help="Output format",
    show_default=True,
)
@click.pass_context
def query(
    ctx,
    directory,
    corrupt,
    scan_mode,
    min_confidence,
    since,
    limit,
    output,
    output_format,
    config,
):
    """Query scan results from database.

    Search and filter scan results stored in the database with various criteria.

    Examples:

    \b
    # Show all corrupt files
    corrupt-video-inspector database query --corrupt

    \b
    # Show files scanned in the last week
    corrupt-video-inspector database query --since "7 days ago"

    \b
    # Show high-confidence corrupt files
    corrupt-video-inspector database query --corrupt --min-confidence 0.8
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Import database components
        from src.database.models import DatabaseQueryFilter
        from src.database.service import DatabaseService

        # Initialize database service
        db_service = DatabaseService(
            app_config.database.path, app_config.database.auto_cleanup_days
        )

        # Parse since date if provided
        since_timestamp = None
        if since:
            import time
            from datetime import datetime

            # Simple parsing for common formats
            if "days ago" in since:
                days = int(since.split()[0])
                since_timestamp = time.time() - (days * 24 * 60 * 60)
            elif "weeks ago" in since:
                weeks = int(since.split()[0])
                since_timestamp = time.time() - (weeks * 7 * 24 * 60 * 60)
            else:
                # Try parsing as date
                try:
                    dt = datetime.fromisoformat(since)
                    since_timestamp = dt.timestamp()
                except ValueError:
                    click.echo(f"Could not parse date: {since}", err=True)
                    sys.exit(1)

        # Build query filter
        filter_opts = DatabaseQueryFilter(
            directory=directory,
            is_corrupt=corrupt if corrupt is not None else None,
            scan_mode=scan_mode,
            min_confidence=min_confidence,
            since_date=since_timestamp,
            limit=limit,
        )

        # Execute query
        results = db_service.query_results(filter_opts)

        if not results:
            click.echo("No results found matching the criteria.")
            return

        # Output results
        if output_format == "json":
            result_data = [result.model_dump() for result in results]
            if output:
                with output.open("w", encoding="utf-8") as f:
                    json.dump(result_data, f, indent=2)
                click.echo(f"Results saved to {output}")
            else:
                click.echo(json.dumps(result_data, indent=2))

        elif output_format == "csv":
            import csv as csv_module

            if output:
                with output.open("w", newline="", encoding="utf-8") as f:
                    if results:
                        writer = csv_module.DictWriter(f, fieldnames=results[0].model_dump().keys())
                        writer.writeheader()
                        for result in results:
                            writer.writerow(result.model_dump())
                click.echo(f"Results saved to {output}")
            else:
                # Output to stdout
                output_str = io.StringIO()
                if results:
                    writer = csv_module.DictWriter(
                        output_str, fieldnames=results[0].model_dump().keys()
                    )
                    writer.writeheader()
                    for result in results:
                        writer.writerow(result.model_dump())
                click.echo(output_str.getvalue())

        else:  # table format
            click.echo(f"\nFound {len(results)} results:\n")
            click.echo(
                f"{'Filename':<50} {'Status':<10} {'Confidence':<12} {'Size (MB)':<10} {'Scan Date':<12}"
            )
            click.echo("-" * 100)

            for result in results:
                filename = result.filename
                if len(filename) > 47:
                    filename = "..." + filename[-44:]

                status = result.status
                confidence = f"{result.confidence:.2f}"
                size_mb = f"{result.file_size / (1024*1024):.1f}"

                from datetime import datetime

                scan_date = datetime.fromtimestamp(result.created_at).strftime("%Y-%m-%d")

                click.echo(
                    f"{filename:<50} {status:<10} {confidence:<12} {size_mb:<10} {scan_date:<12}"
                )

            if output:
                result_data = [result.model_dump() for result in results]
                with output.open("w", encoding="utf-8") as f:
                    json.dump(result_data, f, indent=2)
                click.echo(f"\nResults also saved to {output}")

    except Exception as e:
        logger.exception("Database query failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@database.command()
@global_options
@click.pass_context
def stats(ctx, config):
    """Show database statistics.

    Display information about database contents, including total scans,
    files, corruption rates, and database size.
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Import database components
        from src.database.service import DatabaseService

        # Initialize database service
        db_service = DatabaseService(
            app_config.database.path, app_config.database.auto_cleanup_days
        )

        # Get statistics
        stats = db_service.get_database_stats()

        click.echo("Database Statistics")
        click.echo("=" * 30)
        click.echo(f"Database Path: {app_config.database.path}")
        click.echo(f"Database Size: {stats.database_size_bytes / (1024*1024):.1f} MB")
        click.echo(f"Total Scans: {stats.total_scans}")
        click.echo(f"Total Files: {stats.total_files}")
        click.echo(f"Corrupt Files: {stats.corrupt_files}")
        click.echo(f"Healthy Files: {stats.healthy_files}")
        click.echo(f"Corruption Rate: {stats.corruption_rate:.1f}%")

        if stats.oldest_scan_date:
            click.echo(f"Oldest Scan: {stats.oldest_scan_date.strftime('%Y-%m-%d %H:%M:%S')}")
        if stats.newest_scan_date:
            click.echo(f"Newest Scan: {stats.newest_scan_date.strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        logger.exception("Database stats failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@database.command()
@global_options
@click.option(
    "--days",
    type=click.IntRange(1, 365),
    required=True,
    help="Delete scans older than this many days",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
@click.pass_context
def cleanup(ctx, days, dry_run, config):
    """Clean up old scan records.

    Remove scans and their results that are older than the specified number of days.

    Examples:

    \b
    # Preview cleanup of scans older than 30 days
    corrupt-video-inspector database cleanup --days 30 --dry-run

    \b
    # Actually clean up old scans
    corrupt-video-inspector database cleanup --days 30
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Import database components
        from src.database.service import DatabaseService

        # Initialize database service
        db_service = DatabaseService(
            app_config.database.path, app_config.database.auto_cleanup_days
        )

        if dry_run:
            # Show what would be deleted
            import time

            cutoff_time = time.time() - (days * 24 * 60 * 60)
            from datetime import datetime

            cutoff_date = datetime.fromtimestamp(cutoff_time)

            click.echo(
                f"DRY RUN: Would delete scans older than {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Get count of scans that would be deleted
            with db_service._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) as count FROM scans WHERE started_at < ?
                """,
                    (cutoff_time,),
                )
                count = cursor.fetchone()["count"]

            click.echo(f"Would delete {count} scans")
        else:
            # Actually perform cleanup
            deleted_count = db_service.cleanup_old_scans(days)
            click.echo(f"Deleted {deleted_count} old scans")

            if deleted_count > 0:
                # Vacuum database to reclaim space
                db_service.vacuum_database()
                click.echo("Database optimized")

    except Exception as e:
        logger.exception("Database cleanup failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@database.command()
@global_options
@click.option(
    "--backup-path",
    type=PathType(),
    required=True,
    help="Path for the backup file",
)
@click.pass_context
def backup(ctx, backup_path, config):
    """Create a database backup.

    Create a complete backup of the scan results database.

    Example:

    \b
    # Create backup
    corrupt-video-inspector database backup --backup-path backup.db
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Import database components
        from src.database.service import DatabaseService

        # Initialize database service
        db_service = DatabaseService(
            app_config.database.path, app_config.database.auto_cleanup_days
        )

        # Create backup
        db_service.backup_database(backup_path)
        click.echo(f"Database backup created: {backup_path}")

    except Exception as e:
        logger.exception("Database backup failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@database.command(name="list-scans")
@global_options
@click.option(
    "--limit",
    type=click.IntRange(1, 1000),
    default=20,
    help="Maximum number of scans to show",
    show_default=True,
)
@click.option(
    "--directory",
    "-d",
    help="Filter by directory path",
)
@click.pass_context
def list_scans(ctx, limit, directory, config):
    """List recent scans from database.

    Show recent scans in reverse chronological order with summary information.

    Examples:

    \b
    # Show last 20 scans
    corrupt-video-inspector database list-scans

    \b
    # Show last 50 scans for specific directory
    corrupt-video-inspector database list-scans --limit 50 --directory /media/videos
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Import database components
        from src.database.service import DatabaseService

        # Initialize database service
        db_service = DatabaseService(
            app_config.database.path, app_config.database.auto_cleanup_days
        )

        # Get recent scans
        scans = db_service.get_recent_scans(limit=limit)

        # Filter by directory if specified
        if directory:
            scans = [s for s in scans if directory in s.directory]

        if not scans:
            click.echo("No scans found.")
            return

        # Display scans in table format
        from datetime import datetime

        click.echo(f"\nFound {len(scans)} scans:\n")
        click.echo(
            f"{'ID':<6} {'Directory':<40} {'Started':<20} {'Files':<8} {'Corrupt':<8} {'Mode':<8} {'Time (s)':<10}"
        )
        click.echo("-" * 110)

        for scan in scans:
            directory_str = scan.directory
            if len(directory_str) > 37:
                directory_str = "..." + directory_str[-34:]

            started = datetime.fromtimestamp(scan.started_at).strftime("%Y-%m-%d %H:%M:%S")
            files = f"{scan.processed_files}/{scan.total_files}"
            corrupt = str(scan.corrupt_files)
            mode = scan.scan_mode
            scan_time = f"{scan.scan_time:.1f}"

            click.echo(
                f"{scan.id:<6} {directory_str:<40} {started:<20} {files:<8} {corrupt:<8} {mode:<8} {scan_time:<10}"
            )

    except Exception as e:
        logger.exception("Failed to list scans")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@database.command()
@global_options
@click.option(
    "--input",
    type=PathType(),
    required=True,
    help="Path to backup file to restore from",
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
@click.pass_context
def restore(ctx, input, force, config):
    """Restore database from backup.

    Restore the database from a previously created backup file.
    This will overwrite the current database.

    Example:

    \b
    # Restore from backup
    corrupt-video-inspector database restore --input backup.db
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Check if backup file exists
        if not input.exists():
            click.echo(f"Error: Backup file not found: {input}", err=True)
            sys.exit(1)

        # Confirm before overwriting
        if not force:
            click.echo(f"This will overwrite the current database at: {app_config.database.path}")
            if not click.confirm("Are you sure you want to continue?"):
                click.echo("Restore cancelled.")
                return

        # Import database components
        import shutil

        # Create backup of current database if it exists
        if app_config.database.path.exists():
            backup_current = app_config.database.path.parent / f"{app_config.database.path.name}.pre-restore"
            shutil.copy2(app_config.database.path, backup_current)
            click.echo(f"Current database backed up to: {backup_current}")

        # Copy backup file to database location
        shutil.copy2(input, app_config.database.path)
        click.echo(f"Database restored from: {input}")

        # Verify restored database
        from src.database.service import DatabaseService

        db_service = DatabaseService(
            app_config.database.path, app_config.database.auto_cleanup_days
        )
        stats = db_service.get_database_stats()
        click.echo(f"Restored database contains {stats.total_scans} scans and {stats.total_files} files")

    except Exception as e:
        logger.exception("Database restore failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@database.command()
@global_options
@click.option(
    "--scan-id",
    type=int,
    help="Export specific scan by ID (default: all results)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["csv", "json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format",
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    type=PathType(),
    help="Save to file (default: stdout)",
)
@click.option(
    "--corrupt-only",
    is_flag=True,
    help="Only export corrupt files",
)
@click.pass_context
def export(ctx, scan_id, output_format, output, corrupt_only, config):
    """Export scan results to various formats.

    Export scan results to CSV, JSON, or YAML format for external analysis.

    Examples:

    \b
    # Export all results to JSON
    corrupt-video-inspector database export --format json --output results.json

    \b
    # Export specific scan to CSV
    corrupt-video-inspector database export --scan-id 123 --format csv --output scan-123.csv

    \b
    # Export only corrupt files to YAML
    corrupt-video-inspector database export --corrupt-only --format yaml --output corrupt.yaml
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Import database components
        from src.database.models import DatabaseQueryFilter
        from src.database.service import DatabaseService

        # Initialize database service
        db_service = DatabaseService(
            app_config.database.path, app_config.database.auto_cleanup_days
        )

        # Get results based on filters
        if scan_id:
            results = db_service.get_scan_results(scan_id)
        else:
            filter_opts = DatabaseQueryFilter(
                is_corrupt=True if corrupt_only else None,
                limit=100000,  # Large limit for export
            )
            results = db_service.query_results(filter_opts)

        if not results:
            click.echo("No results to export.")
            return

        # Convert to dictionaries
        data = [result.model_dump() for result in results]

        # Format output
        if output_format == "json":
            import json

            output_str = json.dumps(data, indent=2)
        elif output_format == "csv":
            import csv as csv_module
            import io

            output_io = io.StringIO()
            if data:
                writer = csv_module.DictWriter(output_io, fieldnames=data[0].keys())
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            output_str = output_io.getvalue()
        elif output_format == "yaml":
            import yaml

            output_str = yaml.dump(data, default_flow_style=False, sort_keys=False)

        # Write to file or stdout
        if output:
            output.write_text(output_str, encoding="utf-8")
            click.echo(f"Exported {len(results)} results to {output}")
        else:
            click.echo(output_str)

    except Exception as e:
        logger.exception("Database export failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
