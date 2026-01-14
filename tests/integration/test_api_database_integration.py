"""Integration tests for database GraphQL API endpoints."""

import tempfile
import time
from pathlib import Path

import pytest

from src.api.graphql.resolvers import Query
from src.config.config import AppConfig, DatabaseConfig
from src.core.models.scanning import ScanMode, ScanSummary
from src.database.models import ScanDatabaseModel
from src.database.service import DatabaseService


@pytest.mark.integration
def test_database_stats_integration():
    """Integration test for database_stats with actual data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_service = DatabaseService(db_path=db_path, auto_cleanup_days=0)

        # Add a test scan to the database
        scan_summary = ScanSummary(
            directory=Path("/test/videos"),
            total_files=100,
            processed_files=95,
            corrupt_files=5,
            healthy_files=90,
            scan_mode=ScanMode.HYBRID,
            scan_time=120.5,
            started_at=time.time() - 3600,
            completed_at=time.time() - 3500,
        )
        scan_model = ScanDatabaseModel.from_scan_summary(scan_summary)
        db_service.store_scan(scan_model)

        # Create mock info context
        class MockInfo:
            def __init__(self, config):
                self.context = {"config": config}

        config = AppConfig(
            logging={"level": "INFO", "file": Path("/tmp/test.log")},
            ffmpeg={"command": Path("/usr/bin/ffmpeg")},
            processing={"max_workers": 4, "default_mode": "quick"},
            output={
                "default_json": True,
                "default_output_dir": Path("/tmp"),
                "default_filename": "test.json",
            },
            scan={
                "recursive": True,
                "max_workers": 4,
                "mode": ScanMode.QUICK,
                "default_input_dir": Path("/tmp"),
                "extensions": [".mp4"],
            },
            trakt={"client_id": "", "client_secret": ""},
            database=DatabaseConfig(
                path=db_path, auto_cleanup_days=0, create_backup=True
            ),
        )
        mock_info = MockInfo(config)

        # Test database_stats query
        query = Query()
        result = query.database_stats(mock_info)

        assert result is not None
        assert result.total_scans == 1
        assert result.total_files == 0  # No individual results stored
        assert result.corrupt_files == 0
        assert result.healthy_files == 0


@pytest.mark.integration
def test_scan_history_integration():
    """Integration test for scan_history with actual data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_service = DatabaseService(db_path=db_path, auto_cleanup_days=0)

        # Add multiple test scans to the database
        for i in range(5):
            scan_summary = ScanSummary(
                directory=Path(f"/test/videos{i}"),
                total_files=100 + i * 10,
                processed_files=95 + i * 10,
                corrupt_files=5 + i,
                healthy_files=90 + i * 10,
                scan_mode=ScanMode.HYBRID,
                scan_time=120.5 + i * 10,
                started_at=time.time() - 3600 - i * 100,
                completed_at=time.time() - 3500 - i * 100,
            )
            scan_model = ScanDatabaseModel.from_scan_summary(scan_summary)
            db_service.store_scan(scan_model)

        # Create mock info context
        class MockInfo:
            def __init__(self, config):
                self.context = {"config": config}

        config = AppConfig(
            logging={"level": "INFO", "file": Path("/tmp/test.log")},
            ffmpeg={"command": Path("/usr/bin/ffmpeg")},
            processing={"max_workers": 4, "default_mode": "quick"},
            output={
                "default_json": True,
                "default_output_dir": Path("/tmp"),
                "default_filename": "test.json",
            },
            scan={
                "recursive": True,
                "max_workers": 4,
                "mode": ScanMode.QUICK,
                "default_input_dir": Path("/tmp"),
                "extensions": [".mp4"],
            },
            trakt={"client_id": "", "client_secret": ""},
            database=DatabaseConfig(
                path=db_path, auto_cleanup_days=0, create_backup=True
            ),
        )
        mock_info = MockInfo(config)

        # Test scan_history query
        query = Query()
        result = query.scan_history(mock_info, limit=3)

        assert result is not None
        assert len(result) == 3
        # Most recent scan should be first
        assert result[0].directory == "/test/videos0"


@pytest.mark.integration
def test_corruption_trend_integration():
    """Integration test for corruption_trend with actual data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_service = DatabaseService(db_path=db_path, auto_cleanup_days=0)

        # Add test scans to the database
        for i in range(3):
            scan_summary = ScanSummary(
                directory=Path("/test/videos"),
                total_files=100,
                processed_files=95,
                corrupt_files=5 + i,
                healthy_files=90 - i,
                scan_mode=ScanMode.HYBRID,
                scan_time=120.5,
                started_at=time.time() - 86400 * (3 - i),  # 1-3 days ago
                completed_at=time.time() - 86400 * (3 - i) + 100,
            )
            scan_model = ScanDatabaseModel.from_scan_summary(scan_summary)
            db_service.store_scan(scan_model)

        # Create mock info context
        class MockInfo:
            def __init__(self, config):
                self.context = {"config": config}

        config = AppConfig(
            logging={"level": "INFO", "file": Path("/tmp/test.log")},
            ffmpeg={"command": Path("/usr/bin/ffmpeg")},
            processing={"max_workers": 4, "default_mode": "quick"},
            output={
                "default_json": True,
                "default_output_dir": Path("/tmp"),
                "default_filename": "test.json",
            },
            scan={
                "recursive": True,
                "max_workers": 4,
                "mode": ScanMode.QUICK,
                "default_input_dir": Path("/tmp"),
                "extensions": [".mp4"],
            },
            trakt={"client_id": "", "client_secret": ""},
            database=DatabaseConfig(
                path=db_path, auto_cleanup_days=0, create_backup=True
            ),
        )
        mock_info = MockInfo(config)

        # Test corruption_trend query
        query = Query()
        result = query.corruption_trend(mock_info, directory="/test/videos", days=30)

        assert result is not None
        assert len(result) == 3
        # Verify corruption rate is calculated correctly
        for item in result:
            assert item.total_files == 100
            assert item.corrupt_files >= 5
            assert item.corruption_rate > 0
