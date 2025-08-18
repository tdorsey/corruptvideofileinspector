"""SQLite database operations for storing scan results and summaries."""

import json
import logging
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterator

from src.config.config import DatabaseConfig
from src.core.models.scanning import ScanResult, ScanSummary

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for scan results."""

    def __init__(self, config: DatabaseConfig):
        """Initialize database manager with configuration."""
        self.config = config
        self.db_path = config.path
        self._ensure_database_exists()

    def _ensure_database_exists(self) -> None:
        """Create database and tables if they don't exist."""
        if not self.config.auto_create:
            return

        # Create parent directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            self._create_tables(conn)

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
        """Get database connection with proper error handling and retry logic."""
        conn = None
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            try:
                conn = sqlite3.connect(self.db_path, timeout=5.0)
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                yield conn
                break
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logger.warning(f"Database is locked, retrying ({attempt+1}/{max_attempts})...")
                    attempt += 1
                    time.sleep(1)
                else:
                    if conn:
                        conn.rollback()
                    logger.error(f"Database operation failed: {e}")
                    raise
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"Database operation failed: {e}")
                raise
            finally:
                if conn:
                    conn.close()
        else:
            logger.error("Failed to acquire database connection after multiple attempts due to lock.")
            raise sqlite3.OperationalError("Failed to acquire database connection after multiple attempts due to lock.")
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create database tables for scan results and summaries."""
        # Create scan_summaries table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                directory TEXT NOT NULL,
                scan_mode TEXT NOT NULL,
                total_files INTEGER NOT NULL,
                processed_files INTEGER NOT NULL,
                corrupt_files INTEGER NOT NULL,
                healthy_files INTEGER NOT NULL,
                scan_time REAL NOT NULL,
                deep_scans_needed INTEGER DEFAULT 0,
                deep_scans_completed INTEGER DEFAULT 0,
                started_at REAL NOT NULL,
                completed_at REAL,
                was_resumed BOOLEAN DEFAULT FALSE,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                summary_data TEXT,  -- JSON blob for full summary data
                UNIQUE(directory, started_at)
            )
        """)

        # Create scan_results table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary_id INTEGER,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                is_corrupt BOOLEAN NOT NULL,
                error_message TEXT DEFAULT '',
                ffmpeg_output TEXT DEFAULT '',
                inspection_time REAL NOT NULL,
                scan_mode TEXT NOT NULL,
                needs_deep_scan BOOLEAN DEFAULT FALSE,
                deep_scan_completed BOOLEAN DEFAULT FALSE,
                timestamp REAL NOT NULL,
                confidence REAL DEFAULT 0.0,
                result_data TEXT,  -- JSON blob for full result data
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (summary_id) REFERENCES scan_summaries (id) ON DELETE CASCADE
            )
        """)

        # Create indexes for better query performance
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scan_results_summary_id 
            ON scan_results(summary_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scan_results_file_path 
            ON scan_results(file_path)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scan_results_is_corrupt 
            ON scan_results(is_corrupt)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scan_summaries_directory 
            ON scan_summaries(directory)
        """)

        conn.commit()
        logger.debug("Database tables created/verified")

    def store_scan_summary(self, summary: ScanSummary) -> int:
        """Store scan summary in database and return the summary ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scan_summaries (
                    directory, scan_mode, total_files, processed_files,
                    corrupt_files, healthy_files, scan_time, deep_scans_needed,
                    deep_scans_completed, started_at, completed_at, was_resumed,
                    summary_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(summary.directory),
                summary.scan_mode.value,
                summary.total_files,
                summary.processed_files,
                summary.corrupt_files,
                summary.healthy_files,
                summary.scan_time,
                summary.deep_scans_needed,
                summary.deep_scans_completed,
                summary.started_at,
                summary.completed_at,
                summary.was_resumed,
                json.dumps(summary.model_dump())
            ))
            conn.commit()
            summary_id = cursor.lastrowid
            logger.info(f"Stored scan summary with ID {summary_id} for directory {summary.directory}")
            return summary_id

    def store_scan_results(self, results: list[ScanResult], summary_id: int | None = None) -> None:
        """Store scan results in database."""
        if not results:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Prepare batch insert data
            batch_data = []
            for result in results:
                batch_data.append((
                    summary_id,
                    str(result.video_file.path),
                    result.video_file.size,
                    result.is_corrupt,
                    result.error_message,
                    result.ffmpeg_output,
                    result.inspection_time,
                    result.scan_mode.value,
                    result.needs_deep_scan,
                    result.deep_scan_completed,
                    result.timestamp,
                    result.confidence,
                    json.dumps(result.model_dump())
                ))

            cursor.executemany("""
                INSERT INTO scan_results (
                    summary_id, file_path, file_size, is_corrupt, error_message,
                    ffmpeg_output, inspection_time, scan_mode, needs_deep_scan,
                    deep_scan_completed, timestamp, confidence, result_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch_data)
            
            conn.commit()
            logger.info(f"Stored {len(results)} scan results")

    def get_scan_summaries(
        self, 
        directory: Path | None = None, 
        limit: int | None = None
    ) -> list[ScanSummary]:
        """Retrieve scan summaries from database."""
        with self._get_connection() as conn:
            query = "SELECT summary_data FROM scan_summaries"
            params = []

            if directory:
                query += " WHERE directory = ?"
                params.append(str(directory))

            query += " ORDER BY started_at DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)
            summaries = []

            for row in cursor.fetchall():
                summary_data = json.loads(row[0])
                summary = ScanSummary.model_validate(summary_data)
                summaries.append(summary)

            logger.debug(f"Retrieved {len(summaries)} scan summaries")
            return summaries

    def get_scan_results(
        self, 
        summary_id: int | None = None,
        directory: Path | None = None,
        is_corrupt: bool | None = None
    ) -> list[ScanResult]:
        """Retrieve scan results from database."""
        with self._get_connection() as conn:
            query = "SELECT result_data FROM scan_results"
            params = []
            conditions = []

            if summary_id is not None:
                conditions.append("summary_id = ?")
                params.append(summary_id)

            if directory is not None:
                # Join with scan_summaries to filter by directory
                query = """
                    SELECT sr.result_data 
                    FROM scan_results sr 
                    JOIN scan_summaries ss ON sr.summary_id = ss.id
                    WHERE ss.directory = ?
                """
                params.insert(0, str(directory))

            if is_corrupt is not None:
                conditions.append("is_corrupt = ?")
                params.append(is_corrupt)

            if conditions and "JOIN" not in query:
                query += " WHERE " + " AND ".join(conditions)
            elif conditions and "JOIN" in query:
                query += " AND " + " AND ".join(conditions)

            query += " ORDER BY timestamp DESC"

            cursor = conn.execute(query, params)
            results = []

            for row in cursor.fetchall():
                result_data = json.loads(row[0])
                result = ScanResult.model_validate(result_data)
                results.append(result)

            logger.debug(f"Retrieved {len(results)} scan results")
            return results

    def get_latest_incomplete_scan(self, directory: Path) -> ScanSummary | None:
        """Get the most recent incomplete scan for a directory (for resume functionality)."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT summary_data FROM scan_summaries 
                WHERE directory = ? AND completed_at IS NULL
                ORDER BY started_at DESC LIMIT 1
            """, (str(directory),))

            row = cursor.fetchone()
            if row:
                summary_data = json.loads(row[0])
                summary = ScanSummary.model_validate(summary_data)
                logger.info(f"Found incomplete scan for {directory} started at {summary.started_at}")
                return summary

            return None

    def mark_scan_completed(self, summary_id: int, completed_at: float | None = None) -> None:
        """Mark a scan as completed."""
        if completed_at is None:
            completed_at = time.time()

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE scan_summaries 
                SET completed_at = ? 
                WHERE id = ?
            """, (completed_at, summary_id))
            conn.commit()
            logger.info(f"Marked scan {summary_id} as completed")

    def delete_scan_data(self, summary_id: int) -> None:
        """Delete scan summary and all associated results."""
        with self._get_connection() as conn:
            # Results will be deleted automatically due to CASCADE
            conn.execute("DELETE FROM scan_summaries WHERE id = ?", (summary_id,))
            conn.commit()
            logger.info(f"Deleted scan data for summary ID {summary_id}")

    def get_database_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM scan_summaries) as total_summaries,
                    (SELECT COUNT(*) FROM scan_summaries WHERE completed_at IS NOT NULL) as completed_summaries,
                    (SELECT COUNT(*) FROM scan_results) as total_results,
                    (SELECT COUNT(*) FROM scan_results WHERE is_corrupt = 1) as corrupt_files,
                    (SELECT COUNT(*) FROM scan_results WHERE is_corrupt = 0) as healthy_files
            """)
            
            row = cursor.fetchone()
            return {
                "total_summaries": row[0],
                "completed_summaries": row[1],
                "incomplete_summaries": row[0] - row[1],
                "total_results": row[2],
                "corrupt_files": row[3],
                "healthy_files": row[4],
                "database_path": str(self.db_path),
                "database_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            }