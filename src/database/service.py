"""Database service for scan results persistence."""

import logging
import sqlite3
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from .models import (
    DatabaseQueryFilter,
    DatabaseStats,
    ProbeModel,
    ProbeResultModel,
    ScanDatabaseModel,
    ScanResultDatabaseModel,
    VideoFileModel,
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
            # Create video_files table - central registry
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS video_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    file_name TEXT NOT NULL,
                    file_size INTEGER,
                    file_hash TEXT,
                    first_seen REAL NOT NULL,
                    last_modified REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )

            # Create scans table (unchanged structure)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    directory TEXT NOT NULL,
                    scan_mode TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    completed_at REAL,
                    total_files INTEGER NOT NULL DEFAULT 0,
                    processed_files INTEGER NOT NULL DEFAULT 0,
                    corrupt_files INTEGER NOT NULL DEFAULT 0,
                    healthy_files INTEGER NOT NULL DEFAULT 0,
                    success_rate REAL NOT NULL DEFAULT 0.0,
                    scan_time REAL NOT NULL DEFAULT 0.0
                )
                """
            )

            # Create scan_results table - links scans to video files
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    video_file_id INTEGER NOT NULL,
                    is_corrupt BOOLEAN NOT NULL DEFAULT false,
                    confidence REAL,
                    scan_time_ms INTEGER,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (scan_id) REFERENCES scans (id),
                    FOREIGN KEY (video_file_id) REFERENCES video_files (id),
                    UNIQUE(scan_id, video_file_id)
                )
                """
            )

            # Create probes table - probes linked to video files
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS probes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_file_id INTEGER NOT NULL,
                    probe_type TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    completed_at REAL,
                    success BOOLEAN NOT NULL DEFAULT false,
                    error_message TEXT,
                    triggered_by_scan_id INTEGER,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (video_file_id) REFERENCES video_files (id),
                    FOREIGN KEY (triggered_by_scan_id) REFERENCES scans (id),
                    UNIQUE(video_file_id, probe_type, started_at)
                )
                """
            )

            # Create probe_results table - detailed probe outcomes
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS probe_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    probe_id INTEGER NOT NULL,
                    result_type TEXT NOT NULL,
                    confidence REAL,
                    data_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (probe_id) REFERENCES probes (id)
                )
                """
            )

            # Create indexes for performance
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_video_files_path 
                ON video_files(file_path)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scan_results_video_file 
                ON scan_results(video_file_id)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_probes_video_file 
                ON probes(video_file_id)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_probes_type 
                ON probes(probe_type)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scan_results_corrupt 
                ON scan_results(is_corrupt)
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

            # Check if we need to migrate old schema
            self._migrate_legacy_schema_if_needed(conn)

    def _migrate_legacy_schema_if_needed(self, conn: sqlite3.Connection) -> None:
        """Migrate legacy schema if old scan_results table exists."""
        try:
            # Check if old scan_results table exists with legacy columns
            cursor = conn.execute("PRAGMA table_info(scan_results)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            # If we have the old 'filename' column, we need to migrate
            if 'filename' in columns and 'video_file_id' not in columns:
                logger.info("Migrating legacy database schema...")
                
                # Rename old table
                conn.execute("ALTER TABLE scan_results RENAME TO scan_results_legacy")
                
                # Create new tables (they might not exist yet)
                self._create_new_schema_tables(conn)
                
                # Migrate data
                self._migrate_legacy_data(conn)
                
                # Drop legacy table
                conn.execute("DROP TABLE scan_results_legacy")
                conn.commit()
                
                logger.info("Legacy schema migration completed")
                
        except Exception as e:
            logger.warning(f"Could not check/migrate legacy schema: {e}")

    def _create_new_schema_tables(self, conn: sqlite3.Connection) -> None:
        """Create the new schema tables if they don't exist."""
        # This ensures the new tables exist even if we're migrating
        conn.execute("""
            CREATE TABLE IF NOT EXISTS video_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                first_seen REAL NOT NULL,
                last_modified REAL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL,
                video_file_id INTEGER NOT NULL,
                is_corrupt BOOLEAN NOT NULL DEFAULT false,
                confidence REAL,
                scan_time_ms INTEGER,
                created_at REAL NOT NULL,
                FOREIGN KEY (scan_id) REFERENCES scans (id),
                FOREIGN KEY (video_file_id) REFERENCES video_files (id),
                UNIQUE(scan_id, video_file_id)
            )
        """)

    def _migrate_legacy_data(self, conn: sqlite3.Connection) -> None:
        """Migrate data from legacy schema to new schema."""
        # First, migrate all unique files to video_files table
        conn.execute("""
            INSERT OR IGNORE INTO video_files (
                file_path, file_name, file_size, first_seen, created_at, updated_at
            )
            SELECT DISTINCT 
                filename as file_path,
                SUBSTR(filename, INSTR(filename, '/') + 1) as file_name,
                file_size,
                created_at as first_seen,
                created_at,
                created_at as updated_at
            FROM scan_results_legacy
        """)
        
        # Then migrate scan results
        conn.execute("""
            INSERT INTO scan_results (
                scan_id, video_file_id, is_corrupt, confidence, scan_time_ms, created_at
            )
            SELECT 
                srl.scan_id,
                vf.id as video_file_id,
                srl.is_corrupt,
                srl.confidence,
                CAST(srl.inspection_time * 1000 AS INTEGER) as scan_time_ms,
                srl.created_at
            FROM scan_results_legacy srl
            JOIN video_files vf ON vf.file_path = srl.filename
        """)

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
                        result.video_file_id,
                        result.is_corrupt,
                        result.confidence,
                        result.scan_time_ms,
                        result.created_at.timestamp(),
                    )
                )

            # Batch insert with conflict resolution
            conn.executemany(
                """
                INSERT OR REPLACE INTO scan_results (
                    scan_id, video_file_id, is_corrupt, confidence, scan_time_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                data,
            )

            conn.commit()
            logger.info(f"Stored {len(results)} scan results for scan {scan_id}")
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

        if filter_opts.include_probe_data:
            query = f"""
                SELECT sr.*, vf.*, s.scan_mode, s.directory
                FROM scan_results sr
                JOIN video_files vf ON sr.video_file_id = vf.id
                JOIN scans s ON sr.scan_id = s.id
                WHERE {where_clause}
                ORDER BY sr.created_at DESC
            """
        else:
            query = f"""
                SELECT sr.*, vf.file_path, vf.file_name, vf.file_size, s.scan_mode, s.directory
                FROM scan_results sr
                JOIN video_files vf ON sr.video_file_id = vf.id
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
                # Create VideoFileModel from the joined data
                video_file = VideoFileModel(
                    id=row["video_file_id"],
                    file_path=row["file_path"],
                    file_name=row["file_name"],
                    file_size=row["file_size"],
                    # Other fields would be included if include_probe_data is True
                    first_seen=datetime.fromtimestamp(row.get("first_seen", 0)) if row.get("first_seen") else datetime.now(),
                    created_at=datetime.fromtimestamp(row.get("created_at", 0)) if row.get("created_at") else datetime.now(),
                    updated_at=datetime.fromtimestamp(row.get("updated_at", 0)) if row.get("updated_at") else datetime.now(),
                )
                
                result = ScanResultDatabaseModel(
                    id=row["id"],
                    scan_id=row["scan_id"],
                    video_file_id=row["video_file_id"],
                    is_corrupt=bool(row["is_corrupt"]),
                    confidence=row["confidence"],
                    scan_time_ms=row["scan_time_ms"],
                    created_at=datetime.fromtimestamp(row["created_at"]),
                    video_file=video_file
                )
                results.append(result)

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

            # Get files that were corrupt in the last scan
            cursor = conn.execute(
                """
                SELECT vf.file_path FROM scan_results sr
                JOIN video_files vf ON sr.video_file_id = vf.id
                WHERE sr.scan_id = ? AND sr.is_corrupt = 1
            """,
                (last_scan_id,),
            )

            return [row["file_path"] for row in cursor.fetchall()]

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

            # Get video file counts (confirmed via successful container probes)
            cursor = conn.execute(
                """
                SELECT COUNT(DISTINCT vf.id) as video_files
                FROM video_files vf
                JOIN probes p ON p.video_file_id = vf.id
                WHERE p.probe_type = 'container' AND p.success = true
            """
            )
            row = cursor.fetchone()
            total_video_files = row["video_files"] or 0

            # Get probe statistics
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_probes,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_probes
                FROM probes
            """
            )
            row = cursor.fetchone()
            total_probes = row["total_probes"] or 0
            successful_probes = row["successful_probes"] or 0

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
                total_video_files=total_video_files,
                corrupt_files=corrupt_files,
                healthy_files=healthy_files,
                total_probes=total_probes,
                successful_probes=successful_probes,
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

    # New methods for video files and probes

    def store_video_file(self, file_path: Path, file_size: Optional[int] = None) -> int:
        """Store or update a video file record.

        Args:
            file_path: Path to the video file
            file_size: Size of the file in bytes (optional)

        Returns:
            ID of the video file record
        """
        with self._get_connection() as conn:
            now = time.time()
            file_name = file_path.name
            
            # Try to insert, or update if exists
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO video_files 
                (file_path, file_name, file_size, first_seen, created_at, updated_at)
                VALUES (
                    ?, ?, ?, 
                    COALESCE((SELECT first_seen FROM video_files WHERE file_path = ?), ?),
                    COALESCE((SELECT created_at FROM video_files WHERE file_path = ?), ?),
                    ?
                )
                """,
                (str(file_path), file_name, file_size, str(file_path), now, str(file_path), now, now)
            )
            
            video_file_id = cursor.lastrowid
            conn.commit()
            
            return video_file_id

    def get_video_file(self, file_path: Path) -> Optional[VideoFileModel]:
        """Get video file record by path.

        Args:
            file_path: Path to the video file

        Returns:
            VideoFileModel if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM video_files WHERE file_path = ?",
                (str(file_path),)
            )
            
            row = cursor.fetchone()
            if row is None:
                return None
                
            return VideoFileModel(
                id=row["id"],
                file_path=row["file_path"],
                file_name=row["file_name"],
                file_size=row["file_size"],
                file_hash=row["file_hash"],
                first_seen=datetime.fromtimestamp(row["first_seen"]),
                last_modified=datetime.fromtimestamp(row["last_modified"]) if row["last_modified"] else None,
                created_at=datetime.fromtimestamp(row["created_at"]),
                updated_at=datetime.fromtimestamp(row["updated_at"])
            )

    def store_probe(self, probe: ProbeModel) -> int:
        """Store a probe record.

        Args:
            probe: ProbeModel to store

        Returns:
            ID of the stored probe
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO probes 
                (video_file_id, probe_type, started_at, completed_at, success, 
                 error_message, triggered_by_scan_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    probe.video_file_id,
                    probe.probe_type.value,
                    probe.started_at.timestamp(),
                    probe.completed_at.timestamp() if probe.completed_at else None,
                    probe.success,
                    probe.error_message,
                    probe.triggered_by_scan_id,
                    probe.created_at.timestamp()
                )
            )
            
            probe_id = cursor.lastrowid
            conn.commit()
            
            # Store probe results if any
            if probe.results:
                for result in probe.results:
                    result.probe_id = probe_id
                    self.store_probe_result(result)
            
            return probe_id

    def store_probe_result(self, result: ProbeResultModel) -> int:
        """Store a probe result record.

        Args:
            result: ProbeResultModel to store

        Returns:
            ID of the stored probe result
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO probe_results 
                (probe_id, result_type, confidence, data_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    result.probe_id,
                    result.result_type,
                    result.confidence,
                    result.data_json,
                    result.created_at.timestamp()
                )
            )
            
            result_id = cursor.lastrowid
            conn.commit()
            
            return result_id

    def get_video_files_list(self, limit: int = 100, confirmed_video_only: bool = False) -> List[VideoFileModel]:
        """Get list of video files.

        Args:
            limit: Maximum number of files to return
            confirmed_video_only: If True, only return files confirmed as video files via successful container probes

        Returns:
            List of VideoFileModel objects
        """
        with self._get_connection() as conn:
            if confirmed_video_only:
                query = """
                    SELECT DISTINCT vf.* FROM video_files vf
                    JOIN probes p ON p.video_file_id = vf.id
                    WHERE p.probe_type = 'container' AND p.success = true
                    ORDER BY vf.file_path
                    LIMIT ?
                """
            else:
                query = """
                    SELECT * FROM video_files 
                    ORDER BY file_path 
                    LIMIT ?
                """
            
            cursor = conn.execute(query, (limit,))
            
            files = []
            for row in cursor.fetchall():
                files.append(VideoFileModel(
                    id=row["id"],
                    file_path=row["file_path"],
                    file_name=row["file_name"],
                    file_size=row["file_size"],
                    file_hash=row["file_hash"],
                    first_seen=datetime.fromtimestamp(row["first_seen"]),
                    last_modified=datetime.fromtimestamp(row["last_modified"]) if row["last_modified"] else None,
                    created_at=datetime.fromtimestamp(row["created_at"]),
                    updated_at=datetime.fromtimestamp(row["updated_at"])
                ))
            
            return files
