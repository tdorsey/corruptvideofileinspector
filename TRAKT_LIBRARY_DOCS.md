# Trakt.tv Watchlist Management Library

A comprehensive Python library that provides a simplified interface for managing Trakt.tv watchlists. This library abstracts the complexity of the Trakt.tv API for common watchlist operations, making it easier for developers to integrate Trakt.tv functionality into their applications.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Library Initialization](#library-initialization)
- [Authentication](#authentication)
- [Search Functionality](#search-functionality)
- [Watchlist Management](#watchlist-management)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Best Practices](#best-practices)

## Installation

```bash
# The library is included with the Corrupt Video Inspector
pip install -r requirements.txt
```

## Quick Start

```python
from trakt_library import WatchlistManager

# Initialize with credentials
manager = WatchlistManager(
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Or use environment variables
# export TRAKT_CLIENT_ID="your-client-id"
# export TRAKT_CLIENT_SECRET="your-client-secret"
manager = WatchlistManager()

# Search for content
results = manager.search("inception")
print(f"Found {len(results)} results")

# Add movie to watchlist (requires authentication)
if manager.is_authenticated():
    result = manager.add_movie("inception")
    if result.success:
        print(f"Added to watchlist: {result.message}")
```

## Library Initialization

### Basic Initialization

```python
from trakt_library import WatchlistManager

# With explicit credentials
manager = WatchlistManager(
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# With existing tokens
manager = WatchlistManager(
    client_id="your-client-id", 
    client_secret="your-client-secret",
    access_token="your-access-token",
    refresh_token="your-refresh-token"
)
```

### Environment Variables

```python
import os

# Set environment variables
os.environ['TRAKT_CLIENT_ID'] = 'your-client-id'
os.environ['TRAKT_CLIENT_SECRET'] = 'your-client-secret'

# Initialize without parameters
manager = WatchlistManager()
```

### Custom Token Storage

```python
from trakt_library import WatchlistManager, TokenStorage

class FileTokenStorage(TokenStorage):
    def __init__(self, filename):
        self.filename = filename
    
    def save_tokens(self, access_token, refresh_token):
        with open(self.filename, 'w') as f:
            json.dump({
                'access_token': access_token,
                'refresh_token': refresh_token
            }, f)
    
    def load_tokens(self):
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'access_token': None, 'refresh_token': None}

# Use custom storage
storage = FileTokenStorage('tokens.json')
manager = WatchlistManager(
    client_id="your-client-id",
    client_secret="your-client-secret",
    token_storage=storage
)
```

## Authentication

### OAuth Flow

```python
# 1. Get authorization URL
auth_url = manager.get_auth_url()
print(f"Visit: {auth_url}")

# 2. User authorizes and you get the code
auth_code = input("Enter authorization code: ")

# 3. Exchange code for tokens
if manager.exchange_code(auth_code):
    print("Authentication successful!")
else:
    print("Authentication failed")
```

### Token Management

```python
# Check authentication status
if manager.is_authenticated():
    print("User is authenticated")
else:
    print("Authentication required")

# Refresh tokens manually
if manager.refresh_tokens():
    print("Tokens refreshed successfully")
else:
    print("Token refresh failed")
```

## Search Functionality

### Basic Search

```python
# Search for movies and shows
results = manager.search("breaking bad")
for result in results:
    print(f"{result.title} ({result.year}) - {result.content_type}")
```

### Specific Content Types

```python
# Search only movies
movies = manager.search_movies("inception", year=2010)
for movie in movies:
    print(f"Movie: {movie.title} ({movie.year})")

# Search only TV shows
shows = manager.search_shows("breaking bad", year=2008)
for show in shows:
    print(f"Show: {show.title} ({show.year})")
```

### Search by ID

```python
# Get movie by IMDb ID
movie = manager.get_movie_by_id("tt1375666", id_type="imdb")
if movie:
    print(f"Found: {movie.title}")

# Get show by Trakt ID
show = manager.get_show_by_id(1390, id_type="trakt")
if show:
    print(f"Found: {show.title}")
```

### Advanced Search

```python
# Search by year
recent_movies = manager.search_by_year(2023, content_type="movie")

# Get trending content
trending = manager.get_trending("movies", limit=10)
popular = manager.get_popular("shows", limit=5)
```

## Watchlist Management

### Adding Content

```python
# Add single movie
result = manager.add_movie("inception")
if result.success:
    print(f"Success: {result.message}")
else:
    print(f"Failed: {result.message}")

# Add movie by ID
result = manager.add_movie_by_id("tt1375666", id_type="imdb")

# Add TV show
result = manager.add_show("breaking bad")

# Add show by ID
result = manager.add_show_by_id("81189", id_type="tvdb")
```

### Batch Operations

```python
# Add multiple movies
movies = ["inception", "interstellar", "dunkirk"]
batch_result = manager.add_movies(movies)

print(f"Total: {batch_result.total}")
print(f"Successful: {len(batch_result.successful)}")
print(f"Failed: {len(batch_result.failed)}")

# Add multiple shows
shows = ["breaking bad", "better call saul", "el camino"]
batch_result = manager.add_shows(shows)
```

### Removing Content

```python
# Remove single movie
result = manager.remove_movie("inception")

# Remove by ID
result = manager.remove_movie_by_id("tt1375666", id_type="imdb")

# Remove multiple items
batch_result = manager.remove_movies(["movie1", "movie2"])

# Clear entire watchlist (requires confirmation)
result = manager.clear_watchlist(confirm=True)
```

### Dry Run Mode

```python
# Test additions without actually adding
result = manager.add_movie("test movie", dry_run=True)
print(result.message)  # "Dry run: Would add movie 'test movie'"
```

## Watchlist Retrieval

### Basic Retrieval

```python
# Get entire watchlist
watchlist = manager.get_watchlist()
print(f"Total items: {len(watchlist.items)}")

for item in watchlist.items:
    print(f"{item.title} ({item.year}) - {item.content_type}")
```

### Filtered Retrieval

```python
# Get only movies
movies = manager.get_movies(sort_by="title", limit=10)

# Get only shows
shows = manager.get_shows(sort_by="added", limit=5)

# Custom filtering
recent_watchlist = manager.get_watchlist(
    content_type="movie",
    sort_by="added",
    limit=20
)
```

### Export Options

```python
# Export as JSON
json_data = manager.export_watchlist("json")
print(json_data)

# Export as CSV
csv_data = manager.export_watchlist("csv")
with open("watchlist.csv", "w") as f:
    f.write(csv_data)
```

## Data Models

### SearchResult

```python
from trakt_library import SearchResult

result = SearchResult(
    title="Inception",
    year=2010,
    ids={"trakt": 12345, "imdb": "tt1375666"},
    content_type="movie"
)
```

### OperationResult

```python
from trakt_library import OperationResult

# Check operation success
result = manager.add_movie("inception")
if result:  # Uses __bool__ method
    print("Operation successful")
    print(f"Message: {result.message}")
    if result.item:
        print(f"Item: {result.item.title}")
```

### Watchlist and WatchlistItem

```python
# Get watchlist
watchlist = manager.get_watchlist()

# Convert to dictionary
data = watchlist.to_dict()

# Convert to JSON
json_str = watchlist.to_json()

# Individual items
for item in watchlist.items:
    item_data = item.to_dict()
    print(f"Added: {item.added_at}")
```

## Error Handling

### Exception Types

```python
from trakt_library import (
    TraktWatchlistError,
    AuthenticationError,
    APIError,
    NotFoundError,
    ValidationError
)

try:
    manager = WatchlistManager()  # Missing credentials
except ValidationError as e:
    print(f"Validation error: {e}")

try:
    watchlist = manager.get_watchlist()
except AuthenticationError as e:
    print(f"Authentication required: {e}")

try:
    result = manager.add_movie("nonexistent movie")
except NotFoundError as e:
    print(f"Not found: {e}")
    print(f"Suggestions: {e.suggestions}")
```

### Graceful Error Handling

```python
# Operations return results instead of raising exceptions
result = manager.add_movie("some movie")
if not result.success:
    print(f"Failed to add movie: {result.message}")
    # Handle failure gracefully
```

## Advanced Usage

### Watchlist Statistics

```python
# Get detailed statistics
stats = manager.get_watchlist_stats()
print(f"Total items: {stats['total_items']}")
print(f"Movies: {stats['movies']}")
print(f"Shows: {stats['shows']}")
print(f"Year range: {stats['oldest_year']} - {stats['newest_year']}")
```

### Validation

```python
# Validate watchlist integrity
validation = manager.validate_watchlist()
print(f"Valid items: {validation['valid_items']}")
print(f"Invalid items: {validation['invalid_items']}")

for error in validation['validation_errors']:
    print(f"Issues with {error['item']['title']}: {error['issues']}")
```

### Search Within Watchlist

```python
# Search your own watchlist
matches = manager.search_watchlist("batman")
for match in matches:
    print(f"Found in watchlist: {match.title}")
```

### User Profile

```python
# Get user profile information
profile = manager.get_user_profile()
if 'error' not in profile:
    print(f"Username: {profile.get('username')}")
    print(f"Name: {profile.get('name')}")
```

## API Reference

### WatchlistManager Methods

The WatchlistManager class provides 25+ public methods:

#### Authentication
- `is_authenticated() -> bool`
- `get_auth_url() -> str`
- `exchange_code(auth_code: str) -> bool`
- `refresh_tokens() -> bool`

#### Search
- `search(query: str, **kwargs) -> List[SearchResult]`
- `search_movies(query: str, year: Optional[int] = None) -> List[SearchResult]`
- `search_shows(query: str, year: Optional[int] = None) -> List[SearchResult]`
- `get_movie_by_id(item_id: Union[int, str], id_type: str = "trakt") -> Optional[SearchResult]`
- `get_show_by_id(item_id: Union[int, str], id_type: str = "trakt") -> Optional[SearchResult]`
- `search_by_year(year: int, content_type: Optional[str] = None) -> List[SearchResult]`

#### Add to Watchlist
- `add_movie(title: str, dry_run: bool = False) -> OperationResult`
- `add_movie_by_id(item_id: Union[int, str], id_type: str = "imdb") -> OperationResult`
- `add_show(title: str, dry_run: bool = False) -> OperationResult`
- `add_show_by_id(item_id: Union[int, str], id_type: str = "imdb") -> OperationResult`
- `add_movies(titles: List[str]) -> BatchResult`
- `add_shows(titles: List[str]) -> BatchResult`

#### Remove from Watchlist
- `remove_movie(title: str) -> OperationResult`
- `remove_movie_by_id(item_id: Union[int, str], id_type: str = "imdb") -> OperationResult`
- `remove_show(title: str) -> OperationResult`
- `remove_show_by_id(item_id: Union[int, str], id_type: str = "imdb") -> OperationResult`
- `remove_movies(titles: List[str]) -> BatchResult`
- `remove_shows(titles: List[str]) -> BatchResult`
- `clear_watchlist(confirm: bool = False) -> OperationResult`

#### Watchlist Retrieval
- `get_watchlist(content_type: Optional[str] = None, sort_by: str = "added", limit: Optional[int] = None) -> Watchlist`
- `get_movies(sort_by: str = "added", limit: Optional[int] = None) -> Watchlist`
- `get_shows(sort_by: str = "added", limit: Optional[int] = None) -> Watchlist`

#### Utility and Analysis
- `get_watchlist_stats() -> Dict[str, Any]`
- `validate_watchlist() -> Dict[str, Any]`
- `export_watchlist(format_type: str = "json") -> str`
- `search_watchlist(query: str) -> List[WatchlistItem]`
- `get_recommendations(content_type: Optional[str] = None, limit: int = 10) -> List[SearchResult]`
- `sync_progress() -> Dict[str, Any]`
- `get_user_profile() -> Dict[str, Any]`
- `get_trending(content_type: str = "movies", limit: int = 10) -> List[SearchResult]`
- `get_popular(content_type: str = "movies", limit: int = 10) -> List[SearchResult]`

## Examples

### Complete Workflow Example

```python
from trakt_library import WatchlistManager, ValidationError, AuthenticationError

def main():
    try:
        # Initialize manager
        manager = WatchlistManager(
            client_id="your-client-id",
            client_secret="your-client-secret"
        )
        
        # Authenticate if needed
        if not manager.is_authenticated():
            print("Authentication required")
            auth_url = manager.get_auth_url()
            print(f"Visit: {auth_url}")
            
            auth_code = input("Enter code: ")
            if not manager.exchange_code(auth_code):
                print("Authentication failed")
                return
        
        # Search and add movies
        search_terms = ["inception", "interstellar", "dunkirk"]
        
        print("Searching and adding movies...")
        for term in search_terms:
            result = manager.add_movie(term)
            if result.success:
                print(f"✅ Added: {result.item.title} ({result.item.year})")
            else:
                print(f"❌ Failed: {result.message}")
        
        # Get watchlist statistics
        stats = manager.get_watchlist_stats()
        print(f"\nWatchlist contains {stats['total_items']} items")
        print(f"Movies: {stats['movies']}, Shows: {stats['shows']}")
        
        # Export watchlist
        json_export = manager.export_watchlist("json")
        with open("my_watchlist.json", "w") as f:
            f.write(json_export)
        print("Watchlist exported to my_watchlist.json")
        
    except ValidationError as e:
        print(f"Configuration error: {e}")
    except AuthenticationError as e:
        print(f"Authentication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
```

### Interactive Movie Selection

```python
def interactive_add_movie(manager):
    """Add movie with interactive search result selection."""
    title = input("Enter movie title: ")
    
    # Search for multiple results
    results = manager.search_movies(title)
    
    if not results:
        print("No movies found")
        return
    
    if len(results) == 1:
        # Single result - confirm
        movie = results[0]
        confirm = input(f"Add '{movie.title} ({movie.year})'? [y/N]: ")
        if confirm.lower() == 'y':
            result = manager.add_movie_by_id(movie.ids.get('trakt'), 'trakt')
            print(f"Result: {result.message}")
    else:
        # Multiple results - show menu
        print(f"\nFound {len(results)} movies:")
        for i, movie in enumerate(results, 1):
            print(f"  {i}. {movie.title} ({movie.year})")
        
        try:
            choice = int(input("Select movie (0 to cancel): "))
            if 1 <= choice <= len(results):
                selected = results[choice - 1]
                result = manager.add_movie_by_id(selected.ids.get('trakt'), 'trakt')
                print(f"Result: {result.message}")
            else:
                print("Cancelled")
        except ValueError:
            print("Invalid selection")
```

### Bulk Operations

```python
def bulk_import_from_file(manager, filename):
    """Import movies from a text file (one per line)."""
    try:
        with open(filename, 'r') as f:
            movie_titles = [line.strip() for line in f if line.strip()]
        
        print(f"Importing {len(movie_titles)} movies...")
        
        # Process in batches of 10
        batch_size = 10
        for i in range(0, len(movie_titles), batch_size):
            batch = movie_titles[i:i + batch_size]
            
            print(f"Processing batch {i//batch_size + 1}...")
            result = manager.add_movies(batch)
            
            print(f"  Success: {len(result.successful)}")
            print(f"  Failed: {len(result.failed)}")
            
            # Show failures
            for failure in result.failed:
                print(f"  ❌ {failure.message}")
            
            # Small delay between batches
            time.sleep(1)
        
        print("Import completed!")
        
    except FileNotFoundError:
        print(f"File not found: {filename}")
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
# Good
try:
    result = manager.add_movie("inception")
    if result.success:
        print("Added successfully")
    else:
        print(f"Failed: {result.message}")
except AuthenticationError:
    print("Please authenticate first")

# Avoid
manager.add_movie("inception")  # Could raise exceptions
```

### 2. Rate Limiting

The library handles rate limiting automatically, but be mindful of bulk operations:

```python
# Good - use batch operations
manager.add_movies(["movie1", "movie2", "movie3"])

# Less efficient - individual calls
for movie in movies:
    manager.add_movie(movie)
    time.sleep(1)  # Manual rate limiting
```

### 3. Authentication

Store tokens securely and handle refresh:

```python
# Good - custom secure storage
class SecureTokenStorage(TokenStorage):
    def save_tokens(self, access_token, refresh_token):
        # Save to secure storage (encrypted, keychain, etc.)
        pass
    
    def load_tokens(self):
        # Load from secure storage
        pass

# Avoid - storing tokens in plain text files
```

### 4. Search Optimization

Use specific searches when possible:

```python
# Good - specific search
movies = manager.search_movies("inception", year=2010)

# Less efficient - general search with filtering
results = manager.search("inception")
movies = [r for r in results if r.content_type == "movie" and r.year == 2010]
```

### 5. Watchlist Management

Check for duplicates before adding:

```python
# Check if already in watchlist
watchlist = manager.get_watchlist()
existing_titles = {item.title.lower() for item in watchlist.items}

if "inception" not in existing_titles:
    manager.add_movie("inception")
else:
    print("Movie already in watchlist")
```

### 6. Logging

Enable appropriate logging levels:

```python
import logging
logging.basicConfig(level=logging.INFO)

# For debugging
logging.getLogger('trakt_library').setLevel(logging.DEBUG)
```

This comprehensive library provides all the functionality specified in the Product Requirements Document, with proper error handling, type safety, and extensive documentation. It maintains backward compatibility with existing code while providing a modern, developer-friendly API.