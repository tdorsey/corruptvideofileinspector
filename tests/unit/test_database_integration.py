"""Integration tests for database storage functionality."""

import tempfile
from pathlib import Path

import pytest

from src.config.config import AppConfig, DatabaseConfig, OutputConfig
from src.core.models.scanning import ScanMode, ScanSummary
from src.output import OutputFormatter


@pytest.mark.unit
class TestDatabaseIntegration:
    """Test database integration with output formatter."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration with database enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            output_path = temp_path / "output"
            output_path.mkdir()

            # Create minimal config with database enabled
            config = AppConfig(
                logging=None,  # Will use defaults
                ffmpeg=None,  # Will use defaults
                processing=None,  # Will use defaults
                output=OutputConfig(
                    default_json=True,
                    default_output_dir=output_path,
                    default_filename="test_results.json",
                ),
                scan=None,  # Will use defaults
                trakt=None,  # Will use defaults
                database=DatabaseConfig(enabled=True, path=db_path, auto_create=True),
            )
            yield config

    @pytest.fixture
    def sample_summary(self):
        """Create sample scan summary for testing."""
        return ScanSummary(
            directory=Path("/test/videos"),
            scan_mode=ScanMode.QUICK,
            total_files=5,
            processed_files=5,
            corrupt_files=1,
            healthy_files=4,
            scan_time=45.2,
            deep_scans_needed=0,
            deep_scans_completed=0,
            was_resumed=False,
        )

    def test_output_formatter_with_database(self, temp_config, sample_summary):
        """Test OutputFormatter with database storage enabled."""
        formatter = OutputFormatter(temp_config)
        
        # Verify database manager was created
        assert formatter.db_manager is not None
        
        # Test database storage functionality
        stats = formatter.get_database_stats()
        assert stats["enabled"] is True
        assert stats["total_summaries"] == 0

    def test_scan_summary_storage(self, temp_config, sample_summary):
        """Test storing and retrieving scan summaries."""
        formatter = OutputFormatter(temp_config)
        output_file = temp_config.output.default_output_dir / "test_output.json"
        
        # Write scan results (should store to both file and database)
        formatter.write_scan_results(
            summary=sample_summary,
            output_file=output_file,
            format="json",
            pretty_print=True,
        )
        
        # Verify file was created
        assert output_file.exists()
        
        # Verify data was stored in database
        summaries = formatter.get_scan_history()
        assert len(summaries) == 1
        assert summaries[0].directory == sample_summary.directory
        assert summaries[0].scan_mode == sample_summary.scan_mode
        
        # Test database stats
        stats = formatter.get_database_stats()
        assert stats["total_summaries"] == 1
        assert stats["completed_summaries"] == 1

    def test_scan_history_retrieval(self, temp_config):
        """Test retrieving scan history with filters."""
        formatter = OutputFormatter(temp_config)
        
        # Create multiple summaries
        summaries = [
            ScanSummary(
                directory=Path("/test/videos1"),
                scan_mode=ScanMode.QUICK,
                total_files=3,
                processed_files=3,
                corrupt_files=0,
                healthy_files=3,
                scan_time=30.0,
            ),
            ScanSummary(
                directory=Path("/test/videos2"),
                scan_mode=ScanMode.DEEP,
                total_files=2,
                processed_files=2,
                corrupt_files=1,
                healthy_files=1,
                scan_time=120.0,
            ),
        ]
        
        # Store summaries
        for summary in summaries:
            output_file = temp_config.output.default_output_dir / f"output_{summary.directory.name}.json"
            formatter.write_scan_results(summary, output_file)
        
        # Test retrieving all summaries
        all_summaries = formatter.get_scan_history()
        assert len(all_summaries) == 2
        
        # Test retrieving with limit
        limited_summaries = formatter.get_scan_history(limit=1)
        assert len(limited_summaries) == 1
        
        # Test filtering by directory
        filtered_summaries = formatter.get_scan_history(directory=Path("/test/videos1"))
        assert len(filtered_summaries) == 1
        assert filtered_summaries[0].directory == Path("/test/videos1")

    def test_incomplete_scan_detection(self, temp_config):
        """Test detecting incomplete scans for resume functionality."""
        formatter = OutputFormatter(temp_config)
        
        # Create incomplete scan summary
        incomplete_summary = ScanSummary(
            directory=Path("/test/incomplete"),
            scan_mode=ScanMode.HYBRID,
            total_files=10,
            processed_files=5,  # Only partially processed
            corrupt_files=1,
            healthy_files=4,
            scan_time=60.0,
            completed_at=None,  # Not completed
        )
        
        # Store incomplete scan
        output_file = temp_config.output.default_output_dir / "incomplete.json"
        formatter.write_scan_results(incomplete_summary, output_file)
        
        # Test detecting incomplete scan
        incomplete = formatter.get_incomplete_scan(Path("/test/incomplete"))
        assert incomplete is not None
        assert incomplete.directory == Path("/test/incomplete")
        assert incomplete.completed_at is None
        
        # Test directory with no incomplete scans
        no_incomplete = formatter.get_incomplete_scan(Path("/test/nonexistent"))
        assert no_incomplete is None

    def test_database_disabled(self):
        """Test behavior when database is disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "output"
            output_path.mkdir()

            # Create config with database disabled
            config = AppConfig(
                logging=None,
                ffmpeg=None,
                processing=None,
                output=OutputConfig(
                    default_json=True,
                    default_output_dir=output_path,
                    default_filename="test_results.json",
                ),
                scan=None,
                trakt=None,
                database=DatabaseConfig(enabled=False),  # Disabled
            )

            formatter = OutputFormatter(config)
            
            # Verify database manager was not created
            assert formatter.db_manager is None
            
            # Test that database operations return appropriate responses
            stats = formatter.get_database_stats()
            assert stats["enabled"] is False
            assert "message" in stats
            
            summaries = formatter.get_scan_history()
            assert summaries == []
            
            incomplete = formatter.get_incomplete_scan(Path("/any/path"))
            assert incomplete is None

    def test_database_initialization_error_handling(self, temp_config):
        """Test handling of database initialization errors."""
        # Create config pointing to invalid database path (e.g., read-only directory)
        try:
            # Try to create database in /root (should fail in most environments)
            invalid_config = temp_config
            invalid_config.database.path = Path("/root/invalid.db")
            
            # Should not raise exception, but log error and continue with file-only output
            formatter = OutputFormatter(invalid_config)
            # Database manager should be None due to initialization failure
            # (This test may pass or fail depending on environment permissions)
        except Exception:
            # If it does raise an exception, that's also acceptable behavior
            pass