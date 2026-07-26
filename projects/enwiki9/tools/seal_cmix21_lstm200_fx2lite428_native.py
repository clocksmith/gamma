#!/usr/bin/env python3
"""Seal constructive compact-200 plus FX2-lite endpoint428 prefix evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASELINE_FORECAST_SCORE_BYTES = 110_181_114
BASELINE_PROGRAM_BYTES = 183_008
TARGET_SCORE_BYTES = 109_000_000
OPTION_BYTES = 3
RAW_SCOPE_BYTES = 1_000_000
CONFIRMATION_SCOPE_BYTES = 10_000_000
LEGACY_INCREMENTAL_FLOOR_BYTES_PER_1M = 154.324
EXPECTED_ENDPOINT_WEIGHT_PPM = 225_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def clean_tree_guard(guard: dict[str, Any]) -> bool:
    decimal_limit = int(guard.get("official_decimal_limit_kib", 0))
    return bool(
        guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("limit_mode") == "tree"
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib", 1) == 0
        and decimal_limit > 0
        and int(guard.get("max_sampled_tree_rss_kib", decimal_limit + 1))
        <= decimal_limit
    )


def require_guard_command(
    guard: dict[str, Any], *, wrapper: Path, mode: str, source: Path, target: Path
) -> None:
    command = guard.get("command")
    expected = [
        str(wrapper.resolve()),
        mode,
        str(source.resolve()),
        str(target.resolve()),
    ]
    if command != expected:
        raise RuntimeError(f"guard command differs from frozen wrapper command: {command}")


def calculate_economics(
    *,
    geometry_archive_10m: int,
    compact_archive_10m: int,
    compact_package_bytes: int,
    candidate_package_bytes: int,
    endpoint_full_saved_bytes: int,
    endpoint_holdout_rate_bytes_per_1m: float,
) -> dict[str, int | float | bool]:
    compact_archive_gain_1g = (
        geometry_archive_10m - compact_archive_10m
    ) * (1_000_000_000 // CONFIRMATION_SCOPE_BYTES)
    endpoint_full_gain_1g = endpoint_full_saved_bytes * (
        1_000_000_000 // RAW_SCOPE_BYTES
    )
    candidate_program_bytes = candidate_package_bytes + OPTION_BYTES
    candidate_program_delta = candidate_program_bytes - BASELINE_PROGRAM_BYTES
    direct_forecast_score = (
        BASELINE_FORECAST_SCORE_BYTES
        - compact_archive_gain_1g
        - endpoint_full_gain_1g
        + candidate_program_delta
    )

    package_delta = candidate_package_bytes - compact_package_bytes
    # The prior 154.324 B/M screen charged the compact package and one framing
    # byte. This original-order wrapper emits no framing byte, so remove it once.
    conservative_required_gain = round(
        LEGACY_INCREMENTAL_FLOOR_BYTES_PER_1M * 1000
        + package_delta
        - 1
    )
    conservative_full_margin = endpoint_full_gain_1g - conservative_required_gain
    conservative_holdout_gain = round(endpoint_holdout_rate_bytes_per_1m * 1000)
    conservative_holdout_margin = (
        conservative_holdout_gain - conservative_required_gain
    )
    conservative_full_score = TARGET_SCORE_BYTES - conservative_full_margin
    conservative_holdout_score = TARGET_SCORE_BYTES - conservative_holdout_margin
    return {
        "baseline_forecast_score_bytes": BASELINE_FORECAST_SCORE_BYTES,
        "baseline_program_bytes": BASELINE_PROGRAM_BYTES,
        "target_score_bytes": TARGET_SCORE_BYTES,
        "geometry_archive_bytes_10m": geometry_archive_10m,
        "compact_archive_bytes_10m": compact_archive_10m,
        "compact_archive_gain_bytes_10m": (
            geometry_archive_10m - compact_archive_10m
        ),
        "projected_compact_archive_gain_bytes_1g": compact_archive_gain_1g,
        "endpoint_full_saved_bytes_1m": endpoint_full_saved_bytes,
        "projected_endpoint_full_gain_bytes_1g": endpoint_full_gain_1g,
        "compact_source_package_bytes": compact_package_bytes,
        "candidate_source_package_bytes": candidate_package_bytes,
        "source_package_delta_bytes": package_delta,
        "option_bytes": OPTION_BYTES,
        "archive_marker_bytes": 0,
        "candidate_program_bytes": candidate_program_bytes,
        "candidate_program_delta_bytes": candidate_program_delta,
        "direct_term_forecast_score_bytes": direct_forecast_score,
        "direct_term_forecast_margin_bytes": (
            TARGET_SCORE_BYTES - direct_forecast_score
        ),
        "legacy_incremental_floor_bytes_per_1m": (
            LEGACY_INCREMENTAL_FLOOR_BYTES_PER_1M
        ),
        "conservative_required_endpoint_gain_bytes_1g": (
            conservative_required_gain
        ),
        "conservative_required_endpoint_gain_bytes_per_1m": (
            conservative_required_gain / 1000
        ),
        "conservative_full_forecast_score_bytes": conservative_full_score,
        "conservative_full_forecast_margin_bytes": conservative_full_margin,
        "endpoint_holdout_saved_bytes_per_1m": (
            endpoint_holdout_rate_bytes_per_1m
        ),
        "conservative_holdout_forecast_score_bytes": conservative_holdout_score,
        "conservative_holdout_forecast_margin_bytes": conservative_holdout_margin,
        "full_and_holdout_forecasts_below_target": bool(
            conservative_full_score <= TARGET_SCORE_BYTES
            and conservative_holdout_score <= TARGET_SCORE_BYTES
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package-receipt", type=Path, required=True)
    parser.add_argument("--blend-terminal-receipt", type=Path, required=True)
    parser.add_argument("--endpoint-screen", type=Path, required=True)
    parser.add_argument("--wrapper", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--backend-archive", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-second", type=Path, required=True)
    parser.add_argument("--restored", type=Path, required=True)
    parser.add_argument("--encode-guard", type=Path, required=True)
    parser.add_argument("--decode-guard", type=Path, required=True)
    parser.add_argument("--determinism-guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    package = load_object(args.source_package_receipt)
    blend = load_object(args.blend_terminal_receipt)
    endpoint = load_object(args.endpoint_screen)
    encode_guard = load_object(args.encode_guard)
    decode_guard = load_object(args.decode_guard)
    determinism_guard = load_object(args.determinism_guard)

    if package.get("schema") != "reproducible_source_shar_package_v1":
        raise RuntimeError("unexpected source-package receipt schema")
    package_proof = package.get("proof", {})
    if not (
        package_proof.get("proof_complete") is True
        and package_proof.get("clean_build_complete") is True
    ):
        raise RuntimeError("source package lacks complete clean-build proof")
    if blend.get("schema") != "fx2_cmix21_original_order_blend_terminal_v1":
        raise RuntimeError("unexpected blend terminal receipt schema")
    if endpoint.get("schema") != "cmix_aux_logit_blend_screen_v3":
        raise RuntimeError("unexpected endpoint screen schema")
    if endpoint.get("selection", {}).get("mix_mode") != "native_q16":
        raise RuntimeError("endpoint screen did not use the native Q16 mixer")
    if endpoint.get("selection", {}).get("selected_weight_ppm") != (
        EXPECTED_ENDPOINT_WEIGHT_PPM
    ):
        raise RuntimeError("endpoint blend weight changed")
    endpoint_replay = endpoint.get("exact_replay", {})
    if endpoint_replay.get("full", {}).get("rows") != 4_805_936:
        raise RuntimeError("endpoint screen has the wrong row scope")
    if endpoint.get("guardrails", {}).get("regret_budget_pass") is not True:
        raise RuntimeError("endpoint screen failed its regression budget")
    endpoint_identity = endpoint.get("identity", {})
    required_endpoint_identities = (
        "pair_base_equals_frozen_base_p1",
        "archive_payload_identity",
        "candidate_payload_equals_native_reference",
    )
    if any(endpoint_identity.get(key) is not True for key in required_endpoint_identities):
        raise RuntimeError("endpoint screen lacks exact native payload identity")

    for guard in (encode_guard, decode_guard, determinism_guard):
        if not clean_tree_guard(guard):
            raise RuntimeError("one or more wrapper guards are not clean tree guards")
    require_guard_command(
        encode_guard,
        wrapper=args.wrapper,
        mode="c",
        source=args.input,
        target=args.archive,
    )
    require_guard_command(
        decode_guard,
        wrapper=args.wrapper,
        mode="d",
        source=args.archive,
        target=args.restored,
    )
    require_guard_command(
        determinism_guard,
        wrapper=args.wrapper,
        mode="c",
        source=args.input,
        target=args.archive_second,
    )

    wrapper = artifact(args.wrapper)
    package_artifacts = package.get("artifacts", {})
    clean_program_a = package_artifacts.get("clean_program_a", {})
    clean_program_b = package_artifacts.get("clean_program_b", {})
    if not (
        clean_program_a.get("sha256") == wrapper["sha256"]
        and clean_program_b.get("sha256") == wrapper["sha256"]
    ):
        raise RuntimeError("wrapper-proven program differs from clean source build")

    input_artifact = artifact(args.input)
    restored = artifact(args.restored)
    if any(input_artifact[key] != restored[key] for key in ("bytes", "sha256")):
        raise RuntimeError("wrapper roundtrip failed")
    archive = artifact(args.archive)
    archive_second = artifact(args.archive_second)
    backend_archive = artifact(args.backend_archive)
    endpoint_inputs = endpoint.get("inputs", {})
    recorded_candidate_reference = endpoint_inputs.get(
        "candidate_reference_archive", {}
    )
    if any(
        recorded_candidate_reference.get(key) != backend_archive[key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("endpoint screen native reference differs from backend archive")
    candidate_payload_artifact = endpoint_replay.get("candidate_payload_artifact")
    if not isinstance(candidate_payload_artifact, dict):
        raise RuntimeError("endpoint screen lacks a candidate payload artifact")
    candidate_payload_path = Path(str(candidate_payload_artifact.get("path", "")))
    if not candidate_payload_path.is_file():
        raise RuntimeError("endpoint screen candidate payload is missing")
    observed_candidate_payload = artifact(candidate_payload_path)
    if any(
        observed_candidate_payload[key] != candidate_payload_artifact.get(key)
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("endpoint screen candidate payload changed")
    backend_header_bytes = endpoint_identity.get(
        "candidate_reference_archive_header_bytes"
    )
    if not isinstance(backend_header_bytes, int) or backend_header_bytes < 1:
        raise RuntimeError("endpoint screen lacks a valid native archive header size")
    backend_payload = args.backend_archive.read_bytes()[backend_header_bytes:]
    if not (
        observed_candidate_payload["bytes"] == len(backend_payload)
        and observed_candidate_payload["sha256"]
        == hashlib.sha256(backend_payload).hexdigest()
    ):
        raise RuntimeError("exact replay payload differs from native backend payload")
    if not all(
        archive[key] == candidate[key]
        for candidate in (archive_second, backend_archive)
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("wrapper/backend archive identity or determinism failed")
    base_archive = artifact(args.base_archive)
    endpoint_saved = base_archive["bytes"] - archive["bytes"]
    if endpoint_saved != endpoint_replay.get("full", {}).get("saved_bytes"):
        raise RuntimeError("native archive movement differs from endpoint screen")

    blend_economics = blend.get("economics", {})
    compact_trace = artifact(
        Path(blend["artifacts"]["compact_trace_archive"]["path"])
    )
    recorded_compact_trace = blend["artifacts"]["compact_trace_archive"]
    if any(
        compact_trace[key] != recorded_compact_trace[key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("compact 10M archive changed after terminal receipt")
    package_zip = package_artifacts.get("zip_a", {})
    economics = calculate_economics(
        geometry_archive_10m=int(
            blend_economics["geometry_title_archive_bytes_10m"]
        ),
        compact_archive_10m=compact_trace["bytes"],
        compact_package_bytes=int(blend_economics["compact_source_package_bytes"]),
        candidate_package_bytes=int(package_zip["bytes"]),
        endpoint_full_saved_bytes=endpoint_saved,
        endpoint_holdout_rate_bytes_per_1m=float(
            endpoint_replay["holdout_saved_bytes_per_proportional_1m_raw"]
        ),
    )
    proof_complete = bool(economics["full_and_holdout_forecasts_below_target"])
    receipt = {
        "schema": "cmix21_lstm200_fx2lite428_native_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "constructive_counted_native_wrapper_1m_prefix",
        "artifacts": {
            "source_package_receipt": artifact(args.source_package_receipt),
            "blend_terminal_receipt": artifact(args.blend_terminal_receipt),
            "endpoint_screen": artifact(args.endpoint_screen),
            "endpoint_candidate_payload": observed_candidate_payload,
            "wrapper": wrapper,
            "input": input_artifact,
            "base_archive": base_archive,
            "backend_archive": backend_archive,
            "archive": archive,
            "archive_second": archive_second,
            "restored": restored,
            "encode_guard": artifact(args.encode_guard),
            "decode_guard": artifact(args.decode_guard),
            "determinism_guard": artifact(args.determinism_guard),
            "source_package": package_zip,
        },
        "scope": {
            "raw_bytes": input_artifact["bytes"],
            "wrt_rows": endpoint_replay["full"]["rows"],
            "article_order": "original",
        },
        "mechanism": {
            "base": "no-PAQ CMIX21 compact-200",
            "auxiliary": "FX2-lite FXCM endpoint428 plus byte-LSTM and PPMD20M",
            "auxiliary_cmc2_divisor": 4,
            "blend": "deterministic Q16 integer-logit 31:9",
            "endpoint_weight_ppm": EXPECTED_ENDPOINT_WEIGHT_PPM,
            "state_schedule": "both endpoints update continuously before each next prediction",
        },
        "metrics": {
            "base_archive_bytes": base_archive["bytes"],
            "candidate_archive_bytes": archive["bytes"],
            "native_saved_bytes": endpoint_saved,
            "native_saved_bytes_per_1m": endpoint_saved,
            "holdout_shadow_saved_bytes_per_1m": endpoint_replay[
                "holdout_saved_bytes_per_proportional_1m_raw"
            ],
            "max_encode_tree_rss_kib": encode_guard["max_sampled_tree_rss_kib"],
            "max_decode_tree_rss_kib": decode_guard["max_sampled_tree_rss_kib"],
            "max_determinism_tree_rss_kib": determinism_guard[
                "max_sampled_tree_rss_kib"
            ],
            "decimal_10gb_limit_kib": encode_guard[
                "official_decimal_limit_kib"
            ],
        },
        "economics": economics,
        "proof": {
            "native_probability_archive_matches_backend_shadow": True,
            "wrapper_archive_matches_backend_archive": True,
            "roundtrip_ok": True,
            "determinism_ok": True,
            "all_tree_rss_guards_clean": True,
            "source_package_reconstructs_wrapper_proven_program": True,
            "source_package_deterministic": True,
            "opening_prefix_economics_positive": proof_complete,
        },
        "decision": {
            "exact_10m_confirmation_authorized": proof_complete,
            "official_1g_gate_authorized": False,
            "promotion_authorized": False,
            "verdict": (
                "constructive_counted_opening_pass_requires_exact_10m_confirmation"
                if proof_complete
                else "constructive_opening_fails_counted_economics"
            ),
            "next_action": (
                "run the unchanged source-built original-order wrapper at exact 10M, "
                "then require archive transfer, roundtrip, determinism, tree RSS, and "
                "a conservative counted forecast below target"
            ),
        },
        "claim_boundary": (
            "This is constructive, counted, deterministic, roundtrip-verified 1M "
            "prefix evidence. Both score rows are linear forecasts, not a full-corpus "
            "upper bound. A 10.95 percent claim remains forbidden until an exact 1G "
            "archive plus counted program is at most 109,000,000 bytes and roundtrip "
            "passes."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if proof_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
