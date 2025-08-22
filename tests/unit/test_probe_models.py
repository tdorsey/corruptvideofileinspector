"""
Unit tests for probe-related models and functionality.
"""

import tempfile
import time
from pathlib import Path

from src.core.models.probe import (
    FormatInfo,
    ProbeResult,
    ScanPrerequisites,
    StreamInfo,
    StreamType,
)


class TestProbeResult:
    """Test ProbeResult model functionality."""

    def test_probe_result_creation(self):
        """Test basic ProbeResult creation."""
        file_path = Path("/test/video.mp4")
        probe_result = ProbeResult(
            file_path=file_path,
            success=True,
            file_size=1024,
        )

        assert probe_result.file_path == file_path
        assert probe_result.success is True
        assert probe_result.file_size == 1024
        assert probe_result.streams == []
        assert probe_result.format_info is None

    def test_probe_result_with_streams(self):
        """Test ProbeResult with stream information."""
        video_stream = StreamInfo(
            index=0,
            codec_name="h264",
            codec_type=StreamType.VIDEO,
            width=1920,
            height=1080,
            duration=120.5,
        )

        audio_stream = StreamInfo(
            index=1,
            codec_name="aac",
            codec_type=StreamType.AUDIO,
            duration=120.5,
        )

        probe_result = ProbeResult(
            file_path=Path("/test/video.mp4"),
            success=True,
            streams=[video_stream, audio_stream],
            duration=120.5,
        )

        assert probe_result.has_video_streams is True
        assert probe_result.has_audio_streams is True
        assert len(probe_result.video_streams) == 1
        assert len(probe_result.audio_streams) == 1
        assert probe_result.is_valid_video_file is False  # No format_info

    def test_probe_result_valid_video_file(self):
        """Test ProbeResult for valid video file detection."""
        video_stream = StreamInfo(
            index=0,
            codec_type=StreamType.VIDEO,
            codec_name="h264",
        )

        format_info = FormatInfo(
            filename="test.mp4",
            format_name="mov,mp4,m4a,3gp,3g2,mj2",
            duration=120.5,
        )

        probe_result = ProbeResult(
            file_path=Path("/test/video.mp4"),
            success=True,
            streams=[video_stream],
            format_info=format_info,
        )

        assert probe_result.is_valid_video_file is True

    def test_probe_result_age_calculation(self):
        """Test probe result age calculations."""
        # Create result with specific timestamp
        past_time = time.time() - 3600  # 1 hour ago
        probe_result = ProbeResult(
            file_path=Path("/test/video.mp4"),
            timestamp=past_time,
        )

        assert probe_result.age_seconds >= 3600
        assert probe_result.age_hours >= 1.0
        assert probe_result.is_expired(max_age_hours=0.5) is True
        assert probe_result.is_expired(max_age_hours=2.0) is False

    def test_probe_result_summary(self):
        """Test probe result summary generation."""
        # Failed probe
        failed_result = ProbeResult(
            file_path=Path("/test/video.mp4"),
            success=False,
            error_message="File not found",
        )
        assert "Probe failed" in failed_result.get_summary()

        # Valid video file
        video_stream = StreamInfo(index=0, codec_type=StreamType.VIDEO)
        audio_stream = StreamInfo(index=1, codec_type=StreamType.AUDIO)
        format_info = FormatInfo(filename="test.mp4")

        valid_result = ProbeResult(
            file_path=Path("/test/video.mp4"),
            success=True,
            streams=[video_stream, audio_stream],
            format_info=format_info,
            duration=120.5,
        )

        summary = valid_result.get_summary()
        assert "1 video" in summary
        assert "1 audio" in summary
        assert "120.5s" in summary


class TestStreamInfo:
    """Test StreamInfo model functionality."""

    def test_stream_info_from_ffprobe_data(self):
        """Test creating StreamInfo from FFprobe data."""
        ffprobe_data = {
            "index": 0,
            "codec_name": "h264",
            "codec_type": "video",
            "width": 1920,
            "height": 1080,
            "duration": "120.500000",
            "bit_rate": "2000000",
            "avg_frame_rate": "25/1",
            "pix_fmt": "yuv420p",
        }

        stream = StreamInfo.from_ffprobe_stream(ffprobe_data)

        assert stream.index == 0
        assert stream.codec_name == "h264"
        assert stream.codec_type == StreamType.VIDEO
        assert stream.width == 1920
        assert stream.height == 1080
        assert stream.duration == 120.5
        assert stream.bit_rate == 2000000
        assert stream.frame_rate == "25/1"
        assert stream.pixel_format == "yuv420p"


class TestFormatInfo:
    """Test FormatInfo model functionality."""

    def test_format_info_from_ffprobe_data(self):
        """Test creating FormatInfo from FFprobe data."""
        ffprobe_data = {
            "filename": "/test/video.mp4",
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "format_long_name": "QuickTime / MOV",
            "duration": "120.500000",
            "size": "50000000",
            "bit_rate": "3318784",
            "probe_score": 100,
        }

        format_info = FormatInfo.from_ffprobe_format(ffprobe_data)

        assert format_info.filename == "/test/video.mp4"
        assert format_info.format_name == "mov,mp4,m4a,3gp,3g2,mj2"
        assert format_info.format_long_name == "QuickTime / MOV"
        assert format_info.duration == 120.5
        assert format_info.size == 50000000
        assert format_info.bit_rate == 3318784
        assert format_info.probe_score == 100


class TestScanPrerequisites:
    """Test ScanPrerequisites functionality."""

    def test_can_scan_with_valid_result(self):
        """Test scan prerequisites with valid probe result."""
        video_stream = StreamInfo(index=0, codec_type=StreamType.VIDEO)
        format_info = FormatInfo(filename="test.mp4")

        probe_result = ProbeResult(
            file_path=Path("/test/video.mp4"),
            success=True,
            streams=[video_stream],
            format_info=format_info,
        )

        prerequisites = ScanPrerequisites()
        assert prerequisites.can_scan(probe_result) is True

    def test_can_scan_with_failed_probe(self):
        """Test scan prerequisites with failed probe."""
        probe_result = ProbeResult(
            file_path=Path("/test/video.mp4"),
            success=False,
            error_message="Probe failed",
        )

        prerequisites = ScanPrerequisites()
        assert prerequisites.can_scan(probe_result) is False

        reason = prerequisites.get_rejection_reason(probe_result)
        assert "Probe failed" in reason

    def test_can_scan_without_video_streams(self):
        """Test scan prerequisites without video streams."""
        audio_stream = StreamInfo(index=0, codec_type=StreamType.AUDIO)
        format_info = FormatInfo(filename="test.mp3")

        probe_result = ProbeResult(
            file_path=Path("/test/audio.mp3"),
            success=True,
            streams=[audio_stream],
            format_info=format_info,
        )

        prerequisites = ScanPrerequisites(require_video_streams=True)
        assert prerequisites.can_scan(probe_result) is False

        reason = prerequisites.get_rejection_reason(probe_result)
        assert "No video streams" in reason

