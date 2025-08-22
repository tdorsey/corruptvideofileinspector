"""Unit tests for database models and service."""

import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from src.config.config import DatabaseConfig
from src.database.models import ScanDatabaseModel, ScanResultDatabaseModel
from src.database.service import DatabaseService


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
    def db_service(self, db_config):
        """Create test database service."""
        return DatabaseService(db_config.path, db_config.auto_cleanup_days)

    @pytest.fixture
    def sample_summary(self):
        """Create sample scan summary."""
        return ScanDatabaseModel(
            id=None,
            directory=str(Path("/test/videos")),
            scan_mode="quick",
            total_files=10,
            processed_files=10,
            corrupt_files=2,
            healthy_files=8,
            success_rate=80.0,
            scan_time=120.5,
            deep_scans_needed=1,
            deep_scans_completed=1,
            started_at=time.time() - 200,
            completed_at=time.time() - 80,
            was_resumed=False,
            summary_data={},
        )

    @pytest.fixture
    def sample_results(self):
        """Create sample scan results."""
        return [
            ScanResultDatabaseModel(
                id=None,
                scan_id=1,
                video_file_id=1,
                is_corrupt=False,
                confidence=0.95,
                scan_time_ms=2500,
                created_at=datetime.fromtimestamp(time.time() - 100),
            ),
            ScanResultDatabaseModel(
                id=None,
                scan_id=1,
                video_file_id=2,
                is_corrupt=True,
                confidence=0.80,
                scan_time_ms=3000,
                created_at=datetime.fromtimestamp(time.time() - 95),
            ),
        ]

    def test_store_and_query_scan(self, db_service, sample_summary, sample_results):
        scan_id = db_service.store_scan(sample_summary)
        assert scan_id is not None

        db_service.store_scan_results(scan_id, sample_results)
        results = db_service.query_results(directory=str(Path("/test/videos")), limit=10)
        assert len(results) >= 2
