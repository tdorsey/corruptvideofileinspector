from unittest.mock import MagicMock, patch

from src.cli.handlers import ScanHandler
from src.config.config import AppConfig
from src.core.models.scanning import ScanMode


class DummySummary:
    is_complete = True
    scan_mode = ScanMode.QUICK
    processed_files = 5
    corrupt_files = 1
    healthy_files = 4
    scan_time = 10.0
    success_rate = 80.0
    was_resumed = False
    deep_scans_needed = 0
    deep_scans_completed = 0


@patch("src.cli.handlers.click.echo")
def test_scan_completion_message_once(mock_echo):
    config = MagicMock(spec=AppConfig)
    config.logging.level = "INFO"
    handler = ScanHandler(config)
    summary = DummySummary()

    # Call twice, should only print once
    handler._show_scan_results(summary)
    handler._show_scan_results(summary)

    # Count SCAN COMPLETE and SCAN TERMINATED messages
    scan_complete_count = sum(
        1 for call in mock_echo.call_args_list if "SCAN COMPLETE" in str(call)
    )
    scan_terminated_count = sum(
        1 for call in mock_echo.call_args_list if "SCAN TERMINATED" in str(call)
    )
    # Only one of these should be present, and only once
    assert scan_complete_count + scan_terminated_count == 1

    # Opening/closing lines should also only appear once
    bar_count = sum(1 for call in mock_echo.call_args_list if "=" * 50 in str(call))
    assert bar_count == 2  # one before, one after
