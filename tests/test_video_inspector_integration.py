"""
Integration tests for video_inspector module
"""

import contextlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from cli_handler import get_all_video_object_files, get_ffmpeg_command
from src.core.models.scanning import ScanMode
from src.core.models.inspection import VideoFile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestVideoInspectorIntegration(unittest.TestCase):
    """Integration tests for video inspector functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_files = []

    def tearDown(self):
        """Clean up test environment"""
        # Clean up test files
        for file_path in self.test_files:
            with contextlib.suppress(FileNotFoundError):
                Path(file_path).unlink()

        # Remove test directory
        with contextlib.suppress(OSError):
            Path(self.test_dir).rmdir()

    def create_test_file(self, filename: str, content: str = "test content") -> str:
        """Create a test file and return its path"""
        file_path = Path(self.test_dir) / filename
        file_path.write_text(content)
        self.test_files.append(str(file_path))
        return str(file_path)

    def test_video_file_creation(self):
        """Test VideoFile object creation"""
        # Create a test file
        test_file = self.create_test_file("test.mp4", "fake video content")

        # Create VideoFile object
        video_file = VideoFile(test_file)

        # Verify properties
        assert video_file.filename == test_file
        assert video_file.size > 0  # Should have file size
        assert video_file.duration == 0.0  # Default duration

    def test_video_file_nonexistent(self):
        """Test VideoFile with non-existent file"""
        nonexistent_path = "/nonexistent/file.mp4"
        video_file = VideoFile(nonexistent_path)

        assert video_file.filename == nonexistent_path
        assert video_file.size == 0  # No size for non-existent file
        assert video_file.duration == 0.0

    # Removed tests for VideoInspectionResult (class not implemented)

    def test_scan_mode_enum(self):
        """Test ScanMode enum values"""
        assert ScanMode.QUICK.value == "quick"
        assert ScanMode.DEEP.value == "deep"
        assert ScanMode.HYBRID.value == "hybrid"

    def test_get_ffmpeg_command(self):
        """Test ffmpeg command detection"""
        # This test may fail in environments without ffmpeg
        # but it should not raise an exception
        ffmpeg_cmd = get_ffmpeg_command()

        # Should return either a string (if ffmpeg found) or None
        assert ffmpeg_cmd is None or isinstance(ffmpeg_cmd, str)

        if ffmpeg_cmd:
            # If found, should be a valid path
            assert len(ffmpeg_cmd) > 0

    def test_get_all_video_object_files_empty_directory(self):
        """Test getting video files from empty directory"""
        video_files = get_all_video_object_files(self.test_dir)
        assert len(video_files) == 0
        assert isinstance(video_files, list)

    def test_get_all_video_object_files_with_videos(self):
        """Test getting video files from directory with video files"""
        # Create test video files
        self.create_test_file("video1.mp4")
        self.create_test_file("video2.avi")
        self.create_test_file("video3.mkv")
        self.create_test_file("not_video.txt")

        video_files = get_all_video_object_files(self.test_dir)

        # Should find 3 video files
        assert len(video_files) == 3

        # All should be VideoFile objects
        for vf in video_files:
            assert isinstance(vf, VideoFile)

        # Should be sorted by filename
        filenames = [vf.filename for vf in video_files]
        assert filenames == sorted(filenames)

    def test_get_all_video_object_files_recursive(self):
        """Test recursive scanning for video files"""
        # Create files in root
        self.create_test_file("root.mp4")

        # Create subdirectory and files
        subdir = Path(self.test_dir) / "subdir"
        subdir.mkdir(parents=True, exist_ok=True)

        subfile = subdir / "sub.avi"
        subfile.write_text("test")
        self.test_files.append(str(subfile))

        # Test recursive (default)
        video_files = get_all_video_object_files(self.test_dir, recursive=True)
        assert len(video_files) == 2

        # Test non-recursive
        video_files = get_all_video_object_files(self.test_dir, recursive=False)
        assert len(video_files) == 1

    def test_get_all_video_object_files_custom_extensions(self):
        """Test getting video files with custom extensions"""
        self.create_test_file("test.mp4")
        self.create_test_file("test.avi")
        self.create_test_file("test.custom")

        # Default extensions (should find mp4 and avi)
        video_files = get_all_video_object_files(self.test_dir)
        assert len(video_files) == 2

        # Custom extensions (should find only mp4)
        video_files = get_all_video_object_files(self.test_dir, extensions=[".mp4"])
        assert len(video_files) == 1
        assert video_files[0].filename.endswith(".mp4")

        # Include custom extension
        video_files = get_all_video_object_files(self.test_dir, extensions=[".mp4", ".custom"])
        assert len(video_files) == 2

    def test_get_all_video_object_files_case_insensitive(self):
        """Test case insensitive file extension matching"""
        self.create_test_file("VIDEO.MP4")
        self.create_test_file("movie.AVI")
        self.create_test_file("film.MkV")

        video_files = get_all_video_object_files(self.test_dir)
        assert len(video_files) == 3

    def test_integration_with_test_videos_directory(self):
        """Test integration with actual test-videos directory"""
        test_videos_dir = Path(__file__).resolve().parent.parent / "test-videos"

        if test_videos_dir.exists():
            # This should not raise an exception
            video_files = get_all_video_object_files(str(test_videos_dir))

            # Should return a list
            assert isinstance(video_files, list)

            # All items should be VideoFile objects
            for vf in video_files:
                assert isinstance(vf, VideoFile)
                assert os.path.exists(vf.filename) or vf.size == 0


if __name__ == "__main__":
    unittest.main()
