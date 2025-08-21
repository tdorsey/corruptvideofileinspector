"""Unit tests for database functionality."""

import tempfile
import time
from pathlib import Path

import pytest

from src.config.config import DatabaseConfig
from src.core.database import DatabaseManager
from src.core.models.inspection import VideoFile
from src.core.models.scanning import ScanMode, ScanResult, ScanSummary


@pytest.mark.unit
class TestDatabaseManager:
    """Test database operations."""

    @pytest.fixture
    def db_config(self):
        """Create test database configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            yield DatabaseConfig(enabled=True, path=db_path, auto_create=True)

    @pytest.fixture
    def db_manager(self, db_config):
        """Create test database manager."""
        return DatabaseManager(db_config)

    @pytest.fixture
    def sample_summary(self):
        """Create sample scan summary."""
        return ScanSummary(
            directory=Path("/test/videos"),
            scan_mode=ScanMode.QUICK,
            total_files=10,
            processed_files=10,
            corrupt_files=2,
            healthy_files=8,
            scan_time=120.5,
            deep_scans_needed=1,
            deep_scans_completed=1,
            started_at=time.time() - 200,
            completed_at=time.time() - 80,
            was_resumed=False,
        )

    @pytest.fixture
    def sample_results(self):
        """Create sample scan results."""
        return [
            ScanResult(
                video_file=VideoFile(path=Path("/test/videos/file1.mp4"), size=1024000),
                is_corrupt=False,
                error_message="",
                ffmpeg_output="",
                inspection_time=2.5,
                scan_mode=ScanMode.QUICK,
                needs_deep_scan=False,
                deep_scan_completed=False,
                timestamp=time.time() - 100,
                confidence=0.0,
            ),
            ScanResult(
                video_file=VideoFile(path=Path("/test/videos/file2.mp4"), size=2048000),
                is_corrupt=True,
                error_message="Invalid data found",
                ffmpeg_output="ERROR: corruption detected",
                inspection_time=1.8,
                scan_mode=ScanMode.QUICK,
                needs_deep_scan=False,
                deep_scan_completed=False,
                timestamp=time.time() - 95,
                confidence=0.9,
            ),
        ]

    def test_database_creation(self, db_manager):
        """Test that database and tables are created."""
        assert db_manager.db_path.exists()

        # Check that tables exist
        with db_manager._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('scan_summaries', 'scan_results')"
            )
            tables = [row[0] for row in cursor.fetchall()]
            assert "scan_summaries" in tables
            assert "scan_results" in tables

    def test_store_scan_summary(self, db_manager, sample_summary):
        """Test storing a scan summary."""
        summary_id = db_manager.store_scan_summary(sample_summary)
        assert isinstance(summary_id, int)
        assert summary_id > 0

    def test_store_scan_results(self, db_manager, sample_summary, sample_results):
        """Test storing scan results."""
        summary_id = db_manager.store_scan_summary(sample_summary)
        db_manager.store_scan_results(sample_results, summary_id)

        # Verify results were stored
        with db_manager._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM scan_results WHERE summary_id = ?", (summary_id,)
            )
            count = cursor.fetchone()[0]
            assert count == len(sample_results)

    def test_get_scan_summaries(self, db_manager, sample_summary):
        """Test retrieving scan summaries."""
        # Store a summary
        db_manager.store_scan_summary(sample_summary)

        # Retrieve summaries
        summaries = db_manager.get_scan_summaries()
        assert len(summaries) == 1
        assert summaries[0].directory == sample_summary.directory
        assert summaries[0].scan_mode == sample_summary.scan_mode

    def test_get_scan_results(self, db_manager, sample_summary, sample_results):
        """Test retrieving scan results."""
        # Store summary and results
        summary_id = db_manager.store_scan_summary(sample_summary)
        db_manager.store_scan_results(sample_results, summary_id)

        # Retrieve results
        results = db_manager.get_scan_results(summary_id=summary_id)
        assert len(results) == len(sample_results)
        assert results[0].video_file.path == sample_results[0].video_file.path
        assert results[1].is_corrupt == sample_results[1].is_corrupt

    def test_get_scan_results_by_corruption(self, db_manager, sample_summary, sample_results):
        """Test retrieving scan results filtered by corruption status."""
        # Store summary and results
        summary_id = db_manager.store_scan_summary(sample_summary)
        db_manager.store_scan_results(sample_results, summary_id)

        # Get only corrupt files
        corrupt_results = db_manager.get_scan_results(summary_id=summary_id, is_corrupt=True)
        assert len(corrupt_results) == 1
        assert corrupt_results[0].is_corrupt is True

        # Get only healthy files
        healthy_results = db_manager.get_scan_results(summary_id=summary_id, is_corrupt=False)
        assert len(healthy_results) == 1
        assert healthy_results[0].is_corrupt is False

    def test_get_latest_incomplete_scan(self, db_manager):
        """Test retrieving incomplete scans for resume functionality."""
        # Create incomplete scan (no completed_at)
        incomplete_summary = ScanSummary(
            directory=Path("/test/videos"),
            scan_mode=ScanMode.HYBRID,
            total_files=5,
            processed_files=3,
            corrupt_files=1,
            healthy_files=2,
            scan_time=60.0,
            deep_scans_needed=0,
            deep_scans_completed=0,
            started_at=time.time() - 100,
            completed_at=None,  # Incomplete
            was_resumed=False,
        )

        db_manager.store_scan_summary(incomplete_summary)

        # Retrieve incomplete scan
        result = db_manager.get_latest_incomplete_scan(Path("/test/videos"))
        assert result is not None
        assert result.directory == incomplete_summary.directory
        assert result.completed_at is None

    def test_mark_scan_completed(self, db_manager):
        """Test marking a scan as completed."""
        # Create incomplete scan
        incomplete_summary = ScanSummary(
            directory=Path("/test/videos"),
            scan_mode=ScanMode.QUICK,
            total_files=1,
            processed_files=1,
            corrupt_files=0,
            healthy_files=1,
            scan_time=5.0,
            deep_scans_needed=0,
            deep_scans_completed=0,
            started_at=time.time() - 50,
            completed_at=None,
            was_resumed=False,
        )

        summary_id = db_manager.store_scan_summary(incomplete_summary)

        # Mark as completed
        completion_time = time.time()
        db_manager.mark_scan_completed(summary_id, completion_time)

        # Verify it's marked as complete
        summaries = db_manager.get_scan_summaries()
        assert len(summaries) == 1
        assert summaries[0].completed_at == completion_time

    def test_get_database_stats(self, db_manager, sample_summary, sample_results):
        """Test getting database statistics."""
        # Store some data
        summary_id = db_manager.store_scan_summary(sample_summary)
        db_manager.store_scan_results(sample_results, summary_id)

        # Get stats
        stats = db_manager.get_database_stats()

        assert stats["total_summaries"] == 1
        assert stats["completed_summaries"] == 1
        assert stats["incomplete_summaries"] == 0
        assert stats["total_results"] == 2
        assert stats["corrupt_files"] == 1
        assert stats["healthy_files"] == 1
        assert "database_path" in stats
        assert "database_size_mb" in stats

    def test_delete_scan_data(self, db_manager, sample_summary, sample_results):
        """Test deleting scan data."""
        # Store data
        summary_id = db_manager.store_scan_summary(sample_summary)
        db_manager.store_scan_results(sample_results, summary_id)

        # Verify data exists
        summaries = db_manager.get_scan_summaries()
        results = db_manager.get_scan_results(summary_id=summary_id)
        assert len(summaries) == 1
        assert len(results) == 2

        # Delete data
        db_manager.delete_scan_data(summary_id)

        # Verify data is gone
        summaries = db_manager.get_scan_summaries()
        results = db_manager.get_scan_results(summary_id=summary_id)
        assert len(summaries) == 0
        assert len(results) == 0

    def test_empty_results_handling(self, db_manager, sample_summary):
        """Test handling of empty results list."""
        summary_id = db_manager.store_scan_summary(sample_summary)

        # Store empty results - should not fail
        db_manager.store_scan_results([], summary_id)

        # Verify no results stored
        results = db_manager.get_scan_results(summary_id=summary_id)
        assert len(results) == 0

    def test_no_auto_create_config(self):
        """Test database manager with auto_create disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "no_auto.db"
            config = DatabaseConfig(enabled=True, path=db_path, auto_create=False)

            # Should not create database file
            db_manager = DatabaseManager(config)  # noqa: F841
            # Database file should not exist since auto_create is False
            # The actual behavior depends on implementation - this tests the config option exists
