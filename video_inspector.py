"""
Core video inspection functionality for Corrupt Video Inspector
Handles video file processing, ffmpeg integration, and corruption detection.
"""
import csv
import json
import os
import subprocess
import shlex
import signal
import time
from datetime import datetime
from utils import VIDEO_EXTENSIONS, is_macos, is_windows_os, is_linux_os, convert_time, calculate_progress, truncate_filename


class VideoObject:
    """Represents a video file with its filename and full path"""
    def __init__(self, filename, full_filepath):
        self.filename = filename
        self.full_filepath = full_filepath


def get_all_video_object_files(directory):
    """Get all video files as VideoObject instances for processing"""
    videos_found_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                full_path = os.path.join(root, file)
                videos_found_list.append(VideoObject(file, full_path))
    
    # Sort by filename
    videos_found_list.sort(key=lambda x: x.filename.lower())
    return videos_found_list


def get_ffmpeg_command():
    """Get the appropriate ffmpeg command for the current platform"""
    # First check if system ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return 'ffmpeg'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check for bundled ffmpeg
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if is_windows_os():
        bundled_path = os.path.join(script_dir, 'ffmpeg.exe')
    else:
        bundled_path = os.path.join(script_dir, 'ffmpeg')
    
    if os.path.exists(bundled_path) and os.access(bundled_path, os.X_OK):
        return bundled_path
    
    return None


def inspect_video_files_cli(directory, resume=True, verbose=False, json_output=False):
    """CLI version of video file inspection with automatic resume functionality"""
    
    # Get all video files in directory
    video_files = get_all_video_object_files(directory)
    total_videos = len(video_files)
    
    if total_videos == 0:
        print(f"No video files found in directory: {directory}")
        return
    
    # Initialize scan metadata
    scan_start_time = datetime.now()
    scan_metadata = {
        'directory': directory,
        'total_files': total_videos,
        'start_time': scan_start_time.isoformat(),
        'platform': os.name,
        'ffmpeg_command': get_ffmpeg_command()
    }
    
    # Load existing state if resume is enabled
    processed_files = set()
    start_index = 1
    
    if resume:
        state_data = load_scan_state(directory)
        if state_data:
            processed_files = set(state_data.get('processed_files', []))
            start_index = len(processed_files) + 1
            print(f"Resuming scan from file {start_index} (found {len(processed_files)} already processed)")
            scan_metadata['resumed'] = True
            scan_metadata['resume_time'] = scan_start_time.isoformat()
        else:
            print("Starting new scan")
            scan_metadata['resumed'] = False
    else:
        print("Starting new scan (resume disabled)")
        scan_metadata['resumed'] = False
    
    # Setup output files
    timestamp = scan_start_time.strftime('%Y-%m-%d_%H-%M-%S')
    log_file_path = os.path.join(directory, f'{os.path.basename(directory.rstrip("/\\"))}_Logs.log')
    csv_file_path = os.path.join(directory, f'{os.path.basename(directory.rstrip("/\\"))}_Results.csv')
    
    if json_output:
        json_file_path = os.path.join(directory, f'{os.path.basename(directory.rstrip("/\\"))}_Results.json')
    
    # Initialize CSV file with headers if starting new scan
    if not resume or start_index == 1:
        with open(csv_file_path, 'w', newline='') as csvfile:
            fieldnames = ['File_Number', 'Filename', 'Full_Filepath', 'Corrupt']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    
    # Get ffmpeg command
    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        print("\nError: ffmpeg is required but not found on this system.")
        print("Please install ffmpeg:")
        print("  - On Ubuntu/Debian: sudo apt install ffmpeg")
        print("  - On CentOS/RHEL: sudo yum install ffmpeg") 
        print("  - On macOS: brew install ffmpeg")
        print("  - On Windows: Download from https://ffmpeg.org/download.html")
        return
    
    print(f"Using ffmpeg: {ffmpeg_cmd}")
    print(f"Scanning {total_videos} video files in: {directory}")
    print(f"Output files:")
    print(f"  Log: {log_file_path}")
    print(f"  CSV: {csv_file_path}")
    if json_output:
        print(f"  JSON: {json_file_path}")
    print("")
    
    # Initialize counters and results
    corrupt_files = []
    clean_files = []
    error_files = []
    json_results = []
    
    # Process video files
    for index, video in enumerate(video_files, 1):
        # Skip if already processed during resume
        if video.full_filepath in processed_files:
            continue
            
        if index < start_index:
            continue
        
        print(f"Processing {index}/{total_videos}: {video.filename}")
        
        file_start_time = time.time()
        is_corrupt = False
        ffmpeg_output = ""
        error_msg = ""
        
        try:
            # Prepare ffmpeg command with proper shell escaping
            if is_windows_os():
                cmd = f'"{ffmpeg_cmd}" -v error -i "{video.full_filepath}" -f null - -hide_banner'
            else:
                cmd = f'{shlex.quote(ffmpeg_cmd)} -v error -i {shlex.quote(video.full_filepath)} -f null - -hide_banner'
            
            # Run ffmpeg
            if verbose:
                print(f"  Running: {cmd}")
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=FFMPEG_TIMEOUT_SECONDS)
            ffmpeg_output = result.stderr.strip()
            
            # Determine if file is corrupt
            if result.returncode != 0 or ffmpeg_output:
                is_corrupt = True
                corrupt_files.append(video.full_filepath)
                status = "CORRUPT"
            else:
                clean_files.append(video.full_filepath)
                status = "CLEAN"
                
        except subprocess.TimeoutExpired:
            is_corrupt = True
            error_msg = f"Processing timeout (>{TIMEOUT_SECONDS}s)"
            error_files.append(video.full_filepath)
            status = "ERROR (Timeout)"
        except Exception as e:
            is_corrupt = True
            error_msg = str(e)
            error_files.append(video.full_filepath)
            status = "ERROR"
        
        file_end_time = time.time()
        processing_time = file_end_time - file_start_time
        
        # Log results
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"File {index}: {video.filename}\n")
            log_file.write(f"Path: {video.full_filepath}\n")
            log_file.write(f"Status: {status}\n")
            log_file.write(f"Processing time: {processing_time:.2f}s\n")
            if ffmpeg_output:
                log_file.write(f"FFmpeg output: {ffmpeg_output}\n")
            if error_msg:
                log_file.write(f"Error: {error_msg}\n")
            log_file.write("-" * 50 + "\n")
        
        # Update CSV
        with open(csv_file_path, 'a', newline='') as csvfile:
            fieldnames = ['File_Number', 'Filename', 'Full_Filepath', 'Corrupt']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({
                'File_Number': index,
                'Filename': video.filename,
                'Full_Filepath': video.full_filepath,
                'Corrupt': 'Yes' if is_corrupt else 'No'
            })
        
        # Store for JSON output
        if json_output:
            json_results.append({
                'file_number': index,
                'filename': video.filename,
                'full_filepath': video.full_filepath,
                'is_corrupt': is_corrupt,
                'status': status,
                'processing_time_seconds': round(processing_time, 2),
                'ffmpeg_output': ffmpeg_output,
                'error_message': error_msg
            })
        
        # Update processed files and save state
        processed_files.add(video.full_filepath)
        save_scan_state(directory, video_files, list(processed_files), scan_metadata)
        
        # Show progress
        progress = calculate_progress(index, total_videos)
        print(f"  Result: {status} ({processing_time:.1f}s) - Progress: {progress}")
        
        if verbose and ffmpeg_output:
            print(f"  FFmpeg output: {ffmpeg_output}")
    
    # Calculate final statistics and print summary
    scan_end_time = datetime.now()
    total_duration = (scan_end_time - scan_start_time).total_seconds()
    processed_count = len(processed_files)
    corrupt_count = len(corrupt_files)
    clean_count = len(clean_files)
    error_count = len(error_files)
    
    print("\n" + "="*60)
    print("SCAN COMPLETE")
    print("="*60)
    print(f"Directory: {directory}")
    print(f"Total files found: {total_videos}")
    print(f"Files processed: {processed_count}")
    print(f"Corrupt files: {corrupt_count}")
    print(f"Clean files: {clean_count}")
    print(f"Error files: {error_count}")
    print(f"Corruption rate: {(corrupt_count/processed_count*100):.1f}%" if processed_count > 0 else "N/A")
    print(f"Scan duration: {convert_time(int(total_duration))}")
    print(f"Average per file: {(total_duration/processed_count):.1f}s" if processed_count > 0 else "N/A")
    
    # Generate JSON output if requested
    if json_output:
        scan_metadata.update({
            'end_time': scan_end_time.isoformat(),
            'total_duration_seconds': round(total_duration, 2),
            'files_processed': processed_count,
            'corrupt_files': corrupt_count,
            'clean_files': clean_count,
            'error_files': error_count,
            'corruption_rate_percent': round(corrupt_count/processed_count*100, 2) if processed_count > 0 else 0,
            'average_processing_time_seconds': round(total_duration/processed_count, 2) if processed_count > 0 else 0
        })
        
        json_data = {
            'scan_metadata': scan_metadata,
            'results': json_results,
            'summary': {
                'total_files_found': total_videos,
                'files_processed': processed_count,
                'corrupt_files': corrupt_count,
                'clean_files': clean_count,
                'error_files': error_count,
                'corruption_rate_percent': round(corrupt_count/processed_count*100, 2) if processed_count > 0 else 0,
                'scan_duration_formatted': convert_time(int(total_duration)),
                'average_processing_time_seconds': round(total_duration/processed_count, 2) if processed_count > 0 else 0
            }
        }
        
        with open(json_file_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"\nDetailed results saved to: {json_file_path}")
    
    # Clean up state file on successful completion
    if processed_count == total_videos:
        state_file = get_state_file_path(directory)
        try:
            if os.path.exists(state_file):
                os.remove(state_file)
                print("Scan state file cleaned up.")
        except Exception as e:
            print(f"Warning: Could not remove state file: {e}")


def get_state_file_path(directory):
    """Get the path for the state file for a given directory"""
    safe_dir_name = os.path.basename(directory.rstrip('/\\'))
    if not safe_dir_name:
        safe_dir_name = "root"
    # Replace problematic characters
    safe_dir_name = "".join(c for c in safe_dir_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return os.path.join(directory, f".corruptvideo_scan_state_{safe_dir_name}.json")


def save_scan_state(directory, video_files, processed_files, scan_metadata):
    """Save the current scan state to a JSON file"""
    state_file = get_state_file_path(directory)
    state_data = {
        'directory': directory,
        'scan_metadata': scan_metadata,
        'total_files': len(video_files),
        'video_files': [{'filename': v.filename, 'full_filepath': v.full_filepath} for v in video_files],
        'processed_files': processed_files,
        'last_updated': datetime.now().isoformat()
    }
    
    try:
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save state file: {e}")


def load_scan_state(directory):
    """Load the scan state from a JSON file if it exists"""
    state_file = get_state_file_path(directory)
    if not os.path.exists(state_file):
        return None
    
    try:
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        # Validate the state file
        if state_data.get('directory') != directory:
            return {
                'success': False,
                'error': 'Directory mismatch in state file',
                'data': None
            }
            
        return {
            'success': True,
            'error': None,
            'data': state_data
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Could not load state file: {e}",
            'data': None
        }