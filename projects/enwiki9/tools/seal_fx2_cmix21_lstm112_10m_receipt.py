#!/usr/bin/env python3
"""Seal the terminal native-112 cumulative-10M economics screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASELINE_FORECAST_BYTES = 110_181_114
TARGET_SCORE_BYTES = 108_000_000
BASELINE_PROGRAM_BYTES = 183_008
OPTION_BYTES = 3
ARCHIVE_MARKER_BYTES = 1
GEOMETRY_TITLE_PATCH_BYTES_ESTIMATE = 4
EXPECTED_SCOPE_BYTES = 10_000_000
EXPECTED_INPUT_SHA256 = (
    "fa8ec8a64e0e623796af5a6a11e789529680a6b1c4c43c87a97f726c3fbd87cf"
)
EXPECTED_GEOMETRY_ONLY_SHA256 = (
    "defaeeab1779ab076f96f9d092fa732681b37fe7eab299e1f9a6ff22fb4620c1"
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--screen-receipt",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "fx2_cmix21_runtime_frontier_10m_v1/"
            "nopaq_lstm112x2_native_source_geometry_title_10m/receipt.json"
        ),
    )
    parser.add_argument(
        "--source-zip",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/"
            "fx2-cmix21-hybrid-geometry-nopaq-lstm112x2-native-"
            "source-package-build-v1/"
            "comp9a-decomp9-geometry-nopaq-lstm112x2-native-source.zip"
        ),
    )
    parser.add_argument(
        "--embedded-geometry",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/"
            "fx2-cmix21-hybrid-geometry-nopaq-lstm112x2-native-"
            "source-package-build-v1/stage/geometry.py"
        ),
    )
    parser.add_argument(
        "--fixed96-screen",
        type=Path,
        default=Path(
            "projects/enwiki9/results/"
            "fx2_cmix21_geometry_nopaq_lstm96x2_constructive_v1/"
            "geometry_title_10m_screen.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "projects/enwiki9/results/"
            "fx2_cmix21_lstm112_native_10m_v1/receipt.json"
        ),
    )
    args = parser.parse_args()

    source = load_object(args.screen_receipt)
    fixed96 = load_object(args.fixed96_screen)
    if source.get("scope_raw_bytes") != EXPECTED_SCOPE_BYTES:
        raise RuntimeError("native-112 receipt does not cover exact cumulative 10M")
    if source.get("clean_guard") is not True:
        raise RuntimeError("native-112 screen is not a clean guarded encode")
    if source.get("promotion_authorized") is not False:
        raise RuntimeError("discovery receipt unexpectedly authorizes promotion")

    archive = require_artifact(source["archive"])
    baseline = require_artifact(source["baseline"]["artifact"])
    input_artifact = require_artifact(source["input"])
    binary = require_artifact(source["binary"])
    dictionary = require_artifact(source["dictionary"])
    guard = require_artifact(source["guard"])
    if input_artifact["sha256"] != EXPECTED_INPUT_SHA256:
        raise RuntimeError("native-112 screen used the wrong geometry-title input")
    if source["guard"].get("status") != "complete":
        raise RuntimeError("RSS guard is not terminal")
    if source["guard"].get("returncode") != 0:
        raise RuntimeError("codec did not exit cleanly")
    if source["guard"].get("rss_guard_exceeded") is not False:
        raise RuntimeError("binary 10GiB RSS guard was exceeded")
    if source["guard"].get("official_decimal_over_limit_kib") != 0:
        raise RuntimeError("decimal 10GB RSS boundary was exceeded")

    source_zip = artifact(args.source_zip)
    geometry = artifact(args.embedded_geometry)
    if geometry["sha256"] != EXPECTED_GEOMETRY_ONLY_SHA256:
        raise RuntimeError("embedded geometry-only transform identity changed")
    if fixed96.get("scope_raw_bytes") != EXPECTED_SCOPE_BYTES:
        raise RuntimeError("fixed-96 comparison is not the cumulative 10M screen")
    fixed96_archive = fixed96["archive"]

    corrected_source_zip_bytes = (
        source_zip["bytes"] + GEOMETRY_TITLE_PATCH_BYTES_ESTIMATE
    )
    incremental_program_bytes = (
        corrected_source_zip_bytes + OPTION_BYTES - BASELINE_PROGRAM_BYTES
    )
    forecast_debt_bytes = BASELINE_FORECAST_BYTES - TARGET_SCORE_BYTES
    required_gross_1g_bytes = (
        forecast_debt_bytes + incremental_program_bytes + ARCHIVE_MARKER_BYTES
    )
    required_10m_gain_bytes = math.ceil(required_gross_1g_bytes / 100)
    archive_ceiling_bytes = baseline["bytes"] - required_10m_gain_bytes
    gross_gain_bytes = baseline["bytes"] - archive["bytes"]
    gross_rate = gross_gain_bytes * 1_000_000 / EXPECTED_SCOPE_BYTES
    required_rate = required_gross_1g_bytes / 1000
    miss_bytes = archive["bytes"] - archive_ceiling_bytes
    projected_score_bytes = (
        BASELINE_FORECAST_BYTES
        - round(gross_rate * 1000)
        + incremental_program_bytes
        + ARCHIVE_MARKER_BYTES
    )
    improvement_over_fixed96 = fixed96_archive["bytes"] - archive["bytes"]

    if gross_gain_bytes != source["baseline"]["gross_saved_bytes"]:
        raise RuntimeError("screen receipt gross gain is internally inconsistent")
    if miss_bytes <= 0:
        raise RuntimeError("this sealer is only for the terminal economics miss")

    receipt = {
        "schema": "fx2_cmix21_lstm112_native_10m_terminal_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "algorithm": (
            "geometry-title FX2/WRT plus PAQ-free FXCM/PPMD and one "
            "continuously updated native 112x2 byte LSTM"
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
            "dictionary": dictionary,
            "provisional_source_zip": source_zip,
            "embedded_geometry_only_transform": geometry,
            "fixed96_screen": artifact(args.fixed96_screen),
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
            "provisional_source_zip_bytes": source_zip["bytes"],
            "geometry_title_patch_bytes_estimate": (
                GEOMETRY_TITLE_PATCH_BYTES_ESTIMATE
            ),
            "corrected_source_zip_bytes_estimate": corrected_source_zip_bytes,
            "option_bytes": OPTION_BYTES,
            "archive_marker_bytes": ARCHIVE_MARKER_BYTES,
            "incremental_program_bytes_estimate": incremental_program_bytes,
            "required_gross_1g_bytes": required_gross_1g_bytes,
            "required_gross_bytes_per_1m": required_rate,
            "required_10m_gain_bytes": required_10m_gain_bytes,
            "archive_ceiling_bytes": archive_ceiling_bytes,
        },
        "result": {
            "candidate_archive_bytes": archive["bytes"],
            "gross_saved_bytes": gross_gain_bytes,
            "gross_saved_bytes_per_1m": gross_rate,
            "archive_ceiling_miss_bytes": miss_bytes,
            "remaining_bytes_per_1m": required_rate - gross_rate,
            "projected_score_bytes": projected_score_bytes,
            "projected_target_miss_bytes": projected_score_bytes
            - TARGET_SCORE_BYTES,
            "fixed96_archive_bytes": fixed96_archive["bytes"],
            "improvement_over_fixed96_bytes": improvement_over_fixed96,
            "improvement_over_fixed96_bytes_per_1m": (
                improvement_over_fixed96 * 1_000_000 / EXPECTED_SCOPE_BYTES
            ),
            "verdict": "retire_fixed112_unchanged_archive_screen_miss",
            "promotion_authorized": False,
            "decode_authorized": False,
            "determinism_replay_authorized": False,
            "larger_gate_authorized": False,
        },
        "proof_blockers": [
            "candidate archive is above the counted cumulative-10M ceiling",
            "embedded wrapper transform is geometry-only, not geometry-title",
            "no exact decode, determinism replay, disjoint confirmation, or 1G score",
        ],
        "next_action": (
            "screen a continuously evolved compact recurrent endpoint set "
            "against the identical geometry-title substrate"
        ),
        "claim_boundary": (
            "Exact clean 10M backend archive and RSS evidence. The result "
            "retires fixed native 112x2 unchanged; it is not a package-level "
            "roundtrip, deterministic replay, full-corpus score, or 10.95% claim."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(args.output.resolve())
    print(
        json.dumps(
            {
                "archive_bytes": archive["bytes"],
                "archive_ceiling_miss_bytes": miss_bytes,
                "gross_saved_bytes_per_1m": gross_rate,
                "remaining_bytes_per_1m": required_rate - gross_rate,
                "verdict": receipt["result"]["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
