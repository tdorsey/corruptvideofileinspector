# Docker Trakt Integration

This document describes how to use the Trakt container in the Docker Compose setup for syncing video scan results to your Trakt.tv watchlist.

## Overview

The Trakt container extends the main application container and provides dedicated functionality for syncing video scan results to Trakt.tv watchlists. It runs the `trakt sync` command to process JSON scan results and add movies/shows to your watchlist.

## Setup

### 1. Environment Variables

Create a `.env` file in the `docker/` directory (copy from `.env.example`):

```bash
# Required for Trakt functionality
TRAKT_CLIENT_ID=your_api_client_id

# Required for volume mounts
CVI_VIDEO_DIR=/path/to/your/videos
CVI_OUTPUT_DIR=/path/to/output
CVI_LOG_DIR=/path/to/logs
```

### 2. Get Trakt API Credentials

1. Visit [Trakt.tv API Apps](https://trakt.tv/oauth/applications)
2. Create a new application or use an existing one
3. Note your client ID and client secret
4. Update the Docker secrets files in `docker/secrets/`:
   - `trakt_client_id.txt` - Your client ID
   - `trakt_client_secret.txt` - Your client secret

## Usage

### Production Mode

The Trakt service uses Docker profiles to avoid running by default. Enable it explicitly:

```bash
# Run scan and sync to Trakt
docker-compose --profile trakt up scan trakt

# Run all services including Trakt
docker-compose --profile trakt up
```

### Development Mode

For development with interactive Trakt sync:

```bash
# Development mode with Trakt (interactive)
docker-compose -f docker-compose.dev.yml --profile trakt up app trakt-dev
```

## Container Configuration

### Production Container (`trakt`)

```yaml
trakt:
  extends: scan
  container_name: trakt-sync
  command:
    - trakt
    - sync
    - /app/output/scan_results.json
    - --token
    - ${TRAKT_ACCESS_TOKEN}
  depends_on:
    - scan
  profiles:
    - trakt
```

**Features:**
- Extends the main scan container
- Automatically syncs results after scan completes
- Uses environment variables for authentication
- Only runs when `trakt` profile is enabled

### Development Container (`trakt-dev`)

```yaml
trakt-dev:
  extends: app
  container_name: cvi-trakt-dev
  command:
    - trakt
    - sync
    - /app/output/scan_results.json
    - --token
    - ${TRAKT_ACCESS_TOKEN}
    - --interactive
  profiles:
    - trakt
```

**Features:**
- Includes `--interactive` flag for manual selection
- Hot-reloaded source code from volumes
- Better for development and testing

## Workflow Examples

### Basic Scan and Sync

```bash
# 1. Set environment variables
export TRAKT_CLIENT_ID="your_client_id"
export CVI_VIDEO_DIR="/path/to/videos"
export CVI_OUTPUT_DIR="/path/to/output"
export CVI_LOG_DIR="/path/to/logs"

# 2. Ensure secrets are set up
echo "your_client_id" > docker/secrets/trakt_client_id.txt
echo "your_client_secret" > docker/secrets/trakt_client_secret.txt

# 3. Run scan and sync
docker-compose --profile trakt up scan trakt
```

### Complete Workflow

```bash
# Run scan, generate report, and sync to Trakt
docker-compose --profile trakt up scan report trakt
```

### Development Workflow

```bash
# Start development environment with Trakt
docker-compose -f docker-compose.dev.yml --profile trakt up app trakt-dev

# The trakt-dev container will wait for scan results and provide interactive sync
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TRAKT_CLIENT_ID` | No | API client ID (can be set in config or secrets) |
| `CVI_VIDEO_DIR` | Yes | Path to video directory for scanning |
| `CVI_OUTPUT_DIR` | Yes | Path for output files |
| `CVI_LOG_DIR` | Yes | Path for log files |

## Command Options

The Trakt container supports all standard `trakt sync` options:

- `--interactive`: Enable interactive selection of search results
- `--output`: Save sync results to file
- `--dry-run`: Show what would be synced without actually syncing
- `--verbose`: Enable detailed logging

## Security

- Never commit your access token to version control
- Use environment variables or Docker secrets for sensitive data
- Regularly rotate your API tokens
- The `.env` file is in `.gitignore` by default

## Troubleshooting

### Common Issues

1. **"TRAKT_CLIENT_ID environment variable not set"**
   - Ensure you've set the client ID in your `.env` file or Docker secrets

2. **"No scan results found"**
   - Make sure the scan container has completed successfully
   - Check that scan results exist in the output volume

3. **"Authentication failed"**
   - Verify your client ID and secret are correct in Docker secrets
   - Check your Trakt application settings

### Debug Mode

Enable verbose logging by modifying the command:

```yaml
command:
  - trakt
  - sync
  - /app/output/scan_results.json
  - --token
  - ${TRAKT_ACCESS_TOKEN}
  - --verbose
```

## Volume Mounts

The Trakt container shares the same volumes as the main application:

- `output:/app/output` - Scan results and sync output
- `logs:/app/logs` - Application logs
- `config.yaml` - Application configuration

## Dependencies

The Trakt container depends on the scan container to complete first, ensuring scan results are available before attempting to sync.

## Integration with CI/CD

For automated workflows, you can run the complete pipeline:

```bash
# Complete automated workflow
docker-compose --profile trakt up --abort-on-container-exit scan trakt
```

This will:
1. Scan videos for corruption
2. Automatically sync healthy files to Trakt
3. Exit when both operations complete
