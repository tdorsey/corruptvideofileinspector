# CLI Module Documentation

The CLI module (`src/cli/`) provides the command-line interface for the Corrupt Video Inspector. It handles user interaction, command parsing, and coordinates between different components of the application.

## Architecture

```
src/cli/
├── main.py         # Main CLI entry point
├── commands.py     # Command definitions and argument parsing  
├── handlers.py     # Command execution handlers
└── utils.py        # CLI utility functions
```

## Components

### Main Entry Point (`main.py`)

The main entry point for the CLI application, responsible for:
- Setting up the application context
- Loading configuration
- Initializing the command dispatcher
- Handling global error cases

### Command Definitions (`commands.py`)

Defines the command structure and argument parsing using the Typer framework:
- **Scan commands**: Video file corruption detection
- **Trakt commands**: Watchlist synchronization 
- **Configuration commands**: Config file generation and validation
- **Utility commands**: File listing, version info

### Command Handlers (`handlers.py`)

Implements the business logic for each command:

#### `ScanHandler`
- Coordinates video scanning operations
- Manages scan modes (quick, deep, hybrid)
- Handles progress reporting and resume functionality
- Generates output in multiple formats (JSON, CSV, YAML, text)

#### `TraktHandler`
- Manages Trakt.tv API integration
- Processes scan results for watchlist sync
- Handles authentication and API rate limiting
- Provides interactive mode for ambiguous matches

#### `ConfigHandler`
- Generates sample configuration files
- Validates configuration settings
- Handles different output formats (YAML, JSON)

### CLI Utilities (`utils.py`)

Provides common CLI functionality:
- Progress display and formatting
- User input validation
- Error message formatting
- Output path handling

## Usage Examples

### Basic Scanning

```bash
# Quick scan with default settings
corrupt-video-inspector scan /path/to/videos

# Deep scan with JSON output
corrupt-video-inspector scan --mode deep --output results.json /path/to/videos

# Hybrid scan with custom workers
corrupt-video-inspector scan --mode hybrid --max-workers 8 /path/to/videos
```

### Trakt Integration

```bash
# Set up Trakt credentials first
make secrets-init  # Create secret files
# Edit docker/secrets/trakt_client_id.txt and trakt_client_secret.txt

# Sync scan results to Trakt
corrupt-video-inspector trakt sync results.json

# Interactive mode for manual selection
corrupt-video-inspector trakt sync results.json --interactive

# List available watchlists
corrupt-video-inspector trakt list-watchlists

# View watchlist contents
corrupt-video-inspector trakt view --watchlist "my-movies"
```

### Configuration Management

```bash
# Generate sample config file
corrupt-video-inspector init-config --format yaml --output config.yml

# Validate existing config
corrupt-video-inspector validate-config config.yml
```

## Error Handling

The CLI module implements comprehensive error handling:

- **Validation Errors**: Invalid command arguments or options
- **File System Errors**: Missing directories, permission issues
- **Configuration Errors**: Invalid config files or missing required settings
- **Network Errors**: Trakt API connectivity issues
- **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM

## Configuration

CLI behavior can be customized through:

1. **Command-line arguments**: Override any setting for single execution
2. **Configuration files**: Set defaults in YAML/JSON format
3. **Environment variables**: Use `CVI_` prefixed variables
4. **Docker secrets**: For containerized deployments

## Integration with Core Components

The CLI module serves as the orchestration layer:

- **Scanner**: Delegates video file scanning to `src/core/scanner.py`
- **Inspector**: Uses `src/core/inspector.py` for individual file analysis
- **Reporter**: Leverages `src/core/reporter.py` for output generation
- **Watchlist**: Integrates with `src/core/watchlist.py` for Trakt sync
- **Configuration**: Uses `src/config/` for settings management

## Extension Points

To add new commands:

1. Define command in `commands.py` using Typer decorators
2. Implement handler in `handlers.py` inheriting from `BaseHandler`
3. Add any CLI-specific utilities to `utils.py`
4. Update main dispatcher in `main.py` if needed

## Testing

CLI components are tested through:
- **Unit tests**: Individual function testing in `tests/test_cli_*.py`
- **Integration tests**: End-to-end command execution
- **Mock testing**: External dependency isolation

## API Changes and Migration

### get_all_video_object_files() Return Type Change

**⚠️ Breaking Change in v0.6.0**: The `get_all_video_object_files()` function now returns `list[VideoFile]` instead of `list[Path]`.

#### Migration Required

**Before (v0.5.x and earlier):**
```python
from src.cli.handlers import get_all_video_object_files

# Returned list[Path]
video_paths = get_all_video_object_files("/path/to/videos")
for path in video_paths:
    print(f"Video: {path}")
    print(f"Size: {path.stat().st_size}")
```

**After (v0.6.x and later):**
```python
from src.cli.handlers import get_all_video_object_files

# Now returns list[VideoFile] by default
video_files = get_all_video_object_files("/path/to/videos")
for video_file in video_files:
    print(f"Video: {video_file.path}")
    print(f"Size: {video_file.size}")
    print(f"Duration: {video_file.duration}")
    print(f"Name: {video_file.name}")
```

#### Backward Compatibility (Deprecated)

For temporary compatibility, use the `as_paths=True` parameter (will be removed in v0.6.0):

```python
# Deprecated - will issue warning and be removed in v0.6.0
video_paths = get_all_video_object_files("/path/to/videos", as_paths=True)
```

#### Benefits of New API

- **Rich Metadata**: VideoFile objects provide additional properties like `size`, `duration`, `name`
- **Type Safety**: Better type hints and IDE support
- **Extensibility**: Easier to add new video file properties in the future
- **Consistency**: Aligns with other parts of the API that work with VideoFile objects

## Dependencies

- **Typer**: Modern CLI framework with type hints
- **Rich**: Terminal formatting and progress bars
- **Click**: Underlying CLI infrastructure
- **Core modules**: Business logic components