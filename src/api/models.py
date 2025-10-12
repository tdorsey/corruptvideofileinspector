"""
API data models for request/response validation.
"""

from enum import Enum

from pydantic import BaseModel, Field

from src.core.models.scanning import ScanMode


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy")
    version: str = Field(description="API version")
    ffmpeg_available: bool = Field(description="Whether FFmpeg is available")


class ScanRequest(BaseModel):
    """Request to start a new scan."""

    directory: str = Field(description="Directory path to scan")
    mode: ScanMode = Field(default=ScanMode.QUICK, description="Scan mode")
    recursive: bool = Field(default=True, description="Scan subdirectories")
    max_workers: int = Field(default=8, ge=1, le=32, description="Number of worker threads")


class ScanStatusEnum(str, Enum):
    """Scan status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanResponse(BaseModel):
    """Response after starting a scan."""

    scan_id: str = Field(description="Unique scan identifier")
    status: ScanStatusEnum = Field(description="Current scan status")
    message: str = Field(description="Status message")


class ScanStatusResponse(BaseModel):
    """Detailed scan status response."""

    scan_id: str = Field(description="Unique scan identifier")
    status: ScanStatusEnum = Field(description="Current scan status")
    directory: str = Field(description="Directory being scanned")
    mode: str = Field(description="Scan mode")
    progress: dict = Field(default_factory=dict, description="Progress information")
    results: dict | None = Field(default=None, description="Scan results if completed")
    error: str | None = Field(default=None, description="Error message if failed")


class ScanResultsResponse(BaseModel):
    """Scan results response."""

    scan_id: str = Field(description="Unique scan identifier")
    results: dict = Field(description="Complete scan results")
    summary: dict = Field(description="Scan summary statistics")


class DatabaseStatsResponse(BaseModel):
    """Database statistics response."""

    total_files: int = Field(description="Total files in database")
    healthy_files: int = Field(description="Number of healthy files")
    corrupt_files: int = Field(description="Number of corrupt files")
    suspicious_files: int = Field(description="Number of suspicious files")
    last_scan_time: str | None = Field(default=None, description="Last scan timestamp")


class WebSocketMessage(BaseModel):
    """WebSocket message format."""

    type: str = Field(description="Message type (progress, status, error)")
    data: dict = Field(description="Message payload")
