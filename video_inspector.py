"""
Video inspection functionality using FFmpeg with hybrid detection mode
"""

import json
import logging
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure module logger
logger = logging.getLogger(__name__)


class ScanMode(Enum):
    """Scan modes for video inspection"""

    QUICK = "quick"
    DEEP = "deep"
    HYBRID = "hybrid"


@dataclass
class VideoFile:
    """
    Represents a video file with its properties.

    Attributes:
        filename: Path to the video file
        size: File size in bytes
        duration: Video duration in seconds
    """

    filename: str
    size: int = 0
    duration: float = 0.0

    def __post_init__(self) -> None:
        """Initialize file size if file exists."""
        if os.path.exists(self.filename):
            self.size = os.path.getsize(self.filename)
            logger.debug(f"VideoFile created: {self.filename} ({self.size} bytes)")


class VideoInspectionResult:
    """
    Results of video file inspection.

    Attributes:
        filename: Path to the inspected video file
        is_corrupt: Whether the file is determined to be corrupt
        error_message: Description of any errors found
        ffmpeg_output: Raw output from ffmpeg
        inspection_time: Time taken for inspection in seconds
        file_size: Size of the file in bytes
        scan_mode: Mode used for scanning
        needs_deep_scan: Whether file needs deeper analysis
        deep_scan_completed: Whether deep scan was performed
    """

    def __init__(self, filename: str):
        """
        Initialize inspection result.

        Args:
            filename: Path to the video file
        """
        self.filename = filename
        self.is_corrupt = False
        self.error_message = ""
        self.ffmpeg_output = ""
        self.inspection_time = 0.0
        self.file_size = 0
        self.scan_mode = ScanMode.QUICK
        self.needs_deep_scan = False
        self.deep_scan_completed = False
        logger.debug(f"VideoInspectionResult initialized for: {filename}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary for JSON output.

        Returns:
            Dict[str, Any]: Dictionary representation of the result
        """
        return {
            "filename": self.filename,
            "is_corrupt": self.is_corrupt,
            "error_message": self.error_message,
            "inspection_time": self.inspection_time,
            "file_size": self.file_size,
            "scan_mode": self.scan_mode.value,
            "needs_deep_scan": self.needs_deep_scan,
            "deep_scan_completed": self.deep_scan_completed,
        }


def get_ffmpeg_command() -> Optional[str]:
    """
    Find ffmpeg command on system.

    Returns:
        Optional[str]: Path to ffmpeg command if found, None otherwise
    """
    logger.debug("Searching for ffmpeg command")
    for cmd in ["ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        try:
            logger.debug(f"Trying ffmpeg command: {cmd}")
            subprocess.run([cmd, "-version"], capture_output=True, check=True, timeout=5)
            logger.info(f"Found ffmpeg command: {cmd}")
            return cmd
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.debug(f"Failed to find ffmpeg at {cmd}: {e}")
            continue

    logger.warning("ffmpeg command not found")
    return None


def get_all_video_object_files(
    directory: str, recursive: bool = True, extensions: Optional[List[str]] = None
) -> List[VideoFile]:
    """
    Get all video files in directory as VideoFile objects.

    Args:
        directory: Path to directory to scan
        recursive: Whether to scan subdirectories recursively
        extensions: List of file extensions to include

    Returns:
        List[VideoFile]: List of VideoFile objects found
    """
    if extensions is None:
        extensions = [
            ".mp4",
            ".avi",
            ".mkv",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".m4v",
            ".mpg",
            ".mpeg",
        ]

    logger.debug(f"Scanning for video files in {directory}, recursive={recursive}")
    logger.debug(f"Looking for extensions: {extensions}")

    ext_set = {ext.lower() for ext in extensions}
    video_files = []

    path = Path(directory)

    pattern = "**/*" if recursive else "*"

    for file_path in path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in ext_set:
            video_file = VideoFile(str(file_path))
            video_files.append(video_file)
            logger.debug(f"Found video file: {file_path}")

    result = sorted(video_files, key=lambda x: x.filename)
    logger.info(f"Found {len(result)} video files in {directory}")
    return result


def inspect_single_video_quick(
    video_file: VideoFile, ffmpeg_cmd: str, verbose: bool = False
) -> VideoInspectionResult:
    """
    Quick inspection of a single video file (1 minute timeout).

    Args:
        video_file: VideoFile object to inspect
        ffmpeg_cmd: Path to ffmpeg command
        verbose: Whether to enable verbose output

    Returns:
        VideoInspectionResult: Results of the inspection
    """
    result = VideoInspectionResult(video_file.filename)
    result.file_size = video_file.size
    result.scan_mode = ScanMode.QUICK

    logger.debug(f"Starting quick scan of {video_file.filename}")
    start_time = time.time()

    try:
        # Quick scan - just check file headers and basic structure
        cmd = [
            ffmpeg_cmd,
            "-v",
            "error",
            "-i",
            video_file.filename,
            "-t",
            "10",  # Only process first 10 seconds for quick check
            "-f",
            "null",
            "-",
        ]

        logger.debug(f"Running ffmpeg command: {' '.join(cmd)}")
        process = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout for quick scan
        )

        result.ffmpeg_output = process.stderr
        logger.debug(f"FFmpeg exit code: {process.returncode}")

        # Quick corruption indicators
        quick_error_indicators = [
            "Invalid data found",
            "Error while decoding",
            "corrupt",
            "damaged",
            "incomplete",
            "truncated",
            "malformed",
            "moov atom not found",
            "Invalid NAL unit size",
        ]

        # Warning indicators that suggest need for deeper scan
        warning_indicators = [
            "Non-monotonous DTS",
            "PTS discontinuity",
            "Frame rate very high",
            "DTS out of order",
            "B-frame after EOS",
        ]

        if process.returncode != 0:
            stderr_lower = process.stderr.lower()

            # Check for definitive corruption
            if any(indicator in stderr_lower for indicator in quick_error_indicators):
                result.is_corrupt = True
                result.error_message = "Video file appears to be corrupt (quick scan)"
                logger.warning(f"Quick scan detected corruption in {video_file.filename}")
            # Check for warning signs that need deeper analysis
            elif any(indicator in stderr_lower for indicator in warning_indicators):
                result.needs_deep_scan = True
                result.error_message = "Potential issues detected - needs deep scan"
                logger.info(f"Quick scan flagged {video_file.filename} for deep scan")
            else:
                result.needs_deep_scan = True
                result.error_message = (
                    f"FFmpeg returned error code {process.returncode} - needs verification"
                )
                logger.info(f"Quick scan inconclusive for {video_file.filename}, needs deep scan")
        else:
            logger.debug(f"Quick scan completed successfully for {video_file.filename}")

    except subprocess.TimeoutExpired:
        result.needs_deep_scan = True
        result.error_message = "Quick scan timed out - needs deep scan"
        logger.warning(f"Quick scan timed out for {video_file.filename}")
    except Exception as e:
        result.needs_deep_scan = True
        result.error_message = f"Quick scan failed: {e!s} - needs deep scan"
        logger.exception(f"Quick scan failed for {video_file.filename}")

    result.inspection_time = time.time() - start_time

    if verbose:
        if result.is_corrupt:
            status = "CORRUPT"
        elif result.needs_deep_scan:
            status = "NEEDS_DEEP_SCAN"
        else:
            status = "OK"
        print(
            f"  [QUICK-{status}] {Path(video_file.filename).name} ({result.inspection_time:.2f}s)"
        )

    logger.debug(f"Quick scan completed for {video_file.filename} in {result.inspection_time:.2f}s")
    return result


def inspect_single_video_deep(
    video_file: VideoFile, ffmpeg_cmd: str, verbose: bool = False
) -> VideoInspectionResult:
    """
    Deep inspection of a single video file (full file analysis).

    Args:
        video_file: VideoFile object to inspect
        ffmpeg_cmd: Path to ffmpeg command
        verbose: Whether to enable verbose output

    Returns:
        VideoInspectionResult: Results of the inspection
    """
    result = VideoInspectionResult(video_file.filename)
    result.file_size = video_file.size
    result.scan_mode = ScanMode.DEEP
    result.deep_scan_completed = True

    logger.debug(f"Starting deep scan of {video_file.filename}")
    start_time = time.time()

    try:
        # Deep scan - analyze entire file
        cmd = [ffmpeg_cmd, "-v", "error", "-i", video_file.filename, "-f", "null", "-"]

        logger.debug(f"Running ffmpeg deep scan command: {' '.join(cmd)}")
        process = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=900,  # 15 minute timeout for deep scan
        )

        result.ffmpeg_output = process.stderr
        logger.debug(f"Deep scan ffmpeg exit code: {process.returncode}")

        # All error indicators for deep scan
        error_indicators = [
            "Invalid data found",
            "Error while decoding",
            "corrupt",
            "damaged",
            "incomplete",
            "truncated",
            "malformed",
            "moov atom not found",
            "Invalid NAL unit size",
            "decode_slice_header error",
            "concealing errors",
            "missing reference picture",
        ]

        if process.returncode != 0:
            stderr_lower = process.stderr.lower()
            if any(indicator in stderr_lower for indicator in error_indicators):
                result.is_corrupt = True
                result.error_message = "Video file is corrupt (deep scan confirmed)"
                logger.error(f"Deep scan confirmed corruption in {video_file.filename}")
            else:
                result.error_message = (
                    f"FFmpeg exited with code {process.returncode}: {process.stderr}"
                )
                logger.warning(f"Deep scan completed with warnings for {video_file.filename}")
        else:
            logger.debug(f"Deep scan completed successfully for {video_file.filename}")

    except subprocess.TimeoutExpired:
        result.is_corrupt = True
        result.error_message = "Deep scan timed out - file may be severely corrupted"
        logger.exception(f"Deep scan timed out for {video_file.filename}")
    except Exception as e:
        result.error_message = f"Deep scan failed: {e!s}"
        logger.exception(f"Deep scan failed for {video_file.filename}")

    result.inspection_time = time.time() - start_time

    if verbose:
        status = "CORRUPT" if result.is_corrupt else "OK"
        print(f"  [DEEP-{status}] {Path(video_file.filename).name} ({result.inspection_time:.2f}s)")

    logger.debug(f"Deep scan completed for {video_file.filename} in {result.inspection_time:.2f}s")
    return result


def inspect_single_video(
    video_file: VideoFile,
    ffmpeg_cmd: str,
    verbose: bool = False,
    scan_mode: ScanMode = ScanMode.QUICK,
) -> VideoInspectionResult:
    """
    Inspect a single video file based on scan mode.

    Args:
        video_file: VideoFile object to inspect
        ffmpeg_cmd: Path to ffmpeg command
        verbose: Whether to enable verbose output
        scan_mode: Mode of scanning to use

    Returns:
        VideoInspectionResult: Results of the inspection
    """
    logger.debug(f"Inspecting {video_file.filename} with {scan_mode.value} mode")

    if scan_mode == ScanMode.QUICK:
        return inspect_single_video_quick(video_file, ffmpeg_cmd, verbose)
    if scan_mode == ScanMode.DEEP:
        return inspect_single_video_deep(video_file, ffmpeg_cmd, verbose)
    # For hybrid mode, start with quick scan
    return inspect_single_video_quick(video_file, ffmpeg_cmd, verbose)


def inspect_video_files_cli(
    directory: str,
    resume: bool = True,
    verbose: bool = False,
    json_output: bool = False,
    output_file: Optional[str] = None,
    recursive: bool = True,
    extensions: Optional[List[str]] = None,
    max_workers: int = 4,
    scan_mode: ScanMode = ScanMode.HYBRID,
) -> None:
    """
    CLI interface for video inspection with hybrid detection mode.

    Args:
        directory: Directory to scan for video files
        resume: Whether to resume from previous scan
        verbose: Enable verbose output
        json_output: Generate JSON output file
        output_file: Custom output file path
        recursive: Scan subdirectories recursively
        extensions: List of file extensions to scan
        max_workers: Number of worker threads
        scan_mode: Scanning mode to use

    Raises:
        RuntimeError: If ffmpeg is not found
    """

    logger.info(f"Starting video inspection in {directory}")
    logger.info(f"Scan mode: {scan_mode.value}, workers: {max_workers}, recursive: {recursive}")

    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        logger.critical("FFmpeg not found - cannot proceed")
        raise RuntimeError("FFmpeg not found")

    # Get video files
    video_files = get_all_video_object_files(directory, recursive, extensions)
    total_files = len(video_files)

    if total_files == 0:
        logger.warning("No video files found to inspect")
        print("No video files found to inspect")
        return

    logger.info(f"Found {total_files} video files to inspect")
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
            print(
                f"\r{phase}Progress: {processed_count}/{total_files} ({percent:.1f}%)",
                end="",
                flush=True,
            )

    start_time = time.time()
    logger.info(f"Starting scan at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Phase 1: Quick scan (for HYBRID mode) or single scan (for QUICK/DEEP modes)
        if scan_mode == ScanMode.HYBRID:
            logger.info("Starting Phase 1: Quick scan")
            print("\n=== PHASE 1: QUICK SCAN ===")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks for first phase
            future_to_video = {
                executor.submit(
                    inspect_single_video,
                    video,
                    ffmpeg_cmd,
                    verbose,
                    ScanMode.QUICK if scan_mode == ScanMode.HYBRID else scan_mode,
                ): video
                for video in video_files
            }

            logger.debug(f"Submitted {len(future_to_video)} inspection tasks")

            # Process completed tasks
            for future in future_to_video:
                try:
                    result = future.result()
                    results.append(result)

                    if result.is_corrupt:
                        corrupt_count += 1
                        logger.warning(f"Corrupt file found: {result.filename}")
                        if not verbose:
                            print(f"\nCORRUPT: {Path(result.filename).name}")
                    elif result.needs_deep_scan:
                        deep_scan_needed += 1
                        logger.info(f"File needs deep scan: {result.filename}")
                        if not verbose and scan_mode == ScanMode.HYBRID:
                            print(f"\nNEEDS DEEP SCAN: {Path(result.filename).name}")

                    processed_count += 1
                    phase_label = "Quick Scan " if scan_mode == ScanMode.HYBRID else ""
                    update_progress(phase_label)

                except Exception as e:
                    logger.exception("Error processing file")
                    print(f"\nError processing file: {e}")
                    processed_count += 1
                    update_progress()

        # Phase 2: Deep scan for flagged files (HYBRID mode only)
        if scan_mode == ScanMode.HYBRID and deep_scan_needed > 0:
            logger.info(f"Starting Phase 2: Deep scan for {deep_scan_needed} files")
            print(f"\n\n=== PHASE 2: DEEP SCAN ({deep_scan_needed} files) ===")

            # Get files that need deep scanning
            files_for_deep_scan = [
                (video_files[i], results[i])
                for i in range(len(results))
                if results[i].needs_deep_scan and not results[i].is_corrupt
            ]

            processed_deep = 0

            def update_deep_progress():
                if not verbose:
                    percent = (processed_deep / deep_scan_needed) * 100
                    print(
                        f"\rDeep Scan Progress: {processed_deep}/{deep_scan_needed} ({percent:.1f}%)",
                        end="",
                        flush=True,
                    )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit deep scan tasks
                future_to_index = {}
                for _i, (video_file, old_result) in enumerate(files_for_deep_scan):
                    future = executor.submit(
                        inspect_single_video_deep, video_file, ffmpeg_cmd, verbose
                    )
                    future_to_index[future] = results.index(old_result)

                logger.debug(f"Submitted {len(future_to_index)} deep scan tasks")

                # Process deep scan results
                for future, original_index in future_to_index.items():
                    try:
                        deep_result = future.result()

                        # Update the original result with deep scan findings
                        results[original_index] = deep_result

                        if deep_result.is_corrupt:
                            corrupt_count += 1
                            logger.warning(
                                f"Deep scan confirmed corruption: {deep_result.filename}"
                            )
                            if not verbose:
                                print(f"\nDEEP SCAN CORRUPT: {Path(deep_result.filename).name}")
                        else:
                            logger.info(f"Deep scan cleared: {deep_result.filename}")

                        processed_deep += 1
                        update_deep_progress()

                    except Exception as e:
                        logger.exception("Error in deep scan")
                        print(f"\nError in deep scan: {e}")
                        processed_deep += 1
                        update_deep_progress()

    except KeyboardInterrupt:
        logger.warning(
            f"Scan interrupted by user after processing {processed_count}/{total_files} files"
        )
        print(
            f"\n\nScan interrupted by user after processing {processed_count}/{total_files} files"
        )

    total_time = time.time() - start_time
    logger.info(f"Scan completed in {total_time:.2f} seconds")

    if not verbose:
        print()  # New line after progress

    # Print summary
    print("\n" + "=" * 50)
    print("SCAN COMPLETE")
    print("=" * 50)
    print(f"Scan mode: {scan_mode.value.upper()}")
    print(f"Total files scanned: {processed_count}")
    print(f"Corrupt files found: {corrupt_count}")
    print(f"Healthy files: {processed_count - corrupt_count}")
    if scan_mode == ScanMode.HYBRID:
        print(f"Files requiring deep scan: {deep_scan_needed}")
    print(f"Total scan time: {total_time:.2f} seconds")
    print(f"Average time per file: {total_time / processed_count:.2f} seconds")

    logger.info(
        f"Scan summary - Total: {processed_count}, Corrupt: {corrupt_count}, "
        f"Healthy: {processed_count - corrupt_count}, Time: {total_time:.2f}s"
    )

    # Show corrupt files
    if corrupt_count > 0:
        logger.warning(f"Found {corrupt_count} corrupt files")
        print("\nCORRUPT FILES:")
        for result in results:
            if result.is_corrupt:
                scan_type = (
                    f" ({result.scan_mode.value} scan)" if scan_mode == ScanMode.HYBRID else ""
                )
                print(f"  - {result.filename}{scan_type}")
                logger.error(f"Corrupt file: {result.filename}")
                if result.error_message and verbose:
                    print(f"    Error: {result.error_message}")
    else:
        logger.info("No corrupt files found")

    # Generate JSON output if requested
    if json_output:
        output_path = output_file or str(Path(directory) / "corruption_scan_results.json")

        logger.info(f"Generating JSON output to {output_path}")
        json_data = {
            "scan_summary": {
                "total_files": processed_count,
                "corrupt_files": corrupt_count,
                "healthy_files": processed_count - corrupt_count,
                "deep_scans_needed": deep_scan_needed if scan_mode == ScanMode.HYBRID else 0,
                "scan_mode": scan_mode.value,
                "scan_time": total_time,
                "directory": directory,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "results": [result.to_dict() for result in results],
        }

        try:
            with Path(output_path).open("w") as f:
                json.dump(json_data, f, indent=2)
            logger.info(f"JSON results saved successfully to {output_path}")
            print(f"\nDetailed results saved to: {output_path}")
        except Exception as e:
            logger.exception("Could not save JSON results")
            print(f"Warning: Could not save JSON results: {e}")

    logger.info("Video inspection process completed")
