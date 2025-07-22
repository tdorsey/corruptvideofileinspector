"""
Video inspection functionality using FFmpeg with hybrid detection mode
"""
import os
import subprocess
import json
import threading
import time
import tempfile
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum


class ScanMode(Enum):
    """Scan modes for video inspection"""
    QUICK = "quick"
    DEEP = "deep"
    HYBRID = "hybrid"


@dataclass
class VideoFile:
    """Represents a video file with its properties"""
    filename: str
    size: int = 0
    duration: float = 0.0
    
    def __post_init__(self):
        if os.path.exists(self.filename):
            self.size = os.path.getsize(self.filename)


class VideoInspectionResult:
    """Results of video file inspection"""
    def __init__(self, filename: str):
        self.filename = filename
        self.is_corrupt = False
        self.error_message = ""
        self.ffmpeg_output = ""
        self.inspection_time = 0.0
        self.file_size = 0
        self.scan_mode = ScanMode.QUICK
        self.needs_deep_scan = False
        self.deep_scan_completed = False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON output"""
        return {
            'filename': self.filename,
            'is_corrupt': self.is_corrupt,
            'error_message': self.error_message,
            'inspection_time': self.inspection_time,
            'file_size': self.file_size,
            'scan_mode': self.scan_mode.value,
            'needs_deep_scan': self.needs_deep_scan,
            'deep_scan_completed': self.deep_scan_completed
        }


@dataclass
class WALEntry:
    """Write-ahead log entry for tracking scan progress"""
    filename: str
    result: Dict[str, Any]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'filename': self.filename,
            'result': self.result,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WALEntry':
        return cls(
            filename=data['filename'],
            result=data['result'],
            timestamp=data['timestamp']
        )


class WriteAheadLog:
    """Write-ahead log for resuming interrupted directory scans"""
    
    def __init__(self, directory: str, scan_mode: ScanMode, extensions: Optional[List[str]] = None):
        self.directory = directory
        self.scan_mode = scan_mode
        # Use the same default extensions as get_all_video_object_files
        if extensions is None:
            self.extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg']
        else:
            self.extensions = extensions
        
        # Generate unique WAL filename based on directory and scan parameters
        dir_hash = hashlib.md5(directory.encode()).hexdigest()[:8]
        mode_hash = hashlib.md5(f"{scan_mode.value}-{'-'.join(sorted(self.extensions))}".encode()).hexdigest()[:8]
        wal_filename = f"corrupt_video_inspector_wal_{dir_hash}_{mode_hash}.json"
        
        self.wal_path = Path(tempfile.gettempdir()) / wal_filename
        self.lock = threading.Lock()
        self.processed_files: Set[str] = set()
        self.results: List[WALEntry] = []
        
    def load_existing_wal(self) -> bool:
        """Load existing WAL file if it exists. Returns True if resuming."""
        if not self.wal_path.exists():
            return False
            
        try:
            with open(self.wal_path, 'r') as f:
                data = json.load(f)
            
            # Verify WAL is for the same directory and scan mode
            if (data.get('directory') != self.directory or 
                data.get('scan_mode') != self.scan_mode.value or
                data.get('extensions') != sorted(self.extensions)):
                # Different scan parameters, ignore existing WAL
                return False
            
            # Load processed entries
            for entry_data in data.get('entries', []):
                entry = WALEntry.from_dict(entry_data)
                self.results.append(entry)
                self.processed_files.add(entry.filename)
                
            return True
            
        except (json.JSONDecodeError, KeyError, Exception):
            # Corrupted WAL file, start fresh
            return False
    
    def create_wal_file(self) -> None:
        """Create a new WAL file with metadata"""
        wal_data = {
            'directory': self.directory,
            'scan_mode': self.scan_mode.value,
            'extensions': sorted(self.extensions),
            'created_at': time.time(),
            'entries': []
        }
        
        with self.lock:
            try:
                with open(self.wal_path, 'w') as f:
                    json.dump(wal_data, f, indent=2)
            except Exception as e:
                # If we can't create WAL file, continue without it
                print(f"Warning: Could not create WAL file: {e}")
    
    def append_result(self, result: VideoInspectionResult) -> None:
        """Append a scan result to the WAL file"""
        entry = WALEntry(
            filename=result.filename,
            result=result.to_dict(),
            timestamp=time.time()
        )
        
        with self.lock:
            self.results.append(entry)
            self.processed_files.add(result.filename)
            
            try:
                # Read current WAL file
                if self.wal_path.exists():
                    with open(self.wal_path, 'r') as f:
                        wal_data = json.load(f)
                else:
                    wal_data = {
                        'directory': self.directory,
                        'scan_mode': self.scan_mode.value,
                        'extensions': sorted(self.extensions),
                        'created_at': time.time(),
                        'entries': []
                    }
                
                # Append new entry
                wal_data['entries'].append(entry.to_dict())
                
                # Write back to file
                with open(self.wal_path, 'w') as f:
                    json.dump(wal_data, f, indent=2)
                    
            except Exception as e:
                # If we can't write to WAL file, continue without it
                print(f"Warning: Could not update WAL file: {e}")
    
    def is_processed(self, filename: str) -> bool:
        """Check if a file has already been processed"""
        return filename in self.processed_files
    
    def get_completed_results(self) -> List[VideoInspectionResult]:
        """Get all completed results from WAL"""
        results = []
        for entry in self.results:
            # Reconstruct VideoInspectionResult from stored data
            result = VideoInspectionResult(entry.result['filename'])
            result.is_corrupt = entry.result['is_corrupt']
            result.error_message = entry.result['error_message']
            result.ffmpeg_output = entry.result.get('ffmpeg_output', '')
            result.inspection_time = entry.result['inspection_time']
            result.file_size = entry.result['file_size']
            result.scan_mode = ScanMode(entry.result['scan_mode'])
            result.needs_deep_scan = entry.result.get('needs_deep_scan', False)
            result.deep_scan_completed = entry.result.get('deep_scan_completed', False)
            results.append(result)
        return results
    
    def cleanup(self) -> None:
        """Remove the WAL file after successful completion"""
        try:
            if self.wal_path.exists():
                self.wal_path.unlink()
        except Exception as e:
            print(f"Warning: Could not remove WAL file: {e}")
    
    def get_resume_info(self) -> Dict[str, Any]:
        """Get information about what can be resumed"""
        return {
            'total_completed': len(self.results),
            'wal_file': str(self.wal_path),
            'last_processed': self.results[-1].timestamp if self.results else None
        }


def get_ffmpeg_command() -> Optional[str]:
    """Find ffmpeg command on system"""
    for cmd in ['ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg']:
        try:
            subprocess.run([cmd, '-version'], 
                         capture_output=True, 
                         check=True, 
                         timeout=5)
            return cmd
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def get_all_video_object_files(directory: str, recursive: bool = True, extensions: Optional[List[str]] = None) -> List[VideoFile]:
    """Get all video files in directory as VideoFile objects"""
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg']
    
    ext_set = {ext.lower() for ext in extensions}
    video_files = []
    
    path = Path(directory)
    
    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"
    
    for file_path in path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in ext_set:
            video_files.append(VideoFile(str(file_path)))
    
    return sorted(video_files, key=lambda x: x.filename)


def inspect_single_video_quick(video_file: VideoFile, ffmpeg_cmd: str, verbose: bool = False) -> VideoInspectionResult:
    """Quick inspection of a single video file (1 minute timeout)"""
    result = VideoInspectionResult(video_file.filename)
    result.file_size = video_file.size
    result.scan_mode = ScanMode.QUICK
    
    start_time = time.time()
    
    try:
        # Quick scan - just check file headers and basic structure
        cmd = [
            ffmpeg_cmd, '-v', 'error', '-i', video_file.filename,
            '-t', '10',  # Only process first 10 seconds for quick check
            '-f', 'null', '-'
        ]
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout for quick scan
        )
        
        result.ffmpeg_output = process.stderr
        
        # Quick corruption indicators
        quick_error_indicators = [
            'Invalid data found',
            'Error while decoding',
            'corrupt',
            'damaged',
            'incomplete',
            'truncated',
            'malformed',
            'moov atom not found',
            'Invalid NAL unit size'
        ]
        
        # Warning indicators that suggest need for deeper scan
        warning_indicators = [
            'Non-monotonous DTS',
            'PTS discontinuity',
            'Frame rate very high',
            'DTS out of order',
            'B-frame after EOS'
        ]
        
        if process.returncode != 0:
            stderr_lower = process.stderr.lower()
            
            # Check for definitive corruption
            if any(indicator in stderr_lower for indicator in quick_error_indicators):
                result.is_corrupt = True
                result.error_message = "Video file appears to be corrupt (quick scan)"
            # Check for warning signs that need deeper analysis
            elif any(indicator in stderr_lower for indicator in warning_indicators):
                result.needs_deep_scan = True
                result.error_message = "Potential issues detected - needs deep scan"
            else:
                result.needs_deep_scan = True
                result.error_message = f"FFmpeg returned error code {process.returncode} - needs verification"
        
    except subprocess.TimeoutExpired:
        result.needs_deep_scan = True
        result.error_message = "Quick scan timed out - needs deep scan"
    except Exception as e:
        result.needs_deep_scan = True
        result.error_message = f"Quick scan failed: {str(e)} - needs deep scan"
    
    result.inspection_time = time.time() - start_time
    
    if verbose:
        if result.is_corrupt:
            status = "CORRUPT"
        elif result.needs_deep_scan:
            status = "NEEDS_DEEP_SCAN"
        else:
            status = "OK"
        print(f"  [QUICK-{status}] {os.path.basename(video_file.filename)} ({result.inspection_time:.2f}s)")
    
    return result


def inspect_single_video_deep(video_file: VideoFile, ffmpeg_cmd: str, verbose: bool = False) -> VideoInspectionResult:
    """Deep inspection of a single video file (full file analysis)"""
    result = VideoInspectionResult(video_file.filename)
    result.file_size = video_file.size
    result.scan_mode = ScanMode.DEEP
    result.deep_scan_completed = True
    
    start_time = time.time()
    
    try:
        # Deep scan - analyze entire file
        cmd = [
            ffmpeg_cmd, '-v', 'error', '-i', video_file.filename,
            '-f', 'null', '-'
        ]
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900  # 15 minute timeout for deep scan
        )
        
        result.ffmpeg_output = process.stderr
        
        # All error indicators for deep scan
        error_indicators = [
            'Invalid data found',
            'Error while decoding',
            'corrupt',
            'damaged',
            'incomplete',
            'truncated',
            'malformed',
            'moov atom not found',
            'Invalid NAL unit size',
            'decode_slice_header error',
            'concealing errors',
            'missing reference picture'
        ]
        
        if process.returncode != 0:
            stderr_lower = process.stderr.lower()
            if any(indicator in stderr_lower for indicator in error_indicators):
                result.is_corrupt = True
                result.error_message = "Video file is corrupt (deep scan confirmed)"
            else:
                result.error_message = f"FFmpeg exited with code {process.returncode}: {process.stderr}"
        
    except subprocess.TimeoutExpired:
        result.is_corrupt = True
        result.error_message = "Deep scan timed out - file may be severely corrupted"
    except Exception as e:
        result.error_message = f"Deep scan failed: {str(e)}"
    
    result.inspection_time = time.time() - start_time
    
    if verbose:
        status = "CORRUPT" if result.is_corrupt else "OK"
        print(f"  [DEEP-{status}] {os.path.basename(video_file.filename)} ({result.inspection_time:.2f}s)")
    
    return result


def inspect_single_video(video_file: VideoFile, ffmpeg_cmd: str, verbose: bool = False, scan_mode: ScanMode = ScanMode.QUICK) -> VideoInspectionResult:
    """Inspect a single video file based on scan mode"""
    if scan_mode == ScanMode.QUICK:
        return inspect_single_video_quick(video_file, ffmpeg_cmd, verbose)
    elif scan_mode == ScanMode.DEEP:
        return inspect_single_video_deep(video_file, ffmpeg_cmd, verbose)
    else:
        # For hybrid mode, start with quick scan
        return inspect_single_video_quick(video_file, ffmpeg_cmd, verbose)


def inspect_video_files_cli(directory: str, resume: bool = True, verbose: bool = False, 
                           json_output: bool = False, output_file: Optional[str] = None,
                           recursive: bool = True, extensions: Optional[List[str]] = None,
                           max_workers: int = 4, scan_mode: ScanMode = ScanMode.HYBRID) -> None:
    """CLI interface for video inspection with hybrid detection mode"""
    
    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        raise RuntimeError("FFmpeg not found")
    
    # Initialize Write-Ahead Log
    wal = WriteAheadLog(directory, scan_mode, extensions) if resume else None
    resuming_scan = False
    
    if wal and resume:
        resuming_scan = wal.load_existing_wal()
        if not resuming_scan:
            wal.create_wal_file()
    
    # Get video files
    video_files = get_all_video_object_files(directory, recursive, extensions)
    total_files = len(video_files)
    
    if total_files == 0:
        print("No video files found to inspect")
        return
    
    # Initialize results from WAL if resuming
    results = []
    corrupt_count = 0
    processed_count = 0
    deep_scan_needed = 0
    
    if resuming_scan and wal:
        results = wal.get_completed_results()
        processed_count = len(results)
        corrupt_count = sum(1 for r in results if r.is_corrupt)
        deep_scan_needed = sum(1 for r in results if r.needs_deep_scan and not r.is_corrupt)
        
        resume_info = wal.get_resume_info()
        print(f"Resuming scan from previous session...")
        print(f"Already processed: {resume_info['total_completed']} files")
        if resume_info['last_processed']:
            last_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(resume_info['last_processed']))
            print(f"Last processed: {last_time}")
    
    print(f"Found {total_files} video files to inspect")
    print(f"Scan mode: {scan_mode.value.upper()}")
    print(f"Using {max_workers} worker threads")
    
    # Filter out already processed files if resuming
    if resuming_scan and wal:
        video_files = [vf for vf in video_files if not wal.is_processed(vf.filename)]
        remaining_files = len(video_files)
        print(f"Remaining files to process: {remaining_files}")
    else:
        remaining_files = total_files
    
    # Progress tracking
    def update_progress(phase=""):
        if not verbose:
            current_total = processed_count
            percent = (current_total / total_files) * 100
            print(f"\r{phase}Progress: {current_total}/{total_files} ({percent:.1f}%)", end="", flush=True)
    
    start_time = time.time()
    
    try:
        # Phase 1: Quick scan (for HYBRID mode) or single scan (for QUICK/DEEP modes)
        if scan_mode == ScanMode.HYBRID:
            print("\n=== PHASE 1: QUICK SCAN ===")
        
        if remaining_files > 0:  # Only scan if there are remaining files
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks for first phase
                future_to_video = {
                    executor.submit(inspect_single_video, video, ffmpeg_cmd, verbose, 
                                   ScanMode.QUICK if scan_mode == ScanMode.HYBRID else scan_mode): video 
                    for video in video_files
                }
                
                # Process completed tasks
                for future in future_to_video:
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Update WAL with new result
                        if wal:
                            wal.append_result(result)
                        
                        if result.is_corrupt:
                            corrupt_count += 1
                            if not verbose:
                                print(f"\nCORRUPT: {os.path.basename(result.filename)}")
                        elif result.needs_deep_scan:
                            deep_scan_needed += 1
                            if not verbose and scan_mode == ScanMode.HYBRID:
                                print(f"\nNEEDS DEEP SCAN: {os.path.basename(result.filename)}")
                        
                        processed_count += 1
                        phase_label = "Quick Scan " if scan_mode == ScanMode.HYBRID else ""
                        update_progress(phase_label)
                        
                    except Exception as e:
                        print(f"\nError processing file: {e}")
                        processed_count += 1
                        update_progress()
        
        # Phase 2: Deep scan for flagged files (HYBRID mode only)
        if scan_mode == ScanMode.HYBRID and deep_scan_needed > 0:
            print(f"\n\n=== PHASE 2: DEEP SCAN ({deep_scan_needed} files) ===")
            
            # Get files that need deep scanning (including those from resumed session)
            files_for_deep_scan = []
            for i, result in enumerate(results):
                if result.needs_deep_scan and not result.is_corrupt and not result.deep_scan_completed:
                    # Find the corresponding video file
                    video_file = None
                    for vf in get_all_video_object_files(directory, recursive, extensions):
                        if vf.filename == result.filename:
                            video_file = vf
                            break
                    if video_file:
                        files_for_deep_scan.append((video_file, result, i))
            
            processed_deep = 0
            
            def update_deep_progress():
                if not verbose:
                    percent = (processed_deep / deep_scan_needed) * 100
                    print(f"\rDeep Scan Progress: {processed_deep}/{deep_scan_needed} ({percent:.1f}%)", end="", flush=True)
            
            if files_for_deep_scan:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit deep scan tasks
                    future_to_index = {}
                    for video_file, old_result, result_index in files_for_deep_scan:
                        future = executor.submit(inspect_single_video_deep, video_file, ffmpeg_cmd, verbose)
                        future_to_index[future] = result_index
                    
                    # Process deep scan results
                    for future in future_to_index:
                        try:
                            deep_result = future.result()
                            result_index = future_to_index[future]
                            
                            # Update the original result with deep scan findings
                            results[result_index] = deep_result
                            
                            # Update WAL with deep scan result
                            if wal:
                                wal.append_result(deep_result)
                            
                            if deep_result.is_corrupt:
                                corrupt_count += 1
                                if not verbose:
                                    print(f"\nDEEP SCAN CORRUPT: {os.path.basename(deep_result.filename)}")
                            
                            processed_deep += 1
                            update_deep_progress()
                            
                        except Exception as e:
                            print(f"\nError in deep scan: {e}")
                            processed_deep += 1
                            update_deep_progress()
    
    except KeyboardInterrupt:
        print(f"\n\nScan interrupted by user after processing {processed_count}/{total_files} files")
        if wal:
            print(f"Progress saved to WAL file. Use same command to resume from: {wal.wal_path}")
        raise  # Re-raise to maintain exit code
    
    total_time = time.time() - start_time
    
    if not verbose:
        print()  # New line after progress
    
    # Clean up WAL file on successful completion
    if wal:
        wal.cleanup()
    
    # Print summary
    print(f"\n" + "="*50)
    print(f"SCAN COMPLETE")
    print(f"="*50)
    print(f"Scan mode: {scan_mode.value.upper()}")
    print(f"Total files scanned: {processed_count}")
    print(f"Corrupt files found: {corrupt_count}")
    print(f"Healthy files: {processed_count - corrupt_count}")
    if scan_mode == ScanMode.HYBRID:
        print(f"Files requiring deep scan: {deep_scan_needed}")
    print(f"Total scan time: {total_time:.2f} seconds")
    print(f"Average time per file: {total_time/processed_count:.2f} seconds" if processed_count > 0 else "No files processed")
    
    # Show corrupt files
    if corrupt_count > 0:
        print(f"\nCORRUPT FILES:")
        for result in results:
            if result.is_corrupt:
                scan_type = f" ({result.scan_mode.value} scan)" if scan_mode == ScanMode.HYBRID else ""
                print(f"  - {result.filename}{scan_type}")
                if result.error_message and verbose:
                    print(f"    Error: {result.error_message}")
    
    # Generate JSON output if requested
    if json_output:
        output_path = output_file or os.path.join(directory, 'corruption_scan_results.json')
        
        json_data = {
            'scan_summary': {
                'total_files': processed_count,
                'corrupt_files': corrupt_count,
                'healthy_files': processed_count - corrupt_count,
                'deep_scans_needed': deep_scan_needed if scan_mode == ScanMode.HYBRID else 0,
                'scan_mode': scan_mode.value,
                'scan_time': total_time,
                'directory': directory,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'resumed_scan': resuming_scan
            },
            'results': [result.to_dict() for result in results]
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            print(f"\nDetailed results saved to: {output_path}")
        except Exception as e:
            print(f"Warning: Could not save JSON results: {e}")
