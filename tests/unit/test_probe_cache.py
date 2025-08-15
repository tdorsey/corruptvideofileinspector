"""
Unit tests for probe cache functionality.
"""

import pytest
import tempfile
import time
from pathlib import Path

from src.core.probe_cache import ProbeResultCache
from src.core.models.probe import ProbeResult, StreamInfo, StreamType


class TestProbeResultCache:
    """Test probe cache functionality."""
    
    def test_cache_basic_operations(self):
        """Test basic cache operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            cache = ProbeResultCache(cache_file, max_age_hours=1.0)
            
            # Create test probe result
            probe_result = ProbeResult(
                file_path=Path("/test/video.mp4"),
                success=True,
                file_size=1024,
            )
            
            # Test empty cache
            assert len(cache) == 0
            assert cache.get(Path("/test/video.mp4")) is None
            assert not cache.has(Path("/test/video.mp4"))
            
            # Add result to cache
            cache.put(probe_result)
            
            # Test retrieval
            assert len(cache) == 1
            cached_result = cache.get(Path("/test/video.mp4"))
            assert cached_result is not None
            assert cached_result.file_path == probe_result.file_path
            assert cached_result.success == probe_result.success
            assert cache.has(Path("/test/video.mp4"))
    
    def test_cache_expiration(self):
        """Test cache expiration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            cache = ProbeResultCache(cache_file, max_age_hours=0.001)  # Very short expiry
            
            # Create expired probe result
            old_timestamp = time.time() - 3600  # 1 hour ago
            probe_result = ProbeResult(
                file_path=Path("/test/video.mp4"),
                success=True,
                timestamp=old_timestamp,
            )
            
            cache.put(probe_result)
            
            # Should be expired and return None
            assert cache.get(Path("/test/video.mp4")) is None
            assert not cache.has(Path("/test/video.mp4"))
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            cache = ProbeResultCache(cache_file)
            
            probe_result = ProbeResult(
                file_path=Path("/test/video.mp4"),
                success=True,
            )
            
            cache.put(probe_result)
            assert cache.has(Path("/test/video.mp4"))
            
            # Invalidate
            cache.invalidate(Path("/test/video.mp4"))
            assert not cache.has(Path("/test/video.mp4"))
    
    def test_cache_clear_operations(self):
        """Test cache clearing operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            cache = ProbeResultCache(cache_file, max_age_hours=0.001)
            
            # Add multiple results
            for i in range(3):
                probe_result = ProbeResult(
                    file_path=Path(f"/test/video{i}.mp4"),
                    success=True,
                    timestamp=time.time() - 3600,  # Expired
                )
                cache.put(probe_result)
            
            # Add one fresh result
            fresh_result = ProbeResult(
                file_path=Path("/test/fresh.mp4"),
                success=True,
            )
            cache.put(fresh_result)
            
            assert len(cache) == 4
            
            # Clear expired should remove 3
            removed = cache.clear_expired()
            assert removed == 3
            assert len(cache) == 1
            
            # Clear all should remove everything
            cache.clear_all()
            assert len(cache) == 0
    
    def test_cache_statistics(self):
        """Test cache statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            cache = ProbeResultCache(cache_file)
            
            # Add successful result
            success_result = ProbeResult(
                file_path=Path("/test/success.mp4"),
                success=True,
            )
            cache.put(success_result)
            
            # Add failed result
            failed_result = ProbeResult(
                file_path=Path("/test/failed.mp4"),
                success=False,
                error_message="Test error",
            )
            cache.put(failed_result)
            
            # Add expired result
            expired_result = ProbeResult(
                file_path=Path("/test/expired.mp4"),
                success=True,
                timestamp=time.time() - 3600,  # 1 hour ago
            )
            cache._cache[str(expired_result.file_path.resolve())] = expired_result
            
            stats = cache.get_stats()
            assert stats["total_entries"] == 3
            assert stats["successful_probes"] == 1  # Only non-expired successful
            assert stats["failed_probes"] == 1
            assert stats["expired_entries"] == 1
            assert stats["valid_entries"] == 2
    
    def test_cache_persistence(self):
        """Test cache persistence across instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            
            # Create first cache instance and add data
            cache1 = ProbeResultCache(cache_file)
            probe_result = ProbeResult(
                file_path=Path("/test/video.mp4"),
                success=True,
                file_size=2048,
            )
            cache1.put(probe_result)
            
            # Create second cache instance (should load persisted data)
            cache2 = ProbeResultCache(cache_file)
            
            # Should have loaded the data
            assert len(cache2) == 1
            cached_result = cache2.get(Path("/test/video.mp4"))
            assert cached_result is not None
            assert cached_result.file_path == probe_result.file_path
            assert cached_result.success == probe_result.success
            assert cached_result.file_size == probe_result.file_size
    
    def test_cache_with_complex_probe_result(self):
        """Test cache with complex probe result including streams."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            cache = ProbeResultCache(cache_file)
            
            # Create complex probe result
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
                file_path=Path("/test/complex.mp4"),
                success=True,
                streams=[video_stream, audio_stream],
                duration=120.5,
            )
            
            cache.put(probe_result)
            
            # Retrieve and verify
            cached_result = cache.get(Path("/test/complex.mp4"))
            assert cached_result is not None
            assert len(cached_result.streams) == 2
            assert cached_result.has_video_streams
            assert cached_result.has_audio_streams
            assert cached_result.duration == 120.5
            
            # Test persistence with complex data
            cache2 = ProbeResultCache(cache_file)
            cached_result2 = cache2.get(Path("/test/complex.mp4"))
            assert cached_result2 is not None
            assert len(cached_result2.streams) == 2
            assert cached_result2.has_video_streams
            assert cached_result2.duration == 120.5