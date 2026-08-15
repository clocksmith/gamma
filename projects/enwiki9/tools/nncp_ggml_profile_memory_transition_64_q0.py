#!/usr/bin/env python3
"""Verify the exact open production-profile segment memory transition."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import struct
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_ggml_profile_arithmetic_64_q0 as arithmetic
import nncp_ggml_profile_arithmetic_64_q1 as exact_reduction
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_ggml_profile_memory_transition_64_q0_v1"
Q1_DECISION = ROOT / "results/nncp_ggml_profile_arithmetic_64_q1_v1/decision.json"
Q1_REFLECTION = (
    ROOT / "operations/adaptive/reflections/20260815T230010Z_836682be9c.json"
)
LAYERS = 20
WIDTH = 1024
MEMORY = 256
SEGMENT = 64


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return arithmetic.reference(path, identifier)


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    for identifier, path in (
        ("q1-decision", Q1_DECISION),
        ("q1-reflection", Q1_REFLECTION),
        ("q18-decision", arithmetic.Q18_DECISION),
        ("q18-fixture", arithmetic.Q18_FIXTURE),
        ("q18-source", arithmetic.Q18_SOURCE),
        ("q18-guard", arithmetic.Q18_GUARD),
    ):
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    q1 = json.loads(Q1_DECISION.read_text())
    if not (
        q1.get("promotionPass") is True
        and q1.get("measurements", {}).get("maximumProbabilityCountDifference") == 0
        and q1.get("measurements", {}).get("payloadByteIdentical") is True
    ):
        raise ValueError("Q1 does not authorize the memory transition gate")


def tensor_rows(fixture: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    lines = (fixture / "tensor_index.tsv").read_text().splitlines()
    expected_header = (
        "category\tindex\tname\ttype\tdims\tstrides\tbytes\tsha256\tpayload"
    )
    if not lines or lines[0] != expected_header:
        raise ValueError("fixture tensor index header differs")
    fields = expected_header.split("\t")
    for line in lines[1:]:
        values = line.split("\t")
        if len(values) != len(fields):
            raise ValueError("fixture tensor index row differs")
        rows.append(dict(zip(fields, values, strict=True)))
    return rows


def bf16_to_f32(raw: bytes) -> bytes:
    if len(raw) % 2:
        raise ValueError("BF16 payload has a partial value")
    output = bytearray(len(raw) * 2)
    for index in range(0, len(raw), 2):
        value = int.from_bytes(raw[index : index + 2], "little")
        struct.pack_into("<I", output, index * 2, value << 16)
    return bytes(output)


def aggregate(layers: list[bytes]) -> str:
    digest = hashlib.sha256()
    for layer, payload in enumerate(layers):
        digest.update(struct.pack("<I", layer))
        digest.update(payload)
    return digest.hexdigest()


def transitioned_states(
    fixture: Path,
    open_output: Path | None,
) -> tuple[list[bytes], list[dict[str, str | int]]]:
    rows = tensor_rows(fixture)
    state_rows = {
        row["name"]: row
        for row in rows
        if row["category"] == "state" and row["name"].startswith("mem_h_")
    }
    attention_rows: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if row["category"] == "internal" and row["name"].endswith(
            "_attention_input"
        ):
            attention_rows.setdefault(row["name"], []).append(row)

    states: list[bytes] = []
    receipts: list[dict[str, str | int]] = []
    position_bytes = WIDTH * 4
    for layer in range(LAYERS):
        state_name = f"mem_h_{layer}_stream_0"
        attention_name = f"layer_{layer:02d}_attention_input"
        state_row = state_rows.get(state_name)
        selected = attention_rows.get(attention_name, [])
        if state_row is None or state_row["type"] != "BF16":
            raise ValueError(f"missing BF16 initial state for layer {layer}")
        if state_row["dims"] != f"{WIDTH},1,{MEMORY}":
            raise ValueError(f"initial state geometry differs for layer {layer}")
        if len(selected) != SEGMENT:
            raise ValueError(f"teacher attention population differs for layer {layer}")
        initial = bf16_to_f32((fixture / state_row["payload"]).read_bytes())
        if len(initial) != MEMORY * position_bytes:
            raise ValueError(f"initial state size differs for layer {layer}")
        if open_output is None:
            current = b"".join((fixture / row["payload"]).read_bytes() for row in selected)
        else:
            current = (open_output / f"{attention_name}.f32").read_bytes()
        if len(current) != SEGMENT * position_bytes:
            raise ValueError(f"segment state size differs for layer {layer}")
        next_state = initial[SEGMENT * position_bytes :] + current
        if len(next_state) != MEMORY * position_bytes:
            raise ValueError(f"next state size differs for layer {layer}")
        states.append(next_state)
        receipts.append(
            {
                "layer": layer,
                "initialSha256": hashlib.sha256(initial).hexdigest(),
                "segmentSha256": hashlib.sha256(current).hexdigest(),
                "nextMemorySha256": hashlib.sha256(next_state).hexdigest(),
            }
        )
    return states, receipts


def source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = local_source_closure((Path(__file__),))
    declared = {item["path"]: item for item in experiment["inputs"]}
    for member in members:
        relative = member.relative_to(ROOT).as_posix()
        if declared.get(relative) != reference(member, declared.get(relative, {}).get("id")):
            raise ValueError(f"runtime source closure drifted: {relative}")
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(str(member), arcname=member.relative_to(ROOT).as_posix())
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    compressed = lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    tar_path.unlink()
    if len(compressed) > experiment["budget"]["maximumAddedPackageBytes"]:
        raise ValueError("incremental source closure exceeds the frozen package budget")
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
    if reference(experiment_path) != json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]):
        raise ValueError("job and tool experiment bindings differ")
    candidate_revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    result_root = (ROOT / "results" / CANDIDATE_ID).resolve()
    for relative in experiment["outputs"]:
        path = (ROOT / relative).resolve()
        if path.parent != result_root or path.exists():
            raise ValueError(f"output is outside a fresh result boundary: {relative}")

    output.parent.mkdir(parents=True, exist_ok=True)
    scratch = output.parent / "scratch"
    source = scratch / "source"
    fixture = scratch / "fixture"
    build = scratch / "build"
    executions: dict[str, Any] = {}
    executions["extractSource"] = exact_reduction.extract(arithmetic.Q18_SOURCE, source)
    executions["extractFixture"] = arithmetic.extract(arithmetic.Q18_FIXTURE, fixture)
    executions["configure"] = arithmetic.execute(
        ["cmake", "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"], ROOT
    )
    executions["build"] = arithmetic.execute(
        ["cmake", "--build", str(build), "--parallel", "4"], ROOT
    )
    executable = build / "nncp_ggml_profile_forward_parity"
    open_outputs = []
    for run in (1, 2):
        run_root = scratch / f"open-{run}"
        executions[f"open{run}"] = arithmetic.execute(
            [str(executable), str(fixture), str(run_root)], ROOT
        )
        open_outputs.append(run_root)

    teacher_states, teacher_layers = transitioned_states(fixture, None)
    open_a_states, open_a_layers = transitioned_states(fixture, open_outputs[0])
    open_b_states, open_b_layers = transitioned_states(fixture, open_outputs[1])
    state_receipt = {
        "schema": "gamma.nncp.ggml.profile-memory-transition.q0.v1",
        "teacherAggregateSha256": aggregate(teacher_states),
        "openAggregateSha256": aggregate(open_a_states),
        "openRepeatAggregateSha256": aggregate(open_b_states),
        "teacherLayers": teacher_layers,
        "openLayers": open_a_layers,
        "openRepeatLayers": open_b_layers,
    }
    state_path = output.parent / "state-digests.json"
    state_path.write_text(json.dumps(state_receipt, indent=2, sort_keys=True) + "\n")
    execution_path = output.parent / "execution.json"
    execution_path.write_text(json.dumps(executions, indent=2, sort_keys=True) + "\n")
    package = output.parent / "incremental_source.tar.xz"
    source_package(package, experiment)

    teacher_open_identity = teacher_states == open_a_states
    open_repeat_identity = open_a_states == open_b_states
    differing_layers = sum(
        expected != observed
        for expected, observed in zip(teacher_states, open_a_states, strict=True)
    )
    measurements: dict[str, bool | int | float] = {
        "q1ParentPass": True,
        "layerPopulation": len(teacher_states),
        "teacherOpenMemoryIdentity": teacher_open_identity,
        "openMemoryDeterministic": open_repeat_identity,
        "differingMemoryLayers": differing_layers,
        "sourceClosureBytes": package.stat().st_size,
    }
    promotion = arithmetic.evaluate(experiment["promotionPredicates"], measurements)
    kill = arithmetic.evaluate(experiment["killPredicates"], measurements)
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
        "decision": "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry",
        "artifacts": [
            reference(state_path, "state-digests"),
            reference(execution_path, "execution"),
            reference(package, "source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(scratch)
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
