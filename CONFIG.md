# Configuration Guide

The Corrupt Video Inspector supports flexible configuration through YAML files, environment variables, and Docker secrets with proper precedence handling.

## Configuration Precedence

Settings are applied in this order (highest to lowest precedence):

1. **Environment Variables** - Override everything
2. **Command Line Flags** - Override config file and defaults  
3. **Docker Secrets** - Override config file and defaults
4. **Configuration File** - Override built-in defaults
5. **Built-in Defaults** - Base configuration

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

# Secrets configuration
secrets:
  docker_secrets_path: "/run/secrets"
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

## Troubleshooting

### Configuration Loading Issues

1. **File not found**: Check file path and permissions
2. **YAML syntax errors**: Validate YAML syntax
3. **Type conversion errors**: Check data types match expected values
4. **Permission denied**: Ensure read access to config files

### Checking Current Configuration

The application logs which configuration files were loaded:

```
INFO - Configuration loaded from: ['/app/config.yaml']
```

### Validation

Use the `--verbose` flag to see detailed configuration loading:

```bash
python cli_handler.py --verbose --config my-config.yaml /videos
```