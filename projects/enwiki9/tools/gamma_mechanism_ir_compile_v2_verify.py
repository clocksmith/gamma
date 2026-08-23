#!/usr/bin/env python3
"""Independently repeat closure-aware compilation and exercise frozen rejections."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Callable


OUTPUT_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir-compilation-verification.v2"


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def regular_file(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise SystemExit(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise SystemExit(f"{label}: expected single-link regular file")
    return absolute.resolve(strict=True)


def require_parent(path: Path, label: str) -> None:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parent.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise SystemExit(f"{label}: unsafe parent component {current}")


def tree(root: Path, errors: list[str], label: str) -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}

    def visit(directory: Path, relative: PurePosixPath) -> None:
        for entry in sorted(os.scandir(directory), key=lambda value: value.name):
            metadata = entry.stat(follow_symlinks=False)
            child = relative / entry.name
            name = child.as_posix()
            if stat.S_ISLNK(metadata.st_mode):
                errors.append(f"{label}: symlink forbidden: {name}")
            elif stat.S_ISDIR(metadata.st_mode):
                visit(Path(entry.path), child)
            elif stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1:
                result[name] = (metadata.st_size, sha256_file(Path(entry.path)))
            elif stat.S_ISREG(metadata.st_mode):
                errors.append(f"{label}: hardlink forbidden: {name}")
            else:
                errors.append(f"{label}: special file forbidden: {name}")

    visit(root, PurePosixPath())
    return result


def manifest_sha256(files: dict[str, tuple[int, str]]) -> str:
    digest = hashlib.sha256()
    for path, (size, file_hash) in sorted(files.items()):
        digest.update(path.encode("ascii"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def run_compiler(
    compiler: Path,
    ir: Path,
    closure: Path,
    lease: Path,
    root: Path,
) -> subprocess.CompletedProcess[bytes]:
    root.mkdir(parents=True)
    environment = {"LANG": "C", "LC_ALL": "C", "PYTHONHASHSEED": "0", "TZ": "UTC"}
    completed = subprocess.run(
        [
            sys.executable,
            os.fspath(compiler),
            "--ir",
            os.fspath(ir),
            "--closure",
            os.fspath(closure),
            "--exclusive-lease",
            os.fspath(lease),
            "--evidence-dir",
            os.fspath(root / "compiler-evidence"),
            "--output-dir",
            os.fspath(root / "artifacts"),
            "--receipt",
            os.fspath(root / "receipt.json"),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    (root / "stdout.bin").write_bytes(completed.stdout)
    (root / "stderr.bin").write_bytes(completed.stderr)
    return completed


def source_after_use(value: dict[str, Any]) -> None:
    value["source_availability"][0]["available_at_event"] = "byte64_rejoin"


def missing_state_role(value: dict[str, Any]) -> None:
    value["state_roles"] = value["state_roles"][:-1]


def raw_d_posterior_write(value: dict[str, Any]) -> None:
    for role in value["state_roles"]:
        if role["state_id"] == "safe_mix_global_posterior":
            role["writable_arms"].append("D")
    for arm in value["arms"]:
        if arm["arm"] == "D":
            arm["event_access"][-1]["write_state_ids"].append("safe_mix_global_posterior")


def mismatched_k_write_set(value: dict[str, Any]) -> None:
    for arm in value["arms"]:
        if arm["arm"] == "K":
            arm["event_access"][-1]["write_state_ids"].remove("safe_mix_global_posterior")


def incomplete_join_discard(value: dict[str, Any]) -> None:
    value["join"]["discard_state_ids"] = value["join"]["discard_state_ids"][:-1]


def incomplete_forbidden_copy(value: dict[str, Any]) -> None:
    value["join"]["forbidden_copy_pairs"] = value["join"]["forbidden_copy_pairs"][:-1]


def unknown_arm_state(value: dict[str, Any]) -> None:
    value["arms"][0]["event_access"][0]["read_state_ids"].append("undeclared_state")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--ir", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()

    compiler = regular_file(args.compiler, "compiler")
    ir = regular_file(args.ir, "IR")
    closure = regular_file(args.closure, "closure")
    lease = regular_file(args.exclusive_lease, "exclusive lease")
    for path, label in ((args.evidence_root, "evidence root"),):
        require_parent(path, label)
        if path.exists() or path.is_symlink():
            raise SystemExit(f"{label} must not already exist")
    require_parent(args.verification, "verification")
    if args.verification.exists() or args.verification.is_symlink():
        raise SystemExit("verification path already exists")
    args.evidence_root.mkdir()

    raw_ir = ir.read_bytes()
    raw_closure = closure.read_bytes()
    try:
        ir_document = json.loads(raw_ir.decode("utf-8"))
        closure_document = json.loads(raw_closure.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"input parse failure: {exc}") from exc
    if not isinstance(ir_document, dict) or not isinstance(closure_document, dict):
        raise SystemExit("IR and closure must be JSON objects")

    errors: list[str] = []
    repeat_a = run_compiler(compiler, ir, closure, lease, args.evidence_root / "repeat-a")
    repeat_b = run_compiler(compiler, ir, closure, lease, args.evidence_root / "repeat-b")
    if repeat_a.returncode != 0:
        errors.append(f"repeat-a return code {repeat_a.returncode}")
    if repeat_b.returncode != 0:
        errors.append(f"repeat-b return code {repeat_b.returncode}")
    receipt_a = args.evidence_root / "repeat-a" / "receipt.json"
    receipt_b = args.evidence_root / "repeat-b" / "receipt.json"
    receipt_identity = receipt_a.is_file() and receipt_b.is_file() and receipt_a.read_bytes() == receipt_b.read_bytes()
    if not receipt_identity:
        errors.append("independent compilation receipts differ")
    artifacts_a_root = args.evidence_root / "repeat-a" / "artifacts"
    artifacts_b_root = args.evidence_root / "repeat-b" / "artifacts"
    artifacts_a = tree(artifacts_a_root, errors, "repeat-a artifacts") if artifacts_a_root.is_dir() else {}
    artifacts_b = tree(artifacts_b_root, errors, "repeat-b artifacts") if artifacts_b_root.is_dir() else {}
    artifact_identity = bool(artifacts_a) and artifacts_a == artifacts_b
    if not artifact_identity:
        errors.append("independent artifact trees differ")

    mutations: dict[str, Callable[[dict[str, Any]], None]] = {
        "source_after_use": source_after_use,
        "missing_state_role": missing_state_role,
        "raw_d_posterior_write": raw_d_posterior_write,
        "mismatched_k_write_set": mismatched_k_write_set,
        "incomplete_join_discard": incomplete_join_discard,
        "incomplete_forbidden_copy": incomplete_forbidden_copy,
        "unknown_arm_state": unknown_arm_state,
    }
    controls: dict[str, dict[str, Any]] = {}
    for name, mutate in mutations.items():
        document = copy.deepcopy(closure_document)
        mutate(document)
        root = args.evidence_root / "negative-controls" / name
        root.mkdir(parents=True)
        bad_closure = root / "closure.json"
        bad_closure.write_bytes(json_bytes(document))
        completed = run_compiler(compiler, ir, bad_closure, lease, root / "run")
        no_final = not (root / "run" / "artifacts").exists() and not (root / "run" / "receipt.json").exists()
        rejected = completed.returncode != 0 and no_final
        if not rejected:
            errors.append(f"negative control {name} was not rejected without final output")
        controls[name] = {
            "return_code": completed.returncode,
            "rejected": rejected,
            "no_final_output_pass": no_final,
            "stdout_sha256": sha256_bytes(completed.stdout),
            "stderr_sha256": sha256_bytes(completed.stderr),
        }

    active_root = args.evidence_root / "negative-controls" / "active_exclusive_lease"
    active_root.mkdir(parents=True)
    active_lease = active_root / "exclusive.json"
    active_lease.write_bytes(json_bytes({"active": True, "candidate_id": "negative-control"}))
    active_run = run_compiler(compiler, ir, closure, active_lease, active_root / "run")
    active_no_final = not (active_root / "run" / "artifacts").exists() and not (active_root / "run" / "receipt.json").exists()
    active_rejected = active_run.returncode != 0 and active_no_final
    if not active_rejected:
        errors.append("active exclusive lease was not rejected without final output")
    controls["active_exclusive_lease"] = {
        "return_code": active_run.returncode,
        "rejected": active_rejected,
        "no_final_output_pass": active_no_final,
        "stdout_sha256": sha256_bytes(active_run.stdout),
        "stderr_sha256": sha256_bytes(active_run.stderr),
    }

    evidence_files = tree(args.evidence_root, errors, "evidence root")
    output = {
        "schema": OUTPUT_SCHEMA,
        "mechanism_id": str(ir_document.get("mechanism_id", "invalid")),
        "verified": not errors,
        "errors": errors,
        "compiler_sha256": sha256_file(compiler),
        "source_ir_sha256": sha256_bytes(raw_ir),
        "causal_closure_sha256": sha256_bytes(raw_closure),
        "repeat": {
            "run_a_return_code": repeat_a.returncode,
            "run_b_return_code": repeat_b.returncode,
            "receipt_identity_pass": receipt_identity,
            "artifact_identity_pass": artifact_identity,
            "artifact_set_sha256": manifest_sha256(artifacts_a),
        },
        "negative_controls": controls,
        "evidence_root": {
            "regular_file_count": len(evidence_files),
            "regular_file_bytes": sum(size for size, _ in evidence_files.values()),
            "manifest_sha256": manifest_sha256(evidence_files),
            "filesystem_anomaly_absence_pass": not any("forbidden" in error for error in errors),
        },
        "claim_authority": "none",
        "execution_authority": False,
        "promotion_authority": False,
    }
    with args.verification.open("xb") as stream:
        stream.write(json_bytes(output))
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if output["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
