"""
Video inspection functionality using FFmpeg with hybrid detection mode
"""
import os
import subprocess
import json
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
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
    
    # Get video files
    video_files = get_all_video_object_files(directory, recursive, extensions)
    total_files = len(video_files)
    
    if total_files == 0:
        print("No video files found to inspect")
        return
    
    print(f"Found {total_files} video files to inspect")
    print(f"Scan mode: {scan_mode.value.upper()}")
    print(f"Using {max_workers} worker threads")
    
    results = []
    corrupt_count = 0
    processed_count = 0
    deep_scan_needed = 0
    
    # Progress tracking
    def update_progress(phase=""):
        if not verbose:
            percent = (processed_count / total_files) * 100
            print(f"\r{phase}Progress: {processed_count}/{total_files} ({percent:.1f}%)", end="", flush=True)
    
    start_time = time.time()
    
    try:
        # Phase 1: Quick scan (for HYBRID mode) or single scan (for QUICK/DEEP modes)
        if scan_mode == ScanMode.HYBRID:
            print("\n=== PHASE 1: QUICK SCAN ===")
        
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
            
            # Get files that need deep scanning
            files_for_deep_scan = [
                (video_files[i], results[i]) for i in range(len(results))
                if results[i].needs_deep_scan and not results[i].is_corrupt
            ]
            
            processed_deep = 0
            
            def update_deep_progress():
                if not verbose:
                    percent = (processed_deep / deep_scan_needed) * 100
                    print(f"\rDeep Scan Progress: {processed_deep}/{deep_scan_needed} ({percent:.1f}%)", end="", flush=True)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit deep scan tasks
                future_to_index = {}
                for i, (video_file, old_result) in enumerate(files_for_deep_scan):
                    future = executor.submit(inspect_single_video_deep, video_file, ffmpeg_cmd, verbose)
                    future_to_index[future] = results.index(old_result)
                
                # Process deep scan results
                for future in future_to_index:
                    try:
                        deep_result = future.result()
                        original_index = future_to_index[future]
                        
                        # Update the original result with deep scan findings
                        results[original_index] = deep_result
                        
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
    
    total_time = time.time() - start_time
    
    if not verbose:
        print()  # New line after progress
    
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
    print(f"Average time per file: {total_time/processed_count:.2f} seconds")
    
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
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'results': [result.to_dict() for result in results]
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            print(f"\nDetailed results saved to: {output_path}")
        except Exception as e:
            print(f"Warning: Could not save JSON results: {e}")
