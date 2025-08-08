# Watchlist Functionality Usage Examples

This file demonstrates the new watchlist functionality added to corrupt-video-inspector.

## New Features

### 1. Enhanced `trakt sync` command
The sync command now supports a `--watchlist` parameter to specify which watchlist to sync to:

```bash
# Sync to main watchlist (default behavior)
corrupt-video-inspector trakt sync results.json

# Sync to a specific custom list
corrupt-video-inspector trakt sync results.json --watchlist "my-movies"

# Interactive sync to a custom list
corrupt-video-inspector trakt sync results.json --watchlist "to-watch" --interactive
```

### 2. New `trakt list-watchlists` command
View all available watchlists:

```bash
# List watchlists in table format
corrupt-video-inspector trakt list-watchlists

# List watchlists in JSON format
corrupt-video-inspector trakt list-watchlists --format json

# Save watchlist info to file
corrupt-video-inspector trakt list-watchlists --output watchlists.json
```

### 3. New `trakt view` command
View the contents of any watchlist:

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

## Configuration

Trakt.tv integration now uses config-based authentication with Docker secrets support. Set up your credentials using:

```bash
# Initialize Trakt secrets (creates empty secret files)
make secrets-init

# Edit the secret files with your credentials
echo "your-client-id" > docker/secrets/trakt_client_id.txt
echo "your-client-secret" > docker/secrets/trakt_client_secret.txt
```

You can also set a default watchlist and customize file status filtering in your config file:

```yaml
trakt:
  client_id: "your-client-id"  # Or use Docker secrets
  client_secret: "your-client-secret"  # Or use Docker secrets
  default_watchlist: "my-default-list"  # Optional: sync to this list by default
  include_statuses: ["healthy"]  # Default: only sync healthy files
```

## Workflow Examples

### Discover and organize your collection:
1. Set up Trakt credentials: `make secrets-init` (then edit secret files)
2. Scan your video library: `corrupt-video-inspector scan /path/to/videos --output scan_results.json`
3. List your watchlists: `corrupt-video-inspector trakt list-watchlists`
4. Sync healthy files to a specific list: `corrupt-video-inspector trakt sync scan_results.json --watchlist "my-collection"`
5. View what was added: `corrupt-video-inspector trakt view --watchlist "my-collection"`

### Multiple watchlists for different categories:
1. Sync movies to a movies list: `corrupt-video-inspector trakt sync movie_scan.json --watchlist "my-movies"`
2. Sync TV shows to a shows list: `corrupt-video-inspector trakt sync tv_scan.json --watchlist "my-shows"`
3. Use interactive mode for uncertain matches: `corrupt-video-inspector trakt sync uncertain_scan.json --watchlist "to-review" --interactive`

## Technical Details

- **Backward Compatibility**: All existing sync operations continue to work exactly as before
- **Main Watchlist**: Use `--watchlist "watchlist"` or omit the parameter to sync to the main watchlist
- **Custom Lists**: Use the slug or name of any custom list you have access to
- **Error Handling**: Clear error messages for invalid watchlist names or API issues
- **Output Formats**: Both table and JSON formats supported for all view commands
- **Authentication**: Now uses config-based authentication with Docker secrets support instead of CLI tokens
- **File Status Filtering**: Default behavior now only syncs healthy files (configurable via `include_statuses`)