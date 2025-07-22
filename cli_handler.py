"""
CLI argument parsing and command-line interface functionality for Corrupt Video Inspector
"""
import argparse
import os
import sys
import logging
from pathlib import Path
from typing import Optional
from utils import count_all_video_files
from video_inspector import get_all_video_object_files, get_ffmpeg_command, inspect_video_files_cli, ScanMode

# Configure module logger
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """
    Setup comprehensive logging configuration with appropriate log levels.
    
    Args:
        verbose: Enable debug-level logging
        quiet: Suppress all but error-level logging
    """
    # Determine log level based on verbosity settings
    if quiet:
        log_level = logging.ERROR
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    # Configure root logger with consistent format
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True  # Override any existing configuration
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger('video_inspector').setLevel(log_level)
    logging.getLogger('utils').setLevel(log_level)
    
    logger.info(f"Logging initialized with level: {logging.getLevelName(log_level)}")


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


def parse_cli_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Corrupt Video Inspector - Scan directories for corrupt video files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 cli_handler.py /path/to/videos                    # Run hybrid mode (default)
  python3 cli_handler.py --mode quick /path                 # Quick scan only
  python3 cli_handler.py --mode deep /path                  # Deep scan all files
  python3 cli_handler.py --no-resume /path/videos           # CLI without resume
  python3 cli_handler.py --verbose /path/videos             # CLI with verbose output
  python3 cli_handler.py --json /path/videos                # CLI with JSON output
  python3 cli_handler.py --list-videos /path                # List videos only
        ''')
    
    parser.add_argument('directory', 
                       nargs='?',
                       help='Directory to scan for video files')
    
    parser.add_argument('--mode', 
                       choices=['quick', 'deep', 'hybrid'], 
                       default='hybrid',
                       help='Scan mode: quick (1min timeout), deep (full scan), hybrid (quick then deep for suspicious files) - default: hybrid')
    
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Enable verbose output showing FFmpeg details')
    
    parser.add_argument('--no-resume', 
                       action='store_true',
                       help='Disable automatic resume functionality (start from beginning)')
    
    parser.add_argument('--list-videos', '-l', 
                       action='store_true',
                       help='List all video files in directory without scanning')
    
    parser.add_argument('--json', '-j', 
                       action='store_true',
                       help='Generate JSON output file with detailed scan results')
    
    parser.add_argument('--output', '-o',
                       type=str,
                       help='Specify custom output file path for results')
    
    parser.add_argument('--recursive', '-r',
                       action='store_true',
                       default=True,
                       help='Recursively scan subdirectories (default: True)')
    
    parser.add_argument('--extensions', '-e',
                       type=str,
                       nargs='+',
                       help='Specify video file extensions to scan (e.g., mp4 mkv avi)')
    
    parser.add_argument('--max-workers', '-w',
                       type=int,
                       default=4,
                       help='Maximum number of worker threads for parallel processing (default: 4)')
    
    parser.add_argument('--quiet', '-q',
                       action='store_true',
                       help='Suppress all output except errors')
    
    parser.add_argument('--version', 
                       action='version', 
                       version='Corrupt Video Inspector v2.0 (Hybrid Detection)')
    
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validate argument combinations and values.
    
    Args:
        args: Parsed command line arguments
        
    Raises:
        ValueError: If argument combinations are invalid
    """
    if args.verbose and args.quiet:
        logger.error("Cannot use --verbose and --quiet together")
        raise ValueError("Cannot use --verbose and --quiet together")
    
    if args.max_workers <= 0:
        logger.error("Max workers must be a positive integer")
        raise ValueError("Max workers must be a positive integer")
    
    if args.output and not args.json:
        logger.warning("--output specified without --json, enabling JSON output")
        print("Warning: --output specified without --json, enabling JSON output")
        args.json = True
    
    logger.debug(f"Arguments validated successfully: {vars(args)}")


def list_video_files(directory: Path, recursive: bool = False, extensions: Optional[list] = None) -> None:
    """
    List all video files in directory.
    
    Args:
        directory: Path to directory to scan
        recursive: Whether to scan subdirectories recursively
        extensions: List of file extensions to include
    """
    logger.info(f'Scanning directory: {directory}')
    print(f'Scanning directory: {directory}')
    if recursive:
        logger.info('Including subdirectories in scan')
        print('(including subdirectories)')
    
    try:
        video_files = get_all_video_object_files(str(directory), recursive, extensions)
        
        total_count = len(video_files)
        logger.info(f"Found {total_count} video files")
        
        if total_count == 0:
            logger.warning('No video files found in the specified directory')
            print('No video files found in the specified directory.')
            if extensions:
                extension_list = ", ".join(extensions)
                logger.info(f'Searched for extensions: {extension_list}')
                print(f'Searched for extensions: {extension_list}')
        else:
            print(f'\nFound {total_count} video files:')
            for i, video in enumerate(video_files, 1):
                rel_path = Path(video.filename).relative_to(directory)
                size_mb = Path(video.filename).stat().st_size / (1024 * 1024)
                print(f'  {i:3d}: {rel_path} ({size_mb:.1f} MB)')
                logger.debug(f'Video file {i}: {rel_path} ({size_mb:.1f} MB)')
                
    except Exception as e:
        logger.error(f"Error listing video files: {e}")
        logging.error(f"Error listing video files: {e}")
        sys.exit(1)


def check_system_requirements() -> str:
    """
    Check system requirements and return ffmpeg command.
    
    Returns:
        str: Path to ffmpeg command
        
    Raises:
        SystemExit: If ffmpeg is not found
    """
    logger.debug("Checking for ffmpeg installation")
    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        logger.error("ffmpeg is required but not found on this system")
        print("\nError: ffmpeg is required but not found on this system.")
        print("Please install ffmpeg:")
        print("  - On Ubuntu/Debian: sudo apt install ffmpeg")
        print("  - On CentOS/RHEL: sudo yum install ffmpeg")
        print("  - On macOS: brew install ffmpeg")
        print("  - On Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)
    
    logger.info(f"Found ffmpeg at: {ffmpeg_cmd}")
    return ffmpeg_cmd


def main() -> None:
    """
    Main CLI entry point.
    
    Raises:
        SystemExit: On various error conditions or user interruption
    """
    try:
        # Parse arguments
        args = parse_cli_arguments()
        
        # Setup logging first
        setup_logging(args.verbose and not args.quiet, args.quiet)
        logger.info("Starting Corrupt Video Inspector")
        
        # Validate arguments
        validate_arguments(args)
        
        # Check if directory was provided
        if not args.directory:
            logger.error("Directory argument is required")
            print("Error: Directory argument is required", file=sys.stderr)
            sys.exit(1)
        
        # Validate directory
        directory = validate_directory(args.directory)
        
        # Handle quiet mode
        if args.quiet:
            logger.debug("Quiet mode enabled, redirecting stdout")
            # Redirect stdout to devnull, keep stderr for errors
            sys.stdout = open(os.devnull, 'w')
        
        # Handle list-videos option
        if args.list_videos:
            logger.info("Listing video files only")
            list_video_files(directory, args.recursive, args.extensions)
            return
        
        # Check if directory has video files
        logger.debug("Counting video files in directory")
        total_videos = count_all_video_files(str(directory))
        if total_videos == 0:
            logger.warning(f"No video files found in directory: {directory}")
            print(f"No video files found in directory: {directory}")
            if args.extensions:
                extension_list = ', '.join(args.extensions)
                logger.info(f"Searched for extensions: {extension_list}")
                print(f"Searched for extensions: {extension_list}")
            sys.exit(1)
        
        logger.info(f"Found {total_videos} video files to process")
        
        # Check system requirements
        ffmpeg_cmd = check_system_requirements()
        
        if not args.quiet:
            print(f'Starting video corruption scan...')
            print(f'Directory: {directory}')
            print(f'Scan mode: {args.mode.upper()}')
            if args.mode == 'hybrid':
                print('  Phase 1: Quick scan all files (1min timeout)')
                print('  Phase 2: Deep scan suspicious files (15min timeout)')
            elif args.mode == 'quick':
                print('  Quick scan only (1min timeout per file)')
            elif args.mode == 'deep':
                print('  Deep scan all files (15min timeout per file)')
            print(f'Platform: {sys.platform}')
            print(f'Using ffmpeg: {ffmpeg_cmd}')
            print(f'Max workers: {args.max_workers}')
            if args.recursive:
                print('Recursive scanning: enabled')
            if args.extensions:
                print(f'File extensions: {", ".join(args.extensions)}')
        
        logger.info(f"Starting scan with mode: {args.mode}, workers: {args.max_workers}")
        
        # Convert mode string to enum
        scan_mode = ScanMode(args.mode)
        
        # Start the inspection using video_inspector module
        inspect_video_files_cli(
            directory=str(directory),
            resume=not args.no_resume,
            verbose=args.verbose and not args.quiet,
            json_output=args.json,
            output_file=args.output,
            recursive=args.recursive,
            extensions=args.extensions,
            max_workers=args.max_workers,
            scan_mode=scan_mode
        )
        
        logger.info("Video inspection completed successfully")
        
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Scan interrupted by user")
        print("\nScan interrupted by user", file=sys.stderr)
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Restore stdout if it was redirected
        if hasattr(sys.stdout, 'close') and sys.stdout != sys.__stdout__:
            sys.stdout.close()
            sys.stdout = sys.__stdout__


if __name__ == "__main__":
    main()
