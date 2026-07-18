#!/usr/bin/env python3
"""Seal the exact-10M v7 FX2-lite PPMD statistics-pointer crash."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__:
    from .seal_cmix21_lstm200_fx2lite428_10m_codec_failure import (
        EXPECTED_INPUT_SHA256,
        EXPECTED_SCOPE_BYTES,
        last_progress_percent,
        require_nonmemory_codec_failure,
    )
    from .seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        load_object,
        require_guard_invocation,
    )
else:
    from seal_cmix21_lstm200_fx2lite428_10m_codec_failure import (
        EXPECTED_INPUT_SHA256,
        EXPECTED_SCOPE_BYTES,
        last_progress_percent,
        require_nonmemory_codec_failure,
    )
    from seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        load_object,
        require_guard_invocation,
    )


EXPECTED_FAILURE_FUNCTION = "Fx2LitePPMD::ppmd_Model::processSymbol2_T"


def peak_process_pid(guard: dict[str, Any]) -> int:
    processes = guard.get("peak_sample", {}).get("processes", [])
    if not processes:
        raise RuntimeError("guard has no peak process sample")
    process = max(processes, key=lambda row: int(row.get("rss_kib", -1)))
    return int(process["pid"])


def parse_kernel_fault(text: str, pid: int) -> tuple[str, int]:
    pattern = re.compile(
        rf"^.*cmix\[{pid}\]: segfault .* in cmix\[([0-9a-fA-F]+),[^\]]+\].*$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"expected one kernel cmix fault for PID {pid}, got {len(matches)}")
    match = matches[0]
    return match.group(0), int(match.group(1), 16)


def load_file_offset(binary: Path, virtual_address: int) -> int:
    result = subprocess.run(
        ["readelf", "-lW", str(binary)],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) < 6 or fields[0] != "LOAD":
            continue
        offset = int(fields[1], 16)
        address = int(fields[2], 16)
        file_size = int(fields[4], 16)
        if address <= virtual_address < address + file_size:
            return offset + virtual_address - address
    raise RuntimeError(f"fault address 0x{virtual_address:x} is outside file-backed LOAD segments")


def read_window(binary: Path, file_offset: int, radius: int = 64) -> bytes:
    start = max(0, file_offset - radius)
    with binary.open("rb") as handle:
        handle.seek(start)
        return handle.read(2 * radius)


def addr2line(binary: Path, virtual_address: int) -> str:
    result = subprocess.run(
        ["addr2line", "-Cfipe", str(binary), f"0x{virtual_address:x}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def require_store_payload(store: Path, payload: Path) -> None:
    with store.open("rb") as store_handle, payload.open("rb") as payload_handle:
        if store_handle.read(5) != b"\x80\x00\x00\x00\x00":
            raise RuntimeError("canonical stored-WRT header differs")
        while True:
            left = store_handle.read(1 << 20)
            right = payload_handle.read(1 << 20)
            if left != right:
                raise RuntimeError("preserved WRT payload differs from canonical store")
            if not left:
                return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recovery-receipt", type=Path, required=True)
    parser.add_argument("--wrapper", type=Path, required=True)
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--symbol-backend", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--archive-path", type=Path, required=True)
    parser.add_argument("--guard", type=Path, required=True)
    parser.add_argument("--stderr-log", type=Path, required=True)
    parser.add_argument("--preserved-wrt-stream", type=Path, required=True)
    parser.add_argument("--canonical-store", type=Path, required=True)
    parser.add_argument("--kernel-fault-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    recovery = load_object(args.recovery_receipt)
    if recovery.get("schema") != "cmix21_lstm200_fx2lite428_ram_recovery_v1":
        raise RuntimeError("unexpected combined-recovery receipt schema")

    wrapper = artifact(args.wrapper)
    if any(
        wrapper[key] != recovery["artifacts"]["wrapper"][key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("failed wrapper differs from sealed v7 recovery")

    source_receipt_path = Path(recovery["artifacts"]["source_package_receipt"]["path"])
    source_receipt = load_object(source_receipt_path)
    backend = artifact(args.backend)
    if any(
        backend[key] != source_receipt["artifacts"]["clean_backend_a"][key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("backend differs from deterministic v7 clean build")

    input_artifact = artifact(args.input)
    if not (
        input_artifact["bytes"] == EXPECTED_SCOPE_BYTES
        and input_artifact["sha256"] == EXPECTED_INPUT_SHA256
    ):
        raise RuntimeError("failure did not use canonical original-order exact 10M")

    guard = load_object(args.guard)
    require_nonmemory_codec_failure(guard)
    require_guard_invocation(
        guard,
        wrapper=args.wrapper,
        mode="c",
        source=args.input,
        target=args.archive_path,
    )
    if args.archive_path.exists():
        raise RuntimeError("failed encode unexpectedly left a completed archive")

    progress = last_progress_percent(args.stderr_log.read_text(errors="replace"))
    require_store_payload(args.canonical_store, args.preserved_wrt_stream)

    pid = peak_process_pid(guard)
    kernel_line, crash_address = parse_kernel_fault(
        args.kernel_fault_log.read_text(errors="replace"), pid
    )
    release_offset = load_file_offset(args.backend, crash_address)
    symbol_offset = load_file_offset(args.symbol_backend, crash_address)
    if read_window(args.backend, release_offset) != read_window(
        args.symbol_backend, symbol_offset
    ):
        raise RuntimeError("symbol backend machine-code window differs at crash address")
    source_mapping = addr2line(args.symbol_backend, crash_address)
    if EXPECTED_FAILURE_FUNCTION not in source_mapping:
        raise RuntimeError("crash does not map to the expected FX2-lite PPMD function")

    receipt = {
        "schema": "cmix21_lstm200_fx2lite428_stats_failure_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "exact_guarded_10m_terminal_symbolized_codec_failure",
        "scope": {"raw_bytes": EXPECTED_SCOPE_BYTES, "article_order": "original"},
        "artifacts": {
            "recovery_receipt": artifact(args.recovery_receipt),
            "source_package_receipt": artifact(source_receipt_path),
            "wrapper": wrapper,
            "backend": backend,
            "symbol_backend": artifact(args.symbol_backend),
            "input": input_artifact,
            "guard": artifact(args.guard),
            "stderr_log": artifact(args.stderr_log),
            "preserved_wrt_stream": artifact(args.preserved_wrt_stream),
            "canonical_store": artifact(args.canonical_store),
            "kernel_fault_log": artifact(args.kernel_fault_log),
        },
        "metrics": {
            "last_reported_wrt_progress_percent": progress,
            "crashed_process_pid": pid,
            "crash_virtual_address_hex": f"0x{crash_address:x}",
            "max_sampled_single_rss_kib": guard["max_sampled_single_rss_kib"],
            "max_sampled_tree_rss_kib": guard["max_sampled_tree_rss_kib"],
            "decimal_10gb_limit_kib": guard["official_decimal_limit_kib"],
        },
        "diagnosis": {
            "failure_class": "sigsegv_not_memory",
            "kernel_fault_line": kernel_line,
            "source_mapping": source_mapping,
            "machine_code_window_identity": True,
            "root_boundary": (
                "FX2-lite PPMD processSymbol2_T dereferenced an invalid statistics "
                "span while preparing the next-byte distribution"
            ),
        },
        "proof": {
            "terminal_guard": True,
            "rss_guard_exceeded": False,
            "official_decimal_over_limit_kib": 0,
            "completed_archive_exists": False,
            "preserved_wrt_matches_canonical_store": True,
            "release_to_symbol_machine_code_identity": True,
        },
        "decision": {
            "decode_authorized": False,
            "determinism_replay_authorized": False,
            "official_1g_gate_authorized": False,
            "promotion_authorized": False,
            "stats_span_recovery_replay_authorized": True,
            "verdict": "combined_v7_recovery_rejected_at_10m_statistics_pointer_boundary",
            "next_action": (
                "validate deterministic context, statistics-span, suffix, and successor "
                "recovery with exact 1M archive identity before crossing this WRT boundary"
            ),
        },
        "claim_boundary": (
            "No completed exact-10M archive or compression score exists. This receipt "
            "localizes a codec-correctness failure and cannot support a score forecast "
            "promotion or a 10.95 percent claim."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
