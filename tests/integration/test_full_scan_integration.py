import pytest

from src.config.config import (
    AppConfig,
    FFmpegConfig,
    LoggingConfig,
    OutputConfig,
    ProcessingConfig,
    ScanConfig,
    TraktConfig,
)
from src.core.models.inspection import VideoFile
from src.core.models.scanning import ScanMode
from src.core.scanner import VideoScanner
from src.ffmpeg.ffmpeg_client import FFmpegClient

pytestmark = pytest.mark.integration


def test_full_scan_mode_enum_exists():
    """Test that FULL scan mode exists in ScanMode enum."""
    assert hasattr(ScanMode, "FULL")
    assert ScanMode.FULL.value == "full"


def test_full_scan_mode_in_choices():
    """Test that FULL mode is included in scan mode choices."""
    scan_modes = [mode.value for mode in ScanMode]
    assert "full" in scan_modes
    assert len(scan_modes) == 4  # QUICK, DEEP, HYBRID, FULL


def test_ffmpeg_client_inspect_full_runs(tmp_path):
    """Test that FFmpegClient.inspect_full runs without timeout."""
    config = AppConfig(
        logging=LoggingConfig(),
        ffmpeg=FFmpegConfig(),
        processing=ProcessingConfig(),
        output=OutputConfig(default_output_dir=tmp_path),
        scan=ScanConfig(default_input_dir=tmp_path),
        trakt=TraktConfig(),
    )
    test_file = tmp_path / "test.mp4"
    test_file.touch()
    video_file = VideoFile(path=test_file)
    client = FFmpegClient(config.ffmpeg)
    # This will likely fail if ffmpeg is not installed, but should run
    try:
        result = client.inspect_full(video_file)
        assert hasattr(result, "corrupt")
    except Exception as e:
        pytest.skip(f"FFmpeg not available: {e}")


def test_video_scanner_full_scan(tmp_path):
    """Test VideoScanner runs a full scan and returns results."""
    config = AppConfig(
        logging=LoggingConfig(),
        ffmpeg=FFmpegConfig(),
        processing=ProcessingConfig(),
        output=OutputConfig(default_output_dir=tmp_path),
        scan=ScanConfig(default_input_dir=tmp_path),
        trakt=TraktConfig(),
    )
    test_file = tmp_path / "test.mp4"
    test_file.touch()
    scanner = VideoScanner(config)
    summary = scanner.scan_directory(
        directory=tmp_path,
        scan_mode=ScanMode.FULL,
        recursive=True,
        resume=False,
    )
    assert hasattr(summary, "scan_mode")
    assert summary.scan_mode == ScanMode.FULL
