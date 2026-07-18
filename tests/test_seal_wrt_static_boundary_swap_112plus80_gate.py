from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "enwiki9"
    / "tools"
    / "seal_wrt_static_boundary_swap_112plus80_gate.py"
)
SPEC = importlib.util.spec_from_file_location("boundary_gate", TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_clean_guard_requires_both_memory_boundaries() -> None:
    assert MODULE.clean_guard(
        {
            "status": "complete",
            "returncode": 0,
            "rss_guard_exceeded": False,
            "official_decimal_over_limit_kib": 0,
        }
    )
    assert not MODULE.clean_guard(
        {
            "status": "complete",
            "returncode": 0,
            "rss_guard_exceeded": False,
            "official_decimal_over_limit_kib": 1,
        }
    )


def test_artifact_hashes_content(tmp_path: Path) -> None:
    payload = tmp_path / "payload"
    payload.write_bytes(b"abc")
    assert MODULE.artifact(payload) == {
        "path": str(payload),
        "bytes": 3,
        "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    }


def test_source_wrapper_is_the_next_constructive_proof() -> None:
    source = Path(TOOL).read_text()
    assert "target_closing_10m_screen_requires_source_wrapper_proof" in source
    assert '"wrapper_proof_authorized": target_closing_screen' in source
    assert "--source-package-receipt" in source


def test_source_package_shrink_closes_the_tail_forecast_without_archive_gain() -> None:
    metrics = MODULE.economics(
        baseline_archive_bytes=1_635_670,
        candidate_archive_bytes=1_635_670,
        baseline_source_zip_bytes=288_265,
        candidate_source_zip_bytes=264_593,
    )
    assert metrics["archive_saved_bytes"] == 0
    assert metrics["source_package_delta_bytes"] == -23_672
    assert metrics["tail_projected_score_bytes"] == 109_498_826
    assert metrics["tail_projected_margin_to_109500000_bytes"] == 1_174


def test_source_package_shrink_tolerates_only_eleven_10m_archive_bytes() -> None:
    eleven = MODULE.economics(
        baseline_archive_bytes=1_635_670,
        candidate_archive_bytes=1_635_681,
        baseline_source_zip_bytes=288_265,
        candidate_source_zip_bytes=264_593,
    )
    twelve = MODULE.economics(
        baseline_archive_bytes=1_635_670,
        candidate_archive_bytes=1_635_682,
        baseline_source_zip_bytes=288_265,
        candidate_source_zip_bytes=264_593,
    )
    assert eleven["tail_projected_score_bytes"] == 109_499_926
    assert twelve["tail_projected_score_bytes"] == 109_500_026


def test_negative_archive_transfer_is_not_relabelled_by_package_savings() -> None:
    source = Path(TOOL).read_text()
    assert "elif archive_saved_bytes <= 0:" in source
    assert "retire_static_boundary_swap_negative_exact_transfer" in source
