
class ConfigurationError(CorruptVideoInspectorError):
    """Configuration-related errors.
    
    Raised when there are issues with application configuration,
    such as invalid config files, missing required settings, etc.
    """

    def __init__(
        self,
        message: str,
        config_path: Path | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize configuration error.
        
        Args:
            message: Error message
            config_path: Path to problematic config file
            cause: Underlying exception
        """
        super().__init__(message, cause)
        self.config_path = config_path

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data["config_path"] = str(self.config_path) if self.config_path else None
        return data


class ScanError(CorruptVideoInspectorError):
    """Scanning-related errors.
    
    Base class for errors that occur during the video scanning process.
    """

    def __init__(
        self,
        message: str,
        file_path: Path | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize scan error.
        
        Args:
            message: Error message
            file_path: Path to file that caused the error
            cause: Underlying exception
        """
        super().__init__(message, cause)
        self.file_path = file_path

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data["file_path"] = str(self.file_path) if self.file_path else None
        return data


class FFmpegError(ScanError):
    """FFmpeg-related errors.
    
    Raised when FFmpeg execution fails or produces unexpected output.
    """

    def __init__(
        self,
        message: str,
        file_path: Path | None = None,
        exit_code: int | None = None,
        stderr: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize FFmpeg error.
        
        Args:
            message: Error message
            file_path: Path to file being processed
            exit_code: FFmpeg exit code
            stderr: FFmpeg stderr output
            cause: Underlying exception
        """
        super().__init__(message, file_path, cause)
        self.exit_code = exit_code
        self.stderr = stderr

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "exit_code": self.exit_code,
            "stderr": self.stderr[:500] + "..." if self.stderr and len(self.stderr) > 500 else self.stderr,
        })
        return data


class TraktError(CorruptVideoInspectorError):
    """Trakt integration errors.
    
    Raised when communication with Trakt.tv API fails.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize Trakt error.
        
        Args:
            message: Error message
            status_code: HTTP status code from Trakt API
            response_body: Response body from Trakt API
            cause: Underlying exception
        """
        super().__init__(message, cause)
        self.status_code = status_code
        self.response_body = response_body

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "status_code": self.status_code,
            "response_body": self.response_body[:200] + "..." if self.response_body and len(self.response_body) > 200 else self.response_body,
        })
        return data


class StorageError(CorruptVideoInspectorError):
    """Storage and persistence errors.
    
    Raised when there are issues with file I/O, database operations,
    or other storage-related operations.
    """

    def __init__(
        self,
        message: str,
        file_path: Path | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize storage error.
        
        Args:
            message: Error message
            file_path: Path that caused the error
            cause: Underlying exception
        """
        super().__init__(message, cause)
        self.file_path = file_path

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data["file_path"] = str(self.file_path) if self.file_path else None
        return data
"""Exception hierarchy for Corrupt Video Inspector."""
from pathlib import Path
from typing import Any

class CorruptVideoInspectorError(Exception):
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause
    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message
    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "cause": str(self.cause) if self.cause else None,
        }

class ConfigurationError(CorruptVideoInspectorError):
    def __init__(self, message: str, config_path: Path | None = None, cause: Exception | None = None) -> None:
        super().__init__(message, cause)
        self.config_path = config_path
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["config_path"] = str(self.config_path) if self.config_path else None
        return data

class ScanError(CorruptVideoInspectorError):
    def __init__(self, message: str, file_path: Path | None = None, cause: Exception | None = None) -> None:
        super().__init__(message, cause)
        self.file_path = file_path
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["file_path"] = str(self.file_path) if self.file_path else None
        return data

class FFmpegError(ScanError):
    def __init__(self, message: str, file_path: Path | None = None, exit_code: int | None = None, stderr: str | None = None, cause: Exception | None = None) -> None:
        super().__init__(message, file_path, cause)
        self.exit_code = exit_code
        self.stderr = stderr
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "exit_code": self.exit_code,
            "stderr": self.stderr[:500] + "..." if self.stderr and len(self.stderr) > 500 else self.stderr,
        })
        return data

class TraktError(CorruptVideoInspectorError):
    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None, cause: Exception | None = None) -> None:
        super().__init__(message, cause)
        self.status_code = status_code
        self.response_body = response_body
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "status_code": self.status_code,
            "response_body": self.response_body[:200] + "..." if self.response_body and len(self.response_body) > 200 else self.response_body,
        })
        return data

class StorageError(CorruptVideoInspectorError):
    def __init__(self, message: str, file_path: Path | None = None, cause: Exception | None = None) -> None:
        super().__init__(message, cause)
        self.file_path = file_path
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["file_path"] = str(self.file_path) if self.file_path else None
        return data
