"""
CLI argument parsing and command-line interface functionality for Corrupt Video Inspector
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List
import typer
from utils import count_all_video_files
from video_inspector import get_all_video_object_files, get_ffmpeg_command, inspect_video_files_cli, ScanMode


def setup_logging(verbose: bool) -> None:
    """Setup logging configuration based on verbosity level"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def validate_directory(directory: str) -> Path:
    """Validate and return Path object for directory"""
    path = Path(directory).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Directory '{path}' does not exist.")
    if not path.is_dir():
        raise NotADirectoryError(f"Path '{path}' is not a directory.")
    return path


def parse_cli_arguments():
    """Parse command line arguments - kept for compatibility"""
    # This function is kept for backward compatibility but not used in typer implementation
    pass


def validate_arguments(verbose: bool, quiet: bool, max_workers: int, json_output: bool, output: Optional[str]) -> None:
    """Validate argument combinations and values"""
    if verbose and quiet:
        typer.echo("Error: Cannot use --verbose and --quiet together", err=True)
        raise typer.Exit(1)
    
    if max_workers <= 0:
        typer.echo("Error: Max workers must be a positive integer", err=True)
        raise typer.Exit(1)
    
    if output and not json_output:
        typer.echo("Warning: --output specified without --json, enabling JSON output")


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
    no_args_is_help=True
)


@app.command()
def main_command(
    directory: Optional[str] = typer.Argument(None, help="Directory to scan for video files"),
    mode: str = typer.Option("hybrid", "--mode", help="Scan mode: quick (1min timeout), deep (full scan), hybrid (quick then deep for suspicious files)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output showing FFmpeg details"),
    no_resume: bool = typer.Option(False, "--no-resume", help="Disable automatic resume functionality (start from beginning)"),
    list_videos: bool = typer.Option(False, "--list-videos", "-l", help="List all video files in directory without scanning"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Generate JSON output file with detailed scan results"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Specify custom output file path for results"),
    recursive: bool = typer.Option(True, "--recursive", "-r", help="Recursively scan subdirectories"),
    extensions: Optional[List[str]] = typer.Option(None, "--extensions", "-e", help="Specify video file extensions to scan (e.g., mp4 mkv avi)"),
    max_workers: int = typer.Option(4, "--max-workers", "-w", help="Maximum number of worker threads for parallel processing"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress all output except errors"),
    version: bool = typer.Option(False, "--version", help="Show version and exit")
) -> None:
    """Main CLI command for Corrupt Video Inspector"""
    try:
        # Handle version
        if version:
            typer.echo("Corrupt Video Inspector v2.0 (Hybrid Detection)")
            return
        
        # Validate mode
        if mode not in ['quick', 'deep', 'hybrid']:
            typer.echo(f"Error: Mode must be one of: quick, deep, hybrid", err=True)
            raise typer.Exit(1)
        
        # Setup logging
        setup_logging(verbose and not quiet)
        
        # Validate arguments
        validate_arguments(verbose, quiet, max_workers, json_output, output)
        
        # Check if directory was provided
        if not directory:
            typer.echo("Error: Directory argument is required", err=True)
            raise typer.Exit(1)
        
        # Validate directory
        try:
            directory_path = validate_directory(directory)
        except (FileNotFoundError, NotADirectoryError) as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
        
        # Handle quiet mode
        if quiet:
            # Redirect stdout to devnull, keep stderr for errors
            sys.stdout = open(os.devnull, 'w')
        
        # Handle list-videos option
        if list_videos:
            list_video_files(directory_path, recursive, extensions)
            return
        
        # Check if directory has video files
        total_videos = count_all_video_files(str(directory_path))
        if total_videos == 0:
            typer.echo(f"No video files found in directory: {directory_path}")
            if extensions:
                typer.echo(f"Searched for extensions: {', '.join(extensions)}")
            raise typer.Exit(1)
        
        # Check system requirements
        ffmpeg_cmd = check_system_requirements()
        
        if not quiet:
            typer.echo(f'Starting video corruption scan...')
            typer.echo(f'Directory: {directory_path}')
            typer.echo(f'Scan mode: {mode.upper()}')
            if mode == 'hybrid':
                typer.echo('  Phase 1: Quick scan all files (1min timeout)')
                typer.echo('  Phase 2: Deep scan suspicious files (15min timeout)')
            elif mode == 'quick':
                typer.echo('  Quick scan only (1min timeout per file)')
            elif mode == 'deep':
                typer.echo('  Deep scan all files (15min timeout per file)')
            typer.echo(f'Platform: {sys.platform}')
            typer.echo(f'Using ffmpeg: {ffmpeg_cmd}')
            typer.echo(f'Max workers: {max_workers}')
            if recursive:
                typer.echo('Recursive scanning: enabled')
            if extensions:
                typer.echo(f'File extensions: {", ".join(extensions)}')
        
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
            scan_mode=scan_mode
        )
        
    except typer.Exit as e:
        # Re-raise typer exits without logging
        raise e
    except (ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        typer.echo("\nScan interrupted by user", err=True)
        raise typer.Exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise typer.Exit(1)
    finally:
        # Restore stdout if it was redirected
        if hasattr(sys.stdout, 'close') and sys.stdout != sys.__stdout__:
            sys.stdout.close()
            sys.stdout = sys.__stdout__


def list_video_files(directory: Path, recursive: bool = False, extensions: Optional[List[str]] = None) -> None:
    """List all video files in directory"""
    typer.echo(f'Scanning directory: {directory}')
    if recursive:
        typer.echo('(including subdirectories)')
    
    try:
        video_files = get_all_video_object_files(str(directory), recursive, extensions)
        
        total_count = len(video_files)
        
        if total_count == 0:
            typer.echo('No video files found in the specified directory.')
            if extensions:
                typer.echo(f'Searched for extensions: {", ".join(extensions)}')
        else:
            typer.echo(f'\nFound {total_count} video files:')
            for i, video in enumerate(video_files, 1):
                rel_path = Path(video.filename).relative_to(directory)
                size_mb = Path(video.filename).stat().st_size / (1024 * 1024)
                typer.echo(f'  {i:3d}: {rel_path} ({size_mb:.1f} MB)')
                
    except Exception as e:
        logging.error(f"Error listing video files: {e}")
        sys.exit(1)


def check_system_requirements() -> str:
    """Check system requirements and return ffmpeg command"""
    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        typer.echo("\nError: ffmpeg is required but not found on this system.")
        typer.echo("Please install ffmpeg:")
        typer.echo("  - On Ubuntu/Debian: sudo apt install ffmpeg")
        typer.echo("  - On CentOS/RHEL: sudo yum install ffmpeg")
        typer.echo("  - On macOS: brew install ffmpeg")
        typer.echo("  - On Windows: Download from https://ffmpeg.org/download.html")
        raise typer.Exit(1)
    
    return ffmpeg_cmd


def main():
    """Main CLI entry point"""
    app()


if __name__ == "__main__":
    main()
