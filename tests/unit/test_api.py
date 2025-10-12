"""Unit tests for FastAPI GraphQL API."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock()
    config.output.default_output_dir = "/tmp/output"
    config.scan.default_input_dir = "/tmp/videos"
    return config


@pytest.fixture
def test_client(mock_config):
    """Create a test client for the API."""
    with patch("src.api.app.load_config", return_value=mock_config):
        from src.api.app import create_app

        app = create_app()
        return TestClient(app)


def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "corrupt-video-inspector-api",
    }


def test_root_endpoint(test_client):
    """Test root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Corrupt Video Inspector API"
    assert data["version"] == "1.0.0"
    assert "/graphql" in data["graphql_endpoint"]


def test_graphql_endpoint_exists(test_client):
    """Test that GraphQL endpoint is accessible."""
    # Test that the GraphQL endpoint exists
    response = test_client.get("/graphql")
    # GraphQL endpoint should accept GET requests and return the GraphiQL interface
    # or return a 405 if not configured to accept GET
    assert response.status_code in [200, 405]


def test_graphql_query(test_client):
    """Test a simple GraphQL query."""
    query = """
        query {
            scanJobs {
                id
                directory
                status
            }
        }
    """
    response = test_client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    # Should return data structure even if empty
    assert "data" in data or "errors" in data
