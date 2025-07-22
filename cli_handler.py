"""
CLI argument parsing and command-line interface functionality for Corrupt Video Inspector
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, List

import typer

from utils import count_all_video_files
from video_inspector import (
    ScanMode,
    get_all_video_object_files,
    get_ffmpeg_command,
    inspect_video_files_cli,
)

# Configure module logger
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """
    Setup comprehensive logging configuration with appropriate log levels.

    Supports configuration via environment variables:
    - CORRUPT_VIDEO_INSPECTOR_LOG_LEVEL: Set log level (DEBUG, INFO, WARNING, ERROR)
    - CORRUPT_VIDEO_INSPECTOR_LOG_FILE: Set log file path
    - CORRUPT_VIDEO_INSPECTOR_LOG_FORMAT: Set custom log format

    Args:
        verbose: Enable debug-level logging
        quiet: Suppress all but error-level logging
    """
    # Check environment variables for log configuration
    env_log_level = os.getenv("CORRUPT_VIDEO_INSPECTOR_LOG_LEVEL", "").upper()
    env_log_file = os.getenv("CORRUPT_VIDEO_INSPECTOR_LOG_FILE")
    env_log_format = os.getenv("CORRUPT_VIDEO_INSPECTOR_LOG_FORMAT")

    # Determine log level based on environment, then command line args
    if env_log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        log_level = getattr(logging, env_log_level)
    elif quiet:
        log_level = logging.ERROR
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    # Set log format (environment variable overrides default)
    log_format = env_log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure handlers
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    handlers.append(console_handler)

    # File handler if specified
    if env_log_file:
        try:
            file_handler = logging.FileHandler(env_log_file)
            file_handler.setFormatter(logging.Formatter(log_format, date_format))
            handlers.append(file_handler)
            logger.info(f"Logging to file: {env_log_file}")
        except Exception as e:
            logger.warning(f"Could not create log file {env_log_file}: {e}")

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True,  # Override any existing configuration
    )

    # Set specific loggers to appropriate levels
    logging.getLogger("video_inspector").setLevel(log_level)
    logging.getLogger("utils").setLevel(log_level)

    # Log configuration details
    logger.info(f"Logging initialized with level: {logging.getLevelName(log_level)}")
    if env_log_level:
        logger.info(f"Log level set via environment variable: {env_log_level}")
    if env_log_file:
        logger.info(f"Log file configured via environment variable: {env_log_file}")
    if env_log_format:
        logger.info(f"Log format set via environment variable")


def validate_directory(directory: str) -> Path:
    """
    Validate and return Path object for directory.

    Args:
        directory: Path to directory to validate

    Returns:
        Path: Resolved path object

    Raises:
        FileNotFoundError: If directory does not exist
        NotADirectoryError: If path is not a directory
    """
    path = Path(directory).resolve()
    if not path.exists():
        logger.error(f"Directory '{path}' does not exist")
        raise FileNotFoundError(f"Directory '{path}' does not exist.")
    if not path.is_dir():
        logger.error(f"Path '{path}' is not a directory")
        raise NotADirectoryError(f"Path '{path}' is not a directory.")

    logger.debug(f"Validated directory: {path}")
    return path


def validate_arguments(
    verbose: bool, quiet: bool, max_workers: int, json_output: bool, output: Optional[str]
) -> None:
    """
    Validate argument combinations and values.

    Args:
        verbose: Verbose mode flag
        quiet: Quiet mode flag
        max_workers: Number of worker threads
        json_output: JSON output flag
        output: Output file path

    Raises:
        typer.Exit: If argument combinations are invalid
    """
    if verbose and quiet:
        logger.error("Cannot use --verbose and --quiet together")
        typer.echo("Error: Cannot use --verbose and --quiet together", err=True)
        raise typer.Exit(1)

    if max_workers <= 0:
        logger.error("Max workers must be a positive integer")
        typer.echo("Error: Max workers must be a positive integer", err=True)
        raise typer.Exit(1)

    if output and not json_output:
        logger.warning("--output specified without --json, enabling JSON output")
        typer.echo("Warning: --output specified without --json, enabling JSON output")

    logger.debug("Arguments validated successfully")


# Create the typer app
app = typer.Typer(
    help="Corrupt Video Inspector - Scan directories for corrupt video files",
    epilog="""
Examples:
  python3 cli_handler.py /path/to/videos                    # Run hybrid mode (default)
  python3 cli_handler.py --mode quick /path                 # Quick scan only
  python3 cli_handler.py --mode deep /path                  # Deep scan all files
  python3 cli_handler.py --no-resume /path/videos           # CLI without resume
  python3 cli_handler.py --verbose /path/videos             # CLI with verbose output
  python3 cli_handler.py --json /path/videos                # CLI with JSON output
  python3 cli_handler.py --list-videos /path                # List videos only
""",
    no_args_is_help=True,
)


@app.command()
def main_command(
    directory: Optional[str] = typer.Argument(None, help="Directory to scan for video files"),
    mode: str = typer.Option(
        "hybrid",
        "--mode",
        help="Scan mode: quick (1min timeout), deep (full scan), hybrid (quick then deep for suspicious files)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output showing FFmpeg details"
    ),
    no_resume: bool = typer.Option(
        False, "--no-resume", help="Disable automatic resume functionality (start from beginning)"
    ),
    list_videos: bool = typer.Option(
        False, "--list-videos", "-l", help="List all video files in directory without scanning"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Generate JSON output file with detailed scan results"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Specify custom output file path for results"
    ),
    recursive: bool = typer.Option(
        True, "--recursive", "-r", help="Recursively scan subdirectories"
    ),
    extensions: Optional[List[str]] = typer.Option(
        None, "--extensions", "-e", help="Specify video file extensions to scan (e.g., mp4 mkv avi)"
    ),
    max_workers: int = typer.Option(
        4, "--max-workers", "-w", help="Maximum number of worker threads for parallel processing"
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress all output except errors"),
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
) -> None:
    """
    Main CLI command for Corrupt Video Inspector.

    Args:
        directory: Directory to scan for video files
        mode: Scan mode (quick, deep, or hybrid)
        verbose: Enable verbose output
        no_resume: Disable resume functionality
        list_videos: Only list video files without scanning
        json_output: Generate JSON output
        output: Custom output file path
        recursive: Scan subdirectories recursively
        extensions: Video file extensions to scan
        max_workers: Number of worker threads
        quiet: Suppress all output except errors
        version: Show version and exit
    """
    try:
        # Handle version
        if version:
            typer.echo("Corrupt Video Inspector v2.0 (Hybrid Detection)")
            return

        # Validate mode
        if mode not in ["quick", "deep", "hybrid"]:
            logger.error(f"Invalid mode: {mode}")
            typer.echo("Error: Mode must be one of: quick, deep, hybrid", err=True)
            raise typer.Exit(1)

        # Setup logging
        setup_logging(verbose and not quiet, quiet)
        logger.info("Starting Corrupt Video Inspector")

        # Validate arguments
        validate_arguments(verbose, quiet, max_workers, json_output, output)

        # Check if directory was provided
        if not directory:
            logger.error("Directory argument is required")
            typer.echo("Error: Directory argument is required", err=True)
            raise typer.Exit(1)

        # Validate directory
        try:
            directory_path = validate_directory(directory)
        except (FileNotFoundError, NotADirectoryError) as e:
            logger.exception("Directory validation failed")
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from e

        # Handle quiet mode
        if quiet:
            logger.debug("Quiet mode enabled, redirecting stdout")
            # Redirect stdout to devnull, keep stderr for errors
            sys.stdout = open(os.devnull, "w")

        # Handle list-videos option
        if list_videos:
            logger.info("Listing video files only")
            list_video_files(directory_path, recursive, extensions)
            return

        # Check if directory has video files
        logger.debug("Counting video files in directory")
        total_videos = count_all_video_files(str(directory_path))
        if total_videos == 0:
            logger.warning(f"No video files found in directory: {directory_path}")
            typer.echo(f"No video files found in directory: {directory_path}")
            if extensions:
                extension_list = ", ".join(extensions)
                logger.info(f"Searched for extensions: {extension_list}")
                typer.echo(f"Searched for extensions: {extension_list}")
            raise typer.Exit(1)

        logger.info(f"Found {total_videos} video files to process")

        # Check system requirements
        ffmpeg_cmd = check_system_requirements()

        if not quiet:
            typer.echo("Starting video corruption scan...")
            typer.echo(f"Directory: {directory_path}")
            typer.echo(f"Scan mode: {mode.upper()}")
            if mode == "hybrid":
                typer.echo("  Phase 1: Quick scan all files (1min timeout)")
                typer.echo("  Phase 2: Deep scan suspicious files (15min timeout)")
            elif mode == "quick":
                typer.echo("  Quick scan only (1min timeout per file)")
            elif mode == "deep":
                typer.echo("  Deep scan all files (15min timeout per file)")
            typer.echo(f"Platform: {sys.platform}")
            typer.echo(f"Using ffmpeg: {ffmpeg_cmd}")
            typer.echo(f"Max workers: {max_workers}")
            if recursive:
                typer.echo("Recursive scanning: enabled")
            if extensions:
                typer.echo(f"File extensions: {', '.join(extensions)}")

        logger.info(f"Starting scan with mode: {mode}, workers: {max_workers}")

        # Convert mode string to enum
        scan_mode = ScanMode(mode)

        # Enable JSON output if output file is specified
        if output and not json_output:
            json_output = True

        # Start the inspection using video_inspector module
        inspect_video_files_cli(
            directory=str(directory_path),
            resume=not no_resume,
            verbose=verbose and not quiet,
            json_output=json_output,
            output_file=output,
            recursive=recursive,
            extensions=extensions,
            max_workers=max_workers,
            scan_mode=scan_mode,
        )

        logger.info("Video inspection completed successfully")

    except typer.Exit:
        # Re-raise typer exits without logging
        raise
    except ValueError as e:
        logger.exception("Configuration error")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e
    except KeyboardInterrupt:
        logger.warning("Scan interrupted by user")
        typer.echo("\nScan interrupted by user", err=True)
        raise typer.Exit(130) from None  # Standard exit code for Ctrl+C
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        logging.exception(f"Unexpected error: {e}")
        raise typer.Exit(1)
    finally:
        # Restore stdout if it was redirected
        if hasattr(sys.stdout, "close") and sys.stdout != sys.__stdout__:
            sys.stdout.close()
            sys.stdout = sys.__stdout__


def list_video_files(
    directory: Path, recursive: bool = False, extensions: Optional[List[str]] = None
) -> None:
    """
    List all video files in directory.

    Args:
        directory: Path to directory to scan
        recursive: Whether to scan subdirectories recursively
        extensions: List of file extensions to include
    """
    logger.info(f"Scanning directory: {directory}")
    typer.echo(f"Scanning directory: {directory}")
    if recursive:
        logger.info("Including subdirectories in scan")
        typer.echo("(including subdirectories)")

    try:
        video_files = get_all_video_object_files(str(directory), recursive, extensions)

        total_count = len(video_files)
        logger.info(f"Found {total_count} video files")

        if total_count == 0:
            logger.warning("No video files found in the specified directory")
            typer.echo("No video files found in the specified directory.")
            if extensions:
                extension_list = ", ".join(extensions)
                logger.info(f"Searched for extensions: {extension_list}")
                typer.echo(f"Searched for extensions: {extension_list}")
        else:
            typer.echo(f"\nFound {total_count} video files:")
            for i, video in enumerate(video_files, 1):
                rel_path = Path(video.filename).relative_to(directory)
                size_mb = Path(video.filename).stat().st_size / (1024 * 1024)
                typer.echo(f"  {i:3d}: {rel_path} ({size_mb:.1f} MB)")
                logger.debug(f"Video file {i}: {rel_path} ({size_mb:.1f} MB)")

    except Exception as e:
        logger.exception(f"Error listing video files: {e}")
        logging.exception(f"Error listing video files: {e}")
        sys.exit(1)


def check_system_requirements() -> str:
    """
    Check system requirements and return ffmpeg command.

    Returns:
        str: Path to ffmpeg command

    Raises:
        typer.Exit: If ffmpeg is not found
    """
    logger.debug("Checking for ffmpeg installation")
    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        logger.error("ffmpeg is required but not found on this system")
        typer.echo("\nError: ffmpeg is required but not found on this system.")
        typer.echo("Please install ffmpeg:")
        typer.echo("  - On Ubuntu/Debian: sudo apt install ffmpeg")
        typer.echo("  - On CentOS/RHEL: sudo yum install ffmpeg")
        typer.echo("  - On macOS: brew install ffmpeg")
        typer.echo("  - On Windows: Download from https://ffmpeg.org/download.html")
        raise typer.Exit(1)

    logger.info(f"Found ffmpeg at: {ffmpeg_cmd}")
    return ffmpeg_cmd


def main() -> None:
    """
    Main CLI entry point.

    Raises:
        SystemExit: On various error conditions or user interruption
    """
    app()


if __name__ == "__main__":
    main()
