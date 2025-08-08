import tempfile
import unittest
from pathlib import Path

import pytest
import yaml

from src.config import AppConfig, load_config

pytestmark = pytest.mark.unit


class TestConfigDataClasses(unittest.TestCase):
    """Test configuration data classes"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_defaults(self):
        """Test default configuration values"""
        from src.config.config import (
            FFmpegConfig,
            LoggingConfig,
            OutputConfig,
            ProcessingConfig,
            ScanConfig,
            TraktConfig,
        )

        cfg = AppConfig(
            logging=LoggingConfig(level="INFO"),
            ffmpeg=FFmpegConfig(command=Path("/usr/bin/ffmpeg")),
            processing=ProcessingConfig(max_workers=4, default_mode="quick"),
            output=OutputConfig(default_json=True, default_output_dir=Path("/app/output")),
            scan=ScanConfig(recursive=True, default_input_dir=Path("/app/videos")),
            trakt=TraktConfig(client_id="", client_secret=""),
        )

        # Test logging defaults
        assert cfg.logging.level == "INFO"
        assert "%(asctime)s" in cfg.logging.format

        # Test processing defaults
        assert cfg.processing.max_workers == 4
        assert cfg.processing.default_mode == "quick"

        # Test scan defaults
        assert cfg.scan.recursive
        assert cfg.scan.default_input_dir == Path("/app/videos")
        assert ".mp4" in cfg.scan.extensions
        assert ".mkv" in cfg.scan.extensions

    def test_load_config_with_file(self):
        """Test loading configuration with specific file"""
        config_data = {
            "logging": {"level": "WARNING"},
            "ffmpeg": {"command": "/usr/bin/ffmpeg"},
            "processing": {"max_workers": 10, "default_mode": "quick"},
            "output": {"default_json": True, "default_output_dir": "/app/output"},
            "scan": {"recursive": True, "default_input_dir": "/app/videos"},
            "trakt": {"client_id": "", "client_secret": ""},
        }

        config_file = Path(self.temp_dir) / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        cfg = load_config(config_file)

        assert cfg.logging.level == "WARNING"
        assert cfg.processing.max_workers == 10

    def test_load_config_defaults_only(self):
        """Test loading configuration with defaults only"""
        # Test by loading the existing config.yaml
        cfg = load_config()

        # Should have values from the default config file
        assert isinstance(cfg.logging.level, str)
        assert isinstance(cfg.processing.max_workers, int)
        assert isinstance(cfg.scan.recursive, bool)


if __name__ == "__main__":
    unittest.main()
