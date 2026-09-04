from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


TOOL = (
    Path(__file__).resolve().parents[1]
    / "skills/enwiki9-status/scripts/report.py"
)
SPEC = importlib.util.spec_from_file_location("enwiki9_status_skill", TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write_fixture(tmp_path: Path) -> tuple[Path, dict, dict]:
    (tmp_path / "AGENTS.md").write_text("fixture\n")
    evidence = tmp_path / "receipt.json"
    evidence.write_text("{}\n")
    ledger = {
        "schema": "enwiki9_hutter_frontier_v1",
        "target": {
            "input_bytes": 1_000_000_000,
            "score_bytes": 105_000_000,
            "required_roundtrip": True,
        },
        "canonical_best_forecast_id": "candidate",
        "candidates": [
            {
                "id": "candidate",
                "name": "candidate",
                "rank": 1,
                "status": "active",
                "evidence_tier": "constructive_prefix",
                "forecast_score": 109_557_404,
                "score_credit_bytes": 0,
                "source_paths": ["receipt.json"],
                "source_required": True,
                "metric_assertions": [],
                "decision": "test",
                "next_gate": "test",
            }
        ],
        "quarantine": [],
    }
    operational = {
        "target_score_10_95": 105_000_000,
        "best_forecast": {"projected_score": 109_557_404},
        "best_full_1g": {"status": "not verified"},
        "has_10_95_constructive_upper_bound": False,
    }
    return evidence, ledger, operational


def test_normalizes_margin_and_preserves_proof_boundary(tmp_path: Path) -> None:
    _, ledger, operational = write_fixture(tmp_path)

    status, errors = MODULE.validate_and_normalize(
        tmp_path, ledger, operational
    )

    assert errors == []
    assert status["official"]["verified_full_corpus_result"] is False
    assert status["canonical_forecast"]["forecast_margin_bytes"] == -4_557_404
    markdown = MODULE.render_markdown(status)
    assert "Target score: `105,000,000` bytes (`10.5000000%`)" in markdown
    assert "Verified official full-1G score: `unknown`" in markdown
    assert "Best counted forecast: `109,557,404` (`10.9557404%`)" in markdown
    assert "distance above target `4,557,404`" in markdown
    assert "`0.4557404 percentage points`" in markdown
    assert "Active candidate provisional projection: `109,557,404` (`10.9557404%`)" in markdown
    assert "## Recorded Frontier State" in markdown
    assert "Verified target state: `not won`" in markdown
    assert "Active candidate: `candidate`" in markdown
    assert "Recorded next gate: test" in markdown
    assert "Continue toward the Hutter Prize" not in markdown


def test_nonconstructive_score_credit_fails_closed(tmp_path: Path) -> None:
    _, ledger, operational = write_fixture(tmp_path)
    ledger["candidates"][0]["evidence_tier"] = "causal_shadow"
    ledger["candidates"][0]["score_credit_bytes"] = 1

    _, errors = MODULE.validate_and_normalize(tmp_path, ledger, operational)

    assert any("nonconstructive evidence has score credit" in error for error in errors)


def test_missing_required_source_fails_closed(tmp_path: Path) -> None:
    _, ledger, operational = write_fixture(tmp_path)
    ledger["candidates"][0]["source_paths"] = ["missing.json"]

    _, errors = MODULE.validate_and_normalize(tmp_path, ledger, operational)

    assert any("required evidence source missing" in error for error in errors)


def test_verified_official_win_requires_roundtrip(tmp_path: Path) -> None:
    _, ledger, operational = write_fixture(tmp_path)
    operational["best_full_1g"] = {
        "scope_bytes": 1_000_000_000,
        "hutter_score": 104_999_999,
        "roundtrip_ok": False,
    }

    status, _ = MODULE.validate_and_normalize(tmp_path, ledger, operational)

    assert status["official"]["won"] is False
    assert status["official"]["verified_full_corpus_result"] is False


def test_verified_win_reports_state_without_prescribing_work(tmp_path: Path) -> None:
    _, ledger, operational = write_fixture(tmp_path)
    operational["best_full_1g"] = {
        "scope_bytes": 1_000_000_000,
        "hutter_score": 104_999_999,
        "roundtrip_ok": True,
    }
    operational["has_10_95_constructive_upper_bound"] = True

    status, errors = MODULE.validate_and_normalize(tmp_path, ledger, operational)
    markdown = MODULE.render_markdown(status)

    assert errors == []
    assert status["official"]["won"] is True
    assert "Verified target state: `won`" in markdown
    assert "submission packaging" not in markdown


def test_metric_assertion_detects_receipt_drift(tmp_path: Path) -> None:
    _, ledger, operational = write_fixture(tmp_path)
    ledger["candidates"][0]["metric_assertions"] = [
        {
            "source": "receipt.json",
            "pointer": "/score",
            "candidate_field": "forecast_score",
        }
    ]
    (tmp_path / "receipt.json").write_text(json.dumps({"score": 1}) + "\n")

    _, errors = MODULE.validate_and_normalize(tmp_path, ledger, operational)

    assert any("disagrees with" in error for error in errors)


def test_missing_optional_assertion_source_is_skipped(tmp_path: Path) -> None:
    _, ledger, operational = write_fixture(tmp_path)
    candidate = ledger["candidates"][0]
    candidate["source_required"] = False
    candidate["source_paths"] = ["missing.json"]
    candidate["metric_assertions"] = [
        {
            "source": "missing.json",
            "pointer": "/score",
            "candidate_field": "forecast_score",
        }
    ]

    status, errors = MODULE.validate_and_normalize(tmp_path, ledger, operational)

    assert errors == []
    audit = status["canonical_forecast"]["metric_assertion_audit"][0]
    assert audit["pass"] is None
    assert audit["skipped"] is True
    assert audit["reason"] == "optional source absent"


def test_present_optional_assertion_source_still_detects_drift(
    tmp_path: Path,
) -> None:
    _, ledger, operational = write_fixture(tmp_path)
    candidate = ledger["candidates"][0]
    candidate["source_required"] = False
    candidate["metric_assertions"] = [
        {
            "source": "receipt.json",
            "pointer": "/score",
            "candidate_field": "forecast_score",
        }
    ]
    (tmp_path / "receipt.json").write_text(json.dumps({"score": 1}) + "\n")

    _, errors = MODULE.validate_and_normalize(tmp_path, ledger, operational)

    assert any("disagrees with" in error for error in errors)


def test_under_target_forecast_renders_margin_below_target(tmp_path: Path) -> None:
    _, ledger, operational = write_fixture(tmp_path)
    ledger["candidates"][0]["forecast_score"] = 104_908_345
    operational["best_forecast"]["projected_score"] = 104_908_345

    status, errors = MODULE.validate_and_normalize(tmp_path, ledger, operational)
    markdown = MODULE.render_markdown(status)

    assert errors == []
    assert "Best counted forecast: `104,908,345` (`10.4908345%`)" in markdown
    assert "margin below target `91,655` bytes" in markdown
    assert "distance above target `0`" not in markdown


def test_live_observation_renders_guarded_progress(tmp_path: Path) -> None:
    _, ledger, operational = write_fixture(tmp_path)
    live = {
        "candidate": "candidate",
        "scope_bytes": 10_000_000,
        "progress_percent": 35.02,
        "guard_status": "running",
        "terminal": False,
        "max_sampled_single_rss_kib": 9_000_000,
        "max_sampled_tree_rss_kib": 9_010_000,
        "official_decimal_limit_kib": 9_765_625,
        "rss_guard_exceeded": False,
    }

    status, errors = MODULE.validate_and_normalize(
        tmp_path, ledger, operational, live
    )
    markdown = MODULE.render_markdown(status)

    assert errors == []
    assert "Live gate scope `10,000,000`; progress `35.02%`" in markdown
    assert "Decimal single-process margin `765,625` KiB" in markdown


def test_score_percentage_uses_full_corpus_denominator() -> None:
    assert MODULE.fmt_score_percent(108_000_000) == "10.8000000%"
    assert MODULE.fmt_score_percent(109_492_151) == "10.9492151%"
