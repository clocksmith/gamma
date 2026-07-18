#!/usr/bin/env python3
"""Run a guarded source-built wrapper identity, roundtrip, and replay proof."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_SCOPE_BYTES = 10_000_000
EXPECTED_ORIGINAL_SHA256 = (
    "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    path = path.resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def identical(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as lhs, right.open("rb") as rhs:
        while True:
            left_block = lhs.read(1 << 20)
            right_block = rhs.read(1 << 20)
            if left_block != right_block:
                return False
            if not left_block:
                return True


def framed_payload_identical(framed: Path, payload: Path) -> tuple[bytes, bool]:
    if framed.stat().st_size != payload.stat().st_size + 1:
        return b"", False
    with framed.open("rb") as lhs, payload.open("rb") as rhs:
        marker = lhs.read(1)
        while True:
            left_block = lhs.read(1 << 20)
            right_block = rhs.read(1 << 20)
            if left_block != right_block:
                return marker, False
            if not left_block:
                return marker, True


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return value


def require_artifact(entry: dict[str, Any]) -> Path:
    path = Path(entry["path"])
    observed = artifact(path)
    for key in ("bytes", "sha256"):
        if observed[key] != entry[key]:
            raise RuntimeError(
                f"artifact {key} mismatch for {observed['path']}: "
                f"{observed[key]} != {entry[key]}"
            )
    return path


def run_guarded(
    *,
    guard_tool: Path,
    label: str,
    command: list[str],
    guard_path: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> tuple[subprocess.CompletedProcess[bytes], dict[str, Any]]:
    guard_command = [
        sys.executable,
        str(guard_tool.resolve()),
        "--limit-kib",
        "10485760",
        "--official-decimal-limit-kib",
        "9765625",
        "--sample-interval",
        "1",
        "--guard-json",
        str(guard_path.resolve()),
        "--label",
        label,
        "--",
        *command,
    ]
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            guard_command,
            cwd="/home/x/deco/gamma",
            env=os.environ.copy(),
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    if not guard_path.is_file():
        raise RuntimeError(f"guard did not emit a receipt: {guard_path}")
    return completed, load_object(guard_path)


def clean_guard(
    completed: subprocess.CompletedProcess[bytes], guard: dict[str, Any]
) -> bool:
    return (
        completed.returncode == 0
        and guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib") == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    root = Path(
        "/home/x/enwiki9-nonproof/"
        "fx2-cmix21-hybrid-geometry-title-nopaq-lstm112x2-plus80x2-"
        "native-source-package-build-v1"
    )
    parser.add_argument(
        "--sealed-screen",
        type=Path,
        default=Path(
            "projects/enwiki9/results/"
            "fx2_cmix21_lstm112_plus80_native_10m_v1/receipt.json"
        ),
    )
    parser.add_argument(
        "--program", type=Path, default=root / "source-build-a/comp9a-decomp9"
    )
    parser.add_argument("--source-archive", type=Path)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/page_order_rotation_inputs_10m/"
            "10000000_original.raw"
        ),
    )
    parser.add_argument(
        "--result-root",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "fx2_cmix21_lstm112_plus80_wrapper_proof_10m_v1"
        ),
    )
    parser.add_argument(
        "--guard-tool",
        type=Path,
        default=Path("projects/enwiki9/tools/run_with_rss_guard.py"),
    )
    parser.add_argument("--lock", type=Path, default=Path("/tmp/enwiki9-heavy.lock"))
    args = parser.parse_args()

    for path in (
        args.sealed_screen,
        args.program,
        args.input,
        args.guard_tool,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    if args.input.stat().st_size != EXPECTED_SCOPE_BYTES:
        raise RuntimeError("wrapper proof input is not exact cumulative 10M")
    if sha256(args.input) != EXPECTED_ORIGINAL_SHA256:
        raise RuntimeError("wrapper proof input identity changed")

    sealed = load_object(args.sealed_screen)
    decision = sealed.get("result")
    if not isinstance(decision, dict):
        decision = sealed.get("decision", {})
    if decision.get("wrapper_proof_authorized") is not True:
        raise RuntimeError("sealed screen does not authorize wrapper proof")
    reference_archive = require_artifact(sealed["artifacts"]["candidate_archive"])
    source_key = decision.get("selected_source_artifact_key")
    if not isinstance(source_key, str) or source_key not in sealed["artifacts"]:
        raise RuntimeError("sealed screen does not select a source archive")
    sealed_source_archive = sealed["artifacts"][source_key]
    source_archive = (
        args.source_archive
        if args.source_archive is not None
        else Path(sealed_source_archive["path"])
    )
    if not source_archive.is_file():
        raise FileNotFoundError(source_archive)
    if artifact(source_archive)["sha256"] != sealed_source_archive["sha256"]:
        raise RuntimeError("source archive differs from the sealed screen")

    result_dir = args.result_root
    if result_dir.exists():
        raise FileExistsError(f"refusing to overwrite wrapper proof: {result_dir}")
    result_dir.mkdir(parents=True)
    archive_a = result_dir / "archive_a.comp"
    restored = result_dir / "restored.raw"
    archive_b = result_dir / "archive_b.comp"

    stages: dict[str, Any] = {}
    marker = b""
    payload_identity = False
    roundtrip_ok = False
    determinism_ok = False
    with args.lock.open("a+") as lock_stream:
        fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
        encode_a_command = [
            str(args.program.resolve()),
            "c",
            str(args.input.resolve()),
            str(archive_a.resolve()),
        ]
        completed, guard = run_guarded(
            guard_tool=args.guard_tool,
            label="lstm112_plus80_wrapper_encode_a_10m",
            command=encode_a_command,
            guard_path=result_dir / "encode_a_guard.json",
            stdout_path=result_dir / "encode_a_stdout.log",
            stderr_path=result_dir / "encode_a_stderr.log",
        )
        encode_a_clean = clean_guard(completed, guard) and archive_a.is_file()
        stages["encode_a"] = {
            "command": encode_a_command,
            "process_returncode": completed.returncode,
            "clean_guard": encode_a_clean,
            "guard": artifact(result_dir / "encode_a_guard.json"),
            "guard_result": guard,
        }
        if encode_a_clean:
            marker, payload_identity = framed_payload_identical(
                archive_a, reference_archive
            )

        if encode_a_clean and marker == b"G" and payload_identity:
            decode_command = [
                str(args.program.resolve()),
                "d",
                str(archive_a.resolve()),
                str(restored.resolve()),
            ]
            completed, guard = run_guarded(
                guard_tool=args.guard_tool,
                label="lstm112_plus80_wrapper_decode_10m",
                command=decode_command,
                guard_path=result_dir / "decode_guard.json",
                stdout_path=result_dir / "decode_stdout.log",
                stderr_path=result_dir / "decode_stderr.log",
            )
            decode_clean = clean_guard(completed, guard) and restored.is_file()
            roundtrip_ok = decode_clean and identical(restored, args.input)
            stages["decode"] = {
                "command": decode_command,
                "process_returncode": completed.returncode,
                "clean_guard": decode_clean,
                "guard": artifact(result_dir / "decode_guard.json"),
                "guard_result": guard,
            }

        if roundtrip_ok:
            encode_b_command = [
                str(args.program.resolve()),
                "c",
                str(args.input.resolve()),
                str(archive_b.resolve()),
            ]
            completed, guard = run_guarded(
                guard_tool=args.guard_tool,
                label="lstm112_plus80_wrapper_encode_b_10m",
                command=encode_b_command,
                guard_path=result_dir / "encode_b_guard.json",
                stdout_path=result_dir / "encode_b_stdout.log",
                stderr_path=result_dir / "encode_b_stderr.log",
            )
            encode_b_clean = clean_guard(completed, guard) and archive_b.is_file()
            determinism_ok = encode_b_clean and identical(archive_a, archive_b)
            stages["encode_b"] = {
                "command": encode_b_command,
                "process_returncode": completed.returncode,
                "clean_guard": encode_b_clean,
                "guard": artifact(result_dir / "encode_b_guard.json"),
                "guard_result": guard,
            }
        fcntl.flock(lock_stream.fileno(), fcntl.LOCK_UN)

    proof_complete = (
        stages["encode_a"]["clean_guard"]
        and marker == b"G"
        and payload_identity
        and roundtrip_ok
        and determinism_ok
    )
    receipt = {
        "schema": "fx2_cmix21_source_wrapper_proof_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope_raw_bytes": EXPECTED_SCOPE_BYTES,
        "evidence_level": "exact_guarded_10m_source_wrapper_replay",
        "artifacts": {
            "sealed_screen": artifact(args.sealed_screen),
            "program": artifact(args.program),
            "source_archive": artifact(source_archive),
            "selected_source_artifact_key": source_key,
            "input": artifact(args.input),
            "reference_backend_archive": artifact(reference_archive),
            "archive_a": artifact(archive_a) if archive_a.is_file() else None,
            "restored": artifact(restored) if restored.is_file() else None,
            "archive_b": artifact(archive_b) if archive_b.is_file() else None,
        },
        "stages": stages,
        "result": {
            "marker": marker.decode("ascii", errors="replace"),
            "archive_payload_identity": payload_identity,
            "roundtrip_ok": roundtrip_ok,
            "determinism_ok": determinism_ok,
            "proof_complete": proof_complete,
            "promotion_authorized": False,
            "larger_gate_authorized": False,
        },
        "next_action": (
            "seal the candidate decision and disjoint-scope calibration"
            if proof_complete
            else "retire or fix the exact failed wrapper proof boundary"
        ),
        "claim_boundary": (
            "Exact source-built 10M wrapper identity, roundtrip, deterministic "
            "replay, and resource evidence only. This is not a full-corpus score "
            "or 10.95 percent claim."
        ),
    }
    receipt_path = result_dir / "receipt.json"
    temporary = receipt_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, receipt_path)
    print(receipt_path.resolve())
    print(json.dumps(receipt["result"], sort_keys=True))
    return 0 if proof_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
