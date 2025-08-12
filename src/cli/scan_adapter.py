"""
CLI integration adapter for the interface-agnostic scan service.

This module provides a bridge between the existing CLI handler code and
the new interface-agnostic scan service, maintaining backward compatibility
while using the new architecture internally.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.core.scan_service import VideoScanService
from src.interfaces.cli.adapters import (
    CLIConfigurationProvider,
    CLIErrorHandler,
    CLIProgressReporter,
    CLIResultHandler,
)

if TYPE_CHECKING:
    from src.config.config import AppConfig
    from src.core.models.scanning import ScanMode, ScanSummary


class CLIScanServiceAdapter:
    """
    CLI adapter for the interface-agnostic scan service.
    
    This class provides a CLI-friendly interface to the VideoScanService
    while maintaining backward compatibility with existing CLI handler code.
    """

    def __init__(self, config: "AppConfig"):
        """Initialize the CLI scan service adapter.
        
        Args:
            config: Application configuration
        """
        self._config = config

    def run_scan(
        self,
        directory: Path,
        scan_mode: "ScanMode",
        recursive: bool = True,
        resume: bool = True,
        output_file: Path | None = None,
        output_format: str = "json",
        pretty_print: bool = True,
        verbose: bool = True,
    ) -> "ScanSummary":
        """
        Run a video scan using the interface-agnostic service.
        
        This method provides the same interface as the existing CLI handlers
        but uses the new dependency injection architecture internally.
        
        Args:
            directory: Directory to scan
            scan_mode: Type of scan to perform
            recursive: Whether to scan subdirectories
            resume: Whether to resume from previous scan state
            output_file: Optional output file path
            output_format: Output format (json, yaml, csv)
            pretty_print: Whether to pretty-print output
            verbose: Whether to show verbose output
            
        Returns:
            Summary of the scan operation
        """
        # Create a temporary configuration override
        class ScanConfigurationProvider(CLIConfigurationProvider):
            def __init__(self, base_config, **overrides):
                super().__init__(base_config)
                self._overrides = overrides
            
            def get_scan_mode(self):
                return self._overrides.get('scan_mode', super().get_scan_mode())
            
            def get_scan_directory(self):
                return self._overrides.get('directory', super().get_scan_directory())
            
            def get_recursive_scan(self):
                return self._overrides.get('recursive', super().get_recursive_scan())

        # Create interface implementations
        config_provider = ScanConfigurationProvider(
            self._config,
            scan_mode=scan_mode,
            directory=directory,
            recursive=recursive,
        )
        
        result_handler = CLIResultHandler(
            output_path=output_file,
            output_format=output_format,
            verbose=verbose,
        )
        
        progress_reporter = CLIProgressReporter(show_progress=verbose)
        
        # Create and run the scan service
        scan_service = VideoScanService(
            config_provider=config_provider,
            result_handler=result_handler,
            progress_reporter=progress_reporter,
        )
        
        return scan_service.scan_directory(directory)

    def list_files(
        self,
        directory: Path,
        recursive: bool = True,
        output_file: Path | None = None,
        output_format: str = "text",
    ) -> list:
        """
        List video files using the interface-agnostic service.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            output_file: Optional output file path
            output_format: Output format (text, json, csv)
            
        Returns:
            List of found video files
        """
        # For now, use existing logic - this can be refactored later
        # to use interface-agnostic service when we add file listing to it
        from src.core.scanner import VideoScanner
        
        scanner = VideoScanner(self._config)
        return scanner.get_video_files(directory, recursive=recursive)