"""
CLI argument parsing and command-line interface functionality for Corrupt Video Inspector
"""
import argparse
import os
import sys
from utils import count_all_video_files
from video_inspector import get_all_video_object_files, get_ffmpeg_command, inspect_video_files_cli


def parse_cli_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Corrupt Video Inspector - Scan directories for corrupt video files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python CorruptVideoInspector.py                          # Run GUI mode
  python CorruptVideoInspector.py /path/to/videos          # Run CLI mode
  python CorruptVideoInspector.py --no-resume /path/videos # CLI without resume
  python CorruptVideoInspector.py --verbose /path/videos   # CLI with verbose output
  python CorruptVideoInspector.py --json /path/videos      # CLI with JSON output
  python CorruptVideoInspector.py --list-videos /path      # List videos only
        ''')
    
    parser.add_argument('directory', 
                       nargs='?',
                       help='Directory to scan for video files (if not provided, GUI mode will start)')
    
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
    
    parser.add_argument('--version', 
                       action='version', 
                       version='Corrupt Video Inspector v2.0')
    
    return parser.parse_args()


def run_cli_mode(args):
    """Run the application in CLI mode"""
    directory = os.path.abspath(args.directory)
    
    # Validate directory
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist or is not a directory.")
        sys.exit(1)
    
    # Handle list-videos option
    if args.list_videos:
        print(f'Scanning directory: {directory}')
        video_files = get_all_video_object_files(directory)
        total_count = len(video_files)
        
        if total_count == 0:
            print('No video files found in the specified directory.')
        else:
            print(f'\nFound {total_count} video files:')
            for i, video in enumerate(video_files, 1):
                print(f'  {i:3d}: {video.filename}')
        return
    
    # Check if directory has video files
    total_videos = count_all_video_files(directory)
    if total_videos == 0:
        print(f"No video files found in directory: {directory}")
        sys.exit(1)
    
    # Check ffmpeg availability first
    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        print("\nError: ffmpeg is required but not found on this system.")
        print("Please install ffmpeg:")
        print("  - On Ubuntu/Debian: sudo apt install ffmpeg")
        print("  - On CentOS/RHEL: sudo yum install ffmpeg")
        print("  - On macOS: brew install ffmpeg")
        print("  - On Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)
    
    print(f'Starting video corruption scan...')
    print(f'Platform: {sys.platform}')
    print(f'Using ffmpeg: {ffmpeg_cmd}')
    
    # Start the inspection
    resume_enabled = not args.no_resume
    inspect_video_files_cli(directory, resume=resume_enabled, verbose=args.verbose, json_output=args.json)