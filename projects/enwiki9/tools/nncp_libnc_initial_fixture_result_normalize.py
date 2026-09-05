"""Normalize the legacy initializer verdict without altering measured evidence."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
from pathlib import Path
import struct

import enwiki9_candidate_revisions as revisions
import enwiki9_reflections as reflections
import nncp_libnc_profile_initial_fixture_65536_q0 as fixture_tool
import research_contracts as contracts

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = "nncp_libnc_profile_initial_fixture_65536_closurefix_q0_v1"


def reference(path: Path, name: str | None = None) -> dict:
    return fixture_tool.reference(path, name)


def normalize(job_id: str) -> Path:
    job_path, job = reflections.terminal_job(job_id)
    contracts.validate_artifact(job_path)
    revisions.verify_job_binding(job)
    if job["candidate_id"] != CANDIDATE or job["state"] != "completed" or job["returncode"] != 0:
        raise ValueError("normalizer requires the exact completed initializer")
    root = ROOT / "results" / CANDIDATE
    raw_path = root / "decision.json"
    output = root / "decision.canonical.json"
    provenance_path = root / "decision-normalization.json"
    if output.exists() or provenance_path.exists():
        raise FileExistsError("normalization outputs already exist")
    raw_binding = reference(raw_path)
    raw = json.loads(raw_path.read_text())
    if (raw.get("decision") != "authorize-integrated-replay" or raw.get("promotionPass") is not True
            or raw.get("killPass") is not False or raw.get("objectiveCreditBytes") != 0
            or raw.get("evidenceClass") != "oracle" or raw.get("candidateId") != CANDIDATE
            or raw.get("experiment") != job["experiment"]
            or raw.get("candidateRevision", {}).get("candidateTreeSha256") != job["candidate_tree_sha256"]):
        raise ValueError("raw initializer outcome or job binding differs")
    for item in raw["artifacts"]:
        if reference(ROOT / item["path"], item["id"]) != item:
            raise ValueError("raw initializer artifact changed")
    manifest_path = root / "fixture-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if (fixture_tool.directory_manifest(root / "fixture") != manifest["fixture"]
            or manifest["fixture"] != manifest["repeatFixture"]
            or len(manifest["executions"]) != 2
            or any(row["returncode"] != 0 for row in manifest["executions"])):
        raise ValueError("retained fixture or recorded exact repeat differs")
    symbols = [value[0] for value in struct.iter_unpack(
        ">H", (root / "fixture/symbols_65536.be16").read_bytes())]
    validation = fixture_tool.validate_fixture(root / "fixture", symbols)
    if validation != manifest["validation"]:
        raise ValueError("raw initialization topology or boundary differs")
    if (root / "scratch").exists() or (root / "fixture-repeat").exists():
        raise ValueError("initializer cleanup is incomplete")
    resources = job["execution_resources"]
    outer_path = ROOT / resources["guard_path"]
    outer = json.loads(outer_path.read_text())
    legacy_guard_path = root / "guard.json"
    legacy_guard = json.loads(legacy_guard_path.read_text())
    if (resources.get("cleanup_complete") is not True
            or Path(resources["cgroup_path"]).exists()
            or outer.get("status") != "complete" or outer.get("returncode") != 0
            or any(outer["guards"].values()) or not all(outer["measurements"].values())
            or any(outer["cgroup_events"]["delta"].values())
            or legacy_guard.get("status") != "complete" or legacy_guard.get("returncode") != 0):
        raise ValueError("terminal resource or cleanup evidence is incomplete")
    provenance = {
        "schema": "gamma.enwiki9.initializer-result-normalization.v1",
        "candidateId": CANDIDATE, "job": reference(job_path), "rawResult": raw_binding,
        "normalizer": reference(Path(__file__)), "runner": job["runner"],
        "sourceRevision": job["candidate_revision"], "experiment": job["experiment"],
        "outerGuard": reference(outer_path), "legacyGuard": reference(legacy_guard_path),
        "verdictMapping": {"authorize-integrated-replay": "authorize-successor"},
        "unchanged": "All measured values, predicates, candidate/source/population bindings and raw result bytes.",
        "boundary": "Successor authority is limited here to a new pre-forward open-consumer input/state parity gate. The complete integrated replay retains its own input lock and no larger gate is authorized.",
        "objectiveCreditBytes": 0, "scopeSymbols": 65536, "scopeBytes": None,
        "rawValidation": validation, "retainedFixtureHashesVerified": True,
        "repeat": "Two recorded fresh-process manifests are identical; only the first raw fixture remains locally.",
        "generatedUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    canonical = copy.deepcopy(raw)
    canonical["decision"] = "authorize-successor"
    canonical["artifacts"] += [reference(raw_path, "raw-initializer-result"),
                               reference(job_path, "terminal-job"),
                               reference(provenance_path, "normalization-provenance")]
    output.write_text(json.dumps(canonical, indent=2, sort_keys=True) + "\n")
    contracts.validate_artifact(output)
    if reference(raw_path) != raw_binding:
        raise ValueError("raw result changed during normalization")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    print(json.dumps(reference(normalize(args.job)), indent=2))
