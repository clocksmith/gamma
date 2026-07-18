from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/seal_fx2_cmix21_lstm200_source_frontier.py"
)


def load_tool():
    spec = spec_from_file_location("seal_lstm200_frontier", TOOL)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_package_economics_charge_every_counted_byte() -> None:
    tool = load_tool()
    result = tool.package_economics(264_314)
    assert result["counted_program_bytes"] == 264_317
    assert result["incremental_program_bytes"] == 81_309
    assert result["linear_projected_score_bytes"] == 109_113_424
    assert result["linear_projected_target_margin_bytes"] == 386_576
    assert result["required_gross_saved_bytes_per_1m"] == 762.424
