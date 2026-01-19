"""Database service for scan results persistence."""

import logging
import sqlite3
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .models import (
    DatabaseQueryFilter,
    DatabaseStats,
    ScanDatabaseModel,
    ScanResultDatabaseModel,
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing scan results in SQLite database."""

    def __init__(self, db_path: Path, auto_cleanup_days: int = 0):
        """Initialize database service.

        Args:
            db_path: Path to SQLite database file
            auto_cleanup_days: Auto-delete scans older than this many days (0 = disabled)
        """
        self.db_path = db_path
        self.auto_cleanup_days = auto_cleanup_days
        self._ensure_database_directory()
        self._initialize_database()

    def _ensure_database_directory(self) -> None:
        """Ensure database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _initialize_database(self) -> None:
        """Initialize database schema if it doesn't exist."""
        with self._get_connection() as conn:
            # Create scans table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    directory TEXT NOT NULL,
                    scan_mode TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    completed_at REAL,
                    total_files INTEGER NOT NULL,
                    processed_files INTEGER NOT NULL,
                    corrupt_files INTEGER NOT NULL,
                    healthy_files INTEGER NOT NULL,
                    success_rate REAL NOT NULL,
                    scan_time REAL NOT NULL
                )
            """
            )

            # Create scan_results table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    is_corrupt BOOLEAN NOT NULL,
                    confidence REAL NOT NULL,
                    inspection_time REAL NOT NULL,
                    scan_mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    FOREIGN KEY (scan_id) REFERENCES scans(id),
                    UNIQUE(scan_id, filename)
                )
            """
            )

            # Create indexes for common queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scan_results_filename
                ON scan_results(filename)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scan_results_corrupt
                ON scan_results(is_corrupt, confidence)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scans_directory
                ON scans(directory, started_at)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scan_results_created_at
                ON scan_results(created_at)
            """
            )

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection]:
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()

    def store_scan(self, scan: ScanDatabaseModel) -> int:
        """Store a scan record and return the scan ID.

        Args:
            scan: Scan data to store

        Returns:
            The ID of the stored scan
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO scans (
                    directory, scan_mode, started_at, completed_at,
                    total_files, processed_files, corrupt_files,
                    healthy_files, success_rate, scan_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    scan.directory,
                    scan.scan_mode,
                    scan.started_at,
                    scan.completed_at,
                    scan.total_files,
                    scan.processed_files,
                    scan.corrupt_files,
                    scan.healthy_files,
                    scan.success_rate,
                    scan.scan_time,
                ),
            )

            scan_id = cursor.lastrowid
            if scan_id is None:
                raise RuntimeError("Failed to retrieve scan ID after insertion")
            conn.commit()

            logger.info(f"Stored scan {scan_id} for directory {scan.directory}")
            return scan_id

    def store_scan_results(self, scan_id: int, results: list[ScanResultDatabaseModel]) -> None:
        """Store scan results for a given scan.

        Args:
            scan_id: ID of the scan these results belong to
            results: List of scan results to store
        """
        if not results:
            return

        with self._get_connection() as conn:
            # Prepare data for batch insert
            data = []
            for result in results:
                data.append(
                    (
                        scan_id,
                        result.filename,
                        result.file_size,
                        result.is_corrupt,
                        result.confidence,
                        result.inspection_time,
                        result.scan_mode,
                        result.status,
                        result.created_at,
                    )
                )

            # Batch insert with conflict resolution
            conn.executemany(
                """
                INSERT OR REPLACE INTO scan_results (
                    scan_id, filename, file_size, is_corrupt, confidence,
                    inspection_time, scan_mode, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data,
            )

            conn.commit()
            logger.info(f"Stored {len(results)} scan results for scan {scan_id}")

    def get_scan(self, scan_id: int) -> ScanDatabaseModel | None:
        """Get scan by ID.

        Args:
            scan_id: ID of the scan to retrieve

        Returns:
            ScanDatabaseModel if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM scans WHERE id = ?
            """,
                (scan_id,),
            )

            row = cursor.fetchone()
            if row is None:
                return None

            return ScanDatabaseModel(
                id=row["id"],
                directory=row["directory"],
                scan_mode=row["scan_mode"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                total_files=row["total_files"],
                processed_files=row["processed_files"],
                corrupt_files=row["corrupt_files"],
                healthy_files=row["healthy_files"],
                success_rate=row["success_rate"],
                scan_time=row["scan_time"],
            )

    def get_scan_results(self, scan_id: int) -> list[ScanResultDatabaseModel]:
        """Get all results for a specific scan.

        Args:
            scan_id: ID of the scan to get results for

        Returns:
            List of scan results
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM scan_results WHERE scan_id = ?
                ORDER BY filename
            """,
                (scan_id,),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    ScanResultDatabaseModel(
                        id=row["id"],
                        scan_id=row["scan_id"],
                        filename=row["filename"],
                        file_size=row["file_size"],
                        is_corrupt=bool(row["is_corrupt"]),
                        confidence=row["confidence"],
                        inspection_time=row["inspection_time"],
                        scan_mode=row["scan_mode"],
                        status=row["status"],
                        created_at=row["created_at"],
                    )
                )

            return results

    def query_results(self, filter_opts: DatabaseQueryFilter) -> list[ScanResultDatabaseModel]:
        """Query scan results with filtering.

        Args:
            filter_opts: Filter options for the query

        Returns:
            List of matching scan results
        """
        where_clause, params = filter_opts.to_where_clause()

        query = f"""
            SELECT sr.*
            FROM scan_results sr
            JOIN scans s ON sr.scan_id = s.id
            WHERE {where_clause}
            ORDER BY sr.created_at DESC
        """

        if filter_opts.limit is not None:
            query += f" LIMIT {filter_opts.limit}"

        if filter_opts.offset > 0:
            query += f" OFFSET {filter_opts.offset}"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append(
                    ScanResultDatabaseModel(
                        id=row["id"],
                        scan_id=row["scan_id"],
                        filename=row["filename"],
                        file_size=row["file_size"],
                        is_corrupt=bool(row["is_corrupt"]),
                        confidence=row["confidence"],
                        inspection_time=row["inspection_time"],
                        scan_mode=row["scan_mode"],
                        status=row["status"],
                        created_at=row["created_at"],
                    )
                )

            return results

    def get_recent_scans(self, limit: int = 10) -> list[ScanDatabaseModel]:
        """Get most recent scans.

        Args:
            limit: Maximum number of scans to return

        Returns:
            List of recent scans
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM scans
                ORDER BY started_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            scans = []
            for row in cursor.fetchall():
                scans.append(
                    ScanDatabaseModel(
                        id=row["id"],
                        directory=row["directory"],
                        scan_mode=row["scan_mode"],
                        started_at=row["started_at"],
                        completed_at=row["completed_at"],
                        total_files=row["total_files"],
                        processed_files=row["processed_files"],
                        corrupt_files=row["corrupt_files"],
                        healthy_files=row["healthy_files"],
                        success_rate=row["success_rate"],
                        scan_time=row["scan_time"],
                    )
                )

            return scans

    def get_files_needing_rescan(self, directory: str, _scan_mode: str = "quick") -> list[str]:
        """Get files that need rescanning based on last scan results.

        This is used for incremental scanning to skip files that were
        recently scanned and found to be healthy.

        Args:
            directory: Directory being scanned
            _scan_mode: Scan mode being used (reserved for future use)

        Returns:
            List of filenames that should be rescanned
        """
        # Get the most recent scan for this directory
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id FROM scans
                WHERE directory = ?
                ORDER BY started_at DESC
                LIMIT 1
            """,
                (directory,),
            )

            row = cursor.fetchone()
            if row is None:
                return []  # No previous scans, scan all files

            last_scan_id = row["id"]

            # Get files that were corrupt or suspicious in the last scan
            cursor = conn.execute(
                """
                SELECT filename FROM scan_results
                WHERE scan_id = ? AND (is_corrupt = 1 OR status = 'SUSPICIOUS')
            """,
                (last_scan_id,),
            )

            return [row["filename"] for row in cursor.fetchall()]

    def get_database_stats(self) -> DatabaseStats:
        """Get statistics about the database contents.

        Returns:
            DatabaseStats object with summary information
        """
        with self._get_connection() as conn:
            # Get scan counts
            cursor = conn.execute("SELECT COUNT(*) as count FROM scans")
            total_scans = cursor.fetchone()["count"]

            # Get file counts
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_files,
                    SUM(CASE WHEN is_corrupt = 1 THEN 1 ELSE 0 END) as corrupt_files,
                    SUM(CASE WHEN is_corrupt = 0 THEN 1 ELSE 0 END) as healthy_files
                FROM scan_results
            """
            )
            row = cursor.fetchone()
            total_files = row["total_files"] or 0
            corrupt_files = row["corrupt_files"] or 0
            healthy_files = row["healthy_files"] or 0

            # Get date range
            cursor = conn.execute(
                """
                SELECT MIN(started_at) as oldest, MAX(started_at) as newest
                FROM scans
            """
            )
            row = cursor.fetchone()
            oldest_scan = row["oldest"]
            newest_scan = row["newest"]

            # Get database size
            database_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return DatabaseStats(
                total_scans=total_scans,
                total_files=total_files,
                corrupt_files=corrupt_files,
                healthy_files=healthy_files,
                oldest_scan=oldest_scan,
                newest_scan=newest_scan,
                database_size_bytes=database_size,
            )

    def cleanup_old_scans(self, days: int) -> int:
        """Remove scans older than specified number of days.

        Args:
            days: Number of days - scans older than this will be deleted

        Returns:
            Number of scans that were deleted
        """
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        with self._get_connection() as conn:
            # First get the scan IDs that will be deleted
            cursor = conn.execute(
                """
                SELECT id FROM scans WHERE started_at < ?
            """,
                (cutoff_time,),
            )
            scan_ids = [row["id"] for row in cursor.fetchall()]

            if not scan_ids:
                return 0

            # Delete scan results first (due to foreign key constraint)
            placeholders = ",".join("?" * len(scan_ids))
            conn.execute(
                f"""
                DELETE FROM scan_results WHERE scan_id IN ({placeholders})
            """,
                scan_ids,
            )

            # Delete scans
            conn.execute(
                """
                DELETE FROM scans WHERE started_at < ?
            """,
                (cutoff_time,),
            )

            conn.commit()
            logger.info(f"Cleaned up {len(scan_ids)} old scans")
            return len(scan_ids)

    def vacuum_database(self) -> None:
        """Vacuum the database to reclaim space and optimize performance."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")
            logger.info("Database vacuumed successfully")

    def backup_database(self, backup_path: Path) -> None:
        """Create a backup of the database.

        Args:
            backup_path: Path where the backup should be created
        """
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn, sqlite3.connect(str(backup_path)) as backup_conn:
            conn.backup(backup_conn)

        logger.info(f"Database backed up to {backup_path}")

    def get_corruption_trend(self, directory: str, days: int = 30) -> list[dict[str, Any]]:
        """Get corruption rate trend over time for a directory.

        Args:
            directory: Directory to analyze
            days: Number of days to look back

        Returns:
            List of dictionaries with date and corruption rate data
        """
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    DATE(started_at, 'unixepoch') as scan_date,
                    corrupt_files,
                    total_files,
                    ROUND(100.0 * corrupt_files / total_files, 2) as corruption_rate
                FROM scans
                WHERE directory = ? AND started_at >= ?
                ORDER BY started_at
            """,
                (directory, cutoff_time),
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_recent_scan_for_directory(
        self, directory: str, max_age_seconds: int = 3600
    ) -> ScanDatabaseModel | None:
        """Get most recent scan for a directory within time window.

        Args:
            directory: Directory path to check
            max_age_seconds: Maximum age in seconds (default: 1 hour)

        Returns:
            ScanDatabaseModel if found, None otherwise
        """
        cutoff_time = time.time() - max_age_seconds

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM scans
                WHERE directory = ? AND started_at >= ?
                ORDER BY started_at DESC
                LIMIT 1
            """,
                (directory, cutoff_time),
            )

            row = cursor.fetchone()
            if row is None:
                return None

            return ScanDatabaseModel(
                id=row["id"],
                directory=row["directory"],
                scan_mode=row["scan_mode"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                total_files=row["total_files"],
                processed_files=row["processed_files"],
                corrupt_files=row["corrupt_files"],
                healthy_files=row["healthy_files"],
                success_rate=row["success_rate"],
                scan_time=row["scan_time"],
            )
