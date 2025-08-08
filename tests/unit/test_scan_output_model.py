from src.core.models.reporting.scan_output import ScanMode, ScanOutputModel


def test_scan_output_model_serialization():
    model = ScanOutputModel(
        scan_mode=ScanMode.QUICK,
        total_files=10,
        processed_files=10,
        corrupt_files=2,
        healthy_files=8,
        scan_time=12.5,
        success_rate=80.0,
        was_resumed=True,
        deep_scans_needed=3,
        deep_scans_completed=3,
    )
    # Test model to dict
    d = model.model_dump()
    assert d["scan_mode"] == "quick"
    assert d["total_files"] == 10
    assert d["corrupt_files"] == 2
    # Test model to JSON
    json_str = model.model_dump_json()
    assert '"scan_mode":"quick"' in json_str  # JSON without spaces around :
    # Test round-trip
    loaded = ScanOutputModel.model_validate_json(json_str)
    assert loaded.scan_mode == ScanMode.QUICK
    assert loaded.total_files == 10


def test_scan_output_model_optional_fields():
    model = ScanOutputModel(
        scan_mode=ScanMode.DEEP,
        total_files=5,
        processed_files=5,
        corrupt_files=0,
        healthy_files=5,
        scan_time=5.0,
    )
    d = model.model_dump()
    assert d["scan_mode"] == "deep"
    assert d["success_rate"] is None
    assert d["was_resumed"] is None
    assert d["deep_scans_needed"] is None
    assert d["deep_scans_completed"] is None


def test_scan_output_model_json_file(tmp_path):
    model = ScanOutputModel(
        scan_mode=ScanMode.HYBRID,
        total_files=3,
        processed_files=3,
        corrupt_files=1,
        healthy_files=2,
        scan_time=3.0,
        success_rate=66.7,
    )
    out_file = tmp_path / "scan_output.json"
    out_file.write_text(model.model_dump_json(indent=2))
    loaded = ScanOutputModel.model_validate_json(out_file.read_text())
    assert loaded.scan_mode == ScanMode.HYBRID
    assert loaded.success_rate == 66.7
