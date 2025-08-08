"""
Video corruption detection logic for analyzing FFmpeg output.
"""

import logging
import re
from dataclasses import dataclass
from re import Pattern

logger = logging.getLogger(__name__)


@dataclass
class CorruptionAnalysis:
    """Results of corruption analysis."""

    is_corrupt: bool = False
    needs_deep_scan: bool = False
    error_message: str = ""
    confidence: float = 0.0  # 0.0 to 1.0
    detected_issues: list[str] | None = None

    def __post_init__(self):
        if self.detected_issues is None:
            self.detected_issues = []


class CorruptionDetector:
    def _find_pattern_matches(self, patterns: list[Pattern], text: str) -> list[str]:
        """Find all pattern matches in text."""
        matches = []
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                matches.append(match.group(0))
        return matches

    def _format_corruption_message(self, matches: list[str], is_quick_scan: bool) -> str:
        """Format corruption message for detected patterns."""
        base = f"Corruption detected: {', '.join(matches[:3])}"
        if is_quick_scan:
            return base + " - needs deep scan"
        return base

    """Analyzes FFmpeg output to detect video corruption."""

    def __init__(self):
        """Initialize the corruption detector."""
        # Definitive corruption indicators (high confidence)
        self.corruption_patterns = self._compile_patterns(
            [
                r"invalid data found",
                r"error while decoding",
                r"corrupt",
                r"damaged",
                r"incomplete",
                r"truncated",
                r"malformed",
                r"moov atom not found",
                r"invalid nal unit size",
                r"decode_slice_header error",
                r"concealing errors",
                r"missing reference picture",
                r"invalid frame size",
                r"header damaged",
                r"no frame!",
                r"decode error",
                r"stream not found",
                r"invalid.*header",
                r"unexpected end of file",
                r"premature end",
            ]
        )

        # Warning indicators that suggest need for deeper analysis
        self.warning_patterns = self._compile_patterns(
            [
                r"non-monotonous dts",
                r"pts discontinuity",
                r"frame rate very high",
                r"dts out of order",
                r"b-frame after eos",
                r"picture size \d+x\d+ is invalid",
                r"multiple decode errors",
                r"skipping frame",
                r"ac-tex damaged",
                r"slice header damaged",
                r"mb damaged",
                r"warning.*error concealment",
            ]
        )

        # Critical error codes that indicate corruption
        self.critical_exit_codes = {
            1,  # Generic error
            69,  # Data format error
            74,  # IO error
        }

        # Keywords that increase suspicion
        self.suspicious_keywords = {
            "error",
            "warning",
            "failed",
            "invalid",
            "corrupt",
            "damaged",
            "broken",
            "bad",
            "missing",
            "unexpected",
        }

        logger.debug("CorruptionDetector initialized")

    def _compile_patterns(self, patterns: list[str]) -> list[Pattern]:
        """Compile regex patterns for efficient matching."""
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    def analyze_ffmpeg_output(
        self, stderr: str, exit_code: int, is_quick_scan: bool = False
    ) -> CorruptionAnalysis:
        """
        Analyze FFmpeg output to determine corruption status.

        Args:
            stderr: FFmpeg stderr output
            exit_code: FFmpeg exit code
            is_quick_scan: Whether this was a quick scan

        Returns:
            CorruptionAnalysis: Analysis results
        """
        analysis = CorruptionAnalysis()
        stderr_lower = stderr.lower()

        logger.debug(f"Analyzing FFmpeg output (exit_code: {exit_code})")

        # If FFmpeg succeeded, likely no corruption
        if exit_code == 0 and not stderr.strip():
            analysis.confidence = 0.9
            return analysis

        # Check for definitive corruption patterns
        corruption_matches = self._find_pattern_matches(self.corruption_patterns, stderr)
        if corruption_matches:
            analysis.is_corrupt = True
            analysis.confidence = 0.9
            if analysis.detected_issues is None:
                analysis.detected_issues = []
            analysis.detected_issues.extend(corruption_matches)
            analysis.error_message = self._format_corruption_message(
                corruption_matches, is_quick_scan
            )
            logger.debug(f"Corruption detected: {corruption_matches}")
            return analysis

        # Check for warning patterns
        warning_matches = self._find_pattern_matches(self.warning_patterns, stderr)
        if warning_matches:
            if analysis.detected_issues is None:
                analysis.detected_issues = []
            analysis.detected_issues.extend(warning_matches)

            if is_quick_scan:
                analysis.needs_deep_scan = True
                analysis.confidence = 0.6
                analysis.error_message = "Potential issues detected - needs deep scan"
            else:
                # In deep scan, warnings might indicate minor issues
                analysis.confidence = 0.3
                analysis.error_message = f"Warnings detected: " f"{', '.join(warning_matches[:3])}"

            logger.debug(f"Warning patterns detected: {warning_matches}")

        # Analyze exit code
        if exit_code in self.critical_exit_codes:
            if is_quick_scan and not analysis.is_corrupt:
                analysis.needs_deep_scan = True
                analysis.confidence = max(analysis.confidence, 0.5)
                analysis.error_message = f"FFmpeg error (code {exit_code}) - " f"needs verification"
            else:
                # In deep scan, critical exit codes are more concerning
                analysis.is_corrupt = True
                analysis.confidence = 0.7
                analysis.error_message = f"Critical FFmpeg error (code {exit_code})"

            if analysis.detected_issues is None:
                analysis.detected_issues = []
            analysis.detected_issues.append(f"exit_code_{exit_code}")

        # Break long lines
        if sum(1 for keyword in self.suspicious_keywords if keyword in stderr_lower) > 5:
            if is_quick_scan and not analysis.is_corrupt:
                analysis.needs_deep_scan = True
                analysis.confidence = max(analysis.confidence, 0.4)
                if not analysis.error_message:
                    analysis.error_message = "Multiple suspicious indicators - " "needs deep scan"
            else:
                analysis.confidence = max(analysis.confidence, 0.3)

        if exit_code != 0 and not analysis.is_corrupt and not analysis.needs_deep_scan:
            if is_quick_scan:
                analysis.needs_deep_scan = True
                analysis.confidence = 0.3
                analysis.error_message = (
                    f"FFmpeg error (code {exit_code}) - " f"investigation needed"
                )
            else:
                analysis.error_message = f"FFmpeg error (code {exit_code}): " f"{stderr[:200]}"

        # Remove unreachable/duplicate error message assignments
        # Remove unused inner function and comments
        return analysis
