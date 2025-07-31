"""
CLI command definitions using Click framework.
"""

import json
import logging
import sys
from pathlib import Path

import click  # type: ignore

from src.cli.handlers import ListHandler, ScanHandler, TraktHandler
from src.cli.utils import setup_logging
from src.config import load_config
from src.core.models.inspection import VideoFile
from src.core.models.scanning import ScanMode, ScanResult, ScanSummary
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
    f = click.option(
        "--config",
        "-c",
        type=PathType(exists=True),
        help="Path to configuration file (JSON or YAML)",
    )(f)
    f = click.option(
        "--verbose",
        "-v",
        is_flag=True,
        help="Enable verbose output",
    )(f)
    f = click.option(
        "--quiet",
        "-q",
        is_flag=True,
        help="Suppress all output except errors",
    )(f)
    return click.option(
        "--profile",
        type=click.Choice(["default", "development", "production"]),
        help="Configuration profile to use",
    )(f)


# Main CLI group moved from main.py
@click.group(invoke_without_command=True)
@click.version_option(
    version=None,  # Will be set from src.version.__version__ in main.py
    prog_name="corrupt-video-inspector",
    message="%(prog)s %(version)s",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (can be used multiple times: -v, -vv)",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.pass_context
def cli(ctx, verbose: int | None) -> None:
    """Corrupt Video Inspector - Detect and manage corrupted video files.

    A comprehensive tool for scanning video directories, detecting corruption
    using FFmpeg, and optionally syncing healthy files to Trakt.tv.

    Examples:
        corrupt-video-inspector scan /path/to/videos
        corrupt-video-inspector scan /movies --mode deep --recursive
        corrupt-video-inspector scan /tv-shows --trakt-sync
    """
    # Setup logging first
    setup_logging(verbose or 0)

    # Load configuration
    try:
        app_config = load_config()
        ctx.ensure_object(dict)
        ctx.obj["config"] = app_config
        ctx.obj["verbose"] = verbose
    except Exception as e:
        logging.exception("Configuration error")
        raise click.Abort() from e

    # If no command specified, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@global_options
@click.argument("directory", type=PathType(exists=True, file_okay=False))
@click.option(
    "--mode",
    "-m",
    type=ScanModeChoice(),
    default=ScanMode.HYBRID,
    help="Scan mode: quick (1min timeout), deep (full scan), hybrid (quick then deep for suspicious)",
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
@click.option("--output", "-o", type=PathType(), help="Output file path for results")
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
    directory,
    mode,
    max_workers,
    recursive,
    extensions,
    output,
    output_format,
    pretty,
    config,
):
    """
    Scan a directory for corrupt video files.

    Uses FFmpeg to analyze video files and detect corruption. Supports three scan modes:

    \b
    - quick: Fast scan with 1-minute timeout per file
    - deep: Full scan with 15-minute timeout per file
    - hybrid: Quick scan first, then deep scan for suspicious files

    Examples:

    \b
    # Basic hybrid scan
    corrupt-video-inspector scan /path/to/videos

    \b
    # Quick scan with custom output
    corrupt-video-inspector scan --mode quick --output results.json /path/to/videos

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

        # Create and run scan handler
        handler = ScanHandler(app_config)
        handler.run_scan(
            directory=directory,
            scan_mode=mode,
            recursive=recursive,
            output_file=output,
            output_format=output_format,
            pretty_print=pretty,
        )

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
    directory,
    recursive,
    extensions,
    output,
    output_format,
    config,
):
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
        handler.list_files(
            directory=directory,
            recursive=recursive,
            output_file=output,
            output_format=output_format,
        )

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


@trakt.command()
@click.argument("scan_file", type=PathType(exists=True))
@click.option("--token", "-t", required=True, help="Trakt.tv OAuth access token")
@click.option("--client-id", help="Trakt.tv API client ID (can be set via config or env var)")
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
    "--filter-corrupt/--include-corrupt",
    default=True,
    help="Filter out corrupt files from sync (default: filter out)",
    show_default=True,
)
@global_options
@click.pass_context
def sync(
    scan_file,
    token,
    client_id,
    interactive,
    dry_run,
    output,
    filter_corrupt,
    config,
):
    """
    Sync scan results to Trakt.tv watchlist.

    Processes a JSON scan results file and adds discovered movies and TV shows
    to your Trakt.tv watchlist using filename parsing and search matching.

    Examples:

    \b
    # Basic sync
    corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN

    \b
    # Interactive sync with output
    corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN \\
        --interactive --output sync_results.json

    \b
    # Dry run to see what would be synced
    corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN --dry-run
    """
    try:
        # Load configuration
        app_config = load_config(config_path=config)

        # Override config with CLI options
        if client_id:
            app_config.trakt.client_id = client_id

        # Setup logging

        # Create and run Trakt handler
        handler = TraktHandler(app_config)
        handler.sync_to_watchlist(
            scan_file=scan_file,
            access_token=token,
            interactive=interactive,
            dry_run=dry_run,
            filter_corrupt=filter_corrupt,
            output_file=output,
        )

    except Exception as e:
        logger.exception("Trakt sync command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@global_options
@click.pass_context
def test_ffmpeg(config):
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
@click.argument("scan_file", type=PathType(exists=True))
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
    scan_file,
    output,
    include_healthy,
):
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
        app_config = load_config()

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
            video_file = VideoFile(Path(result_data.get("filename", "")))
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
            format="text",
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
def show_config(all_configs, config):
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
