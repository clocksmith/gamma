#!/usr/bin/env python3
"""Seal the strict exact-10M endpoint428 recovery economics gate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__:
    from .seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        TARGET_SCORE_BYTES,
        artifact,
        load_object,
        require_clean_guard,
        require_guard_invocation,
    )
else:  # Direct script execution from the repository root.
    from seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        TARGET_SCORE_BYTES,
        artifact,
        load_object,
        require_clean_guard,
        require_guard_invocation,
    )


EXPECTED_SCOPE_BYTES = 10_000_000
EXPECTED_INPUT_SHA256 = (
    "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97"
)
FULL_SCOPE_DIVISOR = 100


def recovery_wrapper_key(schema: str) -> str:
    """Return the artifact key holding the wrapper for a recovery lineage."""

    if schema in {
        "cmix21_lstm200_fx2lite428_ram_recovery_v1",
        "cmix21_lstm200_fx2lite428_stats_recovery_v1",
        "cmix21_lstm200_fx2lite428_allocator_recovery_v1",
        "cmix21_lstm200_fx2lite428_context_recovery_v1",
    }:
        return "wrapper"
    if schema == "cmix21_lstm200_fx2lite428_ppmd_recovery_v1":
        return "repair_wrapper"
    raise RuntimeError("unexpected recovery receipt schema")


def calculate_10m_economics(
    *,
    base_archive_bytes: int,
    candidate_archive_bytes: int,
    recovery_economics: dict[str, Any],
) -> dict[str, int | float | bool]:
    gross_saved_10m = base_archive_bytes - candidate_archive_bytes
    projected_gain_1g = gross_saved_10m * FULL_SCOPE_DIVISOR
    required_gain_1g = int(
        recovery_economics["conservative_required_endpoint_gain_bytes_1g"]
    )
    margin = projected_gain_1g - required_gain_1g
    ceiling = int(recovery_economics["strict_candidate_archive_ceiling_bytes_10m"])
    return {
        "target_score_bytes": TARGET_SCORE_BYTES,
        "compact_base_archive_bytes_10m": base_archive_bytes,
        "candidate_archive_bytes_10m": candidate_archive_bytes,
        "gross_saved_bytes_10m": gross_saved_10m,
        "gross_saved_bytes_per_1m": gross_saved_10m / 10,
        "projected_endpoint_gain_bytes_1g": projected_gain_1g,
        "conservative_required_endpoint_gain_bytes_1g": required_gain_1g,
        "strict_candidate_archive_ceiling_bytes_10m": ceiling,
        "archive_ceiling_margin_bytes": ceiling - candidate_archive_bytes,
        "conservative_projected_margin_bytes": margin,
        "conservative_projected_score_bytes": TARGET_SCORE_BYTES - margin,
        "strict_10m_economics_pass": bool(
            candidate_archive_bytes <= ceiling and margin >= 0
        ),
    }


def require_recorded_artifact(entry: dict[str, Any], observed: dict[str, Any]) -> None:
    if any(entry[key] != observed[key] for key in ("bytes", "sha256")):
        raise RuntimeError(f"recorded artifact differs: {observed['path']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recovery-receipt", type=Path, required=True)
    parser.add_argument("--blend-terminal-receipt", type=Path, required=True)
    parser.add_argument("--wrapper", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--encode-guard", type=Path, required=True)
    parser.add_argument("--restored", type=Path)
    parser.add_argument("--decode-guard", type=Path)
    parser.add_argument("--archive-second", type=Path)
    parser.add_argument("--determinism-guard", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    recovery = load_object(args.recovery_receipt)
    blend = load_object(args.blend_terminal_receipt)
    recovery_schema = recovery.get("schema")
    wrapper_key = recovery_wrapper_key(recovery_schema)
    if recovery.get("decision", {}).get("exact_10m_confirmation_authorized") is not True:
        raise RuntimeError("recovery receipt does not authorize exact 10M")
    if blend.get("schema") != "fx2_cmix21_original_order_blend_terminal_v1":
        raise RuntimeError("unexpected blend terminal receipt schema")

    wrapper = artifact(args.wrapper)
    require_recorded_artifact(recovery["artifacts"][wrapper_key], wrapper)
    input_artifact = artifact(args.input)
    if not (
        input_artifact["bytes"] == EXPECTED_SCOPE_BYTES
        and input_artifact["sha256"] == EXPECTED_INPUT_SHA256
    ):
        raise RuntimeError("wrong canonical original-order 10M input")
    base_archive = artifact(args.base_archive)
    require_recorded_artifact(
        blend["artifacts"]["compact_trace_archive"], base_archive
    )
    archive = artifact(args.archive)
    encode_guard = require_clean_guard(args.encode_guard)
    require_guard_invocation(
        encode_guard,
        wrapper=args.wrapper,
        mode="c",
        source=args.input,
        target=args.archive,
    )

    economics = calculate_10m_economics(
        base_archive_bytes=base_archive["bytes"],
        candidate_archive_bytes=archive["bytes"],
        recovery_economics=recovery["economics"],
    )
    economics_pass = bool(economics["strict_10m_economics_pass"])
    optional = (
        args.restored,
        args.decode_guard,
        args.archive_second,
        args.determinism_guard,
    )
    final_requested = all(path is not None for path in optional)
    if any(path is not None for path in optional) and not final_requested:
        raise RuntimeError("final replay arguments must be supplied together")
    if final_requested and not economics_pass:
        raise RuntimeError("decode/determinism cannot relabel a strict economics miss")

    artifacts: dict[str, Any] = {
        "recovery_receipt": artifact(args.recovery_receipt),
        "blend_terminal_receipt": artifact(args.blend_terminal_receipt),
        "wrapper": wrapper,
        "input": input_artifact,
        "compact_base_archive": base_archive,
        "archive": archive,
        "encode_guard": artifact(args.encode_guard),
    }
    proof: dict[str, bool] = {
        "canonical_original_order_input": True,
        "same_compact_base_archive": True,
        "clean_encode_tree_rss_guard": True,
        "strict_10m_economics_pass": economics_pass,
        "roundtrip_ok": False,
        "determinism_ok": False,
    }

    if final_requested:
        assert args.restored is not None
        assert args.decode_guard is not None
        assert args.archive_second is not None
        assert args.determinism_guard is not None
        decode_guard = require_clean_guard(args.decode_guard)
        determinism_guard = require_clean_guard(args.determinism_guard)
        require_guard_invocation(
            decode_guard,
            wrapper=args.wrapper,
            mode="d",
            source=args.archive,
            target=args.restored,
        )
        require_guard_invocation(
            determinism_guard,
            wrapper=args.wrapper,
            mode="c",
            source=args.input,
            target=args.archive_second,
        )
        restored = artifact(args.restored)
        archive_second = artifact(args.archive_second)
        if any(
            input_artifact[key] != restored[key] for key in ("bytes", "sha256")
        ):
            raise RuntimeError("exact 10M roundtrip failed")
        if any(archive[key] != archive_second[key] for key in ("bytes", "sha256")):
            raise RuntimeError("exact 10M archive determinism failed")
        artifacts.update(
            {
                "restored": restored,
                "decode_guard": artifact(args.decode_guard),
                "archive_second": archive_second,
                "determinism_guard": artifact(args.determinism_guard),
            }
        )
        proof["roundtrip_ok"] = True
        proof["determinism_ok"] = True

    if not economics_pass:
        verdict = "retire_repaired_endpoint428_strict_10m_economics_miss"
        next_action = (
            "preserve this endpoint as causal evidence and return to the matched "
            "component universe for a stronger increment over compact-200"
        )
    elif not final_requested:
        verdict = "strict_10m_archive_pass_requires_roundtrip_determinism"
        next_action = (
            "decode the exact archive, compare it with the canonical input, and "
            "repeat the unchanged encode"
        )
    else:
        verdict = "constructive_counted_10m_pass_requires_larger_gate_decision"
        next_action = (
            "freeze this exact package and assess transfer margin before authorizing "
            "any larger guarded replay"
        )

    receipt = {
        "schema": "cmix21_lstm200_fx2lite428_native_10m_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": (
            "constructive_counted_native_wrapper_10m_prefix"
            if final_requested
            else "exact_guarded_10m_archive_screen"
        ),
        "scope": {"raw_bytes": EXPECTED_SCOPE_BYTES, "article_order": "original"},
        "artifacts": artifacts,
        "metrics": {
            "max_encode_tree_rss_kib": encode_guard["max_sampled_tree_rss_kib"],
            "decimal_10gb_limit_kib": encode_guard["official_decimal_limit_kib"],
        },
        "economics": economics,
        "proof": proof,
        "decision": {
            "decode_authorized": economics_pass and not final_requested,
            "determinism_replay_authorized": economics_pass and not final_requested,
            "official_1g_gate_authorized": False,
            "promotion_authorized": False,
            "verdict": verdict,
            "next_action": next_action,
        },
        "claim_boundary": (
            "This is exact 10M evidence only. Even a clean constructive pass remains "
            "a prefix forecast, not a full-corpus upper bound or a 10.95 percent claim."
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
