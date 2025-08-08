"""
Tests for Trakt watchlist functionality
"""

import json
import tempfile
import unittest
from pathlib import Path

import pytest

from src.core.watchlist import FilenameParser, MediaItem, process_scan_file

pytestmark = pytest.mark.unit


class TestFilenameParser(unittest.TestCase):
    """Test filename parsing functionality"""

    def test_parse_movie_with_year_dots(self):
        """Test parsing movie with year and dots"""
        result = FilenameParser.parse_filename("The.Matrix.1999.1080p.BluRay.x264.mkv")

        assert result.title == "The Matrix"
        assert result.year == 1999
        assert result.media_type == "movie"
        assert result.season is None
        assert result.episode is None

    def test_parse_movie_with_parentheses(self):
        """Test parsing movie with parentheses format"""
        result = FilenameParser.parse_filename("Inception (2010) [1080p].mp4")

        assert result.title == "Inception"
        assert result.year == 2010
        assert result.media_type == "movie"

    def test_parse_tv_show_season_episode(self):
        """Test parsing TV show with season/episode"""
        result = FilenameParser.parse_filename("Breaking.Bad.S01E01.Pilot.2008.mkv")

        assert result.title == "Breaking Bad"
        assert result.year == 2008
        assert result.media_type == "show"
        assert result.season == 1
        assert result.episode == 1

    def test_parse_tv_show_1x01_format(self):
        """Test parsing TV show with 1x01 format"""
        result = FilenameParser.parse_filename("Game.of.Thrones.1x01.Winter.Is.Coming.mkv")

        assert result.title == "Game of Thrones"
        assert result.media_type == "show"
        assert result.season == 1
        assert result.episode == 1

    def test_parse_movie_no_year(self):
        """Test parsing movie without year"""
        result = FilenameParser.parse_filename("Unknown.Movie.mkv")

        assert result.title == "Unknown Movie"
        assert result.media_type == "movie"
        assert result.year is None

    def test_parse_filename_with_path(self):
        """Test parsing filename with full path"""
        result = FilenameParser.parse_filename("/home/user/movies/The.Avengers.2012.mp4")

        assert result.title == "The Avengers"
        assert result.year == 2012
        assert result.media_type == "movie"

    def test_media_item_title_cleanup(self):
        """Test that MediaItem properly cleans up titles"""
        item = MediaItem(title="Movie.Name.With.Dots", year=2023)

        assert item.title == "Movie Name With Dots"
        assert item.year == 2023
        assert item.media_type == "movie"


class TestScanFileProcessing(unittest.TestCase):
    """Test JSON scan file processing"""

    def setUp(self):
        """Set up test scan file"""
        self.test_data = {
            "scan_summary": {"total_files": 3, "corrupt_files": 1, "healthy_files": 2},
            "results": [
                {"filename": "/test/The.Matrix.1999.mkv", "is_corrupt": False},
                {"filename": "/test/Breaking.Bad.S01E01.mkv", "is_corrupt": True},
                {"filename": "/test/Inception.2010.mp4", "is_corrupt": False},
            ],
        }

    def test_process_valid_scan_file(self):
        """Test processing a valid scan file"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_path = f.name

        try:
            # Process the file
            media_items = process_scan_file(temp_path)

            # Should process all files regardless of corruption status
            assert len(media_items) == 3

            # Check first item (The Matrix)
            matrix = media_items[0]
            assert matrix.title == "The Matrix"
            assert matrix.year == 1999
            assert matrix.media_type == "movie"

            # Check second item (Breaking Bad)
            bb = media_items[1]
            assert bb.title == "Breaking Bad"
            assert bb.media_type == "show"
            assert bb.season == 1
            assert bb.episode == 1

            # Check third item (Inception)
            inception = media_items[2]
            assert inception.title == "Inception"
            assert inception.year == 2010
            assert inception.media_type == "movie"

        finally:
            Path(temp_path).unlink()

    def test_process_nonexistent_file(self):
        """Test processing nonexistent file"""
        with pytest.raises(FileNotFoundError):
            process_scan_file("/nonexistent/file.json")

    def test_process_invalid_json(self):
        """Test processing invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                process_scan_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_process_empty_results(self):
        """Test processing scan file with no results"""
        empty_data = {"scan_summary": {"total_files": 0}, "results": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(empty_data, f)
            temp_path = f.name

        try:
            media_items = process_scan_file(temp_path)
            assert len(media_items) == 0
        finally:
            Path(temp_path).unlink()


class TestMediaItem(unittest.TestCase):
    """Test MediaItem dataclass"""

    def test_media_item_creation(self):
        """Test creating MediaItem instances"""
        movie = MediaItem(title="Test Movie", year=2023, media_type="movie")

        assert movie.title == "Test Movie"
        assert movie.year == 2023
        assert movie.media_type == "movie"
        assert movie.season is None
        assert movie.episode is None

    def test_media_item_show(self):
        """Test creating TV show MediaItem"""
        show = MediaItem(title="Test Show", year=2023, media_type="show", season=1, episode=5)

        assert show.title == "Test Show"
        assert show.media_type == "show"
        assert show.season == 1
        assert show.episode == 5

    def test_media_item_invalid_type(self):
        """Test MediaItem with invalid type defaults to movie"""
        item = MediaItem(title="Test", media_type="invalid")

        assert item.media_type == "movie"


class TestSearchResultsHandling(unittest.TestCase):
    """Test handling of search results and interactive selection"""

    def test_search_results_backward_compatibility(self):
        """Test that single result searches work like before"""
        # This is a unit test for the method signature changes
        # We can't test the actual API calls without mocking
        from src.core.watchlist import TraktAPI

        # Test that the methods exist and have correct signature
        # (without actually instantiating the API to avoid trakt module issues)
        assert hasattr(TraktAPI, "search_movie")
        assert hasattr(TraktAPI, "search_show")
        assert hasattr(TraktAPI, "add_movie_to_watchlist")
        assert hasattr(TraktAPI, "add_show_to_watchlist")

    def test_interactive_select_item_import(self):
        """Test that interactive_select_item function is available"""
        from src.core.watchlist import TraktAPI

        # Function should exist as a static method
        assert hasattr(TraktAPI, "interactive_select_item")
        assert callable(TraktAPI.interactive_select_item)


class TestTraktSyncModels(unittest.TestCase):
    """Test the new Pydantic models for sync results"""

    def test_sync_result_item_creation(self):
        """Test creating a SyncResultItem"""
        from src.core.models.watchlist import SyncResultItem

        result = SyncResultItem(
            title="Test Movie",
            year=2023,
            type="movie",
            status="added",
            trakt_id=123,
            filename="/path/to/test.mp4",
            watchlist="my-list",
        )

        assert result.title == "Test Movie"
        assert result.year == 2023
        assert result.type == "movie"
        assert result.status == "added"
        assert result.trakt_id == 123
        assert result.filename == "/path/to/test.mp4"
        assert result.watchlist == "my-list"

    def test_trakt_sync_summary_creation(self):
        """Test creating a TraktSyncSummary"""
        from src.core.models.watchlist import SyncResultItem, TraktSyncSummary

        summary = TraktSyncSummary(
            total=5,
            movies_added=3,
            shows_added=1,
            failed=1,
            watchlist="test-list",
            results=[
                SyncResultItem(title="Movie 1", type="movie", status="added", filename="movie1.mp4")
            ],
        )

        assert summary.total == 5
        assert summary.movies_added == 3
        assert summary.shows_added == 1
        assert summary.failed == 1
        assert summary.watchlist == "test-list"
        assert summary.success_count == 4
        assert summary.success_rate == 80.0
        assert len(summary.results) == 1

    def test_trakt_sync_summary_properties(self):
        """Test TraktSyncSummary computed properties"""
        from src.core.models.watchlist import TraktSyncSummary

        # Test with zero total
        summary = TraktSyncSummary(total=0, movies_added=0, shows_added=0, failed=0)
        assert summary.success_rate == 0.0

        # Test with normal values
        summary = TraktSyncSummary(total=10, movies_added=6, shows_added=2, failed=2)
        assert summary.success_count == 8
        assert summary.success_rate == 80.0

    def test_watchlist_info_creation(self):
        """Test creating a WatchlistInfo model"""
        from src.core.models.watchlist import WatchlistInfo

        info = WatchlistInfo(
            name="My Test List",
            slug="my-test-list",
            trakt_id=456,
            description="A test watchlist",
            privacy="public",
            item_count=42,
        )

        assert info.name == "My Test List"
        assert info.slug == "my-test-list"
        assert info.trakt_id == 456
        assert info.description == "A test watchlist"
        assert info.privacy == "public"
        assert info.item_count == 42

    def test_watchlist_info_from_trakt_response(self):
        """Test creating WatchlistInfo from Trakt API response"""
        from src.core.models.watchlist import WatchlistInfo

        trakt_response = {
            "name": "My Movies",
            "slug": "my-movies",
            "ids": {"trakt": 123},
            "description": "My favorite movies",
            "privacy": "private",
            "item_count": 25,
            "created_at": "2023-01-01T00:00:00.000Z",
        }

        info = WatchlistInfo.from_trakt_response(trakt_response)
        assert info.name == "My Movies"
        assert info.slug == "my-movies"
        assert info.trakt_id == 123
        assert info.description == "My favorite movies"
        assert info.privacy == "private"
        assert info.item_count == 25
        assert info.created_at is not None

    def test_watchlist_item_creation(self):
        """Test creating a WatchlistItem model"""
        from src.core.models.watchlist import TraktItem, WatchlistItem

        trakt_item = TraktItem(
            title="Test Movie",
            year=2023,
            media_type="movie",
            trakt_id=789,
        )

        item = WatchlistItem(
            rank=1,
            notes="Great movie!",
            type="movie",
            trakt_item=trakt_item,
        )

        assert item.rank == 1
        assert item.notes == "Great movie!"
        assert item.type == "movie"
        assert item.trakt_item.title == "Test Movie"
        assert item.trakt_item.year == 2023

    def test_watchlist_item_from_trakt_response(self):
        """Test creating WatchlistItem from Trakt API response"""
        from src.core.models.watchlist import WatchlistItem

        trakt_response = {
            "rank": 5,
            "listed_at": "2023-01-01T00:00:00.000Z",
            "notes": "Must watch",
            "movie": {
                "title": "The Matrix",
                "year": 1999,
                "ids": {"trakt": 123, "imdb": "tt0133093"},
            },
        }

        item = WatchlistItem.from_trakt_response(trakt_response)
        assert item.rank == 5
        assert item.notes == "Must watch"
        assert item.type == "movie"
        assert item.trakt_item.title == "The Matrix"
        assert item.trakt_item.year == 1999
        assert item.trakt_item.imdb_id == "tt0133093"
        assert item.listed_at is not None


class TestTraktAPIExtensions(unittest.TestCase):
    """Test the extended TraktAPI methods"""

    def test_trakt_api_has_new_methods(self):
        """Test that TraktAPI has the new watchlist methods"""
        from src.core.watchlist import TraktAPI

        # Check that all new methods exist
        assert hasattr(TraktAPI, "list_watchlists")
        assert hasattr(TraktAPI, "get_watchlist_items")
        assert hasattr(TraktAPI, "add_movie_to_list")
        assert hasattr(TraktAPI, "add_show_to_list")

        # Check they are callable
        assert callable(TraktAPI.list_watchlists)
        assert callable(TraktAPI.get_watchlist_items)
        assert callable(TraktAPI.add_movie_to_list)
        assert callable(TraktAPI.add_show_to_list)


class TestWatchlistSyncFunction(unittest.TestCase):
    """Test the updated sync_to_trakt_watchlist function signature"""

    def test_sync_function_accepts_watchlist_parameter(self):
        """Test that sync function accepts watchlist parameter"""
        import inspect

        from src.core.watchlist import sync_to_trakt_watchlist

        # Get function signature
        sig = inspect.signature(sync_to_trakt_watchlist)
        params = list(sig.parameters.keys())

        # Check that watchlist parameter exists
        assert "watchlist" in params

        # Check that watchlist parameter is optional
        watchlist_param = sig.parameters["watchlist"]
        assert watchlist_param.default is None


if __name__ == "__main__":
    unittest.main()
