"""
Scan result processing and analysis utilities.
"""

from pathlib import Path
from typing import Any

from src.core.models.inspection import VideoFile
from src.core.models.scanning import (
    ScanFilter,
    ScanMode,
    ScanResult,
    ScanSummary,
)


def create_video_file_from_path(path: str | Path) -> VideoFile:
    """Create a VideoFile instance from a file path."""
    path_obj = Path(path) if isinstance(path, str) else path
    if not path_obj.exists():
        msg = f"Video file not found: {path_obj}"
        raise FileNotFoundError(msg)
    if not path_obj.is_file():
        msg = f"Path is not a file: {path_obj}"
        raise ValueError(msg)
    return VideoFile(path=path_obj)


def filter_scan_results(results: list[ScanResult], scan_filter: ScanFilter) -> list[ScanResult]:
    """Filter scan results based on the provided filter criteria."""
    return [result for result in results if scan_filter.matches(result)]


def group_scan_results_by_directory(results: list[ScanResult]) -> dict[Path, list[ScanResult]]:
    """Group scan results by their parent directory."""
    groups: dict[Path, list[ScanResult]] = {}
    for result in results:
        directory = result.video_file.path.parent
        if directory not in groups:
            groups[directory] = []
        groups[directory].append(result)
    return groups


def merge_scan_summaries(summaries: list[ScanSummary]) -> ScanSummary:
    """Merge multiple scan summaries into a single summary.

    Args:
        summaries: List of scan summaries to merge

    Returns:
        Merged scan summary

    Raises:
        ValueError: If no summaries provided
    """
    if not summaries:
        msg = "No summaries provided for merging"
        raise ValueError(msg)

    if len(summaries) == 1:
        return summaries[0]

    # Use first summary as base
    first = summaries[0]

    # Find common parent directory
    all_dirs = [s.directory for s in summaries]
    common_parent = Path.cwd()  # fallback
    try:
        # Find the longest common path
        parts_lists = [list(d.parts) for d in all_dirs]
        min_length = min(len(parts) for parts in parts_lists)

        common_parts = []
        for i in range(min_length):
            if all(parts[i] == parts_lists[0][i] for parts in parts_lists):
                common_parts.append(parts_lists[0][i])
            else:
                break

        if common_parts:
            common_parent = Path(*common_parts)
    except Exception:
        pass  # Use fallback

    return ScanSummary(
        directory=common_parent,
        total_files=sum(s.total_files for s in summaries),
        processed_files=sum(s.processed_files for s in summaries),
        corrupt_files=sum(s.corrupt_files for s in summaries),
        healthy_files=sum(s.healthy_files for s in summaries),
        scan_mode=first.scan_mode,  # Use first scan mode
        scan_time=sum(s.scan_time for s in summaries),
        deep_scans_needed=sum(s.deep_scans_needed for s in summaries),
        deep_scans_completed=sum(s.deep_scans_completed for s in summaries),
        started_at=min(s.started_at for s in summaries),
        completed_at=(
            max(s.completed_at for s in summaries if s.completed_at)
            if any(s.completed_at for s in summaries)
            else None
        ),
        was_resumed=any(s.was_resumed for s in summaries),
    )


def sort_scan_results(
    results: list[ScanResult], sort_by: str = "path", reverse: bool = False
) -> list[ScanResult]:
    """Sort scan results by specified field.

    Args:
        results: List of scan results to sort
        sort_by: Field to sort by
        reverse: Sort in reverse order

    Returns:
        Sorted list of scan results

    Raises:
        ValueError: If sort field is invalid
    """
    valid_fields = {"path", "size", "corruption", "confidence", "scan_time"}
    if sort_by not in valid_fields:
        msg = f"Invalid sort field: {sort_by}. Must be one of {valid_fields}"
        raise ValueError(msg)

    if sort_by == "path":

        def key_func(r):
            return str(r.video_file.path)

    elif sort_by == "size":

        def key_func(r):
            return r.video_file.size

    elif sort_by == "corruption":

        def key_func(r):
            return (r.is_corrupt, r.needs_deep_scan)

    elif sort_by == "confidence":

        def key_func(r):
            return r.confidence

    elif sort_by == "scan_time":

        def key_func(r):
            return r.inspection_time

    else:

        def key_func(r):
            return str(r.video_file.path)  # fallback

    return sorted(results, key=key_func, reverse=reverse)


def calculate_scan_statistics(results: list[ScanResult]) -> dict[str, Any]:
    """Calculate comprehensive statistics from scan results.

    Args:
        results: List of scan results to analyze

    Returns:
        Dictionary with statistical information
    """
    if not results:
        return {
            "total_files": 0,
            "corrupt_files": 0,
            "healthy_files": 0,
            "suspicious_files": 0,
            "corruption_rate": 0.0,
            "average_confidence": 0.0,
            "total_size": 0,
            "average_scan_time": 0.0,
        }

    total_files = len(results)
    corrupt_files = sum(1 for r in results if r.is_corrupt)
    suspicious_files = sum(1 for r in results if r.needs_deep_scan and not r.is_corrupt)
    healthy_files = total_files - corrupt_files - suspicious_files

    total_size = sum(r.video_file.size for r in results)
    total_scan_time = sum(r.inspection_time for r in results)

    # Calculate averages
    avg_confidence = sum(r.confidence for r in results) / total_files
    avg_scan_time = total_scan_time / total_files

    # Group by file extensions
    extensions: dict[str, int] = {}
    for result in results:
        ext = result.video_file.suffix.lower()
        extensions[ext] = extensions.get(ext, 0) + 1

    # Find largest and smallest files
    largest_file = max(results, key=lambda r: r.video_file.size) if results else None
    smallest_file = min(results, key=lambda r: r.video_file.size) if results else None

    return {
        "total_files": total_files,
        "corrupt_files": corrupt_files,
        "healthy_files": healthy_files,
        "suspicious_files": suspicious_files,
        "corruption_rate": (corrupt_files / total_files) * 100.0,
        "suspicious_rate": (suspicious_files / total_files) * 100.0,
        "average_confidence": avg_confidence,
        "total_size": total_size,
        "total_size_mb": total_size / (1024 * 1024),
        "total_size_gb": total_size / (1024 * 1024 * 1024),
        "average_file_size": total_size / total_files,
        "total_scan_time": total_scan_time,
        "average_scan_time": avg_scan_time,
        "files_per_second": (total_files / total_scan_time if total_scan_time > 0 else 0),
        "extensions": extensions,
        "largest_file": (
            {
                "path": str(largest_file.video_file.path),
                "size": largest_file.video_file.size,
            }
            if largest_file
            else None
        ),
        "smallest_file": (
            {
                "path": str(smallest_file.video_file.path),
                "size": smallest_file.video_file.size,
            }
            if smallest_file
            else None
        ),
    }


def validate_scan_results(results: list[ScanResult]) -> list[str]:
    """Validate scan results and return list of issues found.

    Args:
        results: List of scan results to validate

    Returns:
        List of validation issues (empty if all valid)
    """
    issues: list[str] = []

    if not results:
        return issues

    for i, result in enumerate(results):
        # Check for missing video file
        if not result.video_file:
            issues.append(f"Result {i}: Missing video file")
            continue

        # Check for invalid paths
        if not result.video_file.path:
            issues.append(f"Result {i}: Invalid file path")

        # Check for negative values
        if result.inspection_time < 0:
            issues.append(f"Result {i}: Negative inspection time: {result.inspection_time}")

        if result.confidence < 0 or result.confidence > 1:
            issues.append(f"Result {i}: Invalid confidence value: {result.confidence}")

        # Check for logical inconsistencies
        if result.is_corrupt and result.needs_deep_scan:
            issues.append(f"Result {i}: File marked as both corrupt and needing deep scan")

        if (
            result.deep_scan_completed
            and not result.needs_deep_scan
            and result.scan_mode == ScanMode.QUICK
        ):
            issues.append(f"Result {i}: Deep scan completed but not needed and mode is quick")

    return issues
