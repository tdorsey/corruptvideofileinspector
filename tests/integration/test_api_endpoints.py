"""
Integration tests for API endpoints.
"""

import pytest

try:
    from fastapi.testclient import TestClient

    from src.api.main import create_app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.integration

# Skip all tests if FastAPI is not installed
if not FASTAPI_AVAILABLE:
    pytest.skip("FastAPI not installed", allow_module_level=True)


@pytest.fixture
def client():
    """Create test client for API."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test health check returns 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_returns_correct_structure(self, client):
        """Test health check returns expected JSON structure."""
        response = client.get("/api/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "ffmpeg_available" in data

    def test_health_check_status_is_healthy(self, client):
        """Test health check status is 'healthy'."""
        response = client.get("/api/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_check_has_version(self, client):
        """Test health check includes version number."""
        response = client.get("/api/health")
        data = response.json()

        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_health_check_ffmpeg_status(self, client):
        """Test health check reports FFmpeg availability."""
        response = client.get("/api/health")
        data = response.json()

        assert isinstance(data["ffmpeg_available"], bool)


class TestScanEndpoints:
    """Test scan-related endpoints."""

    def test_start_scan_requires_directory(self, client):
        """Test starting scan requires directory parameter."""
        response = client.post("/api/scans", json={})
        # Should return 422 for missing required field
        assert response.status_code == 422

    def test_start_scan_with_invalid_directory(self, client):
        """Test starting scan with non-existent directory returns error."""
        response = client.post(
            "/api/scans",
            json={
                "directory": "/nonexistent/path/that/does/not/exist",
                "mode": "quick",
                "recursive": True,
                "max_workers": 8,
            },
        )
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower()

    def test_start_scan_validates_max_workers(self, client):
        """Test start scan validates max_workers parameter."""
        response = client.post(
            "/api/scans",
            json={
                "directory": "/tmp",
                "mode": "quick",
                "max_workers": 0,  # Invalid: too low
            },
        )
        assert response.status_code == 422

        response = client.post(
            "/api/scans",
            json={
                "directory": "/tmp",
                "mode": "quick",
                "max_workers": 100,  # Invalid: too high
            },
        )
        assert response.status_code == 422

    def test_get_scan_status_invalid_id(self, client):
        """Test getting status of non-existent scan returns 404."""
        response = client.get("/api/scans/nonexistent-scan-id")
        assert response.status_code == 404

    def test_get_scan_results_invalid_id(self, client):
        """Test getting results of non-existent scan returns 404."""
        response = client.get("/api/scans/nonexistent-scan-id/results")
        assert response.status_code == 404

    def test_cancel_scan_invalid_id(self, client):
        """Test cancelling non-existent scan returns 404."""
        response = client.delete("/api/scans/nonexistent-scan-id")
        assert response.status_code == 404


class TestDatabaseEndpoints:
    """Test database-related endpoints."""

    def test_database_stats_returns_200(self, client):
        """Test database stats endpoint returns 200 OK."""
        response = client.get("/api/database/stats")
        assert response.status_code == 200

    def test_database_stats_structure(self, client):
        """Test database stats returns expected structure."""
        response = client.get("/api/database/stats")
        data = response.json()

        assert "total_files" in data
        assert "healthy_files" in data
        assert "corrupt_files" in data
        assert "suspicious_files" in data
        assert "last_scan_time" in data

    def test_database_stats_types(self, client):
        """Test database stats field types."""
        response = client.get("/api/database/stats")
        data = response.json()

        assert isinstance(data["total_files"], int)
        assert isinstance(data["healthy_files"], int)
        assert isinstance(data["corrupt_files"], int)
        assert isinstance(data["suspicious_files"], int)
        # last_scan_time can be null or string
        assert data["last_scan_time"] is None or isinstance(data["last_scan_time"], str)


class TestCORSHeaders:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present in responses from allowed origins."""
        # Test with an allowed origin
        response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})

        # Should receive CORS headers for allowed origins
        assert response.status_code == 200
        # CORS headers should be present when using allowed origin
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]
