#!/usr/bin/env python3
"""Seal the endpoint428 pair/layer-0 exact-10M economics and codec proof."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any

if __package__:
    from .seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        load_object,
        require_guard_invocation,
    )
else:
    from seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        load_object,
        require_guard_invocation,
    )


EXPECTED_SCOPE_BYTES = 10_000_000
EXPECTED_INPUT_SHA256 = (
    "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97"
)
EXPECTED_BASE_ARCHIVE_BYTES = 1_635_695


def require_clean_guard(path: Path) -> dict[str, Any]:
    guard = load_object(path)
    measured = guard.get("official_decimal_measured_kib")
    limit = guard.get("official_decimal_limit_kib")
    if not (
        guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib") == 0
        and isinstance(measured, int)
        and isinstance(limit, int)
        and measured <= limit
    ):
        raise ValueError(f"guard is not clean and decimal-compliant: {path}")
    return guard


def calculate_economics(
    *,
    base_archive_bytes: int,
    candidate_archive_bytes: int,
    base_forecast_score_bytes: int,
    incremental_program_bytes: int,
    calibration_factor: float,
    required_gain_bytes: int,
    archive_ceiling_bytes: int,
) -> dict[str, Any]:
    gain = base_archive_bytes - candidate_archive_bytes
    projected_score_float = (
        base_forecast_score_bytes
        + incremental_program_bytes
        - gain * calibration_factor
    )
    projected_score = math.ceil(projected_score_float)
    passed = bool(
        gain >= required_gain_bytes
        and candidate_archive_bytes <= archive_ceiling_bytes
    )
    return {
        "base_archive_bytes_10m": base_archive_bytes,
        "candidate_archive_bytes_10m": candidate_archive_bytes,
        "saved_bytes_10m": gain,
        "saved_bytes_per_1m": gain / 10,
        "calibration_factor": calibration_factor,
        "incremental_program_bytes": incremental_program_bytes,
        "required_saved_bytes_10m": required_gain_bytes,
        "maximum_candidate_archive_bytes_10m": archive_ceiling_bytes,
        "archive_ceiling_margin_bytes": archive_ceiling_bytes
        - candidate_archive_bytes,
        "provisional_calibrated_score_float": projected_score_float,
        "conservative_provisional_score_bytes": projected_score,
        "provisional_target_margin_bytes": 109_500_000 - projected_score,
        "economics_pass": passed,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-1m-receipt", type=Path, required=True)
    parser.add_argument("--wrapper", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--encode-guard", type=Path, required=True)
    parser.add_argument("--restored", type=Path)
    parser.add_argument("--decode-guard", type=Path)
    parser.add_argument("--archive-second", type=Path)
    parser.add_argument("--determinism-guard", type=Path)
    parser.add_argument("--determinism-wrapper", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    native = load_object(args.native_1m_receipt)
    if native.get("schema") != "endpoint428_pair_layer0_native_receipt_v1":
        raise ValueError("unexpected native 1M receipt schema")
    prior = native["economics"]

    input_artifact = artifact(args.input)
    if not (
        input_artifact["bytes"] == EXPECTED_SCOPE_BYTES
        and input_artifact["sha256"] == EXPECTED_INPUT_SHA256
    ):
        raise ValueError("input is not canonical original-order enwik9 10M")
    base_archive = artifact(args.base_archive)
    if base_archive["bytes"] != EXPECTED_BASE_ARCHIVE_BYTES:
        raise ValueError("unexpected endpoint428 exact-10M base archive")
    wrapper = artifact(args.wrapper)
    recorded_wrapper = native["artifacts"]["clean_program_b"]
    if any(wrapper[key] != recorded_wrapper[key] for key in ("bytes", "sha256")):
        raise ValueError("wrapper differs from the sealed native 1M program")

    archive = artifact(args.archive)
    encode_guard = require_clean_guard(args.encode_guard)
    require_guard_invocation(
        encode_guard,
        wrapper=args.wrapper,
        mode="c",
        source=args.input,
        target=args.archive,
    )
    economics = calculate_economics(
        base_archive_bytes=base_archive["bytes"],
        candidate_archive_bytes=archive["bytes"],
        base_forecast_score_bytes=int(prior["base_forecast_score_bytes"]),
        incremental_program_bytes=int(prior["incremental_program_bytes"]),
        calibration_factor=float(prior["ten_m_calibration_factor"]),
        required_gain_bytes=int(prior["required_exact_10m_gain_bytes"]),
        archive_ceiling_bytes=int(prior["maximum_exact_10m_archive_bytes"]),
    )

    replay_paths = (
        args.restored,
        args.decode_guard,
        args.archive_second,
        args.determinism_guard,
    )
    replay_requested = all(path is not None for path in replay_paths)
    if any(path is not None for path in replay_paths) and not replay_requested:
        raise ValueError("all replay arguments must be provided together")
    if replay_requested and not economics["economics_pass"]:
        raise ValueError("codec replay cannot promote an economics miss")
    determinism_wrapper = args.determinism_wrapper or args.wrapper
    if args.determinism_wrapper is not None and not replay_requested:
        raise ValueError("--determinism-wrapper requires complete replay arguments")
    determinism_wrapper_artifact = artifact(determinism_wrapper)
    recorded_determinism_wrapper = native["artifacts"]["clean_program_a"]
    if any(
        determinism_wrapper_artifact[key] != recorded_determinism_wrapper[key]
        for key in ("bytes", "sha256")
    ):
        raise ValueError("determinism wrapper differs from sealed clean program A")

    proof = {
        "canonical_input": True,
        "sealed_wrapper_identity": True,
        "clean_encode_guard": True,
        "economics_pass": economics["economics_pass"],
        "roundtrip_ok": False,
        "determinism_ok": False,
    }
    artifacts = {
        "native_1m_receipt": artifact(args.native_1m_receipt),
        "wrapper": wrapper,
        "input": input_artifact,
        "base_archive": base_archive,
        "archive": archive,
        "encode_guard": artifact(args.encode_guard),
    }
    resources = {
        "encode": {
            "max_sampled_single_rss_kib": encode_guard.get(
                "max_sampled_single_rss_kib"
            ),
            "max_sampled_tree_rss_kib": encode_guard.get(
                "max_sampled_tree_rss_kib"
            ),
            "official_decimal_over_limit_kib": 0,
        }
    }

    if replay_requested:
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
            wrapper=determinism_wrapper,
            mode="c",
            source=args.input,
            target=args.archive_second,
        )
        restored = artifact(args.restored)
        archive_second = artifact(args.archive_second)
        if any(input_artifact[key] != restored[key] for key in ("bytes", "sha256")):
            raise ValueError("exact 10M roundtrip failed")
        if any(archive[key] != archive_second[key] for key in ("bytes", "sha256")):
            raise ValueError("exact 10M deterministic archive replay failed")
        artifacts.update(
            {
                "restored": restored,
                "decode_guard": artifact(args.decode_guard),
                "archive_second": archive_second,
                "determinism_wrapper": determinism_wrapper_artifact,
                "determinism_guard": artifact(args.determinism_guard),
            }
        )
        resources.update(
            {
                "decode": {
                    "max_sampled_single_rss_kib": decode_guard.get(
                        "max_sampled_single_rss_kib"
                    ),
                    "max_sampled_tree_rss_kib": decode_guard.get(
                        "max_sampled_tree_rss_kib"
                    ),
                    "official_decimal_over_limit_kib": 0,
                },
                "determinism": {
                    "max_sampled_single_rss_kib": determinism_guard.get(
                        "max_sampled_single_rss_kib"
                    ),
                    "max_sampled_tree_rss_kib": determinism_guard.get(
                        "max_sampled_tree_rss_kib"
                    ),
                    "official_decimal_over_limit_kib": 0,
                },
            }
        )
        proof["roundtrip_ok"] = True
        proof["determinism_ok"] = True

    if not economics["economics_pass"]:
        verdict = "retire_unchanged_exact_10m_economics_miss"
        next_action = "return to a stronger endpoint428 residual mechanism"
    elif not replay_requested:
        verdict = "exact_10m_economics_pass_requires_codec_replay"
        next_action = "run guarded decode and deterministic re-encode"
    else:
        verdict = "constructive_exact_10m_pass_requires_larger_gate_decision"
        next_action = "freeze the package and decide the next disjoint or full gate"

    receipt = {
        "schema": "endpoint428_pair_layer0_native_10m_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": (
            "constructive_counted_exact_10m_prefix"
            if replay_requested
            else "guarded_exact_10m_archive_screen"
        ),
        "scope": {"raw_bytes": EXPECTED_SCOPE_BYTES, "article_order": "original"},
        "economics": economics,
        "proof": proof,
        "resources": resources,
        "artifacts": artifacts,
        "decision": {
            "decode_authorized": economics["economics_pass"]
            and not replay_requested,
            "determinism_authorized": economics["economics_pass"]
            and not replay_requested,
            "official_1g_gate_authorized": False,
            "verdict": verdict,
            "next_action": next_action,
        },
        "claim_boundary": (
            "This is exact 10M evidence only. A calibrated score below target is "
            "still provisional until a counted exact full-enwik9 proof passes."
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
