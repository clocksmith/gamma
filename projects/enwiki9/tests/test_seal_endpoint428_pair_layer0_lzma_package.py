import json

import pytest

from projects.enwiki9.tools.seal_endpoint428_pair_layer0_lzma_package import (
    economics,
    require_clean_guard,
)


def test_lzma_package_clears_counted_projection() -> None:
    result = economics(package_bytes=278_825)
    assert result["package_saved_bytes_vs_prior"] == 72_117
    assert result["incremental_program_bytes_vs_base"] == -70_370
    assert result["conservative_provisional_score_bytes"] == 109_452_151
    assert result["provisional_target_margin_bytes"] == 47_849
    assert result["economics_pass"] is True


def test_require_clean_guard_accepts_terminal_decimal_compliant_guard(tmp_path) -> None:
    path = tmp_path / "guard.json"
    path.write_text(
        json.dumps(
            {
                "status": "complete",
                "returncode": 0,
                "rss_guard_exceeded": False,
                "official_decimal_over_limit_kib": 0,
                "official_decimal_limit_kib": 9_765_625,
                "max_sampled_single_rss_kib": 9_077_648,
            }
        )
    )
    assert require_clean_guard(path)["status"] == "complete"


def test_require_clean_guard_rejects_decimal_overage(tmp_path) -> None:
    path = tmp_path / "guard.json"
    path.write_text(
        json.dumps(
            {
                "status": "complete",
                "returncode": 0,
                "rss_guard_exceeded": False,
                "official_decimal_over_limit_kib": 1,
                "official_decimal_limit_kib": 9_765_625,
                "max_sampled_single_rss_kib": 9_765_626,
            }
        )
    )
    with pytest.raises(ValueError, match="decimal-compliant"):
        require_clean_guard(path)
