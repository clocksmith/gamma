#!/usr/bin/env python3
"""Replay the complete retained post-update forward with exact branch reduction."""

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
import nncp_ggml_profile_forward_parity_64_qm18 as q18
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_ggml_postupdate_forward_parity_64_q1_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_branch_reduction_postupdate_64_q0_retry_v2"
PARENT_DECISION = ROOT / "results" / PARENT_ID / "decision.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T015840Z_2429c2251f.json"
)
LEGACY_ROOT = ROOT / "results/nncp_ggml_postupdate_forward_parity_64_q0_retry_v2/artifacts"
LEGACY_DECISION = LEGACY_ROOT / "decision.json"
FIXTURE_PACKAGE = LEGACY_ROOT / "production_forward_fixture.tar.xz"
LEGACY_SOURCE = LEGACY_ROOT / "ggml_profile_forward_source_closure.tar.xz"
Q1_DECISION = ROOT / "results/nncp_ggml_profile_arithmetic_64_q1_v1/decision.json"
FAILED_COMPARATOR_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T020543Z_916769ea99.json"
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


def execute(
    command: list[str], cwd: Path, environment: dict[str, str] | None = None
) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
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


def extract(archive: Path, destination: Path) -> dict[str, Any]:
    destination.mkdir()
    return execute(
        [
            "tar",
            "--extract",
            "--xz",
            "--no-same-owner",
            "--no-same-permissions",
            "--file",
            str(archive),
            "--directory",
            str(destination),
        ],
        ROOT,
    )


def pack_source(source: Path, output: Path) -> dict[str, Any]:
    receipt = execute(
        [
            "tar",
            "--sort=name",
            "--mtime=@0",
            "--owner=0",
            "--group=0",
            "--numeric-owner",
            "--create",
            "--xz",
            "--file",
            str(output),
            "--directory",
            str(source),
            ".",
        ],
        ROOT,
    )
    if output.stat().st_size > SOURCE_CEILING:
        raise ValueError("complete open-forward source package exceeds ceiling")
    return receipt


def incremental_source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = [
        *local_source_closure((Path(__file__),)),
        (PROGRAM / "CMakeLists.txt").resolve(),
        (PROGRAM / "profile_forward_parity.cpp").resolve(),
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
        raise ValueError("incremental forward source closure exceeds ceiling")
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
        ("branch-attribution-decision", PARENT_DECISION),
        ("branch-attribution-reflection", PARENT_REFLECTION),
        ("legacy-postupdate-forward-decision", LEGACY_DECISION),
        ("retained-postupdate-fixture", FIXTURE_PACKAGE),
        ("legacy-open-source", LEGACY_SOURCE),
        ("prior-exact-arithmetic-decision", Q1_DECISION),
        ("failed-comparator-reflection", FAILED_COMPARATOR_REFLECTION),
    ):
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    attribution = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    legacy = json.loads(LEGACY_DECISION.read_text())
    q1 = json.loads(Q1_DECISION.read_text())
    failed_comparator = json.loads(FAILED_COMPARATOR_REFLECTION.read_text())
    if not (
        attribution["promotionPass"] is True
        and attribution["measurements"]["exactMismatchCount"] == 0
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and reflection["decision"]["verdict"] == "promote"
        and legacy["maximum_tensor_absolute_error"] == 0
        and legacy["branch_comparison"][
            "maximum_integer_probability_count_difference"
        ]
        == 2
        and legacy["repeat_open_outputs_byte_identical"] is True
        and q1["promotionPass"] is True
        and q1["measurements"]["maximumProbabilityCountDifference"] == 0
        and failed_comparator["validity"]["classification"]
        == "implementation-failure"
        and failed_comparator["hypothesis"]["verdict"] == "not-tested"
        and failed_comparator["decision"]["verdict"] == "retry"
    ):
        raise ValueError("exact post-update forward antecedents are not satisfied")


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
        raise ValueError("exact post-update forward result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("candidate work root was not freshly materialized")

    fixture = WORK / "fixture"
    source = WORK / "source"
    build = WORK / "build"
    run_a = WORK / "open-a"
    run_b = WORK / "open-b"
    executions: dict[str, Any] = {
        "extractFixture": extract(FIXTURE_PACKAGE, fixture),
        "extractSource": extract(LEGACY_SOURCE, source),
    }
    shutil.copyfile(PROGRAM / "CMakeLists.txt", source / "CMakeLists.txt")
    shutil.copyfile(
        PROGRAM / "profile_forward_parity.cpp", source / "profile_forward_parity.cpp"
    )
    executions["configure"] = execute(
        ["cmake", "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"],
        ROOT,
    )
    executions["build"] = execute(
        ["cmake", "--build", str(build), "--parallel", "4"], ROOT
    )
    binaries = [
        path
        for path in build.rglob("nncp_ggml_profile_forward_parity")
        if path.is_file()
    ]
    if len(binaries) != 1:
        raise ValueError("open forward executable is not unique")
    binary = binaries[0]
    ldd = execute(["ldd", str(binary)], ROOT)
    executions["ldd"] = ldd
    forbidden = [
        line
        for line in ldd["stdout"].splitlines()
        if any(
            token in line.lower()
            for token in ("libnc", "ggml", "cuda", "openmp", "gomp", "blas")
        )
    ]
    clean_home = WORK / "home"
    clean_home.mkdir()
    environment = {
        "HOME": str(clean_home),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
    }
    run_a.mkdir()
    run_b.mkdir()
    executions["openA"] = execute(
        [str(binary), str(fixture), str(run_a)], WORK, environment
    )
    executions["openB"] = execute(
        [str(binary), str(fixture), str(run_b)], WORK, environment
    )
    manifest = json.loads((fixture / "fixture_manifest.json").read_text())
    comparisons, branch = q18.base.compare_forward(fixture, manifest, run_a)
    repeat_identical = q18.base.aggregate(run_a) == q18.base.aggregate(run_b)
    repeat_comparisons, repeat_branch = q18.base.compare_forward(
        fixture, manifest, run_b
    )
    maximum_tensor_error = max(
        row["maximum_absolute_error"] for row in comparisons
    )
    maximum_repeat_tensor_error = max(
        row["maximum_absolute_error"] for row in repeat_comparisons
    )
    open_source = RESULT / "ggml_profile_forward_source_closure.tar.xz"
    executions["packSource"] = pack_source(source, open_source)
    incremental = RESULT / "incremental_source.tar.xz"
    incremental_source_package(incremental, experiment)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps(executions, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)

    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "coordinatePass": manifest["profile"]["target_block_position"] == 320
        and manifest["selection"]["truth_original_symbol_start"] == 320
        and manifest["selection"]["truth_original_symbol_end"] == 384,
        "fixtureComplete": len(manifest["internal"]) == len(comparisons),
        "comparedTensorCount": len(comparisons),
        "maximumTensorAbsoluteError": maximum_tensor_error,
        "maximumRepeatTensorAbsoluteError": maximum_repeat_tensor_error,
        "branchRows": branch["rows"],
        "maximumBranchCountDifference": branch[
            "maximum_integer_probability_count_difference"
        ],
        "repeatMaximumBranchCountDifference": repeat_branch[
            "maximum_integer_probability_count_difference"
        ],
        "topologyDisagreementCount": branch[
            "tree_topology_and_symbol_order_disagreements"
        ],
        "truthPathDisagreementCount": branch["truth_path_disagreements"],
        "openForwardDeterministic": repeat_identical,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "openSourceBytes": open_source.stat().st_size,
        "incrementalSourceBytes": incremental.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    decision = (
        "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry"
    )
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
        "decision": decision,
        "artifacts": [
            reference(execution_path, "execution"),
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
