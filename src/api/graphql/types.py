"""GraphQL type definitions using Strawberry."""

from datetime import datetime
from enum import Enum

import strawberry


@strawberry.enum
class ScanModeType(Enum):
    """Scan mode enumeration."""

    QUICK = "quick"
    DEEP = "deep"
    HYBRID = "hybrid"


@strawberry.enum
class FileStatusType(Enum):
    """File status enumeration."""

    HEALTHY = "healthy"
    CORRUPT = "corrupt"
    NEEDS_DEEP_SCAN = "needs_deep_scan"
    ERROR = "error"


@strawberry.type
class ScanResultType:
    """Individual scan result for a video file."""

    path: str
    is_corrupt: bool
    confidence: float
    error_message: str | None
    file_size_bytes: int
    scan_mode: ScanModeType
    status: FileStatusType
    needs_deep_scan: bool
    scanned_at: datetime


@strawberry.type
class ScanSummaryType:
    """Summary of a scan operation."""

    directory: str
    total_files: int
    processed_files: int
    corrupt_files: int
    healthy_files: int
    scan_mode: ScanModeType
    scan_time_seconds: float
    success_rate: float
    files_per_second: float
    started_at: datetime
    completed_at: datetime | None


@strawberry.type
class ScanJobType:
    """Information about a scan job."""

    id: str
    directory: str
    scan_mode: ScanModeType
    status: str
    started_at: datetime
    completed_at: datetime | None
    results_count: int


@strawberry.type
class ReportType:
    """Information about a generated report."""

    id: str
    format: str
    file_path: str
    created_at: datetime
    scan_summary: ScanSummaryType


@strawberry.input
class ScanInputType:
    """Input type for starting a scan."""

    directory: str
    scan_mode: ScanModeType = ScanModeType.QUICK
    recursive: bool = True
    resume: bool = True


@strawberry.input
class ReportInputType:
    """Input type for generating a report."""

    scan_job_id: str
    format: str = "json"
    include_healthy: bool = False
    pretty_print: bool = True


@strawberry.type
class DatabaseStatsType:
    """Statistics about the database contents."""

    total_scans: int
    total_files: int
    corrupt_files: int
    healthy_files: int
    oldest_scan: float | None
    newest_scan: float | None
    database_size_bytes: int


@strawberry.type
class CorruptionTrendDataType:
    """Corruption rate trend data point."""

    scan_date: str
    corrupt_files: int
    total_files: int
    corruption_rate: float


@strawberry.type
class ScanHistoryType:
    """Historical scan record."""

    id: int
    directory: str
    scan_mode: str
    started_at: float
    completed_at: float | None
    total_files: int
    processed_files: int
    corrupt_files: int
    healthy_files: int
    success_rate: float
    scan_time: float


@strawberry.type
class ScanResultHistoryType:
    """Historical scan result record."""

    id: int
    scan_id: int
    filename: str
    file_size: int
    is_corrupt: bool
    confidence: float
    inspection_time: float
    scan_mode: str
    status: str
    created_at: float


@strawberry.input
class DatabaseQueryFilterInput:
    """Filter options for database queries."""

    directory: str | None = None
    is_corrupt: bool | None = None
    scan_mode: str | None = None
    min_confidence: float | None = None
    max_confidence: float | None = None
    min_file_size: int | None = None
    max_file_size: int | None = None
    since_date: float | None = None
    until_date: float | None = None
    filename_pattern: str | None = None
    limit: int | None = None
    offset: int = 0
