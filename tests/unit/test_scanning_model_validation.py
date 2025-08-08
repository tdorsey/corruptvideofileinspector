"""Tests for scanning model validation improvements."""
import pytest
from pathlib import Path
from unittest.mock import patch

from src.core.models.scanning import (
    ScanResult,
    ScanSummary,
    ScanProgress,
    BatchScanRequest,
    ScanMode,
    OutputFormat,
    ScanPhase,
)
from src.core.models.inspection import VideoFile


class TestScanResultValidation:
    """Test ScanResult.model_validate behavior."""

    def test_dict_with_video_file_dict(self):
        """Test validation with video_file as dict."""
        data = {
            "video_file": {"path": "/test/video.mp4"},
            "is_corrupt": True,
            "error_message": "Test error",
        }
        result = ScanResult.model_validate(data)
        assert isinstance(result.video_file, VideoFile)
        assert result.video_file.path == Path("/test/video.mp4")
        assert result.is_corrupt is True

    def test_dict_with_filename_legacy(self):
        """Test validation with legacy filename field."""
        data = {
            "filename": "/test/video.mp4",
            "is_corrupt": False,
            "scan_mode": "quick",
        }
        result = ScanResult.model_validate(data)
        assert isinstance(result.video_file, VideoFile)
        assert result.video_file.path == Path("/test/video.mp4")
        assert result.scan_mode == ScanMode.QUICK

    def test_dict_with_string_scan_mode(self):
        """Test validation with string scan_mode."""
        data = {
            "video_file": {"path": "/test/video.mp4"},
            "scan_mode": "deep",
        }
        result = ScanResult.model_validate(data)
        assert result.scan_mode == ScanMode.DEEP

    def test_strict_mode_support(self):
        """Test that strict mode is properly supported."""
        data = {
            "video_file": {"path": "/test/video.mp4"},
            "is_corrupt": True,
            "scan_mode": ScanMode.QUICK,  # Use enum directly in strict mode
        }
        result = ScanResult.model_validate(data, strict=True)
        assert result.scan_mode == ScanMode.QUICK

    def test_context_support(self):
        """Test that context parameter is supported."""
        data = {
            "video_file": {"path": "/test/video.mp4"},
        }
        context = {"test_key": "test_value"}
        result = ScanResult.model_validate(data, context=context)
        assert isinstance(result, ScanResult)

    def test_from_attributes_support(self):
        """Test that from_attributes parameter is supported."""
        data = {
            "video_file": {"path": "/test/video.mp4"},
        }
        result = ScanResult.model_validate(data, from_attributes=False)
        assert isinstance(result, ScanResult)


class TestScanSummaryValidation:
    """Test ScanSummary.model_validate behavior."""

    def test_dict_with_string_directory(self):
        """Test validation with directory as string."""
        data = {
            "directory": "/test/dir",
            "total_files": 10,
            "processed_files": 8,
            "corrupt_files": 2,
            "healthy_files": 6,
            "scan_mode": "hybrid",
            "scan_time": 30.5,
        }
        result = ScanSummary.model_validate(data)
        assert result.directory == Path("/test/dir")
        assert result.scan_mode == ScanMode.HYBRID

    def test_dict_with_path_directory(self):
        """Test validation with directory as Path."""
        data = {
            "directory": Path("/test/dir"),
            "total_files": 5,
            "processed_files": 5,
            "corrupt_files": 0,
            "healthy_files": 5,
            "scan_mode": ScanMode.QUICK,
            "scan_time": 15.0,
        }
        result = ScanSummary.model_validate(data)
        assert result.directory == Path("/test/dir")
        assert result.scan_mode == ScanMode.QUICK

    def test_strict_mode_with_enums(self):
        """Test strict mode with proper enum values."""
        data = {
            "directory": Path("/test/dir"),
            "total_files": 5,
            "processed_files": 5,
            "corrupt_files": 0,
            "healthy_files": 5,
            "scan_mode": ScanMode.QUICK,
            "scan_time": 15.0,
        }
        result = ScanSummary.model_validate(data, strict=True)
        assert result.scan_mode == ScanMode.QUICK


class TestScanProgressValidation:
    """Test ScanProgress.model_validate behavior."""

    def test_dict_with_string_enums(self):
        """Test validation with string enum values."""
        data = {
            "current_file": "/test/file.mp4",
            "total_files": 5,
            "processed_count": 2,
            "phase": "deep_scan",
            "scan_mode": "full",
        }
        result = ScanProgress.model_validate(data)
        assert result.phase == ScanPhase.DEEP_SCAN
        assert result.scan_mode == ScanMode.FULL

    def test_dict_with_enum_objects(self):
        """Test validation with actual enum objects."""
        data = {
            "total_files": 10,
            "processed_count": 5,
            "phase": ScanPhase.SCANNING,
            "scan_mode": ScanMode.HYBRID,
        }
        result = ScanProgress.model_validate(data)
        assert result.phase == ScanPhase.SCANNING
        assert result.scan_mode == ScanMode.HYBRID


class TestBatchScanRequestValidation:
    """Test BatchScanRequest.model_validate behavior."""

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_dict_with_string_paths(self, mock_is_dir, mock_exists):
        """Test validation with string directory paths."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        
        data = {
            "directories": ["/test/dir1", "/test/dir2"],
            "scan_mode": "hybrid",
            "output_format": "yaml",
        }
        result = BatchScanRequest.model_validate(data)
        assert len(result.directories) == 2
        assert all(isinstance(d, Path) for d in result.directories)
        assert result.scan_mode == ScanMode.HYBRID
        assert result.output_format == OutputFormat.YAML

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_dict_with_path_objects(self, mock_is_dir, mock_exists):
        """Test validation with Path objects."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        
        data = {
            "directories": [Path("/test/dir1"), Path("/test/dir2")],
            "scan_mode": ScanMode.DEEP,
            "output_format": OutputFormat.CSV,
        }
        result = BatchScanRequest.model_validate(data)
        assert len(result.directories) == 2
        assert result.scan_mode == ScanMode.DEEP
        assert result.output_format == OutputFormat.CSV


class TestParameterPropagation:
    """Test that all Pydantic parameters are properly propagated."""

    def test_all_parameters_supported(self):
        """Test that model_validate supports all expected parameters."""
        data = {
            "video_file": {"path": "/test/video.mp4"},
        }
        
        # These should all work without raising exceptions
        ScanResult.model_validate(data, strict=False)
        ScanResult.model_validate(data, from_attributes=False)
        ScanResult.model_validate(data, context={"key": "value"})
        
        # Test combinations
        ScanResult.model_validate(
            data,
            strict=False,
            from_attributes=False,
            context={"key": "value"}
        )

    def test_strict_mode_with_string_enums(self):
        """Test that strict mode works with string enum conversion."""
        data = {
            "video_file": {"path": "/test/video.mp4"},
            "scan_mode": "deep",  # String enum should be converted before strict validation
        }
        
        # This should work because model_validator converts string to enum first
        result = ScanResult.model_validate(data, strict=True)
        assert result.scan_mode == ScanMode.DEEP

    def test_strict_mode_with_invalid_enum(self):
        """Test that strict mode properly rejects invalid enum values."""
        data = {
            "video_file": {"path": "/test/video.mp4"},
            "scan_mode": "invalid_mode",
        }
        
        # Should raise an error due to invalid enum value
        with pytest.raises(ValueError, match="is not a valid ScanMode"):
            ScanResult.model_validate(data, strict=True)

    def test_all_models_support_standard_parameters(self):
        """Test that all models support standard Pydantic parameters."""
        # Test data for each model type
        test_cases = [
            (ScanResult, {"video_file": {"path": "/test/video.mp4"}}),
            (ScanSummary, {
                "directory": "/test/dir",
                "total_files": 5,
                "processed_files": 5,
                "corrupt_files": 0,
                "healthy_files": 5,
                "scan_mode": "quick",
                "scan_time": 10.0
            }),
            (ScanProgress, {
                "total_files": 5,
                "processed_count": 2,
                "phase": "scanning",
                "scan_mode": "quick"
            }),
        ]
        
        for model_class, data in test_cases:
            # All these should work without exceptions
            model_class.model_validate(data, strict=False)
            model_class.model_validate(data, from_attributes=False)
            model_class.model_validate(data, context={"test": "value"})
            model_class.model_validate(
                data,
                strict=False,
                from_attributes=False,
                context={"test": "value"}
            )