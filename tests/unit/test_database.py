"""Unit tests for database models and service."""

import tempfile
import time
from pathlib import Path

import pytest

from src.core.models.inspection import VideoFile
from src.core.models.scanning import ScanMode, ScanResult, ScanSummary
from src.database.models import (
    DatabaseQueryFilter,
    ScanDatabaseModel,
    ScanResultDatabaseModel,
)
from src.database.service import DatabaseService


@pytest.mark.unit
class TestScanDatabaseModel:
    """Test database model for scans."""

    def test_from_scan_summary(self):
        """Test conversion from ScanSummary to database model."""
        summary = ScanSummary(
            directory=Path("/test/videos"),
            total_files=100,
            processed_files=95,
            corrupt_files=5,
            healthy_files=90,
            scan_mode=ScanMode.HYBRID,
            scan_time=120.5,
            started_at=1234567890.0,
            completed_at=1234567950.0,
        )

        db_model = ScanDatabaseModel.from_scan_summary(summary)

        assert db_model.directory == "/test/videos"
        assert db_model.scan_mode == "hybrid"
        assert db_model.total_files == 100
        assert db_model.corrupt_files == 5
        assert db_model.scan_time == 120.5
        assert db_model.started_at == 1234567890.0
        assert db_model.completed_at == 1234567950.0

    def test_to_scan_summary(self):
        """Test conversion from database model to ScanSummary."""
        db_model = ScanDatabaseModel(
            id=1,
            directory="/test/videos",
            scan_mode="quick",
            started_at=1234567890.0,
            completed_at=1234567950.0,
            total_files=50,
            processed_files=48,
            corrupt_files=2,
            healthy_files=46,
            success_rate=95.8,
            scan_time=60.0,
        )

        summary = db_model.to_scan_summary()

        assert summary.directory == Path("/test/videos")
        assert summary.scan_mode == ScanMode.QUICK
        assert summary.total_files == 50
        assert summary.corrupt_files == 2
        assert summary.scan_time == 60.0


@pytest.mark.unit
class TestScanResultDatabaseModel:
    """Test database model for scan results."""

    def test_from_scan_result(self):
        """Test conversion from ScanResult to database model."""
        video_file = VideoFile(path=Path("/test/video.mp4"))
        scan_result = ScanResult(
            video_file=video_file,
            is_corrupt=True,
            confidence=0.85,
            inspection_time=2.5,
            scan_mode=ScanMode.DEEP,
            timestamp=1234567890.0,
        )

        db_model = ScanResultDatabaseModel.from_scan_result(scan_result, scan_id=123)

        assert db_model.scan_id == 123
        assert db_model.filename == "/test/video.mp4"
        assert db_model.is_corrupt is True
        assert db_model.confidence == 0.85
        assert db_model.inspection_time == 2.5
        assert db_model.scan_mode == "deep"
        assert db_model.status == "CORRUPT"
        assert db_model.created_at == 1234567890.0

    def test_to_scan_result(self):
        """Test conversion from database model to ScanResult."""
        db_model = ScanResultDatabaseModel(
            id=1,
            scan_id=123,
            filename="/test/video.mp4",
            file_size=1000000,
            is_corrupt=False,
            confidence=0.95,
            inspection_time=1.5,
            scan_mode="quick",
            status="HEALTHY",
            created_at=1234567890.0,
        )

        scan_result = db_model.to_scan_result()

        assert scan_result.video_file.path == Path("/test/video.mp4")
        assert scan_result.is_corrupt is False
        assert scan_result.confidence == 0.95
        assert scan_result.inspection_time == 1.5
        assert scan_result.scan_mode == ScanMode.QUICK
        assert scan_result.timestamp == 1234567890.0


@pytest.mark.unit
class TestDatabaseQueryFilter:
    """Test database query filter functionality."""

    def test_empty_filter(self):
        """Test filter with no conditions."""
        filter_opts = DatabaseQueryFilter()
        where_clause, params = filter_opts.to_where_clause()

        assert where_clause == "1=1"
        assert params == {}

    def test_single_condition(self):
        """Test filter with single condition."""
        filter_opts = DatabaseQueryFilter(is_corrupt=True)
        where_clause, params = filter_opts.to_where_clause()

        assert where_clause == "sr.is_corrupt = :is_corrupt"
        assert params == {"is_corrupt": True}

    def test_multiple_conditions(self):
        """Test filter with multiple conditions."""
        filter_opts = DatabaseQueryFilter(directory="/test", is_corrupt=True, min_confidence=0.8)
        where_clause, params = filter_opts.to_where_clause()

        expected_conditions = [
            "s.directory = :directory",
            "sr.is_corrupt = :is_corrupt",
            "sr.confidence >= :min_confidence",
        ]

        assert where_clause == " AND ".join(expected_conditions)
        assert params == {"directory": "/test", "is_corrupt": True, "min_confidence": 0.8}


@pytest.mark.unit
class TestDatabaseService:
    """Test database service functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        # Clean up the file so DatabaseService can create it
        db_path.unlink()

        service = DatabaseService(db_path)
        yield service

        # Clean up
        if db_path.exists():
            db_path.unlink()

    def test_database_initialization(self, temp_db):
        """Test that database is properly initialized."""
        assert temp_db.db_path.exists()

        # Check that tables exist
        with temp_db._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('scans', 'scan_results')
            """
            )
            tables = [row[0] for row in cursor.fetchall()]

        assert "scans" in tables
        assert "scan_results" in tables

    def test_store_and_retrieve_scan(self, temp_db):
        """Test storing and retrieving scan data."""
        scan_data = ScanDatabaseModel(
            directory="/test/videos",
            scan_mode="quick",
            started_at=time.time(),
            completed_at=time.time() + 60,
            total_files=10,
            processed_files=10,
            corrupt_files=1,
            healthy_files=9,
            success_rate=90.0,
            scan_time=60.0,
        )

        # Store scan
        scan_id = temp_db.store_scan(scan_data)
        assert scan_id > 0

        # Retrieve scan
        retrieved = temp_db.get_scan(scan_id)
        assert retrieved is not None
        assert retrieved.directory == "/test/videos"
        assert retrieved.scan_mode == "quick"
        assert retrieved.total_files == 10
        assert retrieved.corrupt_files == 1

    def test_store_and_retrieve_scan_results(self, temp_db):
        """Test storing and retrieving scan results."""
        # First create a scan
        scan_data = ScanDatabaseModel(
            directory="/test",
            scan_mode="quick",
            started_at=time.time(),
            total_files=2,
            processed_files=2,
            corrupt_files=1,
            healthy_files=1,
            success_rate=50.0,
            scan_time=30.0,
        )
        scan_id = temp_db.store_scan(scan_data)

        # Create scan results
        results = [
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename="/test/video1.mp4",
                file_size=1000000,
                is_corrupt=True,
                confidence=0.9,
                inspection_time=1.5,
                scan_mode="quick",
                status="CORRUPT",
                created_at=time.time(),
            ),
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename="/test/video2.mp4",
                file_size=2000000,
                is_corrupt=False,
                confidence=0.95,
                inspection_time=1.0,
                scan_mode="quick",
                status="HEALTHY",
                created_at=time.time(),
            ),
        ]

        # Store results
        temp_db.store_scan_results(scan_id, results)

        # Retrieve results
        retrieved_results = temp_db.get_scan_results(scan_id)
        assert len(retrieved_results) == 2

        # Check first result
        result1 = next(r for r in retrieved_results if "video1" in r.filename)
        assert result1.is_corrupt is True
        assert result1.confidence == 0.9
        assert result1.status == "CORRUPT"

        # Check second result
        result2 = next(r for r in retrieved_results if "video2" in r.filename)
        assert result2.is_corrupt is False
        assert result2.confidence == 0.95
        assert result2.status == "HEALTHY"

    def test_query_results_with_filter(self, temp_db):
        """Test querying results with filters."""
        # Setup test data
        scan_data = ScanDatabaseModel(
            directory="/test",
            scan_mode="quick",
            started_at=time.time(),
            total_files=3,
            processed_files=3,
            corrupt_files=2,
            healthy_files=1,
            success_rate=33.3,
            scan_time=30.0,
        )
        scan_id = temp_db.store_scan(scan_data)

        results = [
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename="/test/corrupt1.mp4",
                file_size=1000000,
                is_corrupt=True,
                confidence=0.9,
                inspection_time=1.5,
                scan_mode="quick",
                status="CORRUPT",
                created_at=time.time(),
            ),
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename="/test/corrupt2.mp4",
                file_size=1500000,
                is_corrupt=True,
                confidence=0.7,
                inspection_time=2.0,
                scan_mode="quick",
                status="CORRUPT",
                created_at=time.time(),
            ),
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename="/test/healthy.mp4",
                file_size=2000000,
                is_corrupt=False,
                confidence=0.95,
                inspection_time=1.0,
                scan_mode="quick",
                status="HEALTHY",
                created_at=time.time(),
            ),
        ]
        temp_db.store_scan_results(scan_id, results)

        # Test filter for corrupt files only
        filter_opts = DatabaseQueryFilter(is_corrupt=True)
        corrupt_results = temp_db.query_results(filter_opts)
        assert len(corrupt_results) == 2
        assert all(r.is_corrupt for r in corrupt_results)

        # Test filter with confidence threshold
        filter_opts = DatabaseQueryFilter(min_confidence=0.8)
        high_conf_results = temp_db.query_results(filter_opts)
        assert len(high_conf_results) == 2  # 0.9 and 0.95 confidence
        assert all(r.confidence >= 0.8 for r in high_conf_results)

    def test_get_database_stats(self, temp_db):
        """Test getting database statistics."""
        # Initially empty database
        stats = temp_db.get_database_stats()
        assert stats.total_scans == 0
        assert stats.total_files == 0
        assert stats.corrupt_files == 0
        assert stats.healthy_files == 0

        # Add some test data
        scan_data = ScanDatabaseModel(
            directory="/test",
            scan_mode="quick",
            started_at=time.time(),
            total_files=5,
            processed_files=5,
            corrupt_files=2,
            healthy_files=3,
            success_rate=60.0,
            scan_time=30.0,
        )
        scan_id = temp_db.store_scan(scan_data)

        results = [
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename=f"/test/file{i}.mp4",
                file_size=1000000,
                is_corrupt=i < 2,  # First 2 are corrupt
                confidence=0.9,
                inspection_time=1.0,
                scan_mode="quick",
                status="CORRUPT" if i < 2 else "HEALTHY",
                created_at=time.time(),
            )
            for i in range(5)
        ]
        temp_db.store_scan_results(scan_id, results)

        # Check updated stats
        stats = temp_db.get_database_stats()
        assert stats.total_scans == 1
        assert stats.total_files == 5
        assert stats.corrupt_files == 2
        assert stats.healthy_files == 3
        assert stats.corruption_rate == 40.0  # 2/5 * 100

    def test_cleanup_old_scans(self, temp_db):
        """Test cleaning up old scans."""
        # Create old scan (1 week ago)
        old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
        old_scan = ScanDatabaseModel(
            directory="/old",
            scan_mode="quick",
            started_at=old_time,
            total_files=1,
            processed_files=1,
            corrupt_files=0,
            healthy_files=1,
            success_rate=100.0,
            scan_time=10.0,
        )
        old_scan_id = temp_db.store_scan(old_scan)

        # Create recent scan
        recent_scan = ScanDatabaseModel(
            directory="/recent",
            scan_mode="quick",
            started_at=time.time(),
            total_files=1,
            processed_files=1,
            corrupt_files=0,
            healthy_files=1,
            success_rate=100.0,
            scan_time=10.0,
        )
        recent_scan_id = temp_db.store_scan(recent_scan)

        # Cleanup scans older than 7 days
        deleted_count = temp_db.cleanup_old_scans(7)
        assert deleted_count == 1

        # Verify old scan is gone, recent scan remains
        assert temp_db.get_scan(old_scan_id) is None
        assert temp_db.get_scan(recent_scan_id) is not None
