# Configuration Guide

The Corrupt Video Inspector supports flexible configuration through YAML files, environment variables, and Docker secrets with explicit precedence handling.

## Configuration Precedence

Settings are applied in this order (highest to lowest precedence):

1. **Environment Variables (CVI_*, TRKT_*)** - Override everything
2. **Docker Secrets** - Override config file and defaults  
3. **Configuration File** - Override built-in defaults
4. **Built-in Defaults** - Base configuration

**Important**: Environment variables override Docker secrets for the same setting. Use `--debug` flag with the `show-config` command to see exactly which values are being overridden and from which source.

## Environment Variables

All configuration options can be overridden using environment variables with the `CVI_` prefix for general settings and `TRKT_` prefix for Trakt-specific settings:

### Comprehensive Environment Variable Support

#### Logging Configuration
- `CVI_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `CVI_LOG_FORMAT` - Log message format
- `CVI_LOG_DATE_FORMAT` - Date format for log messages  
- `CVI_LOG_FILE` - Log file path

#### FFmpeg Configuration
- `CVI_FFMPEG_COMMAND` - FFmpeg command path
- `CVI_FFMPEG_QUICK_TIMEOUT` - Quick scan timeout in seconds
- `CVI_FFMPEG_DEEP_TIMEOUT` - Deep scan timeout in seconds

#### Processing Configuration
- `CVI_MAX_WORKERS` - Number of worker threads
- `CVI_DEFAULT_MODE` - Default scan mode (quick, deep, hybrid)

#### Output Configuration
- `CVI_DEFAULT_JSON` - Generate JSON output by default (true/false)
- `CVI_OUTPUT_DIR` - Default output directory
- `CVI_OUTPUT_FILENAME` - Default output filename

#### Scanning Configuration
- `CVI_RECURSIVE` - Scan recursively (true/false)
- `CVI_VIDEO_DIR` - Default input directory to scan
- `CVI_SCAN_MODE` - Scan mode (quick, deep, hybrid)
- `CVI_EXTENSIONS` - Comma-separated list of extensions (.mp4,.mkv,.avi)

#### Trakt Configuration
- `TRKT_CLIENT_ID` - Trakt.tv API client ID
- `TRKT_CLIENT_SECRET` - Trakt.tv API client secret
- `TRKT_DEFAULT_WATCHLIST` - Default watchlist name or slug
- `TRKT_INCLUDE_STATUSES` - Comma-separated list of file statuses (healthy,corrupt,suspicious)

#### Special Configuration
- `CVI_SECRETS_DIR` - Docker secrets directory path (default: /run/secrets)

### Type Conversion

Environment variables are automatically converted to appropriate types:
- **Booleans**: `true`, `1`, `yes`, `on` become True; everything else becomes False
- **Integers**: Converted for timeout and worker count settings
- **Paths**: Converted to Path objects for directory and file settings
- **Lists**: Comma-separated values split into lists
- **Enums**: Converted to appropriate ScanMode and FileStatus enums

### Examples

```bash
# Set logging to debug and increase workers
export CVI_LOG_LEVEL=DEBUG
export CVI_MAX_WORKERS=16

# Configure input and output directories
export CVI_VIDEO_DIR=/path/to/videos
export CVI_OUTPUT_DIR=/path/to/results

# Configure Trakt integration
export TRKT_CLIENT_ID=your_client_id
export TRKT_CLIENT_SECRET=your_client_secret
export TRKT_INCLUDE_STATUSES=healthy,suspicious

# Set scan configuration
export CVI_SCAN_MODE=deep
export CVI_EXTENSIONS=mp4,mkv,avi

# Run with environment overrides
corrupt-video-inspector scan /videos --debug

# One-time environment override
CVI_LOG_LEVEL=ERROR CVI_MAX_WORKERS=2 corrupt-video-inspector scan /videos
```

## Docker Secrets

For secure deployment, sensitive configuration can be provided via Docker secrets. **Environment variables override Docker secrets** for the same setting.

### Supported Secrets

- `trakt_client_id` - Trakt.tv API client ID
- `trakt_client_secret` - Trakt.tv API client secret

### Docker Compose Setup

```yaml
services:
  video:
    # ... other config
    secrets:
      - trakt_client_id
      - trakt_client_secret
      
secrets:
  trakt_client_id:
    file: ./secrets/trakt_client_id.txt
  trakt_client_secret:
    file: ./secrets/trakt_client_secret.txt
```

### Creating Secret Files

```bash
# Create secret files
echo "your_client_id" > secrets/trakt_client_id.txt
echo "your_client_secret" > secrets/trakt_client_secret.txt
```

### Credential Validation

**Important**: Trakt credentials must be provided together - both `client_id` and `client_secret` must be present, or neither. Partial credentials will cause configuration loading to fail with a clear error message.

## Configuration File

### Default Locations

The application automatically looks for configuration files in these locations:

1. `./config.yaml` (current directory)
2. `./config.yml` (current directory)
3. `~/.config/corrupt-video-inspector/config.yaml` (user config)
4. `/etc/corrupt-video-inspector/config.yaml` (system config)

### Custom Configuration File

Use the `--config` flag to specify a custom configuration file:

```bash
python cli_handler.py --config /path/to/my-config.yaml /videos
```

### Configuration Structure

```yaml
# Logging configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"
  file: null  # Optional log file path

# FFmpeg configuration
ffmpeg:
  command: null  # Auto-detect ffmpeg if not specified
  quick_timeout: 60  # Timeout in seconds for quick scans
  deep_timeout: 900  # Timeout in seconds for deep scans

# Processing configuration
processing:
  max_workers: 4  # Number of parallel worker threads
  default_mode: "hybrid"  # Default scan mode: quick, deep, or hybrid

# Output configuration
output:
  default_json: false  # Generate JSON output by default
  default_output_dir: null  # Default output directory
  default_filename: "scan_results.json"

# File scanning configuration
scan:
  recursive: true  # Scan subdirectories recursively by default
  default_input_dir: null  # Default directory to scan (null = require directory argument)
  extensions:  # Video file extensions to scan
    - ".mp4"
    - ".avi"
    - ".mkv"
    # ... more extensions

# Trakt.tv integration configuration
trakt:
  client_id: ""  # Trakt API client ID
  client_secret: ""  # Trakt API client secret  
  default_watchlist: null  # Default watchlist name/slug for sync operations
  include_statuses: ["healthy"]  # File statuses to sync (default: healthy only)

# Secrets configuration
secrets:
  docker_secrets_path: "/run/secrets"
```

## Trakt.tv Configuration

The Trakt.tv integration supports flexible authentication and sync behavior configuration.

### File Status Filtering

The `include_statuses` option controls which files are included in Trakt sync operations:

```yaml
trakt:
  include_statuses: ["healthy"]  # Default: only sync healthy files
  # include_statuses: ["healthy", "suspicious"]  # Include healthy and suspicious
  # include_statuses: ["healthy", "corrupt", "suspicious"]  # Include all files
```

**Default Behavior Change**: The default `include_statuses` is now `["healthy"]` (previously included all statuses). This change was made to:
- Avoid adding potentially corrupted videos to watchlists by default
- Provide safer default behavior for automatic syncing
- Allow explicit configuration for users who want to include other statuses

To override and include all file statuses (legacy behavior):
```yaml
trakt:
  include_statuses: ["healthy", "corrupt", "suspicious"]
```

### Authentication Setup

Trakt credentials can be configured through multiple methods:

#### Method 1: Docker Secrets (Recommended)
```bash
# Initialize secret files
make secrets-init

# Add your credentials
echo "your-client-id" > docker/secrets/trakt_client_id.txt
echo "your-client-secret" > docker/secrets/trakt_client_secret.txt
```

#### Method 2: Configuration File
```yaml
trakt:
  client_id: "your-client-id"
  client_secret: "your-client-secret"
```

#### Method 3: Environment Variables
```bash
export CVI_TRAKT_CLIENT_ID="your-client-id"
export CVI_TRAKT_CLIENT_SECRET="your-client-secret"
```

## Environment Variables

All configuration options can be overridden using environment variables with the `CVI_` prefix:

### Logging
- `CVI_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `CVI_LOG_FORMAT` - Log message format
- `CVI_LOG_FILE` - Log file path

### FFmpeg
- `CVI_FFMPEG_COMMAND` - FFmpeg command path
- `CVI_FFMPEG_QUICK_TIMEOUT` - Quick scan timeout in seconds
- `CVI_FFMPEG_DEEP_TIMEOUT` - Deep scan timeout in seconds

### Processing
- `CVI_MAX_WORKERS` - Number of worker threads
- `CVI_DEFAULT_MODE` - Default scan mode (quick, deep, hybrid)

### Output
- `CVI_DEFAULT_JSON` - Generate JSON output by default (true/false)
- `CVI_OUTPUT_DIR` - Default output directory
- `CVI_OUTPUT_FILENAME` - Default output filename

### Scanning
- `CVI_RECURSIVE` - Scan recursively (true/false)
- `CVI_INPUT_DIR` - Default input directory to scan
- `CVI_EXTENSIONS` - Comma-separated list of extensions (.mp4,.mkv,.avi)

### Trakt.tv Integration
- `CVI_TRAKT_CLIENT_ID` - Trakt API client ID
- `CVI_TRAKT_CLIENT_SECRET` - Trakt API client secret
- `CVI_TRAKT_DEFAULT_WATCHLIST` - Default watchlist name or slug
- `CVI_TRAKT_INCLUDE_STATUSES` - Comma-separated list of statuses (healthy,corrupt,suspicious)
- `CVI_INPUT_DIR` - Default input directory to scan
- `CVI_EXTENSIONS` - Comma-separated list of extensions (.mp4,.mkv,.avi)

### Secrets
- `CVI_SECRETS_PATH` - Docker secrets directory path

### Examples

```bash
# Set logging to debug and increase workers
export CVI_LOG_LEVEL=DEBUG
export CVI_MAX_WORKERS=8

# Configure input and output directories
export CVI_INPUT_DIR=/path/to/videos
export CVI_OUTPUT_DIR=/path/to/results

# Run with environment overrides
python cli_handler.py  # Uses CVI_INPUT_DIR as default

# One-time environment override
CVI_LOG_LEVEL=ERROR CVI_MAX_WORKERS=2 python cli_handler.py /videos
```

## Docker Secrets

For secure deployment, sensitive configuration can be provided via Docker secrets:

### Supported Secrets

- `cvi_log_level` - Override logging level
- `cvi_ffmpeg_command` - Override ffmpeg command path
- `cvi_max_workers` - Override worker count
- `cvi_input_dir` - Override default input directory
- `cvi_output_dir` - Override default output directory

### Docker Compose Setup

```yaml
services:
  video:
    # ... other config
    secrets:
      - cvi_log_level
      - cvi_ffmpeg_command
      
secrets:
  cvi_log_level:
    file: ./secrets/cvi_log_level.txt
  cvi_ffmpeg_command:
    file: ./secrets/cvi_ffmpeg_command.txt
```

### Creating Secret Files

```bash
# Create secret files
echo "DEBUG" > secrets/cvi_log_level.txt
echo "/usr/local/bin/ffmpeg" > secrets/cvi_ffmpeg_command.txt
```

## Docker Configuration

### Basic Docker Usage

```bash
# Use default configuration
docker-compose up

# Use custom configuration file
docker-compose run --rm video python3 cli_handler.py --config /app/my-config.yaml /app/videos
```

### Environment Variables in Docker

```yaml
services:
  video:
    environment:
      - CVI_LOG_LEVEL=DEBUG
      - CVI_MAX_WORKERS=8
      - CVI_DEFAULT_JSON=true
```

### Configuration File Mounting

```yaml
services:
  video:
    volumes:
      - ./my-config.yaml:/app/config.yaml:ro
    command: ["python3", "cli_handler.py", "--config", "/app/config.yaml", "/app/videos"]
```

## Examples

### Development Configuration

```yaml
# config.dev.yaml
logging:
  level: "DEBUG"
  file: "/app/output/debug.log"

processing:
  max_workers: 2
  default_mode: "quick"

output:
  default_json: true
```

### Production Configuration

```yaml
# config.prod.yaml
logging:
  level: "INFO"
  file: "/app/output/inspector.log"

processing:
  max_workers: 8
  default_mode: "hybrid"

ffmpeg:
  quick_timeout: 30
  deep_timeout: 1800

output:
  default_json: true
  default_output_dir: "/app/output"
```

### Configuration with Default Directories

```yaml
# config.autorun.yaml
logging:
  level: "INFO"
  file: "/app/output/inspector.log"

scan:
  default_input_dir: "/app/videos"  # Default input directory
  recursive: true

output:
  default_json: true
  default_output_dir: "/app/output"  # Default output directory
  default_filename: "corruption_scan.json"

processing:
  max_workers: 4
  default_mode: "hybrid"
```

With this configuration, you can run the scanner without specifying directories:

```bash
# Uses default_input_dir and default_output_dir from config
python cli_handler.py --config config.autorun.yaml

# Override just the input directory
python cli_handler.py --config config.autorun.yaml /custom/videos

# Override with environment variables
CVI_INPUT_DIR=/other/videos CVI_OUTPUT_DIR=/other/output python cli_handler.py --config config.autorun.yaml
```

## Debugging Configuration

### Show Effective Configuration

Use the `show-config` command to inspect the current configuration:

```bash
# Show key configuration settings
corrupt-video-inspector show-config

# Show complete configuration in JSON format
corrupt-video-inspector show-config --all-configs

# Show configuration with debug logging to see overrides
corrupt-video-inspector show-config --debug
```

The `--debug` flag will show exactly which configuration values are being overridden and from which source:

```bash
$ CVI_LOG_LEVEL=ERROR CVI_MAX_WORKERS=16 corrupt-video-inspector show-config --debug

Configuration Override Debug Log:
--------------------------------------------------
DEBUG: Config override [environment]: logging.level = ERROR (was: WARNING)
DEBUG: Config override [environment]: processing.max_workers = 16 (was: 8)
--------------------------------------------------

Effective Configuration
==============================
Log Level: ERROR
Max Workers: 16
...
```

### Configuration Loading Order

The configuration merger applies settings in this exact order:

1. **Base configuration** from YAML file
2. **Docker secrets** (if available)
3. **Environment variables** (override secrets)
4. **Post-processing validation** (e.g., Trakt credential validation)

### Testing Configuration

Test different configurations without modifying files:

```bash
# Test with temporary environment variables
CVI_LOG_LEVEL=DEBUG CVI_MAX_WORKERS=4 corrupt-video-inspector show-config

# Test with custom config file
corrupt-video-inspector show-config --config /path/to/test-config.yaml

# Combine custom config with environment overrides
CVI_MAX_WORKERS=16 corrupt-video-inspector show-config --config custom.yaml --debug
```

## Troubleshooting

### Configuration Loading Issues

1. **File not found**: Check file path and permissions
2. **YAML syntax errors**: Validate YAML syntax
3. **Type conversion errors**: Check data types match expected values
4. **Permission denied**: Ensure read access to config files

### Partial Trakt Credentials

If you see this error:
```
ValueError: Partial Trakt credentials detected: client_id provided but client_secret missing
```

**Solution**: Provide both credentials or neither:
- Set both `TRKT_CLIENT_ID` and `TRKT_CLIENT_SECRET`
- Or remove both to disable Trakt integration
- Or provide both via Docker secrets

### Environment Variable Issues

**Problem**: Environment variable not taking effect
**Solution**: 
1. Use `show-config --debug` to verify the variable is being read
2. Check variable name spelling and prefix (`CVI_` or `TRKT_`)
3. Ensure proper type conversion (use lowercase for booleans and enums)

**Problem**: List environment variables not working
**Solution**: Use comma-separated values without spaces:
```bash
# Correct
export CVI_EXTENSIONS=mp4,mkv,avi

# Incorrect  
export CVI_EXTENSIONS="mp4, mkv, avi"  # spaces cause issues
```

### Checking Current Configuration

The application logs which configuration files were loaded:

```
INFO - Configuration loaded from: ['/app/config.yaml']
```

Use the `--debug` flag to see detailed configuration loading:

```bash
corrupt-video-inspector show-config --debug
```

## Migration from Previous Versions

### Removed Features

As of this version, the following legacy features have been **permanently removed**:

- **Legacy path-list return style**: The `as_paths` flag and similar backward compatibility shims are no longer supported
- **Implicit configuration precedence**: All configuration precedence is now explicit and documented

### Breaking Changes

- **Trakt credential validation**: Partial credentials now cause startup failure instead of silent ignore
- **Environment variable precedence**: Environment variables now consistently override Docker secrets
- **Configuration validation**: Invalid configuration values now cause explicit errors instead of being silently ignored