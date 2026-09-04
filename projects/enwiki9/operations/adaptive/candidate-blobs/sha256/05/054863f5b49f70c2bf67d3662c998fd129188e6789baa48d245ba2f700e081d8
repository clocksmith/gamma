#!/usr/bin/env python3
"""Run the generated HARM-Delta scope-coordinate mapper fixture."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import tempfile
from typing import Any

import fixture


CANDIDATE_ID = "harm_delta_scope_coordinate_mapper_q0_v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _environment_json(name: str) -> dict[str, Any]:
    raw = os.environ.get(name)
    if raw is None:
        raise RuntimeError(f"{name} is required")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{name} is not an object")
    return value


def _reference(project_root: Path, value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValueError(f"{label} reference differs")
    path_text = value["path"]
    digest = value["sha256"]
    if not isinstance(path_text, str) or not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise ValueError(f"{label} reference fields differ")
    relative = PurePosixPath(path_text)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} path is unsafe")
    path = (project_root / relative).resolve()
    if project_root.resolve() not in path.parents or not path.is_file():
        raise ValueError(f"{label} path is not a project file")
    if "sha256:" + _sha256(path) != digest:
        raise ValueError(f"{label} digest differs")
    return {"path": path_text, "sha256": digest}


def _predicate(observed: object, operator: str, threshold: object) -> bool:
    operations = {
        "eq": lambda: observed == threshold,
        "gt": lambda: observed > threshold,
        "gte": lambda: observed >= threshold,
        "lt": lambda: observed < threshold,
        "lte": lambda: observed <= threshold,
    }
    if operator not in operations:
        raise ValueError(f"unsupported predicate operator {operator}")
    return bool(operations[operator]())


def _evaluations(rows: list[dict[str, Any]], measurements: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            **row,
            "observed": measurements[row["measurement"]],
            "passed": _predicate(
                measurements[row["measurement"]], row["operator"], row["threshold"]
            ),
        }
        for row in rows
    ]


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(project_root: Path, output_dir: Path) -> dict[str, object]:
    required_output = (project_root / "results" / CANDIDATE_ID).resolve()
    if output_dir.resolve() != required_output:
        raise ValueError(f"output must be results/{CANDIDATE_ID}")
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise FileExistsError("scope-coordinate mapper result boundary is not empty")
    revision = _environment_json("GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON")
    if revision.get("candidateId") != CANDIDATE_ID:
        raise ValueError("candidate revision identity differs")
    experiment_reference = _reference(
        project_root,
        _environment_json("GAMMA_ENWIKI9_EXPERIMENT_JSON"),
        "experiment",
    )
    experiment = json.loads((project_root / experiment_reference["path"]).read_text())
    if (
        experiment.get("experimentId") != CANDIDATE_ID
        or experiment.get("proposalId") != CANDIDATE_ID
        or experiment.get("evidenceClass") != "infrastructure"
        or experiment.get("objectiveCreditBytes") != 0
    ):
        raise ValueError("experiment identity or authority differs")

    with tempfile.TemporaryDirectory(prefix="fixture-", dir=output_dir) as temporary:
        observed = fixture.run_fixture(project_root, Path(temporary) / "generated")
    maximum_rss = max(
        int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        int(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss),
    )
    measurements: dict[str, object] = {
        "nativeReferenceIdentityPass": observed["native_reference_identity_pass"],
        "repeatIdentityPass": observed["repeat_identity_pass"],
        "boundaryLowerBoundPass": observed["boundary_lower_bound_pass"],
        "frontendStateDigestPass": observed["frontend_state_digest_pass"],
        "mappingTranscriptDigestPass": observed["mapping_transcript_digest_pass"],
        "productionConfigClosurePass": observed["production_config_closure_pass"],
        "negativeControlRejectCount": observed["negative_control_reject_count"],
        "boundaryCount": observed["boundary_count"],
        "corpusAccessCount": observed["corpus_access_count"],
        "activeTraceAccessCount": observed["active_trace_access_count"],
        "maximumSelfRssKiB": maximum_rss,
    }
    boolean_measurements = (
        "nativeReferenceIdentityPass",
        "repeatIdentityPass",
        "boundaryLowerBoundPass",
        "frontendStateDigestPass",
        "mappingTranscriptDigestPass",
        "productionConfigClosurePass",
    )
    source_closure = bool(
        all(measurements[key] is True for key in boolean_measurements)
        and measurements["negativeControlRejectCount"] == 8
        and measurements["boundaryCount"] == 7
        and measurements["corpusAccessCount"] == 0
        and measurements["activeTraceAccessCount"] == 0
        and measurements["maximumSelfRssKiB"] <= 262144
    )
    measurements = {"sourceClosurePass": source_closure, **measurements}
    evidence = {
        **observed,
        "candidate_revision": revision,
        "experiment": experiment_reference,
        "measurements": measurements,
        "authority": {
            "archive_authority": False,
            "retained_parent_gain_authority": False,
            "native_integration_authority": False,
            "corpus_execution_authority": False,
            "objective_credit_bytes": 0,
        },
    }
    evidence_path = output_dir / "fixture-evidence.json"
    _write_json(evidence_path, evidence)
    promotion = _evaluations(experiment["promotionPredicates"], measurements)
    kill = _evaluations(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    if promotion_pass and kill_pass:
        raise AssertionError("promotion and kill predicates both pass")
    decision = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": experiment["objective"],
        "experiment": experiment_reference,
        "candidateId": CANDIDATE_ID,
        "candidateRevision": revision,
        "evidenceClass": "infrastructure",
        "objectiveCreditBytes": 0,
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "promotionPass": promotion_pass,
        "killPass": kill_pass,
        "decision": "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry",
        "artifacts": [
            {
                "id": "fixture-evidence",
                "path": evidence_path.relative_to(project_root).as_posix(),
                "sha256": "sha256:" + _sha256(evidence_path),
            }
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _write_json(output_dir / "decision.json", decision)
    return decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true", required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    decision = run(args.project_root.resolve(), args.output_dir.resolve())
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["promotionPass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
