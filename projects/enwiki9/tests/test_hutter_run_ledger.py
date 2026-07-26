from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


TOOL = Path(__file__).resolve().parents[1] / "tools" / "hutter_run_ledger.py"
SPEC = importlib.util.spec_from_file_location("hutter_run_ledger", TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def fixture(tmp_path: Path) -> dict:
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"archive": 90, "gain": 10, "roundtrip": True}))
    return {
        "schema": "enwiki9_hutter_frontier_v1",
        "target": {
            "input_bytes": 1_000_000_000,
            "score_bytes": 109_000_000,
            "required_roundtrip": True,
        },
        "candidates": [
            {
                "id": "candidate",
                "name": "Candidate",
                "rank": 1,
                "status": "active",
                "evidence_tier": "constructive_prefix",
                "scope_bytes": 10_000_000,
                "baseline_archive_bytes": 1_020,
                "archive_bytes": 1_000,
                "program_bytes": 200,
                "forecast_score": 109_400_000,
                "measured_gain_bytes": 20,
                "gain_bytes_per_1m": 2.0,
                "score_credit_bytes": 0,
                "source_paths": ["receipt.json"],
                "additional_runs": [
                    {
                        "run_id": "candidate__1m_prefix",
                        "scope_bytes": 1_000_000,
                        "population": "opening_prefix",
                        "archive_bytes": 90,
                        "measured_gain_bytes": 10,
                        "roundtrip_ok": True,
                        "source_paths": ["receipt.json"],
                        "metric_assertions": [
                            {
                                "source": "receipt.json",
                                "pointer": "/archive",
                                "run_field": "archive_bytes",
                            },
                            {
                                "source": "receipt.json",
                                "pointer": "/gain",
                                "run_field": "measured_gain_bytes",
                            },
                        ],
                    }
                ],
            }
        ],
    }


def test_expands_scopes_and_computes_forecast(tmp_path: Path) -> None:
    ledger, errors = MODULE.build_ledger(tmp_path, fixture(tmp_path))

    assert errors == []
    assert ledger["summary"]["run_count"] == 2
    assert ledger["summary"]["runs_by_scope"] == {"1000000": 1, "10000000": 1}
    primary = next(row for row in ledger["runs"] if row["primary_frontier_run"])
    assert primary["forecast_percent"] == 10.94
    assert primary["forecast_margin_bytes"] == 100_000
    additional = next(row for row in ledger["runs"] if not row["primary_frontier_run"])
    assert additional["population"] == "opening_prefix"
    assert additional["archive_bytes"] == 90


def test_assertion_drift_fails_closed(tmp_path: Path) -> None:
    frontier = fixture(tmp_path)
    frontier["candidates"][0]["additional_runs"][0]["archive_bytes"] = 91

    _, errors = MODULE.build_ledger(tmp_path, frontier)

    assert any("does not match" in error for error in errors)


def test_nonconstructive_score_credit_fails_closed(tmp_path: Path) -> None:
    frontier = fixture(tmp_path)
    candidate = frontier["candidates"][0]
    candidate["evidence_tier"] = "causal_shadow"
    candidate["score_credit_bytes"] = 1

    _, errors = MODULE.build_ledger(tmp_path, frontier)

    assert any("nonconstructive run has score credit" in error for error in errors)


def test_mixed_scope_gain_fails_closed(tmp_path: Path) -> None:
    frontier = fixture(tmp_path)
    frontier["candidates"][0]["measured_gain_bytes"] = 10

    _, errors = MODULE.build_ledger(tmp_path, frontier)

    assert any("archive gain mismatch" in error for error in errors)
    assert any("gain rate mismatch" in error for error in errors)


def test_missing_additional_source_fails_closed(tmp_path: Path) -> None:
    frontier = fixture(tmp_path)
    frontier["candidates"][0]["additional_runs"][0]["source_paths"] = [
        "missing.json"
    ]

    _, errors = MODULE.build_ledger(tmp_path, frontier)

    assert any("missing source missing.json" in error for error in errors)


def test_missing_lineage_parent_fails_closed(tmp_path: Path) -> None:
    frontier = fixture(tmp_path)
    frontier["candidates"][0]["parent_candidate_id"] = "missing"

    _, errors = MODULE.build_ledger(tmp_path, frontier)

    assert any("missing parent candidate missing" in error for error in errors)
