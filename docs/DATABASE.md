# SQLite Database Support

<<<<<<< HEAD
The Corrupt Video Inspector supports optional SQLite database
storage for scan results, providing persistent storage, incremental
scanning, resume capabilities, and richer historical analysis of scan
data. Database storage is optional and does not affect existing CLI
workflows when disabled.

## Features

- Persistent storage of scan runs and per-file results
- Incremental scanning and resume support (skip recently healthy
  files)
- Advanced querying (by corruption status, confidence, dates,
  directory)
- Export results to JSON, CSV, or table formats
- Automatic cleanup and configurable retention policies
- Backup and restore support
- Performance optimizations with appropriate indexes

## Configuration

Add the following section to your `config.yaml` file (example):

```yaml
database:
  enabled: true                    # Enable database storage
  path: "~/.corrupt-video-inspector/scan_results.db"  # DB file
  auto_create: true                # Create DB/tables if missing
  auto_cleanup_days: 30            # Auto-delete scans older than X days
  create_backup: true              # Create backups before schema changes
```

Configuration options:

- `enabled` (boolean) — Enable/disable database storage
  (default: `false`)
- `path` (string) — Path to SQLite database file
  (default: `"scan_results.db"`)
- `auto_create` (boolean) — Create database and tables
  automatically (default: `true`)
- `auto_cleanup_days` (integer) — Number of days to retain scan
  history (0 = disabled)
- `create_backup` (boolean) — Create a backup before schema changes

## Database Schema

The database typically contains two primary tables:

### scan_summaries

Stores metadata about each scan run, for example:

- `id` (PK)
- `directory`
- `scan_mode` (quick, deep, hybrid)
- `total_files`, `processed_files`, `corrupt_files`, `healthy_files`
- `scan_time` (seconds)
- `deep_scans_needed`, `deep_scans_completed`
- `started_at`, `completed_at` (timestamps)
- `was_resumed` (boolean)
- `summary_data` (JSON blob with full scan summary)

### scan_results

Stores individual file scan records, for example:

- `id` (PK)
- `summary_id` (FK to `scan_summaries`)
- `file_path`
- `file_size`
- `is_corrupt` (boolean)
- `confidence` (0.0–1.0)
- `error_message`
- `ffmpeg_output`
- `inspection_time` (seconds)
- `scan_mode`
- `needs_deep_scan`, `deep_scan_completed`
- `timestamp`
- `result_data` (JSON blob with full result data)

Indexes should be created on common query columns
(`directory`, `is_corrupt`, `timestamp`) to keep queries fast.

## CLI Usage

Enable database storage for a particular scan (overrides config):

```bash
# Store scan results in database
corrupt-video-inspector scan /media/videos --store-db

# Disable storing in database for this run
corrupt-video-inspector scan /media/videos --no-store-db

# Incremental scan (skip recently healthy files)
corrupt-video-inspector scan /media/videos --incremental --store-db
```

Database query and management examples:
=======
The Corrupt Video Inspector now includes optional SQLite database support for persistent storage and advanced querying of scan results. This feature addresses the need for historical tracking, trend analysis, and incremental scanning capabilities.

## Features

### 🗄️ Persistent Storage
- Store scan results in SQLite database for long-term retention
- Maintain complete history across multiple scan runs
- Zero-configuration embedded database (no server required)

### 📊 Advanced Querying
- SQL-like filtering and search capabilities
- Query by corruption status, confidence levels, file size, dates
- Custom queries for specific analysis needs
- Export results to JSON, CSV, or table formats

### ⚡ Incremental Scanning
- Skip files that were recently scanned and found healthy
- Focus scanning efforts on files that need attention
- Significant time savings for large media libraries

### 📈 Historical Analysis
- Track corruption trends over time
- Monitor file health changes across scans
- Generate reports spanning multiple time periods
- Identify patterns and problem areas

### 🛠️ Database Management
- Automatic cleanup of old scan records
- Database backup and restore capabilities
- Performance optimization with built-in indexes
- Configurable retention policies

## Configuration

Add database configuration to your `config.yaml`:

```yaml
database:
  enabled: true  # Enable SQLite database storage
  path: "~/.corrupt-video-inspector/scans.db"  # Database file location
  auto_cleanup_days: 30  # Auto-delete scans older than X days (0 = disabled)
  create_backup: true  # Create backups before schema changes
```

## CLI Usage

### Basic Scanning with Database

```bash
# Store scan results in database
corrupt-video-inspector scan /media/videos --database

# Incremental scan (skip recently healthy files)
corrupt-video-inspector scan /media/videos --incremental --database
```

### Database Queries
>>>>>>> e8d7570 (refactor: decouple core modules from CLI interface for better reusability (#160))

```bash
# Show all corrupt files
corrupt-video-inspector database query --corrupt

# Query files from last week
corrupt-video-inspector database query --since "7 days ago"

# High-confidence corrupt files
corrupt-video-inspector database query --corrupt --min-confidence 0.8

# Export corrupt files to CSV
<<<<<<< HEAD
corrupt-video-inspector database query --corrupt --format csv \
  --output corrupt_files.csv

=======
corrupt-video-inspector database query --corrupt --format csv --output corrupt_files.csv

# Query specific directory
corrupt-video-inspector database query --directory "/media/movies"
```

### Database Management

```bash
>>>>>>> e8d7570 (refactor: decouple core modules from CLI interface for better reusability (#160))
# Show database statistics
corrupt-video-inspector database stats

# Clean up old scans (older than 30 days)
corrupt-video-inspector database cleanup --days 30

# Create database backup
corrupt-video-inspector database backup --backup-path backup.db

# Preview cleanup (dry run)
corrupt-video-inspector database cleanup --days 30 --dry-run
```

<<<<<<< HEAD
## Example Queries

Historical corruption trends (SQLite):

```sql
SELECT
  DATE(started_at, 'unixepoch') AS scan_date,
  corrupt_files,
  total_files,
  ROUND(100.0 * corrupt_files / total_files, 2) AS corruption_rate
FROM scan_summaries
=======
## Database Schema

The database uses two main tables:

### Scans Table
Stores metadata about each scan operation:
- Directory scanned, scan mode, timestamps
- File counts (total, processed, corrupt, healthy)
- Performance metrics (scan time, success rate)

### Scan Results Table
Stores individual file scan results:
- File path, size, corruption status
- Confidence levels, inspection time
- Scan mode used, timestamps
- Unique constraint per scan and filename

## Query Examples

### Historical Corruption Trends
```sql
SELECT
    DATE(started_at, 'unixepoch') as scan_date,
    corrupt_files,
    total_files,
    ROUND(100.0 * corrupt_files / total_files, 2) as corruption_rate
FROM scans
>>>>>>> e8d7570 (refactor: decouple core modules from CLI interface for better reusability (#160))
WHERE directory = '/media/movies'
ORDER BY started_at;
```

<<<<<<< HEAD
Files that became corrupt recently:

```sql
SELECT sr.file_path, sr.confidence, s.started_at
FROM scan_results sr
JOIN scan_summaries s ON sr.summary_id = s.id
WHERE sr.is_corrupt = 1
  AND s.started_at > datetime('now', '-7 days');
```

Largest corrupt files:

```sql
SELECT file_path, file_size, confidence
FROM scan_results
WHERE is_corrupt = 1
=======
### Files That Became Corrupt Recently
```sql
SELECT filename, confidence
FROM scan_results sr
JOIN scans s ON sr.scan_id = s.id
WHERE sr.is_corrupt = true
  AND s.started_at > datetime('now', '-7 days');
```

### Largest Corrupt Files
```sql
SELECT filename, file_size, confidence
FROM scan_results
WHERE is_corrupt = true
>>>>>>> e8d7570 (refactor: decouple core modules from CLI interface for better reusability (#160))
ORDER BY file_size DESC
LIMIT 10;
```

## Integration Benefits

<<<<<<< HEAD
- Media server administrators: Monitor library health, identify
  recurring problems, and optimize scan schedules.
- Home media enthusiasts: Maintain a history of collection health and
  quickly find recently corrupted files.
- CI/CD integration: Compare current scan against baseline and fail
  builds if corruption increases.

## Performance Considerations

- Use indexes on frequently queried columns (`directory`, `is_corrupt`,
  `timestamp`)
- Use incremental scans to only process changed or unscanned files
- Enable auto-cleanup to limit database growth
- Use `--limit` on CLI queries for large result sets

## Troubleshooting

Database not found or disabled:

```bash
# Check whether database is enabled in config
corrupt-video-inspector show-config

# Ensure database directory exists
mkdir -p "$(dirname ~/.corrupt-video-inspector/scan_results.db)"
```

Query performance tips:

- Narrow filters (directory, since) and use limits for large datasets
- Run cleanup if database size is unexpectedly large

## Backward Compatibility

- Database storage is entirely optional. Existing output formats
  (JSON, CSV, YAML, text) and CLI commands work the same when
  database features are disabled.
- Database-related dependencies are only required when database
  features are used.

## Best Practices

1. Enable `auto_cleanup_days` to prevent unlimited growth.
2. Regularly backup the database before major operations.
3. Use incremental scans for large libraries.
4. Rely on configured indexes and vacuum/maintenance for performance.

This documentation describes the recommended schema, configuration
options, CLI usage, and operational guidance for the SQLite
integration in Corrupt Video Inspector.
=======
### For Media Server Administrators
- Monitor library health over time
- Identify files that frequently become corrupt
- Track scanning performance and optimize settings
- Generate compliance and health reports

### For Home Media Enthusiasts
- Maintain history of collection health
- Quick queries for recently corrupt files
- Historical trending of storage health
- Efficient incremental scanning

### For CI/CD Integration
- Compare current scan against baseline
- Fail builds if corruption rate increases
- Generate historical reports for monitoring
- API-friendly JSON output for automation

## Performance Considerations

- **Indexed Queries**: Common query patterns are optimized with database indexes
- **Incremental Updates**: Only store new or changed results
- **Automatic Cleanup**: Configurable retention policies prevent database bloat
- **Efficient Storage**: Normalized schema minimizes storage requirements

## Backward Compatibility

Database storage is completely optional and doesn't affect existing functionality:
- All existing output formats (JSON, CSV, YAML, text) remain unchanged
- CLI commands work exactly the same without database configuration
- No dependencies required unless database features are used
- Seamless migration path for existing users

## Best Practices

1. **Enable Auto-Cleanup**: Set `auto_cleanup_days` to prevent unlimited growth
2. **Regular Backups**: Use the backup command before major operations
3. **Incremental Scanning**: Use `--incremental` for large libraries with frequent scans
4. **Index Maintenance**: Database automatically optimizes performance with VACUUM
5. **Query Limits**: Use `--limit` for large result sets to improve performance

## Troubleshooting

### Database Not Found
```bash
# Check if database is enabled in config
corrupt-video-inspector show-config

# Create database directory manually if needed
mkdir -p ~/.corrupt-video-inspector
```

### Performance Issues
```bash
# Check database size and statistics
corrupt-video-inspector database stats

# Clean up old data
corrupt-video-inspector database cleanup --days 30

# The database automatically optimizes itself during cleanup
```

### Query Too Slow
- Use more specific filters (`--directory`, `--since`)
- Add `--limit` to large queries
- Consider enabling auto-cleanup to reduce database size

This SQLite database integration transforms the Corrupt Video Inspector from a one-time scanning tool into a comprehensive video library health monitoring solution with powerful analysis and reporting capabilities.
>>>>>>> e8d7570 (refactor: decouple core modules from CLI interface for better reusability (#160))
