#!/usr/bin/env python3
"""Evaluate the first production open-backward tail boundary."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
import lzma
import mmap
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tarfile
import time
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_output_bias_gradient_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_ggml_postupdate_forward_parity_64_q1_retry_v2"
PARENT_DECISION = ROOT / "results" / PARENT_ID / "decision.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T021607Z_81c2c9ae94.json"
)
JOINT_DECISION = ROOT / (
    "results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/decision.json"
)
JOINT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T024338Z_3839f396a6.json"
)
Q3_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"
Q3_ROOT = ROOT / "results" / Q3_ID
Q3_DECISION = Q3_ROOT / "decision.json"
Q3_MANIFEST = Q3_ROOT / "fixture-manifest.json"
Q3_GUARD = Q3_ROOT / "guard.json"
Q3_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json"
)
Q3_FIXTURE = Q3_ROOT / "fixture"
MINIATURE_HEAD = ROOT / (
    "results/nncp_ggml_output_head_update_parity_qm2_v1/decision.json"
)
OPEN_SOURCE = ROOT / "results" / PARENT_ID / "ggml_profile_forward_source_closure.tar.xz"
PARENT_FORWARD = ROOT / (
    "programs/nncp_ggml_postupdate_forward_parity_64_q1_retry_v1/"
    "profile_forward_parity.cpp"
)
MATERIALIZER = PROGRAM / "materialize_forward.py"
CMAKE = PROGRAM / "CMakeLists.txt"
REDUCER = PROGRAM / "output_bias_gradient.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
STREAMS = 32
STATES = 64
LAYERS = 20
WIDTH = 1024
VOCABULARY = 16392
SOURCE_CEILING = 2_000_000
TYPE_CONTRACT = {
    0: ("F32", 4),
    1: ("BF16", 2),
    2: ("F16", 2),
    3: ("I8", 1),
    4: ("I16", 2),
    5: ("I32", 4),
    6: ("U8", 1),
    7: ("U16", 2),
    8: ("U32", 4),
}


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


class Container:
    def __init__(self, path: Path):
        self.path = path
        self.file = path.open("rb")
        self.mapping = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        self.records: dict[str, dict[str, Any]] = {}
        self.order: list[str] = []
        self._parse()

    def close(self) -> None:
        self.mapping.close()
        self.file.close()

    def _u32(self, offset: int) -> tuple[int, int]:
        if offset + 4 > len(self.mapping):
            raise ValueError(f"truncated container: {self.path}")
        return struct.unpack_from("<I", self.mapping, offset)[0], offset + 4

    def _parse(self) -> None:
        offset = 0
        magic, offset = self._u32(offset)
        if magic != 0x23F4AEFB:
            raise ValueError(f"container magic differs: {self.path}")
        config_size, offset = self._u32(offset)
        offset += config_size
        while offset < len(self.mapping):
            marker, offset = self._u32(offset)
            item_type, offset = self._u32(offset)
            rank, offset = self._u32(offset)
            name_size, offset = self._u32(offset)
            if marker != 0x23F4AEFA or item_type not in TYPE_CONTRACT:
                raise ValueError(f"invalid tensor header: {self.path}")
            dimensions = []
            count = 1
            for _ in range(rank):
                dimension, offset = self._u32(offset)
                dimensions.append(dimension)
                count *= dimension
            name = self.mapping[offset : offset + name_size].decode()
            offset += name_size
            byte_count = count * TYPE_CONTRACT[item_type][1]
            if offset + byte_count > len(self.mapping) or name in self.records:
                raise ValueError(f"invalid tensor payload: {name}")
            self.records[name] = {
                "type": item_type,
                "dimensions": dimensions,
                "offset": offset,
                "bytes": byte_count,
            }
            self.order.append(name)
            offset += byte_count
        if offset != len(self.mapping):
            raise ValueError(f"container trailing bytes: {self.path}")

    def record(self, name: str) -> dict[str, Any]:
        try:
            return self.records[name]
        except KeyError as error:
            raise ValueError(f"missing tensor {name} in {self.path}") from error

    def payload(self, name: str) -> bytes:
        record = self.record(name)
        start = record["offset"]
        return self.mapping[start : start + record["bytes"]]

    def stream_payload(self, name: str, stream: int) -> bytes:
        record = self.record(name)
        dimensions = record["dimensions"]
        item_size = TYPE_CONTRACT[record["type"]][1]
        if dimensions == [STREAMS, STATES]:
            output = bytearray(STATES * item_size)
            for state in range(STATES):
                source = record["offset"] + item_size * (stream + STREAMS * state)
                output[state * item_size : (state + 1) * item_size] = self.mapping[
                    source : source + item_size
                ]
            return bytes(output)
        if dimensions == [WIDTH, STREAMS, 256]:
            output = bytearray(WIDTH * 256 * item_size)
            for state in range(256):
                source = record["offset"] + item_size * WIDTH * (
                    stream + STREAMS * state
                )
                destination = item_size * WIDTH * state
                output[destination : destination + item_size * WIDTH] = self.mapping[
                    source : source + item_size * WIDTH
                ]
            return bytes(output)
        raise ValueError(f"unsupported stream tensor geometry: {name} {dimensions}")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("exact-forward-decision", PARENT_DECISION),
        ("exact-forward-reflection", PARENT_REFLECTION),
        ("joint-transition-decision", JOINT_DECISION),
        ("joint-transition-reflection", JOINT_REFLECTION),
        ("gradient-oracle-decision", Q3_DECISION),
        ("gradient-oracle-manifest", Q3_MANIFEST),
        ("gradient-oracle-guard", Q3_GUARD),
        ("gradient-oracle-reflection", Q3_REFLECTION),
        ("miniature-output-head-decision", MINIATURE_HEAD),
        ("exact-forward-source", OPEN_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    forward = json.loads(PARENT_DECISION.read_text())
    joint = json.loads(JOINT_DECISION.read_text())
    q3 = json.loads(Q3_DECISION.read_text())
    head = json.loads(MINIATURE_HEAD.read_text())
    reflections = [
        json.loads(PARENT_REFLECTION.read_text()),
        json.loads(JOINT_REFLECTION.read_text()),
        json.loads(Q3_REFLECTION.read_text()),
    ]
    if not (
        forward["promotionPass"] is True
        and forward["measurements"]["maximumTensorAbsoluteError"] == 0
        and forward["measurements"]["maximumBranchCountDifference"] == 0
        and joint["promotionPass"] is True
        and joint["measurements"]["openParameterPayloadMismatchCount"] == 0
        and joint["measurements"]["maximumTensorAbsoluteError"] == 0
        and q3["promotionPass"] is True
        and q3["measurements"]["gradientMetadataPopulation"] == 246
        and head["overall_pass"] is True
        and head["gradient_pass"] is True
        and all(reflection["validity"]["valid"] is True for reflection in reflections)
    ):
        raise ValueError("open output-bias antecedents are not satisfied")


def verify_used_fixture() -> dict[str, str]:
    manifest = json.loads(Q3_MANIFEST.read_text())
    declared = {row["path"]: row for row in manifest["fixture"]["files"]}
    relative_paths = (
        "parameters_initial.coefs",
        "state_initial.params",
        "gradients/0245_out_bias.bin",
        "gradients/0245_out_bias.meta",
    )
    observed = {}
    for relative in relative_paths:
        path = Q3_FIXTURE / relative
        row = declared.get(relative)
        if row is None or path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            raise ValueError(f"used Q3 fixture input drifted: {relative}")
        observed[relative] = row["sha256"]
    return observed


def tensor_row(
    category: str,
    index: int,
    name: str,
    type_name: str,
    dimensions: list[int],
    payload: str,
    path: Path,
) -> str:
    strides = []
    stride = TYPE_CONTRACT[
        next(key for key, value in TYPE_CONTRACT.items() if value[0] == type_name)
    ][1]
    for dimension in dimensions:
        strides.append(stride)
        stride *= dimension
    return "\t".join(
        (
            category,
            str(index),
            name,
            type_name,
            ",".join(map(str, dimensions)),
            ",".join(map(str, strides)),
            str(path.stat().st_size),
            sha256(path),
            payload,
        )
    )


def materialize_parameters(container: Container, shared: Path) -> list[str]:
    shared.mkdir()
    rows = []
    for index, name in enumerate(container.order):
        record = container.record(name)
        type_name = TYPE_CONTRACT[record["type"]][0]
        if type_name not in ("F32", "BF16"):
            raise ValueError(f"parameter {name} has unsupported type {type_name}")
        relative = f"parameters/{index:05d}.bin"
        path = shared / f"{index:05d}.bin"
        path.write_bytes(container.payload(name))
        rows.append(
            tensor_row(
                "parameter",
                index,
                name,
                type_name,
                record["dimensions"],
                relative,
                path,
            )
        )
    if len(rows) != 246:
        raise ValueError("production parameter population differs")
    return rows


def materialize_stream_fixture(
    container: Container,
    parameter_directory: Path,
    parameter_rows: list[str],
    stream: int,
    fixture: Path,
) -> None:
    fixture.mkdir()
    (fixture / "parameters").symlink_to(parameter_directory, target_is_directory=True)
    state_directory = fixture / "state"
    state_directory.mkdir()
    rows = list(parameter_rows)
    input_path = state_directory / "00000.bin"
    input_path.write_bytes(container.stream_payload("input_all_streams", stream))
    rows.append(
        tensor_row(
            "state", 0, "input_stream_0", "I32", [1, STATES],
            "state/00000.bin", input_path
        )
    )
    for layer in range(LAYERS):
        path = state_directory / f"{layer + 1:05d}.bin"
        path.write_bytes(container.stream_payload(f"mem_h_{layer}", stream))
        rows.append(
            tensor_row(
                "state", layer + 1, f"mem_h_{layer}_stream_0", "BF16",
                [WIDTH, 1, 256], f"state/{layer + 1:05d}.bin", path
            )
        )
    mask_path = state_directory / "00021.bin"
    mask_path.write_bytes(
        bytes(
            int(key > 256 + state)
            for state in range(STATES)
            for key in range(320)
        )
    )
    rows.append(
        tensor_row(
            "state", 21, "attention_mask", "I8", [320, STATES],
            "state/00021.bin", mask_path
        )
    )
    targets = container.stream_payload("target_all_streams", stream)
    target_values = struct.unpack(f"<{STATES}I", targets)
    if any(value >= VOCABULARY for value in target_values):
        raise ValueError("target is outside production vocabulary")
    (fixture / "target_symbols.u16le").write_bytes(
        struct.pack(f"<{STATES}H", *target_values)
    )
    header = "category\tindex\tname\ttype\tdims\tstrides\tbytes\tsha256\tpayload"
    (fixture / "tensor_index.tsv").write_text(header + "\n" + "\n".join(rows) + "\n")


def bf16_to_float(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value << 16))[0]


def compare_layer_inputs(
    state: Container, stream: int, output: Path
) -> tuple[int, int, float]:
    checkpoints = 0
    mismatches = 0
    maximum = 0.0
    for layer in range(LAYERS):
        path = output / f"layer_{layer:02d}_attention_input.f32"
        payload = path.read_bytes()
        if len(payload) != WIDTH * STATES * 4:
            raise ValueError(f"open layer checkpoint size differs: {path}")
        observed = memoryview(payload).cast("I")
        record = state.record(f"train_h_{layer}")
        if record["type"] != 1 or record["dimensions"] != [WIDTH, STREAMS, STATES]:
            raise ValueError("retained train_h contract differs")
        for position in range(STATES):
            start = record["offset"] + 2 * WIDTH * (stream + STREAMS * position)
            expected = memoryview(state.mapping)[start : start + 2 * WIDTH].cast("H")
            base = position * WIDTH
            for feature in range(WIDTH):
                word = observed[base + feature]
                target = expected[feature]
                if (word & 0xFFFF) != 0 or (word >> 16) != target:
                    mismatches += 1
                    current = struct.unpack("<f", struct.pack("<I", word))[0]
                    maximum = max(maximum, abs(current - bf16_to_float(target)))
        checkpoints += 1
    return checkpoints, mismatches, maximum


def aggregate(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode() + b"\0" + bytes.fromhex(sha256(path)))
    return digest.hexdigest()


def compare_bf16(left: Path, right: Path) -> tuple[int, float]:
    left_bytes = left.read_bytes()
    right_bytes = right.read_bytes()
    if len(left_bytes) != len(right_bytes) or len(left_bytes) % 2:
        raise ValueError("BF16 comparator geometry differs")
    mismatches = 0
    maximum = 0.0
    for left_word, right_word in zip(
        memoryview(left_bytes).cast("H"), memoryview(right_bytes).cast("H")
    ):
        if left_word != right_word:
            mismatches += 1
            maximum = max(
                maximum,
                abs(bf16_to_float(left_word) - bf16_to_float(right_word)),
            )
    return mismatches, maximum


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((Path(__file__), MATERIALIZER)),
        CMAKE.resolve(),
        REDUCER.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        OPEN_SOURCE.resolve(),
    ]
    members = sorted(set(members), key=lambda item: item.relative_to(ROOT).as_posix())
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
        raise ValueError("open output-bias source closure exceeds ceiling")
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
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("open output-bias result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("candidate work root was not freshly materialized")

    used_fixture = verify_used_fixture()
    source = WORK / "source"
    build = WORK / "build"
    shared_parameters = WORK / "parameters"
    fixtures = WORK / "fixtures"
    open_a = WORK / "open-a"
    open_b = WORK / "open-b"
    fixtures.mkdir()
    open_a.mkdir()
    open_b.mkdir()
    source.mkdir()
    executions: dict[str, Any] = {}
    executions["extractSource"] = execute(
        [
            "tar", "--extract", "--xz", "--no-same-owner", "--no-same-permissions",
            "--file", str(OPEN_SOURCE), "--directory", str(source),
        ],
        ROOT,
    )
    executions["materializeForward"] = execute(
        [
            "python3", str(MATERIALIZER), str(PARENT_FORWARD),
            str(source / "profile_output_bias_forward.cpp"),
        ],
        ROOT,
    )
    shutil.copyfile(CMAKE, source / "CMakeLists.txt")
    shutil.copyfile(REDUCER, source / "output_bias_gradient.cpp")
    executions["configure"] = execute(
        ["cmake", "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"],
        ROOT,
    )
    executions["build"] = execute(
        ["cmake", "--build", str(build), "--parallel", "4"], ROOT
    )
    forward_binaries = [
        path for path in build.rglob("nncp_open_profile_forward") if path.is_file()
    ]
    reducer_binaries = [
        path for path in build.rglob("nncp_open_output_bias_gradient") if path.is_file()
    ]
    if len(forward_binaries) != 1 or len(reducer_binaries) != 1:
        raise ValueError("open backward executable population differs")
    forward_binary = forward_binaries[0]
    reducer_binary = reducer_binaries[0]
    forbidden = []
    for label, binary in (("forward", forward_binary), ("reducer", reducer_binary)):
        receipt = execute(["ldd", str(binary)], ROOT)
        executions[f"ldd-{label}"] = receipt
        forbidden.extend(
            line
            for line in receipt["stdout"].splitlines()
            if any(
                token in line.lower()
                for token in ("libnc", "ggml", "cuda", "openmp", "gomp", "blas")
            )
        )

    parameters = Container(Q3_FIXTURE / "parameters_initial.coefs")
    state = Container(Q3_FIXTURE / "state_initial.params")
    try:
        parameter_rows = materialize_parameters(parameters, shared_parameters)
        for stream in range(STREAMS):
            materialize_stream_fixture(
                state,
                shared_parameters,
                parameter_rows,
                stream,
                fixtures / f"stream_{stream:02d}",
            )
        clean_home = WORK / "home"
        clean_home.mkdir()
        environment = {
            "HOME": str(clean_home),
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
        }

        def run_population(label: str, root: Path) -> dict[str, Any]:
            receipts: dict[str, Any] = {}

            def run_stream(stream: int) -> tuple[int, dict[str, Any]]:
                destination = root / f"stream_{stream:02d}"
                destination.mkdir()
                receipt = execute(
                    [
                        str(forward_binary),
                        str(fixtures / f"stream_{stream:02d}"),
                        str(destination),
                    ],
                    WORK,
                    environment,
                )
                return stream, receipt

            with ThreadPoolExecutor(max_workers=2) as executor:
                for stream, receipt in executor.map(run_stream, range(STREAMS)):
                    receipts[f"stream-{stream:02d}"] = receipt
            checkpoints = 0
            mismatches = 0
            maximum = 0.0
            for stream in range(STREAMS):
                current = compare_layer_inputs(
                    state, stream, root / f"stream_{stream:02d}"
                )
                checkpoints += current[0]
                mismatches += current[1]
                maximum = max(maximum, current[2])
            gradient = WORK / f"{label}-out-bias-gradient.bf16"
            shifted = WORK / f"{label}-shifted-out-bias-gradient.bf16"
            receipts["reducer"] = execute(
                [
                    str(reducer_binary),
                    str(Q3_FIXTURE / "state_initial.params"),
                    str(root),
                    str(gradient),
                    str(shifted),
                ],
                WORK,
                environment,
            )
            return {
                "receipts": receipts,
                "checkpoints": checkpoints,
                "mismatches": mismatches,
                "maximum": maximum,
                "gradient": gradient,
                "shifted": shifted,
                "aggregate": aggregate(root),
            }

        replay_a = run_population("a", open_a)
        replay_b = run_population("b", open_b)
    finally:
        state.close()
        parameters.close()

    executions["openA"] = replay_a["receipts"]
    executions["openB"] = replay_b["receipts"]
    open_gradient = RESULT / "open-out-bias-gradient.bf16"
    shutil.copyfile(replay_a["gradient"], open_gradient)
    comparator = Q3_FIXTURE / "gradients/0245_out_bias.bin"
    mismatch_count, maximum_gradient_error = compare_bf16(open_gradient, comparator)
    deterministic = (
        replay_a["aggregate"] == replay_b["aggregate"]
        and replay_a["gradient"].read_bytes() == replay_b["gradient"].read_bytes()
        and replay_a["shifted"].read_bytes() == replay_b["shifted"].read_bytes()
        and replay_a["checkpoints"] == replay_b["checkpoints"]
        and replay_a["mismatches"] == replay_b["mismatches"]
        and replay_a["maximum"] == replay_b["maximum"]
    )
    shifted_differs = replay_a["shifted"].read_bytes() != open_gradient.read_bytes()
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "executions": executions,
                "usedFixtureSha256": used_fixture,
                "openAggregateA": replay_a["aggregate"],
                "openAggregateB": replay_b["aggregate"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)

    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "streamCount": STREAMS,
        "sampleCount": STREAMS * STATES,
        "layerInputCheckpointCount": replay_a["checkpoints"],
        "layerInputMismatchCount": replay_a["mismatches"] + replay_b["mismatches"],
        "maximumLayerInputAbsoluteError": max(
            replay_a["maximum"], replay_b["maximum"]
        ),
        "outputBiasElementCount": open_gradient.stat().st_size // 2,
        "outputBiasMismatchCount": mismatch_count,
        "maximumOutputBiasAbsoluteError": maximum_gradient_error,
        "openGradientDeterministic": deterministic,
        "shiftedTargetControlDiffers": shifted_differs,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "incrementalSourceBytes": incremental_source.stat().st_size,
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
            reference(open_gradient, "open-output-bias-gradient"),
            reference(incremental_source, "incremental-source-package"),
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
