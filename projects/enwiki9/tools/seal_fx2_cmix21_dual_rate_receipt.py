#!/usr/bin/env python3
"""Seal the quarantined dual-rate FX2/CMIX21 constructive evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


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


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def clean_guard(
    path: Path, *, require_official_decimal_field: bool = True
) -> dict[str, object]:
    value = load_json(path)
    clean = (
        value.get("status") == "complete"
        and value.get("returncode") == 0
        and value.get("rss_guard_exceeded") is False
        and (
            not require_official_decimal_field
            or value.get("official_decimal_over_limit_kib") == 0
        )
    )
    if not clean:
        raise RuntimeError(f"guard is not a clean pass: {path}")
    return {**artifact(path), **value}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--nonproof-root",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = args.nonproof_root.resolve()
    results = root / "results/fx2_cmix21_dual_rate_v1"
    discovery_dir = results / "fast112_slow44x2phase_geometry_1m"
    plain_dir = results / "plain112x2_o3_geometry_1m"
    source_dir = results / "dual_source_build_geometry_1m"
    source_1k_dir = results / "dual_source_build_original_1k"
    package_root = root / (
        "fx2-cmix21-hybrid-geometry-nopaq-dual-rate-"
        "source-package-build-v1"
    )
    plain_package_root = root / (
        "fx2-cmix21-hybrid-geometry-nopaq-lstm112x2-"
        "source-package-build-v1"
    )
    input_path = root / "results/page_order_inputs_1m/1000000_geometry.raw"
    baseline_path = root / "results/fx2_order_geometry_1m.comp"
    matched_fx2_guard_path = root / "results/fx2_order_geometry_1m_guard.json"
    discovery_archive = discovery_dir / "archive.comp"
    plain_archive = plain_dir / "archive.comp"
    source_archive = source_dir / "archive.comp"
    restored_path = source_dir / "restored.raw"
    source_zip = package_root / (
        "comp9a-decomp9-geometry-nopaq-dual-rate-source.zip"
    )
    plain_source_zip = plain_package_root / (
        "comp9a-decomp9-geometry-nopaq-lstm112x2-source.zip"
    )
    build_a_cmix = package_root / "source-build-a/cmix.bin"
    build_b_cmix = package_root / "source-build-b/cmix.bin"
    build_a_wrapper = package_root / "source-build-a/comp9a-decomp9"
    build_b_wrapper = package_root / "source-build-b/comp9a-decomp9"

    required = [
        input_path,
        baseline_path,
        matched_fx2_guard_path,
        discovery_archive,
        plain_archive,
        source_archive,
        restored_path,
        source_zip,
        plain_source_zip,
        build_a_cmix,
        build_b_cmix,
        build_a_wrapper,
        build_b_wrapper,
        discovery_dir / "receipt.json",
        plain_dir / "receipt.json",
        source_dir / "receipt.json",
        source_dir / "decode_guard.json",
        source_1k_dir / "receipt.json",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing dual-rate artifacts: {missing}")

    discovery_receipt = load_json(discovery_dir / "receipt.json")
    plain_receipt = load_json(plain_dir / "receipt.json")
    source_receipt = load_json(source_dir / "receipt.json")
    source_1k_receipt = load_json(source_1k_dir / "receipt.json")
    discovery_guard = clean_guard(discovery_dir / "guard.json")
    plain_guard = clean_guard(plain_dir / "guard.json")
    source_encode_guard = clean_guard(source_dir / "guard.json")
    source_decode_guard = clean_guard(source_dir / "decode_guard.json")
    matched_fx2_guard = clean_guard(
        matched_fx2_guard_path, require_official_decimal_field=False
    )

    checks = {
        "source_archive_matches_discovery": identical(
            source_archive, discovery_archive
        ),
        "source_roundtrip": identical(input_path, restored_path),
        "source_build_cmix_identity": identical(build_a_cmix, build_b_cmix),
        "source_build_wrapper_identity": identical(
            build_a_wrapper, build_b_wrapper
        ),
        "source_codec_1k_matches_discovery": (
            source_1k_receipt.get("reference_identical") is True
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"dual-rate equality check failed: {checks}")

    scope_bytes = input_path.stat().st_size
    if scope_bytes != 1_000_000:
        raise RuntimeError(f"unexpected scope: {scope_bytes}")
    baseline_bytes = baseline_path.stat().st_size
    candidate_bytes = source_archive.stat().st_size
    plain_bytes = plain_archive.stat().st_size
    gross_saved_bytes = baseline_bytes - candidate_bytes
    plain_gross_saved_bytes = baseline_bytes - plain_bytes
    if gross_saved_bytes != 1_019 or plain_gross_saved_bytes != 1_010:
        raise RuntimeError(
            "unexpected matched gains: "
            f"dual={gross_saved_bytes}, plain={plain_gross_saved_bytes}"
        )

    baseline_forecast = 110_181_114
    target_score = 109_500_000
    baseline_program_bytes = 183_008
    option_bytes = 3
    archive_marker_bytes = 1
    counted_program_bytes = source_zip.stat().st_size + option_bytes
    incremental_program_bytes = counted_program_bytes - baseline_program_bytes
    forecast_debt_bytes = baseline_forecast - target_score
    required_gross_bytes = (
        forecast_debt_bytes + incremental_program_bytes + archive_marker_bytes
    )
    projected_gross_saved_bytes = gross_saved_bytes * 1_000
    projected_score = (
        baseline_forecast
        - projected_gross_saved_bytes
        + incremental_program_bytes
        + archive_marker_bytes
    )
    phase_source_cost_bytes = (
        source_zip.stat().st_size - plain_source_zip.stat().st_size
    )
    phase_projected_gross_bytes = (
        gross_saved_bytes - plain_gross_saved_bytes
    ) * 1_000
    phase_projected_net_bytes = (
        phase_projected_gross_bytes - phase_source_cost_bytes
    )
    fx2_elapsed = float(matched_fx2_guard["elapsed_s"])

    receipt = {
        "schema": "fx2_cmix21_dual_rate_constructive_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": (
            "exact_guarded_1m_source_codec_roundtrip_determinism_"
            "and_counted_source_package_nonproof"
        ),
        "scope_raw_bytes": scope_bytes,
        "algorithm": (
            "FX2 geometry/WRT plus PAQ-free CMIX21 with a full-rate 112x2 "
            "online LSTM and two alternating decoder-replayed 44x2 LSTMs"
        ),
        "checks": checks,
        "input": artifact(input_path),
        "baseline_archive": artifact(baseline_path),
        "candidate": {
            "discovery_archive": artifact(discovery_archive),
            "source_archive": artifact(source_archive),
            "restored": artifact(restored_path),
            "gross_saved_bytes": gross_saved_bytes,
            "gross_saved_bytes_per_1m": float(gross_saved_bytes),
            "roundtrip_ok": checks["source_roundtrip"],
            "determinism_ok": checks["source_archive_matches_discovery"],
            "guards": {
                "discovery_encode": discovery_guard,
                "source_encode": source_encode_guard,
                "source_decode": source_decode_guard,
            },
            "peak_single_process_rss_kib": max(
                int(discovery_guard["max_sampled_single_rss_kib"]),
                int(source_encode_guard["max_sampled_single_rss_kib"]),
                int(source_decode_guard["max_sampled_single_rss_kib"]),
            ),
        },
        "plain_112x2_control": {
            "archive": artifact(plain_archive),
            "gross_saved_bytes": plain_gross_saved_bytes,
            "guard": plain_guard,
        },
        "phase_increment": {
            "gross_saved_bytes_per_1m": (
                gross_saved_bytes - plain_gross_saved_bytes
            ),
            "projected_gross_bytes_at_1g": phase_projected_gross_bytes,
            "additional_source_bytes": phase_source_cost_bytes,
            "projected_net_bytes_at_1g_before_runtime": (
                phase_projected_net_bytes
            ),
        },
        "source_package": {
            "archive": artifact(source_zip),
            "option_bytes": option_bytes,
            "counted_program_bytes": counted_program_bytes,
            "build_a_cmix": artifact(build_a_cmix),
            "build_b_cmix": artifact(build_b_cmix),
            "build_a_wrapper": artifact(build_a_wrapper),
            "build_b_wrapper": artifact(build_b_wrapper),
            "clean_build_identity_ok": (
                checks["source_build_cmix_identity"]
                and checks["source_build_wrapper_identity"]
            ),
            "source_codec_1k_matches_discovery": checks[
                "source_codec_1k_matches_discovery"
            ],
            "wrapper_replay_complete": False,
        },
        "runtime_screen": {
            "matched_fx2_guard": matched_fx2_guard,
            "source_encode_ratio_to_matched_fx2": (
                float(source_encode_guard["elapsed_s"]) / fx2_elapsed
            ),
            "source_decode_ratio_to_matched_fx2_encode": (
                float(source_decode_guard["elapsed_s"]) / fx2_elapsed
            ),
            "verdict": "portable_o3_fails_local_runtime_screen",
        },
        "program_adjusted_linear_forecast": {
            "baseline_forecast_score_bytes": baseline_forecast,
            "target_score_bytes": target_score,
            "forecast_debt_bytes": forecast_debt_bytes,
            "baseline_program_bytes": baseline_program_bytes,
            "counted_candidate_program_bytes": counted_program_bytes,
            "incremental_program_bytes": incremental_program_bytes,
            "archive_marker_bytes": archive_marker_bytes,
            "required_gross_bytes_at_1g": required_gross_bytes,
            "required_gross_bytes_per_1m": required_gross_bytes / 1_000,
            "observed_gross_bytes_per_1m": float(gross_saved_bytes),
            "linear_projected_gross_saved_bytes_at_1g": (
                projected_gross_saved_bytes
            ),
            "linear_projected_score_bytes": projected_score,
            "linear_projected_target_margin_bytes": target_score - projected_score,
            "clears_program_adjusted_linear_forecast": (
                projected_score <= target_score
            ),
        },
        "source_receipts": {
            "discovery": artifact(discovery_dir / "receipt.json"),
            "plain_control": artifact(plain_dir / "receipt.json"),
            "source_replay": artifact(source_dir / "receipt.json"),
            "source_codec_1k": artifact(source_1k_dir / "receipt.json"),
        },
        "promotion_authorized": False,
        "claim_boundary": (
            "Exact first-1M codec archive, source-build identity, archive "
            "identity across independent builds, roundtrip, RSS, and counted "
            "linear forecast only. The portable O3 build fails the local "
            "runtime screen. Source-wrapper replay, native-build equivalence, "
            "larger-scope scaling, official accounting, and a constructive 1G "
            "score remain unproven."
        ),
    }

    output = args.output or (
        root / "results/fx2_cmix21_dual_rate_constructive_v1/receipt.json"
    )
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, output)
    print(output)
    print(
        json.dumps(
            {
                "archive_bytes": candidate_bytes,
                "gross_saved_bytes_per_1m": gross_saved_bytes,
                "required_gross_bytes_per_1m": required_gross_bytes / 1_000,
                "linear_projected_score_bytes": projected_score,
                "linear_projected_target_margin_bytes": (
                    target_score - projected_score
                ),
                "phase_projected_net_bytes_at_1g_before_runtime": (
                    phase_projected_net_bytes
                ),
                "roundtrip_ok": checks["source_roundtrip"],
                "determinism_ok": checks["source_archive_matches_discovery"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
