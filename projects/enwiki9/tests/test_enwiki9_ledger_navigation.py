"""Browsing defaults must not erase failures, lineage, or uncertain jobs."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import enwiki9_ledger as ledger


def fixture():
    algorithms = [{"id": cid, "name": cid, "status": status, "kind": "candidate",
                   "parents": [{"id": "retired"}] if cid == "current" else [],
                   "children": [], "sources": [f"programs/{cid}/meta.json"],
                   "run_ids": [], "proposal_ids": [], "notes": [], "coverage": []}
                  for cid, status in [("retired", "measured_negative"),
                                      ("current", "candidate"),
                                      ("uncertain", "retired_gate_failure")]]
    runs = [{"id": rid, "candidate_id": cid, "state": state, "kind": "job",
             "source": f"operations/adaptive/{state}/{rid}.json",
             "liveness": {"state": "unknown"}, "revision": {"path": "bound.json"}}
            for rid, cid, state in [("r4", "uncertain", "running"),
                                    ("r3", "current", "completed"),
                                    ("r2", "current", "failed"),
                                    ("r1", "retired", "completed")]]
    for a in algorithms:
        a["run_ids"] = [r["id"] for r in runs if r["candidate_id"] == a["id"]]
    ledger.project_browsing_state(algorithms, runs)
    return {"algorithms": algorithms, "runs": runs, "proposals": [], "notes": [],
            "mixes": [], "tools": [{"id": "tools/example.py", "candidate_ids": ["current"]}],
            "generated_at": "fixture", "host": "fixture", "issues": []}


def query(data, *arguments):
    parser = argparse.ArgumentParser()
    ledger.record_options(parser)
    return ledger.record_query(data, parser.parse_args(arguments))


def test_default_current_view_preserves_unknown_running_and_parent_links():
    data = fixture()
    result = query(data)
    assert [r["id"] for r in result["records"]] == ["uncertain", "current"]
    assert result["hidden_historical_records"] == 1
    assert result["records"][1]["parents"] == [{"id": "retired"}]
    assert query(data, "--history")["total"] == 3
    assert query(data, "--search", "retired")["total"] == 3  # Includes lineage and recorded failure status.
    assert query(data, "--state", "measured_negative")["records"][0]["id"] == "retired"


def test_latest_results_are_compact_and_all_repeats_remain_retrievable():
    data = fixture()
    result = query(data, "--view", "runs")
    assert [r["id"] for r in result["records"]] == ["r4", "r3"]
    assert result["hidden_historical_records"] == 2
    assert query(data, "--view", "runs", "--history")["total"] == 4
    detail = query(data, "--candidate", "current")
    assert [r["id"] for r in detail["records"]] == ["r3", "r2"]
    assert detail["candidate"]["parents"] == [{"id": "retired"}]
    assert query(data, "--view", "runs", "--state", "failed")["total"] == 1


def test_reviews_remain_visible_for_retired_candidates_and_tools_are_searchable():
    data = fixture()
    review = query(data, "--view", "reviews")
    assert {r["candidate_id"] for r in review["records"]} == {"current", "retired"}
    assert query(data, "--view", "tools", "--candidate", "current")["total"] == 1
    assert query(data, "--view", "tools", "--search", "example")["total"] == 1


def test_browsing_projection_does_not_mutate_scientific_status():
    data = fixture()
    statuses = {a["id"]: a["status"] for a in data["algorithms"]}
    for state in ("pending", "held", "running"):
        data["runs"][0]["state"] = state
        ledger.project_browsing_state(data["algorithms"], data["runs"])
        assert data["algorithms"][2]["browsing_state"] == "current"
    assert {a["id"]: a["status"] for a in data["algorithms"]} == statuses
