"""
Example web API interface implementations.

This module demonstrates how the interface abstractions enable
easy creation of alternative presentation layers like web APIs.

NOTE: This is an example/demonstration module. It shows how the
refactored architecture enables future interfaces without modifying
core business logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models.scanning import ScanMode, ScanProgress, ScanResult, ScanSummary

from src.interfaces.base import (
    ConfigurationProvider,
    ErrorHandler,
    ProgressReporter,
    ResultHandler,
)


class WebAPIConfigurationProvider(ConfigurationProvider):
    """
    Web API configuration provider that gets settings from request data.
    
    This example shows how configuration can come from HTTP requests
    instead of CLI arguments or config files.
    """

    def __init__(self, request_data: Dict[str, Any]):
        """Initialize with request data from web API.
        
        Args:
            request_data: Dictionary containing request parameters
        """
        self._request_data = request_data

    def get_scan_mode(self) -> "ScanMode":
        """Get scan mode from request parameter."""
        from src.core.models.scanning import ScanMode
        mode_str = self._request_data.get("scan_mode", "quick")
        return ScanMode(mode_str.lower())

    def get_scan_directory(self) -> Path:
        """Get scan directory from request parameter."""
        directory = self._request_data.get("directory", "/uploads")
        return Path(directory)

    def get_max_workers(self) -> int:
        """Get max workers from request or default."""
        return self._request_data.get("max_workers", 4)

    def get_recursive_scan(self) -> bool:
        """Get recursive setting from request."""
        return self._request_data.get("recursive", True)

    def get_file_extensions(self) -> List[str]:
        """Get file extensions from request."""
        return self._request_data.get("extensions", [".mp4", ".mkv", ".avi"])

    def get_resume_enabled(self) -> bool:
        """Resume not typically used in web API context."""
        return False

    def get_output_path(self) -> Path | None:
        """Web API typically returns results in response, not files."""
        return None

    def get_output_format(self) -> str:
        """Web API typically uses JSON."""
        return "json"

    def get_ffmpeg_command(self) -> str | None:
        """Use default FFmpeg command."""
        return None

    def get_timeout_quick(self) -> int:
        """Get quick timeout from request or default."""
        return self._request_data.get("quick_timeout", 30)

    def get_timeout_deep(self) -> int:
        """Get deep timeout from request or default."""
        return self._request_data.get("deep_timeout", 300)


class WebAPIResultHandler(ResultHandler):
    """
    Web API result handler that collects results for HTTP response.
    
    This example shows how results can be collected for JSON response
    instead of console output or file writing.
    """

    def __init__(self):
        """Initialize the web API result handler."""
        self._results: List[Dict[str, Any]] = []
        self._summary: Dict[str, Any] | None = None
        self._errors: List[Dict[str, Any]] = []

    def handle_scan_start(self, total_files: int, scan_mode: "ScanMode") -> None:
        """Record scan start information."""
        self._start_info = {
            "total_files": total_files,
            "scan_mode": scan_mode.value,
            "status": "started"
        }

    def handle_progress_update(self, progress: "ScanProgress") -> None:
        """Progress updates for web API could be sent via WebSocket."""
        # In a real implementation, this might push to WebSocket
        pass

    def handle_file_result(self, result: "ScanResult") -> None:
        """Collect file result for response."""
        self._results.append({
            "file": str(result.video_file.path),
            "is_corrupt": result.is_corrupt,
            "needs_deep_scan": result.needs_deep_scan,
            "error_message": result.error_message or None,
        })

    def handle_scan_complete(self, summary: "ScanSummary") -> None:
        """Record scan completion information."""
        self._summary = {
            "directory": str(summary.directory),
            "total_files": summary.total_files,
            "processed_files": summary.processed_files,
            "corrupt_files": summary.corrupt_files,
            "healthy_files": summary.healthy_files,
            "scan_mode": summary.scan_mode.value,
            "scan_time": summary.scan_time,
            "status": "completed"
        }

    def handle_scan_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Record scan error for response."""
        self._errors.append({
            "error": str(error),
            "context": context,
        })

    def get_response_data(self) -> Dict[str, Any]:
        """Get collected data for HTTP response.
        
        Returns:
            Dictionary suitable for JSON response
        """
        return {
            "summary": self._summary,
            "results": self._results,
            "errors": self._errors,
        }


class WebAPIProgressReporter(ProgressReporter):
    """
    Web API progress reporter using WebSocket or similar.
    
    This example shows how progress could be reported via WebSocket
    instead of console progress bars.
    """

    def __init__(self, websocket_connection=None):
        """Initialize with optional WebSocket connection.
        
        Args:
            websocket_connection: Optional WebSocket for live progress
        """
        self._websocket = websocket_connection
        self._cancelled = False

    def report_progress(self, progress: "ScanProgress") -> None:
        """Report progress via WebSocket."""
        if self._websocket:
            progress_data = {
                "type": "progress",
                "processed": progress.processed_count,
                "total": progress.total_files,
                "current_file": progress.current_file,
                "corrupt_count": progress.corrupt_count,
            }
            # In real implementation: self._websocket.send(json.dumps(progress_data))

    def is_cancelled(self) -> bool:
        """Check if client cancelled the operation."""
        return self._cancelled

    def cancel(self) -> None:
        """Allow client to cancel operation."""
        self._cancelled = True


class WebAPIErrorHandler(ErrorHandler):
    """
    Web API error handler that collects errors for HTTP response.
    
    This example shows how errors can be handled for web APIs
    with appropriate HTTP status codes.
    """

    def __init__(self):
        """Initialize the web API error handler."""
        self._errors: List[Dict[str, Any]] = []

    def handle_validation_error(self, message: str, details: Dict[str, Any] | None = None) -> None:
        """Handle validation error (HTTP 400)."""
        self._errors.append({
            "type": "validation",
            "message": message,
            "details": details,
            "http_status": 400,
        })

    def handle_configuration_error(self, message: str, details: Dict[str, Any] | None = None) -> None:
        """Handle configuration error (HTTP 400)."""
        self._errors.append({
            "type": "configuration",
            "message": message,
            "details": details,
            "http_status": 400,
        })

    def handle_processing_error(self, message: str, exception: Exception | None = None) -> None:
        """Handle processing error (HTTP 500)."""
        self._errors.append({
            "type": "processing",
            "message": message,
            "exception": str(exception) if exception else None,
            "http_status": 500,
        })

    def handle_fatal_error(self, message: str, exception: Exception | None = None) -> None:
        """Handle fatal error (HTTP 500)."""
        self._errors.append({
            "type": "fatal",
            "message": message,
            "exception": str(exception) if exception else None,
            "http_status": 500,
        })

    def get_errors(self) -> List[Dict[str, Any]]:
        """Get collected errors for response."""
        return self._errors

    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self._errors) > 0

    def get_http_status(self) -> int:
        """Get appropriate HTTP status code based on errors."""
        if not self._errors:
            return 200
        
        # Return highest severity status code
        statuses = [error["http_status"] for error in self._errors]
        return max(statuses)


# Example usage function showing how easy it is to use core business logic
# with a different presentation layer
def scan_via_web_api(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example function showing how to use the scan service for a web API.
    
    This demonstrates how the same core business logic can be used
    with completely different presentation layer without modification.
    
    Args:
        request_data: HTTP request data containing scan parameters
        
    Returns:
        Dictionary suitable for JSON HTTP response
    """
    from src.core.scan_service import VideoScanService
    
    # Create web API specific implementations
    config_provider = WebAPIConfigurationProvider(request_data)
    result_handler = WebAPIResultHandler()
    progress_reporter = WebAPIProgressReporter()
    error_handler = WebAPIErrorHandler()
    
    try:
        # Use the same core service as CLI
        scan_service = VideoScanService(
            config_provider=config_provider,
            result_handler=result_handler,
            progress_reporter=progress_reporter,
        )
        
        # Run the scan
        summary = scan_service.scan_directory()
        
        # Return web API appropriate response
        response_data = result_handler.get_response_data()
        response_data["status"] = "success"
        response_data["http_status"] = 200
        
        return response_data
        
    except Exception as e:
        error_handler.handle_fatal_error("Scan failed", e)
        
        return {
            "status": "error",
            "errors": error_handler.get_errors(),
            "http_status": error_handler.get_http_status(),
        }