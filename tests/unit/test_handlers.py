"""
Unit tests for CLI handlers module.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.cli.handlers import (
    ScanHandler,
    ListHandler,
    TraktHandler,
    UtilityHandler
)

pytestmark = pytest.mark.unit


class TestScanHandler(unittest.TestCase):
    """Test ScanHandler class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_scan_handler_initialization(self):
        """Test scan handler initialization"""
        # Mock config
        mock_config = Mock()
        mock_config.output.default_output_dir = self.temp_path / "output"
        
        with patch('src.cli.handlers.VideoScanner'):
            handler = ScanHandler(mock_config)
            assert handler.config == mock_config


class TestListHandler(unittest.TestCase):
    """Test ListHandler class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Mock config
        self.mock_config = Mock()
        self.mock_config.output.default_output_dir = self.temp_path / "output"
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_list_handler_initialization(self):
        """Test list handler initialization"""
        handler = ListHandler(self.mock_config)
        assert handler.config == self.mock_config


class TestUtilityHandler(unittest.TestCase):
    """Test UtilityHandler class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Mock config
        self.mock_config = Mock()
        self.mock_config.output.default_output_dir = self.temp_path / "output"
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_utility_handler_initialization(self):
        """Test utility handler initialization"""
        handler = UtilityHandler(self.mock_config)
        assert handler.config == self.mock_config


class TestTraktHandler(unittest.TestCase):
    """Test TraktHandler class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_trakt_handler_initialization(self):
        """Test trakt handler initialization"""
        # Mock config
        mock_config = Mock()
        mock_config.output.default_output_dir = self.temp_path / "output"
        mock_config.trakt.client_id = "test_id"
        mock_config.trakt.client_secret = "test_secret"
        
        handler = TraktHandler(mock_config)
        assert handler.config == mock_config


class TestHandlerErrorHandling(unittest.TestCase):
    """Test error handling across handlers"""
    
    def test_base_handler_error_handling(self):
        """Test base handler error handling"""
        mock_config = Mock()
        mock_config.output.default_output_dir = Path("/tmp")
        
        with patch('src.cli.handlers.VideoScanner'):
            handler = ScanHandler(mock_config)
            
            # Test error handling method
            with self.assertRaises(SystemExit):
                handler._handle_error(ValueError("test error"), "Test message")