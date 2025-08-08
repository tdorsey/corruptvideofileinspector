"""
End-to-end integration tests for the entire application
"""

import contextlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from src.cli.handlers import get_all_video_object_files
from src.core.models.inspection import VideoFile
from src.core.video_files import count_all_video_files
from src.core.formatting import format_file_size
from src.config.video_formats import get_video_extensions

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytestmark = pytest.mark.integration


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests for the complete application workflow"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_files = []

        # Create a more complex directory structure
        self.create_test_video_files()

    def tearDown(self):
        """Clean up test environment"""
        # Clean up test files
        for file_path in self.test_files:
            with contextlib.suppress(FileNotFoundError):
                Path(file_path).unlink()

        with contextlib.suppress(OSError):
            shutil.rmtree(self.test_dir)

    def create_test_video_files(self):
        """Create a realistic test directory structure with video files"""
        # Root level video files
        self.create_test_file("movie1.mp4", "fake mp4 content")
        self.create_test_file("documentary.avi", "fake avi content")
        self.create_test_file("series_episode.mkv", "fake mkv content")

        # Mixed file types
        self.create_test_file("readme.txt", "not a video file")
        self.create_test_file("image.jpg", "fake image")

        # Subdirectory with videos
        subdir1 = Path(self.test_dir) / "movies"
        subdir1.mkdir(parents=True, exist_ok=True)

        subfile1 = subdir1 / "action_movie.mp4"
        with subfile1.open("w") as f:
            f.write("fake action movie content")
        self.test_files.append(str(subfile1))

        subfile2 = subdir1 / "comedy.avi"
        with subfile2.open("w") as f:
            f.write("fake comedy content")
        self.test_files.append(str(subfile2))

        # Nested subdirectory
        subdir2 = subdir1 / "classics"
        subdir2.mkdir(parents=True, exist_ok=True)

        subfile3 = subdir2 / "old_movie.mov"
        with subfile3.open("w") as f:
            f.write("fake old movie content")
        self.test_files.append(str(subfile3))

        # Empty subdirectory
        empty_dir = Path(self.test_dir) / "empty"
        empty_dir.mkdir(parents=True, exist_ok=True)

    def create_test_file(self, filename: str, content: str = "test content") -> str:
        """Create a test file and return its path"""
        file_path = Path(self.test_dir) / filename
        with file_path.open("w") as f:
            f.write(content)
        self.test_files.append(str(file_path))
        return str(file_path)

    def test_complete_video_discovery_workflow(self):
        """Test complete video file discovery workflow"""
        # Step 1: Count video files using utils
        total_count = count_all_video_files(self.test_dir, recursive=True)

        assert total_count == 6  # All video files including subdirs

        non_recursive_count = count_all_video_files(str(self.test_dir), recursive=False)
        assert non_recursive_count == 3  # Only root level videos

        # Step 2: Get video file objects using video_inspector

        video_files = get_all_video_object_files(str(self.test_dir), recursive=True)
        assert len(video_files) == 6

        # Verify all are VideoFile objects
        for vf in video_files:
            assert isinstance(vf, VideoFile)
            assert vf.size > 0  # Should have content

        # Step 3: Verify file extensions are handled correctly
        extensions = get_video_extensions()
        found_extensions = set()
        for vf in video_files:
            ext = Path(vf.name).suffix.lower()
            found_extensions.add(ext)
            assert ext in extensions

        # Should find multiple different extensions
        assert len(found_extensions) >= 3

    def test_file_size_formatting_workflow(self):
        """Test file size formatting across different file sizes"""

        video_files = get_all_video_object_files(str(self.test_dir))

        for vf in video_files:
            size = vf.size
            formatted_size = format_file_size(size)

            # Should be a valid format
            assert isinstance(formatted_size, str)
            assert any(unit in formatted_size for unit in ["B", "KB", "MB", "GB"])

            # Should be parseable (contains a number)
            assert any(char.isdigit() for char in formatted_size)

    def test_recursive_vs_non_recursive_consistency(self):
        """Test consistency between recursive and non-recursive scanning"""
        # Get all files recursively

        all_recursive_count = count_all_video_files(str(self.test_dir), recursive=True)
        all_recursive_objects = get_all_video_object_files(str(self.test_dir), recursive=True)

        # Get root files only
        root_count = count_all_video_files(str(self.test_dir), recursive=False)
        root_objects = get_all_video_object_files(str(self.test_dir), recursive=False)

        # Consistency checks
        assert all_recursive_count == len(all_recursive_objects)
        assert root_count == len(root_objects)

        # Recursive should find more files than non-recursive
        assert all_recursive_count > root_count
        assert len(all_recursive_objects) > len(root_objects)

        # All root files should be included in recursive results
        root_filenames = {vf.name for vf in root_objects}
        all_filenames = {vf.name for vf in all_recursive_objects}

        assert root_filenames.issubset(all_filenames)

    def test_extension_filtering_workflow(self):
        """Test custom extension filtering across the workflow"""
        # Test with only MP4 files

        mp4_count = count_all_video_files(str(self.test_dir), extensions=[".mp4"])
        mp4_objects = get_all_video_object_files(str(self.test_dir), extensions=[".mp4"])

        assert mp4_count == len(mp4_objects)

        # Verify all found files are MP4
        for vf in mp4_objects:
            assert vf.name.lower().endswith(".mp4")

        # Test with multiple extensions

        multi_count = count_all_video_files(str(self.test_dir), extensions=[".mp4", ".avi"])
        multi_objects = get_all_video_object_files(str(self.test_dir), extensions=[".mp4", ".avi"])

        assert multi_count == len(multi_objects)
        assert multi_count > mp4_count  # Should find more files

    def test_empty_directory_handling(self):
        """Test handling of empty directories"""
        empty_dir = Path(self.test_dir) / "empty"

        # Should handle empty directory gracefully
        count = count_all_video_files(str(empty_dir))
        assert count == 0

        objects = get_all_video_object_files(str(empty_dir))
        assert len(objects) == 0
        assert isinstance(objects, list)

    def test_large_directory_structure_simulation(self):
        """Test performance with a simulated large directory structure"""
        # Create many subdirectories and files

        large_test_dir = Path(self.test_dir) / "large_test"
        large_test_dir.mkdir(parents=True, exist_ok=True)

        created_files = []
        expected_video_count = 0

        # Create nested structure
        for i in range(5):  # 5 subdirectories
            subdir = large_test_dir / f"subdir_{i}"
            subdir.mkdir(parents=True, exist_ok=True)

            for j in range(3):  # 3 files per directory
                video_file = subdir / f"video_{i}_{j}.mp4"
                with video_file.open("w") as f:
                    f.write(f"fake video content {i}_{j}")
                created_files.append(str(video_file))
                expected_video_count += 1

                # Add some non-video files
                text_file = subdir / f"readme_{i}_{j}.txt"
                with text_file.open("w") as f:
                    f.write("not a video")
                created_files.append(str(text_file))

        try:
            # Test counting
            count = count_all_video_files(str(large_test_dir), recursive=True)
            assert count == expected_video_count

            # Test object creation
            objects = get_all_video_object_files(str(large_test_dir), recursive=True)
            assert len(objects) == expected_video_count

            # Verify all objects are valid
            for obj in objects:
                assert isinstance(obj, VideoFile)
                assert obj.size > 0
                assert obj.filename.endswith(".mp4")
        except Exception as e:
            self.fail("Exception occurred during large directory structure " f"simulation: {e}")
