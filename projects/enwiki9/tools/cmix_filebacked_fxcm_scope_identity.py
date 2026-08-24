#!/usr/bin/env python3
"""Run guarded parent/q1 reset-state probability-identity scopes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from typing import Any


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-scope-identity.v2"
BUILD_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-scope-build.v1"
LOCK_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-program-lock-verification.v1"
CONTROL_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-negative-controls.v2"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PARENT_ID = "cmix_obias_source_full1g_roundtrip_a_qm0_v1"
CANONICAL_BYTES = 1_000_000_000
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
SCOPES = ((0, 250_000), (500_000_000, 250_000), (999_750_000, 250_000))
RSS_LIMIT_KIB = 9_765_625
TEMPORARY_DISK_LIMIT_BYTES = 100_000_000_000
TRACE_RECORD_BYTES = 56
TRACE_BYTE_RECORD_BYTES = 5
FORBIDDEN_MEMORY_FILESYSTEMS = {"tmpfs", "ramfs"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def load_json(path: Path, label: str) -> tuple[Path, dict[str, Any]]:
    regular = existing_regular(path, label)
    value = json.loads(regular.read_text(encoding="ascii"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be a JSON object")
    return regular, value


def no_symlink_components(path: Path, label: str) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        if current.is_symlink():
            raise RuntimeError(f"{label} has a symlink component: {current}")


def existing_regular(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    no_symlink_components(path, label)
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} must be a single-link regular file")
    return path.resolve(strict=True)


def existing_directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    no_symlink_components(path, label)
    metadata = path.stat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise RuntimeError(f"{label} must be a directory")
    return path.resolve(strict=True)


def absent_root(path: Path, label: str) -> tuple[Path, str]:
    if not path.is_absolute() or path.exists() or path.is_symlink():
        raise RuntimeError(f"{label} must be an absent absolute path")
    parent = existing_directory(path.parent, f"{label} parent")
    resolved = parent / path.name
    fs_type = subprocess.run(
        ["/usr/bin/stat", "-f", "-c", "%T", str(parent)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin"},
    ).stdout.decode("ascii").strip().lower()
    if fs_type in FORBIDDEN_MEMORY_FILESYSTEMS:
        raise RuntimeError(f"{label} parent uses forbidden memory filesystem {fs_type}")
    return resolved, fs_type


def verify_artifact_record(record: Any, label: str) -> Path:
    if not isinstance(record, dict):
        raise RuntimeError(f"{label} artifact record is missing")
    path = existing_regular(Path(str(record.get("path", ""))), label)
    if path.stat().st_size != record.get("bytes") or sha256_file(path) != record.get("sha256"):
        raise RuntimeError(f"{label} artifact identity mismatch")
    return path


def controls_pass(value: dict[str, Any]) -> bool:
    controls = value.get("controls")
    if not isinstance(controls, dict) or len(controls) != 15:
        return False
    required = (
        "expected_failure_observed",
        "expected_residual_set_pass",
        "expected_residual_shape_pass",
        "foreign_files_unchanged",
        "preexisting_entries_unchanged",
    )
    return all(
        isinstance(control, dict) and all(control.get(field) is True for field in required)
        for control in controls.values()
    )


def package_paths(build: dict[str, Any]) -> tuple[dict[str, Path], dict[str, Any]]:
    if build.get("schema") != BUILD_SCHEMA or build.get("candidate_id") != CANDIDATE_ID:
        raise RuntimeError("scope build receipt identity mismatch")
    if build.get("package_asset_identity_pass") is not True:
        raise RuntimeError("scope package assets did not pass identity")
    packages = build.get("packages")
    if not isinstance(packages, list) or len(packages) != 2:
        raise RuntimeError("scope build receipt must bind two packages")
    paths: dict[str, Path] = {}
    records: dict[str, Any] = {}
    for package in packages:
        if not isinstance(package, dict) or package.get("arm") not in {"parent", "candidate"}:
            raise RuntimeError("scope build package arm is invalid")
        arm = package["arm"]
        if arm in paths:
            raise RuntimeError("duplicate scope build package arm")
        paths[arm] = verify_artifact_record(package.get("packaged_binary"), f"{arm} package")
        records[arm] = package
    for field in ("dictionary_payload", "article_order_payload", "header"):
        parent = records["parent"][field]
        candidate = records["candidate"][field]
        if parent.get("bytes") != candidate.get("bytes") or parent.get("sha256") != candidate.get("sha256"):
            raise RuntimeError(f"parent/candidate package asset mismatch: {field}")
    return paths, records


def copy_slice(corpus: Path, output: Path, offset: int, length: int) -> str:
    digest = hashlib.sha256()
    remaining = length
    with corpus.open("rb") as source, output.open("xb") as target:
        source.seek(offset)
        while remaining:
            block = source.read(min(8 * 1024 * 1024, remaining))
            if not block:
                raise RuntimeError(f"short canonical corpus read at offset {offset}")
            target.write(block)
            digest.update(block)
            remaining -= len(block)
        target.flush()
        os.fsync(target.fileno())
    return digest.hexdigest()


def write_new(path: Path, value: dict[str, Any]) -> None:
    data = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        if os.write(descriptor, data) != len(data):
            raise OSError("short receipt write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def run_guarded(
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
        "/usr/bin/taskset", "--cpu-list", str(cpu),
        sys.executable,
        str(guard_tool),
        "--limit-kib", str(RSS_LIMIT_KIB),
        "--limit-mode", "tree",
        "--official-decimal-limit-kib", str(RSS_LIMIT_KIB),
        "--sample-interval", "0.25",
        "--scratch-path", str(scratch_root),
        "--temporary-disk-limit-bytes", str(TEMPORARY_DISK_LIMIT_BYTES),
        "--max-logical-cpus", "1",
        "--guard-json", str(guard_receipt),
        "--label", label,
        "--phase", "diagnostic",
        "--",
        *command,
    ]
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        completed = subprocess.run(argv, cwd=cwd, env=environment, stdout=stdout, stderr=stderr, check=False)
    _, guard = load_json(guard_receipt, f"{label} resource guard")
    return completed.returncode, guard


def guard_pass(value: dict[str, Any]) -> bool:
    return (
        value.get("schema") == "gamma.enwiki9.resource-guard-receipt.v2"
        and value.get("status") == "complete"
        and value.get("returncode") == 0
        and value.get("rss_guard_exceeded") is False
        and value.get("official_decimal_memory_exceeded") is False
        and value.get("temporary_disk_guard_exceeded") is False
        and value.get("logical_cpu_guard_exceeded") is False
    )


def parse_trace(trace_root: Path, retained_root: Path, aggregate: "hashlib._Hash") -> dict[str, Any]:
    files = sorted(path for path in trace_root.iterdir() if path.is_file())
    if len(files) != 3 or {path.suffix for path in files} != {".res", ".bytes", ".meta"}:
        raise RuntimeError("expected exactly one complete KH_TRACE trio")
    stems = {path.stem for path in files}
    if len(stems) != 1:
        raise RuntimeError("KH_TRACE trio stems differ")
    source_meta = next(path for path in files if path.suffix == ".meta")
    source_res = source_meta.with_suffix(".res")
    source_bytes = source_meta.with_suffix(".bytes")
    meta: dict[str, str] = {}
    for line in source_meta.read_text(encoding="ascii").splitlines():
        key, separator, value = line.partition("=")
        if not separator or key in meta:
            raise RuntimeError("malformed or duplicate KH_TRACE metadata")
        meta[key] = value
    expected = {
        "format": "res_v3",
        "record_bytes": str(TRACE_RECORD_BYTES),
        "n_stage1": "25",
        "elem": "f16",
        "endian": "little",
        "truncated": "0",
    }
    if any(meta.get(key) != value for key, value in expected.items()):
        raise RuntimeError("KH_TRACE static contract or truncation mismatch")
    bit_records = int(meta["total_bit_records"])
    byte_records = int(meta["total_byte_records"])
    if bit_records <= 0 or bit_records != 8 * byte_records:
        raise RuntimeError("KH_TRACE bit/byte record geometry mismatch")
    if source_res.stat().st_size != bit_records * TRACE_RECORD_BYTES:
        raise RuntimeError("KH_TRACE residual byte size mismatch")
    if source_bytes.stat().st_size != byte_records * TRACE_BYTE_RECORD_BYTES:
        raise RuntimeError("KH_TRACE byte-tier size mismatch")
    probability = hashlib.sha256()
    with source_res.open("rb") as stream:
        while block := stream.read(TRACE_RECORD_BYTES * 65_536):
            if len(block) % TRACE_RECORD_BYTES:
                raise RuntimeError("partial KH_TRACE residual record")
            count = len(block) // TRACE_RECORD_BYTES
            packed = bytearray(count * 2)
            packed[0::2] = block[0::TRACE_RECORD_BYTES]
            packed[1::2] = block[1::TRACE_RECORD_BYTES]
            probability.update(packed)
            aggregate.update(packed)
    retained_root.mkdir(mode=0o700)
    retained: dict[str, dict[str, Any]] = {}
    for source in (source_res, source_bytes, source_meta):
        target = retained_root / source.name
        os.replace(source, target)
        retained[source.suffix[1:]] = artifact(target)
    return {
        "format": "res_v3",
        "record_bytes": TRACE_RECORD_BYTES,
        "bit_records": bit_records,
        "byte_records": byte_records,
        "truncated": False,
        "integer_probability_stream_sha256": probability.hexdigest(),
        "residual_trace": retained["res"],
        "byte_trace": retained["bytes"],
        "metadata": retained["meta"],
    }


def directory_empty(path: Path) -> bool:
    return path.is_dir() and next(path.iterdir(), None) is None


def run_arm(
    arm: str,
    package: Path,
    corpus: Path,
    offset: int,
    length: int,
    result_root: Path,
    scratch_root: Path,
    guard_tool: Path,
    head_blob: Path,
    cpu: int,
    aggregate: "hashlib._Hash",
) -> tuple[str, dict[str, Any]]:
    scope_name = f"scope-{offset:09d}-{arm}"
    arm_result = result_root / scope_name
    arm_result.mkdir(mode=0o700)
    encode_root = scratch_root / f"{scope_name}-encode"
    encode_root.mkdir(mode=0o700)
    local_cmix = encode_root / "cmix"
    local_head = encode_root / "head.blob"
    shutil.copyfile(package, local_cmix)
    shutil.copyfile(head_blob, local_head)
    local_cmix.chmod(0o755)
    input_path = encode_root / "enwik9"
    slice_sha256 = copy_slice(corpus, input_path, offset, length)
    trace_root = encode_root / "trace"
    trace_root.mkdir(mode=0o700)
    backing_root: Path | None = None
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
        "KH_BITLSTM32": str(local_head),
        "KH_TRACE_DIR": str(trace_root),
    }
    if arm == "candidate":
        backing_root = scratch_root / f"{scope_name}-encode-backing"
        backing_root.mkdir(mode=0o700)
        environment["GAMMA_FXCM_BACKING_DIR"] = str(backing_root)
    encode_guard_path = arm_result / "encode-guard.json"
    encode_return, encode_guard = run_guarded(
        ["./cmix", "-e", "enwik9", "out.cmix"],
        encode_root,
        environment,
        guard_tool,
        encode_guard_path,
        arm_result / "encode.stdout",
        arm_result / "encode.stderr",
        scratch_root,
        f"{CANDIDATE_ID}-{scope_name}-encode",
        cpu,
    )
    if encode_return != 0 or not guard_pass(encode_guard):
        raise RuntimeError(f"{scope_name} encode or resource guard failed")
    payload = encode_root / "out.cmix"
    archive = encode_root / "archive9"
    if not payload.is_file() or not archive.is_file():
        raise RuntimeError(f"{scope_name} encode omitted payload or archive")
    trace = parse_trace(trace_root, arm_result / "trace", aggregate)
    retained_payload = arm_result / "out.cmix"
    retained_archive = arm_result / "archive9"
    os.replace(payload, retained_payload)
    os.replace(archive, retained_archive)
    encode_cleanup = backing_root is None or directory_empty(backing_root)
    if not encode_cleanup:
        raise RuntimeError(f"{scope_name} encode left allocator backing files")
    if backing_root is not None:
        backing_root.rmdir()
    shutil.rmtree(encode_root)

    decode_root = scratch_root / f"{scope_name}-decode"
    decode_root.mkdir(mode=0o700)
    local_archive = decode_root / "archive9"
    shutil.copyfile(retained_archive, local_archive)
    local_archive.chmod(0o755)
    decode_environment = {"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "TZ": "UTC"}
    decode_backing: Path | None = None
    if arm == "candidate":
        decode_backing = scratch_root / f"{scope_name}-decode-backing"
        decode_backing.mkdir(mode=0o700)
        decode_environment["GAMMA_FXCM_BACKING_DIR"] = str(decode_backing)
    decode_guard_path = arm_result / "decode-guard.json"
    decode_return, decode_guard = run_guarded(
        ["./archive9"],
        decode_root,
        decode_environment,
        guard_tool,
        decode_guard_path,
        arm_result / "decode.stdout",
        arm_result / "decode.stderr",
        scratch_root,
        f"{CANDIDATE_ID}-{scope_name}-decode",
        cpu,
    )
    if decode_return != 0 or not guard_pass(decode_guard):
        raise RuntimeError(f"{scope_name} decode or resource guard failed")
    restored = decode_root / "enwik9_uncompressed"
    if not restored.is_file():
        raise RuntimeError(f"{scope_name} decode omitted its restored stream")
    raw_slice_inverse = restored.stat().st_size == length and sha256_file(restored) == slice_sha256
    retained_restored = arm_result / "enwik9_uncompressed"
    os.replace(restored, retained_restored)
    decode_cleanup = decode_backing is None or directory_empty(decode_backing)
    if not decode_cleanup:
        raise RuntimeError(f"{scope_name} decode left allocator backing files")
    if decode_backing is not None:
        decode_backing.rmdir()
    shutil.rmtree(decode_root)
    return slice_sha256, {
        "arm": arm,
        "packaged_binary": artifact(package),
        "encode_return_code": encode_return,
        "encode_guard": artifact(encode_guard_path),
        "encode_guard_pass": True,
        "payload": artifact(retained_payload),
        "archive": artifact(retained_archive),
        "trace": trace,
        "decode_return_code": decode_return,
        "decode_guard": artifact(decode_guard_path),
        "decode_guard_pass": True,
        "restored": artifact(retained_restored),
        "raw_slice_inverse_pass": raw_slice_inverse,
        "backing_cleanup_pass": encode_cleanup and decode_cleanup,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-receipt", type=Path, required=True)
    parser.add_argument("--program-lock-verification", type=Path, required=True)
    parser.add_argument("--allocator-controls", type=Path, required=True)
    parser.add_argument("--allocator-positive-fixture", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--resource-guard", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    args = parser.parse_args()

    build_path, build = load_json(args.build_receipt, "scope build receipt")
    lock_path, lock = load_json(args.program_lock_verification, "program lock verification")
    controls_path, controls = load_json(args.allocator_controls, "allocator controls")
    positive_path, positive = load_json(args.allocator_positive_fixture, "allocator positive fixture")
    corpus = existing_regular(args.corpus, "canonical corpus")
    guard_tool = existing_regular(args.resource_guard, "resource guard")
    packages, _ = package_paths(build)
    head_blob = verify_artifact_record(build.get("head_blob"), "head blob")
    if lock.get("schema") != LOCK_SCHEMA or lock.get("candidate_id") != CANDIDATE_ID or lock.get("verified") is not True:
        raise RuntimeError("program lock verification did not pass")
    if controls.get("schema") != CONTROL_SCHEMA or controls.get("candidate_id") != CANDIDATE_ID:
        raise RuntimeError("allocator control receipt identity mismatch")
    if controls.get("shared_source_identity_pass") is not True or not controls_pass(controls):
        raise RuntimeError("all 15 allocator negative controls did not pass")
    if positive.get("pass") is not True or positive.get("return_code") != 0:
        raise RuntimeError("allocator positive fixture did not pass")
    if corpus.stat().st_size != CANONICAL_BYTES or sha256_file(corpus) != CANONICAL_SHA256:
        raise RuntimeError("canonical enwik9 identity mismatch")
    result_root, result_fs = absent_root(args.result_root, "result root")
    scratch_root, scratch_fs = absent_root(args.scratch_root, "scratch root")
    if result_root == scratch_root or result_root in scratch_root.parents or scratch_root in result_root.parents:
        raise RuntimeError("result and scratch roots must be disjoint")
    result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)
    receipt_path = result_root / "scope-identity-receipt.json"
    cpu = min(os.sched_getaffinity(0))
    scopes: list[dict[str, Any]] = []
    aggregate = {arm: hashlib.sha256() for arm in ("parent", "candidate")}
    errors: list[str] = []
    try:
        for offset, length in SCOPES:
            for arm in ("parent", "candidate"):
                aggregate[arm].update(offset.to_bytes(8, "little"))
                aggregate[arm].update(length.to_bytes(8, "little"))
            parent_slice, parent = run_arm(
                "parent", packages["parent"], corpus, offset, length, result_root,
                scratch_root, guard_tool, head_blob, cpu, aggregate["parent"],
            )
            candidate_slice, candidate = run_arm(
                "candidate", packages["candidate"], corpus, offset, length, result_root,
                scratch_root, guard_tool, head_blob, cpu, aggregate["candidate"],
            )
            if parent_slice != candidate_slice:
                raise RuntimeError("parent/candidate slice identity mismatch")
            probability_identity = (
                parent["trace"]["integer_probability_stream_sha256"]
                == candidate["trace"]["integer_probability_stream_sha256"]
            )
            trace_identity = (
                parent["trace"]["residual_trace"]["sha256"] == candidate["trace"]["residual_trace"]["sha256"]
                and parent["trace"]["byte_trace"]["sha256"] == candidate["trace"]["byte_trace"]["sha256"]
            )
            payload_identity = parent["payload"]["sha256"] == candidate["payload"]["sha256"]
            raw_slice_inverse_required = offset == 0
            raw_slice_inverse = (
                parent["raw_slice_inverse_pass"] and candidate["raw_slice_inverse_pass"]
            )
            decoded_identity = (
                parent["restored"]["bytes"] == candidate["restored"]["bytes"]
                and parent["restored"]["sha256"] == candidate["restored"]["sha256"]
            )
            diagnostic_decode_pass = decoded_identity and (
                raw_slice_inverse if raw_slice_inverse_required else True
            )
            scope_pass = (
                probability_identity and trace_identity and payload_identity
                and diagnostic_decode_pass
            )
            scopes.append({
                "offset": offset,
                "bytes": length,
                "slice_sha256": parent_slice,
                "arms": [parent, candidate],
                "integer_probability_identity_pass": probability_identity,
                "full_trace_identity_pass": trace_identity,
                "payload_identity_pass": payload_identity,
                "within_scope_state_trajectory_identity_pass": trace_identity,
                "raw_slice_inverse_required": raw_slice_inverse_required,
                "raw_slice_inverse_pass": raw_slice_inverse,
                "parent_candidate_restored_identity_pass": decoded_identity,
                "diagnostic_decode_identity_pass": diagnostic_decode_pass,
                "scope_pass": scope_pass,
            })
            if not scope_pass:
                raise RuntimeError(f"scope at offset {offset} did not preserve exact behavior")
        if next(scratch_root.iterdir(), None) is not None:
            raise RuntimeError("scratch root is not empty after all scopes")
        scratch_root.rmdir()
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    all_scopes = len(scopes) == len(SCOPES)
    probability_pass = all_scopes and all(scope["integer_probability_identity_pass"] for scope in scopes)
    trace_pass = all_scopes and all(scope["full_trace_identity_pass"] for scope in scopes)
    payload_pass = all_scopes and all(scope["payload_identity_pass"] for scope in scopes)
    opening_inverse_pass = all_scopes and all(
        scope["raw_slice_inverse_pass"]
        for scope in scopes
        if scope["raw_slice_inverse_required"]
    )
    distant_decode_identity_pass = all_scopes and all(
        scope["parent_candidate_restored_identity_pass"]
        for scope in scopes
        if not scope["raw_slice_inverse_required"]
    )
    cleanup_pass = all_scopes and not scratch_root.exists() and all(
        all(arm["backing_cleanup_pass"] for arm in scope["arms"]) for scope in scopes
    )
    resource_pass = all_scopes and all(
        all(arm["encode_guard_pass"] and arm["decode_guard_pass"] for arm in scope["arms"])
        for scope in scopes
    )
    reset_scope_pass = (
        not errors and all_scopes and probability_pass and trace_pass and payload_pass
        and opening_inverse_pass and distant_decode_identity_pass and cleanup_pass
        and resource_pass
    )
    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "authoritative_parent_id": PARENT_ID,
        "population": artifact(corpus),
        "fixed_scopes": [{"offset": offset, "bytes": length} for offset, length in SCOPES],
        "result_filesystem_type": result_fs,
        "scratch_filesystem_type": scratch_fs,
        "selected_logical_cpu": cpu,
        "source_and_controls": {
            "scope_build_receipt": artifact(build_path),
            "program_lock_verification": artifact(lock_path),
            "allocator_negative_controls": artifact(controls_path),
            "allocator_positive_fixture": artifact(positive_path),
            "program_lock_verified": True,
            "allocator_positive_fixture_pass": True,
            "allocator_negative_control_count": 15,
            "allocator_negative_controls_pass": True,
        },
        "event_observation_boundary": {
            "packaged_shared_event_descriptor_used": False,
            "reason": (
                "packaged cmix -e launches two helper cmix processes that inherit a shared "
                "event descriptor and concatenate three independent sequence namespaces; "
                "allocator lifecycle authority comes from the isolated positive fixture and "
                "15 negative controls, while scope runs require empty backing directories"
            ),
        },
        "scopes": scopes,
        "aggregate": {
            "parent_scoped_probability_stream_sha256": aggregate["parent"].hexdigest(),
            "candidate_scoped_probability_stream_sha256": aggregate["candidate"].hexdigest(),
            "scoped_probability_identity_pass": (
                all_scopes and aggregate["parent"].digest() == aggregate["candidate"].digest()
            ),
        },
        "decisions": {
            "all_fixed_scopes_complete": all_scopes,
            "exact_integer_probability_identity_pass": probability_pass,
            "full_trace_identity_pass": trace_pass,
            "payload_identity_pass": payload_pass,
            "opening_both_arms_exact_inverse_pass": opening_inverse_pass,
            "distant_parent_candidate_decode_identity_pass": distant_decode_identity_pass,
            "within_scope_state_trajectory_identity_pass": trace_pass,
            "candidate_backing_cleanup_pass": cleanup_pass,
            "resource_guard_pass": resource_pass,
            "reset_state_scope_identity_pass": reset_scope_pass,
            "full_stream_identity_established": False,
            "persistent_full_corpus_identity_established": False,
            "memory_safe_parent_qualified": False,
            "promotion_authorized": False,
        },
        "errors": errors,
        "terminal_pass": reset_scope_pass,
        "claim_authority": "three_fixed_reset_state_scope_identity_only",
        "claim_boundary": (
            "Exact post-head integer probabilities, complete finite-coder traces, payloads, "
            "and parent/candidate decoded streams are compared on three fixed 250000-byte "
            "corpus slices from cold state. Raw inversion is required only for the opening "
            "slice because the specialized Wikipedia preprocessor is not a standalone raw "
            "inverse for arbitrary interior fragments. This does not establish a full-1G persistent trajectory, full-corpus "
            "resource eligibility, compression gain, package score, or prize qualification."
        ),
        "execution_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    write_new(receipt_path, receipt)
    return 0 if reset_scope_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
