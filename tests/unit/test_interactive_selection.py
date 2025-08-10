"""
Tests for interactive selection functionality with mocked user input.
"""

import unittest
from unittest.mock import patch

import pytest

from src.core.models.watchlist import MediaItem, TraktItem
from src.core.watchlist import TraktAPI

pytestmark = pytest.mark.unit


class TestInteractiveSelection(unittest.TestCase):
    """Test interactive selection functionality"""

    def setUp(self):
        """Set up test data"""
        self.media_item = MediaItem(
            title="Test Movie",
            year=2023,
            media_type="movie",
            original_filename="/path/to/test.movie.2023.mkv",
        )

        self.trakt_items = [
            TraktItem(
                title="Test Movie",
                year=2023,
                media_type="movie",
                trakt_id=123,
                imdb_id="tt1234567",
                tmdb_id=456,
            ),
            TraktItem(
                title="Test Movie 2",
                year=2023,
                media_type="movie",
                trakt_id=124,
                imdb_id="tt1234568",
                tmdb_id=457,
            ),
            TraktItem(
                title="Test Movie (Director's Cut)",
                year=2023,
                media_type="movie",
                trakt_id=125,
                imdb_id="tt1234569",
                tmdb_id=458,
            ),
        ]

    def test_interactive_select_empty_list(self):
        """Test interactive selection with empty item list"""
        result = TraktAPI.interactive_select_item([], self.media_item)
        assert result is None

    def test_interactive_select_single_item(self):
        """Test interactive selection with single item automatically returns it"""
        single_item = [self.trakt_items[0]]

        with patch("builtins.print") as mock_print:
            result = TraktAPI.interactive_select_item(single_item, self.media_item)

        assert result == self.trakt_items[0]
        # Should print the found match information
        mock_print.assert_called()

    @patch("builtins.input", return_value="1")
    @patch("builtins.print")
    def test_interactive_select_multiple_items_valid_choice(self, mock_print, mock_input):
        """Test interactive selection with multiple items and valid user choice"""
        result = TraktAPI.interactive_select_item(self.trakt_items, self.media_item)

        assert result == self.trakt_items[0]
        # Should print the options and prompt
        mock_print.assert_called()
        mock_input.assert_called_once()

    @patch("builtins.input", return_value="0")
    @patch("builtins.print")
    def test_interactive_select_skip_choice(self, mock_print, mock_input):
        """Test interactive selection when user chooses to skip"""
        result = TraktAPI.interactive_select_item(self.trakt_items, self.media_item)

        assert result is None
        mock_input.assert_called_once()

    @patch("builtins.input", side_effect=["invalid", "2"])
    @patch("builtins.print")
    def test_interactive_select_invalid_then_valid_input(self, mock_print, mock_input):
        """Test interactive selection with invalid input followed by valid choice"""
        result = TraktAPI.interactive_select_item(self.trakt_items, self.media_item)

        assert result == self.trakt_items[1]
        # Should have called input twice due to invalid input
        assert mock_input.call_count == 2

    @patch("builtins.input", side_effect=["", "3"])
    @patch("builtins.print")
    def test_interactive_select_empty_then_valid_input(self, mock_print, mock_input):
        """Test interactive selection with empty input followed by valid choice"""
        result = TraktAPI.interactive_select_item(self.trakt_items, self.media_item)

        assert result == self.trakt_items[2]
        # Should have called input twice due to empty input
        assert mock_input.call_count == 2

    @patch("builtins.input", side_effect=["5", "1"])
    @patch("builtins.print")
    def test_interactive_select_out_of_range_then_valid(self, mock_print, mock_input):
        """Test interactive selection with out-of-range input followed by valid choice"""
        result = TraktAPI.interactive_select_item(self.trakt_items, self.media_item)

        assert result == self.trakt_items[0]
        # Should have called input twice due to out-of-range input
        assert mock_input.call_count == 2

    @patch("builtins.input", side_effect=KeyboardInterrupt())
    @patch("builtins.print")
    def test_interactive_select_keyboard_interrupt(self, mock_print, mock_input):
        """Test interactive selection when user presses Ctrl+C"""
        result = TraktAPI.interactive_select_item(self.trakt_items, self.media_item)

        assert result is None
        mock_input.assert_called_once()

    def test_interactive_select_display_format(self):
        """Test that interactive selection displays items in correct format"""
        with patch("builtins.input", return_value="1"), patch("builtins.print") as mock_print:
            TraktAPI.interactive_select_item(self.trakt_items, self.media_item)

            # Check that print was called with the expected format
            print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]

            # Should display the found matches header
            header_found = any("Found 3 matches" in str(call) for call in print_calls)
            assert header_found, "Should display number of matches found"

            # Should display skip option
            skip_found = any("0. Skip" in str(call) for call in print_calls)
            assert skip_found, "Should display skip option"

            # Should display numbered options
            option_found = any("1. Test Movie (2023)" in str(call) for call in print_calls)
            assert option_found, "Should display numbered movie options"

    def test_interactive_select_with_tv_show(self):
        """Test interactive selection with TV show items"""
        show_item = MediaItem(
            title="Test Show",
            year=2023,
            media_type="show",
            season=1,
            episode=1,
            original_filename="/path/to/test.show.s01e01.mkv",
        )

        trakt_shows = [
            TraktItem(
                title="Test Show",
                year=2023,
                media_type="show",
                trakt_id=200,
                imdb_id="tt2000000",
                tmdb_id=500,
                tvdb_id=300,
            )
        ]

        with patch("builtins.print"):
            result = TraktAPI.interactive_select_item(trakt_shows, show_item)

        assert result == trakt_shows[0]
        assert result.media_type == "show"

    def test_interactive_select_with_items_no_year(self):
        """Test interactive selection with items that have no year"""
        no_year_items = [
            TraktItem(title="Test Movie", year=None, media_type="movie", trakt_id=300),
            TraktItem(title="Another Movie", year=2023, media_type="movie", trakt_id=301),
        ]

        with patch("builtins.input", return_value="1"), patch("builtins.print") as mock_print:
            result = TraktAPI.interactive_select_item(no_year_items, self.media_item)

        assert result == no_year_items[0]
        # Should handle items with no year gracefully in the multiple items case
        print_calls = [str(call) for call in mock_print.call_args_list]
        no_year_found = any("(no year)" in call for call in print_calls)
        assert no_year_found, "Should display '(no year)' for items without year"


if __name__ == "__main__":
    unittest.main()
