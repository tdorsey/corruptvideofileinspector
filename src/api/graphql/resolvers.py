"""GraphQL resolvers for queries and mutations."""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import strawberry
from strawberry.types import Info

from src.api.graphql.types import (
    CorruptionTrendDataType,
    DatabaseQueryFilterInput,
    DatabaseStatsType,
    FileStatusType,
    ReportInputType,
    ReportType,
    ScanHistoryType,
    ScanInputType,
    ScanJobType,
    ScanModeType,
    ScanResultHistoryType,
    ScanResultType,
    ScanSummaryType,
)
from src.cli.handlers import ScanHandler
from src.config.config import AppConfig
from src.core.models.scanning import (
    FileStatus,
    ScanMode,
    ScanResult,
    ScanSummary,
)
from src.core.reporter import ReportService
from src.database.models import DatabaseQueryFilter
from src.database.service import DatabaseService

logger = logging.getLogger(__name__)

# In-memory storage for scan jobs and results (in production, use a database)
_scan_jobs: dict[str, dict[str, Any]] = {}
_scan_results: dict[str, list[ScanResult]] = {}


def convert_scan_mode(mode: ScanModeType) -> ScanMode:
    """Convert GraphQL scan mode to internal scan mode."""
    mapping = {
        ScanModeType.QUICK: ScanMode.QUICK,
        ScanModeType.DEEP: ScanMode.DEEP,
        ScanModeType.HYBRID: ScanMode.HYBRID,
    }
    return mapping[mode]


def convert_scan_mode_to_graphql(mode: ScanMode) -> ScanModeType:
    """Convert internal scan mode to GraphQL scan mode."""
    mapping = {
        ScanMode.QUICK: ScanModeType.QUICK,
        ScanMode.DEEP: ScanModeType.DEEP,
        ScanMode.HYBRID: ScanModeType.HYBRID,
    }
    return mapping[mode]


def convert_file_status(status: FileStatus) -> FileStatusType:
    """Convert internal file status to GraphQL file status."""
    mapping = {
        FileStatus.HEALTHY: FileStatusType.HEALTHY,
        FileStatus.CORRUPT: FileStatusType.CORRUPT,
        FileStatus.NEEDS_DEEP_SCAN: FileStatusType.NEEDS_DEEP_SCAN,
        FileStatus.ERROR: FileStatusType.ERROR,
    }
    return mapping.get(status, FileStatusType.ERROR)


def convert_scan_result_to_graphql(result: ScanResult) -> ScanResultType:
    """Convert internal scan result to GraphQL type."""
    return ScanResultType(
        path=str(result.video_file.path),
        is_corrupt=result.is_corrupt,
        confidence=result.confidence,
        error_message=result.error_message,
        file_size_bytes=result.video_file.size_bytes,
        scan_mode=convert_scan_mode_to_graphql(result.scan_mode),
        status=convert_file_status(result.get_status()),
        needs_deep_scan=result.needs_deep_scan,
        scanned_at=datetime.now(),
    )


def convert_scan_summary_to_graphql(summary: ScanSummary) -> ScanSummaryType:
    """Convert internal scan summary to GraphQL type."""
    return ScanSummaryType(
        directory=str(summary.directory),
        total_files=summary.total_files,
        processed_files=summary.processed_files,
        corrupt_files=summary.corrupt_files,
        healthy_files=summary.healthy_files,
        scan_mode=convert_scan_mode_to_graphql(summary.scan_mode),
        scan_time_seconds=summary.scan_time,
        success_rate=summary.success_rate,
        files_per_second=summary.files_per_second,
        started_at=summary.start_time,
        completed_at=summary.end_time,
    )


def get_database_service(config: AppConfig) -> DatabaseService | None:
    """Get database service from configuration.

    Args:
        config: Application configuration

    Returns:
        DatabaseService instance
    """
    if not hasattr(config, "database") or not config.database:
        return None

    db_path = Path(config.database.path).expanduser()
    auto_cleanup_days = config.database.auto_cleanup_days
    return DatabaseService(db_path=db_path, auto_cleanup_days=auto_cleanup_days)


@strawberry.type
class Query:
    """GraphQL queries."""

    @strawberry.field
    def scan_jobs(self, info: Info) -> list[ScanJobType]:
        """Get all scan jobs."""
        jobs = []
        for job_id, job_data in _scan_jobs.items():
            jobs.append(
                ScanJobType(
                    id=job_id,
                    directory=job_data["directory"],
                    scan_mode=job_data["scan_mode"],
                    status=job_data["status"],
                    started_at=job_data["started_at"],
                    completed_at=job_data.get("completed_at"),
                    results_count=len(_scan_results.get(job_id, [])),
                )
            )
        return jobs

    @strawberry.field
    def scan_job(self, info: Info, job_id: str) -> ScanJobType | None:
        """Get a specific scan job by ID."""
        job_data = _scan_jobs.get(job_id)
        if not job_data:
            return None

        return ScanJobType(
            id=job_id,
            directory=job_data["directory"],
            scan_mode=job_data["scan_mode"],
            status=job_data["status"],
            started_at=job_data["started_at"],
            completed_at=job_data.get("completed_at"),
            results_count=len(_scan_results.get(job_id, [])),
        )

    @strawberry.field
    def scan_results(self, info: Info, job_id: str) -> list[ScanResultType]:
        """Get scan results for a specific job."""
        results = _scan_results.get(job_id, [])
        return [convert_scan_result_to_graphql(r) for r in results]

    @strawberry.field
    def scan_summary(self, info: Info, job_id: str) -> ScanSummaryType | None:
        """Get scan summary for a specific job."""
        job_data = _scan_jobs.get(job_id)
        if not job_data or "summary" not in job_data:
            return None

        return convert_scan_summary_to_graphql(job_data["summary"])

    @strawberry.field
    def database_stats(self, info: Info) -> DatabaseStatsType | None:
        """Get database statistics.

        Returns statistics about the database contents including total scans,
        file counts, and date ranges.
        """
        config: AppConfig = info.context["config"]
        db_service = get_database_service(config)

        if not db_service:
            logger.warning("Database not enabled in configuration")
            return None

        try:
            stats = db_service.get_database_stats()
            return DatabaseStatsType(
                total_scans=stats.total_scans,
                total_files=stats.total_files,
                corrupt_files=stats.corrupt_files,
                healthy_files=stats.healthy_files,
                oldest_scan=stats.oldest_scan,
                newest_scan=stats.newest_scan,
                database_size_bytes=stats.database_size_bytes,
            )
        except Exception:
            logger.exception("Failed to get database stats")
            return None

    @strawberry.field
    def database_query(
        self, info: Info, filter: DatabaseQueryFilterInput | None = None
    ) -> list[ScanResultHistoryType]:
        """Query scan results from database with optional filtering.

        Args:
            filter: Optional filter criteria for the query

        Returns:
            List of scan results matching the filter criteria
        """
        config: AppConfig = info.context["config"]
        db_service = get_database_service(config)

        if not db_service:
            logger.warning("Database not enabled in configuration")
            return []

        try:
            # Convert GraphQL input to database filter model
            db_filter = DatabaseQueryFilter()
            if filter:
                db_filter = DatabaseQueryFilter(
                    directory=filter.directory,
                    is_corrupt=filter.is_corrupt,
                    scan_mode=filter.scan_mode,
                    min_confidence=filter.min_confidence,
                    max_confidence=filter.max_confidence,
                    min_file_size=filter.min_file_size,
                    max_file_size=filter.max_file_size,
                    since_date=filter.since_date,
                    until_date=filter.until_date,
                    filename_pattern=filter.filename_pattern,
                    limit=filter.limit,
                    offset=filter.offset,
                )

            results = db_service.query_results(db_filter)

            return [
                ScanResultHistoryType(
                    id=result.id or 0,
                    scan_id=result.scan_id,
                    filename=result.filename,
                    file_size=result.file_size,
                    is_corrupt=result.is_corrupt,
                    confidence=result.confidence,
                    inspection_time=result.inspection_time,
                    scan_mode=result.scan_mode,
                    status=result.status,
                    created_at=result.created_at,
                )
                for result in results
            ]
        except Exception:
            logger.exception("Failed to query database")
            return []

    @strawberry.field
    def corruption_trend(
        self, info: Info, directory: str, days: int = 30
    ) -> list[CorruptionTrendDataType]:
        """Get corruption rate trend over time for a directory.

        Args:
            directory: Directory to analyze
            days: Number of days to look back (default: 30)

        Returns:
            List of corruption rate data points over time
        """
        config: AppConfig = info.context["config"]
        db_service = get_database_service(config)

        if not db_service:
            logger.warning("Database not enabled in configuration")
            return []

        try:
            trend_data = db_service.get_corruption_trend(directory, days)

            return [
                CorruptionTrendDataType(
                    scan_date=data["scan_date"],
                    corrupt_files=data["corrupt_files"],
                    total_files=data["total_files"],
                    corruption_rate=data["corruption_rate"],
                )
                for data in trend_data
            ]
        except Exception:
            logger.exception("Failed to get corruption trend")
            return []

    @strawberry.field
    def scan_history(self, info: Info, limit: int = 10) -> list[ScanHistoryType]:
        """Get recent scan history.

        Args:
            limit: Maximum number of scans to return (default: 10)

        Returns:
            List of recent scan records
        """
        config: AppConfig = info.context["config"]
        db_service = get_database_service(config)

        if not db_service:
            logger.warning("Database not enabled in configuration")
            return []

        try:
            scans = db_service.get_recent_scans(limit)

            return [
                ScanHistoryType(
                    id=scan.id or 0,
                    directory=scan.directory,
                    scan_mode=scan.scan_mode,
                    started_at=scan.started_at,
                    completed_at=scan.completed_at,
                    total_files=scan.total_files,
                    processed_files=scan.processed_files,
                    corrupt_files=scan.corrupt_files,
                    healthy_files=scan.healthy_files,
                    success_rate=scan.success_rate,
                    scan_time=scan.scan_time,
                )
                for scan in scans
            ]
        except Exception:
            logger.exception("Failed to get scan history")
            return []


@strawberry.type
class Mutation:
    """GraphQL mutations."""

    @strawberry.mutation
    def start_scan(self, info: Info, input: ScanInputType) -> ScanJobType:
        """Start a new video scan operation."""
        config: AppConfig = info.context["config"]
        job_id = str(uuid.uuid4())

        # Create scan job record
        _scan_jobs[job_id] = {
            "directory": input.directory,
            "scan_mode": input.scan_mode,
            "status": "running",
            "started_at": datetime.now(),
        }

        try:
            # Initialize scan handler
            scan_handler = ScanHandler(config)

            # Run the scan
            summary = scan_handler.run_scan(
                directory=Path(input.directory),
                scan_mode=convert_scan_mode(input.scan_mode),
                recursive=input.recursive,
                resume=input.resume,
                output_file=None,  # Don't save to file for API
                output_format="json",
                pretty_print=True,
            )

            # Update job with results
            _scan_jobs[job_id]["status"] = "completed"
            _scan_jobs[job_id]["completed_at"] = datetime.now()
            if summary:
                _scan_jobs[job_id]["summary"] = summary
                # Store results (in production, this should be in a database)
                # For now, we'll create empty results list
                _scan_results[job_id] = []

        except Exception as e:
            logger.exception("Scan failed")
            _scan_jobs[job_id]["status"] = "failed"
            _scan_jobs[job_id]["completed_at"] = datetime.now()
            _scan_jobs[job_id]["error"] = str(e)

        job_data = _scan_jobs[job_id]
        return ScanJobType(
            id=job_id,
            directory=job_data["directory"],
            scan_mode=job_data["scan_mode"],
            status=job_data["status"],
            started_at=job_data["started_at"],
            completed_at=job_data.get("completed_at"),
            results_count=len(_scan_results.get(job_id, [])),
        )

    @strawberry.mutation
    def generate_report(self, info: Info, input: ReportInputType) -> ReportType | None:
        """Generate a report for a completed scan."""
        config: AppConfig = info.context["config"]
        job_data = _scan_jobs.get(input.scan_job_id)

        if not job_data or job_data["status"] != "completed":
            return None

        try:
            report_service = ReportService(config)
            summary = job_data.get("summary")
            results = _scan_results.get(input.scan_job_id, [])

            if not summary:
                return None

            # Generate the report
            output_path = report_service.generate_report(
                summary=summary,
                results=results,
                format=input.format,
                include_healthy=input.include_healthy,
            )

            return ReportType(
                id=str(uuid.uuid4()),
                format=input.format,
                file_path=str(output_path),
                created_at=datetime.now(),
                scan_summary=convert_scan_summary_to_graphql(summary),
            )

        except Exception:
            logger.exception("Report generation failed")
            return None
