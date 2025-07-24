#!/usr/bin/env python3
"""
Simple Docker entrypoint for corrupt-video-inspector.
This script provides a basic interface for testing the Docker setup.
"""

import os
import sys
from pathlib import Path

def main():
    """Main entry point for Docker container."""
    print("🐳 Corrupt Video Inspector - Docker Edition")
    print("=" * 50)
    
    # Check environment
    print(f"Running as user: {os.getuid()}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    
    # Check for config file
    config_file = Path("/app/config/config.yaml")
    if config_file.exists():
        print(f"✅ Config file found: {config_file}")
        print(f"Config file size: {config_file.stat().st_size} bytes")
    else:
        print("❌ Config file not found")
    
    # Check directories
    print(f"Videos directory: {Path('/app/videos').exists()}")
    print(f"Output directory: {Path('/app/output').exists()}")
    
    # Check FFmpeg
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg available: {version_line}")
        else:
            print("❌ FFmpeg not working")
    except Exception as e:
        print(f"❌ FFmpeg check failed: {e}")
    
    # Show help or run with args
    if len(sys.argv) == 1:
        print("\n📖 Usage:")
        print("  docker run <image> --help")
        print("  docker run <image> scan /path/to/videos")
        print("\n🔧 Configuration:")
        print("  Mount config: -v ./config.yaml:/app/config/config.yaml:ro")
        print("  Mount videos: -v /path/to/videos:/app/videos:ro")
        print("  Mount output: -v ./output:/app/output")
    else:
        print(f"\n📝 Arguments received: {sys.argv[1:]}")

if __name__ == "__main__":
    main()