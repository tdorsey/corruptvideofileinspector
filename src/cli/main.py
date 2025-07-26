"""Main CLI entry point for corrupt-video-inspector."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import NoReturn

import click
from corrupt_video_inspector import __version__
from corrupt_video_inspector.cli.commands import scan
from corrupt_video_inspector.core.models import ConfigurationError
from rich.console import Console
from rich.logging import RichHandler

from src.config import load_config

# Setup rich console for beautiful output
console = Console()


def setup_logging(verbose: int) -> None:
    """Setup logging configuration based on verbosity level.

    Args:
        verbose: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG).
    """
    level_map = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }

    level = level_map.get(verbose, logging.DEBUG)

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_path=verbose >= 2,
            )
        ],
    )

    # Suppress noisy third-party loggers in production
    if verbose < 2:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


@click.group(invoke_without_command=True)
@click.version_option(
    version=__version__,
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
def cli(ctx: click.Context, verbose: int, config: Path | None) -> None:
    """Corrupt Video Inspector - Detect and manage corrupted video files.

    A comprehensive tool for scanning video directories, detecting corruption
    using FFmpeg, and optionally syncing healthy files to Trakt.tv.

    Examples:
        corrupt-video-inspector scan /path/to/videos
        corrupt-video-inspector scan /movies --mode deep --recursive
        corrupt-video-inspector scan /tv-shows --trakt-sync
    """
    # Setup logging first
    setup_logging(verbose)

    # Load configuration
    try:
        app_config = load_config(config)
        ctx.ensure_object(dict)
        ctx.obj["config"] = app_config
        ctx.obj["verbose"] = verbose
    except ConfigurationError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise click.Abort() from e

    # If no command specified, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Register commands
cli.add_command(scan.scan)


def handle_keyboard_interrupt() -> NoReturn:
    """Handle keyboard interrupt gracefully."""
    console.print("\n[yellow]Operation cancelled by user.[/yellow]")
    sys.exit(130)  # Standard exit code for SIGINT


def handle_general_error(error: Exception) -> NoReturn:
    """Handle general errors with rich formatting.

    Args:
        error: The exception that occurred.
    """
    console.print(f"[red]Error:[/red] {error}")

    # Show traceback in verbose mode
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        console.print_exception()

    sys.exit(1)


def main() -> int:
    """Main entry point with error handling.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    try:
        cli()
        return 0
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except click.Abort:
        # Click already handled the error display
        return 1
    except Exception as e:
        handle_general_error(e)


if __name__ == "__main__":
    sys.exit(main())
