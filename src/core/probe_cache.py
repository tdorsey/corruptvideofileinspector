"""
Persistent cache for FFprobe results to avoid redundant operations.
"""

import json
import logging
import threading
from pathlib import Path

from src.core.models.probe import ProbeResult

logger = logging.getLogger(__name__)


class ProbeResultCache:
    """Persistent cache for storing and retrieving FFprobe results."""

    def __init__(self, cache_file: Path, max_age_hours: float = 24.0):
        """
        Initialize probe result cache.

        Args:
            cache_file: Path to cache file for persistent storage
            max_age_hours: Maximum age for cached results in hours
        """
        self.cache_file = cache_file
        self.max_age_hours = max_age_hours
        self._cache: dict[str, ProbeResult] = {}
        self._lock = threading.Lock()

        # Ensure cache directory exists
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing cache
        self._load_cache()

    def get(self, file_path: Path) -> ProbeResult | None:
        """
        Get cached probe result for a file.

        Args:
            file_path: Path to the video file

        Returns:
            ProbeResult if cached and not expired, None otherwise
        """
        key = str(file_path.resolve())

        with self._lock:
            if key in self._cache:
                probe_result = self._cache[key]

                # Check if result is expired
                if probe_result.is_expired(self.max_age_hours):
                    logger.debug(f"Cached probe result expired for: {file_path}")
                    del self._cache[key]
                    return None

                # Check if file was modified since probe
                try:
                    file_mtime = file_path.stat().st_mtime
                    if file_mtime > probe_result.timestamp:
                        logger.debug(f"File modified since probe, cache invalid: {file_path}")
                        del self._cache[key]
                        return None
                except (OSError, FileNotFoundError):
                    # File no longer exists, remove from cache
                    logger.debug(f"File no longer exists, removing from cache: {file_path}")
                    del self._cache[key]
                    return None

                logger.debug(f"Using cached probe result for: {file_path}")
                return probe_result

            return None

    def put(self, probe_result: ProbeResult) -> None:
        """
        Store probe result in cache.

        Args:
            probe_result: Probe result to cache
        """
        key = str(probe_result.file_path.resolve())

        with self._lock:
            self._cache[key] = probe_result
            logger.debug(f"Cached probe result for: {probe_result.file_path}")

        # Save to disk asynchronously to avoid blocking
        self._save_cache()

    def has(self, file_path: Path) -> bool:
        """
        Check if file has a valid cached probe result.

        Args:
            file_path: Path to the video file

        Returns:
            True if valid cached result exists
        """
        return self.get(file_path) is not None

    def invalidate(self, file_path: Path) -> None:
        """
        Remove cached result for a specific file.

        Args:
            file_path: Path to the video file
        """
        key = str(file_path.resolve())

        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Invalidated cache for: {file_path}")

        self._save_cache()

    def clear_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        removed_count = 0

        with self._lock:
            # Use a single pass approach - build list of valid items
            valid_cache = {}
            for key, probe_result in self._cache.items():
                if not probe_result.is_expired(self.max_age_hours):
                    valid_cache[key] = probe_result
                else:
                    removed_count += 1

            self._cache = valid_cache

        if removed_count > 0:
            logger.info(f"Removed {removed_count} expired entries from probe cache")
            self._save_cache()

        return removed_count

    def clear_all(self) -> None:
        """Clear all cached results."""
        with self._lock:
            self._cache.clear()

        self._save_cache()
        logger.info("Cleared all cached probe results")

    def get_stats(self) -> dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_entries = len(self._cache)

            expired_count = sum(
                1 for result in self._cache.values() if result.is_expired(self.max_age_hours)
            )

            valid_entries = total_entries - expired_count

            successful_probes = sum(
                1
                for result in self._cache.values()
                if result.success and not result.is_expired(self.max_age_hours)
            )

            failed_probes = sum(
                1
                for result in self._cache.values()
                if not result.success and not result.is_expired(self.max_age_hours)
            )

        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": expired_count,
            "successful_probes": successful_probes,
            "failed_probes": failed_probes,
        }

    def _load_cache(self) -> None:
        """Load cache from disk."""
        if not self.cache_file.exists():
            logger.debug(f"Cache file does not exist: {self.cache_file}")
            return

        try:
            with self.cache_file.open("r", encoding="utf-8") as f:
                cache_data = json.load(f)

            loaded_count = 0
            for file_path_str, result_data in cache_data.items():
                try:
                    probe_result = ProbeResult.from_dict(result_data)
                    self._cache[file_path_str] = probe_result
                    loaded_count += 1
                except Exception as e:
                    logger.warning("Failed to load cache entry for %s: %s", file_path_str, e)

            logger.info(f"Loaded {loaded_count} probe results from cache")

            # Clean up expired entries
            self.clear_expired()

        except Exception:
            logger.exception("Failed to load probe cache from %s", self.cache_file)
            # Start with empty cache if loading fails
            self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            # Convert to serializable format
            cache_data = {}
            with self._lock:
                for key, probe_result in self._cache.items():
                    cache_data[key] = probe_result.to_dict()

            # Write atomically by writing to temp file first
            temp_file = self.cache_file.with_suffix(".tmp")
            with temp_file.open("w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, default=str)

            # Atomic rename
            temp_file.replace(self.cache_file)

            logger.debug(f"Saved {len(cache_data)} probe results to cache")

        except Exception:
            logger.exception("Failed to save probe cache to %s", self.cache_file)

    def __len__(self) -> int:
        """Get number of cached entries."""
        with self._lock:
            return len(self._cache)

    def __contains__(self, file_path: Path) -> bool:
        """Check if file path is in cache (regardless of expiration)."""
        key = str(file_path.resolve())
        with self._lock:
            return key in self._cache
