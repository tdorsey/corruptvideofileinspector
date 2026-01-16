# Project-Specific Guidelines

## Architecture, Key Entry Points, and Project-Specific Patterns

### Project Purpose

A comprehensive Python CLI tool for detecting corrupted video files using FFmpeg, with optional Trakt.tv synchronization and Docker containerization support.

### Core Functionality

#### Video Corruption Detection
- Uses FFmpeg to analyze video files
- Multiple scan modes: quick, deep, hybrid
- Detects various corruption types
- Generates detailed reports

#### Trakt.tv Integration
- Optional synchronization with Trakt.tv
- Tracks video health status
- Updates collection status
- Requires API credentials

#### Multiple Interfaces
- CLI interface (primary)
- API server (optional)
- Docker-based workflows

### Architecture Overview

#### Layered Architecture
```
┌─────────────────────────────────────┐
│         CLI Interface               │
│    (cli_handler.py, src/cli/)      │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│       Core Business Logic           │
│         (src/core/)                 │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│    FFmpeg Integration Layer         │
│        (src/ffmpeg/)                │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│    Configuration Management         │
│        (src/config/)                │
└─────────────────────────────────────┘
```

### Key Entry Points

#### CLI Handler
**File**: `cli_handler.py`
- Main entry point for CLI
- Defines Typer application
- Handles command routing
- Loads configuration

**Package Entry Point**: `corrupt-video-inspector` command
- Defined in `pyproject.toml`
- Installs as console script
- Requires configuration file

#### Python Module
**File**: `src/__main__.py`
- Entry point for `python -m src`
- Alternative to installed package
- Useful for development

#### API Server
**File**: `api_server.py`
- Optional HTTP API interface
- RESTful endpoints
- Async/await support
- Separate from CLI

### Module Organization

#### src/cli/
- Command definitions
- CLI-specific logic
- User interaction
- Output formatting for terminal

#### src/core/
- Video scanning logic
- Corruption detection algorithms
- Business rules
- Core domain models

#### src/config/
- Configuration models (Pydantic)
- Configuration loading
- Validation logic
- Default values

#### src/ffmpeg/
- FFmpeg command construction
- Process execution
- Output parsing
- Timeout handling

#### src/output.py
- Output formatting
- Multiple format support (JSON, CSV, YAML)
- File writing
- Result aggregation

#### src/version.py
- Version information
- Poetry dynamic versioning integration
- Version display for CLI

### Dependency Flow

```
cli_handler.py → src/cli/ → src/core/ → src/ffmpeg/
                         ↓
                   src/config/
                         ↓
                   src/output.py
```

### Configuration Requirements

#### Mandatory Configuration
CLI requires a configuration file with these sections:
- **logging**: Log level and file
- **ffmpeg**: Command path and timeouts
- **processing**: Worker configuration
- **output**: Output format and paths
- **scan**: Scan parameters
- **trakt**: Trakt.tv credentials (optional)

#### Configuration Loading
```python
# Priority order:
1. Default values in Pydantic models
2. YAML configuration file
3. Environment variables
4. Docker secrets (in containers)
```

### FFmpeg Integration Patterns

#### Command Execution
```python
# Quick scan
ffmpeg -v error -i video.mp4 -f null -

# Deep scan
ffmpeg -v error -i video.mp4 -f null - -t 0

# With timeout
subprocess.run(cmd, timeout=30, capture_output=True)
```

#### Output Parsing
- Parse stderr for errors
- Detect corruption patterns
- Extract metadata
- Handle various video formats

### Scan Modes

#### Quick Mode
- Fast initial check
- Basic validation
- Short timeout (30 seconds)
- Low resource usage

#### Deep Mode
- Comprehensive analysis
- Full file scan
- Long timeout (30 minutes)
- Higher resource usage

#### Hybrid Mode
- Quick scan first
- Deep scan if issues found
- Balanced approach
- Medium timeout

### Output Formats

#### JSON
```json
{
  "scanned_files": 100,
  "corrupted": 5,
  "healthy": 95,
  "results": [...]
}
```

#### CSV
```csv
file_path,status,scan_mode,duration
video1.mp4,corrupted,quick,2.5
video2.mp4,healthy,quick,1.8
```

#### YAML
```yaml
scanned_files: 100
corrupted: 5
results:
  - file_path: video1.mp4
    status: corrupted
```

### Error Handling Patterns

#### Expected Errors
- File not found → Skip with warning
- FFmpeg not available → Fail with clear message
- Timeout → Mark as timeout, continue
- Invalid config → Fail fast with validation error

#### Unexpected Errors
- Log full traceback
- Attempt graceful degradation
- Provide actionable error messages
- Continue processing other files

### Performance Considerations

#### Parallel Processing
- Use multiprocessing for video scanning
- Configure worker count
- Process pool management
- Progress tracking

#### Resource Management
- Timeout handling prevents hangs
- Memory-efficient file iteration
- Cleanup after processing
- Graceful shutdown

### Testing Patterns

#### Unit Tests
- Mock FFmpeg calls
- Test business logic
- Fast execution
- No external dependencies

#### Integration Tests
- Real FFmpeg execution
- Sample video files
- End-to-end scenarios
- Slower but comprehensive

### Common Development Patterns

#### Adding a New Scan Mode
1. Define mode in config models
2. Implement scan logic in core
3. Add FFmpeg command variant
4. Update CLI help text
5. Add tests
6. Update documentation

#### Adding a New Output Format
1. Add format handler in output.py
2. Update config models
3. Add CLI option
4. Add tests
5. Update documentation

#### Adding a New CLI Command
1. Define command in src/cli/
2. Add to cli_handler.py
3. Implement business logic in core
4. Add tests
5. Update help text

### Docker Integration

#### Development Container
- Full dev environment
- All tools installed
- Source code mounted
- Interactive shell access

#### Production Container
- Minimal dependencies
- Optimized image size
- Multi-stage build
- Production-ready

### Trakt.tv Integration

#### Optional Feature
- Requires API credentials
- Updates collection status
- Tracks video health
- Separate module

#### Configuration
```yaml
trakt:
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  include_statuses: ["healthy"]
```

### Documentation Structure

Detailed module documentation in `docs/`:
- **API.md**: API server documentation
- **CLI.md**: CLI command reference
- **CONFIG.md**: Configuration guide
- **CORE.md**: Core logic documentation
- **FFMPEG.md**: FFmpeg integration details
- **DATABASE.md**: Database integration
- **REPORTER.md**: Reporting functionality
- **UTILS.md**: Utility functions

### Project Conventions

#### Naming
- Snake_case for Python files and functions
- PascalCase for classes
- UPPER_CASE for constants
- Descriptive names over short names

#### File Organization
- Group related functionality
- Keep files focused
- Separate concerns
- Clear module boundaries

#### Type Annotations
- All public APIs must have type hints
- Use typing module for complex types
- Document return types
- Use Optional for nullable values

### Development Workflow

1. **Plan**: Understand requirements
2. **Design**: Architecture and approach
3. **Implement**: Write code with tests
4. **Test**: Run unit and integration tests
5. **Review**: Code review and refinement
6. **Document**: Update docs and comments
7. **Commit**: Conventional commits
8. **Deploy**: Docker or package distribution

### Integration Points

#### External Dependencies
- **FFmpeg**: Core video analysis
- **Trakt.tv API**: Optional sync
- **File system**: Video file access
- **Configuration files**: YAML

#### Internal Dependencies
- **Pydantic**: Configuration validation
- **Typer**: CLI framework
- **pytest**: Testing framework
- **Docker**: Containerization

### Migration and Compatibility

#### Python Version
- Minimum: Python 3.13
- Use modern Python features
- Type hints throughout
- Async/await where beneficial

#### FFmpeg Version
- Tested with FFmpeg 4.x and 5.x
- Command compatibility
- Output parsing variations
- Feature detection

### Extensibility Points

#### Plugin Architecture
- Output formatters
- Scan modes
- Corruption detectors
- Integrations

#### Configuration Extensions
- Custom scan parameters
- Additional metadata
- Integration-specific config
- Environment overrides

### Security Considerations

#### Input Validation
- Validate file paths
- Sanitize user input
- Check file types
- Prevent path traversal

#### Secret Management
- Never commit secrets
- Use environment variables
- Docker secrets support
- Rotation capability

#### Command Injection Prevention
- Parameterized commands
- Input sanitization
- Subprocess safety
- Shell escaping

### Performance Profiling

#### Bottleneck Identification
- FFmpeg execution time
- File I/O operations
- Parallel processing efficiency
- Memory usage patterns

#### Optimization Strategies
- Batch processing
- Caching results
- Parallel execution
- Resource pooling

### Future Directions

#### Planned Features
- Database backend for results
- Web UI for visualization
- Advanced corruption detection
- Cloud storage integration
- Enhanced Trakt.tv features

#### Technical Debt
- Refactor legacy code
- Improve test coverage
- Update dependencies
- Performance optimization

### Project-Specific Troubleshooting

#### FFmpeg Issues
- Verify installation: `ffmpeg -version`
- Check PATH configuration
- Timeout settings
- Format support

#### Video File Issues
- File permissions
- Corrupted source files
- Unsupported formats
- Large file handling

#### Configuration Issues
- YAML syntax errors
- Missing required fields
- Type mismatches
- Invalid values
