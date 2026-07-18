from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/seal_fx2_cmix21_lstm112_plus80_terminal.py"
)


def load_tool():
    spec = spec_from_file_location("seal_lstm112_plus80_terminal", TOOL)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_terminal_metrics_capture_disjoint_collapse():
    tool = load_tool()
    result = tool.summarize_metrics(
        fx2_1m_archive=175_204,
        native112_1m_archive=174_191,
        pair_1m_archive=174_120,
        fx2_10m_archive=1_643_626,
        native112_10m_archive=1_636_868,
        pair_10m_archive=1_635_670,
        disjoint_fx2_archive=45_612,
        disjoint_native112_archive=45_263,
        disjoint_pair_archive=45_259,
    )
    assert result["pair_first_1m_increment_over_native112_bytes"] == 71
    assert result["pair_cumulative_10m_increment_over_native112_bytes"] == 1_198
    assert result["pair_1m_to_10m_tail_bytes_per_1m"] == 763.5555555555555
    assert result["pair_tail_projected_1g_gross_saved_bytes"] == 763_876
    assert result["disjoint_native112_gross_saved_bytes"] == 349
    assert result["disjoint_pair_gross_saved_bytes"] == 353
    assert result["disjoint_pair_increment_over_native112_bytes"] == 4
    assert result["disjoint_pair_clears_required_rate"] is False
