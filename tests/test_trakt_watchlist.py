"""
Tests for Trakt watchlist functionality
"""

import json
import tempfile
import unittest
from pathlib import Path

from trakt_watchlist import FilenameParser, MediaItem, process_scan_file


class TestFilenameParser(unittest.TestCase):
    """Test filename parsing functionality"""
    
    def test_parse_movie_with_year_dots(self):
        """Test parsing movie with year and dots"""
        result = FilenameParser.parse_filename("The.Matrix.1999.1080p.BluRay.x264.mkv")
        
        self.assertEqual(result.title, "The Matrix")
        self.assertEqual(result.year, 1999)
        self.assertEqual(result.media_type, "movie")
        self.assertIsNone(result.season)
        self.assertIsNone(result.episode)
    
    def test_parse_movie_with_parentheses(self):
        """Test parsing movie with parentheses format"""
        result = FilenameParser.parse_filename("Inception (2010) [1080p].mp4")
        
        self.assertEqual(result.title, "Inception")
        self.assertEqual(result.year, 2010)
        self.assertEqual(result.media_type, "movie")
    
    def test_parse_tv_show_season_episode(self):
        """Test parsing TV show with season/episode"""
        result = FilenameParser.parse_filename("Breaking.Bad.S01E01.Pilot.2008.mkv")
        
        self.assertEqual(result.title, "Breaking Bad")
        self.assertEqual(result.year, 2008)
        self.assertEqual(result.media_type, "show")
        self.assertEqual(result.season, 1)
        self.assertEqual(result.episode, 1)
    
    def test_parse_tv_show_1x01_format(self):
        """Test parsing TV show with 1x01 format"""
        result = FilenameParser.parse_filename("Game.of.Thrones.1x01.Winter.Is.Coming.mkv")
        
        self.assertEqual(result.title, "Game of Thrones")
        self.assertEqual(result.media_type, "show")
        self.assertEqual(result.season, 1)
        self.assertEqual(result.episode, 1)
    
    def test_parse_movie_no_year(self):
        """Test parsing movie without year"""
        result = FilenameParser.parse_filename("Unknown.Movie.mkv")
        
        self.assertEqual(result.title, "Unknown Movie")
        self.assertEqual(result.media_type, "movie")
        self.assertIsNone(result.year)
    
    def test_parse_filename_with_path(self):
        """Test parsing filename with full path"""
        result = FilenameParser.parse_filename("/home/user/movies/The.Avengers.2012.mp4")
        
        self.assertEqual(result.title, "The Avengers")
        self.assertEqual(result.year, 2012)
        self.assertEqual(result.media_type, "movie")
    
    def test_media_item_title_cleanup(self):
        """Test that MediaItem properly cleans up titles"""
        item = MediaItem(title="Movie.Name.With.Dots", year=2023)
        
        self.assertEqual(item.title, "Movie Name With Dots")
        self.assertEqual(item.year, 2023)
        self.assertEqual(item.media_type, "movie")


class TestScanFileProcessing(unittest.TestCase):
    """Test JSON scan file processing"""
    
    def setUp(self):
        """Set up test scan file"""
        self.test_data = {
            "scan_summary": {
                "total_files": 3,
                "corrupt_files": 1,
                "healthy_files": 2
            },
            "results": [
                {
                    "filename": "/test/The.Matrix.1999.mkv",
                    "is_corrupt": False
                },
                {
                    "filename": "/test/Breaking.Bad.S01E01.mkv",
                    "is_corrupt": True
                },
                {
                    "filename": "/test/Inception.2010.mp4",
                    "is_corrupt": False
                }
            ]
        }
    
    def test_process_valid_scan_file(self):
        """Test processing a valid scan file"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f)
            temp_path = f.name
        
        try:
            # Process the file
            media_items = process_scan_file(temp_path)
            
            # Should process all files regardless of corruption status
            self.assertEqual(len(media_items), 3)
            
            # Check first item (The Matrix)
            matrix = media_items[0]
            self.assertEqual(matrix.title, "The Matrix")
            self.assertEqual(matrix.year, 1999)
            self.assertEqual(matrix.media_type, "movie")
            
            # Check second item (Breaking Bad)
            bb = media_items[1]
            self.assertEqual(bb.title, "Breaking Bad")
            self.assertEqual(bb.media_type, "show")
            self.assertEqual(bb.season, 1)
            self.assertEqual(bb.episode, 1)
            
            # Check third item (Inception)
            inception = media_items[2]
            self.assertEqual(inception.title, "Inception")
            self.assertEqual(inception.year, 2010)
            self.assertEqual(inception.media_type, "movie")
            
        finally:
            Path(temp_path).unlink()
    
    def test_process_nonexistent_file(self):
        """Test processing nonexistent file"""
        with self.assertRaises(FileNotFoundError):
            process_scan_file("/nonexistent/file.json")
    
    def test_process_invalid_json(self):
        """Test processing invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            with self.assertRaises(json.JSONDecodeError):
                process_scan_file(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_process_empty_results(self):
        """Test processing scan file with no results"""
        empty_data = {
            "scan_summary": {"total_files": 0},
            "results": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(empty_data, f)
            temp_path = f.name
        
        try:
            media_items = process_scan_file(temp_path)
            self.assertEqual(len(media_items), 0)
        finally:
            Path(temp_path).unlink()


class TestMediaItem(unittest.TestCase):
    """Test MediaItem dataclass"""
    
    def test_media_item_creation(self):
        """Test creating MediaItem instances"""
        movie = MediaItem(title="Test Movie", year=2023, media_type="movie")
        
        self.assertEqual(movie.title, "Test Movie")
        self.assertEqual(movie.year, 2023)
        self.assertEqual(movie.media_type, "movie")
        self.assertIsNone(movie.season)
        self.assertIsNone(movie.episode)
    
    def test_media_item_show(self):
        """Test creating TV show MediaItem"""
        show = MediaItem(
            title="Test Show",
            year=2023,
            media_type="show",
            season=1,
            episode=5
        )
        
        self.assertEqual(show.title, "Test Show")
        self.assertEqual(show.media_type, "show")
        self.assertEqual(show.season, 1)
        self.assertEqual(show.episode, 5)
    
    def test_media_item_invalid_type(self):
        """Test MediaItem with invalid type defaults to movie"""
        item = MediaItem(title="Test", media_type="invalid")
        
        self.assertEqual(item.media_type, "movie")


class TestSearchResultsHandling(unittest.TestCase):
    """Test handling of search results and interactive selection"""
    
    def test_search_results_backward_compatibility(self):
        """Test that single result searches work like before"""
        # This is a unit test for the method signature changes
        # We can't test the actual API calls without mocking
        from trakt_watchlist import TraktAPI
        
        # Test that the method exists and has correct signature
        api = TraktAPI("fake_token")
        
        # These should not raise TypeErrors due to signature changes
        self.assertTrue(hasattr(api, 'search_movie'))
        self.assertTrue(hasattr(api, 'search_show'))
    
    def test_interactive_select_item_import(self):
        """Test that interactive_select_item function is available"""
        from trakt_watchlist import interactive_select_item
        
        # Function should exist
        self.assertTrue(callable(interactive_select_item))


if __name__ == '__main__':
    unittest.main()