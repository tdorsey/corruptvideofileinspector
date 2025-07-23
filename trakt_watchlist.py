"""
Trakt.tv Watchlist Management Library

A comprehensive Python library for managing Trakt.tv watchlists with simplified
interface, automatic authentication management, and built-in error handling.

This library provides high-level methods to add and remove movies and TV shows
from user watchlists with minimal boilerplate code, abstracting the complexity
of the trakt.py library.
"""

import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Union

import requests

# Configure module logger
logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================


class TraktWatchlistError(Exception):
    """Base exception for library errors"""



class AuthenticationError(TraktWatchlistError):
    """Authentication-related errors"""



class APIError(TraktWatchlistError):
    """API communication errors"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class NotFoundError(TraktWatchlistError):
    """Item not found errors"""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.suggestions = suggestions or []


class ValidationError(TraktWatchlistError):
    """Data validation errors"""



# ============================================================================
# Token Storage Interface
# ============================================================================


class TokenStorage(ABC):
    """Abstract base class for token storage backends"""

    @abstractmethod
    def save_tokens(self, tokens: Dict[str, str]) -> None:
        """Save authentication tokens"""

    @abstractmethod
    def load_tokens(self) -> Dict[str, str]:
        """Load authentication tokens"""


class MemoryTokenStorage(TokenStorage):
    """In-memory token storage (default, not persistent)"""

    def __init__(self) -> None:
        self._tokens: Dict[str, str] = {}

    def save_tokens(self, tokens: Dict[str, str]) -> None:
        """Save tokens to memory"""
        self._tokens = tokens.copy()

    def load_tokens(self) -> Dict[str, str]:
        """Load tokens from memory"""
        return self._tokens.copy()


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class WatchlistItem:
    """Represents an item in a watchlist"""

    title: str
    year: Optional[int] = None
    content_type: str = "movie"  # "movie" or "show"
    ids: Dict[str, Union[int, str]] = field(default_factory=dict)
    added_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate and clean up watchlist item data"""
        if self.content_type not in ["movie", "show"]:
            raise ValidationError(f"Invalid content_type: {self.content_type}")


@dataclass
class SearchResult:
    """Represents a search result item"""

    title: str
    year: Optional[int] = None
    content_type: str = "movie"  # "movie" or "show"
    ids: Dict[str, Union[int, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate search result data"""
        if self.content_type not in ["movie", "show"]:
            raise ValidationError(f"Invalid content_type: {self.content_type}")


@dataclass
class OperationResult:
    """Result of add/remove operations"""

    success: bool
    message: str
    item: Optional[SearchResult] = None


@dataclass
class BatchResult:
    """Result of batch operations"""

    successful: List[OperationResult]
    failed: List[OperationResult]
    total: int

    @property
    def success_count(self) -> int:
        """Number of successful operations"""
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        """Number of failed operations"""
        return len(self.failed)

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage"""
        if self.total == 0:
            return 0.0
        return (self.success_count / self.total) * 100.0


class Watchlist:
    """Collection of watchlist items with export capabilities"""

    def __init__(self, items: List[WatchlistItem]) -> None:
        self.items = items

    def to_dict(self) -> Dict[str, Any]:
        """Export watchlist to dictionary"""
        return {
            "items": [
                {
                    "title": item.title,
                    "year": item.year,
                    "content_type": item.content_type,
                    "ids": item.ids,
                    "added_at": item.added_at.isoformat() if item.added_at else None,
                }
                for item in self.items
            ],
            "total_count": len(self.items),
        }

    def to_json(self) -> str:
        """Export watchlist to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    def filter_by_type(self, content_type: str) -> "Watchlist":
        """Filter watchlist by content type"""
        filtered_items = [item for item in self.items if item.content_type == content_type]
        return Watchlist(filtered_items)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)


# Legacy data classes for backward compatibility
@dataclass
class MediaItem:
    """Represents a parsed media item (movie or TV show)"""

    title: str
    year: Optional[int] = None
    media_type: str = "movie"  # "movie" or "show"
    season: Optional[int] = None
    episode: Optional[int] = None
    original_filename: str = ""

    def __post_init__(self) -> None:
        """Validate and clean up media item data"""
        # Clean up title (remove dots, underscores, etc.)
        self.title = re.sub(r"[._]", " ", self.title).strip()
        self.title = re.sub(r"\s+", " ", self.title)  # Normalize whitespace

        # Ensure media_type is valid
        if self.media_type not in ["movie", "show"]:
            self.media_type = "movie"

        logger.debug(f"MediaItem created: {self.title} ({self.year}) - {self.media_type}")

    def to_search_result(self) -> SearchResult:
        """Convert to SearchResult for compatibility"""
        return SearchResult(
            title=self.title,
            year=self.year,
            content_type=self.media_type,
        )


@dataclass
class TraktItem:
    """Represents an item from Trakt API with identifiers"""

    title: str
    year: Optional[int]
    media_type: str
    trakt_id: Optional[int] = None
    imdb_id: Optional[str] = None
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None

    @classmethod
    def from_movie_response(cls, data: Dict[str, Any]) -> "TraktItem":
        """Create TraktItem from Trakt movie API response"""
        ids = data.get("ids", {})
        return cls(
            title=data.get("title", ""),
            year=data.get("year"),
            media_type="movie",
            trakt_id=ids.get("trakt"),
            imdb_id=ids.get("imdb"),
            tmdb_id=ids.get("tmdb"),
        )

    @classmethod
    def from_show_response(cls, data: Dict[str, Any]) -> "TraktItem":
        """Create TraktItem from Trakt show API response"""
        ids = data.get("ids", {})
        return cls(
            title=data.get("title", ""),
            year=data.get("year"),
            media_type="show",
            trakt_id=ids.get("trakt"),
            imdb_id=ids.get("imdb"),
            tmdb_id=ids.get("tmdb"),
            tvdb_id=ids.get("tvdb"),
        )

    def to_search_result(self) -> SearchResult:
        """Convert to SearchResult"""
        return SearchResult(
            title=self.title,
            year=self.year,
            content_type=self.media_type,
            ids={
                "trakt": self.trakt_id,
                "imdb": self.imdb_id,
                "tmdb": self.tmdb_id,
                "tvdb": self.tvdb_id,
            },
        )


# ============================================================================
# Main WatchlistManager Class
# ============================================================================


class WatchlistManager:
    """
    Main interface for Trakt.tv watchlist management

    Provides simplified methods for managing Trakt.tv watchlists with automatic
    authentication, error handling, and retry logic.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_storage: Optional[TokenStorage] = None,
    ):
        """
        Initialize WatchlistManager with credentials

        Args:
            client_id: Trakt.tv API client ID (or from TRAKT_CLIENT_ID env var)
            client_secret: Trakt.tv API client secret (or from TRAKT_CLIENT_SECRET env var)
            access_token: OAuth access token (optional if using OAuth flow)
            refresh_token: OAuth refresh token (optional)
            token_storage: Custom token storage backend (default: MemoryTokenStorage)

        Raises:
            AuthenticationError: If credentials are missing or invalid
        """
        # Get credentials from environment if not provided
        self.client_id = client_id or os.getenv("TRAKT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("TRAKT_CLIENT_SECRET")

        if not self.client_id:
            raise AuthenticationError("client_id is required (provide directly or set TRAKT_CLIENT_ID)")

        # Set up token storage
        self.token_storage = token_storage or MemoryTokenStorage()

        # Store tokens if provided
        if access_token:
            tokens = {"access_token": access_token}
            if refresh_token:
                tokens["refresh_token"] = refresh_token
            self.token_storage.save_tokens(tokens)

        # Initialize API client
        self._api = TraktAPI(self.client_id, self.client_secret, self.token_storage)

        logger.info("WatchlistManager initialized")

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated

        Returns:
            bool: True if valid access token is available
        """
        return self._api.is_authenticated()

    def get_auth_url(self) -> str:
        """
        Get OAuth authorization URL for web flow

        Returns:
            str: Authorization URL for user to visit
        """
        return self._api.get_auth_url()

    def exchange_code(self, auth_code: str) -> bool:
        """
        Exchange authorization code for access tokens

        Args:
            auth_code: Authorization code from OAuth callback

        Returns:
            bool: True if token exchange was successful

        Raises:
            AuthenticationError: If token exchange fails
        """
        return self._api.exchange_code(auth_code)

    def refresh_tokens(self) -> bool:
        """
        Manually refresh access tokens

        Returns:
            bool: True if refresh was successful
        """
        return self._api.refresh_tokens()

    # Search functionality
    def search(self, query: str, content_type: Optional[str] = None,
               year: Optional[int] = None, limit: int = 10) -> List[SearchResult]:
        """
        Search for movies and TV shows

        Args:
            query: Search query (title)
            content_type: Filter by "movie" or "show" (optional)
            year: Filter by year (optional)
            limit: Maximum results to return

        Returns:
            List[SearchResult]: List of matching results
        """
        results = []

        if content_type is None or content_type == "movie":
            movie_results = self.search_movies(query, year=year, limit=limit)
            results.extend(movie_results)

        if content_type is None or content_type == "show":
            show_limit = limit - len(results) if content_type is None else limit
            if show_limit > 0:
                show_results = self.search_shows(query, year=year, limit=show_limit)
                results.extend(show_results)

        return results[:limit]

    def search_movies(self, title: str, year: Optional[int] = None, limit: int = 10) -> List[SearchResult]:
        """
        Search for movies

        Args:
            title: Movie title to search for
            year: Optional release year for better matching
            limit: Maximum number of results to return

        Returns:
            List[SearchResult]: List of matching movie results
        """
        trakt_items = self._api.search_movie(title, year, limit)
        return [item.to_search_result() for item in trakt_items]

    def search_shows(self, title: str, year: Optional[int] = None, limit: int = 10) -> List[SearchResult]:
        """
        Search for TV shows

        Args:
            title: Show title to search for
            year: Optional first air year for better matching
            limit: Maximum number of results to return

        Returns:
            List[SearchResult]: List of matching show results
        """
        trakt_items = self._api.search_show(title, year, limit)
        return [item.to_search_result() for item in trakt_items]

    def get_movie_by_id(self, id_value: Union[int, str], id_type: str = "trakt") -> Optional[SearchResult]:
        """
        Get movie by specific ID

        Args:
            id_value: ID value to search for
            id_type: Type of ID ("trakt", "imdb", "tmdb")

        Returns:
            SearchResult: Movie details if found, None otherwise
        """
        trakt_item = self._api.get_movie_by_id(id_value, id_type)
        return trakt_item.to_search_result() if trakt_item else None

    def get_show_by_id(self, id_value: Union[int, str], id_type: str = "trakt") -> Optional[SearchResult]:
        """
        Get TV show by specific ID

        Args:
            id_value: ID value to search for
            id_type: Type of ID ("trakt", "imdb", "tmdb", "tvdb")

        Returns:
            SearchResult: Show details if found, None otherwise
        """
        trakt_item = self._api.get_show_by_id(id_value, id_type)
        return trakt_item.to_search_result() if trakt_item else None

    # Add operations
    def add_movie(self, title: str, year: Optional[int] = None, dry_run: bool = False) -> OperationResult:
        """
        Add movie to watchlist by title

        Args:
            title: Movie title
            year: Optional release year for better matching
            dry_run: If True, validate but don't actually add

        Returns:
            OperationResult: Result of the operation
        """
        # Search for the movie
        results = self.search_movies(title, year, limit=1)
        if not results:
            return OperationResult(
                success=False,
                message=f"Movie not found: {title}",
            )

        result = results[0]
        if dry_run:
            return OperationResult(
                success=True,
                message=f"Would add movie: {result.title} ({result.year})",
                item=result,
            )

        return self.add_movie_by_id(result.ids.get("trakt", 0), "trakt")

    def add_movie_by_id(self, id_value: Union[int, str], id_type: str = "trakt") -> OperationResult:
        """
        Add movie to watchlist by ID

        Args:
            id_value: Movie ID
            id_type: Type of ID ("trakt", "imdb", "tmdb")

        Returns:
            OperationResult: Result of the operation
        """
        # Get movie details
        movie = self.get_movie_by_id(id_value, id_type)
        if not movie:
            return OperationResult(
                success=False,
                message=f"Movie not found with {id_type} ID: {id_value}",
            )

        # Create TraktItem for API call
        trakt_item = TraktItem(
            title=movie.title,
            year=movie.year,
            media_type="movie",
            trakt_id=movie.ids.get("trakt"),
            imdb_id=movie.ids.get("imdb"),
            tmdb_id=movie.ids.get("tmdb"),
        )

        success = self._api.add_movie_to_watchlist(trakt_item)
        return OperationResult(
            success=success,
            message=f"Added movie to watchlist: {movie.title}" if success else f"Failed to add movie: {movie.title}",
            item=movie,
        )

    def add_show(self, title: str, year: Optional[int] = None, dry_run: bool = False) -> OperationResult:
        """
        Add TV show to watchlist by title

        Args:
            title: Show title
            year: Optional first air year for better matching
            dry_run: If True, validate but don't actually add

        Returns:
            OperationResult: Result of the operation
        """
        # Search for the show
        results = self.search_shows(title, year, limit=1)
        if not results:
            return OperationResult(
                success=False,
                message=f"Show not found: {title}",
            )

        result = results[0]
        if dry_run:
            return OperationResult(
                success=True,
                message=f"Would add show: {result.title} ({result.year})",
                item=result,
            )

        return self.add_show_by_id(result.ids.get("trakt", 0), "trakt")

    def add_show_by_id(self, id_value: Union[int, str], id_type: str = "trakt") -> OperationResult:
        """
        Add TV show to watchlist by ID

        Args:
            id_value: Show ID
            id_type: Type of ID ("trakt", "imdb", "tmdb", "tvdb")

        Returns:
            OperationResult: Result of the operation
        """
        # Get show details
        show = self.get_show_by_id(id_value, id_type)
        if not show:
            return OperationResult(
                success=False,
                message=f"Show not found with {id_type} ID: {id_value}",
            )

        # Create TraktItem for API call
        trakt_item = TraktItem(
            title=show.title,
            year=show.year,
            media_type="show",
            trakt_id=show.ids.get("trakt"),
            imdb_id=show.ids.get("imdb"),
            tmdb_id=show.ids.get("tmdb"),
            tvdb_id=show.ids.get("tvdb"),
        )

        success = self._api.add_show_to_watchlist(trakt_item)
        return OperationResult(
            success=success,
            message=f"Added show to watchlist: {show.title}" if success else f"Failed to add show: {show.title}",
            item=show,
        )

    def add_movies(self, titles: List[str]) -> BatchResult:
        """
        Add multiple movies to watchlist

        Args:
            titles: List of movie titles to add

        Returns:
            BatchResult: Results of batch operation
        """
        successful = []
        failed = []

        for title in titles:
            result = self.add_movie(title)
            if result.success:
                successful.append(result)
            else:
                failed.append(result)

        return BatchResult(
            successful=successful,
            failed=failed,
            total=len(titles),
        )

    def add_shows(self, titles: List[str]) -> BatchResult:
        """
        Add multiple TV shows to watchlist

        Args:
            titles: List of show titles to add

        Returns:
            BatchResult: Results of batch operation
        """
        successful = []
        failed = []

        for title in titles:
            result = self.add_show(title)
            if result.success:
                successful.append(result)
            else:
                failed.append(result)

        return BatchResult(
            successful=successful,
            failed=failed,
            total=len(titles),
        )

    # Remove operations
    def remove_movie(self, title: str, year: Optional[int] = None) -> OperationResult:
        """
        Remove movie from watchlist by title

        Args:
            title: Movie title
            year: Optional release year for better matching

        Returns:
            OperationResult: Result of the operation
        """
        # Search for the movie
        results = self.search_movies(title, year, limit=1)
        if not results:
            return OperationResult(
                success=False,
                message=f"Movie not found: {title}",
            )

        result = results[0]
        return self.remove_movie_by_id(result.ids.get("trakt", 0), "trakt")

    def remove_movie_by_id(self, id_value: Union[int, str], id_type: str = "trakt") -> OperationResult:
        """
        Remove movie from watchlist by ID

        Args:
            id_value: Movie ID
            id_type: Type of ID ("trakt", "imdb", "tmdb")

        Returns:
            OperationResult: Result of the operation
        """
        # Get movie details
        movie = self.get_movie_by_id(id_value, id_type)
        if not movie:
            return OperationResult(
                success=False,
                message=f"Movie not found with {id_type} ID: {id_value}",
            )

        # Create TraktItem for API call
        trakt_item = TraktItem(
            title=movie.title,
            year=movie.year,
            media_type="movie",
            trakt_id=movie.ids.get("trakt"),
            imdb_id=movie.ids.get("imdb"),
            tmdb_id=movie.ids.get("tmdb"),
        )

        success = self._api.remove_movie_from_watchlist(trakt_item)
        return OperationResult(
            success=success,
            message=f"Removed movie from watchlist: {movie.title}" if success else f"Failed to remove movie: {movie.title}",
            item=movie,
        )

    def remove_show(self, title: str, year: Optional[int] = None) -> OperationResult:
        """
        Remove TV show from watchlist by title

        Args:
            title: Show title
            year: Optional first air year for better matching

        Returns:
            OperationResult: Result of the operation
        """
        # Search for the show
        results = self.search_shows(title, year, limit=1)
        if not results:
            return OperationResult(
                success=False,
                message=f"Show not found: {title}",
            )

        result = results[0]
        return self.remove_show_by_id(result.ids.get("trakt", 0), "trakt")

    def remove_show_by_id(self, id_value: Union[int, str], id_type: str = "trakt") -> OperationResult:
        """
        Remove TV show from watchlist by ID

        Args:
            id_value: Show ID
            id_type: Type of ID ("trakt", "imdb", "tmdb", "tvdb")

        Returns:
            OperationResult: Result of the operation
        """
        # Get show details
        show = self.get_show_by_id(id_value, id_type)
        if not show:
            return OperationResult(
                success=False,
                message=f"Show not found with {id_type} ID: {id_value}",
            )

        # Create TraktItem for API call
        trakt_item = TraktItem(
            title=show.title,
            year=show.year,
            media_type="show",
            trakt_id=show.ids.get("trakt"),
            imdb_id=show.ids.get("imdb"),
            tmdb_id=show.ids.get("tmdb"),
            tvdb_id=show.ids.get("tvdb"),
        )

        success = self._api.remove_show_from_watchlist(trakt_item)
        return OperationResult(
            success=success,
            message=f"Removed show from watchlist: {show.title}" if success else f"Failed to remove show: {show.title}",
            item=show,
        )

    def remove_movies(self, titles: List[str]) -> BatchResult:
        """
        Remove multiple movies from watchlist

        Args:
            titles: List of movie titles to remove

        Returns:
            BatchResult: Results of batch operation
        """
        successful = []
        failed = []

        for title in titles:
            result = self.remove_movie(title)
            if result.success:
                successful.append(result)
            else:
                failed.append(result)

        return BatchResult(
            successful=successful,
            failed=failed,
            total=len(titles),
        )

    def remove_shows(self, titles: List[str]) -> BatchResult:
        """
        Remove multiple TV shows from watchlist

        Args:
            titles: List of show titles to remove

        Returns:
            BatchResult: Results of batch operation
        """
        successful = []
        failed = []

        for title in titles:
            result = self.remove_show(title)
            if result.success:
                successful.append(result)
            else:
                failed.append(result)

        return BatchResult(
            successful=successful,
            failed=failed,
            total=len(titles),
        )

    def clear_watchlist(self, confirm: bool = False) -> OperationResult:
        """
        Clear entire watchlist (destructive operation)

        Args:
            confirm: Must be True to proceed with clearing

        Returns:
            OperationResult: Result of the operation
        """
        if not confirm:
            return OperationResult(
                success=False,
                message="Confirmation required to clear watchlist (set confirm=True)",
            )

        # This would require getting current watchlist and removing all items
        # For now, return not implemented
        return OperationResult(
            success=False,
            message="Clear watchlist not yet implemented",
        )

    # Watchlist retrieval
    def get_watchlist(
        self,
        content_type: Optional[str] = None,
        sort_by: str = "added",
        limit: Optional[int] = None,
    ) -> Watchlist:
        """
        Get user's watchlist

        Args:
            content_type: Filter by "movie" or "show" (optional)
            sort_by: Sort criteria ("added", "title", "year")
            limit: Maximum number of items to return

        Returns:
            Watchlist: User's watchlist items
        """
        items = self._api.get_watchlist(content_type, sort_by, limit)
        return Watchlist(items)

    def get_movies(self, sort_by: str = "added", limit: Optional[int] = None) -> Watchlist:
        """
        Get movies from watchlist

        Args:
            sort_by: Sort criteria ("added", "title", "year")
            limit: Maximum number of items to return

        Returns:
            Watchlist: Movie items from watchlist
        """
        return self.get_watchlist(content_type="movie", sort_by=sort_by, limit=limit)

    def get_shows(self, sort_by: str = "added", limit: Optional[int] = None) -> Watchlist:
        """
        Get TV shows from watchlist

        Args:
            sort_by: Sort criteria ("added", "title", "year")
            limit: Maximum number of items to return

        Returns:
            Watchlist: Show items from watchlist
        """
        return self.get_watchlist(content_type="show", sort_by=sort_by, limit=limit)


# ============================================================================
# Enhanced TraktAPI Class
# ============================================================================



class TraktAPI:
    """Enhanced Trakt.tv API client for watchlist management"""

    BASE_URL = "https://api.trakt.tv"
    API_VERSION = "2"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_storage: TokenStorage,
    ):
        """
        Initialize Trakt API client

        Args:
            client_id: Trakt.tv API client ID
            client_secret: Trakt.tv API client secret
            token_storage: Token storage backend
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_storage = token_storage
        self.session = requests.Session()

        # Set up default headers
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "trakt-api-version": self.API_VERSION,
                "trakt-api-key": client_id,
            }
        )

        # Load existing tokens
        self._update_auth_header()

        logger.info("TraktAPI client initialized")

    def _update_auth_header(self) -> None:
        """Update authorization header with current access token"""
        tokens = self.token_storage.load_tokens()
        access_token = tokens.get("access_token")

        if access_token:
            self.session.headers["Authorization"] = f"Bearer {access_token}"
        elif "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid access token"""
        tokens = self.token_storage.load_tokens()
        access_token = tokens.get("access_token")

        if not access_token:
            return False

        # Test the token with a simple API call
        try:
            response = self._make_request("GET", "/users/settings")
            return response.status_code == 200
        except Exception:
            logger.debug("Authentication check failed")
            return False

    def get_auth_url(self) -> str:
        """Get OAuth authorization URL"""
        return f"https://trakt.tv/oauth/authorize?response_type=code&client_id={self.client_id}&redirect_uri=urn:ietf:wg:oauth:2.0:oob"

    def exchange_code(self, auth_code: str) -> bool:
        """
        Exchange authorization code for access tokens

        Args:
            auth_code: Authorization code from OAuth callback

        Returns:
            bool: True if successful

        Raises:
            AuthenticationError: If exchange fails
        """
        data = {
            "code": auth_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
            "grant_type": "authorization_code",
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/oauth/token",
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                tokens = response.json()
                self.token_storage.save_tokens(tokens)
                self._update_auth_header()
                logger.info("Successfully exchanged authorization code for tokens")
                return True
            error_msg = f"Token exchange failed: {response.status_code}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg)

        except requests.RequestException as e:
            error_msg = f"Token exchange request failed: {e}"
            logger.exception(error_msg)
            raise AuthenticationError(error_msg) from e

    def refresh_tokens(self) -> bool:
        """
        Refresh access tokens using refresh token

        Returns:
            bool: True if successful
        """
        tokens = self.token_storage.load_tokens()
        refresh_token = tokens.get("refresh_token")

        if not refresh_token:
            logger.error("No refresh token available")
            return False

        data = {
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
            "grant_type": "refresh_token",
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/oauth/token",
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                new_tokens = response.json()
                self.token_storage.save_tokens(new_tokens)
                self._update_auth_header()
                logger.info("Successfully refreshed access tokens")
                return True
            logger.error(f"Token refresh failed: {response.status_code}")
            return False

        except requests.RequestException as e:
            logger.exception(f"Token refresh request failed: {e}")
            return False

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> requests.Response:
        """
        Make authenticated request to Trakt API with retry logic

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: JSON data for POST requests
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            requests.Response: API response

        Raises:
            APIError: If request fails after retries
            AuthenticationError: If authentication fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        max_retries = 3
        base_delay = 1

        logger.debug(f"Making {method} request to {url}")

        try:
            response = self.session.request(
                method=method, url=url, json=data, params=params, timeout=30
            )

            logger.debug(f"Response status: {response.status_code}")

            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                if retry_count >= max_retries:
                    raise APIError("Rate limit exceeded after maximum retries", 429)

                retry_after = int(response.headers.get("Retry-After", base_delay * (2 ** retry_count)))
                logger.warning(f"Rate limited, waiting {retry_after} seconds (attempt {retry_count + 1})")
                time.sleep(retry_after)

                return self._make_request(method, endpoint, data, params, retry_count + 1)

            # Handle authentication errors
            if response.status_code == 401:
                # Try to refresh tokens once
                if retry_count == 0 and self.refresh_tokens():
                    logger.info("Refreshed tokens, retrying request")
                    return self._make_request(method, endpoint, data, params, retry_count + 1)
                raise AuthenticationError("Authentication failed - check your access token")

            # Handle other errors with retry
            if response.status_code >= 500 and retry_count < max_retries:
                delay = base_delay * (2 ** retry_count)
                logger.warning(f"Server error {response.status_code}, retrying in {delay}s (attempt {retry_count + 1})")
                time.sleep(delay)
                return self._make_request(method, endpoint, data, params, retry_count + 1)

            return response

        except requests.RequestException as e:
            if retry_count < max_retries:
                delay = base_delay * (2 ** retry_count)
                logger.warning(f"Request failed, retrying in {delay}s: {e}")
                time.sleep(delay)
                return self._make_request(method, endpoint, data, params, retry_count + 1)
            logger.exception(f"Request failed after {max_retries} retries: {e}")
            raise APIError(f"Request failed: {e}") from e

    def search_movie(
        self, title: str, year: Optional[int] = None, limit: int = 10
    ) -> List[TraktItem]:
        """
        Search for movies on Trakt

        Args:
            title: Movie title to search for
            year: Optional release year for better matching
            limit: Maximum number of results to return

        Returns:
            List[TraktItem]: List of matching movie results
        """
        params = {"query": title, "limit": str(limit)}
        if year:
            params["year"] = str(year)

        logger.info(f"Searching for movie: {title} ({year})")

        try:
            response = self._make_request("GET", "/search/movie", params=params)
        except Exception as e:
            logger.exception(f"Error searching for movie: {e}")
            return []

        if response.status_code == 200:
            results = response.json()
            trakt_items: List[TraktItem] = []

            for result in results:
                movie_data = result.get("movie", {})
                if not movie_data:
                    continue

                trakt_item = TraktItem.from_movie_response(movie_data)

                # Filter by year if specified
                if year is not None and trakt_item.year != year:
                    logger.debug(f"Skipping movie with different year: {trakt_item.title} ({trakt_item.year}) != {year}")
                    continue

                trakt_items.append(trakt_item)
                logger.debug(f"Found movie: {trakt_item.title} ({trakt_item.year})")

            logger.info(f"Found {len(trakt_items)} movie results for: {title}")
            return trakt_items

        logger.warning(f"Movie search failed with status {response.status_code}")
        return []

    def search_show(
        self, title: str, year: Optional[int] = None, limit: int = 10
    ) -> List[TraktItem]:
        """
        Search for TV shows on Trakt

        Args:
            title: Show title to search for
            year: Optional first air year for better matching
            limit: Maximum number of results to return

        Returns:
            List[TraktItem]: List of matching show results
        """
        params = {"query": title, "limit": str(limit)}
        if year:
            params["year"] = str(year)

        logger.info(f"Searching for TV show: {title} ({year})")

        try:
            response = self._make_request("GET", "/search/show", params=params)
        except Exception as e:
            logger.exception(f"Error searching for show: {e}")
            return []

        if response.status_code == 200:
            results = response.json()
            trakt_items: List[TraktItem] = []

            for result in results:
                show_data = result.get("show", {})
                if not show_data:
                    continue

                trakt_item = TraktItem.from_show_response(show_data)

                # Filter by year if specified
                if year is not None and trakt_item.year != year:
                    logger.debug(f"Skipping show with different year: {trakt_item.title} ({trakt_item.year}) != {year}")
                    continue

                trakt_items.append(trakt_item)
                logger.debug(f"Found show: {trakt_item.title} ({trakt_item.year})")

            logger.info(f"Found {len(trakt_items)} show results for: {title}")
            return trakt_items

        logger.warning(f"Show search failed with status {response.status_code}")
        return []

    def get_movie_by_id(self, id_value: Union[int, str], id_type: str = "trakt") -> Optional[TraktItem]:
        """
        Get movie by specific ID

        Args:
            id_value: ID value to search for
            id_type: Type of ID ("trakt", "imdb", "tmdb")

        Returns:
            TraktItem: Movie details if found, None otherwise
        """
        try:
            response = self._make_request("GET", f"/movies/{id_value}")

            if response.status_code == 200:
                movie_data = response.json()
                return TraktItem.from_movie_response(movie_data)

        except Exception as e:
            logger.exception(f"Error getting movie by {id_type} ID {id_value}: {e}")

        return None

    def get_show_by_id(self, id_value: Union[int, str], id_type: str = "trakt") -> Optional[TraktItem]:
        """
        Get TV show by specific ID

        Args:
            id_value: ID value to search for
            id_type: Type of ID ("trakt", "imdb", "tmdb", "tvdb")

        Returns:
            TraktItem: Show details if found, None otherwise
        """
        try:
            response = self._make_request("GET", f"/shows/{id_value}")

            if response.status_code == 200:
                show_data = response.json()
                return TraktItem.from_show_response(show_data)

        except Exception as e:
            logger.exception(f"Error getting show by {id_type} ID {id_value}: {e}")

        return None

    def add_movie_to_watchlist(self, trakt_item: TraktItem) -> bool:
        """Add a movie to user's watchlist"""
        if trakt_item.media_type != "movie":
            logger.error(f"Item is not a movie: {trakt_item.media_type}")
            return False

        movie_data: Dict[str, List[Dict[str, Any]]] = {
            "movies": [{"title": trakt_item.title, "year": trakt_item.year, "ids": {}}]
        }

        # Add available IDs
        if trakt_item.trakt_id:
            movie_data["movies"][0]["ids"]["trakt"] = trakt_item.trakt_id
        if trakt_item.imdb_id:
            movie_data["movies"][0]["ids"]["imdb"] = trakt_item.imdb_id
        if trakt_item.tmdb_id:
            movie_data["movies"][0]["ids"]["tmdb"] = trakt_item.tmdb_id

        logger.info(f"Adding movie to watchlist: {trakt_item.title}")

        try:
            response = self._make_request("POST", "/sync/watchlist", data=movie_data)

            if response.status_code == 201:
                result = response.json()
                added = result.get("added", {}).get("movies", 0)
                if added > 0:
                    logger.info(f"Successfully added movie to watchlist: {trakt_item.title}")
                    return True
                logger.warning(f"Movie was not added (may already be in watchlist): {trakt_item.title}")
                return True  # Consider this a success

            logger.error(f"Failed to add movie to watchlist: {response.status_code}")
            return False

        except Exception as e:
            logger.exception(f"Error adding movie to watchlist: {e}")
            return False

    def add_show_to_watchlist(self, trakt_item: TraktItem) -> bool:
        """Add a TV show to user's watchlist"""
        if trakt_item.media_type != "show":
            logger.error(f"Item is not a show: {trakt_item.media_type}")
            return False

        show_data: Dict[str, List[Dict[str, Any]]] = {
            "shows": [{"title": trakt_item.title, "year": trakt_item.year, "ids": {}}]
        }

        # Add available IDs
        if trakt_item.trakt_id:
            show_data["shows"][0]["ids"]["trakt"] = trakt_item.trakt_id
        if trakt_item.imdb_id:
            show_data["shows"][0]["ids"]["imdb"] = trakt_item.imdb_id
        if trakt_item.tmdb_id:
            show_data["shows"][0]["ids"]["tmdb"] = trakt_item.tmdb_id
        if trakt_item.tvdb_id:
            show_data["shows"][0]["ids"]["tvdb"] = trakt_item.tvdb_id

        logger.info(f"Adding show to watchlist: {trakt_item.title}")

        try:
            response = self._make_request("POST", "/sync/watchlist", data=show_data)

            if response.status_code == 201:
                result = response.json()
                added = result.get("added", {}).get("shows", 0)
                if added > 0:
                    logger.info(f"Successfully added show to watchlist: {trakt_item.title}")
                    return True
                logger.warning(f"Show was not added (may already be in watchlist): {trakt_item.title}")
                return True  # Consider this a success

            logger.error(f"Failed to add show to watchlist: {response.status_code}")
            return False

        except Exception as e:
            logger.exception(f"Error adding show to watchlist: {e}")
            return False

    def remove_movie_from_watchlist(self, trakt_item: TraktItem) -> bool:
        """Remove a movie from user's watchlist"""
        if trakt_item.media_type != "movie":
            logger.error(f"Item is not a movie: {trakt_item.media_type}")
            return False

        movie_data: Dict[str, List[Dict[str, Any]]] = {
            "movies": [{"title": trakt_item.title, "year": trakt_item.year, "ids": {}}]
        }

        # Add available IDs
        if trakt_item.trakt_id:
            movie_data["movies"][0]["ids"]["trakt"] = trakt_item.trakt_id
        if trakt_item.imdb_id:
            movie_data["movies"][0]["ids"]["imdb"] = trakt_item.imdb_id
        if trakt_item.tmdb_id:
            movie_data["movies"][0]["ids"]["tmdb"] = trakt_item.tmdb_id

        logger.info(f"Removing movie from watchlist: {trakt_item.title}")

        try:
            response = self._make_request("POST", "/sync/watchlist/remove", data=movie_data)

            if response.status_code == 200:
                result = response.json()
                deleted = result.get("deleted", {}).get("movies", 0)
                if deleted > 0:
                    logger.info(f"Successfully removed movie from watchlist: {trakt_item.title}")
                    return True
                logger.warning(f"Movie was not removed (may not be in watchlist): {trakt_item.title}")
                return True  # Consider this a success

            logger.error(f"Failed to remove movie from watchlist: {response.status_code}")
            return False

        except Exception as e:
            logger.exception(f"Error removing movie from watchlist: {e}")
            return False

    def remove_show_from_watchlist(self, trakt_item: TraktItem) -> bool:
        """Remove a TV show from user's watchlist"""
        if trakt_item.media_type != "show":
            logger.error(f"Item is not a show: {trakt_item.media_type}")
            return False

        show_data: Dict[str, List[Dict[str, Any]]] = {
            "shows": [{"title": trakt_item.title, "year": trakt_item.year, "ids": {}}]
        }

        # Add available IDs
        if trakt_item.trakt_id:
            show_data["shows"][0]["ids"]["trakt"] = trakt_item.trakt_id
        if trakt_item.imdb_id:
            show_data["shows"][0]["ids"]["imdb"] = trakt_item.imdb_id
        if trakt_item.tmdb_id:
            show_data["shows"][0]["ids"]["tmdb"] = trakt_item.tmdb_id
        if trakt_item.tvdb_id:
            show_data["shows"][0]["ids"]["tvdb"] = trakt_item.tvdb_id

        logger.info(f"Removing show from watchlist: {trakt_item.title}")

        try:
            response = self._make_request("POST", "/sync/watchlist/remove", data=show_data)

            if response.status_code == 200:
                result = response.json()
                deleted = result.get("deleted", {}).get("shows", 0)
                if deleted > 0:
                    logger.info(f"Successfully removed show from watchlist: {trakt_item.title}")
                    return True
                logger.warning(f"Show was not removed (may not be in watchlist): {trakt_item.title}")
                return True  # Consider this a success

            logger.error(f"Failed to remove show from watchlist: {response.status_code}")
            return False

        except Exception as e:
            logger.exception(f"Error removing show from watchlist: {e}")
            return False

    def get_watchlist(
        self,
        content_type: Optional[str] = None,
        sort_by: str = "added",
        limit: Optional[int] = None,
    ) -> List[WatchlistItem]:
        """
        Get user's watchlist

        Args:
            content_type: Filter by "movie" or "show" (optional)
            sort_by: Sort criteria ("added", "title", "year")
            limit: Maximum number of items to return

        Returns:
            List[WatchlistItem]: Watchlist items
        """
        try:
            response = self._make_request("GET", "/sync/watchlist")

            if response.status_code == 200:
                data = response.json()
                items = []

                for item_data in data:
                    if "movie" in item_data:
                        movie = item_data["movie"]
                        if content_type is None or content_type == "movie":
                            watchlist_item = WatchlistItem(
                                title=movie.get("title", ""),
                                year=movie.get("year"),
                                content_type="movie",
                                ids=movie.get("ids", {}),
                                added_at=datetime.fromisoformat(item_data.get("added_at", "").replace("Z", "+00:00")) if item_data.get("added_at") else None,
                            )
                            items.append(watchlist_item)

                    elif "show" in item_data:
                        show = item_data["show"]
                        if content_type is None or content_type == "show":
                            watchlist_item = WatchlistItem(
                                title=show.get("title", ""),
                                year=show.get("year"),
                                content_type="show",
                                ids=show.get("ids", {}),
                                added_at=datetime.fromisoformat(item_data.get("added_at", "").replace("Z", "+00:00")) if item_data.get("added_at") else None,
                            )
                            items.append(watchlist_item)

                # Apply sorting
                if sort_by == "title":
                    items.sort(key=lambda x: x.title.lower())
                elif sort_by == "year":
                    items.sort(key=lambda x: x.year or 0, reverse=True)
                elif sort_by == "added":
                    items.sort(key=lambda x: x.added_at or datetime.min, reverse=True)

                # Apply limit
                if limit:
                    items = items[:limit]

                logger.info(f"Retrieved {len(items)} watchlist items")
                return items

        except Exception as e:
            logger.exception(f"Error getting watchlist: {e}")

        return []


# ============================================================================
# Legacy Functions (for backward compatibility)
# ============================================================================



def interactive_select_item(items: List[TraktItem], media_item: MediaItem) -> Optional[TraktItem]:
    """
    Interactively select the correct item from search results

    Args:
        items: List of TraktItem search results
        media_item: Original MediaItem being searched for

    Returns:
        TraktItem: Selected item, or None if no selection made
    """
    if not items:
        return None

    if len(items) == 1:
        # Only one result, ask for confirmation
        item = items[0]
        print(f"\nFound 1 match for '{media_item.title}' ({media_item.year}):")
        print(f"  → {item.title} ({item.year}) [{item.media_type}]")

        while True:
            choice = input("Accept this match? [Y/n]: ").strip().lower()
            if choice in ["", "y", "yes"]:
                logger.info(f"User accepted match: {item.title} ({item.year})")
                return item
            if choice in ["n", "no"]:
                logger.info(f"User rejected match for: {media_item.title}")
                return None
            print("Please enter 'y' for yes or 'n' for no.")

    # Multiple results, show selection menu
    print(f"\nFound {len(items)} matches for '{media_item.title}' ({media_item.year}):")
    print("  0. Skip (don't add to watchlist)")

    for i, item in enumerate(items, 1):
        year_str = f"({item.year})" if item.year else "(no year)"
        print(f"  {i}. {item.title} {year_str} [{item.media_type}]")

    while True:
        try:
            choice = input(f"\nSelect an option [0-{len(items)}]: ").strip()

            if not choice:
                continue

            choice_num = int(choice)

            if choice_num == 0:
                logger.info(f"User chose to skip: {media_item.title}")
                return None
            if 1 <= choice_num <= len(items):
                selected_item = items[choice_num - 1]
                logger.info(f"User selected: {selected_item.title} ({selected_item.year})")
                return selected_item
            print(f"Please enter a number between 0 and {len(items)}.")

        except ValueError:
            print(f"Please enter a valid number between 0 and {len(items)}.")
        except KeyboardInterrupt:
            print("\nSelection cancelled.")
            logger.info(f"User cancelled selection for: {media_item.title}")
            return None


class FilenameParser:
    """Parser for extracting media information from filenames"""

    # Patterns for movie filenames
    MOVIE_PATTERNS: ClassVar[List[str]] = [
        # Movie.Name.2023.1080p.BluRay.x264.mkv
        r"^(.+?)\.(\d{4})\.(?:\d+p|BluRay|WEB|HDTV|x264|H264)",
        # Movie Name (2023) [quality].ext
        r"^(.+?)\s*\((\d{4})\)",
        # Movie.Name.2023.mkv (simpler pattern)
        r"^(.+?)\.(\d{4})(?:\.|$)",
        # Movie Name 2023 quality.ext
        r"^(.+?)\s+(\d{4})\s+",
        # Movie.Name.mkv (no year, with file extension)
        r"^(.+?)\.(?:mkv|mp4|avi|mov|wmv|flv|webm|m4v|mpg|mpeg|3gp|asf)$",
        # Final fallback: any filename
        r"^(.+)$",
    ]

    # Patterns for TV show filenames
    TV_PATTERNS: ClassVar[List[str]] = [
        # Show.Name.S01E01.Episode.Title.2023.mkv
        r"^(.+?)\.S(\d+)E(\d+)",
        # Show Name S01E01 Episode Title (2023).mkv
        r"^(.+?)\s+S(\d+)E(\d+)",
        # Show.Name.1x01.Episode.Title.mkv
        r"^(.+?)\.(\d+)x(\d+)",
        # Show Name 1x01 Episode Title.mkv
        r"^(.+?)\s+(\d+)x(\d+)",
    ]

    @classmethod
    def parse_filename(cls, filename: str) -> MediaItem:
        """
        Parse filename to extract media information

        Args:
            filename: Full path or filename to parse

        Returns:
            MediaItem: Parsed media item with title, year, and type
        """
        # Get just the filename without path and extension
        base_name = Path(filename).stem

        logger.debug(f"Parsing filename: {base_name}")

        # First try TV show patterns
        for pattern in cls.TV_PATTERNS:
            match = re.search(pattern, base_name, re.IGNORECASE)
            if match:
                title = match.group(1)
                season = int(match.group(2))
                episode = int(match.group(3))

                # Extract year if present in the remaining part
                year_match = re.search(r"(\d{4})", base_name[match.end() :])
                year = int(year_match.group(1)) if year_match else None

                media_item = MediaItem(
                    title=title,
                    year=year,
                    media_type="show",
                    season=season,
                    episode=episode,
                    original_filename=filename,
                )

                logger.info(f"Parsed as TV show: {media_item.title} S{season:02d}E{episode:02d}")
                return media_item

        # Try movie patterns
        for pattern in cls.MOVIE_PATTERNS:
            match = re.search(pattern, base_name, re.IGNORECASE)
            if match:
                title = match.group(1)
                year = None

                # Check if pattern captured year
                if len(match.groups()) > 1 and match.group(2).isdigit():
                    year = int(match.group(2))
                else:
                    # Look for year in the title
                    year_match = re.search(r"(\d{4})", title)
                    if year_match:
                        year = int(year_match.group(1))
                        title = title.replace(year_match.group(0), "").strip()

                media_item = MediaItem(
                    title=title,
                    year=year,
                    media_type="movie",
                    original_filename=filename,
                )

                logger.info(f"Parsed as movie: {media_item.title} ({year})")
                return media_item

        # Fallback: treat as movie with just the filename as title
        media_item = MediaItem(title=base_name, media_type="movie", original_filename=filename)

        logger.warning(f"Could not parse filename, treating as movie: {base_name}")
        return media_item


def process_scan_file(file_path: str) -> List[MediaItem]:
    """
    Process a JSON scan file to extract media items

    Args:
        file_path: Path to JSON file containing scan results

    Returns:
        List[MediaItem]: List of parsed media items from all files

    Raises:
        FileNotFoundError: If scan file doesn't exist
        json.JSONDecodeError: If scan file is not valid JSON
    """
    logger.info(f"Processing scan file: {file_path}")

    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"Scan file not found: {file_path}")

    try:
        with file_path_obj.open(encoding="utf-8") as f:
            scan_data = json.load(f)
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in scan file")
        raise

    media_items: List[MediaItem] = []

    # Process scan results
    results = scan_data.get("results", [])
    logger.info(f"Found {len(results)} files in scan results")

    for result in results:
        filename = result.get("filename", "")
        if not filename:
            logger.warning("Skipping result with missing filename")
            continue

        # Parse filename regardless of corruption status
        # (as per requirements: process all files)
        try:
            media_item = FilenameParser.parse_filename(filename)
            media_items.append(media_item)
            logger.debug(f"Added media item: {media_item.title}")
        except Exception as e:
            logger.warning(f"Failed to parse filename {filename}: {e}")
            continue

    logger.info(f"Successfully parsed {len(media_items)} media items")
    return media_items


def sync_to_trakt_watchlist(
    scan_file: str,
    access_token: str,
    client_id: Optional[str] = None,
    verbose: bool = False,
    interactive: bool = False,
) -> Dict[str, Any]:
    """
    Legacy function to sync scan results to Trakt watchlist

    This function maintains backward compatibility with existing CLI integration.
    For new code, use WatchlistManager class instead.

    Args:
        scan_file: Path to JSON scan file
        access_token: Trakt API access token
        client_id: Optional Trakt API client ID
        verbose: Enable verbose output
        interactive: Enable interactive selection of search results

    Returns:
        Dict[str, Any]: Summary of sync operation with counts and results
    """
    logger.info("Starting Trakt watchlist sync (legacy function)")

    if verbose:
        print("Starting Trakt watchlist sync...")
        print(f"Processing scan file: {scan_file}")

    # Use legacy TraktAPI for backward compatibility
    # Create a minimal token storage for this function
    class LegacyTokenStorage(TokenStorage):
        def __init__(self, access_token: str):
            self._tokens = {"access_token": access_token}

        def save_tokens(self, tokens: Dict[str, str]) -> None:
            self._tokens.update(tokens)

        def load_tokens(self) -> Dict[str, str]:
            return self._tokens

    # Initialize API client with legacy approach
    token_storage = LegacyTokenStorage(access_token)
    api = TraktAPI(client_id or "legacy", "", token_storage)

    # Override the authorization header directly for backward compatibility
    api.session.headers["Authorization"] = f"Bearer {access_token}"
    if client_id:
        api.session.headers["trakt-api-key"] = client_id

    # Process scan file
    try:
        media_items = process_scan_file(scan_file)
    except Exception:
        logger.exception("Failed to process scan file")
        raise

    if not media_items:
        logger.warning("No media items found to sync")
        if verbose:
            print("No media items found to sync")
        return {"total": 0, "movies_added": 0, "shows_added": 0, "failed": 0}

    # Sync to watchlist
    summary: Dict[str, Any] = {
        "total": len(media_items),
        "movies_added": 0,
        "shows_added": 0,
        "failed": 0,
        "results": [],
    }

    if verbose:
        print(f"Found {len(media_items)} media items to sync")
        if interactive:
            print("Interactive mode enabled - you will be prompted to select matches")
        print("Searching and adding to watchlist...")

    for i, media_item in enumerate(media_items, 1):
        if verbose:
            progress = f"({i}/{len(media_items)})"
            print(
                f"  {progress} Processing: {media_item.title} "
                f"({media_item.year}) [{media_item.media_type}]"
            )

        try:
            # Search for the item
            if interactive:
                # Interactive mode: get multiple results and let user choose
                search_limit = 5  # Get up to 5 results for selection
                if media_item.media_type == "movie":
                    search_results = api.search_movie(
                        media_item.title, media_item.year, limit=search_limit
                    )
                else:
                    search_results = api.search_show(
                        media_item.title, media_item.year, limit=search_limit
                    )

                # Let user select from results
                trakt_item = interactive_select_item(search_results, media_item)
            else:
                # Automatic mode: get first result only (backward compatibility)
                if media_item.media_type == "movie":
                    search_results = api.search_movie(media_item.title, media_item.year, limit=1)
                else:
                    search_results = api.search_show(media_item.title, media_item.year, limit=1)

                trakt_item = search_results[0] if search_results else None

            if not trakt_item:
                logger.warning(f"No Trakt match found for: {media_item.title}")
                if verbose:
                    print("    ❌ Not found on Trakt" if not interactive else "    ❌ Skipped")
                summary["failed"] += 1
                summary["results"].append(
                    {
                        "title": media_item.title,
                        "year": media_item.year,
                        "type": media_item.media_type,
                        "status": ("not_found" if not interactive else "skipped"),
                        "filename": media_item.original_filename,
                    }
                )
                continue

            # Add to watchlist
            if media_item.media_type == "movie":
                success = api.add_movie_to_watchlist(trakt_item)
            else:
                success = api.add_show_to_watchlist(trakt_item)

            if success:
                if media_item.media_type == "movie":
                    summary["movies_added"] += 1
                else:
                    summary["shows_added"] += 1

                if verbose:
                    print("    ✅ Added to watchlist")

                summary["results"].append(
                    {
                        "title": trakt_item.title,
                        "year": trakt_item.year,
                        "type": trakt_item.media_type,
                        "status": "added",
                        "trakt_id": trakt_item.trakt_id,
                        "filename": media_item.original_filename,
                    }
                )
            else:
                summary["failed"] += 1
                if verbose:
                    print("    ❌ Failed to add")

                summary["results"].append(
                    {
                        "title": trakt_item.title,
                        "year": trakt_item.year,
                        "type": trakt_item.media_type,
                        "status": "failed",
                        "filename": media_item.original_filename,
                    }
                )

        except Exception as e:
            logger.exception(f"Error processing {media_item.title}")
            summary["failed"] += 1
            if verbose:
                print(f"    ❌ Error: {e}")

            summary["results"].append(
                {
                    "title": media_item.title,
                    "year": media_item.year,
                    "type": media_item.media_type,
                    "status": "error",
                    "error": str(e),
                    "filename": media_item.original_filename,
                }
            )

    # Print summary
    if verbose or logger.isEnabledFor(logging.INFO):
        print("\n" + "=" * 50)
        print("TRAKT SYNC SUMMARY")
        print("=" * 50)
        print(f"Total items processed: {summary['total']}")
        print(f"Movies added: {summary['movies_added']}")
        print(f"Shows added: {summary['shows_added']}")
        print(f"Failed/Not found: {summary['failed']}")
        percent = (summary["movies_added"] + summary["shows_added"]) / summary["total"] * 100
        print(f"Success rate: {percent:.1f}%")

    logger.info(
        "Trakt sync completed: "
        f"{summary['movies_added']} movies, "
        f"{summary['shows_added']} shows added"
    )

    return summary
