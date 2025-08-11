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

### Fixed
- Updated test expectations to match new Trakt sync default behavior

### Documentation
- Updated CONFIG.md with Trakt configuration documentation
- Updated trakt.md to clarify new default sync behavior
- Added migration instructions for users requiring previous behavior