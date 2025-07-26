"""
CLI command definitions using Click framework.
"""

import json
import logging
import sys
from pathlib import Path

import click

from ..config import load_config
from ..core.models import ScanMode
from ..utils import setup_logging
from .handlers import ListHandler, ScanHandler, TraktHandler

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


@click.group()
@click.version_option(version="2.0.0", prog_name="corrupt-video-inspector")
@click.pass_context
def cli(ctx):
    """
    Corrupt Video Inspector - Scan directories for corrupt video files and sync to Trakt.

    A comprehensive tool for detecting corrupted video files using FFmpeg and
    optionally syncing healthy files to your Trakt.tv watchlist.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)


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
    verbose,
    quiet,
    profile,
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
        app_config = load_config(config_file=config, profile=profile)

        # Override config with CLI options
        if max_workers:
            app_config.scanner.max_workers = max_workers
        if extensions:
            app_config.scanner.extensions = [
                f".{ext}" if not ext.startswith(".") else ext for ext in extensions
            ]

        # Setup logging
        setup_logging(app_config.logging, verbose, quiet)

        # Create and run scan handler
        handler = ScanHandler(app_config)
        handler.run_scan(
            directory=directory,
            scan_mode=mode,
            recursive=recursive,
            resume=resume,
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
    ctx,
    directory,
    recursive,
    extensions,
    output,
    output_format,
    config,
    verbose,
    quiet,
    profile,
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
        app_config = load_config(config_file=config, profile=profile)

        # Override config with CLI options
        if extensions:
            app_config.scanner.extensions = [
                f".{ext}" if not ext.startswith(".") else ext for ext in extensions
            ]

        # Setup logging
        setup_logging(app_config.logging, verbose, quiet)

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
@global_options
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
@click.pass_context
def sync(
    ctx,
    scan_file,
    token,
    client_id,
    interactive,
    dry_run,
    output,
    filter_corrupt,
    config,
    verbose,
    quiet,
    profile,
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
        app_config = load_config(config_file=config, profile=profile)

        # Override config with CLI options
        if client_id:
            app_config.trakt.client_id = client_id

        # Setup logging
        setup_logging(app_config.logging, verbose, quiet)

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
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"], case_sensitive=False),
    default="yaml",
    help="Configuration file format",
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    type=PathType(),
    default="config.yml",
    help="Output file path",
    show_default=True,
)
@click.pass_context
def init_config(ctx, output_format, output, config, verbose, quiet, profile):
    """
    Generate an example configuration file.

    Creates a configuration file with all available options and their
    default values, which you can then customize for your needs.

    Examples:

    \b
    # Generate YAML config
    corrupt-video-inspector init-config

    \b
    # Generate JSON config
    corrupt-video-inspector init-config --format json --output config.json
    """
    try:
        from ..config import create_example_config

        create_example_config(output, output_format)
        click.echo(f"Configuration file created: {output}")

    except Exception as e:
        logger.exception("Config init command failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@global_options
@click.pass_context
def test_ffmpeg(ctx, config, verbose, quiet, profile):
    """
    Test FFmpeg installation and show diagnostic information.

    Validates that FFmpeg is properly installed and accessible,
    showing version information and supported formats.
    """
    try:
        # Load configuration
        app_config = load_config(config_file=config, profile=profile)

        # Setup logging
        setup_logging(app_config.logging, verbose, quiet)

        # Test FFmpeg
        from ..integrations.ffmpeg.client import FFmpegClient

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
    ctx,
    scan_file,
    output,
    output_format,
    include_healthy,
    config,
    verbose,
    quiet,
    profile,
):
    """
    Generate a detailed report from scan results.

    Creates formatted reports with statistics, file lists, and analysis
    from JSON scan results.

    Examples:

    \b
    # Generate HTML report
    corrupt-video-inspector report results.json

    \b
    # Generate PDF report with only corrupt files
    corrupt-video-inspector report results.json --format pdf --corrupt-only
    """
    try:
        # Load configuration
        app_config = load_config(config_file=config, profile=profile)

        # Setup logging
        setup_logging(app_config.logging, verbose, quiet)

        # Generate report
        from ..utils import ReportGenerator

        generator = ReportGenerator(app_config)
        report_path = generator.generate_report(
            scan_file=scan_file,
            output_file=output,
            format=output_format,
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
def show_config(ctx, all_configs, config, verbose, quiet, profile):
    """
    Show current configuration settings.

    Displays the effective configuration after loading from all sources
    (defaults, files, environment variables, etc.).
    """
    try:
        # Load configuration
        app_config = load_config(config_file=config, profile=profile)

        if all_configs:
            # Show detailed configuration
            config_dict = app_config.to_dict()
            click.echo(json.dumps(config_dict, indent=2))
        else:
            # Show key settings
            click.echo("Current Configuration")
            click.echo("=" * 30)
            click.echo(f"Profile: {app_config.profile}")
            click.echo(f"Debug Mode: {app_config.debug}")
            click.echo(f"Log Level: {app_config.logging.level}")
            click.echo(f"Max Workers: {app_config.scanner.max_workers}")
            click.echo(f"Default Scan Mode: {app_config.scanner.default_mode}")
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
