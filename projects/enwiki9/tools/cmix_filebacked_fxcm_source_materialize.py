#!/usr/bin/env python3
"""Materialize the exact q0+q1 patched CMIX source tree and closure list."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
from typing import Any


CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-source-materialization.v1"
TRACKED_TREE = "23de249ff899db5ba84dd3514a6a1bb52a83d0f5"
EXPECTED_SOURCE_ARCHIVE = "656a3100b7c4580658080fb0eda221a28b2f982f798f0b7ddc13409f2ce9c249"
EXPECTED_PROFILE = "5141320933c09c4fd24d7f332da67b1008a3e730dd09c8784ea36769f2fe1e52"
EXPECTED_Q0_PATCH = "aaa443b18e8cd4d190c04b55b680d7e102f2b96eacab3e11d888cca27e7a2001"
EXPECTED_Q0_APPLICATOR = "abcf3631e99516c4f676a5002c4d3111e4748af8c563d863139160ee28619a86"
EXPECTED_Q1_PATCH = "a88a06c02d05e73093aa9cf57c104a8732ec9a355c571b205363240601f03744"
EXPECTED_Q1_APPLICATOR = "78a8ea5b688d05c01eea19c679bebb3ae385d49364c64b7148148cecf912ca85"
SHARED_HEADER = "src/models/gamma-filebacked-fxcm.h"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regular(path: Path, label: str) -> Path:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has symlink component: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} must be a single-link regular file")
    return absolute.resolve(strict=True)


def directory(path: Path, label: str) -> Path:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"{label} has invalid component: {current}")
    return absolute.resolve(strict=True)


def write_new(path: Path, payload: bytes, mode: int = 0o600) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    parent = directory(path.parent, "output parent")
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        mode,
    )
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def safe_member(member: tarfile.TarInfo) -> Path:
    path = Path(member.name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError(f"unsafe source archive member: {member.name}")
    if not (member.isdir() or member.isfile()):
        raise RuntimeError(f"unsupported source archive member: {member.name}")
    return path


def extract_source(archive_path: Path, source_root: Path) -> None:
    with tarfile.open(archive_path, mode="r:") as archive:
        for member in archive:
            relative = safe_member(member)
            target = source_root / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                target.chmod(member.mode & 0o777)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = archive.extractfile(member)
            if stream is None:
                raise RuntimeError(f"missing source archive payload: {member.name}")
            descriptor = os.open(
                target,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                member.mode & 0o777,
            )
            try:
                while block := stream.read(1024 * 1024):
                    offset = 0
                    while offset < len(block):
                        written = os.write(descriptor, block[offset:])
                        if written <= 0:
                            raise OSError(f"short source extraction write: {target}")
                        offset += written
            finally:
                os.close(descriptor)


def run_patch(step_id: str, applicator: Path, source_root: Path) -> dict[str, Any]:
    argv = ["/bin/sh", str(applicator), str(source_root)]
    completed = subprocess.run(
        argv,
        cwd=source_root,
        env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "TZ": "UTC"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = {
        "id": step_id,
        "argv": argv,
        "return_code": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }
    if completed.returncode != 0:
        raise RuntimeError(
            f"{step_id} failed: {completed.stderr.decode('utf-8', 'replace')[-2000:]}"
        )
    return result


def classify(path: str) -> str:
    if path == SHARED_HEADER:
        return "shared_allocator_header"
    if Path(path).suffix in {".c", ".cc", ".cpp", ".h", ".hh", ".hpp"}:
        return "source"
    return "build_input"


def source_files(source_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(source_root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"materialized source contains a symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(source_root).as_posix()
        records.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "role": classify(relative),
            }
        )
    if sum(record["role"] == "shared_allocator_header" for record in records) != 1:
        raise RuntimeError("materialized source lacks one shared allocator header")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", type=Path, required=True)
    parser.add_argument("--pgo-profile", type=Path, required=True)
    parser.add_argument("--q0-patch", type=Path, required=True)
    parser.add_argument("--q0-applicator", type=Path, required=True)
    parser.add_argument("--q1-patch", type=Path, required=True)
    parser.add_argument("--q1-applicator", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--entry-list", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    inputs = {
        "source_archive": regular(args.source_archive, "source archive"),
        "pgo_profile": regular(args.pgo_profile, "PGO profile"),
        "q0_patch": regular(args.q0_patch, "q0 patch"),
        "q0_applicator": regular(args.q0_applicator, "q0 applicator"),
        "q1_patch": regular(args.q1_patch, "q1 patch"),
        "q1_applicator": regular(args.q1_applicator, "q1 applicator"),
    }
    if sha256_file(inputs["source_archive"]) != EXPECTED_SOURCE_ARCHIVE:
        raise RuntimeError("source archive identity mismatch")
    if sha256_file(inputs["pgo_profile"]) != EXPECTED_PROFILE:
        raise RuntimeError("PGO profile identity mismatch")
    if sha256_file(inputs["q0_patch"]) != EXPECTED_Q0_PATCH:
        raise RuntimeError("q0 patch identity mismatch")
    if sha256_file(inputs["q0_applicator"]) != EXPECTED_Q0_APPLICATOR:
        raise RuntimeError("q0 applicator identity mismatch")
    if sha256_file(inputs["q1_patch"]) != EXPECTED_Q1_PATCH:
        raise RuntimeError("q1 patch identity mismatch")
    if sha256_file(inputs["q1_applicator"]) != EXPECTED_Q1_APPLICATOR:
        raise RuntimeError("q1 applicator identity mismatch")
    if args.output_root.exists() or args.output_root.is_symlink():
        raise FileExistsError(args.output_root)
    output_parent = directory(args.output_root.parent, "source output parent")
    source_root = output_parent / args.output_root.name
    source_root.mkdir(mode=0o700)
    extract_source(inputs["source_archive"], source_root)

    profile_asbuilt = source_root / "pgo_data_asbuilt/default.profdata"
    shutil.copyfile(inputs["pgo_profile"], profile_asbuilt)
    profile_build = source_root / "pgo_data/default.profdata"
    profile_build.parent.mkdir(exist_ok=True)
    shutil.copyfile(inputs["pgo_profile"], profile_build)
    patch_steps = [
        run_patch("q0_memory_correction", inputs["q0_applicator"], source_root),
        run_patch("q1_filebacked_fxcm", inputs["q1_applicator"], source_root),
    ]
    files = source_files(source_root)
    entry_payload = "".join(
        f"{record['role']}\t{record['path']}\n" for record in files
    ).encode("ascii")
    write_new(args.entry_list, entry_payload)
    metadata = source_root.stat()
    root_identity = {
        "path": str(source_root.resolve(strict=True)),
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
    }
    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "tracked_tree": TRACKED_TREE,
        "inputs": {name: artifact(path) for name, path in inputs.items()},
        "patch_steps": patch_steps,
        "source_root": str(source_root.resolve(strict=True)),
        "source_root_identity_sha256": hashlib.sha256(canonical(root_identity)).hexdigest(),
        "files": files,
        "entry_list": artifact(args.entry_list),
        "materialized": True,
        "authority": "source_identity_only",
    }
    write_new(
        args.receipt,
        (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode("ascii"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
