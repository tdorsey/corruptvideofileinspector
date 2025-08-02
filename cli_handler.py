import json
import logging
import os
import sys
from pathlib import Path
from shutil import which
from typing import List, Optional

import typer

from src.config import load_config
from src.core.scanner import VideoScanner

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


def validate_arguments(
    verbose: bool,
    quiet: bool,
    max_workers: int,
    json_output: bool,
    output,
) -> None:
    """
    Validate CLI arguments for consistency.

    Raises typer.Exit if invalid.
    """
    if verbose and quiet:
        raise typer.Exit(code=1)
    if max_workers < 1:
        raise typer.Exit(code=1)
    if output and not json_output:
        logging.warning("Output specified without JSON flag; output may not be JSON")


def get_ffmpeg_command() -> str | None:
    """
    Detects ffmpeg command in PATH.

    Returns path or None.
    """
    # already imported at top
    return which("ffmpeg")


def check_system_requirements() -> str:
    """
    Ensure FFmpeg is available, returning its command or exiting.
    """
    cmd = get_ffmpeg_command()
    if not cmd:
        typer.echo("FFmpeg not found")
        raise typer.Exit(code=1)
    return cmd


def get_all_video_object_files(
    directory,
    recursive: bool = True,
    extensions=None,
):
    """
    Return list of video file objects (paths or models).
    Accepts str or Path for directory.
    """
    if isinstance(directory, str):
        directory = Path(directory)
    config = load_config()
    scanner = VideoScanner(config)
    if extensions:
        scanner.config.scan.extensions = extensions
    return scanner.get_video_files(directory, recursive=recursive)


def validate_directory(directory) -> Path:
    """
    Validate that the given directory exists and is a directory.
    Returns the resolved Path if valid, else raises appropriate error.
    """
    path = Path(directory).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    return path


def list_video_files(
    directory: Path,
    recursive: bool = True,
    extensions=None,
) -> None:
    """
    List video files in directory and echo results.

    Exits on errors.
    """
    try:
        files = get_all_video_object_files(directory, recursive, extensions)
        if files:
            for f in files:
                typer.echo(f)
        else:
            typer.echo("No video files found")
    except Exception:
        logging.exception("Error listing video files")
        raise SystemExit from None
