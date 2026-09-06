"""Browsing defaults must not erase failures, lineage, or uncertain jobs."""

import argparse
import json
from pathlib import Path
import subprocess
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


def reflected_fixture(root, reflections):
    """Build the actual projection from isolated canonical record fixtures."""
    def write(path, value):
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(value))

    write("programs/example/meta.json", {"id": "example", "status": "measured_negative"})
    for number, reflection in enumerate(reflections, 1):
        job_id = f"job{number}"
        source = f"operations/adaptive/completed/{job_id}.json"
        write(source, {"job_id": job_id, "candidate_id": "example", "state": "completed",
                       "gate_size": number * 1000, "finished_at": f"2026-09-0{number}"})
        if reflection is not None:
            write(f"operations/adaptive/reflections/{job_id}.json",
                  {**reflection, "job": {"path": source}})
    return ledger.build(root)


def test_reflection_only_terms_find_runs_and_candidates(tmp_path):
    data = reflected_fixture(tmp_path, [{
        "validity": {"valid": True, "classification": "valid"},
        "hypothesis": {"verdict": "supported"},
        "knowledge": {"transferableLessons": ["amortization evidence"],
                      "retiredDimensions": ["singleton configurations"],
                      "uncertainties": ["distant transfer"]},
        "attribution": {"localizedCause": "selector overhead", "failureClass": "weak-compression"},
        "decision": {"verdict": "mutate", "rationale": "test shared arguments", "nextGateBytes": 250000},
    }])
    for term in ("amortization", "singleton", "distant", "selector", "shared arguments"):
        result = query(data, "--view", "runs", "--search", term)
        assert [row["id"] for row in result["records"]] == ["job1"]
        assert "does not validate" in result["reflection_authority"]
        candidates = query(data, "--search", term)
        assert [row["id"] for row in candidates["records"]] == ["example"]
        assert candidates["records"][0]["reflection_count"] == 1
    run = result["records"][0]
    assert run["next_action"]["next_gate_bytes"] == 250000
    assert run["failure_class"] == "weak-compression"
    assert run["reflection_path"] == "operations/adaptive/reflections/job1.json"


def test_reflection_history_and_pagination_preserve_invalid_claims(tmp_path):
    reflections = [{
        "validity": {"valid": valid, "classification": classification},
        "hypothesis": {"verdict": verdict},
        "knowledge": {"transferableLessons": [f"calibration lesson {number}"]},
        "decision": {"verdict": "hold", "rationale": "inspect evidence"},
    } for number, valid, classification, verdict in (
        (1, True, "valid", "supported"), (2, False, "invalid", "inconclusive"),
        (3, False, "unknown", "unreviewed"))]
    data = reflected_fixture(tmp_path, reflections)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*.json")}
    pages = [query(data, "--view", "runs", "--search", "calibration", "--limit", "1",
                   "--offset", str(offset)) for offset in range(3)]
    assert [page["records"][0]["id"] for page in pages] == ["job3", "job2", "job1"]
    assert [page["next_offset"] for page in pages] == [1, 2, None]
    assert all(page["total"] == 3 for page in pages)
    detail = query(data, "--candidate", "example", "--limit", "1")
    history = detail["candidate"]["reflections"]
    assert [row["run_id"] for row in history] == ["job3", "job2", "job1"]
    assert [row["validity"] for row in history] == ["unknown", "invalid", "valid"]
    assert [row["hypothesis"] for row in history] == ["unreviewed", "inconclusive", "supported"]
    assert [row["scope"]["value"] for row in history] == [3000, 2000, 1000]
    assert history[1]["source"] == "operations/adaptive/reflections/job2.json"
    assert detail["candidate"]["status"] == "measured_negative"
    assert {p: p.read_bytes() for p in before} == before


def test_missing_reflection_fields_remain_missing_and_unreviewed(tmp_path):
    data = reflected_fixture(tmp_path, [None, {"knowledge": None, "attribution": None,
                                             "decision": None}])
    detail = query(data, "--candidate", "example")
    assert len(detail["candidate"]["reflections"]) == 1
    for run in detail["records"]:
        assert run["lessons"] == run["retired_dimensions"] == run["uncertainties"] == []
        assert run["localized_cause"] == run["failure_class"] == ""
        assert run["next_action"] == {"verdict": None, "rationale": "", "next_gate_bytes": None}
        assert run["validity"] == run["hypothesis"] == run["outcome"] == "unreviewed"
    assert query(data, "--view", "runs", "--search", "unreviewed", "--limit", "1")["total"] == 2


def test_malformed_optional_reflection_fields_report_source_issues(tmp_path):
    data = reflected_fixture(tmp_path, [{
        "knowledge": "unexpected string", "attribution": ["unexpected list"],
        "validity": {"valid": False, "classification": "invalid"},
        "hypothesis": {"verdict": "inconclusive"},
    }])
    detail = query(data, "--candidate", "example")
    run = detail["records"][0]
    assert run["lessons"] == run["retired_dimensions"] == run["uncertainties"] == []
    assert run["localized_cause"] == run["failure_class"] == ""
    assert run["validity"] == "invalid" and run["hypothesis"] == "inconclusive"
    assert detail["candidate"]["status"] == "measured_negative"
    issues = detail["source_issues"]
    assert len(issues) == 2
    assert all(issue["path"] == "operations/adaptive/reflections/job1.json" for issue in issues)
    assert any("knowledge must be an object" in issue["reason"] for issue in issues)
    assert any("attribution must be an object" in issue["reason"] for issue in issues)


def test_browser_run_details_show_recorded_learning_without_validation():
    template = (ledger.ROOT / "tools/enwiki9_ledger.html").read_text()
    helpers = template.split("    const node =", 1)[1].split("    let data;", 1)[0]
    cards = template.split("    const appendFact =", 1)[1].split("    const metricsNotice =", 1)[0]
    # Execute the actual card renderer with a DOM fixture; no browser dependency.
    script = r'''
const assert = require('node:assert/strict');
class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.textContent = ''; this.classList = {add() {}}; }
  append(...children) { this.children.push(...children); }
  get childNodes() { return this.children; }
  set innerHTML(value) { throw Error('Reflection strings must remain text'); }
}
const document = {createElement: tag => new Element(tag)};
''' + "const node =" + helpers + r'''
const algorithmLink = id => node('a', id);
const scopeText = scope => String(scope.value);
const isActive = () => false;
''' + "const appendFact =" + cards + r'''
const run = {candidate_id:'example', id:'job1', kind:'job', state:'completed',
  scope:{value:1000}, validity:'invalid', hypothesis:'inconclusive', outcome:'hold',
  reflection_path:'operations/adaptive/reflections/job1.json',
  lessons:['literal <b>scaffolding</b>'], localized_cause:'dictionary overhead',
  retired_dimensions:['this configuration'], uncertainties:['transfer unknown'],
  failure_class:'weak-compression', next_action:{verdict:'hold', rationale:'inspect costs', next_gate_bytes:250000},
  links:[{label:'Reflection', path:'operations/adaptive/reflections/job1.json'}]};
const flatten = element => [element, ...element.children.flatMap(flatten)];
const elements = flatten(runCard(run));
const strings = elements.map(element => element.textContent);
for (const expected of ['invalid', 'inconclusive', 'literal <b>scaffolding</b>',
                       'dictionary overhead', 'this configuration', 'transfer unknown',
                       'inspect costs', '250,000']) assert(strings.includes(expected), expected);
assert(strings.some(value => value.includes('Browsing does not validate')));
assert(elements.some(element => element.href === '../operations/adaptive/reflections/job1.json'));
assert(!elements.some(element => element.tag === 'b'));
const missing = flatten(runCard({candidate_id:'example', id:'job2', scope:{value:1000}}));
assert(!missing.some(element => element.textContent === 'Recorded learning'));
'''
    completed = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=15)
    assert completed.returncode == 0, completed.stdout + completed.stderr
