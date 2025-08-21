# SQLite Database Support

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

```bash
# Show all corrupt files
corrupt-video-inspector database query --corrupt

# Query files from last week
corrupt-video-inspector database query --since "7 days ago"

# High-confidence corrupt files
corrupt-video-inspector database query --corrupt --min-confidence 0.8

# Export corrupt files to CSV
corrupt-video-inspector database query --corrupt --format csv \
  --output corrupt_files.csv

# Show database statistics
corrupt-video-inspector database stats

# Clean up old scans (older than 30 days)
corrupt-video-inspector database cleanup --days 30

# Create database backup
corrupt-video-inspector database backup --backup-path backup.db

# Preview cleanup (dry run)
corrupt-video-inspector database cleanup --days 30 --dry-run
```

## Example Queries

Historical corruption trends (SQLite):

```sql
SELECT
  DATE(started_at, 'unixepoch') AS scan_date,
  corrupt_files,
  total_files,
  ROUND(100.0 * corrupt_files / total_files, 2) AS corruption_rate
FROM scan_summaries
WHERE directory = '/media/movies'
ORDER BY started_at;
```

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
ORDER BY file_size DESC
LIMIT 10;
```

## Integration Benefits

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
