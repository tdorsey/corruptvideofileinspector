# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

#### Trakt.tv Authentication Changes
- **BREAKING CHANGE**: Removed `--token` flag from `trakt list-watchlists` and `trakt view` commands
- **NEW**: Config-based authentication using configuration files, environment variables, or Docker secrets
- **NEW**: Added `make secrets-init` command to initialize Trakt credential files
- Authentication is now handled through:
  - Docker secrets: `docker/secrets/trakt_client_id.txt` and `docker/secrets/trakt_client_secret.txt`
  - Configuration file: `trakt.client_id` and `trakt.client_secret` settings
  - Environment variables: `CVI_TRAKT_CLIENT_ID` and `CVI_TRAKT_CLIENT_SECRET`

#### Default Behavior Changes
- **BREAKING CHANGE**: `trakt.include_statuses` default changed from `["healthy", "corrupt", "suspicious"]` to `["healthy"]`
- **RATIONALE**: Safer default behavior to avoid syncing potentially corrupted videos to watchlists
- **OVERRIDE**: Set `include_statuses: ["healthy", "corrupt", "suspicious"]` in config to restore previous behavior

### Updated Documentation
- Updated README.md to reflect config-based Trakt authentication workflow
- Updated docs/CLI.md with new command examples and authentication setup
- Updated docs/trakt.md with comprehensive authentication setup guide
- Updated docs/CONFIG.md with detailed Trakt configuration options and `include_statuses` explanation
- Updated WATCHLIST_USAGE.md examples to remove deprecated `--token` flag usage

### Migration Guide

#### For Trakt.tv Users
1. **Replace token-based commands**:
   ```bash
   # Old (deprecated)
   corrupt-video-inspector trakt list-watchlists --token YOUR_TOKEN
   
   # New (config-based)
   make secrets-init  # Set up credential files
   corrupt-video-inspector trakt list-watchlists
   ```

2. **Set up authentication**:
   ```bash
   # Initialize secret files
   make secrets-init
   
   # Add your credentials
   echo "your-client-id" > docker/secrets/trakt_client_id.txt
   echo "your-client-secret" > docker/secrets/trakt_client_secret.txt
   ```

3. **Update sync behavior if needed**:
   ```yaml
   # In config.yaml, if you want to include all file statuses
   trakt:
     include_statuses: ["healthy", "corrupt", "suspicious"]
   ```

#### Backward Compatibility
- `trakt sync` command behavior remains unchanged
- All existing sync operations continue to work
- Configuration precedence: CLI args > env vars > config file > Docker secrets > defaults