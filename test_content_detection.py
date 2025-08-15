#!/usr/bin/env python3
"""
Manual test for FFprobe content detection functionality.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_basic_imports():
    """Test that all new modules can be imported"""
    try:
        from src.config.config import ScanConfig
        print("✓ ScanConfig import successful")
        
        # Test new configuration fields
        config = ScanConfig(
            default_input_dir=Path("/tmp"),
            use_content_detection=True,
            ffprobe_timeout=30,
            extension_filter=[".mp4"]
        )
        print(f"✓ ScanConfig creation successful: use_content_detection={config.use_content_detection}")
        
    except Exception as e:
        print(f"✗ ScanConfig test failed: {e}")
        return False
        
    try:
        from src.ffmpeg.ffmpeg_client import FFmpegClient
        print("✓ FFmpegClient import successful")
        
        # Test new methods exist
        assert hasattr(FFmpegClient, 'analyze_streams')
        assert hasattr(FFmpegClient, 'is_video_file')
        assert hasattr(FFmpegClient, '_get_ffprobe_command')
        print("✓ FFmpegClient new methods exist")
        
    except Exception as e:
        print(f"✗ FFmpegClient test failed: {e}")
        return False
        
    return True

def test_config_fields():
    """Test that configuration includes new fields"""
    try:
        from src.config.config import ScanConfig
        
        # Test default values
        config = ScanConfig(default_input_dir=Path("/tmp"))
        assert config.use_content_detection == True, "Default use_content_detection should be True"
        assert config.ffprobe_timeout == 30, "Default ffprobe_timeout should be 30"
        assert config.extension_filter == [], "Default extension_filter should be empty list"
        
        print("✓ Configuration defaults are correct")
        
        # Test custom values
        config = ScanConfig(
            default_input_dir=Path("/tmp"),
            use_content_detection=False,
            ffprobe_timeout=60,
            extension_filter=[".mp4", ".mkv"]
        )
        assert config.use_content_detection == False
        assert config.ffprobe_timeout == 60
        assert config.extension_filter == [".mp4", ".mkv"]
        
        print("✓ Configuration custom values work")
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False
        
    return True

def test_ffmpeg_client_methods():
    """Test FFmpeg client method signatures"""
    try:
        import json
        from unittest.mock import Mock, patch
        from src.ffmpeg.ffmpeg_client import FFmpegClient
        from src.config.config import FFmpegConfig
        
        config = FFmpegConfig(
            command=Path("/usr/bin/ffmpeg"),
            quick_timeout=30,
            deep_timeout=900
        )
        
        with patch.object(FFmpegClient, '_validate_ffmpeg_command', return_value=True):
            client = FFmpegClient(config)
            
            # Test _get_ffprobe_command
            client._ffmpeg_path = "/usr/bin/ffmpeg"
            ffprobe_cmd = client._get_ffprobe_command()
            assert ffprobe_cmd == "/usr/bin/ffprobe"
            print("✓ _get_ffprobe_command works")
            
            client._ffmpeg_path = None
            ffprobe_cmd = client._get_ffprobe_command()
            assert ffprobe_cmd == "ffprobe"
            print("✓ _get_ffprobe_command fallback works")
            
    except Exception as e:
        print(f"✗ FFmpeg client methods test failed: {e}")
        return False
        
    return True

def main():
    """Run all tests"""
    print("Running manual tests for FFprobe content detection...")
    print()
    
    tests = [
        ("Basic imports", test_basic_imports),
        ("Configuration fields", test_config_fields),
        ("FFmpeg client methods", test_ffmpeg_client_methods),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())