# Watchlist Functionality Usage Examples

This file demonstrates the new watchlist functionality added to corrupt-video-inspector.

## New Features

### 1. Enhanced `trakt sync` command
The sync command now supports a `--watchlist` parameter to specify which watchlist to sync to:

```bash
# Sync to main watchlist (default behavior)
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN

# Sync to a specific custom list
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN --watchlist "my-movies"

# Interactive sync to a custom list
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN --watchlist "to-watch" --interactive
```

### 2. New `trakt list-watchlists` command
View all available watchlists:

```bash
# List watchlists in table format
corrupt-video-inspector trakt list-watchlists --token YOUR_TOKEN

# List watchlists in JSON format
corrupt-video-inspector trakt list-watchlists --token YOUR_TOKEN --format json

# Save watchlist info to file
corrupt-video-inspector trakt list-watchlists --token YOUR_TOKEN --output watchlists.json
```

### 3. New `trakt view` command
View the contents of any watchlist:

```bash
# View main watchlist
corrupt-video-inspector trakt view --token YOUR_TOKEN

# View a specific custom list
corrupt-video-inspector trakt view --token YOUR_TOKEN --watchlist "my-movies"

# View watchlist in JSON format
corrupt-video-inspector trakt view --token YOUR_TOKEN --watchlist "favorites" --format json

# Save watchlist contents to file
corrupt-video-inspector trakt view --token YOUR_TOKEN --watchlist "to-watch" --output contents.json
```

## Configuration

You can set a default watchlist in your config file:

```yaml
trakt:
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  default_watchlist: "my-default-list"  # Optional: sync to this list by default
```

## Workflow Examples

### Discover and organize your collection:
1. Scan your video library: `corrupt-video-inspector scan /path/to/videos --output scan_results.json`
2. List your watchlists: `corrupt-video-inspector trakt list-watchlists --token YOUR_TOKEN`
3. Sync healthy files to a specific list: `corrupt-video-inspector trakt sync scan_results.json --token YOUR_TOKEN --watchlist "my-collection"`
4. View what was added: `corrupt-video-inspector trakt view --token YOUR_TOKEN --watchlist "my-collection"`

### Multiple watchlists for different categories:
1. Sync movies to a movies list: `corrupt-video-inspector trakt sync movie_scan.json --token YOUR_TOKEN --watchlist "my-movies"`
2. Sync TV shows to a shows list: `corrupt-video-inspector trakt sync tv_scan.json --token YOUR_TOKEN --watchlist "my-shows"`
3. Use interactive mode for uncertain matches: `corrupt-video-inspector trakt sync uncertain_scan.json --token YOUR_TOKEN --watchlist "to-review" --interactive`

## Technical Details

- **Backward Compatibility**: All existing sync operations continue to work exactly as before
- **Main Watchlist**: Use `--watchlist "watchlist"` or omit the parameter to sync to the main watchlist
- **Custom Lists**: Use the slug or name of any custom list you have access to
- **Error Handling**: Clear error messages for invalid watchlist names or API issues
- **Output Formats**: Both table and JSON formats supported for all view commands