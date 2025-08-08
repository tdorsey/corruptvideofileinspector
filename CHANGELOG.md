# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING CHANGE**: Removed `--token` CLI option from `trakt list-watchlists` and `trakt view` commands
- Trakt commands now use configuration-based authentication (client_id/client_secret from config file, environment variables, or Docker secrets)

### Added
- Enhanced error messages for missing Trakt credentials with configuration guidance
- Runtime validation for Trakt credentials in CLI commands

### Deprecated
- The `--token` CLI option for Trakt commands has been removed in favor of configuration-based authentication

### Migration Guide
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