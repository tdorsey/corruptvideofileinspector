# SQLite Database Support

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
# Scan directory and store results in database (automatic)
corrupt-video-inspector scan /media/videos

# Incremental scan (skip recently healthy files)
corrupt-video-inspector scan /media/videos --incremental

# Incremental scan with custom time window (default: 7 days)
corrupt-video-inspector scan /media/videos --incremental --max-age 14
```

### Incremental Scanning

Incremental scanning dramatically speeds up repeated scans of large video libraries by skipping files that were recently scanned and found healthy. This feature queries the database to identify which files can be safely skipped.

**How It Works:**
1. Query database for files scanned within the `--max-age` window (default: 7 days)
2. Filter out files that were found healthy in recent scans
3. Always rescan files that were previously corrupt or suspicious
4. Scan any new files not found in previous scans

**Usage Examples:**

```bash
# Skip files scanned and healthy within last 7 days (default)
corrupt-video-inspector scan /media/videos --incremental

# Custom time window: 14 days
corrupt-video-inspector scan /media/videos --incremental --max-age 14

# Aggressive caching: 30 days
corrupt-video-inspector scan /media/videos --incremental --max-age 30
```

**Performance Benefits:**
- 50-90% time reduction on repeated scans of large libraries
- Focuses scanning effort on files that need attention
- Preserves thorough scanning of problematic files

**When to Use Incremental Scanning:**
- ✅ Regular monitoring of stable video libraries
- ✅ Large collections with infrequent file additions
- ✅ CI/CD pipelines with frequent scan runs
- ❌ First-time scans (no previous data to reference)
- ❌ After significant library reorganization

### Database Commands Reference

#### query - Query and Filter Scan Results

Search and filter scan results with advanced criteria:

```bash
# Show all corrupt files
corrupt-video-inspector database query --corrupt

# Query files from last week
corrupt-video-inspector database query --since "7 days ago"

# High-confidence corrupt files
corrupt-video-inspector database query --corrupt --min-confidence 0.8

# Export corrupt files to CSV
corrupt-video-inspector database query --corrupt --format csv --output corrupt_files.csv

# Query specific directory
corrupt-video-inspector database query --directory "/media/movies"

# Query specific scan by ID
corrupt-video-inspector database query --scan-id 42

# Limit results for large datasets
corrupt-video-inspector database query --limit 100

# Query with multiple filters
corrupt-video-inspector database query --corrupt --min-confidence 0.7 --directory "/media/tv"
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

#### stats - Database Statistics

Display comprehensive database statistics:

```bash
# Show database statistics
corrupt-video-inspector database stats
```

**Output includes:**
- Total number of scans
- Total scan results stored
- Overall corruption rate
- Database file size
- Date range of stored scans
- Average scan duration

#### list-scans - List Recent Scans

Display a table of recent scan operations:

```bash
# List last 20 scans (default)
corrupt-video-inspector database list-scans

# List last 50 scans
corrupt-video-inspector database list-scans --limit 50

# Filter by directory
corrupt-video-inspector database list-scans --directory "/media/movies"

# Combine filters
corrupt-video-inspector database list-scans --limit 10 --directory "/media/tv"
```

**Output columns:**
- Scan ID
- Directory scanned
- Start time
- Total files processed
- Corrupt files found
- Scan mode (quick/deep/hybrid)
- Scan duration

**Options:**
- `--limit`: Number of scans to display (default: 20)
- `--directory`: Filter by directory path

#### cleanup - Remove Old Scans

Clean up old scan data to manage database size:

```bash
# Preview cleanup (dry run)
corrupt-video-inspector database cleanup --days 30 --dry-run

# Clean up scans older than 30 days
corrupt-video-inspector database cleanup --days 30

# Aggressive cleanup (90 days)
corrupt-video-inspector database cleanup --days 90
```

**Features:**
- Removes scans and associated results atomically
- Respects foreign key constraints
- Displays count of affected records
- Auto-vacuum after cleanup to reclaim space
- Dry-run mode for safe preview

**Options:**
- `--days`: Remove scans older than N days (required)
- `--dry-run`: Preview changes without modifying database

#### backup - Create Database Backup

Create a complete backup of the database:

```bash
# Backup to default location with timestamp
corrupt-video-inspector database backup

# Backup to specific file
corrupt-video-inspector database backup --backup-path /backups/scans-$(date +%Y%m%d).db

# Backup with custom output
corrupt-video-inspector database backup --output backup.db
```

**Features:**
- Creates complete database copy
- Verifies backup integrity
- Shows backup size and location
- Atomic operation (backup fails if disk space insufficient)

**Options:**
- `--backup-path` or `--output`: Backup file path (default: auto-generated with timestamp)

#### restore - Restore from Backup

Restore database from a backup file:

```bash
# Restore from backup (with confirmation prompt)
corrupt-video-inspector database restore --input backup.db

# Force restore without confirmation
corrupt-video-inspector database restore --input backup.db --force
```

**Features:**
- Validates backup file before restore
- Creates backup of current database before restore
- Confirmation prompt (unless `--force` used)
- Displays statistics after restore
- Verifies data integrity post-restore

**Options:**
- `--input`: Backup file to restore from (required)
- `--force`: Skip confirmation prompt

**Safety Note:** Current database is automatically backed up before restore operation.

#### export - Export Scan Results

Export scan results to various formats for external analysis:

```bash
# Export latest scan to JSON
corrupt-video-inspector database export --format json --output latest.json

# Export specific scan to CSV
corrupt-video-inspector database export --scan-id 42 --format csv --output scan-42.csv

# Export corrupt files only
corrupt-video-inspector database export --corrupt-only --format json --output corrupt.json

# Export all scans to YAML
corrupt-video-inspector database export --format yaml --output all-scans.yaml

# Export to stdout for piping
corrupt-video-inspector database export --format json | jq '.results[] | select(.is_corrupt)'
```

**Features:**
- Multiple format support (JSON, CSV, YAML)
- Filter by scan ID or export all
- Corrupt-only filtering
- Stdout or file output
- Supports large exports (100k+ records)

**Options:**
- `--scan-id`: Export specific scan (default: latest)
- `--format`: Output format (json, csv, yaml)
- `--output`: Output file (default: stdout)
- `--corrupt-only`: Export only corrupt files

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
WHERE directory = '/media/movies'
ORDER BY started_at;
```

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
ORDER BY file_size DESC
LIMIT 10;
```

## Integration Benefits

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