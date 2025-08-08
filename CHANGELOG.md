# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING**: `get_all_video_object_files()` now returns `list[VideoFile]` instead of `list[Path]` by default
  - **Migration**: Use the `.path` property to access the file path from VideoFile objects
  - **Backward Compatibility**: Use `as_paths=True` parameter to get the old behavior (deprecated)
  - **Timeline**: The `as_paths` parameter will be removed in v0.6.0

### Added
- Added `as_paths` parameter to `get_all_video_object_files()` for backward compatibility
- Added deprecation warning when `as_paths=True` is used
- Enhanced VideoFile objects returned by `get_all_video_object_files()` with rich metadata

### Migration Guide

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