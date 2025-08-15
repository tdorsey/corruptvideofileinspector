"""Database models for scan results persistence."""

import time
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.core.models.scanning import ScanMode, ScanResult, ScanSummary


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
    """Database model for individual scan results.

    Maps to the 'scan_results' table in SQLite database.
    """

    id: int | None = Field(None, description="Primary key (auto-generated)")
    scan_id: int = Field(..., description="Foreign key to scans table")
    filename: str = Field(..., description="Full path to the video file")
    file_size: int = Field(..., description="File size in bytes")
    is_corrupt: bool = Field(..., description="Whether file is corrupt")
    confidence: float = Field(..., description="Confidence level (0.0-1.0)")
    inspection_time: float = Field(..., description="Time taken to scan file")
    scan_mode: str = Field(..., description="Scan mode used for this file")
    status: str = Field(..., description="File status (HEALTHY/CORRUPT/SUSPICIOUS)")
    created_at: float = Field(default_factory=time.time, description="When record was created")

    @classmethod
    def from_scan_result(cls, result: ScanResult, scan_id: int) -> "ScanResultDatabaseModel":
        """Create database model from ScanResult.

        Args:
            result: ScanResult object to convert
            scan_id: ID of the scan this result belongs to

        Returns:
            ScanResultDatabaseModel instance
        """
        return cls(
            scan_id=scan_id,
            filename=str(result.video_file.path),
            file_size=result.video_file.size,
            is_corrupt=result.is_corrupt,
            confidence=result.confidence,
            inspection_time=result.inspection_time,
            scan_mode=result.scan_mode.value,
            status=result.status,
            created_at=result.timestamp,
        )

    def to_scan_result(self) -> ScanResult:
        """Convert to ScanResult object.

        Note: This creates a basic ScanResult. The VideoFile will only have
        path and size information from the database.

        Returns:
            ScanResult instance
        """
        from src.core.models.inspection import VideoFile

        video_file = VideoFile(path=Path(self.filename))

        return ScanResult(
            video_file=video_file,
            is_corrupt=self.is_corrupt,
            confidence=self.confidence,
            inspection_time=self.inspection_time,
            scan_mode=ScanMode(self.scan_mode),
            timestamp=self.created_at,
        )


class DatabaseQueryFilter(BaseModel):
    """Filter options for database queries."""

    directory: str | None = Field(None, description="Filter by directory")
    is_corrupt: bool | None = Field(None, description="Filter by corruption status")
    scan_mode: str | None = Field(None, description="Filter by scan mode")
    min_confidence: float | None = Field(None, description="Minimum confidence level")
    max_confidence: float | None = Field(None, description="Maximum confidence level")
    min_file_size: int | None = Field(None, description="Minimum file size")
    max_file_size: int | None = Field(None, description="Maximum file size")
    since_date: float | None = Field(None, description="Filter results since timestamp")
    until_date: float | None = Field(None, description="Filter results until timestamp")
    filename_pattern: str | None = Field(None, description="SQL LIKE pattern for filename")
    limit: int | None = Field(None, description="Maximum number of results")
    offset: int = Field(0, description="Number of results to skip")

    def to_where_clause(self) -> tuple[str, dict[str, Any]]:
        """Generate SQL WHERE clause and parameters.

        Returns:
            Tuple of (where_clause, parameters)
        """
        conditions = []
        params = {}

        if self.directory is not None:
            conditions.append("s.directory = :directory")
            params["directory"] = self.directory

        if self.is_corrupt is not None:
            conditions.append("sr.is_corrupt = :is_corrupt")
            params["is_corrupt"] = self.is_corrupt

        if self.scan_mode is not None:
            conditions.append("sr.scan_mode = :scan_mode")
            params["scan_mode"] = self.scan_mode

        if self.min_confidence is not None:
            conditions.append("sr.confidence >= :min_confidence")
            params["min_confidence"] = self.min_confidence

        if self.max_confidence is not None:
            conditions.append("sr.confidence <= :max_confidence")
            params["max_confidence"] = self.max_confidence

        if self.min_file_size is not None:
            conditions.append("sr.file_size >= :min_file_size")
            params["min_file_size"] = self.min_file_size

        if self.max_file_size is not None:
            conditions.append("sr.file_size <= :max_file_size")
            params["max_file_size"] = self.max_file_size

        if self.since_date is not None:
            conditions.append("sr.created_at >= :since_date")
            params["since_date"] = self.since_date

        if self.until_date is not None:
            conditions.append("sr.created_at <= :until_date")
            params["until_date"] = self.until_date

        if self.filename_pattern is not None:
            conditions.append("sr.filename LIKE :filename_pattern")
            params["filename_pattern"] = self.filename_pattern

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params


class DatabaseStats(BaseModel):
    """Statistics about the database contents."""

    total_scans: int = Field(..., description="Total number of scans")
    total_files: int = Field(..., description="Total number of files scanned")
    corrupt_files: int = Field(..., description="Total number of corrupt files")
    healthy_files: int = Field(..., description="Total number of healthy files")
    oldest_scan: float | None = Field(None, description="Timestamp of oldest scan")
    newest_scan: float | None = Field(None, description="Timestamp of newest scan")
    database_size_bytes: int = Field(..., description="Database file size in bytes")

    @property
    def corruption_rate(self) -> float:
        """Calculate overall corruption rate percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.corrupt_files / self.total_files) * 100.0

    @property
    def oldest_scan_date(self) -> datetime | None:
        """Get oldest scan as datetime object."""
        if self.oldest_scan is None:
            return None
        return datetime.fromtimestamp(self.oldest_scan)

    @property
    def newest_scan_date(self) -> datetime | None:
        """Get newest scan as datetime object."""
        if self.newest_scan is None:
            return None
        return datetime.fromtimestamp(self.newest_scan)
