# Report Generation System

The `src/core/reporter.py` module provides comprehensive report generation capabilities for the Corrupt Video Inspector, supporting multiple output formats and detailed analytics.

## Features

### 🎯 **Multiple Output Formats**
- **JSON**: Structured data for APIs and machine processing
- **CSV**: Spreadsheet-compatible format for data analysis
- **YAML**: Human-readable configuration format
- **Text**: Human-readable summary reports

### 📊 **Comprehensive Analytics**
- File size statistics (total, average, min/max)
- Scan time performance metrics
- Corruption confidence analysis
- File extension breakdown
- Directory-based grouping
- Processing rate calculations

### ⚙️ **Flexible Configuration**
- Include/exclude healthy files
- Filter by confidence threshold
- Sort by multiple criteria (path, size, corruption, confidence, scan time)
- Group results by directory
- Optional FFmpeg output inclusion
- Metadata tracking

## Quick Start

### Basic Usage

```python
from src.core.reporter import ReportService
from src.config.config import load_config

# Initialize the service
config = load_config()
report_service = ReportService(config)

# Generate a JSON report
report_path = report_service.generate_report(
    summary=scan_summary,
    results=scan_results,
    format="json",
    include_healthy=False,  # Only show corrupt files
)

print(f"Report generated: {report_path}")
```

### Multiple Formats

```python
# Generate reports in multiple formats
formats = ["json", "csv", "text"]
reports = report_service.generate_multiple_formats(
    summary=scan_summary,
    results=scan_results,
    formats=formats,
    include_healthy=True,
    sort_by="confidence",
)

for format, path in reports.items():
    print(f"{format.upper()} report: {path}")
```

### Quick Report Functions

```python
from src.core.reporter import generate_json_report, generate_csv_summary

# Quick JSON report
generate_json_report(
    summary=scan_summary,
    results=scan_results,
    output_path=Path("scan_report.json"),
    include_healthy=True,
)

# Quick CSV summary (corrupt files only)
generate_csv_summary(
    summary=scan_summary,
    results=scan_results,
    output_path=Path("corrupt_files.csv"),
)
```

## Report Structure

### JSON Report Example

```json
{
  "metadata": {
    "generated_at": "2025-07-26T15:30:00Z",
    "tool_version": "2.0.0",
    "report_format": "json",
    "total_results": 150
  },
  "summary": {
    "directory": "/path/to/videos",
    "total_files": 150,
    "processed_files": 150,
    "corrupt_files": 3,
    "healthy_files": 147,
    "scan_mode": "hybrid",
    "scan_time": 1234.56,
    "success_rate": 98.0,
    "files_per_second": 2.1
  },
  "analytics": {
    "file_sizes": {
      "total_gb": 45.2,
      "average_bytes": 314572800,
      "min_bytes": 52428800,
      "max_bytes": 2147483648
    },
    "file_extensions": {
      ".mp4": {"total": 120, "corrupt": 2, "healthy": 118},
      ".mkv": {"total": 25, "corrupt": 1, "healthy": 24},
      ".avi": {"total": 5, "corrupt": 0, "healthy": 5}
    },
    "corruption_confidence": {
      "average": 0.89,
      "high_confidence_count": 2,
      "medium_confidence_count": 1,
      "low_confidence_count": 0
    }
  },
  "results": [
    {
      "filename": "/path/to/video.mp4",
      "is_corrupt": false,
      "status": "HEALTHY",
      "confidence": 0.05,
      "file_size": 1073741824,
      "inspection_time": 2.3,
      "scan_mode": "quick"
    }
  ]
}
```

### Text Report Example

```
==============================================================
CORRUPT VIDEO INSPECTOR - SCAN REPORT
==============================================================

Generated: 2025-07-26 15:30:00 UTC
Tool Version: 2.0.0
Total Results: 150

SCAN SUMMARY
--------------------
Directory: /path/to/videos
Scan Mode: HYBRID
Total Files: 150
Processed: 150
Corrupt: 3
Healthy: 147
Success Rate: 98.0%
Scan Time: 1234.56 seconds
Processing Rate: 2.1 files/sec

ANALYTICS
--------------------
Total Data: 45.20 GB
Average File Size: 300.0 MB

File Extensions:
  .mp4: 120 files (1.7% corrupt)
  .mkv: 25 files (4.0% corrupt)
  .avi: 5 files (0.0% corrupt)

Corruption Confidence:
  High (>80%): 2 files
  Medium (50-80%): 1 files
  Low (<50%): 0 files

DETAILED RESULTS
--------------------

1. /path/to/corrupt_video.mp4
   Status: CORRUPT
   Size: 1024.0 MB
   Scan Time: 5.23s
   Mode: deep
   Confidence: 94.5%
   Error: Detected frame corruption
```

## Integration with CLI

The reporter is integrated into the CLI handlers through the `ReportService`:

```python
# In handlers.py
class ScanHandler(BaseHandler):
    def __init__(self, config: AppConfig):
        super().__init__(config)
        self.report_service = ReportService(config)
    
    def generate_comprehensive_report(self, summary, results, **kwargs):
        return self.report_service.generate_report(
            summary=summary,
            results=results,
            **kwargs
        )
```

## Configuration Options

Reports can be customized through `ReportConfiguration`:

```python
from src.core.models.reporting import ReportConfiguration

config = ReportConfiguration(
    output_path=Path("detailed_report.json"),
    format="json",
    include_healthy=False,           # Only corrupt files
    include_metadata=True,           # Include file metadata
    include_ffmpeg_output=False,     # Exclude raw FFmpeg output
    group_by_directory=True,         # Group by directory
    sort_by="confidence",            # Sort by confidence level
)
```

## Supported Sort Fields

- `path`: Sort by file path (alphabetical)
- `size`: Sort by file size (largest first)
- `corruption`: Sort by corruption status (corrupt first)
- `confidence`: Sort by confidence level (highest first)
- `scan_time`: Sort by scan duration (longest first)

## Error Handling

The reporter includes comprehensive error handling:

```python
try:
    report_path = report_service.generate_report(
        summary=summary,
        results=results,
        format="json"
    )
except ValueError as e:
    print(f"Invalid configuration: {e}")
except OSError as e:
    print(f"File system error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Considerations

- **Large datasets**: CSV and JSON formats are more efficient for large result sets
- **Memory usage**: Text reports load everything into memory; stream large datasets
- **File I/O**: Reports are written atomically to prevent corruption
- **Analytics**: Calculated once per report generation and cached

## Extending the Reporter

To add new report formats, implement the `ReportGenerator` interface:

```python
class CustomReportGenerator(ReportGenerator):
    def generate(self, report: ScanReport, config: ReportConfiguration) -> None:
        # Implement your custom format generation
        pass
    
    def get_file_extension(self) -> str:
        return ".custom"

# Register with ReportService
service._generators["custom"] = CustomReportGenerator()
```

## Dependencies

The reporter requires:
- `yaml` for YAML output support
- Standard library modules: `json`, `csv`
- Internal modules: scanning models, configuration system

## Testing

See `examples/report_demo.py` for a comprehensive demonstration of all reporter features and usage patterns.
