"""
Video corruption detection logic for analyzing FFmpeg output.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Pattern

logger = logging.getLogger(__name__)


@dataclass
class CorruptionAnalysis:
    """Results of corruption analysis."""

    is_corrupt: bool = False
    needs_deep_scan: bool = False
    error_message: str = ""
    confidence: float = 0.0  # 0.0 to 1.0
    detected_issues: List[str] = None

    def __post_init__(self):
        if self.detected_issues is None:
            self.detected_issues = []


class CorruptionDetector:
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

    def _compile_patterns(self, patterns: List[str]) -> List[Pattern]:
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
        corruption_matches = self._find_pattern_matches(
            self.corruption_patterns, stderr
        )
        if corruption_matches:
            analysis.is_corrupt = True
            analysis.confidence = 0.9
            analysis.detected_issues.extend(corruption_matches)
            analysis.error_message = self._format_corruption_message(
                corruption_matches, is_quick_scan
            )
            logger.debug(f"Corruption detected: {corruption_matches}")
            return analysis

        # Check for warning patterns
        warning_matches = self._find_pattern_matches(self.warning_patterns, stderr)
        if warning_matches:
            analysis.detected_issues.extend(warning_matches)

            if is_quick_scan:
                analysis.needs_deep_scan = True
                analysis.confidence = 0.6
                analysis.error_message = "Potential issues detected - needs deep scan"
            else:
                # In deep scan, warnings might indicate minor issues but not corruption
                analysis.confidence = 0.3
                analysis.error_message = (
                    f"Warnings detected: {', '.join(warning_matches[:3])}"
                )

            logger.debug(f"Warning patterns detected: {warning_matches}")

        # Analyze exit code
        if exit_code in self.critical_exit_codes:
            if is_quick_scan and not analysis.is_corrupt:
                analysis.needs_deep_scan = True
                analysis.confidence = max(analysis.confidence, 0.5)
                analysis.error_message = (
                    f"FFmpeg error (code {exit_code}) - needs verification"
                )
            else:
                # In deep scan, critical exit codes are more concerning
                analysis.is_corrupt = True
                analysis.confidence = 0.7
                analysis.error_message = f"Critical FFmpeg error (code {exit_code})"

            analysis.detected_issues.append(f"exit_code_{exit_code}")

        # Count suspicious keywords for additional confidence scoring
        suspicious_count = sum(
            1 for keyword in self.suspicious_keywords if keyword in stderr_lower
        )

        if suspicious_count > 5:
            if is_quick_scan and not analysis.is_corrupt:
                analysis.needs_deep_scan = True
                analysis.confidence = max(analysis.confidence, 0.4)
                if not analysis.error_message:
                    analysis.error_message = (
                        "Multiple suspicious indicators - needs deep scan"
                    )
            else:
                analysis.confidence = max(analysis.confidence, 0.3)

        # Special handling for specific error patterns
        analysis = self._analyze_specific_errors(stderr, analysis, is_quick_scan)

        # Default handling for unrecognized errors
        if exit_code != 0 and not analysis.is_corrupt and not analysis.needs_deep_scan:
            if is_quick_scan:
                analysis.needs_deep_scan = True
                analysis.confidence = 0.3
                analysis.error_message = (
                    f"FFmpeg error (code {exit_code}) - investigation needed"
                )
            else:
                analysis.error_message = (
                    f"FFmpeg error (code {exit_code}): {stderr[:200]}"
                )

        logger.debug(
            f"Analysis complete: corrupt={analysis.is_corrupt}, "
            f"deep_scan={analysis.needs_deep_scan}, confidence={analysis.confidence}"
        )

        return analysis

    def _find_pattern_matches(self, patterns: List[Pattern], text: str) -> List[str]:
        """Find all pattern matches in text."""
        matches = []
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                matches.append(match.group(0))
        return matches

    def _format_corruption_message(
        self, matches: List[str], is_quick_scan: bool
    ) -> str:
        """Format corruption message based on detected issues."""
        scan_type = "quick scan" if is_quick_scan else "deep scan"

        if len(matches) == 1:
            return f"Corruption detected ({scan_type}): {matches[0]}"
        elif len(matches) <= 3:
            return f"Multiple corruption indicators ({scan_type}): {', '.join(matches)}"
        else:
            return (
                f"Severe corruption detected ({scan_type}): {len(matches)} issues found"
            )

    def _analyze_specific_errors(
        self, stderr: str, analysis: CorruptionAnalysis, is_quick_scan: bool
    ) -> CorruptionAnalysis:
        """Analyze specific error patterns for more nuanced detection."""
        stderr_lower = stderr.lower()

        # Timeout-related patterns
        if "timeout" in stderr_lower or "timed out" in stderr_lower:
            if is_quick_scan:
                analysis.needs_deep_scan = True
                analysis.confidence = max(analysis.confidence, 0.6)
                analysis.error_message = "Processing timeout - may indicate corruption"
            else:
                analysis.is_corrupt = True
                analysis.confidence = 0.8
                analysis.error_message = "Deep scan timeout - likely severe corruption"
            analysis.detected_issues.append("timeout")

        # Container format specific issues
        if "moov" in stderr_lower and (
            "not found" in stderr_lower or "missing" in stderr_lower
        ):
            analysis.is_corrupt = True
            analysis.confidence = 0.95
            analysis.error_message = "MP4 container corruption: missing moov atom"
            analysis.detected_issues.append("missing_moov_atom")

        # Network/streaming related issues that might not be corruption
        streaming_indicators = ["connection", "network", "http", "ssl", "certificate"]
        if any(indicator in stderr_lower for indicator in streaming_indicators):
            # These might be network issues, not file corruption
            analysis.confidence = max(0.1, analysis.confidence - 0.3)
            if "network" not in analysis.error_message.lower():
                analysis.error_message += " (possible network issue)"

        # Audio/video sync issues
        if "pts" in stderr_lower and "dts" in stderr_lower:
            sync_patterns = ["discontinuity", "non-monotonous", "out of order"]
            if any(pattern in stderr_lower for pattern in sync_patterns):
                if is_quick_scan:
                    analysis.needs_deep_scan = True
                    analysis.confidence = max(analysis.confidence, 0.4)
                    analysis.error_message = (
                        "Timestamp issues detected - needs verification"
                    )
                else:
                    # In deep scan, timestamp issues might not mean corruption
                    analysis.confidence = min(analysis.confidence, 0.4)
                analysis.detected_issues.append("timestamp_issues")

        return analysis

    def get_corruption_confidence(self, analysis: CorruptionAnalysis) -> str:
        """Get human-readable confidence level."""
        if analysis.confidence >= 0.9:
            return "Very High"
        elif analysis.confidence >= 0.7:
            return "High"
        elif analysis.confidence >= 0.5:
            return "Medium"
        elif analysis.confidence >= 0.3:
            return "Low"
        else:
            return "Very Low"

    def should_retry_with_different_settings(
        self, analysis: CorruptionAnalysis
    ) -> bool:
        """Determine if scan should be retried with different FFmpeg settings."""
        # Retry if we have low confidence and specific indicators
        if analysis.confidence < 0.5 and any(
            "timeout" in issue for issue in analysis.detected_issues
        ):
            return True

        return False

    def get_recommended_action(
        self, analysis: CorruptionAnalysis, is_quick_scan: bool
    ) -> str:
        """Get recommended action based on analysis."""
        if analysis.is_corrupt and analysis.confidence >= 0.8:
            return "File is likely corrupt - consider removing or re-downloading"
        elif analysis.is_corrupt and analysis.confidence >= 0.5:
            return "File may be corrupt - manual review recommended"
        elif analysis.needs_deep_scan and is_quick_scan:
            return "File needs deep scan for definitive analysis"
        elif analysis.confidence < 0.3:
            return "File appears healthy but had minor processing issues"
        else:
            return "File appears healthy"
