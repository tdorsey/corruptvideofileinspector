"""
Video corruption detection logic for analyzing FFmpeg output.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CorruptionSeverity(Enum):
    """Severity levels for detected corruption."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CorruptionAnalysis:
    """Results of corruption analysis.

    Attributes:
        is_corrupt: Whether definitive corruption was detected
        needs_deep_scan: Whether file needs deeper analysis
        error_message: Human-readable error description
        confidence: Confidence level (0.0-1.0)
        detected_issues: List of specific issues found
        severity: Overall corruption severity level
        suggested_action: Recommended action based on analysis
    """

    is_corrupt: bool = False
    needs_deep_scan: bool = False
    error_message: str = ""
    confidence: float = 0.0
    detected_issues: list[str] = field(default_factory=list)
    severity: CorruptionSeverity = CorruptionSeverity.NONE
    suggested_action: str = ""

    def __post_init__(self: CorruptionAnalysis) -> None:
        """Set suggested action based on analysis results."""
        if not self.suggested_action:
            self.suggested_action = self._determine_suggested_action()

    def _determine_suggested_action(self: CorruptionAnalysis) -> str:
        """Determine suggested action based on corruption analysis."""
        if self.is_corrupt:
            if self.severity == CorruptionSeverity.CRITICAL:
                return "File is severely corrupted and should be deleted or " "restored from backup"
            if self.severity == CorruptionSeverity.HIGH:
                return "File has significant corruption and may be unusable"
            return "File has corruption but may still be playable"
        if self.needs_deep_scan:
            return "Run deep scan to determine if file is corrupt"
        return "File appears to be healthy"


class Inspector:
    """Inspector for analyzing video file health using FFmpegClient."""

    def __init__(self: Inspector, ffmpeg_client: Any) -> None:
        self.ffmpeg_client: Any = ffmpeg_client

    def inspect_quick(self: Inspector, video_file: Any) -> CorruptionAnalysis:
        """Perform quick inspection using FFmpegClient."""
        scan_result: Any = self.ffmpeg_client.inspect_quick(video_file)
        return self._analyze_scan_result(scan_result)

    def inspect_deep(self: Inspector, video_file: Any) -> CorruptionAnalysis:
        """Perform deep inspection using FFmpegClient."""
        scan_result: Any = self.ffmpeg_client.inspect_deep(video_file)
        return self._analyze_scan_result(scan_result)

    def _analyze_scan_result(self: Inspector, scan_result: Any) -> CorruptionAnalysis:
        """Convert ScanResult to CorruptionAnalysis."""
        severity: CorruptionSeverity = CorruptionSeverity.NONE
        if scan_result.is_corrupt:
            if scan_result.confidence > 0.8:
                severity = CorruptionSeverity.CRITICAL
            elif scan_result.confidence > 0.5:
                severity = CorruptionSeverity.HIGH
            elif scan_result.confidence > 0.2:
                severity = CorruptionSeverity.MEDIUM
            else:
                severity = CorruptionSeverity.LOW

        return CorruptionAnalysis(
            is_corrupt=scan_result.is_corrupt,
            needs_deep_scan=scan_result.needs_deep_scan,
            error_message=scan_result.error_message,
            confidence=scan_result.confidence,
            detected_issues=[],
            severity=severity,
            suggested_action="",
        )
