"""Unit tests for database GraphQL API endpoints."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.api.graphql.resolvers import Query, get_database_service
from src.config.config import AppConfig, DatabaseConfig
from src.database.models import DatabaseQueryFilter, DatabaseStats
from src.database.service import DatabaseService


@pytest.mark.unit
def test_get_database_service_with_valid_config():
    """Test get_database_service returns DatabaseService with valid config."""
    config = MagicMock(spec=AppConfig)
    config.database = DatabaseConfig(
        path=Path("/tmp/test.db"), auto_cleanup_days=30, create_backup=True
    )

    with patch("src.api.graphql.resolvers.DatabaseService") as MockDBService:
        result = get_database_service(config)
        MockDBService.assert_called_once()


@pytest.mark.unit
def test_get_database_service_without_database_config():
    """Test get_database_service returns None when database config is missing."""
    config = MagicMock(spec=AppConfig)
    config.database = None

    result = get_database_service(config)
    assert result is None


@pytest.mark.unit
def test_database_stats_query():
    """Test database_stats GraphQL query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_service = DatabaseService(db_path=db_path, auto_cleanup_days=0)

        # Create mock info context
        mock_info = MagicMock()
        config = MagicMock(spec=AppConfig)
        config.database = DatabaseConfig(
            path=db_path, auto_cleanup_days=0, create_backup=True
        )
        mock_info.context = {"config": config}

        # Create query instance and call database_stats
        query = Query()
        result = query.database_stats(mock_info)

        assert result is not None
        assert result.total_scans == 0
        assert result.total_files == 0
        assert result.corrupt_files == 0
        assert result.healthy_files == 0


@pytest.mark.unit
def test_database_query_with_filter():
    """Test database_query GraphQL query with filter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_service = DatabaseService(db_path=db_path, auto_cleanup_days=0)

        # Create mock info context
        mock_info = MagicMock()
        config = MagicMock(spec=AppConfig)
        config.database = DatabaseConfig(
            path=db_path, auto_cleanup_days=0, create_backup=True
        )
        mock_info.context = {"config": config}

        # Create query instance and call database_query
        query = Query()
        result = query.database_query(mock_info, filter=None)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.unit
def test_corruption_trend_query():
    """Test corruption_trend GraphQL query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_service = DatabaseService(db_path=db_path, auto_cleanup_days=0)

        # Create mock info context
        mock_info = MagicMock()
        config = MagicMock(spec=AppConfig)
        config.database = DatabaseConfig(
            path=db_path, auto_cleanup_days=0, create_backup=True
        )
        mock_info.context = {"config": config}

        # Create query instance and call corruption_trend
        query = Query()
        result = query.corruption_trend(mock_info, directory="/test/directory", days=30)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.unit
def test_scan_history_query():
    """Test scan_history GraphQL query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_service = DatabaseService(db_path=db_path, auto_cleanup_days=0)

        # Create mock info context
        mock_info = MagicMock()
        config = MagicMock(spec=AppConfig)
        config.database = DatabaseConfig(
            path=db_path, auto_cleanup_days=0, create_backup=True
        )
        mock_info.context = {"config": config}

        # Create query instance and call scan_history
        query = Query()
        result = query.scan_history(mock_info, limit=10)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.unit
def test_database_stats_with_no_config():
    """Test database_stats returns None when database config is missing."""
    mock_info = MagicMock()
    config = MagicMock(spec=AppConfig)
    config.database = None
    mock_info.context = {"config": config}

    query = Query()
    result = query.database_stats(mock_info)

    assert result is None


@pytest.mark.unit
def test_database_query_with_no_config():
    """Test database_query returns empty list when database config is missing."""
    mock_info = MagicMock()
    config = MagicMock(spec=AppConfig)
    config.database = None
    mock_info.context = {"config": config}

    query = Query()
    result = query.database_query(mock_info, filter=None)

    assert result == []


@pytest.mark.unit
def test_corruption_trend_with_no_config():
    """Test corruption_trend returns empty list when database config is missing."""
    mock_info = MagicMock()
    config = MagicMock(spec=AppConfig)
    config.database = None
    mock_info.context = {"config": config}

    query = Query()
    result = query.corruption_trend(mock_info, directory="/test/directory", days=30)

    assert result == []


@pytest.mark.unit
def test_scan_history_with_no_config():
    """Test scan_history returns empty list when database config is missing."""
    mock_info = MagicMock()
    config = MagicMock(spec=AppConfig)
    config.database = None
    mock_info.context = {"config": config}

    query = Query()
    result = query.scan_history(mock_info, limit=10)

    assert result == []
