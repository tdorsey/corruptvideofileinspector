"""
Unit tests for corruption detector module.
"""
import pytest

from src.ffmpeg.corruption_detector import CorruptionAnalysis, CorruptionDetector

pytestmark = pytest.mark.unit


class TestCorruptionAnalysis:
    """Test CorruptionAnalysis dataclass"""
    
    def test_corruption_analysis_defaults(self):
        """Test default values for CorruptionAnalysis"""
        analysis = CorruptionAnalysis()
        assert not analysis.is_corrupt
        assert not analysis.needs_deep_scan
        assert analysis.error_message == ""
        assert analysis.confidence == 0.0
        assert analysis.detected_issues == []
    
    def test_corruption_analysis_with_issues(self):
        """Test CorruptionAnalysis with custom values"""
        analysis = CorruptionAnalysis(
            is_corrupt=True,
            needs_deep_scan=False,
            error_message="Test error",
            confidence=0.8,
            detected_issues=["invalid data found"]
        )
        assert analysis.is_corrupt
        assert not analysis.needs_deep_scan
        assert analysis.error_message == "Test error"
        assert analysis.confidence == 0.8
        assert analysis.detected_issues == ["invalid data found"]


class TestCorruptionDetector:
    """Test CorruptionDetector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.detector = CorruptionDetector()
    
    def test_detector_initialization(self):
        """Test corruption detector initializes correctly"""
        detector = CorruptionDetector()
        assert hasattr(detector, 'corruption_patterns')
        assert hasattr(detector, 'warning_patterns')
        assert hasattr(detector, 'critical_exit_codes')
        assert len(detector.corruption_patterns) > 0
        assert len(detector.warning_patterns) > 0
        assert len(detector.critical_exit_codes) > 0
    
    def test_analyze_clean_output(self):
        """Test analysis of clean FFmpeg output"""
        detector = CorruptionDetector()
        clean_output = "Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'video.mp4':"
        
        analysis = detector.analyze_ffmpeg_output(clean_output, exit_code=0, is_quick_scan=True)
        assert not analysis.is_corrupt
        assert not analysis.needs_deep_scan
        assert analysis.confidence == 0.0
    
    def test_analyze_corruption_patterns(self):
        """Test detection of corruption patterns"""
        detector = CorruptionDetector()
        corrupt_output = "invalid data found when processing video stream"
        
        analysis = detector.analyze_ffmpeg_output(corrupt_output, exit_code=1, is_quick_scan=True)
        assert analysis.is_corrupt
        assert "invalid data found" in analysis.error_message
        assert analysis.confidence > 0.0
    
    def test_analyze_warning_patterns(self):
        """Test detection of warning patterns"""
        detector = CorruptionDetector()
        warning_output = "non-monotonous dts in stream"
        
        analysis = detector.analyze_ffmpeg_output(warning_output, exit_code=0, is_quick_scan=True)
        assert not analysis.is_corrupt
        assert analysis.needs_deep_scan
    
    def test_analyze_critical_exit_codes(self):
        """Test detection of critical exit codes"""
        detector = CorruptionDetector()
        normal_output = "Processing video file"
        
        analysis = detector.analyze_ffmpeg_output(normal_output, exit_code=69, is_quick_scan=True)
        assert analysis.is_corrupt
        assert "Exit code 69" in analysis.error_message
    
    def test_find_pattern_matches(self):
        """Test pattern matching functionality"""
        detector = CorruptionDetector()
        text = "invalid data found and corrupted header detected"
        
        matches = detector._find_pattern_matches(detector.corruption_patterns, text)
        assert len(matches) >= 1
        assert any("invalid data found" in match for match in matches)
    
    def test_format_corruption_message(self):
        """Test corruption message formatting"""
        detector = CorruptionDetector()
        
        # Test quick scan message
        matches = ["invalid data found", "corrupted"]
        message = detector._format_corruption_message(matches, is_quick_scan=True)
        assert "invalid data found" in message
        assert "needs deep scan" in message
        
        # Test deep scan message
        message = detector._format_corruption_message(matches, is_quick_scan=False)
        assert "invalid data found" in message
        assert "needs deep scan" not in message
    
    def test_multiple_corruption_indicators(self):
        """Test handling of multiple corruption indicators"""
        detector = CorruptionDetector()
        output = "invalid data found, corrupt header, damaged frame detected"
        
        analysis = detector.analyze_ffmpeg_output(output, exit_code=1, is_quick_scan=False)
        assert analysis.is_corrupt
        assert analysis.confidence > 0.5
        assert len(analysis.detected_issues) > 1