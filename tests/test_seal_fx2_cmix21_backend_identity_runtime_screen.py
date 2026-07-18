from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/seal_fx2_cmix21_backend_identity_runtime_screen.py"
)


def load_tool():
    spec = spec_from_file_location("seal_backend_runtime", TOOL)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_verify_screen_rejects_wrong_scope() -> None:
    tool = load_tool()
    receipt = {
        "schema": "fx2_cmix21_backend_identity_runtime_screen_v1",
        "scope_bytes": 999,
        "metrics": {"all_guards_clean": True, "archive_identity": True},
        "runs": [],
    }
    try:
        tool.verify_screen(receipt, 1_000)
    except RuntimeError as error:
        assert "not exact 1000" in str(error)
    else:
        raise AssertionError("wrong scope was accepted")


def test_package_metrics_charge_source_delta() -> None:
    tool = load_tool()
    result = tool.package_metrics(
        reference_package_bytes=264_646,
        candidate_package_bytes=264_711,
    )
    assert result["candidate_source_package_delta_bytes"] == 65
    assert result["candidate_tail_forecast_score_bytes"] == 109_498_944
    assert result["candidate_tail_forecast_margin_bytes"] == 1_056
