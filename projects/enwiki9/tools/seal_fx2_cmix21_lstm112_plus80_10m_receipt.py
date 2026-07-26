#!/usr/bin/env python3
"""Seal the heterogeneous 112+80 cumulative-10M economics screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASELINE_FORECAST_BYTES = 110_181_114
TARGET_SCORE_BYTES = 109_000_000
BASELINE_PROGRAM_BYTES = 183_008
OPTION_BYTES = 3
ARCHIVE_MARKER_BYTES = 1
EXPECTED_SCOPE_BYTES = 10_000_000
EXPECTED_INPUT_SHA256 = (
    "fa8ec8a64e0e623796af5a6a11e789529680a6b1c4c43c87a97f726c3fbd87cf"
)
EXPECTED_ORIGINAL_SHA256 = (
    "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97"
)
EXPECTED_GEOMETRY_SHA256 = (
    "ec564c15bc818b9b66c21eb445d393ade95fb2934816139fea56b99a639216be"
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


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return value


def require_artifact(entry: dict[str, Any]) -> dict[str, Any]:
    observed = artifact(Path(entry["path"]))
    for key in ("bytes", "sha256"):
        if observed[key] != entry[key]:
            raise RuntimeError(
                f"artifact {key} mismatch for {observed['path']}: "
                f"{observed[key]} != {entry[key]}"
            )
    return observed


def calculate_accounting(
    source_zip_bytes: int, baseline_archive_bytes: int, candidate_archive_bytes: int
) -> dict[str, int | float]:
    candidate_program_bytes = source_zip_bytes + OPTION_BYTES
    incremental_program_bytes = candidate_program_bytes - BASELINE_PROGRAM_BYTES
    forecast_debt_bytes = BASELINE_FORECAST_BYTES - TARGET_SCORE_BYTES
    required_gross_1g_bytes = (
        forecast_debt_bytes + incremental_program_bytes + ARCHIVE_MARKER_BYTES
    )
    required_10m_gain_bytes = math.ceil(required_gross_1g_bytes / 100)
    archive_ceiling_bytes = baseline_archive_bytes - required_10m_gain_bytes
    gross_gain_bytes = baseline_archive_bytes - candidate_archive_bytes
    gross_rate = gross_gain_bytes / 10
    required_rate = required_gross_1g_bytes / 1000
    projected_score_bytes = (
        BASELINE_FORECAST_BYTES
        - gross_gain_bytes * 100
        + incremental_program_bytes
        + ARCHIVE_MARKER_BYTES
    )
    return {
        "candidate_program_bytes": candidate_program_bytes,
        "incremental_program_bytes": incremental_program_bytes,
        "forecast_debt_bytes": forecast_debt_bytes,
        "required_gross_1g_bytes": required_gross_1g_bytes,
        "required_10m_gain_bytes": required_10m_gain_bytes,
        "archive_ceiling_bytes": archive_ceiling_bytes,
        "gross_gain_bytes": gross_gain_bytes,
        "gross_rate": gross_rate,
        "required_rate": required_rate,
        "margin_bytes": archive_ceiling_bytes - candidate_archive_bytes,
        "projected_score_bytes": projected_score_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    root = Path(
        "/home/x/enwiki9-nonproof/"
        "fx2-cmix21-hybrid-geometry-title-nopaq-lstm112x2-plus80x2-"
        "native-source-package-build-v1"
    )
    parser.add_argument(
        "--screen-receipt",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "fx2_cmix21_recurrent_ensemble_10m_v1/"
            "nopaq_lstm112x2_plus80x2_native_source_geometry_title_10m/"
            "receipt.json"
        ),
    )
    parser.add_argument(
        "--source-zip",
        type=Path,
        default=root
        / "comp9a-decomp9-geometry-title-nopaq-lstm112x2-plus80x2-native-source.zip",
    )
    parser.add_argument(
        "--source-tar-xz",
        type=Path,
        default=root
        / "comp9a-decomp9-geometry-title-nopaq-lstm112x2-plus80x2-native-source.tar.xz",
    )
    parser.add_argument(
        "--source-bzip2-zip",
        type=Path,
        default=root
        / "comp9a-decomp9-geometry-title-nopaq-lstm112x2-plus80x2-native-source-bzip2.zip",
    )
    parser.add_argument("--source-binary", type=Path, default=root / "source-build-a/cmix.bin")
    parser.add_argument(
        "--bzip2-source-binary",
        type=Path,
        default=root / "source-build-bzip2-a/cmix.bin",
    )
    parser.add_argument(
        "--bzip2-source-program",
        type=Path,
        default=root / "source-build-bzip2-a/comp9a-decomp9",
    )
    parser.add_argument("--geometry", type=Path, default=root / "stage/geometry.py")
    parser.add_argument(
        "--transformed-proof",
        type=Path,
        default=root / "transform-proof-10m/10000000_geometry_title.raw",
    )
    parser.add_argument(
        "--restored-proof",
        type=Path,
        default=root / "transform-proof-10m/10000000_restored.raw",
    )
    parser.add_argument(
        "--marker", type=Path, default=root / "transform-proof-10m/marker.bin"
    )
    parser.add_argument(
        "--native112-receipt",
        type=Path,
        default=Path(
            "projects/enwiki9/results/fx2_cmix21_lstm112_native_10m_v1/receipt.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "projects/enwiki9/results/"
            "fx2_cmix21_lstm112_plus80_native_10m_v1/receipt.json"
        ),
    )
    args = parser.parse_args()

    source = load_object(args.screen_receipt)
    native112 = load_object(args.native112_receipt)
    if source.get("scope_raw_bytes") != EXPECTED_SCOPE_BYTES:
        raise RuntimeError("screen does not cover exact cumulative 10M")
    if source.get("clean_guard") is not True:
        raise RuntimeError("screen is not a clean guarded encode")
    if source.get("promotion_authorized") is not False:
        raise RuntimeError("discovery receipt unexpectedly authorizes promotion")

    archive = require_artifact(source["archive"])
    baseline = require_artifact(source["baseline"]["artifact"])
    input_artifact = require_artifact(source["input"])
    binary = require_artifact(source["binary"])
    dictionary = require_artifact(source["dictionary"])
    guard = require_artifact(source["guard"])
    if input_artifact["sha256"] != EXPECTED_INPUT_SHA256:
        raise RuntimeError("screen used the wrong geometry-title input")
    if source["guard"].get("status") != "complete":
        raise RuntimeError("RSS guard is not terminal")
    if source["guard"].get("returncode") != 0:
        raise RuntimeError("codec did not exit cleanly")
    if source["guard"].get("rss_guard_exceeded") is not False:
        raise RuntimeError("binary 10GiB RSS guard was exceeded")
    if source["guard"].get("official_decimal_over_limit_kib") != 0:
        raise RuntimeError("decimal 10GB RSS boundary was exceeded")

    source_zip = artifact(args.source_zip)
    source_tar_xz = artifact(args.source_tar_xz)
    source_bzip2_zip = artifact(args.source_bzip2_zip)
    source_binary = artifact(args.source_binary)
    bzip2_source_binary = (
        artifact(args.bzip2_source_binary)
        if args.bzip2_source_binary.is_file()
        else None
    )
    bzip2_source_program = (
        artifact(args.bzip2_source_program)
        if args.bzip2_source_program.is_file()
        else None
    )
    geometry = artifact(args.geometry)
    transformed = artifact(args.transformed_proof)
    restored = artifact(args.restored_proof)
    marker = artifact(args.marker)
    if source_binary["sha256"] != binary["sha256"]:
        raise RuntimeError("screen binary differs from the clean source build")
    bzip2_clean_build_identity = (
        bzip2_source_binary is not None
        and bzip2_source_program is not None
        and bzip2_source_binary["sha256"] == binary["sha256"]
    )
    if geometry["sha256"] != EXPECTED_GEOMETRY_SHA256:
        raise RuntimeError("geometry-title transform identity changed")
    if transformed["sha256"] != EXPECTED_INPUT_SHA256:
        raise RuntimeError("forward transform does not reproduce the screened stream")
    if restored["sha256"] != EXPECTED_ORIGINAL_SHA256:
        raise RuntimeError("inverse transform does not reproduce the original prefix")
    if args.marker.read_bytes() != b"G":
        raise RuntimeError("geometry-title transform did not emit the G marker")

    accounting = calculate_accounting(
        source_zip["bytes"], baseline["bytes"], archive["bytes"]
    )
    tar_xz_accounting = calculate_accounting(
        source_tar_xz["bytes"], baseline["bytes"], archive["bytes"]
    )
    bzip2_zip_accounting = calculate_accounting(
        source_bzip2_zip["bytes"], baseline["bytes"], archive["bytes"]
    )
    candidate_program_bytes = accounting["candidate_program_bytes"]
    incremental_program_bytes = accounting["incremental_program_bytes"]
    forecast_debt_bytes = accounting["forecast_debt_bytes"]
    required_gross_1g_bytes = accounting["required_gross_1g_bytes"]
    required_10m_gain_bytes = accounting["required_10m_gain_bytes"]
    archive_ceiling_bytes = accounting["archive_ceiling_bytes"]
    gross_gain_bytes = accounting["gross_gain_bytes"]
    gross_rate = accounting["gross_rate"]
    required_rate = accounting["required_rate"]
    margin_bytes = accounting["margin_bytes"]
    projected_score_bytes = accounting["projected_score_bytes"]
    native112_archive = native112["result"]["candidate_archive_bytes"]
    passed = margin_bytes >= 0
    bzip2_zip_passed = bzip2_zip_accounting["margin_bytes"] >= 0
    tar_xz_passed = tar_xz_accounting["margin_bytes"] >= 0
    if bzip2_zip_passed and bzip2_clean_build_identity:
        selected_source_artifact_key = "source_bzip2_zip"
        verdict = "advance_exact_wrapper_proof"
    elif passed:
        selected_source_artifact_key = "source_zip"
        verdict = "advance_exact_wrapper_proof"
    elif bzip2_zip_passed:
        selected_source_artifact_key = None
        verdict = "advance_bzip2_zip_build_and_accounting_proof"
    elif tar_xz_passed:
        selected_source_artifact_key = None
        verdict = "advance_tar_xz_build_and_accounting_proof"
    else:
        selected_source_artifact_key = None
        verdict = "retire_heterogeneous_112_plus80_unchanged_archive_screen_miss"
    wrapper_proof_authorized = selected_source_artifact_key is not None
    selected_accounting = (
        bzip2_zip_accounting
        if selected_source_artifact_key == "source_bzip2_zip"
        else accounting
    )

    receipt = {
        "schema": "fx2_cmix21_lstm112_plus80_native_10m_terminal_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "algorithm": (
            "geometry-title FX2/WRT plus PAQ-free FXCM/PPMD and continuously "
            "updated native 112x2 and 80x2 byte-LSTM endpoints"
        ),
        "evidence_level": "exact_guarded_10m_backend_archive_screen",
        "scope_raw_bytes": EXPECTED_SCOPE_BYTES,
        "artifacts": {
            "source_screen_receipt": artifact(args.screen_receipt),
            "guard": guard,
            "input": input_artifact,
            "baseline_archive": baseline,
            "candidate_archive": archive,
            "backend_binary": binary,
            "clean_source_binary": source_binary,
            "bzip2_clean_source_binary": bzip2_source_binary,
            "bzip2_clean_source_program": bzip2_source_program,
            "dictionary": dictionary,
            "source_zip": source_zip,
            "source_tar_xz": source_tar_xz,
            "source_bzip2_zip": source_bzip2_zip,
            "geometry_title_transform": geometry,
            "forward_transform_proof": transformed,
            "inverse_transform_proof": restored,
            "transform_marker": marker,
            "native112_receipt": artifact(args.native112_receipt),
        },
        "resources": {
            "max_sampled_single_rss_kib": source["guard"][
                "max_sampled_single_rss_kib"
            ],
            "max_sampled_tree_rss_kib": source["guard"][
                "max_sampled_tree_rss_kib"
            ],
            "official_decimal_over_limit_kib": 0,
            "rss_guard_exceeded": False,
        },
        "accounting": {
            "baseline_forecast_bytes": BASELINE_FORECAST_BYTES,
            "target_score_bytes": TARGET_SCORE_BYTES,
            "forecast_debt_bytes": forecast_debt_bytes,
            "baseline_program_bytes": BASELINE_PROGRAM_BYTES,
            "source_zip_bytes": source_zip["bytes"],
            "option_bytes": OPTION_BYTES,
            "candidate_program_bytes": candidate_program_bytes,
            "archive_marker_bytes": ARCHIVE_MARKER_BYTES,
            "incremental_program_bytes": incremental_program_bytes,
            "required_gross_1g_bytes": required_gross_1g_bytes,
            "required_gross_bytes_per_1m": required_rate,
            "required_10m_gain_bytes": required_10m_gain_bytes,
            "archive_ceiling_bytes": archive_ceiling_bytes,
            "selected_source_artifact_key": selected_source_artifact_key,
            "selected_representation": {
                "candidate_program_bytes": selected_accounting[
                    "candidate_program_bytes"
                ],
                "incremental_program_bytes": selected_accounting[
                    "incremental_program_bytes"
                ],
                "required_gross_1g_bytes": selected_accounting[
                    "required_gross_1g_bytes"
                ],
                "required_gross_bytes_per_1m": selected_accounting[
                    "required_rate"
                ],
                "required_10m_gain_bytes": selected_accounting[
                    "required_10m_gain_bytes"
                ],
                "archive_ceiling_bytes": selected_accounting[
                    "archive_ceiling_bytes"
                ],
            },
            "tar_xz_representation": {
                "source_archive_bytes": source_tar_xz["bytes"],
                "candidate_program_bytes": tar_xz_accounting[
                    "candidate_program_bytes"
                ],
                "incremental_program_bytes": tar_xz_accounting[
                    "incremental_program_bytes"
                ],
                "required_gross_1g_bytes": tar_xz_accounting[
                    "required_gross_1g_bytes"
                ],
                "required_gross_bytes_per_1m": tar_xz_accounting[
                    "required_rate"
                ],
                "required_10m_gain_bytes": tar_xz_accounting[
                    "required_10m_gain_bytes"
                ],
                "archive_ceiling_bytes": tar_xz_accounting[
                    "archive_ceiling_bytes"
                ],
                "archive_ceiling_margin_bytes": tar_xz_accounting[
                    "margin_bytes"
                ],
            },
            "bzip2_zip_representation": {
                "source_archive_bytes": source_bzip2_zip["bytes"],
                "candidate_program_bytes": bzip2_zip_accounting[
                    "candidate_program_bytes"
                ],
                "incremental_program_bytes": bzip2_zip_accounting[
                    "incremental_program_bytes"
                ],
                "required_gross_1g_bytes": bzip2_zip_accounting[
                    "required_gross_1g_bytes"
                ],
                "required_gross_bytes_per_1m": bzip2_zip_accounting[
                    "required_rate"
                ],
                "required_10m_gain_bytes": bzip2_zip_accounting[
                    "required_10m_gain_bytes"
                ],
                "archive_ceiling_bytes": bzip2_zip_accounting[
                    "archive_ceiling_bytes"
                ],
                "archive_ceiling_margin_bytes": bzip2_zip_accounting[
                    "margin_bytes"
                ],
            },
        },
        "result": {
            "candidate_archive_bytes": archive["bytes"],
            "gross_saved_bytes": gross_gain_bytes,
            "gross_saved_bytes_per_1m": gross_rate,
            "archive_ceiling_margin_bytes": selected_accounting["margin_bytes"],
            "headroom_bytes_per_1m": (
                gross_rate - selected_accounting["required_rate"]
            ),
            "projected_score_bytes": selected_accounting[
                "projected_score_bytes"
            ],
            "projected_target_margin_bytes": (
                TARGET_SCORE_BYTES - selected_accounting["projected_score_bytes"]
            ),
            "deflate_zip_archive_ceiling_margin_bytes": margin_bytes,
            "deflate_zip_projected_score_bytes": projected_score_bytes,
            "native112_archive_bytes": native112_archive,
            "improvement_over_native112_bytes": native112_archive - archive["bytes"],
            "verdict": verdict,
            "promotion_authorized": False,
            "wrapper_proof_authorized": wrapper_proof_authorized,
            "selected_source_artifact_key": selected_source_artifact_key,
            "bzip2_clean_build_identity": bzip2_clean_build_identity,
            "bzip2_zip_build_proof_authorized": (
                bzip2_zip_passed and not bzip2_clean_build_identity
            ),
            "tar_xz_build_proof_authorized": (
                not wrapper_proof_authorized and tar_xz_passed
            ),
            "larger_gate_authorized": False,
        },
        "next_action": (
            "prove exact wrapper archive identity, roundtrip, and deterministic replay"
            if wrapper_proof_authorized
            else (
                "prove bzip2 ZIP clean-build equivalence and source-package accounting"
                if bzip2_zip_passed
                else (
                    "obtain committee acceptance, then prove tar.xz clean-build equivalence"
                    if tar_xz_passed
                    else "construct a stronger continuously replayable endpoint universe"
                )
            )
        ),
        "claim_boundary": (
            "Exact clean 10M backend archive, source-build identity, transform, and "
            "RSS evidence. A pass authorizes package proof only; it is not a full-"
            "corpus score or 10.95 percent claim."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(args.output.resolve())
    print(
        json.dumps(
            {
                "archive_bytes": archive["bytes"],
                "archive_ceiling_bytes": selected_accounting[
                    "archive_ceiling_bytes"
                ],
                "archive_ceiling_margin_bytes": selected_accounting[
                    "margin_bytes"
                ],
                "gross_saved_bytes_per_1m": gross_rate,
                "tar_xz_archive_ceiling_bytes": tar_xz_accounting[
                    "archive_ceiling_bytes"
                ],
                "tar_xz_archive_ceiling_margin_bytes": tar_xz_accounting[
                    "margin_bytes"
                ],
                "bzip2_zip_archive_ceiling_bytes": bzip2_zip_accounting[
                    "archive_ceiling_bytes"
                ],
                "bzip2_zip_archive_ceiling_margin_bytes": bzip2_zip_accounting[
                    "margin_bytes"
                ],
                "verdict": verdict,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
