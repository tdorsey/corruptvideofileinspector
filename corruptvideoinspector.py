#!/usr/bin/env python3
"""
CLI version of Corrupt Video Inspector

This script provides a command-line interface for the Corrupt Video Inspector functionality,
allowing users to scan directories for corrupt video files from the terminal.
"""

import argparse
import csv
import json
import os
import subprocess
import shlex
import platform
import psutil
import signal
import time
import sys
from datetime import datetime

# Video file extensions supported
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm', '.m4v', '.m4p', '.mpeg', '.mpg', '.3gp', '.3g2']

class VideoObject:
    """Simple class to represent a video file"""
    def __init__(self, filename, full_filepath):
        self.filename = filename
        self.full_filepath = full_filepath

def is_linux_os():
    """Check if running on Linux"""
    return 'Linux' in platform.system()

def is_macos():
    """Check if running on macOS"""
    return 'Darwin' in platform.system()

def is_windows_os():
    """Check if running on Windows"""
    return 'Windows' in platform.system()

def convert_time(seconds):
    """Convert seconds to readable HH:MM:SS format"""
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

def count_all_video_files(directory):
    """Count total video files in directory and subdirectories"""
    total = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                total += 1
    return total

def get_all_video_files(directory):
    """Get list of all video files in directory and subdirectories"""
    videos_found_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                videos_found_list.append(file)
    videos_found_list.sort()
    return videos_found_list

def get_ffmpeg_command():
    """Get the appropriate ffmpeg command for the current system"""
    # First try system ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return 'ffmpeg'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Try bundled binaries
    script_dir = os.path.dirname(__file__)
    if is_macos():
        ffmpeg_path = os.path.join(script_dir, 'ffmpeg')
        if os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
            return ffmpeg_path
    elif is_windows_os():
        ffmpeg_path = os.path.join(script_dir, 'ffmpeg.exe')
        if os.path.isfile(ffmpeg_path):
            return ffmpeg_path
    elif is_linux_os():
        # Try to use the bundled ffmpeg, but it might be for wrong architecture
        ffmpeg_path = os.path.join(script_dir, 'ffmpeg')
        if os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
            # Test if it actually works
            try:
                subprocess.run([ffmpeg_path, '-version'], capture_output=True, check=True, timeout=5)
                return ffmpeg_path
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, OSError):
                pass
    
    return None

def calculate_progress(count, total):
    """Calculate progress percentage"""
    return "{0}%".format(int((count / total) * 100))

def inspect_video_files_cli(directory, start_index=1, verbose=False, json_output=False):
    """
    CLI version of video inspection functionality
    """
    try:
        # Initialize data structures for tracking results
        scan_start_time = time.time()
        scan_start_datetime = datetime.now()
        
        # Setup log file
        log_file_path = os.path.join(directory, '_Logs.log')
        if os.path.isfile(log_file_path):
            os.remove(log_file_path)
        log_file = open(log_file_path, 'a', encoding="utf8")

        print('CORRUPT VIDEO FILE INSPECTOR (CLI)')
        print('=' * 50)
        log_file.write('=================================================================\n')
        log_file.write('                CORRUPT VIDEO FILE INSPECTOR (CLI)\n')
        log_file.write('=================================================================\n')
        log_file.write('CREATED: _Logs.log\n')
        log_file.write('CREATED: _Results.csv\n')
        if json_output:
            log_file.write('CREATED: _Results.json\n')
        log_file.write('=================================================================\n')
        log_file.flush()

        # Setup CSV results file
        results_file_path = os.path.join(directory, '_Results.csv')
        if os.path.isfile(results_file_path):
            os.remove(results_file_path)

        results_file = open(results_file_path, 'a+', encoding="utf8", newline='')
        results_file_writer = csv.writer(results_file)
        header = ['Video File', 'Corrupted']
        results_file_writer.writerow(header)
        results_file.flush()

        # Setup JSON results file if requested
        json_file_path = None
        json_data = {
            "scan_info": {
                "directory": directory,
                "start_index": start_index,
                "start_time": scan_start_datetime.isoformat(),
                "platform": platform.system(),
                "ffmpeg_command": get_ffmpeg_command()
            },
            "results": [],
            "summary": {}
        }
        
        if json_output:
            json_file_path = os.path.join(directory, '_Results.json')
            if os.path.isfile(json_file_path):
                os.remove(json_file_path)

        # Get all video files
        total_video_files = count_all_video_files(directory)
        start_time = scan_start_datetime.strftime('%Y-%m-%d %I:%M %p')

        print(f'Directory: {directory}')
        print(f'Total video files found: {total_video_files}')
        print(f'Starting from video index: {start_index}')
        print(f'Start time: {start_time}')
        if json_output:
            print('JSON output: ENABLED')
        print('=' * 50)

        log_file.write(f'DIRECTORY: {directory}\n')
        log_file.write(f'TOTAL VIDEO FILES FOUND: {total_video_files}\n')
        log_file.write(f'STARTING FROM VIDEO INDEX: {start_index}\n')
        log_file.write(f'START TIME: {start_time}\n')
        if json_output:
            log_file.write('JSON OUTPUT: ENABLED\n')
        log_file.write('=================================================================\n')
        log_file.write('(DURATION IS IN HOURS:MINUTES:SECONDS)\n')
        log_file.flush()

        # Update JSON data
        json_data["scan_info"]["total_video_files"] = total_video_files

        # Collect all video files
        all_videos_found = []
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                    video_obj = VideoObject(filename, os.path.join(root, filename))
                    all_videos_found.append(video_obj)

        # Sort alphabetically
        all_videos_found.sort(key=lambda x: x.filename)

        if total_video_files == 0:
            print("No video files found in the specified directory!")
            return

        # Process videos
        count = 0
        corrupted_count = 0
        processed_videos = []
        
        for video in all_videos_found:
            if (start_index > count + 1):
                count += 1
                continue

            start_time_video = time.time()
            current_progress = calculate_progress(count, total_video_files)
            
            print(f'\n[{current_progress}] Processing ({count + 1}/{total_video_files}): {video.filename}')
            
            # Run ffmpeg analysis
            ffmpeg_cmd = get_ffmpeg_command()
            proc = None
                
            if is_macos() or is_linux_os():
                proc = subprocess.Popen(f'{ffmpeg_cmd} -v error -i {shlex.quote(video.full_filepath)} -f null - 2>&1', 
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif is_windows_os():
                proc = subprocess.Popen(f'"{ffmpeg_cmd}" -v error -i "{video.full_filepath}" -f null error.log', 
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                print("Unsupported operating system!")
                return

            output, error = proc.communicate()

            if verbose:
                print(f'  ffmpeg output: {output}')
                print(f'  ffmpeg error: {error}')

            elapsed_time = time.time() - start_time_video
            readable_time = convert_time(elapsed_time)

            # Determine if video is corrupt
            ffmpeg_result = ''
            if is_macos() or is_linux_os():
                ffmpeg_result = output
            elif is_windows_os():
                ffmpeg_result = error

            video_result = {
                "filename": video.filename,
                "full_path": video.full_filepath,
                "index": count + 1,
                "processing_time_seconds": elapsed_time,
                "processing_time_readable": readable_time,
                "corrupted": bool(ffmpeg_result),
                "ffmpeg_output": ffmpeg_result.decode() if isinstance(ffmpeg_result, bytes) else str(ffmpeg_result),
                "timestamp": datetime.now().isoformat()
            }

            if not ffmpeg_result:
                # Healthy
                print(f"  ✓ HEALTHY ✓ (processed in {readable_time})")
                
                log_file.write('=================================================================\n')
                log_file.write(f'{video.filename}\n')
                log_file.write('STATUS: ✓ HEALTHY ✓\n')
                log_file.write(f'DURATION: {readable_time}\n')
                log_file.flush()

                row = [video.filename, 0]
            else:
                # Corrupt
                corrupted_count += 1
                print(f"  ✗ CORRUPT ✗ (processed in {readable_time})")
                
                log_file.write('=================================================================\n')
                log_file.write(f'{video.filename}\n')
                log_file.write('STATUS: X CORRUPT X\n')
                log_file.write(f'DURATION: {readable_time}\n')
                log_file.flush()

                row = [video.filename, 1]

            results_file_writer.writerow(row)
            results_file.flush()
            
            # Add to JSON data if enabled
            if json_output:
                json_data["results"].append(video_result)
            
            processed_videos.append(video_result)
            count += 1

        # Calculate scan duration
        scan_end_time = time.time()
        scan_end_datetime = datetime.now()
        total_scan_duration = scan_end_time - scan_start_time
        total_scan_readable = convert_time(total_scan_duration)

        # Final summary
        final_progress = calculate_progress(count, total_video_files)
        end_time = scan_end_datetime.strftime('%Y-%m-%d %I:%M %p')
        
        print('\n' + '=' * 50)
        print('SCAN COMPLETE!')
        print(f'Progress: {final_progress}')
        processed_count = count - (start_index - 1)
        print(f'Processed files: {processed_count}/{total_video_files}')
        print(f'Corrupted files found: {corrupted_count}')
        print(f'Healthy files: {processed_count - corrupted_count}')
        print(f'Total scan duration: {total_scan_readable}')
        print(f'End time: {end_time}')
        print('=' * 50)

        log_file.write('=================================================================\n')
        log_file.write(f'SUCCESSFULLY PROCESSED {processed_count} VIDEO FILES\n')
        log_file.write(f'CORRUPTED FILES FOUND: {corrupted_count}\n')
        log_file.write(f'HEALTHY FILES: {processed_count - corrupted_count}\n')
        log_file.write(f'TOTAL SCAN DURATION: {total_scan_readable}\n')
        log_file.write(f'END TIME: {end_time}\n')
        log_file.write('=================================================================\n')
        log_file.flush()
        log_file.close()
        results_file.close()

        # Generate JSON output if requested
        if json_output:
            # Update JSON summary data
            json_data["summary"] = {
                "total_files_found": total_video_files,
                "files_processed": processed_count,
                "files_skipped": start_index - 1,
                "corrupted_files": corrupted_count,
                "healthy_files": processed_count - corrupted_count,
                "corruption_rate": round((corrupted_count / processed_count * 100) if processed_count > 0 else 0, 2),
                "scan_duration_seconds": total_scan_duration,
                "scan_duration_readable": total_scan_readable,
                "end_time": scan_end_datetime.isoformat(),
                "average_processing_time": round(total_scan_duration / processed_count, 2) if processed_count > 0 else 0
            }
            
            # Write JSON file
            with open(json_file_path, 'w', encoding='utf8') as json_file:
                json.dump(json_data, json_file, indent=2, ensure_ascii=False)
            
            print(f'\nResults saved to:')
            print(f'  Log file: {log_file_path}')
            print(f'  CSV file: {results_file_path}')
            print(f'  JSON file: {json_file_path}')
        else:
            print(f'\nResults saved to:')
            print(f'  Log file: {log_file_path}')
            print(f'  CSV file: {results_file_path}')

    except Exception as e:
        print(f'ERROR in video inspection: {e}')
        if 'log_file' in locals():
            log_file.write(f'ERROR in "inspect_video_files_cli": {e}\n')
            log_file.flush()

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='CLI version of Corrupt Video Inspector - Scan directories for corrupted video files using ffmpeg',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  corruptvideoinspector.py /path/to/videos                    # Scan all videos starting from index 1
  corruptvideoinspector.py /path/to/videos --start-index 10  # Resume scanning from the 10th video
  corruptvideoinspector.py /path/to/videos --verbose          # Show detailed ffmpeg output
  corruptvideoinspector.py /path/to/videos --json            # Generate JSON output with detailed results
  corruptvideoinspector.py --list-videos /path/to/videos      # List all video files found

Supported video formats:
  ''' + ', '.join(VIDEO_EXTENSIONS) + '''

Output files created in the target directory:
  _Logs.log    - Detailed log of the scanning process
  _Results.csv - CSV file with corruption status for each video
  _Results.json - JSON file with comprehensive scan results (when --json is used)
        '''
    )
    
    parser.add_argument('directory', 
                       help='Directory to scan for video files (includes subdirectories)')
    
    parser.add_argument('--start-index', '-s', 
                       type=int, 
                       default=1,
                       help='Start scanning from this video index (default: 1)')
    
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Show detailed ffmpeg output during processing')
    
    parser.add_argument('--list-videos', '-l', 
                       action='store_true',
                       help='List all video files found in directory and exit')
    
    parser.add_argument('--json', '-j', 
                       action='store_true',
                       help='Generate JSON output file with detailed scan results')
    
    parser.add_argument('--version', 
                       action='version', 
                       version='Corrupt Video Inspector CLI v1.0')

    args = parser.parse_args()

    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist or is not a directory.")
        sys.exit(1)

    # Convert to absolute path
    directory = os.path.abspath(args.directory)

    # Handle list-videos option
    if args.list_videos:
        print(f'Scanning directory: {directory}')
        video_files = get_all_video_files(directory)
        total_count = len(video_files)
        
        if total_count == 0:
            print('No video files found in the specified directory.')
        else:
            print(f'\nFound {total_count} video files:')
            for i, video in enumerate(video_files, 1):
                print(f'  {i:3d}: {video}')
        return

    # Validate start index
    total_videos = count_all_video_files(directory)
    if total_videos == 0:
        print(f"No video files found in directory: {directory}")
        sys.exit(1)
        
    if args.start_index < 1 or args.start_index > total_videos:
        print(f"Error: Start index must be between 1 and {total_videos}")
        sys.exit(1)

    # Start the inspection
    print(f'Starting video corruption scan...')
    print(f'Platform: {platform.system()}')
    
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
    
    print(f'Using ffmpeg: {ffmpeg_cmd}')
    
    inspect_video_files_cli(directory, args.start_index, args.verbose, args.json)

if __name__ == '__main__':
    main()