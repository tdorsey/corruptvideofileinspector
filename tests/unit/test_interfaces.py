"""
Unit tests for interface abstractions.

These tests validate that the interface abstractions work correctly
and that CLI adapters properly implement the abstract interfaces.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from src.interfaces.base import (
    ConfigurationProvider,
    ErrorHandler,
    ProgressReporter,
    ResultHandler,
)
from src.interfaces.factory import InterfaceFactory, InterfaceType


@pytest.mark.unit
def test_interface_factory_registration():
    """Test that interface factory registration works correctly."""
    # Create mock classes
    mock_config_provider = Mock(spec=ConfigurationProvider)
    mock_result_handler = Mock(spec=ResultHandler)
    mock_progress_reporter = Mock(spec=ProgressReporter)
    mock_error_handler = Mock(spec=ErrorHandler)
    
    # Register implementations
    InterfaceFactory.register_configuration_provider(InterfaceType.CLI, mock_config_provider)
    InterfaceFactory.register_result_handler(InterfaceType.CLI, mock_result_handler)
    InterfaceFactory.register_progress_reporter(InterfaceType.CLI, mock_progress_reporter)
    InterfaceFactory.register_error_handler(InterfaceType.CLI, mock_error_handler)
    
    # Test creation (this will call the mock classes as constructors)
    config_provider = InterfaceFactory.create_configuration_provider(InterfaceType.CLI)
    result_handler = InterfaceFactory.create_result_handler(InterfaceType.CLI)
    progress_reporter = InterfaceFactory.create_progress_reporter(InterfaceType.CLI)
    error_handler = InterfaceFactory.create_error_handler(InterfaceType.CLI)
    
    # Verify mocks were called (as constructors)
    mock_config_provider.assert_called_once()
    mock_result_handler.assert_called_once()
    mock_progress_reporter.assert_called_once()
    mock_error_handler.assert_called_once()


@pytest.mark.unit
def test_interface_factory_unregistered_type():
    """Test that factory raises error for unregistered interface types."""
    with pytest.raises(KeyError):
        InterfaceFactory.create_configuration_provider(InterfaceType.WEB)


@pytest.mark.unit
def test_configuration_provider_interface():
    """Test that ConfigurationProvider interface has required methods."""
    from src.core.models.scanning import ScanMode
    
    # Create a minimal implementation for testing
    class TestConfigProvider(ConfigurationProvider):
        def get_scan_mode(self) -> ScanMode:
            return ScanMode.QUICK
        
        def get_scan_directory(self) -> Path:
            return Path("/test")
        
        def get_max_workers(self) -> int:
            return 4
        
        def get_recursive_scan(self) -> bool:
            return True
        
        def get_file_extensions(self) -> list[str]:
            return [".mp4", ".mkv"]
        
        def get_resume_enabled(self) -> bool:
            return True
        
        def get_output_path(self) -> Path | None:
            return None
        
        def get_output_format(self) -> str:
            return "json"
        
        def get_ffmpeg_command(self) -> str | None:
            return None
        
        def get_timeout_quick(self) -> int:
            return 30
        
        def get_timeout_deep(self) -> int:
            return 300
    
    provider = TestConfigProvider()
    
    # Test that all interface methods work
    assert provider.get_scan_mode() == ScanMode.QUICK
    assert provider.get_scan_directory() == Path("/test")
    assert provider.get_max_workers() == 4
    assert provider.get_recursive_scan() is True
    assert provider.get_file_extensions() == [".mp4", ".mkv"]
    assert provider.get_resume_enabled() is True
    assert provider.get_output_path() is None
    assert provider.get_output_format() == "json"
    assert provider.get_ffmpeg_command() is None
    assert provider.get_timeout_quick() == 30
    assert provider.get_timeout_deep() == 300


@pytest.mark.unit
def test_result_handler_interface():
    """Test that ResultHandler interface has required methods."""
    from src.core.models.scanning import ScanMode, ScanProgress, ScanResult, ScanSummary
    from src.core.models.inspection import VideoFile
    
    class TestResultHandler(ResultHandler):
        def __init__(self):
            self.calls = []
        
        def handle_scan_start(self, total_files: int, scan_mode: ScanMode) -> None:
            self.calls.append(('start', total_files, scan_mode))
        
        def handle_progress_update(self, progress: ScanProgress) -> None:
            self.calls.append(('progress', progress))
        
        def handle_file_result(self, result: ScanResult) -> None:
            self.calls.append(('result', result))
        
        def handle_scan_complete(self, summary: ScanSummary) -> None:
            self.calls.append(('complete', summary))
        
        def handle_scan_error(self, error: Exception, context: dict) -> None:
            self.calls.append(('error', error, context))
    
    handler = TestResultHandler()
    
    # Test interface methods
    handler.handle_scan_start(10, ScanMode.QUICK)
    progress = ScanProgress(total_files=10, processed_count=5, scan_mode="quick")
    handler.handle_progress_update(progress)
    
    video_file = VideoFile(path=Path("/test.mp4"))
    result = ScanResult(video_file=video_file, is_corrupt=False)
    handler.handle_file_result(result)
    
    summary = ScanSummary(
        directory=Path("/test"),
        total_files=10,
        processed_files=10,
        corrupt_files=0,
        healthy_files=10,
        scan_mode=ScanMode.QUICK,
        scan_time=5.0
    )
    handler.handle_scan_complete(summary)
    
    error = Exception("Test error")
    handler.handle_scan_error(error, {"file": "/test.mp4"})
    
    # Verify all methods were called
    assert len(handler.calls) == 5
    assert handler.calls[0][0] == 'start'
    assert handler.calls[1][0] == 'progress'
    assert handler.calls[2][0] == 'result'
    assert handler.calls[3][0] == 'complete'
    assert handler.calls[4][0] == 'error'