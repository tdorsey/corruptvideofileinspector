"""Main CLI entry point for corrupt-video-inspector."""

from __future__ import annotations

import logging
import sys
from typing import NoReturn

import click  # type: ignore
from rich.console import Console  # type: ignore

from src.cli.commands import cli

# Setup rich console for beautiful output
console = Console()


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
