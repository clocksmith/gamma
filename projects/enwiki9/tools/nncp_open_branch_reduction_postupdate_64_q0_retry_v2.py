#!/usr/bin/env python3
"""Finalize complete branch attribution with the shared result vocabulary."""

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
CANDIDATE_ID = "nncp_open_branch_reduction_postupdate_64_q0_retry_v2"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_branch_reduction_postupdate_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_REPLAY = PARENT_RESULT / "replay.json"
PARENT_EXTRACTION = PARENT_RESULT / "selective-extraction.json"
PARENT_BUILD = PARENT_RESULT / "build-receipt.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T015325Z_b49b5c80ad.json"
)
MATERIALIZER = (
    ROOT / "tools/nncp_open_branch_reduction_postupdate_64_q0_retry_v2_materializer.py"
)
SOURCE_CEILING = 250_000


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


def require_inputs(experiment: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    for identifier, path in (
        ("invalid-parent-result", PARENT_DECISION),
        ("parent-finalization-reflection", PARENT_REFLECTION),
        ("parent-replay", PARENT_REPLAY),
        ("parent-selective-extraction", PARENT_EXTRACTION),
        ("parent-build-receipt", PARENT_BUILD),
        ("parent-guard", PARENT_GUARD),
    ):
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    if not (
        parent["candidateId"] == PARENT_ID
        and parent["decision"] == "authorize-exact-reducer-integration"
        and parent["promotionPass"] is True
        and parent["killPass"] is False
        and all(row["passed"] for row in parent["promotionPredicates"])
        and parent["measurements"]["probabilityTensorCount"] == 64
        and parent["measurements"]["branchRows"] == 896
        and parent["measurements"]["scalarMismatchCount"] == 19
        and parent["measurements"]["scalarMaximumDifference"] == 2
        and parent["measurements"]["exactMismatchCount"] == 0
        and parent["measurements"]["exactMaximumDifference"] == 0
        and parent["measurements"]["deterministicReplay"] is True
        and reflection["validity"]["classification"] == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
        and "authorize-exact-reducer-integration"
        in reflection["attribution"]["localizedCause"]
    ):
        raise ValueError("schema-finalization antecedents are not satisfied")
    expected_artifacts = {
        item["id"]: item for item in parent["artifacts"]
    }
    for identifier, path in (
        ("selective-extraction", PARENT_EXTRACTION),
        ("build-receipt", PARENT_BUILD),
        ("attribution-replay", PARENT_REPLAY),
        ("incremental-source-package", PARENT_RESULT / "incremental_source.tar.xz"),
    ):
        if expected_artifacts.get(identifier) != reference(path, identifier):
            raise ValueError(f"parent result artifact drifted: {identifier}")
    return parent, reflection


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
        raise ValueError("schema-finalizer source closure exceeds its frozen ceiling")
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
    parent, reflection = require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("schema-finalization result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("candidate work root was not freshly materialized")

    replay = RESULT / "replay.json"
    extraction = RESULT / "selective-extraction.json"
    shutil.copyfile(PARENT_REPLAY, replay)
    shutil.copyfile(PARENT_EXTRACTION, extraction)
    finalization = RESULT / "build-receipt.json"
    finalization.write_text(
        json.dumps(
            {
                "schema": "gamma.enwiki9.retained-control-finalization.v1",
                "candidateId": CANDIDATE_ID,
                "scientificControlsRecomputed": False,
                "reason": "Parent controls completed; only the result decision enum was invalid.",
                "parentResult": reference(PARENT_DECISION),
                "parentReflection": reference(PARENT_REFLECTION),
                "parentBuild": reference(PARENT_BUILD),
                "parentGuard": reference(PARENT_GUARD),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    source = RESULT / "incremental_source.tar.xz"
    source_package(source, experiment)
    shutil.rmtree(WORK)

    measurements = dict(parent["measurements"])
    measurements["incrementalSourceBytes"] = source.stat().st_size
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    if not promotion_pass or kill_pass:
        raise ValueError("retained measurements do not satisfy the frozen predicates")
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
            reference(extraction, "selective-extraction"),
            reference(finalization, "build-receipt"),
            reference(replay, "attribution-replay"),
            reference(source, "incremental-source-package"),
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
