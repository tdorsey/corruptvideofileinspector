from pathlib import Path
from unittest.mock import MagicMock

from src.cli.handlers import ScanHandler
from src.config.config import AppConfig
from src.core.models.scanning import ScanMode


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
    config.output.default_output_dir = tmp_path
    config.output.default_json = True
    config.logging.level = "INFO"
    handler = ScanHandler(config)
    handler.output_formatter = MagicMock()

    # Ensure output dir is writable
    test_file = tmp_path / "writability_check.txt"
    try:
        with test_file.open("w"):
            pass
    except Exception as e:
        pytest.fail(f"Output directory is not writable: {e}")

    # Call _generate_output with no output_file
    handler._generate_output(
        summary=DummySummary(),
        output_file=None,
        output_format="json",
        pretty_print=True,
    )

    # Check that output_formatter.write_scan_results was called with a file in tmp_path
    called_path = handler.output_formatter.write_scan_results.call_args[1]["output_file"]
    assert Path(called_path).parent == tmp_path
    assert Path(called_path).name.startswith("scan_results.")
