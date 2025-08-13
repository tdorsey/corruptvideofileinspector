import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.cli.handlers import BaseHandler
from src.config.config import AppConfig
from src.core.models.scanning import ScanMode, ScanSummary

pytestmark = pytest.mark.unit


class DummySummary(ScanSummary):
    """
    Dummy summary object that inherits from ScanSummary for type compatibility.
    """

    # Override with test defaults
    total_files: int = 1
    processed_files: int = 1
    healthy_files: int = 0
    corrupt_files: int = 0
    directory: Path = Path("/test")
    scan_mode: ScanMode = ScanMode.QUICK
    scan_time: float = 1.0

    result: str = "default"

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        data["result"] = self.result
        return data


@pytest.fixture
def config(tmp_path):
    """
    Provides a mock AppConfig with output defaults set to tmp_path/output.
    """
    cfg = MagicMock(spec=AppConfig)
    # Setup nested output config
    cfg.output = MagicMock()
    cfg.output.default_output_dir = tmp_path / "output"
    cfg.output.default_filename = "scan_results.json"
    return cfg


def test_generate_output_uses_default_dir_when_given_directory(config, tmp_path, caplog):
    """
    If output_file is a directory, BaseHandler._generate_output should
    write to config.output.default_output_dir and log a warning.
    """
    # Arrange
    handler = BaseHandler(config)
    summary = DummySummary(result="42")
    # Create a directory to simulate passing a directory as output_file
    output_dir = tmp_path / "some_dir"
    output_dir.mkdir()

    caplog.set_level(logging.WARNING)

    # Act
    handler._generate_output(
        summary=summary,  # type: ignore[arg-type]
        output_file=output_dir,
        output_format="json",
        pretty_print=True,
    )

    # Assert: file written to default_output_dir
    expected_path = config.output.default_output_dir / config.output.default_filename
    assert expected_path.exists(), f"Expected output file at {expected_path} but not found"
    content = json.loads(expected_path.read_text(encoding="utf-8"))

    # Check that the custom result field is present
    assert "result" in content
    assert content["result"] == "42"

    # Check that essential ScanSummary fields are present
    assert "directory" in content
    assert "total_files" in content
    assert "processed_files" in content
    assert content["total_files"] == 1
    assert content["processed_files"] == 1

    # Assert: warning logged about using default directory
    warning_msgs = [r.message for r in caplog.records]
    assert any("using default output directory" in msg for msg in warning_msgs)


def test_generate_output_writes_to_specified_file(config, tmp_path):
    """
    If output_file is a file path, BaseHandler._generate_output should
    write directly to that path without redirect.
    """
    handler = BaseHandler(config)
    summary = DummySummary(result="bar")
    # Specify a file path
    target_file = tmp_path / "custom.json"
    # Act
    handler._generate_output(
        summary=summary,  # type: ignore[arg-type]
        output_file=target_file,
        output_format="json",
        pretty_print=False,
    )

    # Assert: file written to the specified path
    assert target_file.exists(), "Expected custom output file to be created"
    content = json.loads(target_file.read_text(encoding="utf-8"))

    # Check that the custom result field is present
    assert "result" in content
    assert content["result"] == "bar"

    # Check that essential ScanSummary fields are present
    assert "directory" in content
    assert "total_files" in content


def test_generate_output_default_writes_to_default_dir(config, tmp_path):
    """
    When no output_file is specified, BaseHandler._generate_output should
    write to config.output.default_output_dir using default_filename.
    """
    handler = BaseHandler(config)
    summary = DummySummary(result="123")
    # Act: no output_file
    handler._generate_output(
        summary=summary,  # type: ignore[arg-type]
        output_file=None,
        output_format="json",
        pretty_print=False,
    )

    # Assert: file written to default_output_dir
    expected = config.output.default_output_dir / config.output.default_filename
    assert expected.exists(), f"Expected output at {expected}"
    data = json.loads(expected.read_text(encoding="utf-8"))

    # Check that the data contains the expected result field
    assert "result" in data
    assert data["result"] == "123"

    # Check that essential ScanSummary fields are present
    assert "directory" in data
    assert "total_files" in data
    assert "processed_files" in data
    assert data["total_files"] == 1
    assert data["processed_files"] == 1
