#!/usr/bin/env python3
"""Test script to understand current model_validate behavior."""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.models.scanning import ScanResult, ScanSummary, ScanProgress, BatchScanRequest, ScanMode, OutputFormat, ScanPhase
from core.models.inspection import VideoFile

def test_current_behavior():
    """Test the current model_validate implementations."""
    
    print("Testing ScanResult.model_validate...")
    
    # Test with dict containing video_file as dict
    scan_data = {
        "video_file": {"path": "/test/video.mp4"},
        "is_corrupt": True,
        "error_message": "Test error",
        "scan_mode": "quick"
    }
    
    try:
        result = ScanResult.model_validate(scan_data)
        print(f"✓ ScanResult from dict: {result.video_file.path}")
    except Exception as e:
        print(f"✗ ScanResult from dict failed: {e}")
    
    # Test with dict containing filename (legacy)
    legacy_scan_data = {
        "filename": "/test/video.mp4",
        "is_corrupt": True,
        "error_message": "Test error"
    }
    
    try:
        result = ScanResult.model_validate(legacy_scan_data)
        print(f"✓ ScanResult from legacy dict: {result.video_file.path}")
    except Exception as e:
        print(f"✗ ScanResult from legacy dict failed: {e}")
    
    print("\nTesting ScanSummary.model_validate...")
    
    # Test with dict containing string paths and enum values
    summary_data = {
        "directory": "/test/dir",
        "total_files": 10,
        "processed_files": 10,
        "corrupt_files": 2,
        "healthy_files": 8,
        "scan_mode": "quick",  # string, should convert to enum
        "scan_time": 30.5
    }
    
    try:
        summary = ScanSummary.model_validate(summary_data)
        print(f"✓ ScanSummary from dict: {summary.directory}, mode={summary.scan_mode}")
    except Exception as e:
        print(f"✗ ScanSummary from dict failed: {e}")
    
    print("\nTesting ScanProgress.model_validate...")
    
    # Test with dict containing string enum values
    progress_data = {
        "current_file": "/test/file.mp4",
        "total_files": 5,
        "processed_count": 2,
        "phase": "scanning",  # string, should convert to enum
        "scan_mode": "deep"   # string, should convert to enum
    }
    
    try:
        progress = ScanProgress.model_validate(progress_data)
        print(f"✓ ScanProgress from dict: phase={progress.phase}, mode={progress.scan_mode}")
    except Exception as e:
        print(f"✗ ScanProgress from dict failed: {e}")
    
    print("\nTesting BatchScanRequest.model_validate...")
    
    # Test with dict containing string paths and enum values
    batch_data = {
        "directories": ["/test/dir1", "/test/dir2"],
        "scan_mode": "hybrid",
        "output_format": "json"
    }
    
    try:
        batch = BatchScanRequest.model_validate(batch_data)
        print(f"✓ BatchScanRequest from dict: {len(batch.directories)} dirs, mode={batch.scan_mode}")
    except Exception as e:
        print(f"✗ BatchScanRequest from dict failed: {e}")
    
    print("\nTesting parameter passing...")
    
    # Test with additional parameters
    try:
        result = ScanResult.model_validate(scan_data, strict=True)
        print(f"✓ ScanResult with strict=True works")
    except Exception as e:
        print(f"✗ ScanResult with strict=True failed: {e}")
    
    try:
        result = ScanResult.model_validate(scan_data, context={"test": "value"})
        print(f"✓ ScanResult with context works")
    except Exception as e:
        print(f"✗ ScanResult with context failed: {e}")

if __name__ == "__main__":
    test_current_behavior()