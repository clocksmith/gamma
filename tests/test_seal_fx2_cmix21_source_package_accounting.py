from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/seal_fx2_cmix21_source_package_accounting.py"
)


def load_tool():
    spec = spec_from_file_location("seal_source_package_accounting", TOOL)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_accounting_metrics_keep_forecast_boundary_explicit() -> None:
    tool = load_tool()
    result = tool.accounting_metrics(
        prior_package_bytes=288_265,
        replacement_package_bytes=264_646,
    )
    assert result["source_package_saved_bytes"] == 23_619
    assert result["replacement_tail_forecast_score_bytes"] == 109_498_879
    assert result["replacement_tail_forecast_margin_bytes"] == 1_121
