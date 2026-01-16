# Python Development

## Python-Specific Development Patterns and Project Structure

### Language and Build System
- **Primary language**: Python 3.13 with strict type checking
- **Build system**: pyproject.toml with Poetry-style configuration
- **Code quality**: Black + Ruff + MyPy enforcement via `make check`
- **CLI framework**: Typer with Click integration
- **Core dependency**: FFmpeg for video analysis and corruption detection

### Project Structure
```
src/
├── cli/                           # Command-line interface → docs/CLI.md
├── core/                          # Core business logic → docs/CORE.md
├── config/                        # Configuration management → docs/CONFIG.md
├── ffmpeg/                        # FFmpeg integration → docs/FFMPEG.md
├── output.py                      # Output formatting and file handling
├── version.py                     # Version information
└── __main__.py                    # Main entry point: python -m src
```

### Code Quality Standards
- **⚠️ CRITICAL: `make check` MUST pass successfully before every commit**
- All tests must pass before submitting changes
- Follow existing code style and patterns in the repository

### Python Best Practices
- Use f-strings for string formatting
- Maintain 79-character line length for code (100 for comments/docs per Black config)
- Always use proper type annotations
- Follow PEP 8 style guide
- Use descriptive variable and function names

### Development Commands
```bash
# Install dependencies (NETWORK REQUIRED for local development)
make install-dev                 # 2-5 min, timeout 10+ min
poetry lock --no-update          # Update lock file for changed deps
poetry lock                      # Update all dependencies
poetry check                     # Verify pyproject.toml consistency
poetry show --tree               # Show dependency tree

# Code quality
make format                      # Format with black (30-60 sec)
make lint                        # Lint with ruff (10-30 sec)
make type                        # Type check with mypy (30 sec-2 min)
make check                       # All above combined

# Pre-commit hooks
make pre-commit-install          # Setup hooks (10-30 sec)
make pre-commit-run              # Run hooks manually (1-3 min)
```

### Type Checking
- MyPy is configured for strict type checking
- All public APIs must have type annotations
- Use `typing` module for complex types
- Example:
  ```python
  from typing import List, Optional, Dict
  
  def process_video(path: str, timeout: int = 30) -> Dict[str, str]:
      ...
  ```

### Dependency Management (REQUIRED)
**When adding or updating dependencies:**
- **MUST update `poetry.lock`** after changes to `pyproject.toml`
- Run `poetry lock --no-update` to update only changed dependencies
- Run `poetry lock` to update all dependencies to latest compatible versions
- Always commit `poetry.lock` changes alongside `pyproject.toml` changes
- Verify changes with `poetry check` before committing

### Virtual Environment Management
```bash
# Poetry manages virtual environments automatically
poetry shell                     # Activate virtual environment
poetry env info                  # Show environment information
poetry env list                  # List all environments

# Alternative: Manual PYTHONPATH setup (for testing without install)
export PYTHONPATH=$(pwd)/src
python3 cli_handler.py --config config.yaml --help
```

### CLI Development
- CLI uses Typer framework built on Click
- Main entry point: `cli_handler.py`
- Package entry point: `corrupt-video-inspector` command
- Configuration file is required for CLI operation

### Import Organization
Follow this import order:
1. Standard library imports
2. Third-party imports
3. Local application imports

Example:
```python
import os
import sys
from pathlib import Path

import typer
from pydantic import BaseModel

from config.models import Config
from core.scanner import VideoScanner
```

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Log errors appropriately
- Example:
  ```python
  try:
      result = process_video(path)
  except FileNotFoundError as e:
      logger.error(f"Video file not found: {path}")
      raise
  except Exception as e:
      logger.error(f"Unexpected error processing {path}: {e}")
      raise
  ```

### Application Validation

#### CLI Testing Scenarios
Always manually validate changes by running complete scenarios:

1. **Basic CLI functionality**:
   ```bash
   # Create minimal config file
   cat > /tmp/config.yaml << 'EOF'
   logging:
     level: INFO
     file: /tmp/inspector.log
   ffmpeg:
     command: /usr/bin/ffmpeg
     quick_timeout: 30
     deep_timeout: 1800
   processing:
     max_workers: 8
     default_mode: "quick"
   output:
     default_json: true
     default_output_dir: /tmp/output
     default_filename: "scan_results.json"
   scan:
     recursive: true
     max_workers: 8
     mode: "quick"
     default_input_dir: /tmp/videos
     extensions: [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"]
   trakt:
     client_id: ""
     client_secret: ""
     include_statuses: ["healthy"]
   EOF

   # Test CLI
   export PYTHONPATH=$(pwd)/src
   python3 cli_handler.py --config /tmp/config.yaml --help
   python3 cli_handler.py --config /tmp/config.yaml scan --help
   ```

2. **CLI validation commands**:
   ```bash
   python3 cli_handler.py --config /tmp/config.yaml test-ffmpeg
   python3 cli_handler.py --config /tmp/config.yaml show-config
   ```

3. **Video scanning workflow**:
   ```bash
   mkdir -p test-videos /tmp/output
   python3 cli_handler.py --config /tmp/config.yaml scan --directory test-videos --output /tmp/test-results.json
   ```

### Manual Testing Requirements
- **ALWAYS** run through at least one complete end-to-end scenario after changes
- **CRITICAL**: CLI requires a configuration file to operate
- Test the CLI with actual video files when possible
- Verify configuration files are properly generated and read
- Check that output formats (JSON, CSV, YAML) are properly generated

### Configuration Management
- Use Pydantic models for configuration validation
- Support multiple configuration sources (YAML, environment variables)
- Validate configuration on startup
- Provide clear error messages for invalid configuration

### Logging Best Practices
- Use Python's logging module
- Configure log levels appropriately (INFO, DEBUG, WARNING, ERROR)
- Include context in log messages
- Use structured logging where appropriate
- Example:
  ```python
  import logging
  
  logger = logging.getLogger(__name__)
  logger.info(f"Processing video: {video_path}")
  logger.debug(f"FFmpeg command: {cmd}")
  logger.error(f"Failed to process {video_path}: {error}")
  ```

### Performance Considerations
- Use async/await for I/O-bound operations when beneficial
- Implement parallel processing for video scanning
- Use generators for memory-efficient data processing
- Profile performance-critical sections
- Cache results where appropriate

### FFmpeg Integration
- FFmpeg is a core dependency for video analysis
- Wrapper modules handle FFmpeg command execution
- Timeout handling for long-running operations
- Parse and interpret FFmpeg output for corruption detection
