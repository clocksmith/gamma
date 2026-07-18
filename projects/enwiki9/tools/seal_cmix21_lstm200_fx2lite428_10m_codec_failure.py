#!/usr/bin/env python3
"""Seal the non-memory exact-10M endpoint428 codec failure."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__:
    from .seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        load_object,
        require_clean_guard,
        require_guard_invocation,
    )
else:
    from seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        load_object,
        require_clean_guard,
        require_guard_invocation,
    )


EXPECTED_SCOPE_BYTES = 10_000_000
EXPECTED_INPUT_SHA256 = (
    "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97"
)


def last_progress_percent(text: str) -> float:
    matches = re.findall(r"progress:\s*([0-9]+(?:\.[0-9]+)?)%", text)
    if not matches:
        raise RuntimeError("codec log has no progress sample")
    return float(matches[-1])


def require_nonmemory_codec_failure(guard: dict[str, Any]) -> None:
    if not (
        guard.get("status") == "complete"
        and guard.get("returncode") != 0
        and guard.get("limit_mode") == "tree"
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib") == 0
        and int(guard.get("max_sampled_tree_rss_kib", 0))
        <= int(guard.get("official_decimal_limit_kib", -1))
    ):
        raise RuntimeError("guard does not prove a terminal non-memory codec failure")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recovery-receipt", type=Path, required=True)
    parser.add_argument("--wrapper", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--archive-path", type=Path, required=True)
    parser.add_argument("--guard", type=Path, required=True)
    parser.add_argument("--stderr-log", type=Path, required=True)
    parser.add_argument("--preserved-wrt-stream", type=Path, required=True)
    parser.add_argument("--ram-ppmd-1m-archive", type=Path, required=True)
    parser.add_argument("--ram-ppmd-1m-guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    recovery = load_object(args.recovery_receipt)
    if recovery.get("schema") != "cmix21_lstm200_fx2lite428_ppmd_recovery_v1":
        raise RuntimeError("unexpected recovery receipt schema")
    wrapper = artifact(args.wrapper)
    recorded_wrapper = recovery["artifacts"]["repair_wrapper"]
    if any(wrapper[key] != recorded_wrapper[key] for key in ("bytes", "sha256")):
        raise RuntimeError("failed wrapper differs from the sealed v6 repair")

    input_artifact = artifact(args.input)
    if not (
        input_artifact["bytes"] == EXPECTED_SCOPE_BYTES
        and input_artifact["sha256"] == EXPECTED_INPUT_SHA256
    ):
        raise RuntimeError("failure did not use canonical original-order 10M")
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
    stderr_text = args.stderr_log.read_text(errors="replace")
    progress = last_progress_percent(stderr_text)

    ram_guard = require_clean_guard(args.ram_ppmd_1m_guard)
    ram_archive = artifact(args.ram_ppmd_1m_archive)
    recovery_archive = recovery["artifacts"]["repair_1m_archive"]
    if any(ram_archive[key] != recovery_archive[key] for key in ("bytes", "sha256")):
        raise RuntimeError("RAM-backed PPMD changes the exact 1M archive")

    receipt = {
        "schema": "cmix21_lstm200_fx2lite428_10m_codec_failure_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "exact_guarded_10m_terminal_codec_failure",
        "scope": {"raw_bytes": EXPECTED_SCOPE_BYTES, "article_order": "original"},
        "artifacts": {
            "recovery_receipt": artifact(args.recovery_receipt),
            "wrapper": wrapper,
            "input": input_artifact,
            "guard": artifact(args.guard),
            "stderr_log": artifact(args.stderr_log),
            "preserved_wrt_stream": artifact(args.preserved_wrt_stream),
            "ram_ppmd_1m_archive": ram_archive,
            "ram_ppmd_1m_guard": artifact(args.ram_ppmd_1m_guard),
        },
        "metrics": {
            "last_reported_wrt_progress_percent": progress,
            "max_sampled_tree_rss_kib": guard["max_sampled_tree_rss_kib"],
            "decimal_10gb_limit_kib": guard["official_decimal_limit_kib"],
            "decimal_tree_rss_margin_kib": guard["official_decimal_limit_kib"]
            - guard["max_sampled_tree_rss_kib"],
        },
        "diagnosis": {
            "failure_class": "codec_returncode_failure_not_memory",
            "remaining_silent_exit_surface": (
                "FX2-lite PPMD periodic disk-backed unmap/remap path"
            ),
            "independent_control": (
                "RAM-backed FX2-lite PPMD is archive-identical at exact 1M"
            ),
        },
        "proof": {
            "terminal_guard": True,
            "rss_guard_exceeded": False,
            "official_decimal_over_limit_kib": 0,
            "completed_archive_exists": False,
            "ram_ppmd_1m_archive_identity": True,
        },
        "decision": {
            "decode_authorized": False,
            "determinism_replay_authorized": False,
            "official_1g_gate_authorized": False,
            "promotion_authorized": False,
            "combined_ram_ppmd_context_guard_boundary_replay_authorized": True,
            "verdict": "repair_v6_rejected_at_10m_codec_correctness_boundary",
            "next_action": (
                "combine the archive-identical RAM-backed PPMD storage path with "
                "the proven context-chain guard and require exact 1.5M archive identity"
            ),
        },
        "claim_boundary": (
            "No completed 10M archive or compression score exists. This is a terminal "
            "codec-correctness receipt and cannot support an economics or 10.95 percent claim."
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
