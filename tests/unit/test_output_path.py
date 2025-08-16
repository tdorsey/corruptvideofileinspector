import json
from unittest.mock import MagicMock

import pytest

from src.cli.handlers import BaseHandler
from src.config.config import AppConfig
from src.core.models.scanning import ScanMode

pytestmark = pytest.mark.unit


class DummySummary:
    is_complete = True
    scan_mode = ScanMode.QUICK
    processed_files = 1
    corrupt_files = 0
    healthy_files = 1
    scan_time = 1.0
    success_rate = 100.0
    was_resumed = False
    deep_scans_needed = 0
    deep_scans_completed = 0


def test_generate_output_uses_output_dir(tmp_path):
    # Setup config with output dir as tmp_path
    config = MagicMock(spec=AppConfig)
    config.output = MagicMock()
    config.output.default_output_dir = tmp_path
    config.output.default_filename = "results.json"
    config.database = MagicMock()
    config.database.enabled = False

    # Create a mock handler with our config
    handler = BaseHandler(config)

    # Create a mock summary object that has model_dump method
    summary = MagicMock()
    summary.model_dump.return_value = {"test": "data"}

    # Call generate output
    handler._generate_output(summary)

    # Check file was created in the right place
    output_file = tmp_path / "results.json"
    assert output_file.exists()

    # Check file contains expected data
    content = json.loads(output_file.read_text(encoding="utf-8"))
    assert content == {"test": "data"}
