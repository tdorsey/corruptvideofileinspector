"""
Unit tests for the interface-agnostic video scan service.

These tests verify that the VideoScanService works correctly with
dependency injection and different interface implementations.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.scan_service import VideoScanService


@pytest.mark.unit
def test_video_scan_service_initialization():
    """Test that VideoScanService initializes correctly with dependencies."""
    # Create mock dependencies
    config_provider = Mock()
    result_handler = Mock()
    progress_reporter = Mock()
    
    # Initialize service
    service = VideoScanService(
        config_provider=config_provider,
        result_handler=result_handler,
        progress_reporter=progress_reporter,
    )
    
    # Verify dependencies are stored
    assert service._config_provider is config_provider
    assert service._result_handler is result_handler
    assert service._progress_reporter is progress_reporter
    assert not service.is_shutdown_requested


@pytest.mark.unit
def test_video_scan_service_shutdown():
    """Test that shutdown functionality works correctly."""
    config_provider = Mock()
    result_handler = Mock()
    
    service = VideoScanService(
        config_provider=config_provider,
        result_handler=result_handler,
    )
    
    # Initially not shutdown
    assert not service.is_shutdown_requested
    
    # Request shutdown
    service.request_shutdown()
    assert service.is_shutdown_requested


@pytest.mark.unit 
@patch('src.core.scan_service.VideoScanService._find_video_files')
def test_scan_directory_no_files(mock_find_files):
    """Test scanning directory with no video files."""
    # Setup mocks
    config_provider = Mock()
    config_provider.get_scan_directory.return_value = Path("/test")
    config_provider.get_scan_mode.return_value = Mock(value="quick")
    config_provider.get_recursive_scan.return_value = True
    config_provider.get_file_extensions.return_value = [".mp4"]
    
    result_handler = Mock()
    
    # Mock finding no files
    mock_find_files.return_value = []
    
    service = VideoScanService(
        config_provider=config_provider,
        result_handler=result_handler,
    )
    
    # Run scan
    with patch('src.core.models.scanning.ScanSummary') as mock_summary_class:
        mock_summary = Mock()
        mock_summary_class.return_value = mock_summary
        
        summary = service.scan_directory()
        
        # Verify summary creation
        mock_summary_class.assert_called_once()
        
        # Verify result handler was called
        result_handler.handle_scan_complete.assert_called_once_with(mock_summary)


@pytest.mark.unit
@patch('src.core.scan_service.VideoScanService._perform_scan')
@patch('src.core.scan_service.VideoScanService._find_video_files')
def test_scan_directory_with_files(mock_find_files, mock_perform_scan):
    """Test scanning directory with video files."""
    from src.core.models.inspection import VideoFile
    
    # Setup mocks
    config_provider = Mock()
    config_provider.get_scan_directory.return_value = Path("/test")
    config_provider.get_scan_mode.return_value = Mock(value="quick")
    config_provider.get_recursive_scan.return_value = True
    config_provider.get_file_extensions.return_value = [".mp4"]
    
    result_handler = Mock()
    
    # Mock finding files
    video_files = [VideoFile(path=Path("/test/file1.mp4"))]
    mock_find_files.return_value = video_files
    
    # Mock scan results
    mock_summary = Mock()
    mock_perform_scan.return_value = mock_summary
    
    service = VideoScanService(
        config_provider=config_provider,
        result_handler=result_handler,
    )
    
    # Run scan
    summary = service.scan_directory()
    
    # Verify calls
    mock_find_files.assert_called_once()
    result_handler.handle_scan_start.assert_called_once_with(1, config_provider.get_scan_mode())
    mock_perform_scan.assert_called_once_with(video_files, config_provider.get_scan_mode())
    result_handler.handle_scan_complete.assert_called_once_with(mock_summary)
    
    assert summary is mock_summary


@pytest.mark.unit
@patch('pathlib.Path.glob')
def test_find_video_files(mock_glob):
    """Test finding video files in directory."""
    from src.core.models.inspection import VideoFile
    
    config_provider = Mock()
    result_handler = Mock()
    
    service = VideoScanService(
        config_provider=config_provider,
        result_handler=result_handler,
    )
    
    # Mock file paths
    mock_file1 = Mock()
    mock_file1.is_file.return_value = True
    mock_file1.suffix.lower.return_value = ".mp4"
    
    mock_file2 = Mock()
    mock_file2.is_file.return_value = True
    mock_file2.suffix.lower.return_value = ".txt"  # Not a video file
    
    mock_file3 = Mock()
    mock_file3.is_file.return_value = True
    mock_file3.suffix.lower.return_value = ".mkv"
    
    mock_glob.return_value = [mock_file1, mock_file2, mock_file3]
    
    # Test finding files
    video_files = service._find_video_files(
        directory=Path("/test"),
        recursive=True,
        extensions=[".mp4", ".mkv"]
    )
    
    # Should find 2 video files (mp4 and mkv, not txt)
    assert len(video_files) == 2
    
    # Verify glob was called with correct pattern
    mock_glob.assert_called_once_with("**/*")