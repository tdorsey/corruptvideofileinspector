"""
Unit tests for API models.
"""

import pytest

try:
    from src.api.models import (
        DatabaseStatsResponse,
        HealthResponse,
        ScanRequest,
        ScanResponse,
        ScanStatusEnum,
        ScanStatusResponse,
    )
    from src.core.models.scanning import ScanMode

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.unit

# Skip all tests if FastAPI is not installed
if not FASTAPI_AVAILABLE:
    pytest.skip("FastAPI not installed", allow_module_level=True)


class TestAPIModels:
    """Test API model validation and serialization."""

    def test_health_response_creation(self):
        """Test HealthResponse model creation."""
        response = HealthResponse(status="healthy", version="0.1.0", ffmpeg_available=True)
        assert response.status == "healthy"
        assert response.version == "0.1.0"
        assert response.ffmpeg_available is True

    def test_scan_request_defaults(self):
        """Test ScanRequest with default values."""
        request = ScanRequest(directory="/test/path")
        assert request.directory == "/test/path"
        assert request.mode == ScanMode.QUICK
        assert request.recursive is True
        assert request.max_workers == 8

    def test_scan_request_custom_values(self):
        """Test ScanRequest with custom values."""
        request = ScanRequest(
            directory="/test/path",
            mode=ScanMode.DEEP,
            recursive=False,
            max_workers=16,
        )
        assert request.mode == ScanMode.DEEP
        assert request.recursive is False
        assert request.max_workers == 16

    def test_scan_request_max_workers_validation(self):
        """Test ScanRequest validates max_workers range."""
        from pydantic import ValidationError

        # Valid values
        request = ScanRequest(directory="/test", max_workers=1)
        assert request.max_workers == 1

        request = ScanRequest(directory="/test", max_workers=32)
        assert request.max_workers == 32

        # Invalid values should raise validation error
        with pytest.raises(ValidationError, match="max_workers"):
            ScanRequest(directory="/test", max_workers=0)

        with pytest.raises(ValidationError, match="max_workers"):
            ScanRequest(directory="/test", max_workers=33)

    def test_scan_response_creation(self):
        """Test ScanResponse model creation."""
        response = ScanResponse(
            scan_id="test-id-123",
            status=ScanStatusEnum.PENDING,
            message="Scan started",
        )
        assert response.scan_id == "test-id-123"
        assert response.status == ScanStatusEnum.PENDING
        assert response.message == "Scan started"

    def test_scan_status_response_with_progress(self):
        """Test ScanStatusResponse with progress data."""
        response = ScanStatusResponse(
            scan_id="test-id",
            status=ScanStatusEnum.RUNNING,
            directory="/test",
            mode="quick",
            progress={
                "processed_count": 10,
                "total_files": 100,
                "progress_percentage": 10.0,
            },
        )
        assert response.status == ScanStatusEnum.RUNNING
        assert response.progress["processed_count"] == 10
        assert response.results is None
        assert response.error is None

    def test_scan_status_response_with_error(self):
        """Test ScanStatusResponse with error."""
        response = ScanStatusResponse(
            scan_id="test-id",
            status=ScanStatusEnum.FAILED,
            directory="/test",
            mode="quick",
            progress={},
            error="Test error message",
        )
        assert response.status == ScanStatusEnum.FAILED
        assert response.error == "Test error message"

    def test_database_stats_response(self):
        """Test DatabaseStatsResponse model."""
        response = DatabaseStatsResponse(
            total_files=100,
            healthy_files=90,
            corrupt_files=10,
            suspicious_files=5,
            last_scan_time="2024-01-01T00:00:00Z",
        )
        assert response.total_files == 100
        assert response.healthy_files == 90
        assert response.corrupt_files == 10
        assert response.suspicious_files == 5
        assert response.last_scan_time == "2024-01-01T00:00:00Z"

    def test_database_stats_response_without_last_scan(self):
        """Test DatabaseStatsResponse without last scan time."""
        response = DatabaseStatsResponse(
            total_files=0,
            healthy_files=0,
            corrupt_files=0,
            suspicious_files=0,
        )
        assert response.last_scan_time is None

    def test_scan_status_enum_values(self):
        """Test ScanStatusEnum has expected values."""
        assert ScanStatusEnum.PENDING.value == "pending"
        assert ScanStatusEnum.RUNNING.value == "running"
        assert ScanStatusEnum.COMPLETED.value == "completed"
        assert ScanStatusEnum.FAILED.value == "failed"
        assert ScanStatusEnum.CANCELLED.value == "cancelled"
