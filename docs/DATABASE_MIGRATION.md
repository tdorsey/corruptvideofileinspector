# Database Migration Guide

This guide helps users migrate from file-based scan result storage to the new SQLite database storage system.

## Overview

Starting with version 0.6.0, Corrupt Video Inspector uses SQLite database for persistent storage of scan results. File-based output (JSON, CSV, YAML files) has been replaced with automatic database storage for improved functionality and performance.

## What Changed

### Before (File-Based Storage)
- Scan results saved to individual JSON/CSV/YAML files
- No historical tracking across scans
- Manual file management required
- Limited querying capabilities
- No incremental scanning support

### After (Database Storage)
- All scans automatically stored in SQLite database
- Complete historical tracking
- Automatic cleanup and maintenance
- Advanced querying and filtering
- Incremental scanning support
- Report generation from any previous scan
- Trend analysis and comparisons

## Migration Steps

### 1. Understand the New Workflow

**Old workflow:**
```bash
# Scan and save to file
corrupt-video-inspector scan /media/videos --output results.json

# Generate report from file
corrupt-video-inspector report --input results.json
```

**New workflow:**
```bash
# Scan (automatically stored in database)
corrupt-video-inspector scan /media/videos

# Generate report from latest scan
corrupt-video-inspector report

# Or from specific scan by ID
corrupt-video-inspector report --scan-id 42
```

### 2. Database Location

The database is automatically created at:
```
~/.corrupt-video-inspector/scans.db
```

You can customize this location in your configuration file:

```yaml
database:
  path: "/custom/path/to/scans.db"
```

### 3. Migrate Existing Scan Files (Optional)

If you have existing scan result files and want to import them into the database, follow these steps:

#### Option A: Re-run Scans
The simplest approach is to re-run your scans. Results will be automatically stored in the database:

```bash
# Re-scan your directories
corrupt-video-inspector scan /media/movies
corrupt-video-inspector scan /media/tv
```

#### Option B: Manual Import (Advanced)

If you have many historical scans you want to preserve, you can create a Python script to import them:

```python
from src.database.service import DatabaseService
from src.database.models import ScanDatabaseModel, ScanResultDatabaseModel
import json
from pathlib import Path
from datetime import datetime

def import_json_scan(db_path: Path, json_path: Path):
    """Import scan results from JSON file into database."""
    db = DatabaseService(db_path)
    
    with open(json_path) as f:
        data = json.load(f)
    
    # Create scan record
    scan = ScanDatabaseModel(
        directory=data["directory"],
        mode=data.get("scan_mode", "hybrid"),
        started_at=datetime.fromisoformat(data.get("started_at", datetime.now().isoformat())),
        completed_at=datetime.fromisoformat(data.get("completed_at", datetime.now().isoformat())),
        total_files=data["scan_summary"]["total_files"],
        processed_files=data["scan_summary"]["total_files"],
        corrupt_files=data["scan_summary"]["corrupt_files"],
        healthy_files=data["scan_summary"]["healthy_files"],
        suspicious_files=data["scan_summary"].get("suspicious_files", 0),
        scan_time=data["scan_summary"].get("total_time", 0),
    )
    scan_id = db.store_scan(scan)
    
    # Create result records
    results = []
    for result in data["results"]:
        result_model = ScanResultDatabaseModel(
            scan_id=scan_id,
            filename=result["filename"],
            file_size=result.get("file_size", 0),
            is_corrupt=result["is_corrupt"],
            confidence=result["confidence"],
            file_status=result.get("status", "HEALTHY" if not result["is_corrupt"] else "CORRUPT"),
            scan_mode=result.get("scan_mode", "hybrid"),
            inspection_time=result.get("inspection_time", 0),
        )
        results.append(result_model)
    
    db.store_scan_results(scan_id, results)
    print(f"Imported scan with ID {scan_id}: {len(results)} results")

# Usage
db_path = Path.home() / ".corrupt-video-inspector" / "scans.db"
import_json_scan(db_path, Path("old_results.json"))
```

### 4. Update Your Scripts and Automation

If you have scripts that use the CLI, update them:

**Before:**
```bash
#!/bin/bash
corrupt-video-inspector scan /media/videos --output results.json
corrupt-video-inspector report --input results.json --format html --output report.html
```

**After:**
```bash
#!/bin/bash
# Scan stores results automatically
corrupt-video-inspector scan /media/videos

# Generate report from latest scan
corrupt-video-inspector report --format html --output report.html

# Or reference specific scan
SCAN_ID=$(corrupt-video-inspector database list-scans --limit 1 | tail -n 1 | awk '{print $1}')
corrupt-video-inspector report --scan-id $SCAN_ID --format html --output report.html
```

### 5. Take Advantage of New Features

#### Incremental Scanning

Dramatically speed up repeated scans:

```bash
# First scan (full)
corrupt-video-inspector scan /media/videos

# Subsequent scans (incremental - 50-90% faster)
corrupt-video-inspector scan /media/videos --incremental
```

#### Historical Comparisons

Compare scans to identify new corruption:

```bash
# List recent scans
corrupt-video-inspector database list-scans

# Compare two scans
corrupt-video-inspector report --compare 41 42
```

#### Trend Analysis

Track corruption rates over time:

```bash
# View 30-day trend
corrupt-video-inspector report --trend --directory /media/movies --days 30
```

#### Advanced Queries

Filter and search scan results:

```bash
# Find high-confidence corrupt files
corrupt-video-inspector database query --corrupt --min-confidence 0.8

# Query specific directory
corrupt-video-inspector database query --directory "/media/tv"

# Export to CSV for analysis
corrupt-video-inspector database export --format csv --output analysis.csv
```

## Backward Compatibility

### Configuration Files

Existing configuration files remain compatible. The database is enabled by default.

If you have old configuration with file output settings, they will be ignored:

```yaml
# Old settings (ignored but won't cause errors)
output:
  format: json
  path: results.json

# New database settings (optional)
database:
  path: "~/.corrupt-video-inspector/scans.db"
  auto_cleanup_days: 90
```

### API and Python Integration

If you're using the Python API directly:

**Before:**
```python
from src.cli.handlers import ScanHandler

handler = ScanHandler()
results = handler.scan_directory("/media/videos", output_file="results.json")
```

**After:**
```python
from src.cli.handlers import run_scan
from src.database.service import DatabaseService

# Scan and get results
summary, results = run_scan("/media/videos")

# Results are automatically in database
db = DatabaseService()
recent_scans = db.get_recent_scans(limit=1)
scan_id = recent_scans[0].id

# Query results
stored_results = db.get_scan_results(scan_id)
```

## Performance Considerations

### Database Size Management

The database grows with each scan. Manage size with cleanup:

```bash
# Preview cleanup (dry run)
corrupt-video-inspector database cleanup --days 90 --dry-run

# Clean up scans older than 90 days
corrupt-video-inspector database cleanup --days 90
```

### Automatic Cleanup

Configure automatic cleanup in your config file:

```yaml
database:
  auto_cleanup_days: 90  # Auto-delete scans older than 90 days
```

### Database Location on Fast Storage

For best performance, place database on SSD storage:

```yaml
database:
  path: "/fast/ssd/path/scans.db"
```

### Backup Strategy

Regular backups recommended for large databases:

```bash
# Backup database
corrupt-video-inspector database backup --output /backups/scans-$(date +%Y%m%d).db

# Or use cron for automated backups
0 2 * * 0 corrupt-video-inspector database backup --output /backups/weekly.db
```

## Troubleshooting

### Problem: Database File Growing Too Large

**Solution:** Clean up old scans regularly:

```bash
# Remove scans older than 60 days
corrupt-video-inspector database cleanup --days 60

# Verify size reduction
corrupt-video-inspector database stats
```

### Problem: Missing Scan Results

**Solution:** Check that scans completed successfully:

```bash
# List recent scans
corrupt-video-inspector database list-scans

# Check for specific directory
corrupt-video-inspector database list-scans --directory "/media/videos"
```

### Problem: Slow Queries

**Solution:** Database is automatically optimized with indexes. If still slow:

```bash
# Run vacuum to optimize
corrupt-video-inspector database cleanup --days 0 --dry-run  # triggers vacuum

# Or reduce dataset size
corrupt-video-inspector database cleanup --days 30
```

### Problem: Database Corruption

**Solution:** Restore from backup:

```bash
# Restore from backup
corrupt-video-inspector database restore --input backup.db

# Or start fresh (moves old database to .bak)
mv ~/.corrupt-video-inspector/scans.db ~/.corrupt-video-inspector/scans.db.bak
corrupt-video-inspector scan /media/videos  # Creates new database
```

### Problem: Need Old JSON File Format

**Solution:** Export scan results to JSON:

```bash
# Export latest scan
corrupt-video-inspector database export --format json --output results.json

# Export specific scan
corrupt-video-inspector database export --scan-id 42 --format json --output scan-42.json

# Export only corrupt files
corrupt-video-inspector database export --corrupt-only --format json --output corrupt.json
```

## Docker Usage

### Volume Mapping

When using Docker, ensure database persistence:

```yaml
# docker-compose.yml
services:
  cvi:
    volumes:
      - ./data:/data
    environment:
      - CVI_DB_PATH=/data/scans.db
```

### Backup in Docker

```bash
# Backup database from container
docker compose exec cvi corrupt-video-inspector database backup --output /data/backup.db

# Copy to host
docker compose cp cvi:/data/backup.db ./backup.db
```

## FAQ

### Q: Can I disable database storage?

A: No, database storage is now the core storage mechanism. However, you can export results to files as needed.

### Q: Where are my old JSON files?

A: Old JSON files are preserved. They're just not automatically created anymore. Use the export command to generate files when needed.

### Q: How do I share scan results with others?

A: Use the export command:
```bash
corrupt-video-inspector database export --scan-id 42 --format json --output share.json
```

### Q: Can I use multiple databases?

A: Yes, specify different database paths in your config or via environment variables:
```bash
export CVI_DB_PATH=/path/to/project1.db
corrupt-video-inspector scan /media/project1

export CVI_DB_PATH=/path/to/project2.db
corrupt-video-inspector scan /media/project2
```

### Q: What happens if database is deleted?

A: A new empty database is automatically created on the next scan. Previous scan history is lost unless restored from backup.

### Q: How do I migrate database to another machine?

A: Simply copy the database file:
```bash
# On source machine
corrupt-video-inspector database backup --output scans-backup.db

# Copy to new machine
scp scans-backup.db user@newmachine:/path/to/

# On new machine
mkdir -p ~/.corrupt-video-inspector
cp scans-backup.db ~/.corrupt-video-inspector/scans.db
```

## Getting Help

If you encounter issues during migration:

1. Check the [Database Documentation](DATABASE.md) for detailed feature information
2. Review the [CLI Documentation](CLI.md) for command reference
3. Open an issue on GitHub with details about your migration scenario
4. Include database statistics output: `corrupt-video-inspector database stats`

## Migration Checklist

- [ ] Understand new database-first workflow
- [ ] Update scripts and automation to remove `--output` flags
- [ ] Configure database location if needed (optional)
- [ ] Import historical scans (optional)
- [ ] Set up automatic cleanup policy
- [ ] Configure backup strategy
- [ ] Test incremental scanning
- [ ] Try historical comparison and trend reports
- [ ] Update documentation for your team
- [ ] Remove or archive old JSON files

## Benefits Summary

After migration, you'll benefit from:

- ✅ **50-90% faster** scans with incremental mode
- ✅ **Historical tracking** of all scans
- ✅ **Comparison reports** to identify new corruption
- ✅ **Trend analysis** over time
- ✅ **Advanced querying** capabilities
- ✅ **Better performance** with indexed queries
- ✅ **Simpler workflow** (no file management)
- ✅ **Automatic cleanup** to manage storage
- ✅ **Backup/restore** for data protection

Welcome to the enhanced Corrupt Video Inspector with database-powered features!
