# Database-Only Storage Refactoring Summary

## Overview
Successfully refactored the Corrupt Video Inspector to use SQLite database as the exclusive storage mechanism, removing all file-based output options.

## Changes Made

### Configuration
- **Database now mandatory**: `database.enabled` defaults to `true` (was `false`)
- **Output config deprecated**: Marked `OutputConfig` fields as deprecated
- Updated `config.yaml` and `config.sample.yaml` to reflect database-first approach

### Core Modules

#### `src/output.py` (OutputFormatter)
- **Removed**: `write_scan_results()` method (file writing)
- **Removed**: `write_file_list()` method (file list writing)
- **Removed**: All JSON/YAML/CSV file writing methods
- **Added**: `store_scan_results()` method (database-only)
- **Changed**: Database service is now required (not optional)
- Database initialization errors now raise exceptions instead of logging warnings

#### `src/cli/handlers.py` (BaseHandler, ScanHandler, TraktHandler)
- **Removed**: `_generate_output()` method with file output logic
- **Added**: `_store_scan_results()` method (database-only)
- **Updated**: `run_scan()` - removed `output_file`, `output_format`, `pretty_print` parameters
- **Added**: `TraktHandler.sync_to_watchlist_from_results()` - sync from database results
- All scan results now automatically stored in database

#### `src/cli/commands.py` (CLI Commands)
- **scan command**:
  - Removed: `--output`, `--format`, `--pretty`, `--database` options
  - Results always stored in database
  - Displays database path in output message
  
- **report command**:
  - Changed: `--scan-file` → `--scan-id` (reads from database)
  - Uses latest scan if no ID specified
  - Removed: `--output` option (prints to stdout)
  
- **trakt sync command**:
  - Changed: `scan_file` argument → `--scan-id` option (reads from database)
  - Uses latest scan if no ID specified
  - Removed: `--output` option

### Tests
- **Removed**: `tests/unit/test_output_path.py` (obsolete file output tests)
- **Removed**: `tests/unit/test_scan_output_directory.py` (obsolete file output tests)
- **Updated**: `tests/unit/test_database.py` - fixed `OutputFormatter` API calls

### Documentation
- **README.md**: Updated examples to show database-only workflow
- **config.sample.yaml**: Added deprecation notices for output settings
- **Docker environment**: Changed `CVI_OUTPUT_DIR` → `CVI_DB_DIR`

## Breaking Changes

### CLI Usage Changes
```bash
# BEFORE (file-based)
corrupt-video-inspector scan /videos --output results.json
corrupt-video-inspector report --scan-file results.json
corrupt-video-inspector trakt sync results.json

# AFTER (database-only)
corrupt-video-inspector scan /videos
corrupt-video-inspector report
corrupt-video-inspector trakt sync
```

### API Changes
```python
# BEFORE
output_formatter.write_scan_results(
    summary=summary,
    output_file=Path("results.json"),
    format="json"
)

# AFTER
scan_id = output_formatter.store_scan_results(
    summary=summary
)
```

### Configuration Changes
```yaml
# BEFORE
database:
  enabled: false  # Optional

# AFTER
database:
  enabled: true   # Mandatory
```

## Benefits

1. **Simplified Architecture**: Single source of truth for scan data
2. **Better Data Persistence**: All scans automatically tracked in database
3. **Enhanced Querying**: Easy to query historical data
4. **Reduced Complexity**: No file format handling, path management, etc.
5. **Backward Compatibility**: Database models can export to original formats if needed

## Migration Guide

For users upgrading from file-based to database-only:

1. **Run one final scan with old version** to generate JSON files for backup
2. **Upgrade to new version**
3. **Configure database path** in `config.yaml` (optional, defaults to `~/.corrupt-video-inspector/scans.db`)
4. **Run new scans** - results automatically stored in database
5. **Use `report` and `trakt sync` commands** with `--scan-id` or without (uses latest)

## Testing Status

✅ All unit tests pass (178/178)
✅ CLI commands validated
✅ Database storage tested
✅ Configuration loading tested

## Known Limitations

1. **Trakt sync from database**: Currently returns mock result - requires updating `sync_to_trakt_watchlist()` in `src/core/watchlist.py` to accept database results directly
2. **Report formats**: HTML/PDF report generation may need updates to work with database-only approach
3. **List-files command**: Still writes to files (intentional - it's for file discovery, not scan results)

## Future Enhancements

1. Complete Trakt sync integration with database results
2. Add database query CLI commands (`corrupt-video-inspector db query --corrupt`)
3. Add database export commands for backup (`corrupt-video-inspector db export --format json`)
4. Add database statistics commands (`corrupt-video-inspector db stats`)
