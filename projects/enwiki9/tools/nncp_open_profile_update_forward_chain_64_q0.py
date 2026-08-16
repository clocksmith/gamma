#!/usr/bin/env python3
"""Chain the open production update and memory transition into the next forward."""

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

import numpy as np

from enwiki9_python_source_closure import local_source_closure
import nncp_ggml_profile_forward_parity_64_qm18 as q18
import nncp_ggml_profile_memory_transition_64_q0 as memory
import nncp_open_profile_adam_replay_64_q0_retry_v2 as adam
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_update_forward_chain_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"

Q3_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
UPDATE_FIXTURE = Q3_ROOT / "fixture"
Q3_DECISION = Q3_ROOT / "decision.json"
Q3_MANIFEST = Q3_ROOT / "fixture-manifest.json"
Q3_GUARD = Q3_ROOT / "guard.json"
Q3_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json"
)
ADAM_DECISION = ROOT / (
    "results/nncp_open_profile_adam_replay_64_q0_retry_v2/decision.json"
)
ADAM_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T003855Z_aab09244b0.json"
)
MEMORY_DECISION = ROOT / (
    "results/nncp_ggml_profile_memory_transition_64_q0_v1/decision.json"
)
MEMORY_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260815T231108Z_4912fe7f1f.json"
)
PRE_DECISION = ROOT / (
    "results/nncp_ggml_profile_forward_parity_64_qm18_v1/decision.json"
)
PRE_FIXTURE = ROOT / (
    "results/nncp_ggml_profile_forward_parity_64_qm18_v1/"
    "production_forward_fixture.tar.xz"
)
POST_DECISION = ROOT / (
    "results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v2/decision.json"
)
POST_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T021607Z_81c2c9ae94.json"
)
POST_FIXTURE = ROOT / (
    "results/nncp_ggml_postupdate_forward_parity_64_q0_retry_v2/artifacts/"
    "production_forward_fixture.tar.xz"
)
POST_SOURCE = ROOT / (
    "results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v2/"
    "ggml_profile_forward_source_closure.tar.xz"
)
ADAM_SOURCE = PROGRAM / "adam_payloads.cpp"
ADAM_PARENT_SOURCE = ROOT / (
    "programs/nncp_open_profile_adam_replay_64_q0_retry_v2/adam_replay.cpp"
)
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / "tools/nncp_open_profile_update_forward_chain_64_q0_materializer.py"
SOURCE_CEILING = 2_000_000
LAYERS = 20
WIDTH = 1024
MEMORY = 256
SEGMENT = 64
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


def aggregate(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        digest.update(path.relative_to(directory).as_posix().encode() + b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


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
    paths = (
        ("q3-update-decision", Q3_DECISION),
        ("q3-update-manifest", Q3_MANIFEST),
        ("q3-update-guard", Q3_GUARD),
        ("q3-update-reflection", Q3_REFLECTION),
        ("open-adam-decision", ADAM_DECISION),
        ("open-adam-reflection", ADAM_REFLECTION),
        ("open-memory-decision", MEMORY_DECISION),
        ("open-memory-reflection", MEMORY_REFLECTION),
        ("preupdate-forward-decision", PRE_DECISION),
        ("preupdate-forward-fixture", PRE_FIXTURE),
        ("postupdate-forward-decision", POST_DECISION),
        ("postupdate-forward-reflection", POST_REFLECTION),
        ("postupdate-forward-fixture", POST_FIXTURE),
        ("exact-forward-source", POST_SOURCE),
        ("open-adam-parent-source", ADAM_PARENT_SOURCE),
    )
    for identifier, path in paths:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    q3 = json.loads(Q3_DECISION.read_text())
    open_adam = json.loads(ADAM_DECISION.read_text())
    open_memory = json.loads(MEMORY_DECISION.read_text())
    pre = json.loads(PRE_DECISION.read_text())
    post = json.loads(POST_DECISION.read_text())
    post_reflection = json.loads(POST_REFLECTION.read_text())
    if not (
        q3["promotionPass"] is True
        and q3["measurements"]["fixtureComplete"] is True
        and open_adam["promotionPass"] is True
        and open_adam["measurements"]["openReplayExact"] is True
        and open_memory["promotionPass"] is True
        and open_memory["measurements"]["teacherOpenMemoryIdentity"] is True
        and pre["overall_pass"] is True
        and pre["maximum_tensor_absolute_error"] == 0
        and post["promotionPass"] is True
        and post["measurements"]["maximumTensorAbsoluteError"] == 0
        and post["measurements"]["maximumBranchCountDifference"] == 0
        and post_reflection["validity"]["valid"] is True
        and post_reflection["decision"]["verdict"] == "promote"
    ):
        raise ValueError("joint open-chain antecedents are not satisfied")


def source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = [
        *local_source_closure((Path(__file__),)),
        ADAM_SOURCE.resolve(),
        ADAM_PARENT_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        MATERIALIZER.resolve(),
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
    if len(compressed) > SOURCE_CEILING:
        raise ValueError("joint open-chain source package exceeds ceiling")
    path.write_bytes(compressed)


def manifest_by_name(path: Path) -> dict[str, dict[str, Any]]:
    manifest = json.loads(path.read_text())
    tensors = manifest.get("tensors", [])
    rows = {row["name"]: row for row in tensors}
    if len(rows) != manifest.get("tensor_count") or len(rows) != len(tensors):
        raise ValueError(f"tensor manifest population differs: {path}")
    return rows


def validate_and_inject_parameters(
    generated: Path, fixture: Path
) -> tuple[int, int]:
    expected = manifest_by_name(fixture / "parameters/manifest.json")
    generated_names = {path.stem for path in generated.glob("*.bin")}
    if generated_names != set(expected):
        raise ValueError("open parameter payload population differs")
    mismatches = 0
    for name, row in expected.items():
        source = generated / f"{name}.bin"
        if source.stat().st_size != row["bytes"] or sha256(source) != row["sha256"]:
            mismatches += 1
        target = fixture / "parameters" / row["payload"]
        target.unlink()
        shutil.copyfile(source, target)
    (fixture / "parameters.coefs").unlink()
    return len(expected), mismatches


def f32_to_bf16(raw: bytes) -> bytes:
    if len(raw) % 4:
        raise ValueError("open memory input has a partial float32 value")
    bits = np.frombuffer(raw, dtype="<u4").astype(np.uint64)
    rounded = bits + np.uint64(0x7FFF) + ((bits >> np.uint64(16)) & np.uint64(1))
    return (rounded >> np.uint64(16)).astype("<u2").tobytes()


def generate_state_payloads(
    pre_fixture: Path, pre_output: Path, destination: Path
) -> dict[str, str]:
    destination.mkdir()
    rows = memory.tensor_rows(pre_fixture)
    states = {
        row["name"]: row
        for row in rows
        if row["category"] == "state" and row["name"].startswith("mem_h_")
    }
    position_bytes = WIDTH * 2
    digests: dict[str, str] = {}
    for layer in range(LAYERS):
        name = f"mem_h_{layer}_stream_0"
        row = states.get(name)
        if row is None or row["type"] != "BF16" or row["dims"] != f"{WIDTH},1,{MEMORY}":
            raise ValueError(f"pre-update memory geometry differs for layer {layer}")
        initial = (pre_fixture / row["payload"]).read_bytes()
        current = (pre_output / f"layer_{layer:02d}_attention_input.f32").read_bytes()
        current_bf16 = f32_to_bf16(current)
        if len(initial) != MEMORY * position_bytes or len(current_bf16) != SEGMENT * position_bytes:
            raise ValueError(f"open memory byte geometry differs for layer {layer}")
        updated = initial[SEGMENT * position_bytes :] + current_bf16
        output = destination / f"{name}.bin"
        output.write_bytes(updated)
        digests[name] = sha256(output)
    return digests


def validate_and_inject_states(generated: Path, fixture: Path) -> tuple[int, int]:
    expected = manifest_by_name(fixture / "state/manifest.json")
    memory_rows = {
        name: row for name, row in expected.items() if name.startswith("mem_h_")
    }
    if len(memory_rows) != LAYERS:
        raise ValueError("post-update memory population differs")
    mismatches = 0
    for name, row in memory_rows.items():
        source = generated / f"{name}.bin"
        if source.stat().st_size != row["bytes"] or sha256(source) != row["sha256"]:
            mismatches += 1
        target = fixture / "state" / row["payload"]
        target.unlink()
        shutil.copyfile(source, target)
    (fixture / "state.params").unlink()
    return len(memory_rows), mismatches


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
        raise ValueError("joint open-chain result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("joint open-chain work root is not freshly materialized")

    update_identity = adam.verify_fixture()
    pre_fixture = WORK / "pre-fixture"
    post_fixture = WORK / "post-fixture"
    source = WORK / "source"
    build = WORK / "build"
    pre_a = WORK / "pre-open-a"
    pre_b = WORK / "pre-open-b"
    state_a = WORK / "state-a"
    state_b = WORK / "state-b"
    parameters_a = WORK / "parameters-a"
    parameters_b = WORK / "parameters-b"
    post_a = WORK / "post-open-a"
    post_b = WORK / "post-open-b"
    executions: dict[str, Any] = {
        "extractPreFixture": extract(PRE_FIXTURE, pre_fixture),
        "extractPostFixture": extract(POST_FIXTURE, post_fixture),
        "extractSource": extract(POST_SOURCE, source),
    }
    executions["configureForward"] = execute(
        ["cmake", "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"],
        ROOT,
    )
    executions["buildForward"] = execute(
        ["cmake", "--build", str(build), "--parallel", "4"], ROOT
    )
    binaries = [
        path for path in build.rglob("nncp_ggml_profile_forward_parity") if path.is_file()
    ]
    if len(binaries) != 1:
        raise ValueError("open forward executable is not unique")
    forward_binary = binaries[0]
    ldd = execute(["ldd", str(forward_binary)], ROOT)
    executions["forwardLdd"] = ldd
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
    pre_a.mkdir()
    pre_b.mkdir()
    executions["preForwardA"] = execute(
        [str(forward_binary), str(pre_fixture), str(pre_a)], WORK, environment
    )
    executions["preForwardB"] = execute(
        [str(forward_binary), str(pre_fixture), str(pre_b)], WORK, environment
    )
    pre_manifest = json.loads((pre_fixture / "fixture_manifest.json").read_text())
    pre_comparisons, _pre_branch = q18.base.compare_forward(
        pre_fixture, pre_manifest, pre_a
    )
    pre_repeat_comparisons, _pre_repeat_branch = q18.base.compare_forward(
        pre_fixture, pre_manifest, pre_b
    )
    maximum_pre_tensor_error = max(
        row["maximum_absolute_error"] for row in pre_comparisons
    )
    maximum_pre_repeat_tensor_error = max(
        row["maximum_absolute_error"] for row in pre_repeat_comparisons
    )
    state_digests_a = generate_state_payloads(pre_fixture, pre_a, state_a)
    state_digests_b = generate_state_payloads(pre_fixture, pre_b, state_b)
    pre_forward_deterministic = q18.base.aggregate(pre_a) == q18.base.aggregate(pre_b)
    state_deterministic = state_digests_a == state_digests_b

    adam_binary = WORK / "adam_payloads"
    executions["buildAdam"] = execute(
        ["c++", *BUILD_FLAGS, str(ADAM_SOURCE), "-o", str(adam_binary)], ROOT
    )
    adam_reports = [WORK / "adam-a.json", WORK / "adam-b.json"]
    executions["adamA"] = execute(
        [str(adam_binary), str(UPDATE_FIXTURE), str(adam_reports[0]), str(parameters_a)],
        WORK,
        environment,
    )
    executions["adamB"] = execute(
        [str(adam_binary), str(UPDATE_FIXTURE), str(adam_reports[1]), str(parameters_b)],
        WORK,
        environment,
    )
    adam_results = [json.loads(path.read_text()) for path in adam_reports]
    parameter_deterministic = (
        aggregate(parameters_a) == aggregate(parameters_b)
        and adam_reports[0].read_bytes() == adam_reports[1].read_bytes()
    )
    parameter_count, parameter_mismatches = validate_and_inject_parameters(
        parameters_a, post_fixture
    )
    state_count, state_mismatches = validate_and_inject_states(state_a, post_fixture)
    incumbent_containers_removed = not (post_fixture / "parameters.coefs").exists() and not (
        post_fixture / "state.params"
    ).exists()

    post_a.mkdir()
    post_b.mkdir()
    executions["postForwardA"] = execute(
        [str(forward_binary), str(post_fixture), str(post_a)], WORK, environment
    )
    executions["postForwardB"] = execute(
        [str(forward_binary), str(post_fixture), str(post_b)], WORK, environment
    )
    manifest = json.loads((post_fixture / "fixture_manifest.json").read_text())
    comparisons, branch = q18.base.compare_forward(post_fixture, manifest, post_a)
    repeat_comparisons, repeat_branch = q18.base.compare_forward(
        post_fixture, manifest, post_b
    )
    post_forward_deterministic = q18.base.aggregate(post_a) == q18.base.aggregate(post_b)
    maximum_tensor_error = max(row["maximum_absolute_error"] for row in comparisons)
    maximum_repeat_tensor_error = max(
        row["maximum_absolute_error"] for row in repeat_comparisons
    )
    chain_receipt = {
        "schema": "gamma.nncp.open-update-forward-chain.q0.v1",
        "updateFixtureAggregateSha256": update_identity["aggregateSha256"],
        "openAdamReportsExact": all(report["exact"] is True for report in adam_results),
        "openParameterPayloadAggregateSha256": aggregate(parameters_a),
        "openParameterRepeatAggregateSha256": aggregate(parameters_b),
        "openStatePayloads": state_digests_a,
        "openStateRepeatPayloads": state_digests_b,
        "incumbentPostupdateContainersRemoved": incumbent_containers_removed,
        "postForwardOutputAggregateSha256": q18.base.aggregate(post_a),
        "postForwardRepeatOutputAggregateSha256": q18.base.aggregate(post_b),
    }
    chain_path = RESULT / "chain-receipt.json"
    chain_path.write_text(json.dumps(chain_receipt, indent=2, sort_keys=True) + "\n")
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps(executions, indent=2, sort_keys=True) + "\n")
    package = RESULT / "incremental_source.tar.xz"
    source_package(package, experiment)
    shutil.rmtree(WORK)

    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "updateFixtureIdentityPass": update_identity["aggregateSha256"]
        == "0c904f4a262a3245cd455c4441fa1159f5247bcf23f132403580d538fe3c9fda",
        "openAdamExact": all(report["exact"] is True for report in adam_results),
        "openParameterPayloadCount": parameter_count,
        "openParameterPayloadMismatchCount": parameter_mismatches,
        "openParameterDeterministic": parameter_deterministic,
        "preComparedTensorCount": len(pre_comparisons),
        "maximumPreTensorAbsoluteError": maximum_pre_tensor_error,
        "maximumPreRepeatTensorAbsoluteError": maximum_pre_repeat_tensor_error,
        "preForwardDeterministic": pre_forward_deterministic,
        "openStateLayerCount": state_count,
        "openStateMismatchCount": state_mismatches,
        "openStateDeterministic": state_deterministic,
        "incumbentPostupdateContainersRemoved": incumbent_containers_removed,
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
        "postForwardDeterministic": post_forward_deterministic,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "incrementalSourceBytes": package.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
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
            "authorize-successor"
            if promotion_pass
            else "retire"
            if kill_pass
            else "retry"
        ),
        "artifacts": [
            reference(chain_path, "chain-receipt"),
            reference(execution_path, "execution"),
            reference(package, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if promotion_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
