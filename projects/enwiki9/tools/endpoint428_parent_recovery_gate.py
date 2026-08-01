#!/usr/bin/env python3
"""Certify recovered endpoint428 artifacts and optionally replay exact 1M.

This is a source/substrate identity gate. It assigns no compression score
credit and deliberately does not modify or rebuild the recovered parent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile


PROJECT = Path(__file__).resolve().parents[1]
NONPROOF = Path("/home/x/enwiki9-nonproof")
ORIGINAL = NONPROOF / "results/endpoint428_pair_layer0_gate_dot_fuse_output_update_loop_lzma_source_package_v1"
MINIFIED = NONPROOF / "results/endpoint428_pair_layer0_gate_dot_fuse_output_update_loop_minified_lzma_source_package_v1"
NATIVE_10M = NONPROOF / "results/endpoint428_pair_layer0_gate_dot_fuse_output_update_loop_native_10m_v1"
RUNTIME = NONPROOF / "runtime/endpoint428_pair_layer0_dual_context_lstm_parallel_v2_native_fastmath_staticgomp_bptt_output_single_lookup_extra_fuse_gate_dot_fuse_output_update_loop_v1"
IDENTITY_1K = NONPROOF / "results/endpoint428_pair_layer0_output_update_loop_identity_1k_v1"

EXPECTED = {
    "original_package": (280_147, "19ddcc4ec1b6f31958bed4aa19c0fbc83a56c78121933e1447e4ee011547aee0"),
    "minified_package": (261_125, "b6fe6b09d6adbd8a287a08d284ca1f439ba72ff007b4d40c66bf7647a54a5d43"),
    "program": (2_326_416, "37ee8cd73ade9845b1afcb39f3bbd9358956c3ff9aea3b69328da7441ee32361"),
    "backend": (1_899_840, "d1066630f0d58894e69bd84519ec7d0f608b9e2fce67ab9ebedde65c58eca194"),
    "dictionary": (411_996, "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"),
    "input_1k": (1_000, "0f35cdeee80ba4c570885c34ee901aa579441fb8ba97351568a81bacdfc241fd"),
    "archive_1k": (259, "245b647b159599882620e473c5694e305aa0b2fd390a28a19cae72b04fdd72d4"),
    "input_10m": (10_000_000, "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97"),
    "archive_10m": (1_634_500, "93d7f5cb69ecad5457078ff9de34a63d8b0a8dcf21cc0fa9e20df895e13b1880"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path, expected: tuple[int, str], *, zip_integrity: bool = False) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    digest = sha256_file(path)
    expected_size, expected_digest = expected
    row: dict[str, object] = {
        "path": str(path),
        "bytes": size,
        "sha256": digest,
        "expected_bytes": expected_size,
        "expected_sha256": expected_digest,
        "identity_ok": size == expected_size and digest == expected_digest,
    }
    if zip_integrity:
        with ZipFile(path) as archive:
            bad_member = archive.testzip()
        row["zip_bad_member"] = bad_member
        row["zip_integrity_ok"] = bad_member is None
    if not row["identity_ok"] or (zip_integrity and not row["zip_integrity_ok"]):
        raise ValueError(f"artifact identity failed: {path}")
    return row


def observed_artifact(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def run_guarded(label: str, output_dir: Path, command: list[str]) -> dict[str, object]:
    guard_path = output_dir / f"{label}_guard.json"
    log_path = output_dir / f"{label}.log"
    guard_tool = PROJECT / "tools/run_with_rss_guard.py"
    invocation = [
        sys.executable,
        str(guard_tool),
        "--limit-kib",
        "10485760",
        "--limit-mode",
        "max_single",
        "--official-decimal-limit-kib",
        "9765625",
        "--sample-interval",
        "1",
        "--guard-json",
        str(guard_path),
        "--label",
        label,
        "--",
        *command,
    ]
    with log_path.open("wb") as log:
        completed = subprocess.run(invocation, stdout=log, stderr=subprocess.STDOUT, check=False)
    if not guard_path.is_file():
        raise RuntimeError(f"missing guard receipt for {label}; returncode={completed.returncode}")
    guard = json.loads(guard_path.read_text())
    ok = (
        completed.returncode == 0
        and guard.get("returncode") == 0
        and guard.get("status") == "complete"
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib") == 0
    )
    if not ok:
        raise RuntimeError(f"guarded replay failed for {label}: {guard}")
    return {
        "command": command,
        "guard": guard,
        "guard_path": str(guard_path),
        "log_path": str(log_path),
        "ok": True,
    }


def audit_artifacts() -> dict[str, object]:
    clean_a = ORIGINAL / "clean-build-a"
    clean_b = ORIGINAL / "clean-build-b"
    artifacts = {
        "original_package_a": artifact(ORIGINAL / "source_package_a.zip", EXPECTED["original_package"], zip_integrity=True),
        "original_package_b": artifact(ORIGINAL / "source_package_b.zip", EXPECTED["original_package"], zip_integrity=True),
        "minified_package_a": artifact(MINIFIED / "source_package_a.zip", EXPECTED["minified_package"], zip_integrity=True),
        "minified_package_b": artifact(MINIFIED / "source_package_b.zip", EXPECTED["minified_package"], zip_integrity=True),
        "program_a": artifact(clean_a / "comp9a-decomp9", EXPECTED["program"]),
        "program_b": artifact(clean_b / "comp9a-decomp9", EXPECTED["program"]),
        "backend_a": artifact(clean_a / "build/cmix.bin", EXPECTED["backend"]),
        "backend_b": artifact(clean_b / "build/cmix.bin", EXPECTED["backend"]),
        "runtime_backend": artifact(RUNTIME / "cmix.bin", EXPECTED["backend"]),
        "dictionary": artifact(RUNTIME / "english.dic", EXPECTED["dictionary"]),
        "input_1k": artifact(PROJECT / "data/enwik9_1000.bin", EXPECTED["input_1k"]),
        "archive_1k": artifact(IDENTITY_1K / "archive.bin", EXPECTED["archive_1k"]),
        "input_10m": artifact(PROJECT / "data/enwik9_10000000.bin", EXPECTED["input_10m"]),
        "archive_10m": artifact(NATIVE_10M / "archive.bin", EXPECTED["archive_10m"]),
        "archive_10m_reencode": artifact(NATIVE_10M / "archive_reencode.bin", EXPECTED["archive_10m"]),
        "restored_10m": artifact(NATIVE_10M / "restored.bin", EXPECTED["input_10m"]),
    }
    return {
        "artifacts": artifacts,
        "all_identity_ok": all(bool(row["identity_ok"]) for row in artifacts.values()),
        "all_zip_integrity_ok": all(
            bool(row.get("zip_integrity_ok", True)) for row in artifacts.values()
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-1m", action="store_true")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    audit = audit_artifacts()
    replay: dict[str, object] | None = None

    if args.run_1m:
        input_path = (PROJECT / "data/enwik9_1000000.bin").resolve()
        if input_path.stat().st_size != 1_000_000:
            raise ValueError(f"wrong 1M input size: {input_path}")
        archive_a = output_dir / "archive.bin"
        restored = output_dir / "restored.bin"
        archive_b = output_dir / "archive_reencode.bin"
        for path in (archive_a, restored, archive_b):
            if path.exists():
                raise FileExistsError(f"refusing to overwrite replay artifact: {path}")
        program_a = (ORIGINAL / "clean-build-a/comp9a-decomp9").resolve()
        program_b = (ORIGINAL / "clean-build-b/comp9a-decomp9").resolve()
        phases = {
            "encode": run_guarded("encode_1m", output_dir, [str(program_a), "c", str(input_path), str(archive_a)]),
            "decode": run_guarded("decode_1m", output_dir, [str(program_a), "d", str(archive_a), str(restored)]),
            "reencode": run_guarded("reencode_1m", output_dir, [str(program_b), "c", str(input_path), str(archive_b)]),
        }
        input_row = observed_artifact(input_path)
        archive_row = observed_artifact(archive_a)
        restored_row = observed_artifact(restored)
        reencode_row = observed_artifact(archive_b)
        roundtrip_ok = restored_row["bytes"] == input_row["bytes"] and restored_row["sha256"] == input_row["sha256"]
        determinism_ok = reencode_row["bytes"] == archive_row["bytes"] and reencode_row["sha256"] == archive_row["sha256"]
        replay = {
            "scope_bytes": 1_000_000,
            "input": input_row,
            "archive": archive_row,
            "restored": restored_row,
            "archive_reencode": reencode_row,
            "phases": phases,
            "roundtrip_ok": roundtrip_ok,
            "determinism_ok": determinism_ok,
            "decimal_memory_ok": all(
                phase["guard"]["official_decimal_over_limit_kib"] == 0
                for phase in phases.values()
            ),
        }
        if not roundtrip_ok or not determinism_ok or not replay["decimal_memory_ok"]:
            raise RuntimeError(f"1M replay identity failed: {replay}")

    complete = bool(audit["all_identity_ok"] and audit["all_zip_integrity_ok"] and replay is not None)
    decision = {
        "schema": "endpoint428_parent_recovery_gate_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "typed_event_sleeping_bayes_parent_recovery_q0_v1",
        "evidence_level": "source_artifact_materialization" if replay is None else "constructive_exact_parent_1m_replay",
        "audit": audit,
        "replay_1m": replay,
        "forecast": {
            "best_counted_forecast_bytes": 109_389_323,
            "design_target_bytes": 108_000_000,
            "remaining_debt_bytes": 1_389_323,
            "exact_full_1g_score": None,
            "score_credit_bytes": 0,
        },
        "proof": {
            "original_package_materialized": True,
            "minified_package_materialized": True,
            "program_identity": True,
            "backend_identity": True,
            "archived_1k_identity": True,
            "archived_10m_roundtrip_identity": True,
            "archived_10m_reencode_identity": True,
            "fresh_1m_roundtrip": bool(replay and replay["roundtrip_ok"]),
            "fresh_1m_determinism": bool(replay and replay["determinism_ok"]),
            "gate0_complete": complete,
        },
        "decision": {
            "verdict": "parent_artifacts_recovered_1m_replay_pending" if replay is None else "parent_artifacts_and_1m_replay_exact",
            "typed_event_gate2_authorized": complete,
            "full_1g_authorized": False,
            "next_action": "Run the exact fresh 1M replay." if replay is None else "Create a receipt-bound exact parent P1 trace before typed-event scoring.",
        },
        "claim_boundary": "This gate proves recovered parent artifact identity and, when requested, a fresh exact 1M wrapper replay. It assigns no candidate savings and does not establish an official full-1G score.",
    }
    decision_path = output_dir / "decision.json"
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(json.dumps({"decision_path": str(decision_path), "verdict": decision["decision"]["verdict"], "gate0_complete": complete}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
