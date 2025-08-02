import logging
from pathlib import Path
from shutil import which
from typing import Optional

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


from typing import Any, Sequence


def get_all_video_object_files(
    directory: Path | str,
    recursive: bool = True,
    extensions: Optional[Sequence[str]] = None,
) -> list[Any]:
    """
    Return list of video file objects (paths or models).
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
