#!/usr/bin/env python3
"""Replay the complete production-profile Adam update in open code."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_adam_replay_64_q0_v1"
Q3_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"
Q3_ROOT = ROOT / "results" / Q3_ID
Q3_DECISION = Q3_ROOT / "decision.json"
Q3_MANIFEST = Q3_ROOT / "fixture-manifest.json"
Q3_GUARD = Q3_ROOT / "guard.json"
Q3_REFLECTION = ROOT / "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json"
FIXTURE = Q3_ROOT / "fixture"
OPEN_SOURCE = (
    ROOT / "programs" / CANDIDATE_ID / "adam_replay.cpp"
)
PROGRAM_DESCRIPTOR = ROOT / "programs" / CANDIDATE_ID / "program.py"
BUILD_FLAGS = (
    "-std=c++20",
    "-O3",
    "-Wall",
    "-Wextra",
    "-Werror",
    "-mavx2",
    "-mfma",
    "-fno-math-errno",
    "-fno-trapping-math",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents:
        raise ValueError(f"reference escapes enwiki9 project: {path}")
    if not resolved.is_file():
        raise FileNotFoundError(f"referenced file is missing: {path}")
    row = {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }
    if identifier is not None:
        row["id"] = identifier
    return row


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
        "stdoutSha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderrSha256": hashlib.sha256(completed.stderr).hexdigest(),
        "stdout": completed.stdout.decode(errors="replace"),
        "stderr": completed.stderr.decode(errors="replace"),
    }
    if completed.returncode:
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt


def evaluate(
    predicates: list[dict[str, Any]],
    measurements: dict[str, bool | int | float],
) -> list[dict[str, Any]]:
    operations = {
        "eq": lambda value, threshold: value == threshold,
        "neq": lambda value, threshold: value != threshold,
        "gt": lambda value, threshold: value > threshold,
        "gte": lambda value, threshold: value >= threshold,
        "lt": lambda value, threshold: value < threshold,
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
        ("q3-decision", Q3_DECISION),
        ("q3-fixture-manifest", Q3_MANIFEST),
        ("q3-guard", Q3_GUARD),
        ("q3-reflection", Q3_REFLECTION),
    ):
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    parent = json.loads(Q3_DECISION.read_text())
    reflection = json.loads(Q3_REFLECTION.read_text())
    if not (
        parent.get("promotionPass") is True
        and parent.get("measurements", {}).get("fixtureComplete") is True
        and parent.get("measurements", {}).get("fixtureRepeatByteIdentical") is True
        and reflection.get("decision") == "promote"
    ):
        raise ValueError("Q3 does not authorize the open Adam replay")


def verify_fixture() -> dict[str, int | str]:
    manifest = json.loads(Q3_MANIFEST.read_text())
    fixture = manifest["fixture"]
    if (
        manifest.get("candidateId") != Q3_ID
        or manifest.get("rawFixturePath") != FIXTURE.relative_to(ROOT).as_posix()
        or not manifest.get("rawFixtureRetainedLocal")
    ):
        raise ValueError("Q3 manifest does not bind the retained fixture")
    digest = hashlib.sha256()
    total = 0
    population = 0
    declared_paths: set[str] = set()
    for row in fixture["files"]:
        relative = row["path"]
        path = FIXTURE / relative
        if relative in declared_paths or not path.is_file():
            raise ValueError(f"missing or duplicate fixture path: {relative}")
        declared_paths.add(relative)
        if path.stat().st_size != row["bytes"]:
            raise ValueError(f"fixture byte count drifted: {relative}")
        observed = sha256(path)
        if observed != row["sha256"]:
            raise ValueError(f"fixture digest drifted: {relative}")
        digest.update(relative.encode() + b"\0" + bytes.fromhex(observed))
        total += row["bytes"]
        population += 1
    actual_paths = {
        path.relative_to(FIXTURE).as_posix()
        for path in FIXTURE.rglob("*")
        if path.is_file()
    }
    if actual_paths != declared_paths:
        raise ValueError("retained fixture file population drifted")
    aggregate = digest.hexdigest()
    if (
        population != fixture["fileCount"]
        or total != fixture["totalBytes"]
        or aggregate != fixture["aggregateSha256"]
    ):
        raise ValueError("retained fixture aggregate drifted")
    return {"fileCount": population, "totalBytes": total, "aggregateSha256": aggregate}


def source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = [
        *local_source_closure((Path(__file__),)),
        OPEN_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
    ]
    members = sorted(set(members), key=lambda item: item.relative_to(ROOT).as_posix())
    declared = {item["path"]: item for item in experiment["inputs"]}
    for member in members:
        relative = member.relative_to(ROOT).as_posix()
        expected = declared.get(relative)
        if expected is None or expected != reference(member, expected.get("id")):
            raise ValueError(f"runtime source closure drifted: {relative}")
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
    if len(compressed) > experiment["budget"]["maximumAddedPackageBytes"]:
        raise ValueError("open Adam source closure exceeds the frozen package budget")
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
    require_inputs(experiment)
    result_root = (ROOT / "results" / CANDIDATE_ID).resolve()
    for relative in experiment["outputs"]:
        path = (ROOT / relative).resolve()
        if path.parent != result_root or path.exists():
            raise ValueError(f"output is outside a fresh result boundary: {relative}")

    fixture_identity = verify_fixture()
    output.parent.mkdir(parents=True)
    scratch = output.parent / "scratch"
    scratch.mkdir()
    executable = scratch / "adam_replay"
    execution: dict[str, Any] = {}
    execution["compiler"] = execute(["c++", "--version"], ROOT)
    execution["build"] = execute(
        ["c++", *BUILD_FLAGS, str(OPEN_SOURCE), "-o", str(executable)], ROOT
    )
    execution["executableSha256"] = sha256(executable)
    replay_paths = [output.parent / "replay-1.json", output.parent / "replay-2.json"]
    for index, replay in enumerate(replay_paths, start=1):
        execution[f"replay{index}"] = execute(
            [str(executable), str(FIXTURE), str(replay)], ROOT
        )
    reports = [json.loads(path.read_text()) for path in replay_paths]
    deterministic = replay_paths[0].read_bytes() == replay_paths[1].read_bytes()
    execution_path = output.parent / "execution.json"
    execution_path.write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
    package = output.parent / "incremental_source.tar.xz"
    source_package(package, experiment)
    shutil.rmtree(scratch)

    report = reports[0]
    totals = report["totals"]
    measurements: dict[str, bool | int | float] = {
        "q3ParentPass": True,
        "fixtureIdentityPass": fixture_identity["aggregateSha256"]
        == "0c904f4a262a3245cd455c4441fa1159f5247bcf23f132403580d538fe3c9fda",
        "fixtureFilePopulation": int(fixture_identity["fileCount"]),
        "openReplayExact": report["exact"] is True,
        "openReplayDeterministic": deterministic and reports[0] == reports[1],
        "parameterPopulation": totals["tensorCount"],
        "bf16ParameterPopulation": totals["bf16TensorCount"],
        "f32ParameterPopulation": totals["f32TensorCount"],
        "parameterWordPopulation": totals["parameterWordCount"],
        "parameterHighMismatchCount": totals["parameterHighMismatchCount"],
        "parameterLowMismatchCount": totals["parameterLowMismatchCount"],
        "varianceMismatchCount": totals["varianceMismatchCount"],
        "sourceClosureBytes": package.stat().st_size,
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
        "decision": (
            "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry"
        ),
        "artifacts": [
            reference(replay_paths[0], "open-replay-1"),
            reference(replay_paths[1], "open-replay-2"),
            reference(execution_path, "execution"),
            reference(package, "source-package"),
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
