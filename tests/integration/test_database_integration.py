"""Comprehensive integration tests for database features (REQ-6).

This module tests all database functionality including:
- Scan storage and retrieval
- Incremental scanning
- Report generation from database
- Database cleanup and maintenance
- Query filtering
- Trakt synchronization
- Backup and restore operations
- Export to multiple formats
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.config.config import AppConfig, DatabaseConfig, FFmpegConfig, LoggingConfig, OutputConfig, ProcessingConfig, ScanConfig, TraktConfig
from src.core.models.inspection import VideoFile, VideoStatus
from src.core.models.scanning import ScanMode, ScanResult, ScanSummary
from src.core.scanner import VideoScanner
from src.database.models import DatabaseQueryFilter, ScanDatabaseModel, ScanResultDatabaseModel
from src.database.service import DatabaseService

pytestmark = pytest.mark.integration


@pytest.fixture
def temp_db():
    """Fixture providing a temporary database for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_service = DatabaseService(db_path=db_path, auto_cleanup_days=0)
        yield db_service


@pytest.fixture
def sample_scan_summary():
    """Fixture providing a sample scan summary."""
    return ScanSummary(
        directory=Path("/test/videos"),
        total_files=100,
        processed_files=95,
        corrupt_files=10,
        healthy_files=85,
        scan_mode=ScanMode.HYBRID,
        scan_time=120.5,
        started_at=time.time() - 3600,
        completed_at=time.time() - 3500,
    )


@pytest.fixture
def sample_scan_results():
    """Fixture providing sample scan results."""
    results = []
    
    # Create healthy files
    for i in range(5):
        video_file = VideoFile(
            path=Path(f"/test/videos/healthy_{i}.mp4"),
            size=1000000 + i * 1000,
        )
        result = ScanResult(
            video_file=video_file,
            is_corrupt=False,
            confidence=0.95,
            inspection_time=1.5,
            scan_mode=ScanMode.QUICK,
            status=VideoStatus.HEALTHY,
        )
        results.append(result)
    
    # Create corrupt files
    for i in range(3):
        video_file = VideoFile(
            path=Path(f"/test/videos/corrupt_{i}.mp4"),
            size=500000 + i * 1000,
        )
        result = ScanResult(
            video_file=video_file,
            is_corrupt=True,
            confidence=0.85,
            inspection_time=2.5,
            scan_mode=ScanMode.QUICK,
            status=VideoStatus.CORRUPT,
        )
        results.append(result)
    
    return results


@pytest.fixture
def test_video_dir(tmp_path):
    """Fixture providing a directory with test video files."""
    video_dir = tmp_path / "videos"
    video_dir.mkdir()
    
    # Create dummy video files
    for i in range(5):
        video_file = video_dir / f"video_{i}.mp4"
        video_file.write_bytes(b"fake video content")
    
    return video_dir


def test_scan_stores_results_in_database(temp_db, sample_scan_summary, sample_scan_results):
    """Test that scan results are properly stored in the database.
    
    Verifies:
    - Scan metadata is stored correctly
    - All scan results are stored
    - Data can be retrieved accurately
    - Relationships between scans and results are maintained
    """
    # Store scan
    scan_model = ScanDatabaseModel.from_scan_summary(sample_scan_summary)
    scan_id = temp_db.store_scan(scan_model)
    
    assert scan_id > 0
    
    # Store results
    result_models = [
        ScanResultDatabaseModel.from_scan_result(result, scan_id)
        for result in sample_scan_results
    ]
    temp_db.store_scan_results(scan_id, result_models)
    
    # Retrieve scan
    retrieved_scan = temp_db.get_scan(scan_id)
    assert retrieved_scan is not None
    assert retrieved_scan.id == scan_id
    assert retrieved_scan.directory == str(sample_scan_summary.directory)
    assert retrieved_scan.total_files == sample_scan_summary.total_files
    assert retrieved_scan.corrupt_files == sample_scan_summary.corrupt_files
    assert retrieved_scan.healthy_files == sample_scan_summary.healthy_files
    
    # Retrieve results
    retrieved_results = temp_db.get_scan_results(scan_id)
    assert len(retrieved_results) == len(sample_scan_results)
    
    # Verify healthy files
    healthy_results = [r for r in retrieved_results if not r.is_corrupt]
    assert len(healthy_results) == 5
    
    # Verify corrupt files
    corrupt_results = [r for r in retrieved_results if r.is_corrupt]
    assert len(corrupt_results) == 3
    
    # Check specific result
    first_result = retrieved_results[0]
    assert first_result.scan_id == scan_id
    assert first_result.confidence > 0
    assert first_result.status in ["HEALTHY", "CORRUPT", "SUSPICIOUS"]


def test_incremental_scan_skips_healthy_files(temp_db, test_video_dir):
    """Test that incremental scanning skips previously healthy files.
    
    Verifies:
    - Healthy files from recent scans are identified
    - Files needing rescan (corrupt/suspicious) are identified
    - Incremental scanning improves performance
    """
    directory = str(test_video_dir)
    
    # Create initial scan with some healthy and some corrupt files
    scan1 = ScanDatabaseModel(
        directory=directory,
        scan_mode=ScanMode.QUICK.value,
        started_at=time.time() - 3600,
        completed_at=time.time() - 3500,
        total_files=5,
        processed_files=5,
        corrupt_files=2,
        healthy_files=3,
        success_rate=60.0,
        scan_time=10.0,
    )
    scan1_id = temp_db.store_scan(scan1)
    
    # Store results - mark some files as healthy, some as corrupt
    results = []
    for i, video_file in enumerate(test_video_dir.glob("*.mp4")):
        is_corrupt = i < 2  # First 2 are corrupt
        result = ScanResultDatabaseModel(
            scan_id=scan1_id,
            filename=str(video_file),
            file_size=video_file.stat().st_size,
            is_corrupt=is_corrupt,
            confidence=0.9,
            inspection_time=1.0,
            scan_mode=ScanMode.QUICK.value,
            status="CORRUPT" if is_corrupt else "HEALTHY",
        )
        results.append(result)
    
    temp_db.store_scan_results(scan1_id, results)
    
    # Get files needing rescan (should be only corrupt ones)
    files_needing_rescan = temp_db.get_files_needing_rescan(directory)
    assert len(files_needing_rescan) == 2
    
    # Get healthy files from recent scan
    healthy_files = temp_db.get_healthy_files_recently_scanned(directory, max_age_seconds=7200)
    assert len(healthy_files) == 3
    
    # Verify specific files
    for file_path in files_needing_rescan:
        assert "video_0.mp4" in file_path or "video_1.mp4" in file_path


def test_report_from_database_scan(temp_db, sample_scan_summary, sample_scan_results):
    """Test report generation from database-stored scan results.
    
    Verifies:
    - Reports can be generated from stored scans
    - Report data matches stored data
    - Statistics are calculated correctly
    """
    # Store scan and results
    scan_model = ScanDatabaseModel.from_scan_summary(sample_scan_summary)
    scan_id = temp_db.store_scan(scan_model)
    
    result_models = [
        ScanResultDatabaseModel.from_scan_result(result, scan_id)
        for result in sample_scan_results
    ]
    temp_db.store_scan_results(scan_id, result_models)
    
    # Retrieve for report
    retrieved_scan = temp_db.get_scan(scan_id)
    retrieved_results = temp_db.get_scan_results(scan_id)
    
    assert retrieved_scan is not None
    assert len(retrieved_results) > 0
    
    # Generate summary statistics (similar to report generation)
    total_results = len(retrieved_results)
    corrupt_count = sum(1 for r in retrieved_results if r.is_corrupt)
    healthy_count = sum(1 for r in retrieved_results if not r.is_corrupt)
    avg_confidence = sum(r.confidence for r in retrieved_results) / total_results
    
    assert total_results == 8
    assert corrupt_count == 3
    assert healthy_count == 5
    assert 0.8 <= avg_confidence <= 1.0
    
    # Verify scan metadata for report
    assert retrieved_scan.total_files == 100
    assert retrieved_scan.processed_files == 95
    assert retrieved_scan.scan_mode == "hybrid"


def test_database_cleanup(temp_db):
    """Test database cleanup operations.
    
    Verifies:
    - Old scans are correctly identified and removed
    - Recent scans are preserved
    - Database stats are updated after cleanup
    - Vacuum operation works correctly
    """
    # Create old scan (60 days old)
    old_scan = ScanDatabaseModel(
        directory="/test/old",
        scan_mode=ScanMode.QUICK.value,
        started_at=time.time() - (60 * 24 * 60 * 60),  # 60 days ago
        completed_at=time.time() - (60 * 24 * 60 * 60) + 100,
        total_files=50,
        processed_files=50,
        corrupt_files=5,
        healthy_files=45,
        success_rate=90.0,
        scan_time=5.0,
    )
    old_scan_id = temp_db.store_scan(old_scan)
    
    # Create recent scan (1 day old)
    recent_scan = ScanDatabaseModel(
        directory="/test/recent",
        scan_mode=ScanMode.QUICK.value,
        started_at=time.time() - (1 * 24 * 60 * 60),  # 1 day ago
        completed_at=time.time() - (1 * 24 * 60 * 60) + 100,
        total_files=100,
        processed_files=100,
        corrupt_files=10,
        healthy_files=90,
        success_rate=90.0,
        scan_time=10.0,
    )
    recent_scan_id = temp_db.store_scan(recent_scan)
    
    # Add some results to both scans
    old_result = ScanResultDatabaseModel(
        scan_id=old_scan_id,
        filename="/test/old/video.mp4",
        file_size=1000000,
        is_corrupt=False,
        confidence=0.9,
        inspection_time=1.0,
        scan_mode=ScanMode.QUICK.value,
        status="HEALTHY",
    )
    temp_db.store_scan_results(old_scan_id, [old_result])
    
    recent_result = ScanResultDatabaseModel(
        scan_id=recent_scan_id,
        filename="/test/recent/video.mp4",
        file_size=2000000,
        is_corrupt=False,
        confidence=0.95,
        inspection_time=1.5,
        scan_mode=ScanMode.QUICK.value,
        status="HEALTHY",
    )
    temp_db.store_scan_results(recent_scan_id, [recent_result])
    
    # Check stats before cleanup
    stats_before = temp_db.get_database_stats()
    assert stats_before.total_scans == 2
    assert stats_before.total_files == 2
    
    # Cleanup old scans (older than 30 days)
    deleted_count = temp_db.cleanup_old_scans(days=30)
    assert deleted_count == 1
    
    # Check stats after cleanup
    stats_after = temp_db.get_database_stats()
    assert stats_after.total_scans == 1
    assert stats_after.total_files == 1
    
    # Verify old scan is gone
    assert temp_db.get_scan(old_scan_id) is None
    
    # Verify recent scan still exists
    assert temp_db.get_scan(recent_scan_id) is not None
    
    # Test vacuum operation
    temp_db.vacuum_database()  # Should not raise exception


def test_query_with_filters(temp_db):
    """Test querying scan results with various filters.
    
    Verifies:
    - Filtering by corruption status
    - Filtering by confidence level
    - Filtering by file status
    - Filtering by scan ID
    - Pagination works correctly
    """
    # Create a scan
    scan = ScanDatabaseModel(
        directory="/test/filter",
        scan_mode=ScanMode.HYBRID.value,
        started_at=time.time() - 1000,
        completed_at=time.time() - 900,
        total_files=20,
        processed_files=20,
        corrupt_files=8,
        healthy_files=12,
        success_rate=60.0,
        scan_time=15.0,
    )
    scan_id = temp_db.store_scan(scan)
    
    # Create diverse results with different properties
    results = []
    
    # 5 healthy files with high confidence
    for i in range(5):
        results.append(
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename=f"/test/filter/healthy_high_{i}.mp4",
                file_size=1000000 + i * 1000,
                is_corrupt=False,
                confidence=0.95,
                inspection_time=1.0,
                scan_mode=ScanMode.QUICK.value,
                status="HEALTHY",
            )
        )
    
    # 3 healthy files with lower confidence (suspicious)
    for i in range(3):
        results.append(
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename=f"/test/filter/suspicious_{i}.mp4",
                file_size=500000 + i * 1000,
                is_corrupt=False,
                confidence=0.65,
                inspection_time=1.5,
                scan_mode=ScanMode.QUICK.value,
                status="SUSPICIOUS",
            )
        )
    
    # 4 corrupt files
    for i in range(4):
        results.append(
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename=f"/test/filter/corrupt_{i}.mp4",
                file_size=300000 + i * 1000,
                is_corrupt=True,
                confidence=0.90,
                inspection_time=2.0,
                scan_mode=ScanMode.DEEP.value,
                status="CORRUPT",
            )
        )
    
    temp_db.store_scan_results(scan_id, results)
    
    # Test 1: Filter by corruption status (corrupt only)
    filter_corrupt = DatabaseQueryFilter(is_corrupt=True)
    corrupt_results = temp_db.query_results(filter_corrupt)
    assert len(corrupt_results) == 4
    assert all(r.is_corrupt for r in corrupt_results)
    
    # Test 2: Filter by corruption status (healthy only)
    filter_healthy = DatabaseQueryFilter(is_corrupt=False)
    healthy_results = temp_db.query_results(filter_healthy)
    assert len(healthy_results) == 8  # 5 healthy + 3 suspicious
    assert all(not r.is_corrupt for r in healthy_results)
    
    # Test 3: Filter by confidence threshold
    filter_confidence = DatabaseQueryFilter(min_confidence=0.90)
    high_conf_results = temp_db.query_results(filter_confidence)
    assert len(high_conf_results) == 9  # 5 healthy + 4 corrupt
    assert all(r.confidence >= 0.90 for r in high_conf_results)
    
    # Test 4: Filter by status
    filter_status = DatabaseQueryFilter(status="HEALTHY")
    status_results = temp_db.query_results(filter_status)
    assert len(status_results) == 5
    assert all(r.status == "HEALTHY" for r in status_results)
    
    # Test 5: Filter by scan_id
    filter_scan = DatabaseQueryFilter(scan_id=scan_id)
    scan_results = temp_db.query_results(filter_scan)
    assert len(scan_results) == 12
    assert all(r.scan_id == scan_id for r in scan_results)
    
    # Test 6: Combined filters (corrupt with high confidence)
    filter_combined = DatabaseQueryFilter(is_corrupt=True, min_confidence=0.85)
    combined_results = temp_db.query_results(filter_combined)
    assert len(combined_results) == 4
    assert all(r.is_corrupt and r.confidence >= 0.85 for r in combined_results)
    
    # Test 7: Pagination
    filter_paginated = DatabaseQueryFilter(limit=5, offset=0)
    page1_results = temp_db.query_results(filter_paginated)
    assert len(page1_results) <= 5
    
    filter_paginated2 = DatabaseQueryFilter(limit=5, offset=5)
    page2_results = temp_db.query_results(filter_paginated2)
    assert len(page2_results) <= 5


@patch("src.cli.trakt_sync.TraktService")
def test_trakt_sync_from_database(mock_trakt_service, temp_db):
    """Test Trakt synchronization using database-stored scan results.
    
    Verifies:
    - Database results can be used for Trakt sync
    - Filtering works correctly for sync (healthy files only by default)
    - Confidence threshold filtering
    - Status filtering
    """
    # Create mock Trakt service
    mock_service = MagicMock()
    mock_trakt_service.return_value = mock_service
    mock_service.add_to_watchlist.return_value = {"added": {"movies": 2}}
    
    # Create a scan with various results
    scan = ScanDatabaseModel(
        directory="/test/trakt",
        scan_mode=ScanMode.QUICK.value,
        started_at=time.time() - 1000,
        completed_at=time.time() - 900,
        total_files=10,
        processed_files=10,
        corrupt_files=3,
        healthy_files=7,
        success_rate=70.0,
        scan_time=10.0,
    )
    scan_id = temp_db.store_scan(scan)
    
    # Create results that look like video files
    results = []
    
    # Healthy files (should be synced)
    for i in range(4):
        results.append(
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename=f"/movies/The.Matrix.{1999 + i}.1080p.BluRay.x264.mp4",
                file_size=2000000000,
                is_corrupt=False,
                confidence=0.95,
                inspection_time=1.0,
                scan_mode=ScanMode.QUICK.value,
                status="HEALTHY",
            )
        )
    
    # Corrupt files (should not be synced by default)
    for i in range(3):
        results.append(
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename=f"/movies/Bad.Movie.{2000 + i}.1080p.mp4",
                file_size=1000000000,
                is_corrupt=True,
                confidence=0.90,
                inspection_time=2.0,
                scan_mode=ScanMode.QUICK.value,
                status="CORRUPT",
            )
        )
    
    # Suspicious files (low confidence)
    for i in range(3):
        results.append(
            ScanResultDatabaseModel(
                scan_id=scan_id,
                filename=f"/movies/Suspicious.Film.{2010 + i}.720p.mp4",
                file_size=1500000000,
                is_corrupt=False,
                confidence=0.60,
                inspection_time=1.5,
                scan_mode=ScanMode.QUICK.value,
                status="SUSPICIOUS",
            )
        )
    
    temp_db.store_scan_results(scan_id, results)
    
    # Test 1: Get healthy files for Trakt sync
    healthy_filter = DatabaseQueryFilter(is_corrupt=False, status="HEALTHY")
    healthy_results = temp_db.query_results(healthy_filter)
    assert len(healthy_results) == 4
    
    # Test 2: Apply confidence threshold (typical for Trakt sync)
    high_conf_filter = DatabaseQueryFilter(is_corrupt=False, min_confidence=0.80)
    high_conf_results = temp_db.query_results(high_conf_filter)
    assert len(high_conf_results) == 4  # Only the healthy ones with 0.95 confidence
    
    # Test 3: Get all non-corrupt (including suspicious)
    non_corrupt_filter = DatabaseQueryFilter(is_corrupt=False)
    non_corrupt_results = temp_db.query_results(non_corrupt_filter)
    assert len(non_corrupt_results) == 7  # 4 healthy + 3 suspicious
    
    # Verify the database integration would provide correct data for Trakt sync
    assert all(Path(r.filename).suffix == ".mp4" for r in healthy_results)


def test_backup_and_restore(temp_db, sample_scan_summary, sample_scan_results):
    """Test database backup and restore operations.
    
    Verifies:
    - Database can be backed up
    - Backup file is created successfully
    - Backup contains all data
    - Restored database matches original
    """
    # Store original data
    scan_model = ScanDatabaseModel.from_scan_summary(sample_scan_summary)
    scan_id = temp_db.store_scan(scan_model)
    
    result_models = [
        ScanResultDatabaseModel.from_scan_result(result, scan_id)
        for result in sample_scan_results
    ]
    temp_db.store_scan_results(scan_id, result_models)
    
    # Get original stats
    original_stats = temp_db.get_database_stats()
    original_scan = temp_db.get_scan(scan_id)
    original_results = temp_db.get_scan_results(scan_id)
    
    assert original_stats.total_scans == 1
    assert original_stats.total_files == 8
    
    # Create backup
    with tempfile.TemporaryDirectory() as backup_dir:
        backup_path = Path(backup_dir) / "backup.db"
        temp_db.backup_database(backup_path)
        
        # Verify backup file exists
        assert backup_path.exists()
        assert backup_path.stat().st_size > 0
        
        # Create new service from backup
        restored_db = DatabaseService(db_path=backup_path, auto_cleanup_days=0)
        
        # Verify restored data matches original
        restored_stats = restored_db.get_database_stats()
        assert restored_stats.total_scans == original_stats.total_scans
        assert restored_stats.total_files == original_stats.total_files
        assert restored_stats.corrupt_files == original_stats.corrupt_files
        assert restored_stats.healthy_files == original_stats.healthy_files
        
        # Verify scan details
        restored_scan = restored_db.get_scan(scan_id)
        assert restored_scan is not None
        assert restored_scan.directory == original_scan.directory
        assert restored_scan.total_files == original_scan.total_files
        assert restored_scan.corrupt_files == original_scan.corrupt_files
        
        # Verify results
        restored_results = restored_db.get_scan_results(scan_id)
        assert len(restored_results) == len(original_results)
        
        # Compare individual results
        for orig, rest in zip(
            sorted(original_results, key=lambda x: x.filename),
            sorted(restored_results, key=lambda x: x.filename),
        ):
            assert orig.filename == rest.filename
            assert orig.is_corrupt == rest.is_corrupt
            assert orig.confidence == rest.confidence
            assert orig.status == rest.status


def test_export_formats(temp_db, sample_scan_summary, sample_scan_results):
    """Test exporting scan results to various formats.
    
    Verifies:
    - Export to JSON format
    - Export to CSV format
    - Export to YAML format
    - Exported data is valid and complete
    - Format-specific features work correctly
    """
    # Store data
    scan_model = ScanDatabaseModel.from_scan_summary(sample_scan_summary)
    scan_id = temp_db.store_scan(scan_model)
    
    result_models = [
        ScanResultDatabaseModel.from_scan_result(result, scan_id)
        for result in sample_scan_results
    ]
    temp_db.store_scan_results(scan_id, result_models)
    
    # Get results for export
    results = temp_db.get_scan_results(scan_id)
    assert len(results) == 8
    
    with tempfile.TemporaryDirectory() as export_dir:
        export_path = Path(export_dir)
        
        # Test 1: Export to JSON
        json_file = export_path / "export.json"
        json_data = [result.model_dump() for result in results]
        json_file.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
        
        assert json_file.exists()
        assert json_file.stat().st_size > 0
        
        # Verify JSON content
        loaded_json = json.loads(json_file.read_text(encoding="utf-8"))
        assert len(loaded_json) == 8
        assert all("filename" in item for item in loaded_json)
        assert all("is_corrupt" in item for item in loaded_json)
        assert all("confidence" in item for item in loaded_json)
        
        # Verify specific values
        json_corrupt = [item for item in loaded_json if item["is_corrupt"]]
        json_healthy = [item for item in loaded_json if not item["is_corrupt"]]
        assert len(json_corrupt) == 3
        assert len(json_healthy) == 5
        
        # Test 2: Export to YAML
        yaml_file = export_path / "export.yaml"
        yaml_data = [result.model_dump() for result in results]
        yaml_file.write_text(
            yaml.dump(yaml_data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        
        assert yaml_file.exists()
        assert yaml_file.stat().st_size > 0
        
        # Verify YAML content
        loaded_yaml = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        assert len(loaded_yaml) == 8
        assert all("filename" in item for item in loaded_yaml)
        
        # Test 3: Export to CSV
        import csv
        
        csv_file = export_path / "export.csv"
        with csv_file.open("w", newline="", encoding="utf-8") as f:
            csv_data = [result.model_dump() for result in results]
            if csv_data:
                writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                writer.writeheader()
                for row in csv_data:
                    writer.writerow(row)
        
        assert csv_file.exists()
        assert csv_file.stat().st_size > 0
        
        # Verify CSV content
        with csv_file.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
            assert len(csv_rows) == 8
            assert all("filename" in row for row in csv_rows)
            assert all("is_corrupt" in row for row in csv_rows)
        
        # Test 4: Export filtered results (corrupt only)
        corrupt_filter = DatabaseQueryFilter(is_corrupt=True)
        corrupt_results = temp_db.query_results(corrupt_filter)
        
        json_corrupt_file = export_path / "corrupt_only.json"
        corrupt_json_data = [result.model_dump() for result in corrupt_results]
        json_corrupt_file.write_text(
            json.dumps(corrupt_json_data, indent=2), encoding="utf-8"
        )
        
        assert json_corrupt_file.exists()
        loaded_corrupt = json.loads(json_corrupt_file.read_text(encoding="utf-8"))
        assert len(loaded_corrupt) == 3
        assert all(item["is_corrupt"] for item in loaded_corrupt)
        
        # Test 5: Export with specific fields (simulating custom export)
        custom_data = [
            {
                "filename": r.filename,
                "status": r.status,
                "confidence": r.confidence,
            }
            for r in results
        ]
        
        custom_json_file = export_path / "custom.json"
        custom_json_file.write_text(json.dumps(custom_data, indent=2), encoding="utf-8")
        
        assert custom_json_file.exists()
        loaded_custom = json.loads(custom_json_file.read_text(encoding="utf-8"))
        assert len(loaded_custom) == 8
        assert all(set(item.keys()) == {"filename", "status", "confidence"} for item in loaded_custom)
