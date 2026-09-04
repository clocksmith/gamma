#!/usr/bin/env python3
"""Fail-closed front end for the frozen open NNCP midpoint replay.

This source is deliberately not an executable scientific result yet. The
``inspect`` mode validates the prospective immutable input closure. Replay,
comparison, and repeat modes remain disabled until production-oracle parity
and the complete population/state closure are sealed in this candidate tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import stat
import sys
from dataclasses import dataclass
from typing import Any, NoReturn


SCHEMA = "gamma.enwiki9.nncp-open-integrated-midpoint-input-lock.v2"
RECEIPT_SCHEMA = "gamma.enwiki9.nncp-open-integrated-midpoint-inspection.v2"
EXPECTED_EXPERIMENT = "nncp_open_integrated_midpoint_segment_replay_65536_q0_v2"
EXPECTED_SYMBOLS = 65_536
EXPECTED_SEGMENTS = 1_024
EXPECTED_SEGMENT_LENGTH = 64
EXPECTED_FIRST_HALF = 32
EXPECTED_STREAMS = 32
EXPECTED_PARAMETERS = 246
REQUIRED_ROLES = frozenset(
    {
        "population_manifest",
        "truth_population",
        "initial_parameters",
        "initial_optimizer_state",
        "initial_recurrent_state",
        "initial_attention_state",
        "initial_cache_state",
        "first_half_oracle",
        "loss_oracle",
        "backward_oracle",
        "post_update_oracle",
        "state_rebuild_oracle",
        "second_half_oracle",
        "negative_control_permutation",
    }
)
THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


class ContractError(ValueError):
    """An input violates the frozen fail-closed contract."""


@dataclass(frozen=True)
class Artifact:
    role: str
    relative_path: str
    path: pathlib.Path
    size: int
    sha256: str
    dtype: str
    shape: tuple[int, ...]
    layout: str
    endianness: str
    producer_path: str
    producer_sha256: str


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def _require_int(value: Any, expected: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != expected:
        raise ContractError(f"{label} must equal {expected}")


def _require_sha256(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ContractError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _relative_file(root: pathlib.Path, value: Any, label: str) -> tuple[str, pathlib.Path]:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{label} must be a nonempty relative path")
    relative = pathlib.PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise ContractError(f"{label} must be a normalized relative path")
    path = root.joinpath(*relative.parts)
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ContractError(f"{label} escapes the immutable input root") from error
    current = root
    for part in relative.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as error:
            raise ContractError(f"{label} is missing: {value}") from error
        if stat.S_ISLNK(mode):
            raise ContractError(f"{label} traverses a symlink: {value}")
    if not stat.S_ISREG(path.stat().st_mode):
        raise ContractError(f"{label} is not a regular file: {value}")
    return value, path


def _parse_artifact(root: pathlib.Path, raw: Any, index: int) -> Artifact:
    row = _require_object(raw, f"artifacts[{index}]")
    required_fields = {
        "role",
        "path",
        "bytes",
        "sha256",
        "dtype",
        "shape",
        "layout",
        "endianness",
        "producerEvidence",
    }
    if set(row) != required_fields:
        missing = sorted(required_fields - set(row))
        extra = sorted(set(row) - required_fields)
        raise ContractError(
            f"artifacts[{index}] fields differ; missing={missing}, extra={extra}"
        )
    role = row["role"]
    if not isinstance(role, str) or role not in REQUIRED_ROLES:
        raise ContractError(f"artifacts[{index}].role is unknown")
    relative_path, path = _relative_file(root, row["path"], f"artifact {role}")
    size = row["bytes"]
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise ContractError(f"artifact {role} bytes must be a nonnegative integer")
    if path.stat().st_size != size:
        raise ContractError(f"artifact {role} byte size differs")
    expected_digest = _require_sha256(row["sha256"], f"artifact {role} sha256")
    if _sha256(path) != expected_digest:
        raise ContractError(f"artifact {role} SHA-256 differs")
    dtype = row["dtype"]
    if not isinstance(dtype, str) or not dtype:
        raise ContractError(f"artifact {role} dtype must be nonempty")
    shape_value = row["shape"]
    if (
        not isinstance(shape_value, list)
        or not shape_value
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in shape_value
        )
    ):
        raise ContractError(f"artifact {role} shape must contain positive integers")
    layout = row["layout"]
    if not isinstance(layout, str) or not layout:
        raise ContractError(f"artifact {role} layout must be nonempty")
    endianness = row["endianness"]
    if endianness not in {"little", "not-applicable"}:
        raise ContractError(f"artifact {role} endianness is unsupported")
    producer = _require_object(row["producerEvidence"], f"artifact {role} producer")
    if set(producer) != {"path", "sha256"}:
        raise ContractError(f"artifact {role} producer fields differ")
    producer_relative, producer_path = _relative_file(
        root, producer["path"], f"artifact {role} producer"
    )
    producer_digest = _require_sha256(
        producer["sha256"], f"artifact {role} producer sha256"
    )
    if _sha256(producer_path) != producer_digest:
        raise ContractError(f"artifact {role} producer SHA-256 differs")
    return Artifact(
        role=role,
        relative_path=relative_path,
        path=path,
        size=size,
        sha256=expected_digest,
        dtype=dtype,
        shape=tuple(shape_value),
        layout=layout,
        endianness=endianness,
        producer_path=producer_relative,
        producer_sha256=producer_digest,
    )


def inspect_lock(lock_path: pathlib.Path) -> tuple[dict[str, Any], list[Artifact]]:
    if lock_path.is_symlink() or not lock_path.is_file():
        raise ContractError("input lock must be a regular non-symlink file")
    raw_bytes = lock_path.read_bytes()
    try:
        lock = json.loads(raw_bytes, object_pairs_hook=_reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f"input lock is not valid UTF-8 JSON: {error}") from error
    lock = _require_object(lock, "input lock")
    if raw_bytes != _canonical_bytes(lock):
        raise ContractError("input lock is not canonical JSON")
    required_top = {"schema", "experimentId", "population", "runtime", "artifacts"}
    if set(lock) != required_top:
        raise ContractError("input lock top-level fields differ")
    if lock["schema"] != SCHEMA:
        raise ContractError("input lock schema differs")
    if lock["experimentId"] != EXPECTED_EXPERIMENT:
        raise ContractError("input lock experiment identity differs")

    population = _require_object(lock["population"], "population")
    if set(population) != {
        "symbols",
        "segments",
        "segmentLength",
        "firstHalfLength",
        "streams",
        "parameterCount",
    }:
        raise ContractError("population fields differ")
    _require_int(population["symbols"], EXPECTED_SYMBOLS, "population.symbols")
    _require_int(population["segments"], EXPECTED_SEGMENTS, "population.segments")
    _require_int(
        population["segmentLength"],
        EXPECTED_SEGMENT_LENGTH,
        "population.segmentLength",
    )
    _require_int(
        population["firstHalfLength"],
        EXPECTED_FIRST_HALF,
        "population.firstHalfLength",
    )
    _require_int(population["streams"], EXPECTED_STREAMS, "population.streams")
    _require_int(
        population["parameterCount"],
        EXPECTED_PARAMETERS,
        "population.parameterCount",
    )

    runtime = _require_object(lock["runtime"], "runtime")
    if set(runtime) != {"threads", "networkAllowed", "closedRuntimeAllowed"}:
        raise ContractError("runtime fields differ")
    _require_int(runtime["threads"], 1, "runtime.threads")
    if runtime["networkAllowed"] is not False:
        raise ContractError("runtime.networkAllowed must be false")
    if runtime["closedRuntimeAllowed"] is not False:
        raise ContractError("runtime.closedRuntimeAllowed must be false")
    for variable in THREAD_ENVIRONMENT:
        value = os.environ.get(variable)
        if value not in {None, "", "1"}:
            raise ContractError(f"{variable} must be unset or 1")

    rows = lock["artifacts"]
    if not isinstance(rows, list):
        raise ContractError("artifacts must be an array")
    artifacts = [
        _parse_artifact(lock_path.parent, row, index)
        for index, row in enumerate(rows)
    ]
    roles = [artifact.role for artifact in artifacts]
    if len(roles) != len(set(roles)):
        raise ContractError("artifact roles must be unique")
    if set(roles) != REQUIRED_ROLES:
        raise ContractError(
            "artifact role closure differs; "
            f"missing={sorted(REQUIRED_ROLES - set(roles))}"
        )
    paths = [artifact.relative_path for artifact in artifacts]
    if len(paths) != len(set(paths)):
        raise ContractError("artifact paths must be unique")
    if roles != sorted(roles):
        raise ContractError("artifacts must be ordered lexicographically by role")
    return lock, artifacts


def _write_receipt(path: pathlib.Path, receipt: dict[str, Any]) -> None:
    if path.exists():
        raise ContractError("receipt path already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}")
    try:
        with temporary.open("xb") as output:
            output.write(_canonical_bytes(receipt))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--input-lock", required=True, type=pathlib.Path)
    parser.add_argument(
        "--mode",
        required=True,
        choices=("inspect", "replay", "compare", "repeat-compare"),
    )
    parser.add_argument("--arm", choices=("O", "K", "F", "S"))
    parser.add_argument("--output-root", type=pathlib.Path)
    parser.add_argument("--arm-receipts")
    parser.add_argument("--first", type=pathlib.Path)
    parser.add_argument("--second", type=pathlib.Path)
    parser.add_argument("--receipt", required=True, type=pathlib.Path)
    return parser


def _unimplemented(mode: str) -> NoReturn:
    raise ContractError(
        f"mode {mode} is sealed dormant: production parity and complete "
        "population/state closure are absent"
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        lock, artifacts = inspect_lock(args.input_lock)
        if args.mode != "inspect":
            _unimplemented(args.mode)
        if any(
            value is not None
            for value in (
                args.arm,
                args.output_root,
                args.arm_receipts,
                args.first,
                args.second,
            )
        ):
            raise ContractError("inspect mode rejects replay-only arguments")
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "experimentId": EXPECTED_EXPERIMENT,
            "inputLock": {
                "bytes": args.input_lock.stat().st_size,
                "sha256": _sha256(args.input_lock),
            },
            "artifactCount": len(artifacts),
            "artifactBytes": sum(artifact.size for artifact in artifacts),
            "artifactAggregateSha256": hashlib.sha256(
                b"".join(bytes.fromhex(artifact.sha256) for artifact in artifacts)
            ).hexdigest(),
            "population": lock["population"],
            "inputClosurePass": True,
            "executionAuthorized": False,
            "compressionCreditBytes": 0,
            "terminalClassification": "source_closure_incomplete",
        }
        _write_receipt(args.receipt, receipt)
        return 0
    except (ContractError, OSError) as error:
        print(f"input closure rejected: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
