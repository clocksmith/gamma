#!/usr/bin/env python3
"""Finalize complete exact-forward evidence in the comparator population unit."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_ggml_postupdate_forward_parity_64_q1_retry_v2"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_ggml_postupdate_forward_parity_64_q1_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_OPEN_SOURCE = PARENT_RESULT / "ggml_profile_forward_source_closure.tar.xz"
PARENT_INCREMENTAL_SOURCE = PARENT_RESULT / "incremental_source.tar.xz"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_ggml_postupdate_forward_parity_64_q1_retry_v1.json"
)
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T021035Z_f751ae43e8.json"
)
SEQUENTIAL_COMPARATOR = ROOT / "tools/nncp_ggml_profile_forward_parity_64_qm2.py"
MATERIALIZER = (
    ROOT / "tools/nncp_ggml_postupdate_forward_parity_64_q1_retry_v2_materializer.py"
)
SOURCE_CEILING = 2_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"reference is not a project file: {path}")
    value = {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }
    if identifier is not None:
        value["id"] = identifier
    return value


def evaluate(
    predicates: list[dict[str, Any]], measurements: dict[str, bool | int | float]
) -> list[dict[str, Any]]:
    operations = {
        "eq": lambda value, threshold: value == threshold,
        "gt": lambda value, threshold: value > threshold,
        "lte": lambda value, threshold: value <= threshold,
    }
    return [
        {
            **predicate,
            "observed": measurements[predicate["measurement"]],
            "passed": bool(
                operations[predicate["operator"]](
                    measurements[predicate["measurement"]], predicate["threshold"]
                )
            ),
        }
        for predicate in predicates
    ]


def require_inputs(experiment: dict[str, Any]) -> dict[str, Any]:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    for identifier, path in (
        ("parent-forward-result", PARENT_DECISION),
        ("parent-forward-execution", PARENT_EXECUTION),
        ("parent-forward-open-source", PARENT_OPEN_SOURCE),
        ("parent-forward-incremental-source", PARENT_INCREMENTAL_SOURCE),
        ("parent-forward-guard", PARENT_GUARD),
        ("parent-forward-reflection", PARENT_REFLECTION),
        ("parent-forward-experiment", PARENT_EXPERIMENT),
        ("promoted-sequential-comparator", SEQUENTIAL_COMPARATOR),
    ):
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    research_contracts.validate_artifact(PARENT_DECISION)
    parent = json.loads(PARENT_DECISION.read_text())
    execution = json.loads(PARENT_EXECUTION.read_text())
    guard = json.loads(PARENT_GUARD.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    parent_experiment = json.loads(PARENT_EXPERIMENT.read_text())
    failed_promotions = [
        row["measurement"] for row in parent["promotionPredicates"] if not row["passed"]
    ]
    parent_inputs = {item["path"]: item for item in parent_experiment["inputs"]}
    comparator_reference = reference(SEQUENTIAL_COMPARATOR)
    if not (
        parent["candidateId"] == PARENT_ID
        and parent["decision"] == "retry"
        and parent["promotionPass"] is False
        and parent["killPass"] is False
        and failed_promotions == ["fixtureComplete"]
        and parent["measurements"]["fixtureComplete"] is False
        and parent["measurements"]["comparedTensorCount"] == 244
        and parent["measurements"]["maximumTensorAbsoluteError"] == 0
        and parent["measurements"]["maximumRepeatTensorAbsoluteError"] == 0
        and parent["measurements"]["branchRows"] == 896
        and parent["measurements"]["maximumBranchCountDifference"] == 0
        and parent["measurements"]["repeatMaximumBranchCountDifference"] == 0
        and parent["measurements"]["topologyDisagreementCount"] == 0
        and parent["measurements"]["truthPathDisagreementCount"] == 0
        and parent["measurements"]["openForwardDeterministic"] is True
        and parent["measurements"]["forbiddenDynamicDependencyCount"] == 0
        and parent["measurements"]["guardedWorkRootPass"] is True
        and all(
            receipt["returncode"] == 0
            for receipt in execution.values()
        )
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and reflection["validity"]["classification"] == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
        and "15616" in reflection["validity"]["reasons"][0]
        and parent_inputs.get(comparator_reference["path"], {}).get("sha256")
        == comparator_reference["sha256"]
    ):
        raise ValueError("population-finalization antecedents are not satisfied")
    expected_artifacts = {item["id"]: item for item in parent["artifacts"]}
    for identifier, path in (
        ("execution", PARENT_EXECUTION),
        ("open-source-package", PARENT_OPEN_SOURCE),
        ("incremental-source-package", PARENT_INCREMENTAL_SOURCE),
    ):
        if expected_artifacts.get(identifier) != reference(path, identifier):
            raise ValueError(f"parent forward artifact drifted: {identifier}")
    return parent


def source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = [
        *local_source_closure((Path(__file__), MATERIALIZER)),
        (PROGRAM / "program.py").resolve(),
    ]
    members = sorted(set(members), key=lambda item: item.relative_to(ROOT).as_posix())
    declared = {item["path"]: item for item in experiment["inputs"]}
    for member in members:
        expected = declared.get(member.relative_to(ROOT).as_posix())
        if expected is None or expected != reference(member, expected["id"]):
            raise ValueError(f"runtime source closure drifted: {member}")
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(ROOT).as_posix()
            )
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    compressed = lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    tar_path.unlink()
    if len(compressed) > SOURCE_CEILING:
        raise ValueError("population-finalizer source closure exceeds its ceiling")
    path.write_bytes(compressed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    experiment_path = args.experiment.resolve()
    output = args.output.resolve()
    research_contracts.validate_artifact(experiment_path)
    experiment = json.loads(experiment_path.read_text())
    if experiment["proposalId"] != CANDIDATE_ID:
        raise ValueError("experiment identifies another candidate")
    if reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and tool experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    parent = require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("population-finalization result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("candidate work root was not freshly materialized")

    execution = RESULT / "execution.json"
    open_source = RESULT / "ggml_profile_forward_source_closure.tar.xz"
    shutil.copyfile(PARENT_EXECUTION, execution)
    shutil.copyfile(PARENT_OPEN_SOURCE, open_source)
    incremental = RESULT / "incremental_source.tar.xz"
    source_package(incremental, experiment)
    shutil.rmtree(WORK)

    measurements = dict(parent["measurements"])
    measurements["fixtureComplete"] = measurements["comparedTensorCount"] == 244
    measurements["incrementalSourceBytes"] = incremental.stat().st_size
    measurements["guardedWorkRootPass"] = not WORK.exists()
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    if not all(row["passed"] for row in promotion) or all(
        row["passed"] for row in kill
    ):
        raise ValueError("retained exact-forward measurements fail frozen predicates")
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": reference(experiment_path),
        "candidateId": CANDIDATE_ID,
        "candidateRevision": candidate_revision,
        "evidenceClass": experiment["evidenceClass"],
        "objectiveCreditBytes": 0,
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "promotionPass": True,
        "killPass": False,
        "decision": "authorize-successor",
        "artifacts": [
            reference(execution, "execution"),
            reference(open_source, "open-source-package"),
            reference(incremental, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
