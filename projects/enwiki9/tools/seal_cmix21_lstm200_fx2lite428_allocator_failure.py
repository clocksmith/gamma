#!/usr/bin/env python3
"""Seal the exact-10M v9 FX2-lite PPMD allocator free-list crash."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

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
    from .seal_cmix21_lstm200_fx2lite428_stats_failure import (
        addr2line,
        load_file_offset,
        parse_kernel_fault,
        peak_process_pid,
        read_window,
        require_store_payload,
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
    from seal_cmix21_lstm200_fx2lite428_stats_failure import (
        addr2line,
        load_file_offset,
        parse_kernel_fault,
        peak_process_pid,
        read_window,
        require_store_payload,
    )


EXPECTED_FAILURE_FUNCTION = "Fx2LitePPMD::ppmd_Model::remove"
EXPECTED_CALLER_FUNCTIONS = (
    "Fx2LitePPMD::ppmd_Model::AllocUnits",
    "Fx2LitePPMD::ppmd_Model::UpdateModel",
)


def require_allocator_mapping(source_mapping: str) -> None:
    required = (EXPECTED_FAILURE_FUNCTION, *EXPECTED_CALLER_FUNCTIONS)
    missing = [function for function in required if function not in source_mapping]
    if missing:
        raise RuntimeError(f"fault mapping misses allocator chain: {missing}")


def require_same_artifact(first: dict[str, object], second: dict[str, object]) -> None:
    if any(first[key] != second[key] for key in ("bytes", "sha256")):
        raise RuntimeError("artifact identity differs from sealed recovery")


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
    if recovery.get("schema") != "cmix21_lstm200_fx2lite428_stats_recovery_v1":
        raise RuntimeError("unexpected statistics-recovery receipt")
    if recovery.get("decision", {}).get("exact_10m_confirmation_authorized") is not True:
        raise RuntimeError("statistics recovery did not authorize exact 10M")

    wrapper = artifact(args.wrapper)
    backend = artifact(args.backend)
    require_same_artifact(wrapper, recovery["artifacts"]["wrapper"])
    require_same_artifact(backend, recovery["artifacts"]["backend"])

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
    require_allocator_mapping(source_mapping)

    receipt = {
        "schema": "cmix21_lstm200_fx2lite428_allocator_failure_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "exact_guarded_10m_terminal_symbolized_allocator_failure",
        "scope": {"raw_bytes": EXPECTED_SCOPE_BYTES, "article_order": "original"},
        "artifacts": {
            "recovery_receipt": artifact(args.recovery_receipt),
            "source_package_receipt": recovery["artifacts"]["source_package_receipt"],
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
            "decimal_tree_rss_margin_kib": (
                guard["official_decimal_limit_kib"] - guard["max_sampled_tree_rss_kib"]
            ),
        },
        "diagnosis": {
            "failure_class": "sigsegv_not_memory",
            "kernel_fault_line": kernel_line,
            "source_mapping": source_mapping,
            "machine_code_window_identity": True,
            "root_boundary": (
                "FX2-lite PPMD followed a malformed allocator free-list link while "
                "removing a block during AllocUnits; downstream context/statistics "
                "guards cannot protect this earlier allocator boundary"
            ),
            "existing_proven_fix_source": (
                "the primary CMIX21 PPMD implementation in the same candidate tree "
                "already validates heap pointers, free-list links, block spans, "
                "context chains, and allocator rebuilds"
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
            "full_primary_ppmd_safety_port_replay_authorized": True,
            "verdict": "stats_recovery_v9_rejected_at_10m_allocator_boundary",
            "next_action": (
                "port the primary CMIX21 PPMD heap/free-list/context validation layer "
                "into FX2-lite, guarantee zero-initialized model memory, and require "
                "exact 1M archive identity before another exact 10M gate"
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
