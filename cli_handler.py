"""
CLI argument parsing and command-line interface functionality for
Corrupt Video Inspector
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

import typer

from trakt_watchlist import sync_to_trakt_watchlist
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
    handlers: list[logging.Handler] = []

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
        except Exception as e:
            logger.exception(f"Could not create log file {env_log_file}: {e}")  # Temporary fallback

    # Log successful file handler addition after configuration
    if env_log_file:
        logger.info(f"Logging to file: {env_log_file}")
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

    logger.info(f"Logging initialized with level: " f"{logging.getLevelName(log_level)}")


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
    verbose: bool,
    quiet: bool,
    max_workers: int,
    json_output: bool,
    output: Optional[str],
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
    help=(
        "Corrupt Video Inspector - Scan directories for corrupt video files " "and sync to Trakt"
    ),
    epilog=(
        """
Examples:
  python3 cli_handler.py /path/to/videos  # Run hybrid mode (default)
  python3 cli_handler.py --mode quick /path  # Quick scan only
  python3 cli_handler.py --mode deep /path  # Deep scan all files
  python3 cli_handler.py --no-resume /path/videos  # CLI without resume
  python3 cli_handler.py --verbose /path/videos  # CLI with verbose output
  python3 cli_handler.py --json /path/videos  # CLI with JSON output
  python3 cli_handler.py --list-videos /path  # List videos only

  # Trakt.tv integration
  python3 cli_handler.py trakt scan_results.json \
    --token YOUR_TOKEN  # Auto sync
  python3 cli_handler.py trakt scan_results.json --token YOUR_TOKEN \
    --interactive  # Interactive mode
  python3 cli_handler.py trakt scan_results.json --token YOUR_TOKEN \
    --verbose -o out.json  # Verbose with output
"""
    ),
    no_args_is_help=True,
)


@app.command()
def main_command(
    directory: Optional[str] = typer.Argument(None, help="Directory to scan for video files"),
    mode: str = typer.Option(
        "hybrid",
        "--mode",
        help=(
            "Scan mode: quick (1min timeout), deep (full scan), "
            "hybrid (quick then deep for suspicious files)"
        ),
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output showing FFmpeg details",
    ),
    no_resume: bool = typer.Option(
        False,
        "--no-resume",
        help="Disable automatic resume functionality (start from beginning)",
    ),
    list_videos: bool = typer.Option(
        False,
        "--list-videos",
        "-l",
        help="List all video files in directory without scanning",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Generate JSON output file with detailed scan results",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Specify custom output file path for results",
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive",
        "-r",
        help="Recursively scan subdirectories",
    ),
    extensions: Optional[List[str]] = None,
    max_workers: int = typer.Option(
        4,
        "--max-workers",
        "-w",
        help="Maximum number of worker threads for parallel processing",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress all output except errors"),
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
) -> None:
    if extensions is None:
        extensions = typer.Option(
            default=None,
            help=("Specify video file extensions to scan " "(e.g., mp4 mkv avi)"),
        )
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

    def _exit():
        raise typer.Exit(1)

    try:
        # Handle version
        if version:
            typer.echo("Corrupt Video Inspector v2.0 (Hybrid Detection)")
            return

        # Validate mode
        if mode not in ["quick", "deep", "hybrid"]:
            logger.error(f"Invalid mode: {mode}")
            typer.echo("Error: Mode must be one of: quick, deep, hybrid", err=True)
            _exit()

        # Setup logging
        setup_logging(verbose and not quiet, quiet)
        logger.info("Starting Corrupt Video Inspector")

        # Validate arguments
        validate_arguments(verbose, quiet, max_workers, json_output, output)

        # Check if directory was provided
        if not directory:
            logger.error("Directory argument is required")
            typer.echo("Error: Directory argument is required", err=True)
            _exit()

        # Validate directory
        # Ensure directory is not None for type checker
        if directory is None:
            logger.error("Directory argument is required (None received)")
            typer.echo("Error: Directory argument is required", err=True)
            _exit()
        try:
            directory_path = validate_directory(str(directory))
        except (FileNotFoundError, NotADirectoryError) as e:
            logger.exception("Directory validation failed")
            typer.echo(f"Error: {e}", err=True)
            _exit()

        # Handle quiet mode
        if quiet:
            logger.debug("Quiet mode enabled, redirecting stdout")
            # Redirect stdout to devnull, keep stderr for errors
            with Path(os.devnull).open("w") as devnull:
                sys.stdout = devnull
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
                    _exit()
                logger.info(f"Found {total_videos} video files to process")
                ffmpeg_cmd = check_system_requirements()
                # Only print scan info if not quiet.
                # Should not happen in quiet mode,
                # but keep logic for completeness.
                # All output is suppressed in quiet mode,
                # so this block is unreachable.
                logger.info(f"Starting scan with mode: {mode}, workers: {max_workers}")
                scan_mode = ScanMode(mode)
                if output and not json_output:
                    json_output = True
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
                return

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
            _exit()

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
        _exit()
    except KeyboardInterrupt:
        logger.warning("Scan interrupted by user")
        typer.echo("\nScan interrupted by user", err=True)
        raise typer.Exit(130) from None  # Standard exit code for Ctrl+C
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        logging.exception("Unexpected error")
        _exit()


def list_video_files(
    directory: Path,
    recursive: bool = False,
    extensions: Optional[List[str]] = None,
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

    except Exception:
        logger.exception("Error listing video files")
        logging.exception("Error listing video files")
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


def exit_with_error(message: str, log_message: Optional[str] = None) -> None:
    """Exit the application with an error message."""
    if log_message:
        logger.error(log_message)
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(1)


def main() -> None:
    """
    Main CLI entry point.

    Raises:
        SystemExit: On various error conditions or user interruption
    """
    app()


@app.command()
def trakt(
    scan_file: str = typer.Argument(
        ...,
        help="Path to JSON scan results file",
    ),
    token: str = typer.Option(
        ...,
        "--token",
        "-t",
        help="Trakt.tv OAuth access token",
    ),
    client_id: Optional[str] = typer.Option(
        None, "--client-id", "-c", help="Trakt.tv API client ID (optional)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Enable interactive selection of search results",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save sync results to JSON file"
    ),
) -> None:
    """
    Sync video scan results to Trakt.tv watchlist.

    This command processes JSON scan results from the video inspector and
    automatically adds discovered movies and TV shows to your Trakt.tv
    watchlist using filename parsing.

    With --interactive mode, you can manually select the correct match when
    multiple search results are found, ensuring accurate additions to your
    watchlist.

    Args:
        scan_file: Path to JSON file containing video scan results
        token: Trakt.tv OAuth 2.0 access token for API authentication
        client_id: Optional Trakt.tv API client ID
        verbose: Enable detailed progress output
        interactive: Enable manual selection of search matches
        output: Optional path to save sync results as JSON
    """

    def _exit():
        raise typer.Exit(1)

    try:
        # Setup logging
        setup_logging(verbose, False)
        logger.info("Starting Trakt watchlist sync command")

        # Validate scan file exists
        scan_file_path = Path(scan_file)
        if not scan_file_path.exists():
            logger.error(f"Scan file not found: {scan_file}")
            typer.echo(f"Error: Scan file not found: {scan_file}", err=True)
            _exit()

        if scan_file_path.suffix.lower() != ".json":
            logger.warning(f"Scan file may not be JSON: {scan_file}")
            typer.echo(f"Warning: File does not have .json extension: {scan_file}")

        if not verbose:
            typer.echo("Syncing scan results to Trakt.tv watchlist...")
            typer.echo(f"Scan file: {scan_file}")
            if interactive:
                typer.echo("Interactive mode: You will be prompted to select matches")
            typer.echo("Processing...")

        # Perform the sync
        try:
            results = sync_to_trakt_watchlist(
                scan_file=str(scan_file_path),
                access_token=token,
                client_id=client_id,
                verbose=verbose,
                interactive=interactive,
            )

            # Save results if requested
            if output:
                output_path = Path(output)
                logger.info(f"Saving sync results to: {output}")

                try:
                    with output_path.open("w", encoding="utf-8") as f:
                        json.dump(results, f, indent=2)

                    if verbose:
                        typer.echo(f"\nSync results saved to: {output}")

                except Exception as e:
                    logger.exception("Failed to save results")
                    typer.echo(f"Warning: Could not save results to {output}: {e}")

            # Exit with appropriate code
            if results["failed"] == results["total"]:
                # All items failed
                logger.error("All items failed to sync")
                _exit()
            if results["failed"] > 0:
                # Some items failed
                logger.warning(f"{results['failed']} items failed to sync")
                # Exit with code 0 for partial success

            logger.info("Trakt sync command completed successfully")

        except FileNotFoundError:
            logger.exception(f"Scan file not found: {scan_file}")
            typer.echo(f"Error: Scan file not found: {scan_file}", err=True)
            raise typer.Exit(1) from None
        except json.JSONDecodeError as e:
            # Remove exception object from logging calls (TRY401)
            logger.exception("Invalid JSON in scan file")
            typer.echo(f"Error: Invalid JSON in scan file: {e}", err=True)
            raise typer.Exit(1) from e
        except Exception as e:
            logger.exception("Sync failed")
            typer.echo(f"Error: Sync failed: {e}", err=True)
            raise typer.Exit(1) from e

    except typer.Exit:
        # Re-raise typer exits without logging
        raise
    except KeyboardInterrupt:
        logger.warning("Trakt sync interrupted by user")
        typer.echo("\nSync interrupted by user", err=True)
        raise typer.Exit(130) from None
    except Exception as e:
        logger.critical(f"Unexpected error in Trakt sync: {e}", exc_info=True)
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e


if __name__ == "__main__":
    main()
