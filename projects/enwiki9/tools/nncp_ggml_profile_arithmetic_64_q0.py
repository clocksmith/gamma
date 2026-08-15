#!/usr/bin/env python3
"""Terminate the retained open GGML production-profile branch stream."""

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
import subprocess
import tarfile
import time
from typing import Any

from enwiki9_python_source_closure import local_source_closure
from nncp_symbol_cache32_marginal_qm0 import RangeDecoder, RangeEncoder
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_ggml_profile_arithmetic_64_q0_v1"
Q18_ID = "nncp_ggml_profile_forward_parity_64_qm18_v1"
Q18_ROOT = ROOT / "results" / Q18_ID
Q18_DECISION = Q18_ROOT / "decision.json"
Q18_FIXTURE = Q18_ROOT / "production_forward_fixture.tar.xz"
Q18_SOURCE = Q18_ROOT / "ggml_profile_forward_source_closure.tar.xz"
Q18_GUARD = ROOT / "results/nncp_ggml_profile_forward_parity_64_qm18_guard_v1.json"
TREE_HEADER = struct.Struct("<8sII")
TREE_ROW = struct.Struct("<8I")
TREE_MAGIC = b"NNPTREE1"
EXPECTED_SYMBOLS = 64
EXPECTED_VOCABULARY = 16_392
EXPECTED_BRANCHES = 896


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents:
        raise ValueError(f"reference escapes enwiki9 project: {path}")
    if not resolved.is_file():
        raise FileNotFoundError(f"referenced file is missing: {path}")
    row = {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{research_contracts.file_digest(resolved, 'sha256')}",
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


def extract(archive: Path, destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True)
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


def load_tree(path: Path) -> tuple[list[dict[str, int]], list[int]]:
    raw = path.read_bytes()
    if len(raw) < TREE_HEADER.size:
        raise ValueError(f"truncated branch path: {path}")
    magic, symbols, vocabulary = TREE_HEADER.unpack_from(raw)
    if (
        magic != TREE_MAGIC
        or symbols != EXPECTED_SYMBOLS
        or vocabulary != EXPECTED_VOCABULARY
    ):
        raise ValueError(f"branch path header differs from contract: {path}")
    payload = raw[TREE_HEADER.size :]
    if len(payload) % TREE_ROW.size:
        raise ValueError(f"branch path has a partial row: {path}")
    rows: list[dict[str, int]] = []
    targets = [-1] * symbols
    expected_position = 0
    expected_depth = 0
    for offset in range(0, len(payload), TREE_ROW.size):
        values = TREE_ROW.unpack_from(payload, offset)
        row = dict(
            zip(
                (
                    "position",
                    "symbol",
                    "depth",
                    "start",
                    "range",
                    "range0",
                    "probability0",
                    "bit",
                ),
                values,
                strict=True,
            )
        )
        if row["position"] != expected_position or row["depth"] != expected_depth:
            raise ValueError(f"branch path order differs at row {len(rows)}: {path}")
        if row["range"] <= 1 or row["range0"] != row["range"] >> 1:
            raise ValueError(f"invalid tree geometry at row {len(rows)}: {path}")
        if not 1 <= row["probability0"] < 32_768 or row["bit"] not in (0, 1):
            raise ValueError(f"invalid probability or truth at row {len(rows)}: {path}")
        boundary = row["start"] + row["range0"]
        expected_bit = int(row["symbol"] >= boundary)
        if row["bit"] != expected_bit:
            raise ValueError(f"truth does not select symbol at row {len(rows)}: {path}")
        next_range = row["range"] - row["range0"] if row["bit"] else row["range0"]
        next_start = boundary if row["bit"] else row["start"]
        rows.append(row)
        if next_range == 1:
            if next_start != row["symbol"]:
                raise ValueError(f"tree path terminates at another symbol: {path}")
            targets[expected_position] = next_start
            expected_position += 1
            expected_depth = 0
        else:
            expected_depth += 1
    if expected_position != symbols or len(rows) != EXPECTED_BRANCHES or min(targets) < 0:
        raise ValueError(f"branch path population is incomplete: {path}")
    return rows, targets


def compare_trees(
    oracle: list[dict[str, int]],
    observed: list[dict[str, int]],
) -> tuple[bool, int]:
    if len(oracle) != len(observed):
        return False, 2**31 - 1
    maximum_delta = 0
    for expected, actual in zip(oracle, observed, strict=True):
        for field in ("position", "symbol", "depth", "start", "range", "range0", "bit"):
            if expected[field] != actual[field]:
                return False, 2**31 - 1
        maximum_delta = max(
            maximum_delta,
            abs(expected["probability0"] - actual["probability0"]),
        )
    return True, maximum_delta


def encode(rows: list[dict[str, int]]) -> bytes:
    coder = RangeEncoder()
    for row in rows:
        coder.put_bit(row["probability0"], row["bit"])
    return coder.finish()


def decode(
    payload: bytes,
    rows: list[dict[str, int]],
    expected_symbols: list[int],
) -> bool:
    decoder = RangeDecoder(payload)
    decoded: list[int] = []
    start = 0
    active = EXPECTED_VOCABULARY
    position = 0
    depth = 0
    for row in rows:
        if (
            row["position"] != position
            or row["depth"] != depth
            or row["start"] != start
            or row["range"] != active
        ):
            raise ValueError("decoder tree coordinates differ from branch receipt")
        bit = decoder.get_bit(row["probability0"])
        left = active >> 1
        if bit:
            start += left
            active -= left
        else:
            active = left
        if active == 1:
            decoded.append(start)
            start = 0
            active = EXPECTED_VOCABULARY
            position += 1
            depth = 0
        else:
            depth += 1
    return decoded == expected_symbols


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
                    measurements[predicate["measurement"]],
                    predicate["threshold"],
                )
            ),
        }
        for predicate in predicates
    ]


def source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = local_source_closure((Path(__file__),))
    declared = {item["path"]: item for item in experiment["inputs"]}
    for member in members:
        relative = member.relative_to(ROOT).as_posix()
        observed = reference(member)
        expected = declared.get(relative)
        if expected is None or any(
            observed[key] != expected.get(key) for key in ("path", "sha256")
        ):
            raise ValueError(f"runtime source closure drifted: {relative}")
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(ROOT).as_posix()
            )
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mtime = 0
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    path.write_bytes(lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME))
    tar_path.unlink()


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    for identifier, path in (
        ("q18-decision", Q18_DECISION),
        ("q18-fixture", Q18_FIXTURE),
        ("q18-source", Q18_SOURCE),
        ("q18-guard", Q18_GUARD),
    ):
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    parent = json.loads(Q18_DECISION.read_text())
    if not (
        parent.get("overall_pass") is True
        and parent.get("maximum_tensor_absolute_error") == 0.0
        and parent.get("branch_pass") is True
        and parent.get("branch_comparison", {}).get(
            "maximum_integer_probability_count_difference"
        )
        == 1
    ):
        raise ValueError("q18 parent does not authorize arithmetic termination")


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
    output.parent.mkdir(parents=True, exist_ok=True)
    scratch = output.parent / "scratch"
    source = scratch / "source"
    fixture = scratch / "fixture"
    build = scratch / "build"
    executions: dict[str, Any] = {}
    executions["extractSource"] = extract(Q18_SOURCE, source)
    executions["extractFixture"] = extract(Q18_FIXTURE, fixture)
    executions["configure"] = execute(
        ["cmake", "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"],
        ROOT,
    )
    executions["build"] = execute(
        ["cmake", "--build", str(build), "--parallel", "4"],
        ROOT,
    )
    executable = build / "nncp_ggml_profile_forward_parity"
    open_trees: list[Path] = []
    for run in (1, 2):
        run_root = scratch / f"open-{run}"
        executions[f"open{run}"] = execute(
            [str(executable), str(fixture), str(run_root)],
            ROOT,
        )
        retained = output.parent / f"open-tree-{run}.u32le"
        shutil.copyfile(run_root / "tree_path.u32le", retained)
        open_trees.append(retained)
        shutil.rmtree(run_root)

    oracle_rows, oracle_symbols = load_tree(fixture / "tree_path.u32le")
    observed_runs = [load_tree(path) for path in open_trees]
    topology, maximum_delta = compare_trees(oracle_rows, observed_runs[0][0])
    repeat_topology, repeat_maximum_delta = compare_trees(
        observed_runs[0][0], observed_runs[1][0]
    )
    oracle_payload = encode(oracle_rows)
    open_payloads = [encode(rows) for rows, _symbols in observed_runs]
    payload_paths = [
        output.parent / "oracle.bin",
        output.parent / "open.bin",
        output.parent / "open-repeat.bin",
    ]
    for path, payload in zip(
        payload_paths,
        (oracle_payload, *open_payloads),
        strict=True,
    ):
        path.write_bytes(payload)
    package = output.parent / "incremental_source.tar.xz"
    source_package(package, experiment)
    execution_path = output.parent / "execution.json"
    execution_path.write_text(json.dumps(executions, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(scratch)

    q18 = json.loads(Q18_DECISION.read_text())
    measurements: dict[str, bool | int | float] = {
        "q18ParentPass": q18["overall_pass"] is True,
        "topologyTruthIdentity": topology and oracle_symbols == observed_runs[0][1],
        "maximumProbabilityCountDifference": maximum_delta,
        "openTreeDeterministic": repeat_topology
        and repeat_maximum_delta == 0
        and open_trees[0].read_bytes() == open_trees[1].read_bytes(),
        "oracleDecodeExact": decode(oracle_payload, oracle_rows, oracle_symbols),
        "openDecodeExact": decode(open_payloads[0], observed_runs[0][0], oracle_symbols),
        "openRepeatDecodeExact": decode(
            open_payloads[1], observed_runs[1][0], oracle_symbols
        ),
        "openPayloadDeterministic": open_payloads[0] == open_payloads[1],
        "payloadBytesEqual": len(oracle_payload) == len(open_payloads[0]),
        "payloadByteIdentical": oracle_payload == open_payloads[0],
        "oraclePayloadBytes": len(oracle_payload),
        "openPayloadBytes": len(open_payloads[0]),
        "sourceClosureBytes": Q18_SOURCE.stat().st_size,
    }
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    decision = "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry"
    artifacts = [
        reference(payload_paths[0], "oracle-payload"),
        reference(payload_paths[1], "open-payload"),
        reference(payload_paths[2], "open-repeat-payload"),
        reference(open_trees[0], "open-tree-1"),
        reference(open_trees[1], "open-tree-2"),
        reference(execution_path, "execution"),
        reference(package, "source-package"),
    ]
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
        "artifacts": artifacts,
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
