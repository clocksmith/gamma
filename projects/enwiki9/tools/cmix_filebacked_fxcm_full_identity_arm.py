#!/usr/bin/env python3
"""Run one sealed full-corpus CMIX probability/state observer arm."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from typing import Any

import jsonschema

import cmix_filebacked_fxcm_100m_identity_resource_verify as proof
import cmix_filebacked_fxcm_100m_observer_calibrate as calibration
import cmix_filebacked_fxcm_scope_identity as scope


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity-arm.v1"
BUILD_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-100m-observer-build.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
CANONICAL_BYTES = 1_000_000_000
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
FIXED_MODELED_CHECKPOINTS = (
    16_777_216,
    33_554_432,
    50_331_648,
    100_000_000,
    500_000_000,
)
EXPECTED_RANGES = 26
MINIMUM_RANGE_BYTES = 64 * 1024 * 1024
DIAGNOSTIC_RSS_LIMIT_KIB = 11_500_000
TEMPORARY_DISK_LIMIT_BYTES = 100_000_000_000


def artifact(path: Path) -> dict[str, Any]:
    return scope.artifact(path)


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(value) for value in argv)).hexdigest()


def load_json_lines(path: Path, label: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"{label} line {line_number}: {error}") from error
        if not isinstance(value, dict):
            raise RuntimeError(f"{label} line {line_number} is not an object")
        records.append(value)
    return records


def valid_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return True


def parse_observer_outputs(observer_root: Path) -> dict[str, Any]:
    probability_path = scope.existing_regular(
        observer_root / "probability.json", "full probability summary"
    )
    coder_path = scope.existing_regular(
        observer_root / "coder-checkpoints.jsonl", "full coder checkpoints"
    )
    state_path = scope.existing_regular(
        observer_root / "persistent-state.jsonl", "full persistent state"
    )
    probability = json.loads(probability_path.read_text(encoding="ascii"))
    if not isinstance(probability, dict):
        raise RuntimeError("full probability summary is not an object")
    modeled_bytes = probability.get("completed_coded_bytes")
    probability_sha256 = probability.get("post_head_probability_sha256")
    if (
        set(probability)
        != {
            "coded_bits",
            "completed_coded_bytes",
            "post_head_probability_sha256",
        }
        or not isinstance(modeled_bytes, int)
        or modeled_bytes <= FIXED_MODELED_CHECKPOINTS[-1]
        or probability.get("coded_bits") != modeled_bytes * 8
        or not valid_sha256(probability_sha256)
    ):
        raise RuntimeError("full probability summary geometry mismatch")

    checkpoints = (0, *FIXED_MODELED_CHECKPOINTS, modeled_bytes)
    kinds = ("start", *("fixed" for _ in FIXED_MODELED_CHECKPOINTS), "terminal")
    coder = load_json_lines(coder_path, "full coder checkpoints")
    if len(coder) != len(checkpoints):
        raise RuntimeError("full coder checkpoint count mismatch")
    coder_summary: list[dict[str, Any]] = []
    for index, (record, checkpoint, kind) in enumerate(zip(coder, checkpoints, kinds)):
        if (
            set(record)
            != {
                "coded_bits",
                "completed_coded_bytes",
                "high",
                "kind",
                "low",
                "payload_bytes",
                "probability_sha256",
            }
            or record.get("kind") != kind
            or record.get("completed_coded_bytes") != checkpoint
            or record.get("coded_bits") != checkpoint * 8
            or not valid_sha256(record.get("probability_sha256"))
            or not all(
                isinstance(record.get(name), int) and record[name] >= 0
                for name in ("low", "high", "payload_bytes")
            )
            or record["low"] > 0xFFFFFFFF
            or record["high"] > 0xFFFFFFFF
        ):
            raise RuntimeError(f"full coder checkpoint {index} geometry mismatch")
        coder_summary.append(
            {
                "modeled_bytes": checkpoint,
                "kind": kind,
                "coded_bits": record["coded_bits"],
                "low": record["low"],
                "high": record["high"],
                "payload_bytes": record["payload_bytes"],
                "probability_sha256": record["probability_sha256"],
            }
        )
    if coder_summary[-1]["probability_sha256"] != probability_sha256:
        raise RuntimeError("terminal coder probability digest mismatch")

    state = load_json_lines(state_path, "full persistent state")
    records_per_checkpoint = EXPECTED_RANGES + 1
    if len(state) != len(checkpoints) * records_per_checkpoint:
        raise RuntimeError("full persistent-state record count mismatch")
    frozen_geometry: tuple[tuple[int, int], ...] | None = None
    state_summary: list[dict[str, Any]] = []
    for checkpoint_index, (checkpoint, kind) in enumerate(zip(checkpoints, kinds)):
        begin = checkpoint_index * records_per_checkpoint
        chunk = state[begin : begin + records_per_checkpoint]
        ranges = chunk[:-1]
        manifest = chunk[-1]
        geometry: list[tuple[int, int]] = []
        aggregate = hashlib.sha256()
        for ordinal, record in enumerate(ranges):
            byte_count = record.get("bytes")
            alignment = record.get("alignment")
            range_sha256 = record.get("sha256")
            if (
                set(record)
                != {"alignment", "bytes", "checkpoint", "kind", "ordinal", "sha256"}
                or record.get("checkpoint") != checkpoint
                or record.get("kind") != kind
                or record.get("ordinal") != ordinal
                or not isinstance(byte_count, int)
                or byte_count < MINIMUM_RANGE_BYTES
                or not isinstance(alignment, int)
                or alignment <= 0
                or alignment & (alignment - 1)
                or not valid_sha256(range_sha256)
            ):
                raise RuntimeError(
                    f"full state checkpoint {checkpoint_index} range {ordinal} mismatch"
                )
            geometry.append((byte_count, alignment))
            aggregate.update(struct.pack("<Q", ordinal))
            aggregate.update(struct.pack("<Q", byte_count))
            aggregate.update(struct.pack("<Q", alignment))
            aggregate.update(bytes.fromhex(range_sha256))
        geometry_tuple = tuple(geometry)
        if frozen_geometry is None:
            frozen_geometry = geometry_tuple
        elif geometry_tuple != frozen_geometry:
            raise RuntimeError("semantic range geometry changed between checkpoints")
        if (
            set(manifest)
            != {"allocation_count", "checkpoint", "kind", "manifest_sha256"}
            or manifest.get("allocation_count") != EXPECTED_RANGES
            or manifest.get("checkpoint") != checkpoint
            or manifest.get("kind") != kind
            or manifest.get("manifest_sha256") != aggregate.hexdigest()
        ):
            raise RuntimeError(
                f"full state checkpoint {checkpoint_index} manifest mismatch"
            )
        state_summary.append(
            {
                "modeled_bytes": checkpoint,
                "kind": kind,
                "allocation_count": EXPECTED_RANGES,
                "manifest_sha256": aggregate.hexdigest(),
            }
        )
    return {
        "modeled_bytes": modeled_bytes,
        "coded_bits": modeled_bytes * 8,
        "probability_sha256": probability_sha256,
        "coder_checkpoints": coder_summary,
        "state_checkpoints": state_summary,
        "probability_manifest": artifact(probability_path),
        "coder_manifest": artifact(coder_path),
        "state_manifest": artifact(state_path),
    }


def run_guarded(
    *,
    command: list[str],
    cwd: Path,
    environment: dict[str, str],
    guard_tool: Path,
    guard_receipt: Path,
    stdout_path: Path,
    stderr_path: Path,
    scratch_root: Path,
    label: str,
    cpu: int,
) -> tuple[int, dict[str, Any]]:
    argv = [
        "/usr/bin/taskset",
        "--cpu-list",
        str(cpu),
        sys.executable,
        str(guard_tool),
        "--limit-kib",
        str(DIAGNOSTIC_RSS_LIMIT_KIB),
        "--limit-mode",
        "tree",
        "--sample-interval",
        "0.25",
        "--scratch-path",
        str(scratch_root),
        "--temporary-disk-limit-bytes",
        str(TEMPORARY_DISK_LIMIT_BYTES),
        "--max-logical-cpus",
        "1",
        "--guard-json",
        str(guard_receipt),
        "--label",
        label,
        "--phase",
        "diagnostic",
        "--",
        *command,
    ]
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=environment,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    _, guard = scope.load_json(guard_receipt, f"{label} guard receipt")
    return completed.returncode, guard


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=("parent", "q1"), required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--observer-build-receipt", type=Path, required=True)
    parser.add_argument("--observer-build-schema", type=Path, required=True)
    parser.add_argument("--resource-guard", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--receipt-schema", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--cpu", type=int, required=True)
    args = parser.parse_args()

    proof.require_released_lease(args.exclusive_lease)
    corpus = scope.existing_regular(args.corpus, "canonical full corpus")
    if corpus.stat().st_size != CANONICAL_BYTES or scope.sha256_file(corpus) != CANONICAL_SHA256:
        raise RuntimeError("canonical full corpus identity mismatch")
    guard_tool = scope.existing_regular(args.resource_guard, "diagnostic resource guard")
    build_path, build = scope.load_json(args.observer_build_receipt, "observer build")
    build_schema_path, build_schema = scope.load_json(
        args.observer_build_schema, "observer build schema"
    )
    if build.get("schema") != BUILD_SCHEMA:
        raise RuntimeError("observer build schema identity mismatch")
    jsonschema.Draft202012Validator.check_schema(build_schema)
    jsonschema.validate(build, build_schema)
    packages, head_blob = calibration.packages_from_build(build)
    package = packages["parent" if args.role == "parent" else "candidate"]
    receipt_schema_path, receipt_schema = scope.load_json(
        args.receipt_schema, "full identity arm schema"
    )
    jsonschema.Draft202012Validator.check_schema(receipt_schema)
    if args.cpu not in os.sched_getaffinity(0):
        raise RuntimeError("selected CPU is outside full-arm affinity")
    result_root, _ = scope.absent_root(args.result_root, "full-arm result root")
    scratch_root, _ = scope.absent_root(args.scratch_root, "full-arm scratch root")
    if (
        result_root == scratch_root
        or result_root in scratch_root.parents
        or scratch_root in result_root.parents
    ):
        raise RuntimeError("full-arm result and scratch roots must be disjoint")
    result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)

    encode_root = scratch_root / "encode"
    encode_root.mkdir(mode=0o700)
    local_cmix = encode_root / "cmix"
    local_head = encode_root / "head.blob"
    local_input = encode_root / "enwik9"
    shutil.copyfile(package, local_cmix)
    shutil.copyfile(head_blob, local_head)
    shutil.copyfile(corpus, local_input)
    local_cmix.chmod(0o700)
    observer_root = result_root / "observer"
    observer_root.mkdir(mode=0o700)
    transformed_input = result_root / "transformed-input"
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
        "KH_BITLSTM32": str(local_head),
        "GAMMA_FULL_IDENTITY_DIR": str(observer_root),
        "GAMMA_FULL_IDENTITY_EXTENDED_CHECKPOINTS": "1",
        "GAMMA_FULL_IDENTITY_TRANSFORMED_INPUT": str(transformed_input),
    }
    backing_root: Path | None = None
    if args.role == "q1":
        backing_root = scratch_root / "backing"
        backing_root.mkdir(mode=0o700)
        environment["GAMMA_FXCM_BACKING_DIR"] = str(backing_root)
    guard_path = result_root / "encode-guard.json"
    command = ["./cmix", "-e", "enwik9", "out.cmix"]
    return_code, guard = run_guarded(
        command=command,
        cwd=encode_root,
        environment=environment,
        guard_tool=guard_tool,
        guard_receipt=guard_path,
        stdout_path=result_root / "encode.stdout",
        stderr_path=result_root / "encode.stderr",
        scratch_root=scratch_root,
        label=f"{CANDIDATE_ID}-full-identity-{args.role}",
        cpu=args.cpu,
    )
    if return_code != 0 or not scope.guard_pass(guard):
        raise RuntimeError(f"full {args.role} observer encode or guard failed")

    payload_source = scope.existing_regular(encode_root / "out.cmix", "full payload")
    archive_source = scope.existing_regular(encode_root / "archive9", "full archive")
    payload = result_root / "out.cmix"
    archive = result_root / "archive9"
    os.replace(payload_source, payload)
    os.replace(archive_source, archive)
    transformed_input = scope.existing_regular(transformed_input, "full transformed input")
    observed = parse_observer_outputs(observer_root)
    if transformed_input.stat().st_size != observed["modeled_bytes"]:
        raise RuntimeError("transformed stream size differs from observer terminal byte")
    backing_cleanup = backing_root is None or scope.directory_empty(backing_root)
    if not backing_cleanup:
        raise RuntimeError("file-backed observer arm left backing files")
    if backing_root is not None:
        backing_root.rmdir()
    shutil.rmtree(encode_root)
    if next(scratch_root.iterdir(), None) is not None:
        raise RuntimeError("full identity arm scratch residue survived")
    scratch_root.rmdir()

    receipt = {
        "schema": SCHEMA,
        "role": args.role,
        "candidate_id": CANDIDATE_ID,
        "runner": artifact(Path(__file__).resolve(strict=True)),
        "receipt_schema": artifact(receipt_schema_path),
        "command_sha256": command_sha256([sys.executable, *sys.argv]),
        "population": artifact(corpus),
        "observer_build_receipt": artifact(build_path),
        "observer_build_schema": artifact(build_schema_path),
        "binary": artifact(package),
        "head": artifact(head_blob),
        "return_code": return_code,
        "selected_logical_cpu": args.cpu,
        "scratch_root": str(scratch_root),
        "resource_guard": artifact(guard_path),
        "diagnostic_rss_limit_kib": DIAGNOSTIC_RSS_LIMIT_KIB,
        "modeled_stream": artifact(transformed_input),
        "coded_bits": observed["coded_bits"],
        "probability_sha256": observed["probability_sha256"],
        "coder_checkpoints": observed["coder_checkpoints"],
        "state_checkpoints": observed["state_checkpoints"],
        "payload": artifact(payload),
        "self_extracting_archive": artifact(archive),
        "observer_outputs": {
            "probability_manifest": observed["probability_manifest"],
            "coder_manifest": observed["coder_manifest"],
            "state_manifest": observed["state_manifest"],
        },
        "backing_cleanup_pass": backing_cleanup,
        "arm_pass": True,
        "claim_boundary": (
            "Diagnostic full-corpus encode identity arm only; memory and runtime are "
            "not prize qualification, and no compression or score credit is granted."
        ),
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.validate(receipt, receipt_schema)
    scope.write_new(result_root / "full-identity-arm-receipt.json", receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
