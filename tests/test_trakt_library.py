"""
Tests for the Trakt.tv Watchlist Management Library.
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from trakt_library import (
    WatchlistManager,
    TraktAPI,
    SearchResult,
    OperationResult,
    WatchlistItem,
    Watchlist,
    BatchResult,
    MemoryTokenStorage,
    TraktWatchlistError,
    AuthenticationError,
    APIError,
    NotFoundError,
    ValidationError
)


class TestExceptions:
    """Test exception hierarchy."""
    
    def test_base_exception(self):
        """Test base TraktWatchlistError."""
        error = TraktWatchlistError("test message")
        assert str(error) == "test message"
        assert error.message == "test message"
    
    def test_authentication_error(self):
        """Test AuthenticationError inheritance."""
        error = AuthenticationError("auth failed")
        assert isinstance(error, TraktWatchlistError)
        assert str(error) == "auth failed"
    
    def test_api_error_with_status_code(self):
        """Test APIError with status code."""
        error = APIError("request failed", 404)
        assert isinstance(error, TraktWatchlistError)
        assert error.status_code == 404
        assert str(error) == "request failed"
    
    def test_not_found_error_with_suggestions(self):
        """Test NotFoundError with suggestions."""
        suggestions = ["suggestion1", "suggestion2"]
        error = NotFoundError("not found", suggestions)
        assert isinstance(error, TraktWatchlistError)
        assert error.suggestions == suggestions
    
    def test_validation_error(self):
        """Test ValidationError inheritance."""
        error = ValidationError("invalid input")
        assert isinstance(error, TraktWatchlistError)
        assert str(error) == "invalid input"


class TestDataModels:
    """Test data model classes."""
    
    def test_search_result_creation(self):
        """Test SearchResult creation and validation."""
        result = SearchResult(
            title="Test Movie",
            year=2023,
            ids={"trakt": 12345, "imdb": "tt1234567"},
            content_type="movie"
        )
        
        assert result.title == "Test Movie"
        assert result.year == 2023
        assert result.ids["trakt"] == 12345
        assert result.content_type == "movie"
    
    def test_search_result_invalid_content_type(self):
        """Test SearchResult validation with invalid content type."""
        with pytest.raises(ValidationError, match="Invalid content_type"):
            SearchResult(
                title="Test",
                year=2023,
                ids={},
                content_type="invalid"
            )
    
    def test_operation_result_boolean_evaluation(self):
        """Test OperationResult boolean evaluation."""
        success = OperationResult(True, "success")
        failure = OperationResult(False, "failed")
        
        assert bool(success) is True
        assert bool(failure) is False
    
    def test_watchlist_item_to_dict(self):
        """Test WatchlistItem dictionary conversion."""
        added_at = datetime(2023, 1, 1, 12, 0, 0)
        item = WatchlistItem(
            title="Test Movie",
            year=2023,
            content_type="movie",
            ids={"trakt": 12345},
            added_at=added_at
        )
        
        result = item.to_dict()
        expected = {
            'title': "Test Movie",
            'year': 2023,
            'content_type': "movie",
            'ids': {"trakt": 12345},
            'added_at': "2023-01-01T12:00:00"
        }
        
        assert result == expected
    
    def test_watchlist_to_dict_and_json(self):
        """Test Watchlist conversion methods."""
        added_at = datetime(2023, 1, 1, 12, 0, 0)
        item = WatchlistItem(
            title="Test Movie",
            year=2023,
            content_type="movie",
            ids={"trakt": 12345},
            added_at=added_at
        )
        
        watchlist = Watchlist([item])
        
        # Test to_dict
        result_dict = watchlist.to_dict()
        assert result_dict['total_count'] == 1
        assert len(result_dict['items']) == 1
        assert result_dict['items'][0]['title'] == "Test Movie"
        
        # Test to_json
        result_json = watchlist.to_json()
        parsed = json.loads(result_json)
        assert parsed['total_count'] == 1
        assert parsed['items'][0]['title'] == "Test Movie"
    
    def test_batch_result_auto_total(self):
        """Test BatchResult automatic total calculation."""
        successful = [OperationResult(True, "success")]
        failed = [OperationResult(False, "failed")]
        
        batch = BatchResult(successful, failed, 0)
        assert batch.total == 2  # Auto-calculated


class TestTokenStorage:
    """Test token storage implementations."""
    
    def test_memory_token_storage(self):
        """Test MemoryTokenStorage functionality."""
        storage = MemoryTokenStorage()
        
        # Initially no tokens
        tokens = storage.load_tokens()
        assert tokens['access_token'] is None
        assert tokens['refresh_token'] is None
        
        # Save tokens
        storage.save_tokens("access123", "refresh456")
        
        # Load tokens
        tokens = storage.load_tokens()
        assert tokens['access_token'] == "access123"
        assert tokens['refresh_token'] == "refresh456"


class TestTraktAPI:
    """Test enhanced TraktAPI functionality."""
    
    def test_api_initialization(self):
        """Test TraktAPI initialization."""
        api = TraktAPI(
            client_id="test_client",
            client_secret="test_secret",
            access_token="test_token"
        )
        
        assert api.client_id == "test_client"
        assert api.client_secret == "test_secret"
        assert api.access_token == "test_token"
        assert "Authorization" in api.session.headers
        assert api.session.headers["trakt-api-key"] == "test_client"
    
    @patch('trakt_library.requests.Session.request')
    def test_successful_request(self, mock_request):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_request.return_value = mock_response
        
        api = TraktAPI("client", "secret", "token")
        response = api._make_request("GET", "/test")
        
        assert response.status_code == 200
        mock_request.assert_called_once()
    
    @patch('trakt_library.requests.Session.request')
    def test_rate_limit_retry(self, mock_request):
        """Test rate limit handling with retry."""
        # First call returns 429, second returns 200
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}
        
        success_response = Mock()
        success_response.status_code = 200
        
        mock_request.side_effect = [rate_limit_response, success_response]
        
        api = TraktAPI("client", "secret", "token")
        
        with patch('time.sleep') as mock_sleep:
            response = api._make_request("GET", "/test")
            
        assert response.status_code == 200
        assert mock_request.call_count == 2
        mock_sleep.assert_called_once_with(1)
    
    @patch('trakt_library.requests.Session.request')
    def test_authentication_error(self, mock_request):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        api = TraktAPI("client", "secret", "token")
        
        with pytest.raises(AuthenticationError):
            api._make_request("GET", "/test")
    
    @patch('trakt_library.requests.Session.request')
    def test_server_error_retry(self, mock_request):
        """Test server error retry logic."""
        # First call returns 500, second returns 200
        server_error = Mock()
        server_error.status_code = 500
        
        success_response = Mock()
        success_response.status_code = 200
        
        mock_request.side_effect = [server_error, success_response]
        
        api = TraktAPI("client", "secret", "token")
        
        with patch('time.sleep') as mock_sleep:
            response = api._make_request("GET", "/test")
            
        assert response.status_code == 200
        assert mock_request.call_count == 2
        mock_sleep.assert_called_once()
    
    @patch('trakt_library.requests.Session.request')
    def test_search_movies(self, mock_request):
        """Test movie search functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "movie": {
                    "title": "Inception",
                    "year": 2010,
                    "ids": {"trakt": 12345, "imdb": "tt1375666"}
                }
            }
        ]
        mock_request.return_value = mock_response
        
        api = TraktAPI("client", "secret", "token")
        results = api.search("inception", content_type="movie")
        
        assert len(results) == 1
        assert results[0].title == "Inception"
        assert results[0].year == 2010
        assert results[0].content_type == "movie"
        assert results[0].ids["trakt"] == 12345
    
    @patch('trakt_library.requests.Session.request')
    def test_search_shows(self, mock_request):
        """Test TV show search functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "show": {
                    "title": "Breaking Bad",
                    "year": 2008,
                    "ids": {"trakt": 54321, "tvdb": 81189}
                }
            }
        ]
        mock_request.return_value = mock_response
        
        api = TraktAPI("client", "secret", "token")
        results = api.search("breaking bad", content_type="show")
        
        assert len(results) == 1
        assert results[0].title == "Breaking Bad"
        assert results[0].year == 2008
        assert results[0].content_type == "show"
        assert results[0].ids["trakt"] == 54321
    
    @patch('trakt_library.requests.Session.request')
    def test_token_refresh(self, mock_request):
        """Test token refresh functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token"
        }
        mock_request.return_value = mock_response
        
        storage = MemoryTokenStorage()
        api = TraktAPI("client", "secret", "old_token", "refresh_token", storage)
        
        result = api.refresh_tokens()
        
        assert result is True
        assert api.access_token == "new_access_token"
        assert api.refresh_token == "new_refresh_token"
        
        # Check tokens were saved to storage
        tokens = storage.load_tokens()
        assert tokens['access_token'] == "new_access_token"
        assert tokens['refresh_token'] == "new_refresh_token"


class TestWatchlistManager:
    """Test WatchlistManager functionality."""
    
    def test_initialization_with_credentials(self):
        """Test manager initialization with provided credentials."""
        manager = WatchlistManager(
            client_id="test_client",
            client_secret="test_secret"
        )
        
        assert manager.client_id == "test_client"
        assert manager.client_secret == "test_secret"
        assert isinstance(manager.api, TraktAPI)
    
    def test_initialization_missing_credentials(self):
        """Test manager initialization fails with missing credentials."""
        with pytest.raises(ValidationError, match="client_id and client_secret are required"):
            WatchlistManager()
    
    def test_initialization_with_environment_variables(self):
        """Test manager initialization using environment variables."""
        with patch.dict(os.environ, {
            'TRAKT_CLIENT_ID': 'env_client',
            'TRAKT_CLIENT_SECRET': 'env_secret'
        }):
            manager = WatchlistManager()
            
            assert manager.client_id == "env_client"
            assert manager.client_secret == "env_secret"
    
    def test_authentication_status(self):
        """Test authentication status checking."""
        manager = WatchlistManager("client", "secret")
        
        # No token initially
        assert manager.is_authenticated() is False
        
        # Set token
        manager.api.access_token = "test_token"
        assert manager.is_authenticated() is True
    
    def test_get_auth_url(self):
        """Test OAuth authorization URL generation."""
        manager = WatchlistManager("test_client", "secret")
        auth_url = manager.get_auth_url()
        
        assert "trakt.tv/oauth/authorize" in auth_url
        assert "client_id=test_client" in auth_url
    
    @patch('trakt_library.TraktAPI._make_request')
    def test_oauth_code_exchange(self, mock_request):
        """Test OAuth authorization code exchange."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token"
        }
        mock_request.return_value = mock_response
        
        manager = WatchlistManager("client", "secret")
        result = manager.exchange_code("auth_code_123")
        
        assert result is True
        assert manager.api.access_token == "new_access_token"
        assert manager.api.refresh_token == "new_refresh_token"
    
    @patch('trakt_library.TraktAPI.search')
    def test_search_methods(self, mock_search):
        """Test search method delegation."""
        mock_search.return_value = [
            SearchResult("Test Movie", 2023, {"trakt": 123}, "movie")
        ]
        
        manager = WatchlistManager("client", "secret")
        
        # Test general search
        results = manager.search("test")
        assert len(results) == 1
        mock_search.assert_called_with("test")
        
        # Test movie-specific search
        results = manager.search_movies("test movie", year=2023)
        mock_search.assert_called_with("test movie", content_type="movie", year=2023)
        
        # Test show-specific search
        results = manager.search_shows("test show", year=2023)
        mock_search.assert_called_with("test show", content_type="show", year=2023)
    
    @patch('trakt_library.WatchlistManager.search_movies')
    @patch('trakt_library.WatchlistManager._add_movie_to_watchlist')
    def test_add_movie_success(self, mock_add, mock_search):
        """Test successful movie addition."""
        movie = SearchResult("Test Movie", 2023, {"trakt": 123}, "movie")
        mock_search.return_value = [movie]
        mock_add.return_value = OperationResult(True, "Movie added", movie)
        
        manager = WatchlistManager("client", "secret", "token")
        result = manager.add_movie("test movie")
        
        assert result.success is True
        assert "Movie added" in result.message
        assert result.item == movie
        mock_search.assert_called_once_with("test movie")
        mock_add.assert_called_once_with(movie)
    
    @patch('trakt_library.WatchlistManager.search_movies')
    def test_add_movie_not_found(self, mock_search):
        """Test movie addition when movie not found."""
        mock_search.return_value = []  # No results
        
        manager = WatchlistManager("client", "secret", "token")
        result = manager.add_movie("nonexistent movie")
        
        assert result.success is False
        assert "not found" in result.message
        assert result.item is None
    
    def test_add_movie_not_authenticated(self):
        """Test movie addition fails when not authenticated."""
        manager = WatchlistManager("client", "secret")  # No token
        result = manager.add_movie("test movie")
        
        assert result.success is False
        assert "Authentication required" in result.message
    
    def test_add_movie_dry_run(self):
        """Test movie addition in dry run mode."""
        manager = WatchlistManager("client", "secret", "token")
        result = manager.add_movie("test movie", dry_run=True)
        
        assert result.success is True
        assert "Dry run" in result.message
        assert "test movie" in result.message
    
    @patch('trakt_library.WatchlistManager.add_movie')
    def test_add_movies_batch(self, mock_add_movie):
        """Test batch movie addition."""
        # Mock individual results
        mock_add_movie.side_effect = [
            OperationResult(True, "Added movie 1"),
            OperationResult(False, "Failed movie 2"),
            OperationResult(True, "Added movie 3")
        ]
        
        manager = WatchlistManager("client", "secret", "token")
        result = manager.add_movies(["movie1", "movie2", "movie3"])
        
        assert isinstance(result, BatchResult)
        assert result.total == 3
        assert len(result.successful) == 2
        assert len(result.failed) == 1
        assert mock_add_movie.call_count == 3
    
    @patch('trakt_library.TraktAPI._make_request')
    def test_internal_add_movie_to_watchlist(self, mock_request):
        """Test internal movie addition to watchlist."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "added": {"movies": 1}
        }
        mock_request.return_value = mock_response
        
        manager = WatchlistManager("client", "secret", "token")
        movie = SearchResult("Test Movie", 2023, {"trakt": 123}, "movie")
        
        result = manager._add_movie_to_watchlist(movie)
        
        assert result.success is True
        assert "added to watchlist" in result.message
        assert result.item == movie
        
        # Verify API call
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"  # method
        assert call_args[0][1] == "/sync/watchlist"  # endpoint
        
        # Check data structure
        data = call_args[1]['data']
        assert "movies" in data
        assert len(data["movies"]) == 1
        assert data["movies"][0]["title"] == "Test Movie"
    
    @patch('trakt_library.TraktAPI._make_request')
    def test_internal_add_show_to_watchlist(self, mock_request):
        """Test internal show addition to watchlist."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "added": {"shows": 1}
        }
        mock_request.return_value = mock_response
        
        manager = WatchlistManager("client", "secret", "token")
        show = SearchResult("Test Show", 2023, {"trakt": 123}, "show")
        
        result = manager._add_show_to_watchlist(show)
        
        assert result.success is True
        assert "added to watchlist" in result.message
        assert result.item == show
        
        # Verify API call
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"  # method
        assert call_args[0][1] == "/sync/watchlist"  # endpoint
        
        # Check data structure
        data = call_args[1]['data']
        assert "shows" in data
        assert len(data["shows"]) == 1
        assert data["shows"][0]["title"] == "Test Show"
    
    def test_get_watchlist_not_authenticated(self):
        """Test watchlist retrieval fails when not authenticated."""
        manager = WatchlistManager("client", "secret")  # No token
        
        with pytest.raises(AuthenticationError, match="Authentication required"):
            manager.get_watchlist()
    
    def test_get_movies_delegation(self):
        """Test get_movies delegates to get_watchlist with movie filter."""
        manager = WatchlistManager("client", "secret", "token")
        
        with patch.object(manager, 'get_watchlist') as mock_get:
            mock_get.return_value = Watchlist()
            
            result = manager.get_movies(sort_by="title", limit=10)
            
            mock_get.assert_called_once_with(
                content_type="movie",
                sort_by="title",
                limit=10
            )
    
    def test_get_shows_delegation(self):
        """Test get_shows delegates to get_watchlist with show filter."""
        manager = WatchlistManager("client", "secret", "token")
        
        with patch.object(manager, 'get_watchlist') as mock_get:
            mock_get.return_value = Watchlist()
            
            result = manager.get_shows(sort_by="added", limit=5)
            
            mock_get.assert_called_once_with(
                content_type="show",
                sort_by="added",
                limit=5
            )


class TestLibraryIntegration:
    """Test library integration and end-to-end functionality."""
    
    @patch('trakt_library.WatchlistManager.search_movies')
    @patch('trakt_library.WatchlistManager._add_movie_to_watchlist')
    def test_full_workflow_example(self, mock_add, mock_search):
        """Test a complete workflow example."""
        # Mock search result
        movie = SearchResult("Inception", 2010, {"trakt": 12345, "imdb": "tt1375666"}, "movie")
        mock_search.return_value = [movie]
        
        # Mock add result
        mock_add.return_value = OperationResult(True, "Movie 'Inception' added to watchlist", movie)
        
        # Initialize manager and perform workflow
        manager = WatchlistManager("client", "secret", "token")
        
        # Search for movie
        results = manager.search_movies("inception")
        assert len(results) == 1
        assert results[0].title == "Inception"
        
        # Add to watchlist
        result = manager.add_movie("inception")
        assert result.success is True
        assert "added to watchlist" in result.message
        
        # Verify methods were called
        mock_search.assert_called_with("inception")
        mock_add.assert_called_once()
    
    def test_error_handling_chain(self):
        """Test error handling throughout the library."""
        # Test validation error
        with pytest.raises(ValidationError):
            WatchlistManager()  # Missing credentials
        
        # Test authentication error
        manager = WatchlistManager("client", "secret")
        result = manager.add_movie("test")
        assert result.success is False
        assert "Authentication required" in result.message
    
    def test_backward_compatibility_check(self):
        """Test that library doesn't break existing imports."""
        # This test ensures the library can coexist with existing trakt_watchlist.py
        try:
            from trakt_library import WatchlistManager
            from trakt_watchlist import sync_to_trakt_watchlist
            
            # Both should be importable
            assert WatchlistManager is not None
            assert sync_to_trakt_watchlist is not None
            
        except ImportError as e:
            pytest.fail(f"Import compatibility broken: {e}")


if __name__ == "__main__":
    pytest.main([__file__])