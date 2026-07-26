#!/usr/bin/env python3
"""Seal the LZMA-ZIP accounting bridge for the endpoint428 online mixer."""

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


TARGET_SCORE = 108_000_000
BASE_FORECAST_SCORE = 109_557_404
BASE_PACKAGE_BYTES = 349_195
EXPECTED_OLD_PACKAGE_BYTES = 350_942
EXPECTED_ARCHIVE_BYTES = 1_635_174
EXPECTED_SAVED_BYTES = 521
CALIBRATION_FACTOR = 66.955334
EXPECTED_SCOPE_BYTES = 10_000_000
EXPECTED_INPUT_SHA256 = (
    "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97"
)


def economics(*, package_bytes: int) -> dict[str, Any]:
    incremental_program_bytes = package_bytes - BASE_PACKAGE_BYTES
    projected_float = (
        BASE_FORECAST_SCORE
        + incremental_program_bytes
        - EXPECTED_SAVED_BYTES * CALIBRATION_FACTOR
    )
    projected = math.ceil(projected_float)
    return {
        "target_score_bytes": TARGET_SCORE,
        "base_forecast_score_bytes": BASE_FORECAST_SCORE,
        "base_package_bytes": BASE_PACKAGE_BYTES,
        "prior_candidate_package_bytes": EXPECTED_OLD_PACKAGE_BYTES,
        "candidate_package_bytes": package_bytes,
        "package_saved_bytes_vs_prior": EXPECTED_OLD_PACKAGE_BYTES - package_bytes,
        "incremental_program_bytes_vs_base": incremental_program_bytes,
        "candidate_archive_bytes_10m": EXPECTED_ARCHIVE_BYTES,
        "saved_bytes_10m": EXPECTED_SAVED_BYTES,
        "saved_bytes_per_1m": EXPECTED_SAVED_BYTES / 10,
        "calibration_factor": CALIBRATION_FACTOR,
        "provisional_calibrated_score_float": projected_float,
        "conservative_provisional_score_bytes": projected,
        "provisional_target_margin_bytes": TARGET_SCORE - projected,
        "economics_pass": projected <= TARGET_SCORE,
    }


def require_same_artifact(left: dict[str, Any], right: dict[str, Any], label: str) -> None:
    for key in ("bytes", "sha256"):
        if left.get(key) != right.get(key):
            raise ValueError(f"{label} {key} identity failed")


def require_clean_guard(path: Path) -> dict[str, Any]:
    guard = load_object(path)
    decimal_limit = guard.get("official_decimal_limit_kib")
    peak_single = guard.get("max_sampled_single_rss_kib")
    if not (
        guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib") == 0
        and isinstance(decimal_limit, int)
        and isinstance(peak_single, int)
        and peak_single <= decimal_limit
    ):
        raise ValueError(f"guard is not clean and decimal-compliant: {path}")
    return guard


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-1m-receipt", type=Path, required=True)
    parser.add_argument("--terminal-10m-receipt", type=Path, required=True)
    parser.add_argument("--source-package-receipt", type=Path, required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--restored", type=Path)
    parser.add_argument("--decode-guard", type=Path)
    parser.add_argument("--archive-second", type=Path)
    parser.add_argument("--determinism-guard", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    native = load_object(args.native_1m_receipt)
    terminal = load_object(args.terminal_10m_receipt)
    package = load_object(args.source_package_receipt)
    if native.get("schema") != "endpoint428_pair_layer0_native_receipt_v1":
        raise ValueError("unexpected native 1M receipt schema")
    if terminal.get("schema") != "endpoint428_pair_layer0_native_10m_receipt_v1":
        raise ValueError("unexpected terminal 10M receipt schema")
    if package.get("schema") != "reproducible_source_shar_package_v1":
        raise ValueError("unexpected source package receipt schema")
    proof = package.get("proof", {})
    for field in (
        "proof_complete",
        "clean_build_complete",
        "clean_backend_identity",
        "clean_program_identity",
        "reference_backend_identity",
    ):
        if proof.get(field) is not True:
            raise ValueError(f"source package proof failed {field}")
    zip_proof = package.get("zip", {})
    if not (
        zip_proof.get("compression_method") == "lzma"
        and zip_proof.get("all_entries_expected_method") is True
        and zip_proof.get("direct_entries_ok") is True
        and zip_proof.get("integrity_ok") is True
    ):
        raise ValueError("source package is not a valid direct-entry LZMA ZIP")

    package_a = package["artifacts"]["zip_a"]
    package_b = package["artifacts"]["zip_b"]
    require_same_artifact(package_a, package_b, "source package")
    clean_a = package["artifacts"]["clean_program_a"]
    clean_b = package["artifacts"]["clean_program_b"]
    require_same_artifact(clean_a, clean_b, "clean program")
    require_same_artifact(clean_a, native["artifacts"]["clean_program_a"], "native program")
    if terminal["artifacts"]["archive"]["bytes"] != EXPECTED_ARCHIVE_BYTES:
        raise ValueError("exact 10M archive changed")
    if terminal["economics"]["saved_bytes_10m"] != EXPECTED_SAVED_BYTES:
        raise ValueError("exact 10M gain changed")

    accounting = economics(package_bytes=int(package_a["bytes"]))
    if accounting["package_saved_bytes_vs_prior"] <= 0:
        raise ValueError("LZMA source package does not save bytes")
    if not accounting["economics_pass"]:
        raise ValueError("LZMA source package does not clear the counted forecast")

    replay_paths = (
        args.input,
        args.restored,
        args.decode_guard,
        args.archive_second,
        args.determinism_guard,
    )
    replay_requested = all(path is not None for path in replay_paths)
    if any(path is not None for path in replay_paths) and not replay_requested:
        raise ValueError("all replay arguments must be provided together")

    replay_artifacts: dict[str, dict[str, Any]] = {}
    resources: dict[str, dict[str, int]] = {}
    if replay_requested:
        assert args.input is not None
        assert args.restored is not None
        assert args.decode_guard is not None
        assert args.archive_second is not None
        assert args.determinism_guard is not None
        input_artifact = artifact(args.input)
        if not (
            input_artifact["bytes"] == EXPECTED_SCOPE_BYTES
            and input_artifact["sha256"] == EXPECTED_INPUT_SHA256
        ):
            raise ValueError("input is not canonical original-order enwik9 10M")
        archive_path = Path(str(terminal["artifacts"]["archive"]["path"]))
        require_same_artifact(artifact(archive_path), terminal["artifacts"]["archive"], "archive")
        decode_wrapper = Path(str(clean_a["path"]))
        determinism_wrapper = Path(str(clean_b["path"]))
        require_same_artifact(artifact(decode_wrapper), clean_a, "decode wrapper")
        require_same_artifact(
            artifact(determinism_wrapper), clean_b, "determinism wrapper"
        )
        decode_guard = require_clean_guard(args.decode_guard)
        determinism_guard = require_clean_guard(args.determinism_guard)
        require_guard_invocation(
            decode_guard,
            wrapper=decode_wrapper,
            mode="d",
            source=archive_path,
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
        require_same_artifact(input_artifact, restored, "exact 10M roundtrip")
        require_same_artifact(
            terminal["artifacts"]["archive"],
            archive_second,
            "exact 10M deterministic archive replay",
        )
        replay_artifacts = {
            "input": input_artifact,
            "restored": restored,
            "decode_guard": artifact(args.decode_guard),
            "archive_second": archive_second,
            "determinism_guard": artifact(args.determinism_guard),
        }
        resources = {
            "decode": {
                "max_sampled_single_rss_kib": int(
                    decode_guard["max_sampled_single_rss_kib"]
                ),
                "max_sampled_tree_rss_kib": int(
                    decode_guard["max_sampled_tree_rss_kib"]
                ),
                "official_decimal_over_limit_kib": 0,
            },
            "determinism": {
                "max_sampled_single_rss_kib": int(
                    determinism_guard["max_sampled_single_rss_kib"]
                ),
                "max_sampled_tree_rss_kib": int(
                    determinism_guard["max_sampled_tree_rss_kib"]
                ),
                "official_decimal_over_limit_kib": 0,
            },
        }

    receipt = {
        "schema": "endpoint428_pair_layer0_lzma_package_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": (
            "constructive_counted_exact_10m_lzma_package_and_codec_proof"
            if replay_requested
            else "counted_lzma_zip_package_plus_guarded_exact_10m_archive"
        ),
        "scope": {"raw_bytes": 10_000_000, "article_order": "original"},
        "algorithm": (
            "endpoint428 compact/FX2 pair plus layer-0 online residual mixer; "
            "unchanged codec, LZMA-method source ZIP"
        ),
        "economics": accounting,
        "proof": {
            "direct_entry_zip": True,
            "zip_lzma_method": True,
            "source_reconstruction_ok": True,
            "two_clean_builds_identical": True,
            "clean_program_matches_native_program": True,
            "exact_10m_archive_identity_preserved": True,
            "roundtrip_ok": replay_requested,
            "determinism_ok": replay_requested,
        },
        "resources": resources,
        "artifacts": {
            "native_1m_receipt": artifact(args.native_1m_receipt),
            "terminal_10m_receipt": artifact(args.terminal_10m_receipt),
            "source_package_receipt": artifact(args.source_package_receipt),
            "source_package": package_a,
            "clean_program_a": clean_a,
            "clean_program_b": clean_b,
            "archive": terminal["artifacts"]["archive"],
            **replay_artifacts,
        },
        "decision": {
            "verdict": (
                "constructive_exact_10m_lzma_pass_authorizes_official_1g_gate"
                if replay_requested
                else "reopen_exact_10m_codec_replay_after_counted_package_pass"
            ),
            "decode_authorized": not replay_requested,
            "determinism_authorized": not replay_requested,
            "official_1g_gate_authorized": replay_requested,
            "next_action": (
                "freeze this package and run the guarded exact full-enwik9 gate"
                if replay_requested
                else "run guarded exact 10M decode and deterministic re-encode"
            ),
        },
        "claim_boundary": (
            "The LZMA-method ZIP is a counted source package under the official "
            "zipped-source relaxation and clean-builds to the exact wrapper-proven "
            "program. The resulting score is a calibrated exact-10M forecast, not an "
            "official full-enwik9 result."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
