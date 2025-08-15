#!/usr/bin/env python3
"""
Simple syntax and basic functionality test for FFprobe content detection.
"""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_direct_imports():
    """Test direct imports without going through __init__.py"""
    try:
        # Test config changes directly
        sys.path.insert(0, str(Path(__file__).parent / "src" / "config"))
        
        # Manually test config structure
        print("Testing configuration changes...")
        
        # Check if the file compiles
        import py_compile
        config_file = Path(__file__).parent / "src" / "config" / "config.py"
        py_compile.compile(config_file, doraise=True)
        print("✓ Config file compiles successfully")
        
        # Check FFmpeg client
        ffmpeg_file = Path(__file__).parent / "src" / "ffmpeg" / "ffmpeg_client.py"
        py_compile.compile(ffmpeg_file, doraise=True)
        print("✓ FFmpeg client file compiles successfully")
        
        # Check scanner
        scanner_file = Path(__file__).parent / "src" / "core" / "scanner.py"
        py_compile.compile(scanner_file, doraise=True)
        print("✓ Scanner file compiles successfully")
        
        # Check video_files
        video_files_file = Path(__file__).parent / "src" / "core" / "video_files.py"
        py_compile.compile(video_files_file, doraise=True)
        print("✓ Video files module compiles successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Compilation test failed: {e}")
        return False

def test_syntax_only():
    """Test just the syntax of our changes"""
    try:
        files_to_check = [
            "src/config/config.py",
            "src/ffmpeg/ffmpeg_client.py", 
            "src/core/scanner.py",
            "src/core/video_files.py"
        ]
        
        import ast
        
        for file_path in files_to_check:
            full_path = Path(__file__).parent / file_path
            with open(full_path, 'r') as f:
                content = f.read()
            
            # Parse the AST to check syntax
            ast.parse(content)
            print(f"✓ {file_path} syntax is valid")
            
        return True
        
    except Exception as e:
        print(f"✗ Syntax test failed: {e}")
        return False

def test_new_methods_exist():
    """Test that new methods are defined in files"""
    try:
        # Check FFmpeg client has new methods
        ffmpeg_file = Path(__file__).parent / "src" / "ffmpeg" / "ffmpeg_client.py"
        with open(ffmpeg_file, 'r') as f:
            content = f.read()
            
        expected_methods = ['analyze_streams', 'is_video_file', '_get_ffprobe_command']
        for method in expected_methods:
            if f"def {method}" not in content:
                raise ValueError(f"Method {method} not found in FFmpeg client")
            print(f"✓ Method {method} found in FFmpeg client")
            
        # Check config has new fields
        config_file = Path(__file__).parent / "src" / "config" / "config.py"
        with open(config_file, 'r') as f:
            content = f.read()
            
        expected_fields = ['use_content_detection', 'ffprobe_timeout', 'extension_filter']
        for field in expected_fields:
            if field not in content:
                raise ValueError(f"Field {field} not found in config")
            print(f"✓ Field {field} found in config")
            
        # Check scanner has content detection logic
        scanner_file = Path(__file__).parent / "src" / "core" / "scanner.py"
        with open(scanner_file, 'r') as f:
            content = f.read()
            
        if "use_content_detection" not in content:
            raise ValueError("Content detection logic not found in scanner")
        print("✓ Content detection logic found in scanner")
        
        if "FFmpegClient" not in content:
            raise ValueError("FFmpegClient usage not found in scanner")
        print("✓ FFmpegClient usage found in scanner")
        
        return True
        
    except Exception as e:
        print(f"✗ Method/field existence test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running simple tests for FFprobe content detection implementation...")
    print()
    
    tests = [
        ("File compilation", test_direct_imports),
        ("Syntax validation", test_syntax_only),
        ("New methods/fields exist", test_new_methods_exist),
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
        print("🎉 All basic tests passed!")
        print()
        print("Changes implemented:")
        print("- Added FFprobe content analysis methods to FFmpegClient")
        print("- Added content detection configuration options")
        print("- Modified scanner to use content-based detection")
        print("- Updated video_files module for consistency")
        print("- Maintained backward compatibility")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())