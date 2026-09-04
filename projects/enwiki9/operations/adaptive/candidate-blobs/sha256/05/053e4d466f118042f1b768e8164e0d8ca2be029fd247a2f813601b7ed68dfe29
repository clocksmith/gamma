#!/usr/bin/env python3
"""Run the bounded HARM-Delta sparse-input ABI source fixture."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path, PurePosixPath
import resource
import tempfile
from typing import Any

import abi
import fixture


def _load_environment_reference(name: str) -> dict[str, Any]:
    raw = os.environ.get(name)
    if raw is None:
        raise RuntimeError(f"{name} is required")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{name} is not an object")
    return value


def _project_reference(
    project_root: Path, value: object, label: str
) -> tuple[Path, dict[str, str]]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValueError(f"{label} reference is malformed")
    path_text = value["path"]
    digest = value["sha256"]
    if (
        not isinstance(path_text, str)
        or not isinstance(digest, str)
        or not digest.startswith("sha256:")
    ):
        raise ValueError(f"{label} reference fields are malformed")
    relative = PurePosixPath(path_text)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} path is not project-relative")
    path = (project_root / relative).resolve()
    root = project_root.resolve()
    if path == root or root not in path.parents or not path.is_file():
        raise ValueError(f"{label} is not a regular project file")
    if "sha256:" + abi.sha256_path(path) != digest:
        raise ValueError(f"{label} digest differs")
    return path, {"path": path_text, "sha256": digest}


def _candidate_revision() -> dict[str, Any]:
    value = _load_environment_reference("GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON")
    if set(value) != {"candidateId", "candidateTreeSha256", "receipt"}:
        raise ValueError("candidate revision environment fields differ")
    if value["candidateId"] != abi.CANDIDATE_ID:
        raise ValueError("candidate revision identifies another candidate")
    return value


def _experiment(project_root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    reference = _load_environment_reference("GAMMA_ENWIKI9_EXPERIMENT_JSON")
    path, normalized = _project_reference(project_root, reference, "experiment")
    value = json.loads(path.read_text())
    if (
        not isinstance(value, dict)
        or value.get("schema")
        != "gamma.enwiki9.adaptive-experiment-contract.v1"
        or value.get("experimentId") != abi.CANDIDATE_ID
        or value.get("proposalId") != abi.CANDIDATE_ID
        or value.get("evidenceClass") != "infrastructure"
        or value.get("objectiveCreditBytes") != 0
    ):
        raise ValueError("adaptive experiment identity differs")
    return value, normalized


def _predicate_pass(observed: object, operator: str, threshold: object) -> bool:
    operations = {
        "eq": lambda: observed == threshold,
        "gt": lambda: observed > threshold,
        "gte": lambda: observed >= threshold,
        "lt": lambda: observed < threshold,
        "lte": lambda: observed <= threshold,
    }
    if operator not in operations:
        raise ValueError(f"unsupported predicate operator: {operator}")
    return bool(operations[operator]())


def _evaluations(
    predicates: list[dict[str, Any]], measurements: dict[str, object]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for predicate in predicates:
        observed = measurements[predicate["measurement"]]
        rows.append(
            {
                **predicate,
                "observed": observed,
                "passed": _predicate_pass(
                    observed, predicate["operator"], predicate["threshold"]
                ),
            }
        )
    return rows


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _require_empty_output(output_dir: Path, project_root: Path) -> None:
    root = project_root.resolve()
    resolved = output_dir.resolve()
    required = (root / "results" / abi.CANDIDATE_ID).resolve()
    if resolved != required:
        raise ValueError(
            f"output directory must be results/{abi.CANDIDATE_ID}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise FileExistsError("HARM sparse-input result boundary is not empty")


def run_fixture(project_root: Path, output_dir: Path) -> dict[str, object]:
    _require_empty_output(output_dir, project_root)
    candidate_revision = _candidate_revision()
    experiment, experiment_reference = _experiment(project_root)
    with tempfile.TemporaryDirectory(
        prefix="fixture-work-", dir=output_dir
    ) as temporary:
        observed = fixture.run_fixture(project_root, Path(temporary))

    maximum_rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    checks = {
        "harmSourceBindingPass": True,
        "validReplayPass": (
            observed["active_bytes"] == 6
            and observed["sparse_parent_record_count"] == 6
        ),
        "repeatIdentityPass": observed["repeat_identity_pass"],
        "sparseCoveragePass": (
            observed["sparse_parent_record_count"] == 6
            and observed["active_bytes"] == 6
        ),
        "pKIdentityPass": observed["p_k_probability_identity_pass"],
        "eWakePass": observed["e_awake_bytes"] == 3,
        "gOpeningInadmissiblePass": (
            observed["g_awake_bytes"] == 0
            and observed["physical_g_comparator_admissible"] is False
        ),
        "physicalSeedBindingPass": (
            observed["physical_seed_binding"]["record_count"] == 1
        ),
        "negativeControlRejectCount": observed[
            "negative_control_reject_count"
        ],
        "corpusAccessCount": observed["corpus_access_count"],
        "maximumSelfRssKiB": maximum_rss,
    }
    source_closure = bool(
        all(
            checks[key] is True
            for key in (
                "harmSourceBindingPass",
                "validReplayPass",
                "repeatIdentityPass",
                "sparseCoveragePass",
                "pKIdentityPass",
                "eWakePass",
                "gOpeningInadmissiblePass",
                "physicalSeedBindingPass",
            )
        )
        and checks["negativeControlRejectCount"] == 10
        and checks["corpusAccessCount"] == 0
        and checks["maximumSelfRssKiB"] <= 262144
    )
    measurements: dict[str, object] = {
        "sourceClosurePass": source_closure,
        **checks,
    }

    evidence = {
        **observed,
        "candidate_revision": candidate_revision,
        "experiment": experiment_reference,
        "measurements": measurements,
        "hsp1": {
            "magic": "HSP1",
            "version": abi.HSP1_VERSION,
            "header_bytes": abi.HSP1_HEADER_BYTES,
            "record_bytes": abi.HSP1_RECORD.size,
            "probability_scale": 65536,
        },
        "hgs1": {
            "magic": "HGS1",
            "version": abi.HGS1_VERSION,
            "header_bytes": abi.HGS1_HEADER_BYTES,
            "record_bytes": abi.HGS1_RECORD.size,
        },
        "authority": {
            "archive_authority": False,
            "retained_parent_gain_authority": False,
            "corpus_execution_authority": False,
            "objective_credit_bytes": 0,
        },
    }
    evidence_path = output_dir / "fixture-evidence.json"
    _write_json(evidence_path, evidence)

    promotion = _evaluations(
        experiment["promotionPredicates"], measurements
    )
    kill = _evaluations(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    if promotion_pass and kill_pass:
        raise AssertionError("promotion and kill both passed")
    decision = (
        "authorize-successor"
        if promotion_pass
        else "retire"
        if kill_pass
        else "retry"
    )
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": experiment["objective"],
        "experiment": experiment_reference,
        "candidateId": abi.CANDIDATE_ID,
        "candidateRevision": candidate_revision,
        "evidenceClass": "infrastructure",
        "objectiveCreditBytes": 0,
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "promotionPass": promotion_pass,
        "killPass": kill_pass,
        "decision": decision,
        "artifacts": [
            {
                "id": "fixture-evidence",
                "path": evidence_path.relative_to(project_root).as_posix(),
                "sha256": "sha256:" + abi.sha256_path(evidence_path),
            }
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
    }
    decision_path = output_dir / "decision.json"
    _write_json(decision_path, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true", required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_fixture(args.project_root.resolve(), args.output_dir.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["promotionPass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
