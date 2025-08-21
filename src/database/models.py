"""Database models for scan results persistence."""

import json
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.core.models.inspection import VideoFile
from src.core.models.scanning import ScanMode, ScanResult, ScanSummary


# New Probe-related enums and models
class ProbeType(str, Enum):
    """Type of probe operation."""
    CONTAINER = "container"
    STREAM = "stream"


class ProbeStatus(str, Enum):
    """Status of probe operation."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ProbeResultBase(BaseModel):
    """Base class for all probe results."""
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    probe_duration_ms: Optional[int] = None


class ContainerProbeResult(ProbeResultBase):
    """Container-level probe results (format, metadata, overall file health)."""
    format_name: Optional[str] = None
    duration: Optional[float] = None
    size: Optional[int] = None
    bitrate: Optional[int] = None
    streams_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    container_errors: List[str] = Field(default_factory=list)
    is_video_file: bool = False  # Determined by successful container probe


class StreamProbeResult(ProbeResultBase):
    """Individual stream analysis results."""
    stream_index: int
    codec_name: Optional[str] = None
    codec_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_rate: Optional[str] = None
    duration: Optional[float] = None
    bit_rate: Optional[int] = None
    stream_errors: List[str] = Field(default_factory=list)


class VideoFileModel(BaseModel):
    """Central video file entity."""
    id: Optional[int] = None
    file_path: str = Field(..., description="Full path to video file")
    file_name: str = Field(..., description="Filename without path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_hash: Optional[str] = Field(None, description="File hash for integrity")
    first_seen: datetime = Field(default_factory=datetime.now)
    last_modified: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True


class ProbeModel(BaseModel):
    """Main probe execution model."""
    id: Optional[int] = None
    video_file_id: int
    probe_type: ProbeType
    status: ProbeStatus = ProbeStatus.PENDING
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    triggered_by_scan_id: Optional[int] = None  # Optional link to triggering scan
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Related models
    video_file: Optional[VideoFileModel] = None
    results: List["ProbeResultModel"] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class ProbeResultModel(BaseModel):
    """Individual probe result data."""
    id: Optional[int] = None
    probe_id: int
    result_type: str  # 'container_info', 'stream_info'
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    data_json: str  # Serialized probe-specific data
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
    
    @property
    def data(self) -> Dict[str, Any]:
        """Deserialize JSON data."""
        return json.loads(self.data_json)


class ScanDatabaseModel(BaseModel):
    """Database model for scan metadata.

    Maps to the 'scans' table in SQLite database.
    """

    id: int | None = Field(None, description="Primary key (auto-generated)")
    directory: str = Field(..., description="Directory that was scanned")
    scan_mode: str = Field(..., description="Scan mode used (quick/deep/hybrid)")
    started_at: float = Field(..., description="Timestamp when scan started")
    completed_at: float | None = Field(None, description="Timestamp when scan completed")
    total_files: int = Field(..., description="Total number of files found")
    processed_files: int = Field(..., description="Number of files processed")
    corrupt_files: int = Field(..., description="Number of corrupt files found")
    healthy_files: int = Field(..., description="Number of healthy files")
    success_rate: float = Field(..., description="Success rate percentage")
    scan_time: float = Field(..., description="Total scan time in seconds")

    @classmethod
    def from_scan_summary(cls, summary: ScanSummary) -> "ScanDatabaseModel":
        """Create database model from ScanSummary.

        Args:
            summary: ScanSummary object to convert

        Returns:
            ScanDatabaseModel instance
        """
        return cls(
            directory=str(summary.directory),
            scan_mode=summary.scan_mode.value,
            started_at=summary.started_at,
            completed_at=summary.completed_at,
            total_files=summary.total_files,
            processed_files=summary.processed_files,
            corrupt_files=summary.corrupt_files,
            healthy_files=summary.healthy_files,
            success_rate=summary.success_rate,
            scan_time=summary.scan_time,
        )

    def to_scan_summary(self) -> ScanSummary:
        """Convert to ScanSummary object.

        Returns:
            ScanSummary instance
        """
        return ScanSummary(
            directory=Path(self.directory),
            scan_mode=ScanMode(self.scan_mode),
            total_files=self.total_files,
            processed_files=self.processed_files,
            corrupt_files=self.corrupt_files,
            healthy_files=self.healthy_files,
            scan_time=self.scan_time,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )


class ScanResultDatabaseModel(BaseModel):
    """Database model for individual file result within a scan.
    
    Maps to the 'scan_results' table in SQLite database.
    Links scans to video files with corruption status.
    """

    id: Optional[int] = Field(None, description="Primary key (auto-generated)")
    scan_id: int = Field(..., description="Foreign key to scans table")
    video_file_id: int = Field(..., description="Foreign key to video_files table")
    is_corrupt: bool = Field(default=False, description="Whether file is corrupt")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level")
    scan_time_ms: Optional[int] = Field(None, description="Time taken to scan file in ms")
    created_at: datetime = Field(default_factory=datetime.now, description="When record was created")
    
    # Related models (populated by joins)
    video_file: Optional[VideoFileModel] = None
    
    class Config:
        from_attributes = True

    @classmethod
    def from_scan_result(cls, result: ScanResult, scan_id: int, video_file_id: int) -> "ScanResultDatabaseModel":
        """Create database model from ScanResult.

        Args:
            result: ScanResult object to convert
            scan_id: ID of the scan this result belongs to
            video_file_id: ID of the video file

        Returns:
            ScanResultDatabaseModel instance
        """
        return cls(
            scan_id=scan_id,
            video_file_id=video_file_id,
            is_corrupt=result.is_corrupt,
            confidence=result.confidence,
            scan_time_ms=int(result.inspection_time * 1000) if result.inspection_time else None,
            created_at=datetime.fromtimestamp(result.timestamp),
        )

    def to_scan_result(self) -> ScanResult:
        """Convert to ScanResult object.

        Note: This creates a basic ScanResult. The VideoFile information
        should be provided via the video_file relationship.

        Returns:
            ScanResult instance
        """
        if not self.video_file:
            raise ValueError("video_file relationship must be populated to convert to ScanResult")
            
        video_file = VideoFile(path=Path(self.video_file.file_path))

        return ScanResult(
            video_file=video_file,
            is_corrupt=self.is_corrupt,
            confidence=self.confidence or 0.0,
            inspection_time=(self.scan_time_ms / 1000.0) if self.scan_time_ms else 0.0,
            timestamp=self.created_at.timestamp(),
        )


class DatabaseQueryFilter(BaseModel):
    """Filter options for database queries."""

    directory: Optional[str] = Field(None, description="Filter by directory")
    is_corrupt: Optional[bool] = Field(None, description="Filter by corruption status")
    scan_mode: Optional[str] = Field(None, description="Filter by scan mode")
    min_confidence: Optional[float] = Field(None, description="Minimum confidence level")
    max_confidence: Optional[float] = Field(None, description="Maximum confidence level")
    min_file_size: Optional[int] = Field(None, description="Minimum file size")
    max_file_size: Optional[int] = Field(None, description="Maximum file size")
    since_date: Optional[float] = Field(None, description="Filter results since timestamp")
    until_date: Optional[float] = Field(None, description="Filter results until timestamp")
    filename_pattern: Optional[str] = Field(None, description="SQL LIKE pattern for filename")
    limit: Optional[int] = Field(None, description="Maximum number of results")
    offset: int = Field(0, description="Number of results to skip")
    video_files_only: bool = Field(False, description="Only include files confirmed as video files")
    include_probe_data: bool = Field(False, description="Include probe results in output")

    def to_where_clause(self) -> tuple[str, Dict[str, Any]]:
        """Generate SQL WHERE clause and parameters.

        Returns:
            Tuple of (where_clause, parameters)
        """
        conditions = []
        params: Dict[str, Any] = {}

        if self.directory is not None:
            conditions.append("s.directory = :directory")
            params["directory"] = self.directory

        if self.is_corrupt is not None:
            conditions.append("sr.is_corrupt = :is_corrupt")
            params["is_corrupt"] = self.is_corrupt

        if self.scan_mode is not None:
            conditions.append("s.scan_mode = :scan_mode")
            params["scan_mode"] = self.scan_mode

        if self.min_confidence is not None:
            conditions.append("sr.confidence >= :min_confidence")
            params["min_confidence"] = self.min_confidence

        if self.max_confidence is not None:
            conditions.append("sr.confidence <= :max_confidence")
            params["max_confidence"] = self.max_confidence

        if self.min_file_size is not None:
            conditions.append("vf.file_size >= :min_file_size")
            params["min_file_size"] = self.min_file_size

        if self.max_file_size is not None:
            conditions.append("vf.file_size <= :max_file_size")
            params["max_file_size"] = self.max_file_size

        if self.since_date is not None:
            conditions.append("sr.created_at >= :since_date")
            params["since_date"] = self.since_date

        if self.until_date is not None:
            conditions.append("sr.created_at <= :until_date")
            params["until_date"] = self.until_date

        if self.filename_pattern is not None:
            conditions.append("vf.file_path LIKE :filename_pattern")
            params["filename_pattern"] = self.filename_pattern

        if self.video_files_only:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM probes p 
                    WHERE p.video_file_id = vf.id 
                    AND p.probe_type = 'container' 
                    AND p.success = true
                )
            """)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params


class DatabaseStats(BaseModel):
    """Statistics about the database contents."""

    total_scans: int = Field(..., description="Total number of scans")
    total_files: int = Field(..., description="Total number of files scanned")
    total_video_files: int = Field(..., description="Total number of confirmed video files")
    corrupt_files: int = Field(..., description="Total number of corrupt files")
    healthy_files: int = Field(..., description="Total number of healthy files")
    total_probes: int = Field(..., description="Total number of probe operations")
    successful_probes: int = Field(..., description="Number of successful probes")
    oldest_scan: Optional[float] = Field(None, description="Timestamp of oldest scan")
    newest_scan: Optional[float] = Field(None, description="Timestamp of newest scan")
    database_size_bytes: int = Field(..., description="Database file size in bytes")

    @property
    def corruption_rate(self) -> float:
        """Calculate overall corruption rate percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.corrupt_files / self.total_files) * 100.0

    @property
    def probe_success_rate(self) -> float:
        """Calculate probe success rate percentage."""
        if self.total_probes == 0:
            return 0.0
        return (self.successful_probes / self.total_probes) * 100.0

    @property
    def oldest_scan_date(self) -> Optional[datetime]:
        """Get oldest scan as datetime object."""
        if self.oldest_scan is None:
            return None
        return datetime.fromtimestamp(self.oldest_scan)

    @property
    def newest_scan_date(self) -> Optional[datetime]:
        """Get newest scan as datetime object."""
        if self.newest_scan is None:
            return None
        return datetime.fromtimestamp(self.newest_scan)
