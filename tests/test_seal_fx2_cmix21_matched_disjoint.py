import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[1]
    / "projects/enwiki9/tools/seal_fx2_cmix21_matched_disjoint.py"
)
SPEC = importlib.util.spec_from_file_location("seal_matched_disjoint", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_smaller_package_reduces_blend_floor():
    result = MODULE.economics(264_427, 290.0)
    assert result["base_forecast_score_bytes"] == 109_752_737
    assert result["base_forecast_debt_bytes"] == 252_737
    assert result["required_blend_gain_bytes_per_1m_before_integration"] == 252.737
    assert result["linear_projected_score_before_integration_bytes"] == 109_462_737
    assert result["maximum_integration_bytes_at_target"] == 37_263


def test_guarded_binary_skips_env_assignments(tmp_path):
    binary = tmp_path / "cmix"
    binary.write_bytes(b"binary")
    guard = {"command": ["env", "CMIX_P1_TRACE=trace.bin", str(binary), "-r"]}
    assert MODULE.guarded_binary(guard) == binary
