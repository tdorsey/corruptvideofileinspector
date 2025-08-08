# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

#### ⚠️ **BREAKING CHANGE**: Trakt sync default behavior

- **Changed default `include_statuses` for Trakt sync from `[CORRUPT, SUSPICIOUS]` to `[HEALTHY]`**
  
  **Impact**: Trakt sync operations will now sync healthy video files by default instead of corrupt/suspicious files.
  
  **Rationale**: 
  - Users typically want to sync their working video files to Trakt watchlists
  - Syncing corrupt files to a watchlist provides limited value
  - Previous default was counterintuitive for most use cases
  
  **Migration**: To restore previous behavior, explicitly configure:
  ```yaml
  trakt:
    include_statuses: [CORRUPT, SUSPICIOUS]
  ```
  
  Or use CLI flag:
  ```bash
  corrupt-video-inspector trakt sync results.json --include-statuses CORRUPT SUSPICIOUS
  ```

- **BREAKING CHANGE**: Removed `--token` CLI option from `trakt list-watchlists` and `trakt view` commands
- Trakt commands now use configuration-based authentication (client_id/client_secret from config file, environment variables, or Docker secrets)

- **BREAKING**: `get_all_video_object_files()` now returns `list[VideoFile]` instead of `list[Path]` by default
  - **Migration**: Use the `.path` property to access the file path from VideoFile objects
  - **Backward Compatibility**: Use `as_paths=True` parameter to get the old behavior (deprecated)
  - **Timeline**: The `as_paths` parameter will be removed in v0.6.0

### Added
- Enhanced error messages for missing Trakt credentials with configuration guidance
- Runtime validation for Trakt credentials in CLI commands
- Added `as_paths` parameter to `get_all_video_object_files()` for backward compatibility
- Added deprecation warning when `as_paths=True` is used
- Enhanced VideoFile objects returned by `get_all_video_object_files()` with rich metadata
- Initial changelog setup with automated generation from conventional commits

### Fixed
- Updated test expectations to match new Trakt sync default behavior

### Deprecated
- The `--token` CLI option for Trakt commands has been removed in favor of configuration-based authentication

### Documentation
- Updated CONFIG.md with Trakt configuration documentation
- Updated trakt.md to clarify new default sync behavior
- Added migration instructions for users requiring previous behavior

### Migration Guide

#### Trakt Authentication Changes

**For users who previously used `--token` with Trakt commands:**

**Before:**
```bash
corrupt-video-inspector trakt list-watchlists --token YOUR_TOKEN
corrupt-video-inspector trakt view --token YOUR_TOKEN --watchlist "my-list"
```

**After:**
1. Get your Trakt API credentials from https://trakt.tv/oauth/applications
2. Configure them using one of these methods:

**Option 1: Configuration file (config.yaml)**
```yaml
trakt:
  client_id: your_client_id
  client_secret: your_client_secret
```

**Option 2: Environment variables**
```bash
export CVI_TRAKT_CLIENT_ID=your_client_id
export CVI_TRAKT_CLIENT_SECRET=your_client_secret
```

**Option 3: Docker secrets** (for containerized deployments)
```bash
echo "your_client_id" > docker/secrets/trakt_client_id.txt
echo "your_client_secret" > docker/secrets/trakt_client_secret.txt
```

3. Run commands without `--token`:
```bash
corrupt-video-inspector trakt list-watchlists
corrupt-video-inspector trakt view --watchlist "my-list"
```

**Note:** This change improves security by removing the need to pass tokens as command-line arguments and provides a more consistent configuration experience across all application features.

#### get_all_video_object_files API Change

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

**Temporary compatibility (deprecated, will be removed in v0.6.0):**
```python
# Use as_paths=True for old behavior (with deprecation warning)
video_paths = get_all_video_object_files("/path/to/videos", as_paths=True)
```

## Previous Versions

*No previous changelog entries - this is the first version with a changelog.*
