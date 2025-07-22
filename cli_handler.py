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


def parse_cli_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
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
    """Validate argument combinations and values"""
    if args.verbose and args.quiet:
        raise ValueError("Cannot use --verbose and --quiet together")
    
    if args.max_workers <= 0:
        raise ValueError("Max workers must be a positive integer")
    
    if args.output and not args.json:
        print("Warning: --output specified without --json, enabling JSON output")
        args.json = True


def list_video_files(directory: Path, recursive: bool = False, extensions: Optional[list] = None) -> None:
    """List all video files in directory"""
    print(f'Scanning directory: {directory}')
    if recursive:
        print('(including subdirectories)')
    
    try:
        video_files = get_all_video_object_files(str(directory), recursive, extensions)
        
        total_count = len(video_files)
        
        if total_count == 0:
            print('No video files found in the specified directory.')
            if extensions:
                print(f'Searched for extensions: {", ".join(extensions)}')
        else:
            print(f'\nFound {total_count} video files:')
            for i, video in enumerate(video_files, 1):
                rel_path = Path(video.filename).relative_to(directory)
                size_mb = Path(video.filename).stat().st_size / (1024 * 1024)
                print(f'  {i:3d}: {rel_path} ({size_mb:.1f} MB)')
                
    except Exception as e:
        logging.error(f"Error listing video files: {e}")
        sys.exit(1)


def check_system_requirements() -> str:
    """Check system requirements and return ffmpeg command"""
    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        print("\nError: ffmpeg is required but not found on this system.")
        print("Please install ffmpeg:")
        print("  - On Ubuntu/Debian: sudo apt install ffmpeg")
        print("  - On CentOS/RHEL: sudo yum install ffmpeg")
        print("  - On macOS: brew install ffmpeg")
        print("  - On Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)
    
    return ffmpeg_cmd


def main():
    """Main CLI entry point"""
    try:
        # Parse arguments
        args = parse_cli_arguments()
        
        # Setup logging
        setup_logging(args.verbose and not args.quiet)
        
        # Validate arguments
        validate_arguments(args)
        
        # Check if directory was provided
        if not args.directory:
            print("Error: Directory argument is required", file=sys.stderr)
            sys.exit(1)
        
        # Validate directory
        directory = validate_directory(args.directory)
        
        # Handle quiet mode
        if args.quiet:
            # Redirect stdout to devnull, keep stderr for errors
            sys.stdout = open(os.devnull, 'w')
        
        # Handle list-videos option
        if args.list_videos:
            list_video_files(directory, args.recursive, args.extensions)
            return
        
        # Check if directory has video files
        total_videos = count_all_video_files(str(directory))
        if total_videos == 0:
            print(f"No video files found in directory: {directory}")
            if args.extensions:
                print(f"Searched for extensions: {', '.join(args.extensions)}")
            sys.exit(1)
        
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
        
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nScan interrupted by user", file=sys.stderr)
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Restore stdout if it was redirected
        if hasattr(sys.stdout, 'close') and sys.stdout != sys.__stdout__:
            sys.stdout.close()
            sys.stdout = sys.__stdout__


if __name__ == "__main__":
    main()
