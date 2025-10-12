"""GraphQL type definitions using Strawberry."""

from datetime import datetime
from enum import Enum
from typing import Optional

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
    error_message: Optional[str]
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
    completed_at: Optional[datetime]


@strawberry.type
class ScanJobType:
    """Information about a scan job."""

    id: str
    directory: str
    scan_mode: ScanModeType
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
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
