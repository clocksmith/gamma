from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/seal_fx2_cmix21_lstm200_disjoint.py"
)


def load_tool():
    spec = spec_from_file_location("seal_lstm200_disjoint", TOOL)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_summarize_uses_counted_required_rate() -> None:
    tool = load_tool()
    result = tool.summarize(
        baseline_archive_bytes=45_612,
        candidate_archive_bytes=44_800,
        required_rate=762.424,
    )
    assert result["gross_saved_bytes"] == 812
    assert abs(result["margin_over_required_rate_bytes_per_1m"] - 49.576) < 1e-9
    assert result["clears_required_rate"] is True
