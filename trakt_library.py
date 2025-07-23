"""
Trakt.tv Watchlist Management Library

A simplified Python library that provides a high-level interface for managing
Trakt.tv watchlists using the trakt.py library. This library abstracts the
complexity of the trakt.py library for common watchlist operations.

Example usage:
    from trakt_library import WatchlistManager
    
    manager = WatchlistManager(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
    
    # Search for content
    results = manager.search("inception")
    
    # Add to watchlist
    result = manager.add_movie("inception")
    
    # Get watchlist
    watchlist = manager.get_watchlist()
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests

# Configure module logger
logger = logging.getLogger(__name__)


# Exception hierarchy
class TraktWatchlistError(Exception):
    """Base exception for library errors."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthenticationError(TraktWatchlistError):
    """Authentication-related errors."""
    pass


class APIError(TraktWatchlistError):
    """API communication errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class NotFoundError(TraktWatchlistError):
    """Item not found errors."""
    
    def __init__(self, message: str, suggestions: Optional[List[str]] = None) -> None:
        super().__init__(message)
        self.suggestions = suggestions or []


class ValidationError(TraktWatchlistError):
    """Input validation errors."""
    pass


# Data models
@dataclass
class SearchResult:
    """Represents a search result item."""
    title: str
    year: Optional[int]
    ids: Dict[str, Union[int, str]]
    content_type: str  # 'movie' or 'show'
    
    def __post_init__(self) -> None:
        """Validate and normalize data."""
        if self.content_type not in ('movie', 'show'):
            raise ValidationError(f"Invalid content_type: {self.content_type}")


@dataclass
class OperationResult:
    """Result of add/remove operations."""
    success: bool
    message: str
    item: Optional[SearchResult] = None
    
    def __bool__(self) -> bool:
        """Allow boolean evaluation of operation result."""
        return self.success


@dataclass
class WatchlistItem:
    """Represents an item in a watchlist."""
    title: str
    year: Optional[int]
    content_type: str  # 'movie' or 'show'
    ids: Dict[str, Union[int, str]]
    added_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'title': self.title,
            'year': self.year,
            'content_type': self.content_type,
            'ids': self.ids,
            'added_at': self.added_at.isoformat()
        }


@dataclass
class Watchlist:
    """Collection of watchlist items."""
    items: List[WatchlistItem] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'items': [item.to_dict() for item in self.items],
            'total_count': len(self.items)
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)


@dataclass  
class BatchResult:
    """Result of batch operations."""
    successful: List[OperationResult]
    failed: List[OperationResult]
    total: int
    
    def __post_init__(self) -> None:
        """Calculate totals."""
        if self.total == 0:
            self.total = len(self.successful) + len(self.failed)


# Token storage interface
class TokenStorage:
    """Abstract base class for token storage backends."""
    
    def save_tokens(self, access_token: str, refresh_token: str) -> None:
        """Save access and refresh tokens."""
        raise NotImplementedError
    
    def load_tokens(self) -> Dict[str, Optional[str]]:
        """Load tokens. Return dict with 'access_token' and 'refresh_token' keys."""
        raise NotImplementedError


class MemoryTokenStorage(TokenStorage):
    """In-memory token storage (tokens lost when process ends)."""
    
    def __init__(self) -> None:
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
    
    def save_tokens(self, access_token: str, refresh_token: str) -> None:
        """Save tokens in memory."""
        self._access_token = access_token
        self._refresh_token = refresh_token
        logger.debug("Tokens saved to memory storage")
    
    def load_tokens(self) -> Dict[str, Optional[str]]:
        """Load tokens from memory."""
        return {
            'access_token': self._access_token,
            'refresh_token': self._refresh_token
        }


# Enhanced TraktAPI class
class TraktAPI:
    """Enhanced Trakt.tv API client with retry logic and rate limiting."""
    
    BASE_URL = "https://api.trakt.tv"
    API_VERSION = "2"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_storage: Optional[TokenStorage] = None
    ) -> None:
        """
        Initialize enhanced Trakt API client.
        
        Args:
            client_id: Trakt API client ID
            client_secret: Trakt API client secret
            access_token: Optional OAuth access token
            refresh_token: Optional OAuth refresh token
            token_storage: Optional token storage backend
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_storage = token_storage or MemoryTokenStorage()
        
        self.session = requests.Session()
        self._setup_headers()
        
        # Load tokens from storage if not provided
        if not self.access_token:
            tokens = self.token_storage.load_tokens()
            self.access_token = tokens.get('access_token')
            self.refresh_token = tokens.get('refresh_token')
            
        logger.info("Enhanced TraktAPI client initialized")
    
    def _setup_headers(self) -> None:
        """Setup default headers for API requests."""
        self.session.headers.update({
            "Content-Type": "application/json",
            "trakt-api-version": self.API_VERSION,
            "trakt-api-key": self.client_id
        })
        
        if self.access_token:
            self.session.headers["Authorization"] = f"Bearer {self.access_token}"
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retries: int = 3
    ) -> requests.Response:
        """
        Make authenticated request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            retries: Number of retry attempts
            
        Returns:
            requests.Response: API response
            
        Raises:
            APIError: If request fails after retries
            AuthenticationError: If authentication fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                logger.debug(f"Making {method} request to {endpoint} (attempt {attempt + 1})")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=30
                )
                
                # Handle different status codes
                if response.status_code == 200 or response.status_code == 201:
                    return response
                elif response.status_code == 401:
                    # Try to refresh token once
                    if self.refresh_token and attempt == 0:
                        logger.info("Access token expired, attempting refresh")
                        if self.refresh_tokens():
                            self._setup_headers()
                            continue  # Retry with new token
                    raise AuthenticationError("Authentication failed - invalid or expired token")
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 10))
                    if attempt < retries:
                        logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        time.sleep(retry_after)
                        continue
                    raise APIError(f"Rate limit exceeded after {retries} retries", response.status_code)
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    raise APIError(f"Server error: {response.status_code}", response.status_code)
                else:
                    # Other client errors
                    raise APIError(f"API request failed: {response.status_code}", response.status_code)
                    
            except requests.RequestException as e:
                if attempt < retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                raise APIError(f"Network error: {e}")
        
        raise APIError(f"Request failed after {retries + 1} attempts")
    
    def refresh_tokens(self) -> bool:
        """
        Refresh access token using refresh token.
        
        Returns:
            bool: True if refresh successful, False otherwise
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False
        
        try:
            response = self._make_request(
                "POST",
                "/oauth/token",
                data={
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token"
                },
                retries=1  # Don't retry token refresh
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                
                # Save new tokens
                if self.access_token and self.refresh_token:
                    self.token_storage.save_tokens(self.access_token, self.refresh_token)
                    logger.info("Tokens refreshed successfully")
                    return True
                    
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
        
        return False
    
    def search(
        self, 
        query: str, 
        content_type: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Search for content on Trakt.
        
        Args:
            query: Search query
            content_type: Optional content type filter ('movie' or 'show')
            year: Optional year filter
            limit: Maximum results to return
            
        Returns:
            List[SearchResult]: Search results
        """
        params = {"query": query, "limit": str(limit)}
        if year:
            params["year"] = str(year)
        
        endpoint = "/search/movie,show"
        if content_type == "movie":
            endpoint = "/search/movie"
        elif content_type == "show":
            endpoint = "/search/show"
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            results = response.json()
            
            search_results = []
            for result in results:
                if "movie" in result:
                    movie = result["movie"]
                    search_results.append(SearchResult(
                        title=movie.get("title", ""),
                        year=movie.get("year"),
                        ids=movie.get("ids", {}),
                        content_type="movie"
                    ))
                elif "show" in result:
                    show = result["show"]
                    search_results.append(SearchResult(
                        title=show.get("title", ""),
                        year=show.get("year"),
                        ids=show.get("ids", {}),
                        content_type="show"
                    ))
            
            logger.info(f"Search for '{query}' returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []


# Main WatchlistManager class
class WatchlistManager:
    """Main interface for Trakt.tv watchlist management."""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_storage: Optional[TokenStorage] = None
    ) -> None:
        """
        Initialize WatchlistManager.
        
        Args:
            client_id: Trakt API client ID (or from TRAKT_CLIENT_ID env var)
            client_secret: Trakt API client secret (or from TRAKT_CLIENT_SECRET env var)
            access_token: Optional OAuth access token
            refresh_token: Optional OAuth refresh token
            token_storage: Optional token storage backend
            
        Raises:
            ValidationError: If required credentials are missing
        """
        import os
        
        # Use environment variables if not provided
        self.client_id = client_id or os.getenv("TRAKT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("TRAKT_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            raise ValidationError(
                "client_id and client_secret are required. "
                "Provide them as parameters or set TRAKT_CLIENT_ID and TRAKT_CLIENT_SECRET environment variables."
            )
        
        # Initialize API client
        self.api = TraktAPI(
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=access_token,
            refresh_token=refresh_token,
            token_storage=token_storage
        )
        
        logger.info("WatchlistManager initialized successfully")
    
    # Authentication methods
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.api.access_token is not None
    
    def get_auth_url(self) -> str:
        """Get OAuth authorization URL for web applications."""
        # This would typically involve generating a state parameter and redirect URL
        # For simplicity, providing the basic OAuth URL format
        return f"https://trakt.tv/oauth/authorize?response_type=code&client_id={self.client_id}"
    
    def exchange_code(self, auth_code: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> bool:
        """
        Exchange authorization code for access tokens.
        
        Args:
            auth_code: Authorization code from OAuth flow
            redirect_uri: OAuth redirect URI
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = self.api._make_request(
                "POST",
                "/oauth/token",
                data={
                    "code": auth_code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                },
                retries=1
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.api.access_token = token_data.get("access_token")
                self.api.refresh_token = token_data.get("refresh_token")
                
                if self.api.access_token and self.api.refresh_token:
                    self.api.token_storage.save_tokens(self.api.access_token, self.api.refresh_token)
                    self.api._setup_headers()
                    logger.info("OAuth tokens exchanged successfully")
                    return True
                    
        except Exception as e:
            logger.error(f"OAuth code exchange failed: {e}")
        
        return False
    
    def refresh_tokens(self) -> bool:
        """Refresh access tokens."""
        return self.api.refresh_tokens()
    
    # Search methods
    def search(self, query: str, **kwargs: Any) -> List[SearchResult]:
        """Search for movies and TV shows."""
        return self.api.search(query, **kwargs)
    
    def search_movies(self, query: str, year: Optional[int] = None) -> List[SearchResult]:
        """Search for movies only."""
        return self.api.search(query, content_type="movie", year=year)
    
    def search_shows(self, query: str, year: Optional[int] = None) -> List[SearchResult]:
        """Search for TV shows only."""
        return self.api.search(query, content_type="show", year=year)
    
    def get_movie_by_id(self, item_id: Union[int, str], id_type: str = "trakt") -> Optional[SearchResult]:
        """Get movie by specific ID type."""
        try:
            endpoint = f"/movies/{item_id}"
            if id_type != "trakt":
                endpoint = f"/search/movie?{id_type}={item_id}"
            
            response = self.api._make_request("GET", endpoint)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list) and data:
                    # Search response format
                    movie_data = data[0].get("movie", {})
                else:
                    # Direct lookup response format
                    movie_data = data
                
                if movie_data:
                    return SearchResult(
                        title=movie_data.get("title", ""),
                        year=movie_data.get("year"),
                        ids=movie_data.get("ids", {}),
                        content_type="movie"
                    )
            
            logger.info(f"Movie with {id_type} ID '{item_id}' not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting movie by {id_type} ID '{item_id}': {e}")
            return None
    
    def get_show_by_id(self, item_id: Union[int, str], id_type: str = "trakt") -> Optional[SearchResult]:
        """Get TV show by specific ID type."""
        try:
            endpoint = f"/shows/{item_id}"
            if id_type != "trakt":
                endpoint = f"/search/show?{id_type}={item_id}"
            
            response = self.api._make_request("GET", endpoint)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list) and data:
                    # Search response format
                    show_data = data[0].get("show", {})
                else:
                    # Direct lookup response format
                    show_data = data
                
                if show_data:
                    return SearchResult(
                        title=show_data.get("title", ""),
                        year=show_data.get("year"),
                        ids=show_data.get("ids", {}),
                        content_type="show"
                    )
            
            logger.info(f"Show with {id_type} ID '{item_id}' not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting show by {id_type} ID '{item_id}': {e}")
            return None
    
    # Add to watchlist methods
    def add_movie(self, title: str, dry_run: bool = False) -> OperationResult:
        """Add a movie to watchlist by title."""
        if not self.is_authenticated():
            return OperationResult(False, "Authentication required")
        
        if dry_run:
            return OperationResult(True, f"Dry run: Would add movie '{title}'")
        
        # Search for movie
        results = self.search_movies(title)
        if not results:
            return OperationResult(False, f"Movie '{title}' not found", None)
        
        # Use first result
        movie = results[0]
        return self._add_movie_to_watchlist(movie)
    
    def add_movie_by_id(self, item_id: Union[int, str], id_type: str = "imdb") -> OperationResult:
        """Add movie to watchlist by specific ID."""
        if not self.is_authenticated():
            return OperationResult(False, "Authentication required")
        
        movie = self.get_movie_by_id(item_id, id_type)
        if not movie:
            return OperationResult(False, f"Movie with {id_type} ID '{item_id}' not found")
        
        return self._add_movie_to_watchlist(movie)
    
    def add_show(self, title: str, dry_run: bool = False) -> OperationResult:
        """Add a TV show to watchlist by title."""
        if not self.is_authenticated():
            return OperationResult(False, "Authentication required")
        
        if dry_run:
            return OperationResult(True, f"Dry run: Would add show '{title}'")
        
        # Search for show
        results = self.search_shows(title)
        if not results:
            return OperationResult(False, f"Show '{title}' not found", None)
        
        # Use first result
        show = results[0]
        return self._add_show_to_watchlist(show)
    
    def add_movies(self, titles: List[str]) -> BatchResult:
        """Add multiple movies to watchlist."""
        successful = []
        failed = []
        
        for title in titles:
            result = self.add_movie(title)
            if result.success:
                successful.append(result)
            else:
                failed.append(result)
        
        return BatchResult(successful, failed, len(titles))
    
    def _add_movie_to_watchlist(self, movie: SearchResult) -> OperationResult:
        """Internal method to add movie to watchlist."""
        try:
            data = {
                "movies": [{
                    "title": movie.title,
                    "year": movie.year,
                    "ids": movie.ids
                }]
            }
            
            response = self.api._make_request("POST", "/sync/watchlist", data=data)
            
            if response.status_code == 201:
                result = response.json()
                added = result.get("added", {}).get("movies", 0)
                if added > 0:
                    return OperationResult(True, f"Movie '{movie.title}' added to watchlist", movie)
                else:
                    return OperationResult(True, f"Movie '{movie.title}' already in watchlist", movie)
            else:
                return OperationResult(False, f"Failed to add movie '{movie.title}'")
                
        except Exception as e:
            logger.error(f"Error adding movie to watchlist: {e}")
            return OperationResult(False, f"Error adding movie '{movie.title}': {e}")
    
    def _add_show_to_watchlist(self, show: SearchResult) -> OperationResult:
        """Internal method to add show to watchlist."""
        try:
            data = {
                "shows": [{
                    "title": show.title,
                    "year": show.year,
                    "ids": show.ids
                }]
            }
            
            response = self.api._make_request("POST", "/sync/watchlist", data=data)
            
            if response.status_code == 201:
                result = response.json()
                added = result.get("added", {}).get("shows", 0)
                if added > 0:
                    return OperationResult(True, f"Show '{show.title}' added to watchlist", show)
                else:
                    return OperationResult(True, f"Show '{show.title}' already in watchlist", show)
            else:
                return OperationResult(False, f"Failed to add show '{show.title}'")
                
        except Exception as e:
            logger.error(f"Error adding show to watchlist: {e}")
            return OperationResult(False, f"Error adding show '{show.title}': {e}")
    
    # Remove from watchlist methods
    def remove_movie(self, title: str) -> OperationResult:
        """Remove movie from watchlist by title."""
        if not self.is_authenticated():
            return OperationResult(False, "Authentication required")
        
        # Search for movie first
        results = self.search_movies(title)
        if not results:
            return OperationResult(False, f"Movie '{title}' not found")
        
        # Use first result
        movie = results[0]
        return self._remove_movie_from_watchlist(movie)
    
    def remove_movie_by_id(self, item_id: Union[int, str], id_type: str = "imdb") -> OperationResult:
        """Remove movie from watchlist by specific ID."""
        if not self.is_authenticated():
            return OperationResult(False, "Authentication required")
        
        movie = self.get_movie_by_id(item_id, id_type)
        if not movie:
            return OperationResult(False, f"Movie with {id_type} ID '{item_id}' not found")
        
        return self._remove_movie_from_watchlist(movie)
    
    def remove_show(self, title: str) -> OperationResult:
        """Remove TV show from watchlist by title."""
        if not self.is_authenticated():
            return OperationResult(False, "Authentication required")
        
        # Search for show first
        results = self.search_shows(title)
        if not results:
            return OperationResult(False, f"Show '{title}' not found")
        
        # Use first result
        show = results[0]
        return self._remove_show_from_watchlist(show)
    
    def remove_show_by_id(self, item_id: Union[int, str], id_type: str = "imdb") -> OperationResult:
        """Remove show from watchlist by specific ID."""
        if not self.is_authenticated():
            return OperationResult(False, "Authentication required")
        
        show = self.get_show_by_id(item_id, id_type)
        if not show:
            return OperationResult(False, f"Show with {id_type} ID '{item_id}' not found")
        
        return self._remove_show_from_watchlist(show)
    
    def remove_movies(self, titles: List[str]) -> BatchResult:
        """Remove multiple movies from watchlist."""
        successful = []
        failed = []
        
        for title in titles:
            result = self.remove_movie(title)
            if result.success:
                successful.append(result)
            else:
                failed.append(result)
        
        return BatchResult(successful, failed, len(titles))
    
    def remove_shows(self, titles: List[str]) -> BatchResult:
        """Remove multiple shows from watchlist."""
        successful = []
        failed = []
        
        for title in titles:
            result = self.remove_show(title)
            if result.success:
                successful.append(result)
            else:
                failed.append(result)
        
        return BatchResult(successful, failed, len(titles))
    
    def clear_watchlist(self, confirm: bool = False) -> OperationResult:
        """Clear entire watchlist (requires confirmation)."""
        if not self.is_authenticated():
            return OperationResult(False, "Authentication required")
        
        if not confirm:
            return OperationResult(False, "Confirmation required to clear entire watchlist")
        
        try:
            # Get current watchlist
            watchlist = self.get_watchlist()
            if not watchlist.items:
                return OperationResult(True, "Watchlist is already empty")
            
            # Remove all items
            movie_ids = []
            show_ids = []
            
            for item in watchlist.items:
                if item.content_type == "movie":
                    movie_ids.append({"ids": item.ids})
                else:
                    show_ids.append({"ids": item.ids})
            
            # Prepare removal data
            removal_data = {}
            if movie_ids:
                removal_data["movies"] = movie_ids
            if show_ids:
                removal_data["shows"] = show_ids
            
            if removal_data:
                response = self.api._make_request("POST", "/sync/watchlist/remove", data=removal_data)
                
                if response.status_code == 200:
                    result = response.json()
                    removed_movies = result.get("deleted", {}).get("movies", 0)
                    removed_shows = result.get("deleted", {}).get("shows", 0)
                    total_removed = removed_movies + removed_shows
                    
                    return OperationResult(True, f"Cleared {total_removed} items from watchlist")
                else:
                    return OperationResult(False, "Failed to clear watchlist")
            
            return OperationResult(True, "No items to clear")
            
        except Exception as e:
            logger.error(f"Error clearing watchlist: {e}")
            return OperationResult(False, f"Error clearing watchlist: {e}")
    
    def _remove_movie_from_watchlist(self, movie: SearchResult) -> OperationResult:
        """Internal method to remove movie from watchlist."""
        try:
            data = {
                "movies": [{
                    "title": movie.title,
                    "year": movie.year,
                    "ids": movie.ids
                }]
            }
            
            response = self.api._make_request("POST", "/sync/watchlist/remove", data=data)
            
            if response.status_code == 200:
                result = response.json()
                deleted = result.get("deleted", {}).get("movies", 0)
                if deleted > 0:
                    return OperationResult(True, f"Movie '{movie.title}' removed from watchlist", movie)
                else:
                    return OperationResult(False, f"Movie '{movie.title}' was not in watchlist", movie)
            else:
                return OperationResult(False, f"Failed to remove movie '{movie.title}'")
                
        except Exception as e:
            logger.error(f"Error removing movie from watchlist: {e}")
            return OperationResult(False, f"Error removing movie '{movie.title}': {e}")
    
    def _remove_show_from_watchlist(self, show: SearchResult) -> OperationResult:
        """Internal method to remove show from watchlist."""
        try:
            data = {
                "shows": [{
                    "title": show.title,
                    "year": show.year,
                    "ids": show.ids
                }]
            }
            
            response = self.api._make_request("POST", "/sync/watchlist/remove", data=data)
            
            if response.status_code == 200:
                result = response.json()
                deleted = result.get("deleted", {}).get("shows", 0)
                if deleted > 0:
                    return OperationResult(True, f"Show '{show.title}' removed from watchlist", show)
                else:
                    return OperationResult(False, f"Show '{show.title}' was not in watchlist", show)
            else:
                return OperationResult(False, f"Failed to remove show '{show.title}'")
                
        except Exception as e:
            logger.error(f"Error removing show from watchlist: {e}")
            return OperationResult(False, f"Error removing show '{show.title}': {e}")
    
    # Watchlist retrieval methods
    def get_watchlist(
        self,
        content_type: Optional[str] = None,
        sort_by: str = "added",
        limit: Optional[int] = None
    ) -> Watchlist:
        """Get user's watchlist."""
        if not self.is_authenticated():
            raise AuthenticationError("Authentication required to get watchlist")
        
        try:
            response = self.api._make_request("GET", "/sync/watchlist")
            
            if response.status_code == 200:
                data = response.json()
                items = []
                
                for entry in data:
                    # Parse different entry types
                    item_data = None
                    entry_type = None
                    
                    if "movie" in entry:
                        item_data = entry["movie"]
                        entry_type = "movie"
                    elif "show" in entry:
                        item_data = entry["show"]
                        entry_type = "show"
                    
                    if item_data and entry_type:
                        # Filter by content type if specified
                        if content_type and entry_type != content_type:
                            continue
                        
                        # Parse added date
                        added_at = datetime.now()  # Default fallback
                        if "listed_at" in entry:
                            try:
                                added_at = datetime.fromisoformat(entry["listed_at"].replace('Z', '+00:00'))
                            except ValueError:
                                pass
                        
                        watchlist_item = WatchlistItem(
                            title=item_data.get("title", ""),
                            year=item_data.get("year"),
                            content_type=entry_type,
                            ids=item_data.get("ids", {}),
                            added_at=added_at
                        )
                        
                        items.append(watchlist_item)
                
                # Sort items
                if sort_by == "added":
                    items.sort(key=lambda x: x.added_at, reverse=True)
                elif sort_by == "title":
                    items.sort(key=lambda x: x.title.lower())
                elif sort_by == "year":
                    items.sort(key=lambda x: x.year or 0, reverse=True)
                
                # Apply limit
                if limit and limit > 0:
                    items = items[:limit]
                
                logger.info(f"Retrieved {len(items)} items from watchlist")
                return Watchlist(items)
            else:
                logger.error(f"Failed to get watchlist: {response.status_code}")
                return Watchlist()
                
        except Exception as e:
            logger.error(f"Error getting watchlist: {e}")
            return Watchlist()
    
    def get_movies(self, sort_by: str = "added", limit: Optional[int] = None) -> Watchlist:
        """Get only movies from watchlist."""
        return self.get_watchlist(content_type="movie", sort_by=sort_by, limit=limit)
    
    def get_shows(self, sort_by: str = "added", limit: Optional[int] = None) -> Watchlist:
        """Get only shows from watchlist."""
        return self.get_watchlist(content_type="show", sort_by=sort_by, limit=limit)
    
    # Additional utility methods to reach 25+ public methods
    def add_show_by_id(self, item_id: Union[int, str], id_type: str = "imdb") -> OperationResult:
        """Add show to watchlist by specific ID."""
        if not self.is_authenticated():
            return OperationResult(False, "Authentication required")
        
        show = self.get_show_by_id(item_id, id_type)
        if not show:
            return OperationResult(False, f"Show with {id_type} ID '{item_id}' not found")
        
        return self._add_show_to_watchlist(show)
    
    def add_shows(self, titles: List[str]) -> BatchResult:
        """Add multiple shows to watchlist."""
        successful = []
        failed = []
        
        for title in titles:
            result = self.add_show(title)
            if result.success:
                successful.append(result)
            else:
                failed.append(result)
        
        return BatchResult(successful, failed, len(titles))
    
    def search_by_year(self, year: int, content_type: Optional[str] = None) -> List[SearchResult]:
        """Search for content by year."""
        # This is a simplified implementation - real implementation would use proper year search
        return self.search(str(year), content_type=content_type, year=year)
    
    def get_watchlist_stats(self) -> Dict[str, Any]:
        """Get statistics about the user's watchlist."""
        if not self.is_authenticated():
            raise AuthenticationError("Authentication required")
        
        watchlist = self.get_watchlist()
        
        movies = [item for item in watchlist.items if item.content_type == "movie"]
        shows = [item for item in watchlist.items if item.content_type == "show"]
        
        # Calculate year distribution
        years = [item.year for item in watchlist.items if item.year]
        year_counts = {}
        for year in years:
            year_counts[year] = year_counts.get(year, 0) + 1
        
        return {
            "total_items": len(watchlist.items),
            "movies": len(movies),
            "shows": len(shows),
            "oldest_year": min(years) if years else None,
            "newest_year": max(years) if years else None,
            "year_distribution": year_counts,
            "last_updated": datetime.now().isoformat()
        }
    
    def validate_watchlist(self) -> Dict[str, Any]:
        """Validate all items in watchlist and report any issues."""
        if not self.is_authenticated():
            raise AuthenticationError("Authentication required")
        
        watchlist = self.get_watchlist()
        valid_items = []
        invalid_items = []
        
        for item in watchlist.items:
            # Basic validation
            issues = []
            if not item.title:
                issues.append("Missing title")
            if not item.ids:
                issues.append("Missing IDs")
            if item.content_type not in ("movie", "show"):
                issues.append("Invalid content type")
            
            if issues:
                invalid_items.append({
                    "item": item.to_dict(),
                    "issues": issues
                })
            else:
                valid_items.append(item.to_dict())
        
        return {
            "total_items": len(watchlist.items),
            "valid_items": len(valid_items),
            "invalid_items": len(invalid_items),
            "validation_errors": invalid_items,
            "validation_date": datetime.now().isoformat()
        }
    
    def export_watchlist(self, format_type: str = "json") -> str:
        """Export watchlist in various formats."""
        if not self.is_authenticated():
            raise AuthenticationError("Authentication required")
        
        watchlist = self.get_watchlist()
        
        if format_type.lower() == "json":
            return watchlist.to_json()
        elif format_type.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["title", "year", "content_type", "trakt_id", "imdb_id", "added_at"])
            
            # Write data
            for item in watchlist.items:
                writer.writerow([
                    item.title,
                    item.year or "",
                    item.content_type,
                    item.ids.get("trakt", ""),
                    item.ids.get("imdb", ""),
                    item.added_at.isoformat()
                ])
            
            return output.getvalue()
        else:
            raise ValidationError(f"Unsupported export format: {format_type}")
    
    def search_watchlist(self, query: str) -> List[WatchlistItem]:
        """Search within the user's watchlist."""
        if not self.is_authenticated():
            raise AuthenticationError("Authentication required")
        
        watchlist = self.get_watchlist()
        query_lower = query.lower()
        
        matching_items = []
        for item in watchlist.items:
            if query_lower in item.title.lower():
                matching_items.append(item)
        
        return matching_items
    
    def get_recommendations(self, content_type: Optional[str] = None, limit: int = 10) -> List[SearchResult]:
        """Get recommended content based on watchlist (placeholder implementation)."""
        if not self.is_authenticated():
            raise AuthenticationError("Authentication required")
        
        # This is a placeholder - real implementation would use Trakt's recommendation API
        logger.warning("get_recommendations is a placeholder implementation")
        return []
    
    def sync_progress(self) -> Dict[str, Any]:
        """Get sync progress and status information."""
        if not self.is_authenticated():
            raise AuthenticationError("Authentication required")
        
        try:
            # Get last activity
            response = self.api._make_request("GET", "/sync/last_activities")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to get sync progress: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting sync progress: {e}")
            return {"error": str(e)}
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get authenticated user's profile information."""
        if not self.is_authenticated():
            raise AuthenticationError("Authentication required")
        
        try:
            response = self.api._make_request("GET", "/users/me")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to get user profile: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {"error": str(e)}
    
    def get_trending(self, content_type: str = "movies", limit: int = 10) -> List[SearchResult]:
        """Get trending movies or shows."""
        try:
            endpoint = f"/movies/trending" if content_type == "movies" else "/shows/trending"
            params = {"limit": str(limit)}
            
            response = self.api._make_request("GET", endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for entry in data:
                    item_data = entry.get("movie" if content_type == "movies" else "show", {})
                    if item_data:
                        results.append(SearchResult(
                            title=item_data.get("title", ""),
                            year=item_data.get("year"),
                            ids=item_data.get("ids", {}),
                            content_type="movie" if content_type == "movies" else "show"
                        ))
                
                return results
            else:
                logger.error(f"Failed to get trending {content_type}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting trending {content_type}: {e}")
            return []
    
    def get_popular(self, content_type: str = "movies", limit: int = 10) -> List[SearchResult]:
        """Get popular movies or shows."""
        try:
            endpoint = f"/movies/popular" if content_type == "movies" else "/shows/popular"
            params = {"limit": str(limit)}
            
            response = self.api._make_request("GET", endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item_data in data:
                    if item_data:
                        results.append(SearchResult(
                            title=item_data.get("title", ""),
                            year=item_data.get("year"),
                            ids=item_data.get("ids", {}),
                            content_type="movie" if content_type == "movies" else "show"
                        ))
                
                return results
            else:
                logger.error(f"Failed to get popular {content_type}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting popular {content_type}: {e}")
            return []