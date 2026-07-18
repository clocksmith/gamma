from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/seal_fx2_cmix21_lstm112_plus80_10m_receipt.py"
)


def load_tool():
    spec = spec_from_file_location("seal_lstm112_plus80", TOOL)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_exact_counted_boundary():
    tool = load_tool()
    result = tool.calculate_accounting(301_162, 1_643_626, 1_635_633)
    assert result == {
        "candidate_program_bytes": 301_165,
        "incremental_program_bytes": 118_157,
        "forecast_debt_bytes": 681_114,
        "required_gross_1g_bytes": 799_272,
        "required_10m_gain_bytes": 7_993,
        "archive_ceiling_bytes": 1_635_633,
        "gross_gain_bytes": 7_993,
        "gross_rate": 799.3,
        "required_rate": 799.272,
        "margin_bytes": 0,
        "projected_score_bytes": 109_499_972,
    }


def test_one_byte_screen_miss_is_negative_margin():
    tool = load_tool()
    result = tool.calculate_accounting(301_162, 1_643_626, 1_635_634)
    assert result["margin_bytes"] == -1
    assert result["projected_score_bytes"] == 109_500_072


def test_tar_xz_counted_boundary():
    tool = load_tool()
    result = tool.calculate_accounting(247_404, 1_643_626, 1_636_170)
    assert result["candidate_program_bytes"] == 247_407
    assert result["incremental_program_bytes"] == 64_399
    assert result["required_gross_1g_bytes"] == 745_514
    assert result["required_rate"] == 745.514
    assert result["required_10m_gain_bytes"] == 7_456
    assert result["archive_ceiling_bytes"] == 1_636_170
    assert result["margin_bytes"] == 0


def test_bzip2_zip_counted_boundary():
    tool = load_tool()
    result = tool.calculate_accounting(288_265, 1_643_626, 1_635_762)
    assert result["candidate_program_bytes"] == 288_268
    assert result["incremental_program_bytes"] == 105_260
    assert result["required_gross_1g_bytes"] == 786_375
    assert result["required_rate"] == 786.375
    assert result["required_10m_gain_bytes"] == 7_864
    assert result["archive_ceiling_bytes"] == 1_635_762
    assert result["margin_bytes"] == 0


def test_bzip2_zip_measured_candidate_projects_below_target():
    tool = load_tool()
    result = tool.calculate_accounting(288_265, 1_643_626, 1_635_670)
    assert result["gross_rate"] == 795.6
    assert result["required_rate"] == 786.375
    assert result["margin_bytes"] == 92
    assert result["projected_score_bytes"] == 109_490_775
