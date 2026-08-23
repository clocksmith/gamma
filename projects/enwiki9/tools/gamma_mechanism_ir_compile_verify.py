#!/usr/bin/env python3
"""Run independent Mechanism IR compilations and frozen rejection controls."""

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


OUTPUT_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir-compilation-verification.v1"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def tree_files(
    root: Path,
    errors: list[str],
    label: str,
    anomaly_counts: dict[str, int] | None = None,
) -> dict[str, tuple[int, str]]:
    files: dict[str, tuple[int, str]] = {}

    def visit(directory: Path, relative: PurePosixPath) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            errors.append(f"{label}: cannot scan {directory}: {exc}")
            return
        for entry in entries:
            child_relative = relative / entry.name
            name = child_relative.as_posix()
            metadata = entry.stat(follow_symlinks=False)
            if stat.S_ISLNK(metadata.st_mode):
                if anomaly_counts is not None:
                    anomaly_counts["symlink_count"] += 1
                errors.append(f"{label}: symlink forbidden: {name}")
            elif stat.S_ISDIR(metadata.st_mode):
                visit(Path(entry.path), child_relative)
            elif stat.S_ISREG(metadata.st_mode):
                if metadata.st_nlink != 1:
                    if anomaly_counts is not None:
                        anomaly_counts["hardlink_count"] += 1
                    errors.append(f"{label}: hardlink forbidden: {name}")
                files[name] = (metadata.st_size, sha256_file(Path(entry.path)))
            else:
                if anomaly_counts is not None:
                    anomaly_counts["special_count"] += 1
                errors.append(f"{label}: special file forbidden: {name}")

    visit(root, PurePosixPath())
    return files


def resolve_existing_regular_without_symlinks(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise SystemExit(f"{label}: cannot lstat {current}: {exc}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise SystemExit(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode):
        raise SystemExit(f"{label}: expected regular file")
    if metadata.st_nlink != 1:
        raise SystemExit(f"{label}: hard-linked file forbidden")
    return absolute.resolve(strict=True)


def require_existing_parent_without_symlinks(path: Path, label: str) -> None:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parent.parts[1:]:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise SystemExit(f"{label}: cannot lstat parent {current}: {exc}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise SystemExit(f"{label}: symlink parent forbidden: {current}")
        if not stat.S_ISDIR(metadata.st_mode):
            raise SystemExit(f"{label}: parent component is not a directory: {current}")


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


def run_compiler(compiler: Path, ir: Path, run_root: Path) -> subprocess.CompletedProcess[bytes]:
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PYTHONHASHSEED": "0",
        "TZ": "UTC",
    }
    completed = subprocess.run(
        [
            sys.executable,
            os.fspath(compiler),
            "--ir",
            os.fspath(ir),
            "--output-dir",
            os.fspath(run_root / "artifacts"),
            "--receipt",
            os.fspath(run_root / "receipt.json"),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "stdout.bin").write_bytes(completed.stdout)
    (run_root / "stderr.bin").write_bytes(completed.stderr)
    return completed


def mutate_invalid_id(ir: dict[str, Any]) -> None:
    ir["mechanism_id"] = "../invalid"


def mutate_equation_hash(ir: dict[str, Any]) -> None:
    ir["update"]["equation_sha256"] = "0" * 64


def mutate_state_hash(ir: dict[str, Any]) -> None:
    ir["state_writes"][0]["audit_hash"] = "undeclared_hash"


def mutate_persistent_policy(ir: dict[str, Any]) -> None:
    ir["lifecycle"]["persistent_write_policy"] = "none"


def mutate_K(ir: dict[str, Any]) -> None:
    ir["controls"]["K"] = ""


def mutate_outputs(ir: dict[str, Any]) -> None:
    ir["generated_outputs"] = ir["generated_outputs"][:-1]


def mutate_memory(ir: dict[str, Any]) -> None:
    ir["ceilings"]["process_tree_memory_bytes"] = 10000000001


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--ir", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()

    compiler = resolve_existing_regular_without_symlinks(args.compiler, "compiler")
    ir_path = resolve_existing_regular_without_symlinks(args.ir, "IR")
    require_existing_parent_without_symlinks(args.evidence_root, "evidence root")
    require_existing_parent_without_symlinks(args.verification, "verification")
    if args.evidence_root.exists():
        raise SystemExit("evidence root must not already exist")
    if args.verification.exists() or args.verification.is_symlink():
        raise SystemExit("verification path already exists")
    args.evidence_root.mkdir(parents=True)

    errors: list[str] = []
    raw_ir = ir_path.read_bytes()
    try:
        ir = json.loads(raw_ir.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"IR parse failure: {exc}")
    if not isinstance(ir, dict):
        raise SystemExit("IR must be a JSON object")
    mechanism_id = str(ir.get("mechanism_id", "invalid"))

    run_a = run_compiler(compiler, ir_path, args.evidence_root / "repeat-a")
    run_b = run_compiler(compiler, ir_path, args.evidence_root / "repeat-b")
    if run_a.returncode != 0:
        errors.append(f"repeat-a compiler return code {run_a.returncode}")
    if run_b.returncode != 0:
        errors.append(f"repeat-b compiler return code {run_b.returncode}")
    receipt_a = args.evidence_root / "repeat-a" / "receipt.json"
    receipt_b = args.evidence_root / "repeat-b" / "receipt.json"
    receipt_identity = receipt_a.is_file() and receipt_b.is_file() and receipt_a.read_bytes() == receipt_b.read_bytes()
    if not receipt_identity:
        errors.append("independent compilation receipts differ")
    artifacts_a_root = args.evidence_root / "repeat-a" / "artifacts"
    artifacts_b_root = args.evidence_root / "repeat-b" / "artifacts"
    artifacts_a = tree_files(artifacts_a_root, errors, "repeat-a artifacts") if artifacts_a_root.is_dir() else {}
    artifacts_b = tree_files(artifacts_b_root, errors, "repeat-b artifacts") if artifacts_b_root.is_dir() else {}
    artifact_identity = bool(artifacts_a) and artifacts_a == artifacts_b
    if not artifact_identity:
        errors.append("independent compilation artifact trees differ")
    artifact_set_hash = manifest_sha256(artifacts_a)
    for label, receipt_path in (("repeat-a", receipt_a), ("repeat-b", receipt_b)):
        if not receipt_path.is_file():
            continue
        try:
            receipt_document = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{label} receipt parse failure: {exc}")
            continue
        if not isinstance(receipt_document, dict):
            errors.append(f"{label} receipt is not a JSON object")
            continue
        if receipt_document.get("artifact_set_sha256") != artifact_set_hash:
            errors.append(f"{label} receipt artifact_set_sha256 does not match the recomputed artifact tree")
        declared_artifacts = receipt_document.get("artifacts")
        if not isinstance(declared_artifacts, list):
            errors.append(f"{label} receipt artifacts are not an array")
            continue
        declared_tree: dict[str, tuple[int, str]] = {}
        for artifact in declared_artifacts:
            if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
                errors.append(f"{label} receipt contains an invalid artifact entry")
                continue
            path = artifact["path"]
            if path in declared_tree:
                errors.append(f"{label} receipt contains duplicate artifact path {path}")
                continue
            declared_tree[path] = (artifact.get("bytes"), artifact.get("sha256"))
        if declared_tree != artifacts_a:
            errors.append(f"{label} receipt artifact entries do not equal the recomputed artifact tree")

    mutations: dict[str, Callable[[dict[str, Any]], None]] = {
        "invalid_mechanism_id": mutate_invalid_id,
        "equation_hash_mismatch": mutate_equation_hash,
        "missing_state_hash": mutate_state_hash,
        "undeclared_persistent_write": mutate_persistent_policy,
        "missing_K_control": mutate_K,
        "incomplete_output_set": mutate_outputs,
        "memory_ceiling_exceeded": mutate_memory,
    }
    controls: dict[str, dict[str, Any]] = {}
    for name, mutate in mutations.items():
        control_ir = copy.deepcopy(ir)
        mutate(control_ir)
        control_root = args.evidence_root / "negative-controls" / name
        control_root.mkdir(parents=True)
        control_ir_path = control_root / "input.json"
        control_ir_path.write_bytes(json_bytes(control_ir))
        completed = run_compiler(compiler, control_ir_path, control_root / "run")
        artifacts_root = control_root / "run" / "artifacts"
        receipt_path = control_root / "run" / "receipt.json"
        no_artifacts = (not artifacts_root.exists() or (artifacts_root.is_dir() and not any(artifacts_root.iterdir()))) and not receipt_path.exists()
        rejected = completed.returncode != 0 and no_artifacts
        if not rejected:
            errors.append(f"negative control {name} was not rejected without artifacts")
        controls[name] = {
            "return_code": completed.returncode,
            "rejected": rejected,
            "stdout_sha256": sha256_bytes(completed.stdout),
            "stderr_sha256": sha256_bytes(completed.stderr),
            "no_artifacts_pass": no_artifacts,
        }

    anomaly_counts = {"symlink_count": 0, "hardlink_count": 0, "special_count": 0}
    evidence_files = tree_files(args.evidence_root, errors, "evidence root", anomaly_counts)
    output = {
        "schema": OUTPUT_SCHEMA,
        "mechanism_id": mechanism_id,
        "verified": not errors,
        "errors": errors,
        "compiler_sha256": sha256_file(compiler),
        "source_ir_sha256": sha256_bytes(raw_ir),
        "repeat": {
            "run_a_return_code": run_a.returncode,
            "run_b_return_code": run_b.returncode,
            "receipt_identity_pass": receipt_identity,
            "artifact_identity_pass": artifact_identity,
            "artifact_set_sha256": artifact_set_hash,
        },
        "negative_controls": controls,
        "evidence_root": {
            "regular_file_count": len(evidence_files),
            "regular_file_bytes": sum(size for size, _ in evidence_files.values()),
            "manifest_sha256": manifest_sha256(evidence_files),
            "symlink_count": anomaly_counts["symlink_count"],
            "hardlink_count": anomaly_counts["hardlink_count"],
            "special_count": anomaly_counts["special_count"],
            "filesystem_anomaly_absence_pass": all(count == 0 for count in anomaly_counts.values()),
        },
    }
    args.verification.parent.mkdir(parents=True, exist_ok=True)
    args.verification.write_bytes(json_bytes(output))
    return 0 if output["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
