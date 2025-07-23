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
- `CVI_EXTENSIONS` - Comma-separated list of extensions (.mp4,.mkv,.avi)

### Secrets
- `CVI_SECRETS_PATH` - Docker secrets directory path

### Examples

```bash
# Set logging to debug and increase workers
export CVI_LOG_LEVEL=DEBUG
export CVI_MAX_WORKERS=8

# Run with environment overrides
python cli_handler.py /videos

# One-time environment override
CVI_LOG_LEVEL=ERROR CVI_MAX_WORKERS=2 python cli_handler.py /videos
```

## Docker Secrets

For secure deployment, sensitive configuration can be provided via Docker secrets:

### Supported Secrets

- `cvi_log_level` - Override logging level
- `cvi_ffmpeg_command` - Override ffmpeg command path
- `cvi_max_workers` - Override worker count

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

### High-Performance Configuration

```yaml
# config.performance.yaml
logging:
  level: "WARNING"  # Minimal logging for performance

processing:
  max_workers: 16  # High parallelism
  default_mode: "quick"  # Fast scans only

ffmpeg:
  quick_timeout: 30  # Shorter timeouts

scan:
  extensions:  # Only most common formats
    - ".mp4"
    - ".mkv"
    - ".avi"
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