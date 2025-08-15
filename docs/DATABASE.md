# Database Storage Documentation

## Overview

The Corrupt Video Inspector now supports SQLite database storage for scan results, providing persistent storage, resume capabilities, and better analysis of historical scan data.

## Configuration

Add the following section to your `config.yaml` file:

```yaml
database:
  enabled: true                    # Enable database storage
  path: "scan_results.db"         # Path to SQLite database file  
  auto_create: true               # Automatically create database if it doesn't exist
```

### Configuration Options

- **enabled**: `boolean` - Enable/disable database storage (default: `false`)
- **path**: `string` - Path to SQLite database file (default: `"scan_results.db"`)
- **auto_create**: `boolean` - Automatically create database and tables if they don't exist (default: `true`)

## Database Schema

The database contains two main tables:

### scan_summaries
Stores high-level scan information:
- `id` - Primary key
- `directory` - Directory that was scanned
- `scan_mode` - Scan mode used (quick, deep, hybrid)
- `total_files`, `processed_files`, `corrupt_files`, `healthy_files` - File counts
- `scan_time` - Total scan duration in seconds
- `deep_scans_needed`, `deep_scans_completed` - Deep scan statistics
- `started_at`, `completed_at` - Scan timestamps
- `was_resumed` - Whether scan was resumed from previous session
- `summary_data` - JSON blob with complete summary data

### scan_results
Stores individual file scan results:
- `id` - Primary key
- `summary_id` - Foreign key to scan_summaries
- `file_path` - Path to the video file
- `file_size` - File size in bytes
- `is_corrupt` - Whether file is corrupt
- `error_message` - Human-readable error description
- `ffmpeg_output` - Raw FFmpeg output
- `inspection_time` - Time taken to scan this file
- `scan_mode` - Scan mode used for this file
- `needs_deep_scan`, `deep_scan_completed` - Deep scan flags
- `timestamp` - When the scan was performed
- `confidence` - Corruption confidence level (0.0-1.0)
- `result_data` - JSON blob with complete result data

## CLI Usage

### Enable Database Storage for Scans

Use the `--store-db` flag to enable database storage for a specific scan:

```bash
# Enable database storage (overrides config setting)
corrupt-video-inspector scan /path/to/videos --store-db

# Disable database storage (overrides config setting)  
corrupt-video-inspector scan /path/to/videos --no-store-db
```

### View Scan History

Display previous scan summaries from the database:

```bash
# Show last 10 scans
corrupt-video-inspector db-history

# Show scans for specific directory
corrupt-video-inspector db-history --directory /path/to/videos

# Show more results
corrupt-video-inspector db-history --limit 20

# JSON output format
corrupt-video-inspector db-history --format json
```

### Database Statistics

View database information and statistics:

```bash
corrupt-video-inspector db-stats
```

Example output:
```
Database Statistics:
====================
Database Path: /path/to/scan_results.db
Database Size: 2.45 MB
Total Scans: 15
Completed Scans: 14
Incomplete Scans: 1
Total File Results: 1,245
Corrupt Files Found: 23
Healthy Files: 1,222
```

## Features

### Persistent Storage
- Scan results are permanently stored in SQLite database
- No risk of losing scan data due to file corruption or accidental deletion
- Efficient storage with indexes for fast querying

### Resume Functionality
- Incomplete scans are automatically detected
- Resume from where previous scan left off
- Prevents re-scanning files that were already processed

### Historical Analysis
- Query scan history by directory, date range, or corruption status
- Track corruption trends over time
- Compare scan results across different time periods
- Generate reports from historical data

### Data Integrity
- Foreign key constraints ensure data consistency
- WAL (Write-Ahead Logging) mode for better concurrency
- Automatic transaction management

## Performance Considerations

- Database operations are optimized with appropriate indexes
- Batch inserts for scan results improve performance
- Database size grows with number of scans and results
- Consider periodic cleanup of old scan data if storage space is limited

## Backup and Maintenance

### Backup Database
```bash
# Simple file copy (ensure application is not running)
cp scan_results.db scan_results_backup.db

# SQLite backup command
sqlite3 scan_results.db ".backup scan_results_backup.db"
```

### Database Maintenance
```bash
# Compact database (reclaim unused space)
sqlite3 scan_results.db "VACUUM;"

# Check database integrity
sqlite3 scan_results.db "PRAGMA integrity_check;"
```

## Migration from File-Only Storage

The database storage is additive - existing file-based workflows continue to work unchanged. When database storage is enabled:

1. Scan results are written to both files AND database
2. File output remains the primary interface for compatibility
3. Database provides additional capabilities for analysis and resume

## Troubleshooting

### Database Not Created
- Check that the path is writable
- Verify `auto_create` is set to `true`
- Check file permissions on the parent directory

### Performance Issues
- Monitor database size - large databases may slow queries
- Consider adding custom indexes for specific query patterns
- Check available disk space

### Data Recovery
- Database uses WAL mode which provides better crash recovery
- In case of corruption, SQLite has built-in recovery tools
- Regular backups are recommended for critical data

## Example Queries

For advanced users, direct SQLite queries can provide detailed insights:

```sql
-- Find scans with highest corruption rates
SELECT directory, 
       (corrupt_files * 100.0 / total_files) as corruption_rate,
       total_files
FROM scan_summaries 
WHERE total_files > 0
ORDER BY corruption_rate DESC;

-- Average scan time by scan mode
SELECT scan_mode, 
       AVG(scan_time) as avg_time,
       COUNT(*) as scan_count
FROM scan_summaries 
GROUP BY scan_mode;

-- Most frequently corrupt file types
SELECT substr(file_path, -4) as extension,
       COUNT(*) as corrupt_count
FROM scan_results 
WHERE is_corrupt = 1
GROUP BY extension
ORDER BY corrupt_count DESC;
```