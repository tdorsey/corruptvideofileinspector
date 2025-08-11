# Trakt.tv Integration

This document describes how to use the Trakt.tv watchlist integration feature to automatically sync your video collection to your Trakt.tv watchlist.

## Overview

The Trakt watchlist integration allows you to automatically sync your video collection to your Trakt.tv watchlist by processing JSON scan results from the video inspector and using intelligent filename parsing.

## Prerequisites

1. **Trakt.tv Account**: You need a Trakt.tv account
2. **API Access Token**: Generate an OAuth 2.0 access token from your Trakt.tv account
3. **JSON Scan Results**: Video inspection results in JSON format

## Getting a Trakt API Token

1. Visit [Trakt.tv API Apps](https://trakt.tv/oauth/applications)
2. Create a new application or use an existing one
3. Generate an access token for your application
4. Keep your token secure and never commit it to source code

## Usage

### Basic Sync Command

```bash
# Sync scan results to Trakt watchlist
python3 cli_handler.py trakt scan_results.json --token YOUR_ACCESS_TOKEN
```

### Advanced Options

```bash
# With verbose output and result saving
python3 cli_handler.py trakt scan_results.json \
  --token YOUR_ACCESS_TOKEN \
  --client-id YOUR_CLIENT_ID \
  --verbose \
  --output sync_results.json
```

### Command Options

- `--token` / `-t`: **Required** - Your Trakt.tv OAuth access token
- `--client-id` / `-c`: Optional - Your Trakt.tv API client ID
- `--verbose` / `-v`: Enable detailed progress output
- `--interactive` / `-i`: Enable interactive selection of search results
- `--output` / `-o`: Save sync results to JSON file

### Interactive Mode

When using the `--interactive` flag, the tool will prompt you to manually select the correct match when multiple search results are found:

```bash
# Enable interactive selection for ambiguous matches
python3 cli_handler.py trakt scan_results.json \
  --token YOUR_ACCESS_TOKEN \
  --interactive \
  --verbose
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

## Process Files by Status

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

1. **Scan your video collection**:
   ```bash
   python3 cli_handler.py --json /path/to/videos
   ```

2. **Sync to Trakt watchlist**:
   ```bash
   python3 cli_handler.py trakt corruption_scan_results.json --token YOUR_TOKEN --verbose
   ```

3. **Review results**:
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

1. **Environment Variables**: Store your token in environment variables
   ```bash
   export TRAKT_TOKEN="your_access_token_here"
   python3 cli_handler.py trakt scan.json --token "$TRAKT_TOKEN"
   ```

2. **Never Commit Tokens**: Add tokens to your `.gitignore`

3. **Token Rotation**: Regularly rotate your API tokens

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
python3 cli_handler.py trakt scan.json --token YOUR_TOKEN --verbose
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
python3 cli_handler.py --json /videos && \
python3 cli_handler.py trakt corruption_scan_results.json --token $TRAKT_TOKEN
```
