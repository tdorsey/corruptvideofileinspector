"""
CLI command definitions using Click framework.
"""

import importlib.util
import io
import json
import logging
import sys
from pathlib import Path

import click

from src.cli.handlers import ListHandler, ScanHandler, TraktHandler
from src.cli.logging import setup_logging
from src.config import load_config
from src.core.models.inspection import VideoFile
from src.core.models.scanning import FileStatus, ScanMode, ScanResult, ScanSummary
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

# Constants
MAX_DIRECTORY_DISPLAY_LENGTH = 40


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
    # Setup logging first
    setup_logging(0)

    # Load configuration
    try:
        app_config = load_config(config_path=config) if config else load_config()
        ctx.ensure_object(dict)
        ctx.obj["config"] = app_config
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
    "--resume/--no-resume",
    default=True,
    help="Enable/disable resume functionality",
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path, dir_okay=False),
    help="Output file path for results (must be a file, not a directory)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "yaml", "csv"], case_sensitive=False),
    default="json",
    help="Output format",
    show_default=True,
)
@click.option("--pretty/--no-pretty", default=True, help="Pretty-print output", show_default=True)
@click.option(
    "--incremental/--full-scan",
    default=False,
    help="Skip files that were recently scanned and found healthy",
    show_default=True,
)
@click.pass_context
def scan(
    ctx,
    directory,
    mode,
    max_workers,
    recursive,
    resume,
    output,
    output_format,
    pretty,
    incremental,
    config,
):
    """
    Scan a directory for corrupt video files.

    Uses FFmpeg to analyze video files and detect corruption. Supports four scan modes:

    \\b
    - quick: Fast scan with 1-minute timeout per file
    - deep: Full scan with 15-minute timeout per file
    - hybrid: Quick scan first, then deep scan for suspicious files
    - full: Complete scan of entire video stream without timeout

    Database Integration:

    \\b
    - Results are automatically stored in SQLite database
    - Use --incremental to skip files recently scanned and found healthy
    - Database is automatically created on first run

    File Output:

    \\b
    - Use --output to save results to a JSON file
    - Supports --format json (other formats available: yaml, csv)
    - Use --pretty for formatted JSON output

    Examples:

    \\b
    # Basic hybrid scan
    corrupt-video-inspector scan /path/to/videos

    \\b
    # Quick scan with automatic database storage
    corrupt-video-inspector scan --mode quick /path/to/videos

    \\b
    # Incremental scan (skip recently healthy files)
    corrupt-video-inspector scan --incremental /path/to/videos

    \\b
    # Full scan without timeout (for thorough analysis)
    corrupt-video-inspector scan --mode full /path/to/videos

    Note: All files are probed to determine if they are video files (no extension filtering).
    """
    # If no arguments are provided, show the help for the scan subcommand
    if ctx.args == [] and directory is None:
        click.echo(ctx.get_help())
        ctx.exit(0)
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Override config with CLI options
        if max_workers:
            app_config.scan.max_workers = max_workers

        # Convert mode string to ScanMode enum
        scan_mode = ScanMode(mode.lower())

        # Handle incremental scanning
        if incremental:
            try:
                from src.database.service import DatabaseService

                db_service = DatabaseService(
                    app_config.database.path, app_config.database.auto_cleanup_days
                )

                # Get files that were recently scanned and found healthy
                recent_healthy = db_service.get_files_needing_rescan(
                    str(directory), scan_mode.value
                )
                # Invert the logic - skip files NOT in the rescan list
                # (these are files that were healthy in recent scans)
                click.echo(
                    f"Incremental scan: focusing on {len(recent_healthy)} files that need rescanning"
                )
            except Exception as e:
                logger.warning(f"Could not perform incremental scan: {e}")

        # Create and run scan handler
        handler = ScanHandler(app_config)
        summary = handler.run_scan(
            directory=directory,
            scan_mode=scan_mode,
            recursive=recursive,
            resume=resume,
            output_file=output,
            output_format=output_format,
            pretty_print=pretty,
        )
        if summary is not None:
            click.echo("\nScan Summary:")
            click.echo(json.dumps(summary.model_dump(), indent=2 if pretty else None))

            # Show where results were stored
            if app_config.database.enabled:
                click.echo(f"\nResults stored in database: {app_config.database.path}")
                click.echo("Use 'corrupt-video-inspector database query' to view results")
            if output:
                click.echo(f"Results also saved to file: {output}")
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
    output,
    output_format,
    config,
):
    """
    List all video files in a directory without scanning.

    Displays all video files found in the specified directory.
    Useful for previewing what files would be scanned.

    Examples:

    \\b
    # List all video files in directory (probe-based detection)
    corrupt-video-inspector list-files /path/to/videos

    \\b
    # List files to JSON output
    corrupt-video-inspector list-files --format json /videos
    """
    # If no arguments are provided, show the help for the list-files subcommand
    if ctx.args == [] and directory is None:
        click.echo(ctx.get_help())
        ctx.exit(0)

    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Setup logging

        # Create and run list handler
        handler = ListHandler(app_config)
        video_files = handler.list_files(
            directory=directory,
            recursive=recursive,
        )
        if not video_files:
            click.echo("No video files found in the specified directory.")
        else:
            # Write to output file if specified
            if output:
                handler.output_formatter.write_file_list(
                    video_files=video_files,
                    directory=directory,
                    output_file=output,
                    format=output_format,
                )
                click.echo(f"File list saved to: {output}")

            # Always display to console unless output format is not text
            if not output or output_format == "text":
                click.echo(f"\nFound {len(video_files)} video files:")
                for i, vf in enumerate(video_files, 1):
                    rel_path = vf.path.relative_to(directory)
                    size_mb = vf.size / (1024 * 1024) if vf.size > 0 else 0
                    click.echo(f"  {i:3d}: {rel_path} ({size_mb:.1f} MB)")
            elif output:
                click.echo(f"Found {len(video_files)} video files, saved to {output}")

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
@click.argument("scan_file", type=PathType(exists=True))
@click.option("--client-id", help="Trakt.tv API client ID (overrides config setting)")
@click.option(
    "--interactive/--no-interactive",
    "-i",
    default=False,
    help="Enable interactive selection of search results",
    show_default=True,
)
@click.option("--dry-run", is_flag=True, help="Show what would be synced without actually syncing")
@click.option("--output", "-o", type=PathType(), help="Save sync results to file")
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
    scan_file,
    client_id,
    interactive,
    dry_run,
    output,
    watchlist,
    include_status,
    config,
):
    """
    Sync scan results to Trakt.tv watchlist.

    Processes a JSON scan results file and adds discovered movies and TV shows
    to your Trakt.tv watchlist using filename parsing and search matching.
    Authentication is handled through configuration (config file, environment variables, or Docker secrets).

    Examples:

    \b
    # Basic sync to main watchlist
    corrupt-video-inspector trakt sync results.json

    \b
    # Sync to a specific watchlist
    corrupt-video-inspector trakt sync results.json --watchlist "my-custom-list"

    \b
    # Interactive sync
    corrupt-video-inspector trakt sync results.json --interactive

    \b
    # Dry run to see what would be synced
    corrupt-video-inspector trakt sync results.json --dry-run

    \b
    # Save sync results to file
    corrupt-video-inspector trakt sync results.json --output sync_results.json
    """
    # If no arguments are provided, show the help for the trakt sync subcommand
    if ctx.args == [] and scan_file is None:
        click.echo(ctx.get_help())
        ctx.exit(0)
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Override config with CLI options
        if client_id:
            app_config.trakt.client_id = client_id

        # Setup logging

        # Create and run Trakt handler
        handler = TraktHandler(app_config)

        # Convert status strings to FileStatus enums
        include_statuses = [FileStatus(status) for status in include_status]

        # Handle dry-run mode
        if dry_run:
            click.echo("DRY RUN MODE: No actual syncing will be performed")

        result = handler.sync_to_watchlist(
            scan_file=scan_file,
            interactive=interactive,
            watchlist=watchlist,
            include_statuses=include_statuses,
        )

        if dry_run:
            click.echo("DRY RUN COMPLETE")

        click.echo("\nTrakt Sync Result:")
        if result is not None:
            result_json = json.dumps(result.model_dump(), indent=2)
            click.echo(result_json)

            # Save to output file if specified
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("w", encoding="utf-8") as f:
                    f.write(result_json)
                click.echo(f"Sync results also saved to: {output}")
        else:
            click.echo("No sync result returned.")

            # Create empty result file if output specified
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("w", encoding="utf-8") as f:
                    json.dump({"message": "No sync result returned"}, f, indent=2)
                click.echo(f"Empty result saved to: {output}")

    except Exception as e:
        logger.exception("Trakt sync command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@trakt.command()
@global_options
def list_watchlists(config):
    """
    List all available watchlists for the authenticated user.

    Shows all custom lists and the main watchlist that the user has access to.
    Authentication is handled through configuration (config file, environment variables, or Docker secrets).

    Examples:

    \b
    # List watchlists
    corrupt-video-inspector trakt list-watchlists
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
@global_options
@click.option(
    "--watchlist",
    "-w",
    help="Watchlist name or slug to view (default: main watchlist)",
)
def view(watchlist, config):
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
@click.option(
    "--username",
    help="Trakt username (required for OAuth authentication)",
)
@click.option(
    "--store/--no-store",
    default=True,
    help="Store credentials in ~/.pytrakt.json for automatic loading",
    show_default=True,
)
@click.option(
    "--test-only",
    is_flag=True,
    help="Only test existing authentication",
)
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
    """
    Test FFmpeg installation and show diagnostic information.

    Validates that FFmpeg is properly installed and accessible,
    showing version information and supported formats.
    """
    # If no arguments are provided, show the help for the test-ffmpeg subcommand
    if ctx.args == []:
        click.echo(ctx.get_help())
        ctx.exit(0)

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
@click.argument("video_file", type=PathType(exists=True))
def test_ffprobe(video_file, config):
    """Test FFprobe functionality on a specific video file."""
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        setup_logging(0)

        # Import FFprobe client
        from src.core.models.inspection import VideoFile
        from src.ffmpeg.ffprobe_client import FFprobeClient

        # Test FFprobe installation
        ffprobe = FFprobeClient(app_config.ffmpeg)
        install_results = ffprobe.test_installation()

        click.echo("FFprobe Installation Test")
        click.echo("=" * 40)

        click.echo(f"FFprobe Path: {install_results['ffprobe_path'] or 'Not found'}")
        click.echo(f"FFprobe Available: {'✓' if install_results['ffprobe_available'] else '✗'}")
        click.echo(f"JSON Output: {'✓' if install_results['can_parse_json'] else '✗'}")

        if install_results["version_info"]:
            click.echo(f"Version: {install_results['version_info']}")

        if not install_results["ffprobe_available"]:
            click.echo("\nFFprobe is not available.")
            sys.exit(1)

        # Test probe on actual file
        click.echo(f"\nProbing file: {video_file}")
        click.echo("=" * 40)

        video_file_obj = VideoFile(path=video_file)
        probe_result = ffprobe.probe_file(video_file_obj)

        if probe_result.success:
            click.echo("✓ Probe successful")
            click.echo(
                f"Duration: {probe_result.duration}s"
                if probe_result.duration
                else "Duration: Unknown"
            )
            click.echo(f"File size: {probe_result.file_size} bytes")
            click.echo(f"Video streams: {len(probe_result.video_streams)}")
            click.echo(f"Audio streams: {len(probe_result.audio_streams)}")
            click.echo(f"Valid video file: {'✓' if probe_result.is_valid_video_file else '✗'}")

            if probe_result.streams:
                click.echo("\nStreams:")
                for stream in probe_result.streams:
                    stream_info = f"  Stream {stream.index}: {stream.codec_type.value}"
                    if stream.codec_name:
                        stream_info += f" ({stream.codec_name})"
                    if stream.width and stream.height:
                        stream_info += f" {stream.width}x{stream.height}"
                    click.echo(stream_info)

            if probe_result.format_info:
                click.echo(f"\nFormat: {probe_result.format_info.format_name}")
                if probe_result.format_info.format_long_name:
                    click.echo(f"Description: {probe_result.format_info.format_long_name}")
        else:
            click.echo("✗ Probe failed")
            click.echo(f"Error: {probe_result.error_message}")
            sys.exit(1)

        click.echo("\nFFprobe test completed successfully! ✓")

    except Exception as e:
        logger.exception("FFprobe test command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@global_options
@click.option(
    "--scan-file",
    "-s",
    required=True,
    type=PathType(exists=True),
    help="Path to scan results file (JSON)",
)
@click.option("--output", "-o", type=PathType(), help="Output file for the report")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["html", "pdf", "json"], case_sensitive=False),
    default="html",
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
    scan_file,
    output,
    output_format,
    include_healthy,
    config,
):
    """
    Generate a detailed report from scan results.

    Creates formatted reports with statistics, file lists, and analysis
    from JSON scan results.

    Examples:

    \\b
    # Generate HTML report
    corrupt-video-inspector report results.json
    """
    # If no arguments are provided, show the help for the report subcommand
    if ctx.args == [] and scan_file is None:
        click.echo(ctx.get_help())
        ctx.exit(0)

    try:
        # Load configuration
        app_config = load_config(config_path=config) if config else load_config()

        # Setup logging
        setup_logging(0)
        # Generate report
        # Load scan results from file
        with scan_file.open("r", encoding="utf-8") as f:
            scan_data = json.load(f)

        # Extract summary from scan data
        summary = ScanSummary(
            directory=Path(scan_data.get("directory", "/")),
            total_files=scan_data.get("total_files", 0),
            processed_files=scan_data.get("processed_files", 0),
            corrupt_files=scan_data.get("corrupt_files", 0),
            healthy_files=scan_data.get("healthy_files", 0),
            scan_mode=ScanMode(scan_data.get("scan_mode", "quick")),
            scan_time=scan_data.get("scan_time", 0.0),
        )

        # Extract results
        results = []
        for result_data in scan_data.get("results", []):
            video_file = VideoFile(path=Path(result_data.get("filename", "")))
            result = ScanResult(
                video_file=video_file,
                needs_deep_scan=result_data.get("needs_deep_scan", False),
                error_message=result_data.get("error_message", ""),
            )
            results.append(result)

        # Use ReportService to generate report
        service = ReportService(app_config)
        report_path = service.generate_report(
            summary=summary,
            results=results,
            output_path=output,
            format=output_format.lower(),
            include_healthy=include_healthy,
        )

        click.echo(f"Report generated: {report_path}")

    except Exception as e:
        logger.exception("Report command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@global_options
@click.option("--all-configs", is_flag=True, help="Show all configuration sources and values")
@click.option("--debug", is_flag=True, help="Enable debug logging to see configuration overrides")
@click.pass_context
def show_config(ctx, all_configs, debug, config):
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


@cli.command()
@global_options
@click.option(
    "--directory",
    "-d",
    type=PathType(exists=True, file_okay=False, dir_okay=True),
    help="Filter results by directory path",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    help="Maximum number of results to show (default: 10)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    help="Output format (default: table)",
)
def db_history(config, directory, limit, output_format):
    """Show scan history from database.

    Display previous scan summaries stored in the database.

    Examples:

    \b
    # Show last 10 scans
    corrupt-video-inspector db-history

    \b
    # Show scans for specific directory
    corrupt-video-inspector db-history --directory /path/to/videos

    \b
    # Show results in JSON format
    corrupt-video-inspector db-history --format json
    """
    try:
        app_config = load_config(config_path=config)

        if not app_config.database.enabled:
            click.echo("Database is not enabled in configuration", err=True)
            sys.exit(1)

        from src.output import OutputFormatter

        formatter = OutputFormatter(app_config)

        summaries = formatter.get_scan_history(directory, limit)

        if not summaries:
            location = f" in {directory}" if directory else ""
            click.echo(f"No scan history found{location}")
            return

        if output_format == "json":
            output_data = [summary.model_dump() for summary in summaries]
            click.echo(json.dumps(output_data, indent=2))
        else:
            # Table format
            click.echo(f"\nScan History ({len(summaries)} results):\n")
            click.echo(
                f"{'Directory':<40} {'Mode':<8} {'Files':<8} {'Corrupt':<8} {'Time':<12} {'Date'}"
            )
            click.echo("-" * 90)

            for summary in summaries:
                from datetime import datetime

                date_str = datetime.fromtimestamp(summary.started_at).strftime("%Y-%m-%d %H:%M")
                directory_str = (
                    str(summary.directory)[-MAX_DIRECTORY_DISPLAY_LENGTH:]
                    if len(str(summary.directory)) > MAX_DIRECTORY_DISPLAY_LENGTH
                    else str(summary.directory)
                )

                click.echo(
                    f"{directory_str:<40} {summary.scan_mode.value:<8} "
                    f"{summary.processed_files:<8} {summary.corrupt_files:<8} "
                    f"{summary.scan_time:<12.1f} {date_str}"
                )

    except Exception as e:
        logger.exception("Database history command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@global_options
def db_stats(config):
    """Show database statistics.

    Display information about the database including number of scans,
    file counts, and database size.
    """
    try:
        app_config = load_config(config_path=config)

        from src.output import OutputFormatter

        formatter = OutputFormatter(app_config)

        stats = formatter.get_database_stats()

        if not stats.get("enabled"):
            click.echo("Database is not enabled in configuration", err=True)
            sys.exit(1)

        click.echo("\nDatabase Statistics:")
        click.echo("=" * 20)
        click.echo(f"Database Path: {stats['database_path']}")
        click.echo(f"Database Size: {stats['database_size_mb']:.2f} MB")
        click.echo(f"Total Scans: {stats['total_summaries']}")
        click.echo(f"Completed Scans: {stats['completed_summaries']}")
        click.echo(f"Incomplete Scans: {stats['incomplete_summaries']}")
        click.echo(f"Total File Results: {stats['total_results']}")
        click.echo(f"Corrupt Files Found: {stats['corrupt_files']}")
        click.echo(f"Healthy Files: {stats['healthy_files']}")

    except Exception as e:
        logger.exception("Database stats command failed")
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
    Database is automatically initialized on first use.
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
                # Access filename through video_file relationship if available
                if hasattr(result, "video_file") and result.video_file:
                    filename = result.video_file.file_name
                    file_size = result.video_file.file_size or 0
                else:
                    filename = f"File ID: {result.video_file_id}"
                    file_size = 0

                if len(filename) > 47:
                    filename = "..." + filename[-44:]

                status = "corrupt" if result.is_corrupt else "clean"
                confidence = f"{result.confidence:.2f}" if result.confidence else "N/A"
                size_mb = f"{file_size / (1024*1024):.1f}"

                from datetime import datetime

                scan_date = result.created_at.strftime("%Y-%m-%d")

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


@database.command()
@global_options
@click.option(
    "--limit",
    type=click.IntRange(1, 1000),
    default=100,
    help="Maximum number of files to show",
    show_default=True,
)
@click.option(
    "--video-files-only",
    is_flag=True,
    help="Only show files confirmed as video files via successful container probes",
)
@click.option(
    "--output",
    "-o",
    type=PathType(),
    help="Save file list to file (JSON format)",
)
@click.pass_context
def files(ctx, limit, video_files_only, output, config):
    """List video files in database.

    Show video files that have been discovered and stored in the database,
    with optional filtering for files confirmed as video files via successful probes.

    Examples:

    \b
    # List all files in database
    corrupt-video-inspector database files

    \b
    # List only confirmed video files
    corrupt-video-inspector database files --video-files-only

    \b
    # Export confirmed video files to JSON
    corrupt-video-inspector database files --video-files-only --output video-files.json
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

        # Get video files list
        video_files = db_service.get_video_files_list(
            limit=limit, confirmed_video_only=video_files_only
        )

        if not video_files:
            filter_msg = "confirmed video files" if video_files_only else "files"
            click.echo(f"No {filter_msg} found in database.")
            return

        # Display results
        if output:
            # Export to JSON file
            import json

            file_data = [
                {
                    "id": vf.id,
                    "file_path": vf.file_path,
                    "file_name": vf.file_name,
                    "file_size": vf.file_size,
                    "first_seen": vf.first_seen.isoformat(),
                    "created_at": vf.created_at.isoformat(),
                    "updated_at": vf.updated_at.isoformat(),
                }
                for vf in video_files
            ]

            with output.open("w") as f:
                json.dump(file_data, f, indent=2)

            filter_msg = "confirmed video files" if video_files_only else "files"
            click.echo(f"Exported {len(video_files)} {filter_msg} to {output}")
        else:
            # Display in table format
            filter_msg = "Confirmed Video Files" if video_files_only else "Files"
            click.echo(f"\n{filter_msg} in Database:")
            click.echo("-" * 80)

            for vf in video_files:
                size_str = f"{vf.file_size:,} bytes" if vf.file_size else "unknown size"
                click.echo(f"ID: {vf.id:4} | {vf.file_path} ({size_str})")

            click.echo(f"\nTotal: {len(video_files)} files")

    except Exception as e:
        logger.exception("Database files command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
