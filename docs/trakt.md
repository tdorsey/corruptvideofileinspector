# Trakt.tv Integration Guide

This comprehensive guide covers everything you need to know about integrating the Corrupt Video Inspector with Trakt.tv, including authentication setup, watchlist management, and advanced usage scenarios.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Authentication Setup](#authentication-setup)
4. [Basic Usage](#basic-usage)
5. [Watchlist Management](#watchlist-management)
6. [Advanced Features](#advanced-features)
7. [Workflow Examples](#workflow-examples)
8. [Troubleshooting](#troubleshooting)

## Overview

The Trakt.tv integration allows you to automatically sync your video collection to your Trakt.tv watchlists by processing JSON scan results from the video inspector and using intelligent filename parsing. The integration supports multiple watchlists, interactive selection, and various authentication methods.

## Prerequisites

1. **Trakt.tv Account**: You need a free account at [trakt.tv](https://trakt.tv)
2. **API Application**: Create a Trakt.tv API application to get your credentials
3. **JSON Scan Results**: Video inspection results in JSON format from the video scanner

## Authentication Setup

### Step 1: Create a Trakt API Application

1. Visit [Trakt OAuth Applications](https://trakt.tv/oauth/applications)
2. Log in to your Trakt account
3. Click "New Application"
4. Fill out the form:
   - **Name**: Choose a name (e.g., "Corrupt Video Inspector")
   - **Description**: Brief description of your app
   - **Redirect URI**: For OAuth auth, you can use `urn:ietf:wg:oauth:2.0:oob`
   - **Permissions**: Select what you need (at minimum: scopes for reading and writing to watchlists)

5. After creating the application, note down:
   - **Client ID**: A long alphanumeric string
   - **Client Secret**: Another long alphanumeric string

### Step 2: Configure Your Credentials

#### Option 1: Docker Secrets (Recommended)

```bash
# Initialize secret files
make secrets-init

# Add your credentials to the secret files
echo "YOUR_CLIENT_ID_HERE" > docker/secrets/trakt_client_id.txt
echo "YOUR_CLIENT_SECRET_HERE" > docker/secrets/trakt_client_secret.txt
```

#### Option 2: Configuration File

```yaml
# config.yaml
trakt:
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  default_watchlist: "my-default-list"  # Optional
  include_statuses: ["healthy"]  # Default: only sync healthy files
```

#### Option 3: Environment Variables

```bash
export CVI_TRAKT_CLIENT_ID="your-client-id"
export CVI_TRAKT_CLIENT_SECRET="your-client-secret"
```

### Step 3: Authenticate with Trakt

The project includes built-in Trakt authentication commands in the main CLI:

#### OAuth Authentication (Recommended)

```bash
# Run the authentication setup with OAuth method
corrupt-video-inspector trakt auth --username=YOUR_TRAKT_USERNAME --store

# This will:
# 1. Validate your client credentials
# 2. Display an authorization URL to visit
# 3. Prompt you to enter the authorization code
# 4. Test the authentication
# 5. Store credentials in ~/.pytrakt.json for future use
```

#### Authentication without storing credentials

```bash
# Run authentication without storing credentials
corrupt-video-inspector trakt auth --username=YOUR_TRAKT_USERNAME --no-store

# You'll need to re-authenticate each time you use Trakt features
```

#### CLI Authentication Options

- `--username`: Your Trakt username (required)
- `--store/--no-store`: Whether to save credentials to `~/.pytrakt.json`
- `--config`: Path to config file (default: `config.yaml`)
- `--test-only`: Only test existing authentication without re-authenticating

### Step 4: Test Your Authentication

After setting up authentication, test it:

```bash
# Test existing authentication
corrupt-video-inspector trakt auth --test-only

# Should show: "✅ Already authenticated! No setup needed."
```

## Basic Usage

### Basic Sync Command

```bash
# Sync scan results to your main Trakt watchlist
corrupt-video-inspector trakt sync scan_results.json
```

### Enhanced Sync with Watchlist Selection

```bash
# Sync to main watchlist (default behavior)
corrupt-video-inspector trakt sync results.json

# Sync to a specific custom list
corrupt-video-inspector trakt sync results.json --watchlist "my-movies"

# Interactive sync to a custom list
corrupt-video-inspector trakt sync results.json --watchlist "to-watch" --interactive
```

## Watchlist Management

### List Available Watchlists

```bash
# List watchlists in table format
corrupt-video-inspector trakt list-watchlists

# List watchlists in JSON format
corrupt-video-inspector trakt list-watchlists --format json

# Save watchlist info to file
corrupt-video-inspector trakt list-watchlists --output watchlists.json
```

### View Watchlist Contents

```bash
# View main watchlist
corrupt-video-inspector trakt view

# View a specific custom list
corrupt-video-inspector trakt view --watchlist "my-movies"

# View watchlist in JSON format
corrupt-video-inspector trakt view --watchlist "favorites" --format json

# Save watchlist contents to file
corrupt-video-inspector trakt view --watchlist "to-watch" --output contents.json
```

### Command Options

#### For `trakt sync`:
- `--watchlist` / `-w`: Target watchlist name or slug (default: main watchlist)
- `--interactive` / `-i`: Enable interactive selection of search results
- `--dry-run`: Show what would be synced without actually syncing
- `--include-status`: File statuses to include (default: healthy only)
- `--output` / `-o`: Save sync results to JSON file

#### For `trakt list-watchlists`:
- `--format`: Output format (table or json)
- `--output` / `-o`: Save results to file

#### For `trakt view`:
- `--watchlist` / `-w`: Watchlist to view (default: main watchlist)
- `--format`: Output format (table or json)
- `--output` / `-o`: Save results to file

## Advanced Features

### Interactive Mode

When using the `--interactive` flag, the tool will prompt you to manually select the correct match when multiple search results are found:

```bash
# Enable interactive selection for ambiguous matches
corrupt-video-inspector trakt sync scan_results.json \
  --interactive \
  --watchlist "to-review"
```

**Interactive mode features:**
- **Single match confirmation**: When only one result is found, you can confirm or reject it
- **Multiple choice selection**: When multiple results are found, choose from a numbered list
- **Skip option**: Option to skip items that don't have good matches
- **Improved accuracy**: Manually verify matches to avoid adding incorrect items to your watchlist

**Example interactive session:**
```
Found 2 matches for 'The Matrix' (1999):
  0. Skip (don't add to watchlist)
  1. The Matrix (1999) [movie]
  2. The Matrix Reloaded (2003) [movie]

Select an option [0-2]: 1
```

### Advanced Sync Options

```bash
# Sync to a specific watchlist with interactive mode
corrupt-video-inspector trakt sync scan_results.json \
  --watchlist "my-movies" \
  --interactive \
  --output sync_results.json
```

### Supported Filename Formats

The filename parser automatically detects and handles various naming conventions:

#### Movies
- `The.Matrix.1999.1080p.BluRay.x264.mkv` → "The Matrix" (1999)
- `Inception (2010) [1080p].mp4` → "Inception" (2010)
- `Movie.Name.2023.mkv` → "Movie Name" (2023)
- `Unknown.Movie.mkv` → "Unknown Movie" (no year)

#### TV Shows
- `Breaking.Bad.S01E01.Pilot.2008.mkv` → "Breaking Bad" S1E1 (2008)
- `Game.of.Thrones.1x01.Winter.Is.Coming.mkv` → "Game of Thrones" S1E1
- `Show Name S02E05 Episode Title.mp4` → "Show Name" S2E5

## Workflow Examples

### Discover and organize your collection:
1. **Set up Trakt credentials**: `make secrets-init` (then edit secret files)
2. **Scan your video library**: `corrupt-video-inspector scan /path/to/videos --output scan_results.json`
3. **List your watchlists**: `corrupt-video-inspector trakt list-watchlists`
4. **Sync healthy files to a specific list**: `corrupt-video-inspector trakt sync scan_results.json --watchlist "my-collection"`
5. **View what was added**: `corrupt-video-inspector trakt view --watchlist "my-collection"`

### Multiple watchlists for different categories:
1. **Sync movies to a movies list**: `corrupt-video-inspector trakt sync movie_scan.json --watchlist "my-movies"`
2. **Sync TV shows to a shows list**: `corrupt-video-inspector trakt sync tv_scan.json --watchlist "my-shows"`
3. **Use interactive mode for uncertain matches**: `corrupt-video-inspector trakt sync uncertain_scan.json --watchlist "to-review" --interactive`

### Complete workflow example:
```bash
# Set up authentication (one-time setup)
make secrets-init
echo "your-client-id" > docker/secrets/trakt_client_id.txt
echo "your-client-secret" > docker/secrets/trakt_client_secret.txt

# Authenticate with Trakt
corrupt-video-inspector trakt auth --username=YOUR_USERNAME --store

# Scan your video collection
corrupt-video-inspector scan /path/to/videos --output scan_results.json

# List available watchlists
corrupt-video-inspector trakt list-watchlists

# Sync to specific watchlists
corrupt-video-inspector trakt sync scan_results.json --watchlist "my-collection" --verbose

# Review what was added
corrupt-video-inspector trakt view --watchlist "my-collection"
```

### Process Files by Status

**Default Behavior (v2.0+)**: The tool processes **healthy files only** by default, as specified by the `include_statuses` configuration. This ensures only working video files are synced to your Trakt watchlist.

**Configurable Processing**: You can customize which file statuses to include:

- **HEALTHY**: Non-corrupt files that passed video inspection
- **CORRUPT**: Files identified as corrupted during scanning
- **SUSPICIOUS**: Files that require deep scanning or show corruption indicators

**Configuration Examples**:

```yaml
# Default: sync only healthy files
trakt:
  include_statuses: [HEALTHY]

# Sync all files regardless of status
trakt:
  include_statuses: [HEALTHY, CORRUPT, SUSPICIOUS]

# Legacy behavior: sync only problematic files
trakt:
  include_statuses: [CORRUPT, SUSPICIOUS]
```

**Command Line Override**:
```bash
# Sync only healthy files (default)
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN

# Sync all files
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN --include-statuses HEALTHY CORRUPT SUSPICIOUS

# Sync only corrupt files
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN --include-statuses CORRUPT
```

## Example Workflow

1. **Set up authentication** (one-time setup):
   ```bash
   make secrets-init
   echo "your-client-id" > docker/secrets/trakt_client_id.txt
   echo "your-client-secret" > docker/secrets/trakt_client_secret.txt
   ```

2. **Scan your video collection**:
   ```bash
   corrupt-video-inspector scan /path/to/videos --output scan_results.json
   ```

3. **Sync to Trakt watchlist**:
   ```bash
   corrupt-video-inspector trakt sync scan_results.json --verbose
   ```

4. **Review results**:
   ```
   ==================================================
   TRAKT SYNC SUMMARY
   ==================================================
   Total items processed: 150
   Movies added: 75
   Shows added: 60
   Failed/Not found: 15
   Success rate: 90.0%
   ```

## Error Handling

The tool provides comprehensive error handling:

- **Network Issues**: Automatic retry with exponential backoff for rate limits
- **Invalid Files**: Graceful handling of corrupt JSON or missing files
- **API Errors**: Detailed error messages with HTTP status codes
- **Parsing Failures**: Continues processing other files if some fail to parse

## Output Examples

### Verbose Mode
```
Starting Trakt watchlist sync...
Processing scan file: scan_results.json
Found 3 media items to sync
Searching and adding to watchlist...
  (1/3) Processing: The Matrix (1999) [movie]
    ✅ Added to watchlist
  (2/3) Processing: Breaking Bad (2008) [show]
    ✅ Added to watchlist
  (3/3) Processing: Unknown Movie [movie]
    ❌ Not found on Trakt

==================================================
TRAKT SYNC SUMMARY
==================================================
Total items processed: 3
Movies added: 1
Shows added: 1
Failed/Not found: 1
Success rate: 66.7%
```

### JSON Output (with --output)
```json
{
  "total": 3,
  "movies_added": 1,
  "shows_added": 1,
  "failed": 1,
  "results": [
    {
      "title": "The Matrix",
      "year": 1999,
      "type": "movie",
      "status": "added",
      "trakt_id": 1390,
      "filename": "/videos/The.Matrix.1999.mkv"
    },
    {
      "title": "Breaking Bad",
      "year": 2008,
      "type": "show",
      "status": "added",
      "trakt_id": 1390,
      "filename": "/videos/Breaking.Bad.S01E01.mkv"
    },
    {
      "title": "Unknown Movie",
      "year": null,
      "type": "movie",
      "status": "not_found",
      "filename": "/videos/Unknown.Movie.mkv"
    }
  ]
}
```

## Security Best Practices

1. **Docker Secrets** (Recommended): Use Docker secrets for secure credential storage
   ```bash
   make secrets-init
   echo "your-client-id" > docker/secrets/trakt_client_id.txt
   echo "your-client-secret" > docker/secrets/trakt_client_secret.txt
   ```

2. **Environment Variables**: Alternative method for credential storage
   ```bash
   export CVI_TRAKT_CLIENT_ID="your_client_id"
   export CVI_TRAKT_CLIENT_SECRET="your_client_secret"
   corrupt-video-inspector trakt sync scan.json
   ```

3. **Never Commit Credentials**: Add credential files to your `.gitignore`

4. **Credential Rotation**: Regularly rotate your API credentials

## Troubleshooting

### Common Issues

1. **"No media items found"**: Check that your JSON file contains valid scan results
2. **"Authentication failed"**: Verify your access token is valid and not expired
3. **"Rate limited"**: The tool automatically handles rate limits, but you may need to wait
4. **"Not found on Trakt"**: Some obscure titles may not be in Trakt's database

### Credential Configuration Issues

**Error**: `Trakt credentials not configured. Empty files: trakt_client_id.txt, trakt_client_secret.txt. Run 'make secrets-init' then populate trakt_client_id.txt and trakt_client_secret.txt.`

**Cause**: The Trakt client credentials have not been properly configured.

**Solution**:
1. Run `make secrets-init` to create the credential files:
   ```bash
   make secrets-init
   ```

2. Edit the created files with your Trakt API credentials:
   ```bash
   # Add your Trakt client ID
   echo "your_client_id_here" > docker/secrets/trakt_client_id.txt

   # Add your Trakt client secret
   echo "your_client_secret_here" > docker/secrets/trakt_client_secret.txt
   ```

3. Ensure the files contain valid values (not empty or whitespace-only)

**Error**: `Trakt access token is required. Provide it using the --token option. See docs/trakt.md for instructions on obtaining a token.`

**Cause**: The `--token` parameter was not provided or is empty.

**Solution**:
- Always provide a valid access token when using `list-watchlists` or `view` commands:
  ```bash
  corrupt-video-inspector trakt list-watchlists --token YOUR_ACCESS_TOKEN
  corrupt-video-inspector trakt view --token YOUR_ACCESS_TOKEN
## Troubleshooting

### Common Issues

1. **"Client ID not found"**
   - Check that `docker/secrets/trakt_client_id.txt` exists and contains your Client ID
   - Ensure no extra whitespace or newlines

2. **"Invalid client credentials"**
   - Verify your Client ID and Secret are correct
   - Check that your Trakt application is active

3. **"Authentication failed"**
   - Ensure you're using the correct Trakt username
   - Verify the authorization code was copied correctly
   - Your credentials may be invalid or expired - try re-running the authentication process

4. **"Watchlist not found"**
   - Use `corrupt-video-inspector trakt list-watchlists` to see available watchlists
   - Check the exact spelling and case of the watchlist name
   - Some watchlists may use slugs (URL-friendly names) instead of display names

5. **"Rate limit exceeded"**
   - The tool automatically handles rate limits with backoff
   - If issues persist, wait a few minutes before retrying

### Debug Mode

Use `--verbose` flag for detailed logging to help diagnose issues:

```bash
corrupt-video-inspector trakt sync scan.json --verbose
```

### Manual Configuration

If the authentication commands don't work, you can manually configure PyTrakt:

```python
import trakt
import trakt.core

# For OAuth authentication
trakt.core.AUTH_METHOD = trakt.core.OAUTH_AUTH
trakt.init('your_username', client_id='your_client_id',
          client_secret='your_client_secret', store=True)
```

## Technical Details

- **Backward Compatibility**: All existing sync operations continue to work exactly as before
- **Main Watchlist**: Use `--watchlist "watchlist"` or omit the parameter to sync to the main watchlist
- **Custom Lists**: Use the slug or name of any custom list you have access to
- **Error Handling**: Clear error messages for invalid watchlist names or API issues
- **Output Formats**: Both table and JSON formats supported for all view commands
- **Authentication**: Uses config-based authentication with Docker secrets support
- **File Status Filtering**: Default behavior only syncs healthy files (configurable via `include_statuses`)

## API Rate Limits

The tool respects Trakt API rate limits:
- Automatic retry with exponential backoff
- Built-in delay handling for 429 responses
- Graceful degradation during high-traffic periods

## Security Best Practices

1. **Never commit secrets**: Keep Client ID/Secret out of version control
2. **Use environment variables**: For production deployments
3. **Rotate credentials**: Periodically regenerate your API keys
4. **Limit permissions**: Only grant necessary scopes to your application
5. **Store securely**: Use proper secret management in production

## Integration with Video Inspector

This tool is designed to work seamlessly with the existing video inspector:

```bash
# Complete workflow: scan and sync
corrupt-video-inspector scan /videos --output scan_results.json && \
corrupt-video-inspector trakt sync scan_results.json
```

## Related Documentation

For more details on related topics, see:
- [CLI Usage Guide](CLI.md)
- [Configuration Reference](config.md)
- [Docker Integration](DOCKER_TRAKT.md)
