#!/usr/bin/env python3
"""
Example usage of the report generation functionality.

This script demonstrates how to         print("Supported formats:")
        print("- JSON: Structured data, API-friendly")
        print("- CSV: Spreadsheet-compatible, data analysis")  
        print("- YAML: Human-readable configuration format")
        print("- Text: Human-readable summary reports")e various report generation features
in the Corrupt Video Inspector.
"""

import tempfile
from pathlib import Path
from datetime import datetime

# Mock data for demonstration (in real usage, this would come from actual scans)
from src.core.models.scanning import ScanMode, ScanResult, ScanSummary
from src.core.models.inspection import VideoFile
from src.core.reporter import (
    ReportService,
    generate_json_report,
    generate_csv_summary,
    JSONReportGenerator,
    CSVReportGenerator,
    YAMLReportGenerator,
    TextReportGenerator,
)


def create_mock_data():
    """Create mock scan data for demonstration."""

    # Create mock video files
    video_files = [
        VideoFile(Path("/movies/action_movie.mp4")),
        VideoFile(Path("/movies/comedy_show.mkv")),
        VideoFile(Path("/movies/drama_series.avi")),
        VideoFile(Path("/movies/corrupt_video.mp4")),
        VideoFile(Path("/tv_shows/season1/episode1.mkv")),
    ]

    # Create mock scan results
    results = []
    for i, video_file in enumerate(video_files):
        is_corrupt = i == 3  # Make the 4th file corrupt
        confidence = 0.95 if is_corrupt else 0.05

        result = ScanResult(
            video_file=video_file,
            is_corrupt=is_corrupt,
            error_message="Detected frame corruption" if is_corrupt else "",
            inspection_time=2.5 + i * 0.5,
            scan_mode=ScanMode.HYBRID,
            confidence=confidence,
        )
        results.append(result)

    # Create mock summary
    summary = ScanSummary(
        directory=Path("/movies"),
        total_files=5,
        processed_files=5,
        corrupt_files=1,
        healthy_files=4,
        scan_mode=ScanMode.HYBRID,
        scan_time=15.75,
        deep_scans_needed=1,
        deep_scans_completed=1,
    )

    return summary, results


def demonstrate_individual_generators():
    """Demonstrate using individual report generators."""
    print("=== Demonstrating Individual Report Generators ===")

    summary, results = create_mock_data()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # JSON Report
        print("\n1. Generating JSON Report...")
        json_path = temp_path / "report.json"
        generate_json_report(summary, results, json_path, include_healthy=True)
        print(f"   JSON report size: {json_path.stat().st_size} bytes")

        # CSV Report
        print("\n2. Generating CSV Report...")
        csv_path = temp_path / "report.csv"
        generate_csv_summary(summary, results, csv_path)
        print(f"   CSV report size: {csv_path.stat().st_size} bytes")


def demonstrate_report_service():
    """Demonstrate using the ReportService for multiple formats."""
    print("\n=== Demonstrating ReportService ===")

    summary, results = create_mock_data()

    # Mock config (in real usage, this would be loaded from config)
    class MockConfig:
        class Output:
            default_output_dir = Path("/tmp")
            default_json = True
            default_output_dir = Path("/tmp")
            default_filename = "scan_results.json"

    # Note: This would normally use AppConfig but we're mocking for demo
    try:
        # This would work with proper config setup:
        # service = ReportService(config)

        # For now, just show what formats are supported
        from src.core.reporter import ReportService

        print("\nSupported formats:")
        print("- JSON: Structured data, API-friendly")
        print("- CSV: Spreadsheet-compatible, data analysis")
        print("- YAML: Human-readable configuration format")
        print("- XML: Enterprise-compatible structured data")
        print("- Text: Human-readable summary reports")

        print("\nReport features:")
        print("- Comprehensive analytics (file sizes, scan times, confidence)")
        print("- Filtering options (healthy/corrupt files, confidence levels)")
        print("- Grouping by directory or file extension")
        print("- Metadata tracking (generation time, tool version, config)")

    except Exception as e:
        print(f"Note: Full ReportService demo requires proper config setup: {e}")


def demonstrate_report_features():
    """Show the key features of the reporting system."""
    print("\n=== Report Generation Features ===")

    summary, results = create_mock_data()

    print(f"\nScan Summary:")
    print(f"- Directory: {summary.directory}")
    print(f"- Total files: {summary.total_files}")
    print(f"- Corrupt files: {summary.corrupt_files}")
    print(f"- Success rate: {summary.success_rate:.1f}%")
    print(f"- Scan time: {summary.scan_time:.2f}s")
    print(f"- Processing rate: {summary.files_per_second:.1f} files/sec")

    print(f"\nFile Analysis:")
    corrupt_files = [r for r in results if r.is_corrupt]
    healthy_files = [r for r in results if not r.is_corrupt]

    print(f"- Corrupt files: {len(corrupt_files)}")
    for cf in corrupt_files:
        print(f"  * {cf.filename} (confidence: {cf.confidence_percentage:.1f}%)")

    print(f"- Healthy files: {len(healthy_files)}")
    for hf in healthy_files[:2]:  # Show first 2
        print(f"  * {hf.filename} ({hf.inspection_time:.2f}s scan)")
    if len(healthy_files) > 2:
        print(f"  * ... and {len(healthy_files) - 2} more")

    print(f"\nReport Output Options:")
    print("- Include/exclude healthy files")
    print("- Include/exclude FFmpeg raw output")
    print("- Sort by path, size, corruption status, confidence")
    print("- Group results by directory")
    print("- Filter by confidence threshold")


if __name__ == "__main__":
    print("Corrupt Video Inspector - Report Generation Demo")
    print("=" * 50)

    try:
        demonstrate_report_features()
        demonstrate_individual_generators()
        demonstrate_report_service()

        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nTo use in production:")
        print("1. Run a video scan to get real results")
        print("2. Use ReportService.generate_report() with your data")
        print("3. Choose from JSON, CSV, YAML, or Text formats")
        print("4. Customize with filtering and sorting options")

    except Exception as e:
        print(f"\nDemo error (expected due to config dependencies): {e}")
        print("\nThis is normal - the demo shows the structure and features")
        print("that would work with a fully configured environment.")
