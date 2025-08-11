# Trakt.tv Integration

This document describes how to use the Trakt.tv watchlist integration feature to automatically sync your video collection to your Trakt.tv watchlist.

## Overview

The Trakt watchlist integration allows you to automatically sync your video collection to your Trakt.tv watchlist by processing JSON scan results from the video inspector and using intelligent filename parsing.

## Prerequisites

1. **Trakt.tv Account**: You need a Trakt.tv account
2. **API Application**: Create a Trakt.tv API application to get client credentials
3. **JSON Scan Results**: Video inspection results in JSON format

## Authentication Setup

The application now uses config-based authentication with Docker secrets support instead of CLI tokens.

### Getting Trakt API Credentials

1. Visit [Trakt.tv API Apps](https://trakt.tv/oauth/applications)
2. Create a new application or use an existing one
3. Note your **Client ID** and **Client Secret**
4. Keep your credentials secure and never commit them to source code

### Setting up Authentication

#### Option 1: Docker Secrets (Recommended)

```bash
# Initialize secret files
make secrets-init

# Add your credentials to the secret files
echo "your-client-id" > docker/secrets/trakt_client_id.txt
echo "your-client-secret" > docker/secrets/trakt_client_secret.txt
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

## Usage

### Basic Sync Command

```bash
# Sync scan results to Trakt watchlist
corrupt-video-inspector trakt sync scan_results.json
```

### Advanced Options

```bash
# Sync to a specific watchlist with interactive mode
corrupt-video-inspector trakt sync scan_results.json \
  --watchlist "my-movies" \
  --interactive \
  --output sync_results.json
```

### List and View Commands

```bash
# List all your watchlists
corrupt-video-inspector trakt list-watchlists

# View contents of a specific watchlist
corrupt-video-inspector trakt view --watchlist "my-collection"

# Save watchlist data to file
corrupt-video-inspector trakt view --watchlist "favorites" --output watchlist.json
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

## Supported Filename Formats

The filename parser automatically detects and handles various naming conventions:

### Movies
- `The.Matrix.1999.1080p.BluRay.x264.mkv` → "The Matrix" (1999)
- `Inception (2010) [1080p].mp4` → "Inception" (2010)
- `Movie.Name.2023.mkv` → "Movie Name" (2023)
- `Unknown.Movie.mkv` → "Unknown Movie" (no year)

### TV Shows
- `Breaking.Bad.S01E01.Pilot.2008.mkv` → "Breaking Bad" S1E1 (2008)
- `Game.of.Thrones.1x01.Winter.Is.Coming.mkv` → "Game of Thrones" S1E1
- `Show Name S02E05 Episode Title.mp4` → "Show Name" S2E5

## Process All Files

The tool processes **all files** from the scan results, regardless of their corruption status, as specified in the requirements. This ensures your entire collection is synced to Trakt.

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
  ```

**Getting Trakt API Credentials**:
1. Visit [Trakt.tv API Apps](https://trakt.tv/oauth/applications)
2. Create a new application
3. Note your **Client ID** and **Client Secret** 
4. Generate an OAuth access token for API calls

### Debug Mode

Use `--verbose` flag for detailed logging to help diagnose issues:

```bash
corrupt-video-inspector trakt sync scan.json --verbose
```

## API Rate Limits

The tool respects Trakt API rate limits:
- Automatic retry with exponential backoff
- Built-in delay handling for 429 responses
- Graceful degradation during high-traffic periods

## Integration with Video Inspector

This tool is designed to work seamlessly with the existing video inspector:

```bash
# Complete workflow: scan and sync
corrupt-video-inspector scan /videos --output scan_results.json && \
corrupt-video-inspector trakt sync scan_results.json
```
