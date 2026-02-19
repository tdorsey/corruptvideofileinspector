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

## Command Groups

The CLI is organized into several command groups:

- **scan**: Video corruption detection and scanning
- **report**: Report generation from scan results
- **database**: Database management and queries
- **trakt**: Trakt.tv watchlist synchronization
- **config**: Configuration management

## Scan Commands

### Main Entry Point (`main.py`)

The main entry point for the CLI application, responsible for:
- Setting up the application context
- Loading configuration
- Initializing the command dispatcher
- Handling global error cases

## Scan Commands

### scan - Scan Videos for Corruption

Scan video files or directories for corruption with automatic database storage.

```bash
# Basic directory scan
corrupt-video-inspector scan /path/to/videos

# Scan with specific mode
corrupt-video-inspector scan /path/to/videos --mode deep

# Incremental scan (skip recently healthy files)
corrupt-video-inspector scan /path/to/videos --incremental

# Incremental with custom time window (14 days)
corrupt-video-inspector scan /path/to/videos --incremental --max-age 14

# Scan with custom worker count
corrupt-video-inspector scan /path/to/videos --max-workers 8

# Quick scan (fast, less thorough)
corrupt-video-inspector scan /path/to/videos --mode quick
```

**Options:**
- `--mode`: Scan mode (quick, deep, hybrid) - default: hybrid
- `--incremental`: Enable incremental scanning (skip recently healthy files)
- `--max-age`: Days to look back for incremental scans (default: 7)
- `--max-workers`: Number of parallel workers (default: CPU count)
- `--timeout`: FFmpeg timeout in seconds (default: 300)

**Scan Modes:**
- **quick**: Fast metadata checks only
- **deep**: Full frame-by-frame analysis (slowest, most thorough)
- **hybrid**: Smart combination of quick and deep (recommended)

**Database Integration:**
All scan results are automatically stored in the SQLite database at `~/.corrupt-video-inspector/scans.db`. No additional flags required.

## Report Commands

### report - Generate Reports from Scan Results

Generate reports from database-stored scan results with multiple output formats.

```bash
# Generate report from latest scan (text format)
corrupt-video-inspector report

# Report from specific scan ID
corrupt-video-inspector report --scan-id 42

# Report as JSON
corrupt-video-inspector report --format json

# Report as CSV
corrupt-video-inspector report --scan-id 42 --format csv --output report.csv

# Compare two scans
corrupt-video-inspector report --compare 41 42

# Compare with JSON output
corrupt-video-inspector report --compare 41 42 --format json

# Trend analysis for directory
corrupt-video-inspector report --trend --directory /media/movies --days 30

# Trend analysis as CSV
corrupt-video-inspector report --trend --directory /media/tv --days 90 --format csv
```

**Options:**
- `--scan-id`: Specific scan ID to report on (default: latest)
- `--format`: Output format (text, json, csv, html, pdf) - default: text
- `--output`: Output file path (default: stdout)
- `--compare`: Compare two scans (format: SCAN_ID1 SCAN_ID2)
- `--trend`: Enable trend analysis mode
- `--directory`: Directory path for trend analysis (required with --trend)
- `--days`: Number of days for trend analysis (default: 30)

**Report Types:**

1. **Single Scan Report** (default): Detailed report of one scan
2. **Comparison Report** (`--compare`): Side-by-side comparison of two scans
3. **Trend Report** (`--trend`): Corruption rate trends over time

## Database Commands

The `database` command group provides comprehensive database management capabilities.

### database query - Query and Filter Results

Search and filter scan results with advanced criteria.

```bash
# Show all corrupt files
corrupt-video-inspector database query --corrupt

# High-confidence corrupt files
corrupt-video-inspector database query --corrupt --min-confidence 0.8

# Query specific directory
corrupt-video-inspector database query --directory "/media/movies"

# Query specific scan
corrupt-video-inspector database query --scan-id 42

# Query with time filter
corrupt-video-inspector database query --since "7 days ago"

# Export to CSV
corrupt-video-inspector database query --corrupt --format csv --output corrupt.csv

# Limit results
corrupt-video-inspector database query --limit 100

# Complex query
corrupt-video-inspector database query \
  --directory "/media/tv" \
  --corrupt \
  --min-confidence 0.7 \
  --limit 50 \
  --format json
```

**Options:**
- `--scan-id`: Filter by specific scan ID
- `--directory`: Filter by directory path
- `--corrupt`: Show only corrupt files
- `--healthy`: Show only healthy files
- `--min-confidence`: Minimum confidence threshold (0.0-1.0)
- `--since`: Show results since date/time
- `--limit`: Maximum number of results
- `--format`: Output format (table, json, csv, yaml)
- `--output`: Write to file instead of stdout

### database stats - Database Statistics

Display comprehensive database statistics.

```bash
# Show all statistics
corrupt-video-inspector database stats
```

**Output includes:**
- Total scans stored
- Total scan results
- Overall corruption rate
- Database file size
- Date range of data
- Average scan duration

### database list-scans - List Recent Scans

Display a table of recent scan operations.

```bash
# List last 20 scans (default)
corrupt-video-inspector database list-scans

# List last 50 scans
corrupt-video-inspector database list-scans --limit 50

# Filter by directory
corrupt-video-inspector database list-scans --directory "/media/movies"

# Combined filters
corrupt-video-inspector database list-scans --limit 10 --directory "/media/tv"
```

**Options:**
- `--limit`: Number of scans to display (default: 20)
- `--directory`: Filter by directory path

### database cleanup - Remove Old Scans

Clean up old scan data to manage database size.

```bash
# Preview cleanup without making changes
corrupt-video-inspector database cleanup --days 30 --dry-run

# Clean up scans older than 30 days
corrupt-video-inspector database cleanup --days 30

# Aggressive cleanup (90 days)
corrupt-video-inspector database cleanup --days 90
```

**Options:**
- `--days`: Remove scans older than N days (required)
- `--dry-run`: Preview changes without modifying database

**Features:**
- Removes scans and results atomically
- Auto-vacuum after cleanup to reclaim disk space
- Shows count of removed records
- Safe dry-run mode for preview

### database backup - Create Backup

Create a complete backup of the database.

```bash
# Auto-generated backup filename
corrupt-video-inspector database backup

# Custom backup location
corrupt-video-inspector database backup --backup-path /backups/scans.db

# Using --output parameter
corrupt-video-inspector database backup --output backup-$(date +%Y%m%d).db
```

**Options:**
- `--backup-path` or `--output`: Backup file path (default: timestamped filename)

### database restore - Restore from Backup

Restore database from a backup file.

```bash
# Restore with confirmation prompt
corrupt-video-inspector database restore --input backup.db

# Force restore without confirmation
corrupt-video-inspector database restore --input backup.db --force
```

**Options:**
- `--input`: Backup file to restore from (required)
- `--force`: Skip confirmation prompt

**Safety:** Current database is automatically backed up before restore.

### database export - Export Results

Export scan results to various formats for external analysis.

```bash
# Export latest scan to JSON
corrupt-video-inspector database export --format json --output latest.json

# Export specific scan to CSV
corrupt-video-inspector database export --scan-id 42 --format csv --output scan-42.csv

# Export corrupt files only
corrupt-video-inspector database export --corrupt-only --format json

# Export to stdout for piping
corrupt-video-inspector database export --format json | jq '.results[] | select(.is_corrupt)'

# Export all data to YAML
corrupt-video-inspector database export --format yaml --output all-scans.yaml
```

**Options:**
- `--scan-id`: Export specific scan (default: latest scan)
- `--format`: Output format (json, csv, yaml)
- `--output`: Output file path (default: stdout)
- `--corrupt-only`: Export only corrupt files

## Trakt Commands

### trakt sync - Sync to Trakt Watchlist

Synchronize healthy video files from database scans to Trakt.tv watchlist.

```bash
# Set up Trakt credentials first
make secrets-init  # Create secret files
# Edit docker/secrets/trakt_client_id.txt and trakt_client_secret.txt

# Sync latest scan (healthy files only)
corrupt-video-inspector trakt sync

# Sync specific scan
corrupt-video-inspector trakt sync --scan-id 42

# Sync with confidence threshold
corrupt-video-inspector trakt sync --min-confidence 0.8

# Include suspicious files too
corrupt-video-inspector trakt sync --include-status healthy --include-status suspicious

# Dry run to preview
corrupt-video-inspector trakt sync --dry-run

# Sync to custom watchlist
corrupt-video-inspector trakt sync --watchlist "my-movies"

# Complex filtering
corrupt-video-inspector trakt sync \
  --scan-id 42 \
  --min-confidence 0.9 \
  --include-status healthy
```

**Options:**
- `--scan-id`: Sync specific scan (default: latest)
- `--min-confidence`: Minimum confidence threshold (0.0-1.0)
- `--include-status`: File status to include (can be repeated: healthy, suspicious, corrupt)
- `--dry-run`: Preview what would be synced without making changes
- `--watchlist`: Target Trakt watchlist name (default: default watchlist)

**Database Integration:**
- Reads scan results directly from database
- Filters by status (default: healthy only)
- Supports confidence thresholding for quality control
- Tracks sync statistics (movies added, shows added, failed, not found)

## Configuration Commands

## Configuration Commands

### init-config - Generate Sample Config

Generate sample configuration file with default settings.

```bash
# Generate YAML config (default)
corrupt-video-inspector init-config --format yaml --output config.yml

# Generate JSON config
corrupt-video-inspector init-config --format json --output config.json

# Output to stdout
corrupt-video-inspector init-config
```

### validate-config - Validate Config File

Validate configuration file syntax and settings.

```bash
# Validate config file
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