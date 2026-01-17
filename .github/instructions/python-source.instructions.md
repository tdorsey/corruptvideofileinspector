---
applyTo: "src/**/*.py"
---

# Python Source Code Instructions

When writing or modifying Python source code in this repository, follow these strict guidelines:

## Code Quality Standards (CRITICAL)

**⚠️ MUST RUN BEFORE EVERY COMMIT:**
```bash
make check  # Runs black, ruff, and mypy - MUST PASS
```

## Required Code Standards

### 1. Type Annotations (REQUIRED)
All functions must have complete type annotations:

```python
from typing import Dict, List, Optional
from pathlib import Path

def scan_directory(
    directory: Path,
    extensions: List[str],
    recursive: bool = True
) -> Dict[str, Any]:
    """Scan directory for video files."""
    pass
```

### 2. Line Length (79 Characters)
```python
# ❌ Too long
def process_video_file(video_path: str, output_dir: str, enable_deep_scan: bool = False) -> Dict[str, Any]:

# ✅ Correct
def process_video_file(
    video_path: str, output_dir: str, enable_deep_scan: bool = False
) -> Dict[str, Any]:
```

### 3. String Formatting (F-strings)
```python
# ❌ Old style
message = "Processing file: {}".format(filename)

# ✅ F-strings
message = f"Processing file: {filename}"
```

### 4. Import Organization
```python
# Standard library
import sys
from pathlib import Path

# Third-party
import typer
from pydantic import BaseModel

# Local
from src.core.scanner import VideoScanner
```

### 5. Docstrings (Required for Public APIs)
```python
def scan_directory(directory: Path) -> List[Path]:
    """Scan directory for video files.
    
    Args:
        directory: Directory path to scan
        
    Returns:
        List of video file paths
        
    Raises:
        ValueError: If directory is invalid
    """
    pass
```

## Security Requirements

### 1. No shell=True in subprocess
```python
# ❌ DANGEROUS - Command injection risk
subprocess.run(f"ffmpeg -i {video_path}", shell=True)

# ✅ SAFE - Parameterized command
subprocess.run(["ffmpeg", "-i", str(video_path)], shell=False)
```

### 2. Path Validation
```python
from pathlib import Path

def read_file(file_path: Path) -> str:
    """Read file with path validation."""
    # Validate path is within expected directory
    resolved = file_path.resolve()
    if not resolved.is_relative_to(expected_base_dir):
        raise ValueError("Invalid file path")
    return resolved.read_text()
```

### 3. No Hardcoded Secrets
```python
# ❌ NEVER hardcode secrets
API_KEY = "abc123def456"

# ✅ Use environment variables or Docker secrets
import os

def get_api_key() -> str:
    """Get API key from environment or secrets."""
    secret_path = "/run/secrets/api_key"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    return os.getenv("API_KEY", "")
```

## Error Handling Patterns

### Custom Exceptions
```python
class VideoScannerError(Exception):
    """Base exception for video scanner errors."""
    pass

class InvalidDirectoryError(VideoScannerError):
    """Raised when directory is invalid."""
    pass
```

### Proper Error Handling
```python
import logging

logger = logging.getLogger(__name__)

def process_video(video_path: Path) -> Dict[str, Any]:
    """Process video file with proper error handling."""
    try:
        result = check_video_integrity(video_path)
        logger.info(f"Processed {video_path.name}")
        return result
    except FileNotFoundError:
        logger.error(f"Video not found: {video_path}")
        return {"error": "Video file not found"}
    except Exception as e:
        logger.exception("Unexpected error during video processing")
        return {"error": "Internal error occurred"}
```

## Common Patterns

### CLI Commands (Typer)
```python
import typer
from pathlib import Path

app = typer.Typer()

@app.command()
def scan(
    directory: Path = typer.Argument(..., help="Directory to scan"),
    mode: str = typer.Option("quick", help="Scan mode"),
) -> None:
    """Scan directory for corrupted videos."""
    try:
        scanner = VideoScanner(directory)
        results = scanner.scan(mode=mode)
        typer.echo(f"Scanned {len(results)} files")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
```

### Configuration (Pydantic)
```python
from pydantic import BaseModel, Field, field_validator

class ScanConfig(BaseModel):
    """Configuration for video scanning."""
    
    input_dir: Path = Field(..., description="Input directory")
    max_workers: int = Field(default=4, ge=1, le=16)
    
    @field_validator("input_dir")
    @classmethod
    def validate_directory(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Directory does not exist: {v}")
        return v.resolve()
```

## Repository Structure Context

```
src/
├── cli/          # CLI commands (Typer framework)
├── core/         # Business logic (scanner, processor)
├── config/       # Configuration management (Pydantic)
├── ffmpeg/       # FFmpeg integration (subprocess)
├── trakt/        # Trakt.tv API integration
└── output.py     # Output formatting (JSON, CSV, YAML)
```

## Quality Checklist

Before committing, verify:
- [ ] All functions have type annotations
- [ ] Public functions have docstrings
- [ ] Lines are ≤79 characters
- [ ] Using f-strings for formatting
- [ ] Imports properly organized
- [ ] No hardcoded secrets
- [ ] No shell=True in subprocess
- [ ] Error handling implemented
- [ ] `make check` passes
- [ ] MyPy compliant
- [ ] Black formatted
- [ ] Ruff linting passed

## Running Quality Checks

```bash
make check       # Format, lint, and type check (REQUIRED)
make format      # Black formatting only
make lint        # Ruff linting only
make type        # MyPy type checking only
```

## Common Mistakes to Avoid

❌ Missing type annotations
❌ Lines over 79 characters
❌ Using format() or % instead of f-strings
❌ shell=True in subprocess calls
❌ Hardcoded paths or credentials
❌ Missing error handling
❌ No docstrings for public APIs
❌ Incorrect import organization
