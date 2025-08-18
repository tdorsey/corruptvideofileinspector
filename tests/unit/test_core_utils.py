"""Unit tests for core utils module"""

import hashlib
import tempfile
import unittest
from pathlib import Path

import pytest

from src.core.utils import calculate_sha256_hash, format_hash_for_logging

pytestmark = pytest.mark.unit


class TestSha256Hash(unittest.TestCase):
    """Test SHA-256 hash calculation functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_calculate_sha256_hash_small_file(self):
        """Test SHA-256 hash calculation for a small file"""
        # Create test file with known content
        test_content = b"Hello, World! This is a test file."
        test_file = self.temp_path / "test.txt"
        test_file.write_bytes(test_content)

        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()

        # Test function
        result_hash = calculate_sha256_hash(test_file)

        self.assertEqual(result_hash, expected_hash)
        self.assertEqual(len(result_hash), 64)  # SHA-256 hash should be 64 hex chars

    def test_calculate_sha256_hash_empty_file(self):
        """Test SHA-256 hash calculation for an empty file"""
        test_file = self.temp_path / "empty.txt"
        test_file.write_bytes(b"")

        # Expected hash for empty file
        expected_hash = hashlib.sha256(b"").hexdigest()

        result_hash = calculate_sha256_hash(test_file)

        self.assertEqual(result_hash, expected_hash)

    def test_calculate_sha256_hash_large_file(self):
        """Test SHA-256 hash calculation for a larger file (tests chunking)"""
        # Create test file with 10KB of repeated data
        test_content = b"A" * 10240
        test_file = self.temp_path / "large.txt"
        test_file.write_bytes(test_content)

        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()

        result_hash = calculate_sha256_hash(test_file)

        self.assertEqual(result_hash, expected_hash)

    def test_calculate_sha256_hash_nonexistent_file(self):
        """Test SHA-256 hash calculation for non-existent file"""
        nonexistent_file = self.temp_path / "does_not_exist.txt"

        with self.assertRaises(FileNotFoundError):
            calculate_sha256_hash(nonexistent_file)

    def test_calculate_sha256_hash_video_like_content(self):
        """Test SHA-256 hash calculation for video-like binary content"""
        # Create test file with binary data that might represent video
        test_content = bytes(range(256)) * 100  # 25.6KB of binary data
        test_file = self.temp_path / "test.mp4"
        test_file.write_bytes(test_content)

        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()

        result_hash = calculate_sha256_hash(test_file)

        self.assertEqual(result_hash, expected_hash)


class TestHashFormatting(unittest.TestCase):
    """Test hash formatting functionality"""

    def test_format_hash_for_logging_short(self):
        """Test short hash formatting"""
        full_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        expected_short = "abcdef12...7890"

        result = format_hash_for_logging(full_hash, short=True)

        self.assertEqual(result, expected_short)

    def test_format_hash_for_logging_full(self):
        """Test full hash formatting"""
        full_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

        result = format_hash_for_logging(full_hash, short=False)

        self.assertEqual(result, full_hash)

    def test_format_hash_for_logging_short_hash_input(self):
        """Test formatting with short hash input"""
        short_hash = "abcdef12"

        # Should return the full hash if it's too short for shortening
        result = format_hash_for_logging(short_hash, short=True)

        self.assertEqual(result, short_hash)

    def test_format_hash_for_logging_medium_hash(self):
        """Test formatting with medium-length hash"""
        MIN_HASH_SHORTEN_LENGTH = 13  # Should match the threshold in production code
        # Construct a hash just over the minimum threshold for shortening
        medium_hash = "abcdef12" + "34567"  # 8 + 5 = 13 chars

        result = format_hash_for_logging(medium_hash, short=True)

        expected = "abcdef12...567"  # Should be shortened
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()