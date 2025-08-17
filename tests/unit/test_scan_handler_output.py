from unittest.mock import MagicMock, patch

from src.cli.handlers import ScanHandler
from src.config.config import AppConfig
from src.core.models.scanning import ScanMode, ScanSummary


@patch("src.cli.handlers.click.echo")
def test_scan_completion_message_once(mock_echo):
    config = MagicMock(spec=AppConfig)
    config.logging = MagicMock()
    config.logging.level = "INFO"
    config.scan = MagicMock()  # Add scan attribute
    config.processing = MagicMock()  # Add processing attribute
    config.ffmpeg = MagicMock()  # Add ffmpeg attribute
    config.database = MagicMock()
    config.database.enabled = False
    handler = ScanHandler(config)

    summary = ScanSummary(
        directory="/tmp",
        total_files=5,
        processed_files=5,
        corrupt_files=1,
        healthy_files=4,
        scan_mode=ScanMode.QUICK,
        scan_time=10.0,
        deep_scans_needed=0,
        deep_scans_completed=0,
        started_at=0.0,
        completed_at=10.0,
        was_resumed=False,
    )

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
