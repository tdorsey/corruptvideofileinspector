"""
CLI command definitions using Click framework.
"""

import csv
import io
import json
import logging
import sys
from pathlib import Path

import click

from src.cli.handlers import ListHandler, ScanHandler, TraktHandler
from src.cli.utils import setup_logging
from src.config import load_config
from src.core.models.inspection import VideoFile
from src.core.models.scanning import FileStatus, ScanMode, ScanResult, ScanSummary
from src.core.reporter import ReportService
from src.ffmpeg.ffmpeg_client import FFmpegClient

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
    # Setup logging first
    setup_logging(0)

    # Load configuration
    try:
        app_config = load_config(config_path=config) if config else load_config()
        ctx.ensure_object(dict)
        ctx.obj["config"] = app_config
    except Exception as e:
        logging.exception("Configuration error")
        raise click.Abort() from e

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
@click.pass_context
def scan(
    ctx,
    directory,
    mode,
    max_workers,
    recursive,
    extensions,
    resume,
    output,
    output_format,
    pretty,
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

    Examples:

    \b
    # Basic hybrid scan
    corrupt-video-inspector scan /path/to/videos

    \b
    # Quick scan with custom output
    corrupt-video-inspector scan --mode quick --output results.json /path/to/videos

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
            output_file=output,
            output_format=output_format,
            pretty_print=pretty,
        )
        if summary is not None:
            click.echo("\nScan Summary:")
            click.echo(json.dumps(summary.model_dump(), indent=2 if pretty else None))
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
    # If no arguments are provided, show the help for the trakt group
    if ctx.args == []:
        click.echo(ctx.get_help())
        ctx.exit(0)
    """
    Trakt.tv integration commands.

    Sync scan results to your Trakt.tv watchlist by parsing filenames
    and matching them against Trakt's database.
    """


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

    Examples:

    \b
    # Basic sync to main watchlist
    corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN

    \b
    # Sync to a specific watchlist
    corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN \\
        --watchlist "my-custom-list"

    \b
    # Interactive sync with output
    corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN \\
        --interactive --output sync_results.json

    \b
    # Dry run to see what would be synced
    corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN --dry-run
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
            output_file=output,
            watchlist=watchlist,
            include_statuses=include_statuses,
        )

        if dry_run:
            click.echo("DRY RUN COMPLETE")

        click.echo("\nTrakt Sync Result:")
        if result is not None:
            click.echo(json.dumps(result.model_dump(), indent=2))
        else:
            click.echo("No sync result returned.")

    except Exception as e:
        logger.exception("Trakt sync command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@trakt.command()
@click.option("--token", "-t", required=True, help="Trakt.tv OAuth access token")
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
def list_watchlists(token, output, output_format, config):
    """
    List all available watchlists for the authenticated user.

    Shows all custom lists and the main watchlist that the user has access to.

    Examples:

    \b
    # List watchlists in table format
    corrupt-video-inspector trakt list-watchlists --token YOUR_TOKEN

    \b
    # List watchlists in JSON format
    corrupt-video-inspector trakt list-watchlists --token YOUR_TOKEN --format json
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Create and run Trakt handler
        handler = TraktHandler(app_config)
        watchlists = handler.list_watchlists(access_token=token)

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

    except Exception as e:
        logger.exception("List watchlists command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@trakt.command()
@click.option("--token", "-t", required=True, help="Trakt.tv OAuth access token")
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
def view(token, watchlist, output, output_format, config):
    """
    View items in a specific watchlist.

    Shows all movies and TV shows in the specified watchlist.
    If no watchlist is specified, shows items from the main watchlist.

    Examples:

    \b
    # View main watchlist
    corrupt-video-inspector trakt view --token YOUR_TOKEN

    \b
    # View a specific custom list
    corrupt-video-inspector trakt view --token YOUR_TOKEN --watchlist "my-list"

    \b
    # View watchlist in JSON format
    corrupt-video-inspector trakt view --token YOUR_TOKEN --format json
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Create and run Trakt handler
        handler = TraktHandler(app_config)
        items = handler.view_watchlist(access_token=token, watchlist=watchlist)

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

    except Exception as e:
        logger.exception("View watchlist command failed")
        click.echo(f"Error: {e}", err=True)
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
    # If no arguments are provided, show the help for the report subcommand
    if ctx.args == [] and scan_file is None:
        click.echo(ctx.get_help())
        ctx.exit(0)
    """
    Generate a detailed report from scan results.

    Creates formatted reports with statistics, file lists, and analysis
    from JSON scan results.

    Examples:

    \b
    # Generate HTML report
    corrupt-video-inspector report results.json

    """
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
@click.pass_context
def show_config(ctx, all_configs, config):
    # If no arguments are provided, show the help for the show-config subcommand
    if ctx.args == []:
        click.echo(ctx.get_help())
        ctx.exit(0)
    """
    Show current configuration settings.

    Displays the effective configuration after loading from all sources
    (defaults, files, environment variables, etc.).
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        if all_configs:
            # Show detailed configuration
            config_dict = app_config.model_dump()
            click.echo(json.dumps(config_dict, indent=2))
        else:
            # Show key settings
            click.echo("Current Configuration")
            click.echo("=" * 30)
            click.echo(f"Log Level: {app_config.logging.level}")
            click.echo(f"Max Workers: {app_config.scan.max_workers}")
            click.echo(f"Default Scan Mode: {app_config.scan.mode}")
            click.echo(f"FFmpeg Command: {app_config.ffmpeg.command or 'auto-detect'}")
            click.echo(f"Quick Timeout: {app_config.ffmpeg.quick_timeout}s")
            click.echo(f"Deep Timeout: {app_config.ffmpeg.deep_timeout}s")

            if app_config.trakt.client_id:
                click.echo(f"Trakt Client ID: {app_config.trakt.client_id[:8]}...")
            else:
                click.echo("Trakt Client ID: Not configured")

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


if __name__ == "__main__":
    cli()
