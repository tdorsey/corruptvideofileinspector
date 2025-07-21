# Corrupt Video Inspector - CLI Usage

## Overview
The CLI version of Corrupt Video Inspector allows you to scan directories for corrupted video files directly from the command line in a Linux environment. This tool uses ffmpeg to perform deep integrity checks on video files.

## Prerequisites

### Required Software
- Python 3.6 or higher
- ffmpeg (must be installed on your system)

### Installing ffmpeg
- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **CentOS/RHEL**: `sudo yum install ffmpeg` or `sudo dnf install ffmpeg`
- **Arch Linux**: `sudo pacman -S ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/download.html

### Python Dependencies
The CLI requires the `psutil` library:
```bash
pip install psutil
```

## Usage

### Basic Usage
```bash
# Scan all videos in a directory
python3 corruptvideoinspector_cli.py /path/to/your/videos

# Or use the executable directly
./corruptvideoinspector /path/to/your/videos
```

### Command Line Options
```bash
# Show help
python3 corruptvideoinspector_cli.py --help

# List all video files without scanning
python3 corruptvideoinspector_cli.py --list-videos /path/to/videos

# Start scanning from a specific video index (useful for resuming)
python3 corruptvideoinspector_cli.py --start-index 10 /path/to/videos

# Enable verbose output to see ffmpeg details
python3 corruptvideoinspector_cli.py --verbose /path/to/videos

# Generate JSON output with detailed scan results
python3 corruptvideoinspector_cli.py --json /path/to/videos

# Combine multiple options
python3 corruptvideoinspector_cli.py --json --verbose --start-index 5 /path/to/videos

# Show version
python3 corruptvideoinspector_cli.py --version
```

### Supported Video Formats
The CLI supports the same video formats as the original GUI version:
- .mp4, .avi, .mov, .wmv, .mkv, .flv, .webm, .m4v, .m4p, .mpeg, .mpg, .3gp, .3g2

## Output Files

When you run a scan, the following files are automatically created in the target directory:

### _Logs.log
Contains detailed information about the scanning process:
- Directory scanned
- Total files found
- Start/end times
- Processing duration for each file
- Status (HEALTHY/CORRUPT) for each video
- Any errors encountered

### _Results.csv
CSV file with two columns:
- **Video File**: The filename of the video
- **Corrupted**: 0 = healthy, 1 = corrupted

### _Results.json (when --json is used)
Comprehensive JSON file containing:
- **scan_info**: Metadata about the scan (directory, start time, platform, etc.)
- **results**: Array of detailed results for each processed video file including:
  - Filename and full path
  - Processing time (seconds and readable format)
  - Corruption status and ffmpeg output
  - Individual file timestamps
- **summary**: Overall scan statistics including:
  - Total files found/processed/skipped
  - Corruption counts and rates
  - Scan duration and average processing time

## Examples

### Example 1: Basic Scan
```bash
python3 corruptvideoinspector_cli.py ~/Movies
```
This will scan all video files in the ~/Movies directory and all subdirectories.

### Example 2: Resume from Specific Index
If your scan was interrupted, you can resume from where it left off:
```bash
python3 corruptvideoinspector_cli.py --start-index 25 ~/Movies
```
This will start scanning from the 25th video file.

### Example 3: Check What Videos Will Be Scanned
```bash
python3 corruptvideoinspector_cli.py --list-videos ~/Movies
```
This shows all video files that would be scanned without actually scanning them.

### Example 4: Generate JSON Output
```bash
python3 corruptvideoinspector_cli.py --json ~/Movies
```
This creates a comprehensive JSON report with detailed scan results and statistics.

### Example 5: Verbose Output for Debugging
```bash
python3 corruptvideoinspector_cli.py --verbose ~/Movies
```
This shows detailed ffmpeg output for troubleshooting.

### Example 6: Combine Multiple Options
```bash
python3 corruptvideoinspector_cli.py --json --verbose --start-index 10 ~/Movies
```
This resumes from video 10, shows detailed output, and generates JSON reports.

## JSON Output Format

When using the `--json` option, the _Results.json file contains:

### Sample JSON Structure
```json
{
  "scan_info": {
    "directory": "/path/to/videos",
    "start_index": 1,
    "start_time": "2025-01-20T10:30:00.123456",
    "platform": "Linux",
    "ffmpeg_command": "ffmpeg",
    "total_video_files": 100
  },
  "results": [
    {
      "filename": "video.mp4",
      "full_path": "/path/to/videos/video.mp4",
      "index": 1,
      "processing_time_seconds": 2.45,
      "processing_time_readable": "0:00:02",
      "corrupted": false,
      "ffmpeg_output": "",
      "timestamp": "2025-01-20T10:30:02.123456"
    }
  ],
  "summary": {
    "total_files_found": 100,
    "files_processed": 95,
    "files_skipped": 5,
    "corrupted_files": 3,
    "healthy_files": 92,
    "corruption_rate": 3.16,
    "scan_duration_seconds": 450.67,
    "scan_duration_readable": "0:07:30",
    "end_time": "2025-01-20T10:37:30.789012",
    "average_processing_time": 4.74
  }
}
```

## How It Works

1. **Discovery**: The tool recursively searches the specified directory and all subdirectories for video files with supported extensions.

2. **Sorting**: Video files are sorted alphabetically to ensure consistent ordering across runs.

3. **Analysis**: Each video file is analyzed using ffmpeg with the command:
   ```bash
   ffmpeg -v error -i "video_file" -f null -
   ```

4. **Corruption Detection**: If ffmpeg produces any error output, the video is marked as corrupted. This is a very thorough method that checks the entire video file.

5. **Reporting**: Results are displayed in real-time and saved to log and CSV files.

## Performance Notes

- **Speed**: Video analysis is CPU-intensive and can take 2-5 minutes per GB of video content
- **CPU Usage**: ffmpeg will use significant CPU resources (80-100%) during scanning
- **Memory**: Memory usage is minimal as files are processed one at a time
- **Interruption**: You can safely interrupt the scan with Ctrl+C and resume later using `--start-index`

## Troubleshooting

### "ffmpeg is required but not found"
This means ffmpeg is not installed or not in your system PATH. Install it using your package manager.

### "Permission denied" errors
Ensure you have read permissions for the video files and write permissions for the directory (to create log files).

### "Exec format error" 
This typically means the bundled ffmpeg binary is for a different architecture. Install ffmpeg system-wide instead.

### Very slow scanning
This is normal behavior. The tool performs a complete integrity check of each video file, which is thorough but time-consuming.

## Compatibility

- ✅ **Linux**: Fully supported with system ffmpeg
- ✅ **macOS**: Supported (can use bundled or system ffmpeg)
- ✅ **Windows**: Supported (uses bundled ffmpeg.exe)

## Original GUI Version

The original GUI version (`CorruptVideoInspector.py`) has been updated to support Linux as well. You can still use the GUI interface on Linux systems that have tkinter installed:

```bash
sudo apt install python3-tk  # Install tkinter on Ubuntu/Debian
python3 CorruptVideoInspector.py
```

## Migration from GUI

If you were using the GUI version and want to switch to CLI:

1. The output format is identical (same _Logs.log and _Results.csv files)
2. You can resume interrupted GUI scans using the CLI `--start-index` option
3. All video detection and analysis logic is the same

## Integration

The CLI can be easily integrated into scripts and automation workflows:

```bash
#!/bin/bash
# Example script to scan multiple directories
for dir in /media/video1 /media/video2 /media/video3; do
    echo "Scanning $dir..."
    python3 corruptvideoinspector_cli.py "$dir"
    echo "Completed $dir"
done
```