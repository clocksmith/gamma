#!/usr/bin/env python3
"""Attribute the post-update branch mismatch to floating reduction order."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import time
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_branch_reduction_postupdate_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
FIXTURE_PACKAGE = ROOT / (
    "results/nncp_ggml_postupdate_forward_parity_64_q0_retry_v2/"
    "artifacts/production_forward_fixture.tar.xz"
)
LEGACY_DECISION = ROOT / (
    "results/nncp_ggml_postupdate_forward_parity_64_q0_retry_v2/"
    "artifacts/decision.json"
)
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T012011Z_35b4885e21.json"
)
Q1_DECISION = ROOT / "results/nncp_ggml_profile_arithmetic_64_q1_v1/decision.json"
FAILED_ATTRIBUTION_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T014708Z_6572106ab8.json"
)
SOURCE_CEILING = 250_000
OUTPUT_PATTERN = re.compile(r"(?:\./)?internal/[0-9]{5}_output\.f32")


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


def execute(command: list[str], cwd: Path) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    receipt = {
        "command": command,
        "elapsedSeconds": time.monotonic() - started,
        "returncode": completed.returncode,
        "stdout": completed.stdout.decode(errors="replace"),
        "stderr": completed.stderr.decode(errors="replace"),
    }
    if completed.returncode:
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt


def selective_extract(destination: Path) -> dict[str, Any]:
    destination.mkdir()
    internal = destination / "internal"
    internal.mkdir()
    rows: list[dict[str, Any]] = []
    with tarfile.open(FIXTURE_PACKAGE, "r:xz") as archive:
        for member in archive:
            wanted = OUTPUT_PATTERN.fullmatch(member.name) or member.name in {
                "./tree_path.u32le",
                "tree_path.u32le",
            }
            if not wanted:
                continue
            source = archive.extractfile(member)
            if source is None or not member.isfile():
                raise ValueError(f"fixture member is not a regular file: {member.name}")
            name = Path(member.name).name
            target = internal / name if name.endswith("_output.f32") else destination / name
            with target.open("wb") as output:
                shutil.copyfileobj(source, output, 1 << 20)
            rows.append(
                {
                    "member": member.name,
                    "bytes": target.stat().st_size,
                    "sha256": f"sha256:{sha256(target)}",
                }
            )
    tensor_count = sum(row["member"].endswith("_output.f32") for row in rows)
    if tensor_count != 64 or len(rows) != 65:
        raise ValueError("selective fixture extraction is incomplete")
    return {
        "schema": "gamma.enwiki9.selective-fixture-extraction.v1",
        "source": reference(FIXTURE_PACKAGE),
        "tensorCount": tensor_count,
        "members": rows,
    }


def source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = [
        *local_source_closure((Path(__file__),)),
        (PROGRAM / "CMakeLists.txt").resolve(),
        (PROGRAM / "branch_reduction.cpp").resolve(),
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
        raise ValueError("branch-attribution source closure exceeds its frozen ceiling")
    path.write_bytes(compressed)


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


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    for identifier, path in (
        ("retained-postupdate-fixture", FIXTURE_PACKAGE),
        ("legacy-postupdate-forward-decision", LEGACY_DECISION),
        ("parent-reflection", PARENT_REFLECTION),
        ("prior-exact-arithmetic-decision", Q1_DECISION),
        ("failed-attribution-reflection", FAILED_ATTRIBUTION_REFLECTION),
    ):
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    legacy = json.loads(LEGACY_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    q1 = json.loads(Q1_DECISION.read_text())
    failed_attribution = json.loads(FAILED_ATTRIBUTION_REFLECTION.read_text())
    if not (
        legacy["maximum_tensor_absolute_error"] == 0
        and legacy["branch_comparison"][
            "maximum_integer_probability_count_difference"
        ]
        == 2
        and reflection["decision"]["verdict"] == "retry"
        and q1["promotionPass"] is True
        and q1["measurements"]["maximumProbabilityCountDifference"] == 0
        and failed_attribution["validity"]["classification"]
        == "implementation-failure"
        and failed_attribution["hypothesis"]["verdict"] == "not-tested"
        and failed_attribution["decision"]["verdict"] == "retry"
    ):
        raise ValueError("branch-attribution antecedents are not satisfied")


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
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("branch-attribution result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("candidate work root was not freshly materialized")

    fixture = WORK / "fixture"
    extraction = selective_extract(fixture)
    extraction_path = RESULT / "selective-extraction.json"
    extraction_path.write_text(json.dumps(extraction, indent=2, sort_keys=True) + "\n")
    build = WORK / "build"
    build_receipt = execute(
        ["cmake", "-S", str(PROGRAM), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"],
        ROOT,
    )
    build_receipt["compile"] = execute(
        ["cmake", "--build", str(build), "--parallel", "2"], ROOT
    )
    executable = build / "nncp_open_branch_reduction_postupdate"
    run1 = execute([str(executable), str(fixture)], ROOT)
    run2 = execute([str(executable), str(fixture)], ROOT)
    report1 = json.loads(run1["stdout"])
    report2 = json.loads(run2["stdout"])
    build_receipt_path = RESULT / "build-receipt.json"
    build_receipt_path.write_text(
        json.dumps(build_receipt, indent=2, sort_keys=True) + "\n"
    )
    replay_path = RESULT / "replay.json"
    replay_path.write_text(json.dumps(report1, indent=2, sort_keys=True) + "\n")
    source_path = RESULT / "incremental_source.tar.xz"
    source_package(source_path, experiment)
    shutil.rmtree(WORK)

    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "probabilityTensorCount": report1["probabilityTensorCount"],
        "branchRows": report1["branchRows"],
        "scalarMismatchCount": report1["scalarMismatchCount"],
        "scalarMaximumDifference": report1["scalarMaximumDifference"],
        "exactMismatchCount": report1["exactMismatchCount"],
        "exactMaximumDifference": report1["exactMaximumDifference"],
        "legacyMaximumDifference": 2,
        "deterministicReplay": report1 == report2 and run1["stdout"] == run2["stdout"],
        "guardedWorkRootPass": not WORK.exists(),
        "incrementalSourceBytes": source_path.stat().st_size,
    }
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
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
        "promotionPass": promotion_pass,
        "killPass": kill_pass,
        "decision": "authorize-exact-reducer-integration" if promotion_pass else "retire",
        "artifacts": [
            reference(extraction_path, "selective-extraction"),
            reference(build_receipt_path, "build-receipt"),
            reference(replay_path, "attribution-replay"),
            reference(source_path, "incremental-source-package"),
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
