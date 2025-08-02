# Utilities Documentation

The Utilities module (`src/utils/`) provides shared functionality and helper functions used across the Corrupt Video Inspector application. It includes common operations for file handling, output formatting, and general utility functions.

## Architecture

```
src/utils/
├── __init__.py         # Module initialization and exports
├── output.py           # Output formatting and file handling utilities
└── utils.py            # General utility functions (legacy location)
```

Note: There's also a legacy `utils.py` file in the root `src/` directory that may contain additional utilities.

## Components

### Output Utilities (`output.py`)

Handles output formatting, file writing, and result presentation:

#### Key Features:
- **File path handling**: Safe output path generation and validation
- **Format conversion**: Convert between different output formats
- **Progress display**: Terminal output formatting and progress indicators
- **File operations**: Atomic file writing and backup creation
- **Path resolution**: Cross-platform path handling and validation

#### Core Functionality:

```python
class OutputHandler:
    def __init__(self, config: OutputConfig):
        self.default_format = config.default_format
        self.output_dir = config.default_output_dir
        
    def write_output(self, data: Any, format: str, path: Path) -> Path:
        """Write data to file in specified format"""
        # Validate output path
        # Format data according to type
        # Write atomically to prevent corruption
        # Return final path
```

### General Utilities (`utils.py` and legacy `src/utils.py`)

Provides common utility functions used throughout the application:

#### String Processing:
```python
def clean_filename(filename: str) -> str:
    """Clean filename for safe filesystem operations"""
    
def extract_title_from_filename(filename: str) -> str:
    """Extract media title from filename"""
    
def normalize_extension(ext: str) -> str:
    """Normalize file extension format"""
```

#### File System Operations:
```python
def ensure_directory_exists(path: Path) -> None:
    """Create directory if it doesn't exist"""
    
def get_file_size_formatted(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    
def find_video_files(directory: Path, extensions: List[str]) -> List[Path]:
    """Recursively find video files with specified extensions"""
```

#### Data Processing:
```python
def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """Calculate statistical measures (mean, median, std dev)"""
    
def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    
def calculate_success_rate(total: int, successful: int) -> float:
    """Calculate success rate percentage"""
```

## Output Formatting

### Supported Formats

The output utilities support multiple data formats:

#### JSON Output
```python
def format_json_output(data: Dict[str, Any], pretty: bool = True) -> str:
    """Format data as JSON with optional pretty printing"""
    if pretty:
        return json.dumps(data, indent=2, default=str)
    return json.dumps(data, default=str)
```

#### CSV Output
```python
def format_csv_output(results: List[Dict[str, Any]]) -> str:
    """Format scan results as CSV"""
    if not results:
        return ""
    
    fieldnames = results[0].keys()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)
    return output.getvalue()
```

#### YAML Output
```python
def format_yaml_output(data: Dict[str, Any]) -> str:
    """Format data as YAML with proper formatting"""
    return yaml.dump(data, default_flow_style=False, sort_keys=False)
```

#### Text/Summary Output
```python
def format_text_summary(summary: ScanSummary, results: List[ScanResult]) -> str:
    """Generate human-readable text summary"""
    lines = [
        "=" * 60,
        "CORRUPT VIDEO INSPECTOR - SCAN REPORT",
        "=" * 60,
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Files: {summary.total_files}",
        f"Corrupt Files: {summary.corrupt_files}",
        f"Success Rate: {summary.success_rate:.1f}%",
        ""
    ]
    
    # Add detailed results
    for result in results:
        if result.is_corrupt:
            lines.append(f"CORRUPT: {result.filename}")
            lines.append(f"  Confidence: {result.confidence:.1f}%")
            lines.append("")
    
    return "\n".join(lines)
```

### File Path Utilities

Safe and robust file path handling:

```python
def generate_output_path(
    base_dir: Optional[Path] = None,
    filename: Optional[str] = None,
    format: str = "json",
    timestamp: bool = True
) -> Path:
    """Generate safe output file path"""
    
    if base_dir is None:
        base_dir = Path.cwd()
    
    if filename is None:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        if timestamp:
            filename = f"scan_results_{timestamp_str}.{format}"
        else:
            filename = f"scan_results.{format}"
    
    # Ensure proper extension
    if not filename.endswith(f".{format}"):
        filename = f"{filename}.{format}"
    
    # Create full path and ensure directory exists
    full_path = base_dir / filename
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    return full_path

def atomic_write(path: Path, content: str) -> None:
    """Write file atomically to prevent corruption"""
    temp_path = path.with_suffix(path.suffix + '.tmp')
    
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Atomic move
        temp_path.replace(path)
    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise
```

## Progress and Display Utilities

Terminal output formatting for user feedback:

### Progress Indicators
```python
def create_progress_bar(total: int, description: str = "Processing") -> Any:
    """Create Rich progress bar for terminal display"""
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        TimeRemainingColumn(),
    )

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable units"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
```

### Status Formatting
```python
def format_scan_status(result: ScanResult) -> str:
    """Format scan result status for display"""
    if result.is_corrupt:
        confidence = result.confidence * 100
        return f"🔴 CORRUPT ({confidence:.1f}%)"
    else:
        return "🟢 HEALTHY"

def format_processing_summary(
    total: int,
    processed: int,
    corrupt: int,
    elapsed: float
) -> str:
    """Format processing summary for display"""
    rate = processed / elapsed if elapsed > 0 else 0
    success_rate = ((processed - corrupt) / processed * 100) if processed > 0 else 0
    
    return (
        f"Processed {processed}/{total} files "
        f"({rate:.1f} files/sec) - "
        f"{corrupt} corrupt found "
        f"({success_rate:.1f}% healthy)"
    )
```

## Data Validation and Sanitization

Input validation and data sanitization utilities:

```python
def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension against allowed list"""
    ext = Path(filename).suffix.lower()
    return ext in [e.lower() for e in allowed_extensions]

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem operations"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure not empty
    if not filename:
        filename = "untitled"
    
    return filename

def validate_output_path(path: Path) -> None:
    """Validate output path is writable"""
    try:
        # Check if parent directory is writable
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Test write access
        test_file = path.parent / ".write_test"
        test_file.touch()
        test_file.unlink()
        
    except (OSError, PermissionError) as e:
        raise ValueError(f"Output path not writable: {e}")
```

## Configuration Integration

Utilities integrate with the configuration system:

```python
class UtilConfig:
    def __init__(self, config: AppConfig):
        self.output_dir = config.output.default_output_dir
        self.default_format = config.output.default_format
        self.pretty_print = config.output.pretty_print
        self.timestamp_files = config.output.timestamp_files

def get_configured_output_handler(config: AppConfig) -> OutputHandler:
    """Create output handler with configuration"""
    return OutputHandler(UtilConfig(config))
```

## Error Handling

Comprehensive error handling for common utility operations:

```python
class UtilsException(Exception):
    """Base exception for utilities"""
    pass

class OutputError(UtilsException):
    """Error writing output file"""
    pass

class PathValidationError(UtilsException):
    """Invalid file path"""
    pass

class FormatError(UtilsException):
    """Data formatting error"""
    pass
```

## Testing

Utility functions are thoroughly tested:

### Unit Tests
- File path handling and validation
- Data formatting and conversion
- Progress display components
- Error handling and edge cases

### Integration Tests
- End-to-end output generation
- Cross-platform path handling
- Large dataset processing
- Error recovery scenarios

## Performance Considerations

### Optimization Strategies
- **Lazy loading**: Import heavy dependencies only when needed
- **Caching**: Cache formatted strings and compiled patterns
- **Streaming**: Stream large data sets instead of loading into memory
- **Efficient I/O**: Use buffered I/O and atomic operations

### Memory Management
- **Bounded memory**: Limit memory usage for large operations
- **Generator usage**: Use generators for processing large datasets
- **Resource cleanup**: Ensure proper cleanup of resources

## Dependencies

- **Rich**: Terminal formatting and progress bars
- **PyYAML**: YAML format support
- **pathlib**: Cross-platform path handling (standard library)
- **json**: JSON format support (standard library)
- **csv**: CSV format support (standard library)