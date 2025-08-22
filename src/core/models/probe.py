"""
Models for FFprobe analysis results and probe-related data structures.
"""

import time
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class StreamType(Enum):
    """Type of media stream detected by FFprobe."""

    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"
    UNKNOWN = "unknown"


class StreamInfo(BaseModel):
    """Information about a media stream from FFprobe analysis."""

    index: int
    codec_name: str | None = None
    codec_type: StreamType = StreamType.UNKNOWN
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    bit_rate: int | None = None
    frame_rate: str | None = None
    pixel_format: str | None = None

    @classmethod
    def from_ffprobe_stream(cls, stream_data: dict[str, Any]) -> "StreamInfo":
        """Create StreamInfo from FFprobe stream data."""
        codec_type = StreamType.UNKNOWN
        if "codec_type" in stream_data:
            try:
                codec_type = StreamType(stream_data["codec_type"])
            except ValueError:
                codec_type = StreamType.UNKNOWN

        return cls(
            index=stream_data.get("index", 0),
            codec_name=stream_data.get("codec_name"),
            codec_type=codec_type,
            width=stream_data.get("width"),
            height=stream_data.get("height"),
            duration=float(stream_data["duration"]) if stream_data.get("duration") else None,
            bit_rate=int(stream_data["bit_rate"]) if stream_data.get("bit_rate") else None,
            frame_rate=stream_data.get("avg_frame_rate"),
            pixel_format=stream_data.get("pix_fmt"),
        )


class FormatInfo(BaseModel):
    """Container format information from FFprobe analysis."""

    filename: str
    format_name: str | None = None
    format_long_name: str | None = None
    duration: float | None = None
    size: int | None = None
    bit_rate: int | None = None
    probe_score: int | None = None

    @classmethod
    def from_ffprobe_format(cls, format_data: dict[str, Any]) -> "FormatInfo":
        """Create FormatInfo from FFprobe format data."""
        return cls(
            filename=format_data.get("filename", ""),
            format_name=format_data.get("format_name"),
            format_long_name=format_data.get("format_long_name"),
            duration=float(format_data["duration"]) if format_data.get("duration") else None,
            size=int(format_data["size"]) if format_data.get("size") else None,
            bit_rate=int(format_data["bit_rate"]) if format_data.get("bit_rate") else None,
            probe_score=format_data.get("probe_score"),
        )


class ProbeResult(BaseModel):
    """Results of FFprobe analysis for a video file."""

    file_path: Path
    timestamp: float = Field(default_factory=time.time)
    success: bool = False
    streams: list[StreamInfo] = Field(default_factory=list)
    format_info: FormatInfo | None = None
    duration: float | None = None
    file_size: int = 0
    error_message: str = ""
    raw_output: str | None = None

    @property
    def has_video_streams(self) -> bool:
        """Check if file has video streams."""
        return any(stream.codec_type == StreamType.VIDEO for stream in self.streams)

    @property
    def has_audio_streams(self) -> bool:
        """Check if file has audio streams."""
        return any(stream.codec_type == StreamType.AUDIO for stream in self.streams)

    @property
    def video_streams(self) -> list[StreamInfo]:
        """Get only video streams."""
        return [stream for stream in self.streams if stream.codec_type == StreamType.VIDEO]

    @property
    def audio_streams(self) -> list[StreamInfo]:
        """Get only audio streams."""
        return [stream for stream in self.streams if stream.codec_type == StreamType.AUDIO]

    @property
    def is_valid_video_file(self) -> bool:
        """Check if this is a valid video file suitable for corruption scanning."""
        return self.success and self.has_video_streams and self.format_info is not None

    @property
    def age_seconds(self) -> float:
        """Get age of probe result in seconds."""
        return time.time() - self.timestamp

    @property
    def age_hours(self) -> float:
        """Get age of probe result in hours."""
        return self.age_seconds / 3600

    def is_expired(self, max_age_hours: float = 24.0) -> bool:
        """Check if probe result is expired based on age."""
        return self.age_hours > max_age_hours

    def get_summary(self) -> str:
        """Get human-readable summary of probe result."""
        if not self.success:
            return f"Probe failed: {self.error_message or 'Unknown error'}"

        if not self.is_valid_video_file:
            return "Not a valid video file"

        video_count = len(self.video_streams)
        audio_count = len(self.audio_streams)
        duration_str = f"{self.duration:.1f}s" if self.duration else "unknown duration"

        return f"{video_count} video, {audio_count} audio streams, {duration_str}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": str(self.file_path),
            "timestamp": self.timestamp,
            "success": self.success,
            "streams": [stream.model_dump() for stream in self.streams],
            "format_info": self.format_info.model_dump() if self.format_info else None,
            "duration": self.duration,
            "file_size": self.file_size,
            "error_message": self.error_message,
            "has_video_streams": self.has_video_streams,
            "has_audio_streams": self.has_audio_streams,
            "is_valid_video_file": self.is_valid_video_file,
            "age_hours": self.age_hours,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProbeResult":
        """Create ProbeResult from dictionary."""
        streams = []
        if data.get("streams"):
            streams = [StreamInfo.model_validate(stream) for stream in data["streams"]]

        format_info = None
        if data.get("format_info"):
            format_info = FormatInfo.model_validate(data["format_info"])

        return cls(
            file_path=Path(data["file_path"]),
            timestamp=data.get("timestamp", time.time()),
            success=data.get("success", False),
            streams=streams,
            format_info=format_info,
            duration=data.get("duration"),
            file_size=data.get("file_size", 0),
            error_message=data.get("error_message"),
            raw_output=data.get("raw_output"),
        )


class ScanPrerequisites(BaseModel):
    """Helper class to check scan prerequisites based on probe results."""

    require_video_streams: bool = True
    require_format_info: bool = True

    def can_scan(self, probe_result: ProbeResult | None) -> bool:
        """Check if file can be scanned based on probe result."""
        if probe_result is None:
            return False

        if not probe_result.success:
            return False

        if self.require_video_streams and not probe_result.has_video_streams:
            return False

        return not (self.require_format_info and probe_result.format_info is None)

    def get_rejection_reason(self, probe_result: ProbeResult | None) -> str:
        """Get reason why file cannot be scanned."""
        if probe_result is None:
            return "No probe result available"

        if not probe_result.success:
            return f"Probe failed: {probe_result.error_message or 'Unknown error'}"

        if self.require_video_streams and not probe_result.has_video_streams:
            return "No video streams detected"

        if self.require_format_info and probe_result.format_info is None:
            return "No format information available"

        return "Unknown rejection reason"
