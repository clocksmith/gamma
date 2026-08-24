#!/usr/bin/env python3
"""Run one prize-facing q1 encode or corpus-independent decode stage."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
from typing import Any


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-stage.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
CANONICAL_BYTES = 1_000_000_000
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def regular(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has symlink component: {current}")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} must be a single-link regular file")
    return path.resolve(strict=True)


def directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"{label} has invalid component: {current}")
    return path.resolve(strict=True)


def marker(path: Path, phase: str, event: str, detail: str | None = None) -> None:
    value: dict[str, str] = {"phase": phase, "event": event}
    if detail is not None:
        value["detail"] = detail
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        cursor = 0
        while cursor < len(raw):
            written = os.write(descriptor, raw[cursor:])
            if written <= 0:
                raise OSError("short phase-marker write")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_new(path: Path, value: dict[str, Any]) -> None:
    raw = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        cursor = 0
        while cursor < len(raw):
            written = os.write(descriptor, raw[cursor:])
            if written <= 0:
                raise OSError("short stage-receipt write")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def run_codec(
    argv: list[str], cwd: Path, environment: dict[str, str], stdout: Path, stderr: Path
) -> int:
    with stdout.open("xb") as out, stderr.open("xb") as err:
        return subprocess.run(
            argv,
            cwd=cwd,
            env=environment,
            stdout=out,
            stderr=err,
            check=False,
        ).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("encode", "decode"), required=True)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--head", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    work_root = directory(args.work_root, "stage work root")
    result_root = directory(args.result_root, "stage result root")
    receipt = args.receipt
    if receipt.parent.resolve(strict=True) != result_root or receipt.exists() or receipt.is_symlink():
        raise RuntimeError("stage receipt must be a new direct child of result root")
    marker_path = regular(
        Path(os.environ.get("GAMMA_RESOURCE_PHASE_MARKERS", "")), "phase marker"
    )
    backing = work_root / "fxcm-backing"
    if backing.exists() or backing.is_symlink():
        raise RuntimeError("stage backing root must be absent")
    backing.mkdir(mode=0o700)
    environment = {
        "GAMMA_FXCM_BACKING_DIR": str(backing),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
    }
    phase = f"{args.mode}_stage"
    marker(marker_path, phase, "start")

    outputs: dict[str, dict[str, Any]] = {}
    exact_inverse: bool | None = None
    errors: list[str] = []
    if args.mode == "encode":
        if args.corpus is None or args.package is None or args.head is None or args.archive is not None:
            raise RuntimeError("encode requires corpus/package/head and forbids archive")
        corpus = regular(args.corpus, "canonical corpus")
        corpus_record = artifact(corpus)
        if corpus_record["bytes"] != CANONICAL_BYTES or corpus_record["sha256"] != CANONICAL_SHA256:
            raise RuntimeError("canonical corpus identity mismatch")
        package = regular(args.package, "packaged CMIX binary")
        head = regular(args.head, "head blob")
        inputs = {
            "corpus": corpus_record,
            "package": artifact(package),
            "head": artifact(head),
        }
        local_cmix = work_root / "cmix"
        local_head = work_root / "head.blob"
        shutil.copyfile(package, local_cmix)
        shutil.copyfile(head, local_head)
        local_cmix.chmod(0o755)
        environment["KH_BITLSTM32"] = str(local_head)
        command = ["./cmix", "-e", str(corpus), "out.cmix"]
        return_code = run_codec(
            command,
            work_root,
            environment,
            result_root / "encode.codec.stdout",
            result_root / "encode.codec.stderr",
        )
        marker(marker_path, phase, "end", f"returncode={return_code}")
        if return_code != 0:
            errors.append(f"codec_return_code={return_code}")
        else:
            payload = regular(work_root / "out.cmix", "encoded payload")
            archive = regular(work_root / "archive9", "self-extracting archive")
            retained_payload = result_root / "out.cmix"
            retained_archive = result_root / "archive9"
            os.replace(payload, retained_payload)
            os.replace(archive, retained_archive)
            outputs = {
                "payload": artifact(retained_payload),
                "archive": artifact(retained_archive),
            }
    else:
        if args.corpus is not None or args.archive is None or args.package is not None or args.head is not None:
            raise RuntimeError("decode requires only archive and forbids corpus/package/head")
        source_archive = regular(args.archive, "retained archive")
        inputs = {"archive": artifact(source_archive)}
        local_archive = work_root / "archive9"
        shutil.copyfile(source_archive, local_archive)
        local_archive.chmod(0o755)
        command = ["./archive9"]
        return_code = run_codec(
            command,
            work_root,
            environment,
            result_root / "decode.codec.stdout",
            result_root / "decode.codec.stderr",
        )
        marker(marker_path, phase, "end", f"returncode={return_code}")
        if return_code != 0:
            errors.append(f"codec_return_code={return_code}")
        else:
            restored_options = [
                path
                for path in (work_root / "enwik9", work_root / "enwik9_uncompressed")
                if path.is_file() and not path.is_symlink()
            ]
            if len(restored_options) != 1:
                raise RuntimeError("full decode did not emit exactly one known restored path")
            restored = regular(restored_options[0], "restored corpus")
            retained_restored = result_root / "enwik9-restored"
            os.replace(restored, retained_restored)
            restored_artifact = artifact(retained_restored)
            exact_inverse = (
                restored_artifact["bytes"] == CANONICAL_BYTES
                and restored_artifact["sha256"] == CANONICAL_SHA256
            )
            if not exact_inverse:
                errors.append("canonical_inverse_mismatch")
            outputs = {"restored": restored_artifact}

    backing_cleanup = not any(backing.iterdir())
    if backing_cleanup:
        backing.rmdir()
    else:
        errors.append("file_backed_fxcm_state_survived_codec_exit")
    stage_pass = not errors and return_code == 0 and backing_cleanup
    stage_receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "mode": args.mode,
        "population": {"bytes": CANONICAL_BYTES, "sha256": CANONICAL_SHA256},
        "inputs": inputs,
        "command": command,
        "return_code": return_code,
        "outputs": outputs,
        "exact_raw_inverse_pass": exact_inverse,
        "backing_cleanup_pass": backing_cleanup,
        "errors": errors,
        "phase_marker": artifact(marker_path),
        "stage_runner": artifact(Path(__file__).resolve(strict=True)),
        "work_root": str(work_root),
        "result_root": str(result_root),
        "stage_pass": stage_pass,
        "claim_authority": "single_guarded_prize_runtime_stage_only",
        "execution_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    write_new(receipt, stage_receipt)
    return 0 if stage_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
