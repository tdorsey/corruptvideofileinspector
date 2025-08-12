"""
Base interface abstractions for presentation layer independence.

These abstract base classes define the contracts that any presentation layer
must implement to interact with the core business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models.scanning import ScanMode, ScanProgress, ScanResult, ScanSummary


class ConfigurationProvider(ABC):
    """Abstract interface for providing configuration to core modules.
    
    This allows core modules to receive configuration from any source
    (CLI arguments, config files, environment variables, API requests, etc.)
    without being coupled to any specific configuration mechanism.
    """

    @abstractmethod
    def get_scan_mode(self) -> "ScanMode":
        """Get the scan mode to use."""
        pass

    @abstractmethod
    def get_scan_directory(self) -> Path:
        """Get the directory to scan."""
        pass

    @abstractmethod
    def get_max_workers(self) -> int:
        """Get the maximum number of worker threads."""
        pass

    @abstractmethod
    def get_recursive_scan(self) -> bool:
        """Check if subdirectories should be scanned recursively."""
        pass

    @abstractmethod
    def get_file_extensions(self) -> List[str]:
        """Get the list of video file extensions to include."""
        pass

    @abstractmethod
    def get_resume_enabled(self) -> bool:
        """Check if scan resumption is enabled."""
        pass

    @abstractmethod
    def get_output_path(self) -> Path | None:
        """Get the output file path, if specified."""
        pass

    @abstractmethod
    def get_output_format(self) -> str:
        """Get the output format (json, yaml, csv, etc.)."""
        pass

    @abstractmethod
    def get_ffmpeg_command(self) -> str | None:
        """Get the FFmpeg command path, if specified."""
        pass

    @abstractmethod
    def get_timeout_quick(self) -> int:
        """Get the timeout for quick scans in seconds."""
        pass

    @abstractmethod
    def get_timeout_deep(self) -> int:
        """Get the timeout for deep scans in seconds."""
        pass


class ResultHandler(ABC):
    """Abstract interface for handling scan results.
    
    This allows core modules to output results to any destination
    (console, files, web responses, GUI displays, etc.) without being
    coupled to any specific output mechanism.
    """

    @abstractmethod
    def handle_scan_start(self, total_files: int, scan_mode: "ScanMode") -> None:
        """Handle the start of a scan operation.
        
        Args:
            total_files: Total number of files to be scanned
            scan_mode: The scan mode being used
        """
        pass

    @abstractmethod
    def handle_progress_update(self, progress: "ScanProgress") -> None:
        """Handle a progress update during scanning.
        
        Args:
            progress: Current scan progress information
        """
        pass

    @abstractmethod
    def handle_file_result(self, result: "ScanResult") -> None:
        """Handle the result of scanning a single file.
        
        Args:
            result: The scan result for a single file
        """
        pass

    @abstractmethod
    def handle_scan_complete(self, summary: "ScanSummary") -> None:
        """Handle the completion of a scan operation.
        
        Args:
            summary: Summary of the completed scan
        """
        pass

    @abstractmethod
    def handle_scan_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Handle an error during scanning.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        pass


class ProgressReporter(ABC):
    """Abstract interface for reporting progress updates.
    
    This allows core modules to report progress to any UI paradigm
    (CLI progress bars, web sockets, GUI progress dialogs, etc.)
    without being coupled to any specific progress reporting mechanism.
    """

    @abstractmethod
    def report_progress(self, progress: "ScanProgress") -> None:
        """Report scan progress.
        
        Args:
            progress: Current progress information
        """
        pass

    @abstractmethod
    def is_cancelled(self) -> bool:
        """Check if the operation should be cancelled.
        
        Returns:
            True if the operation should be cancelled
        """
        pass


class ErrorHandler(ABC):
    """Abstract interface for handling errors in a presentation-appropriate way.
    
    This allows core modules to report errors without being coupled to
    any specific error handling mechanism (CLI error messages, web error
    responses, GUI error dialogs, etc.).
    """

    @abstractmethod
    def handle_validation_error(self, message: str, details: Dict[str, Any] | None = None) -> None:
        """Handle a validation error.
        
        Args:
            message: Human-readable error message
            details: Optional additional error details
        """
        pass

    @abstractmethod
    def handle_configuration_error(self, message: str, details: Dict[str, Any] | None = None) -> None:
        """Handle a configuration error.
        
        Args:
            message: Human-readable error message
            details: Optional additional error details
        """
        pass

    @abstractmethod
    def handle_processing_error(self, message: str, exception: Exception | None = None) -> None:
        """Handle a processing error.
        
        Args:
            message: Human-readable error message
            exception: Optional underlying exception
        """
        pass

    @abstractmethod
    def handle_fatal_error(self, message: str, exception: Exception | None = None) -> None:
        """Handle a fatal error that should terminate the operation.
        
        Args:
            message: Human-readable error message
            exception: Optional underlying exception
        """
        pass