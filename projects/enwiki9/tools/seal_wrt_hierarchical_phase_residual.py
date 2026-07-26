#!/usr/bin/env python3
"""Seal disjoint evidence for the hierarchical WRT phase residual endpoint."""

from __future__ import annotations

import argparse
import gzip
import json
import lzma
from pathlib import Path
from typing import Any

from seal_wrt_hashed_residual_online import artifact, load_json, sha256


FROZEN_VARIANT = "p256_s250000_log128"
TARGET_BYTES = 108_000_000
CANONICAL_FORECAST_BYTES = 109_557_404
TARGET_DEBT_BYTES = CANONICAL_FORECAST_BYTES - TARGET_BYTES


def selected_row(receipt: dict[str, Any], path: Path) -> dict[str, Any]:
    rows = [row for row in receipt.get("variants", []) if row.get("variant_id") == FROZEN_VARIANT]
    if len(rows) != 1:
        raise ValueError(f"expected one frozen row in {path}")
    return rows[0]


def seal_window(
    root: Path,
    *,
    phase: str,
    offset: int,
    core_path: Path,
    trace_dir: Path,
    trace_receipt_path: Path | None = None,
) -> dict[str, Any]:
    core = load_json(core_path)
    row = selected_row(core, core_path)
    if phase == "selection" and core.get("best_variant_id") != FROZEN_VARIANT:
        raise ValueError("selection receipt does not select the frozen variant")
    exact_saved = int(row["exact_saved_bytes"])
    artifacts = {
        "raw_input": artifact(root, trace_dir / "input.raw"),
        "probability_trace": artifact(root, trace_dir / "probability.trace"),
        "wrt_store": artifact(root, trace_dir / "input.wrt.store"),
        "baseline_archive": artifact(root, trace_dir / "baseline.cmix"),
        "compression_guard": artifact(root, trace_dir / "compression.guard.json"),
        "core_receipt": artifact(root, core_path),
    }
    if trace_receipt_path is not None:
        artifacts["trace_receipt"] = artifact(root, trace_receipt_path)
    return {
        "phase": phase,
        "offset": offset,
        "scope_bytes": 500_000,
        "selection_applied": phase == "selection",
        "locally_best_variant_id": core.get("best_variant_id"),
        "frozen_variant": {
            "variant_id": FROZEN_VARIANT,
            "prior": row["prior"],
            "strength_ppm": row["strength_ppm"],
            "state_bytes": row["state_bytes"],
            "train_qbits": row["train_qbits"],
            "development_qbits": row["development_qbits"],
            "holdout_qbits": row["holdout_qbits"],
            "exact_saved_bytes": exact_saved,
            "exact_saved_bytes_per_million": exact_saved * 2.0,
            "baseline_payload_bytes": core["baseline_payload_bytes"],
            "candidate_payload_bytes": row["candidate_payload_bytes"],
            "positive_blocks": row["positive_blocks"],
            "regressing_blocks": row["regressing_blocks"],
            "block_qbits": row["block_qbits"],
        },
        "artifacts": artifacts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--endpoint-overlay", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def overlay_artifact(path: Path, logical_name: str) -> dict[str, Any]:
    return {
        "logical_name": logical_name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "availability": "local_nonproof_overlay_not_in_git",
    }


def main() -> int:
    args = parse_args()
    root = (args.repo_root or Path(__file__).resolve().parents[3]).resolve()
    base = root / "projects/enwiki9/results/fx2_reference_residual_v1"
    random_base = (
        root
        / "projects/enwiki9/results/random_window_novelty_v1/"
        "wrt_title_token_automaton_v1"
    )
    source_path = root / "projects/enwiki9/tools/wrt_hierarchical_phase_residual_screen.cpp"
    source = source_path.read_bytes()
    windows = [
        seal_window(
            root,
            phase="selection",
            offset=306_000_000,
            core_path=base / "wrt-hierarchical-phase-residual-selection-500000-306000000.json",
            trace_dir=base / "trace/reference-dense-500000-0",
        ),
        seal_window(
            root,
            phase="confirmation",
            offset=205_537_142,
            core_path=base / "wrt-hierarchical-phase-residual-confirmation-500000-205537142.json",
            trace_dir=random_base / "selection-500000-0",
            trace_receipt_path=random_base / "selection-500000-0.json",
        ),
        seal_window(
            root,
            phase="confirmation",
            offset=367_974_158,
            core_path=base / "wrt-hierarchical-phase-residual-confirmation-500000-367974158.json",
            trace_dir=random_base / "selection-500000-1",
            trace_receipt_path=random_base / "selection-500000-1.json",
        ),
    ]
    rates = [window["frozen_variant"]["exact_saved_bytes_per_million"] for window in windows]
    gzip_bytes = len(gzip.compress(source, compresslevel=9, mtime=0))
    xz_bytes = len(lzma.compress(source, format=lzma.FORMAT_XZ, preset=9))
    conservative_gross = int(min(rates) * 1000)
    conservative_margin = conservative_gross - TARGET_DEBT_BYTES - gzip_bytes
    counterfactual_score = CANONICAL_FORECAST_BYTES - conservative_gross + gzip_bytes
    if args.endpoint_overlay is None:
        raise ValueError("--endpoint-overlay is required for the target-substrate decision")
    overlay = args.endpoint_overlay.resolve()
    endpoint_core_path = base / "wrt-hierarchical-phase-residual-endpoint428-1000000.json"
    layer_core_path = base / "wrt-hierarchical-phase-residual-layer0mixer10-1000000.json"
    endpoint_core = load_json(endpoint_core_path)
    layer_core = load_json(layer_core_path)
    endpoint_row = selected_row(endpoint_core, endpoint_core_path)
    layer_row = selected_row(layer_core, layer_core_path)
    layer_receipt_path = overlay / "layer0_mixer10_over_endpoint428_nativeq16_v1.json"
    layer_receipt = load_json(layer_receipt_path)
    native_component_path = base / "wrt-phase-residual-native-component.json"
    native_component = load_json(native_component_path)
    layer_gain = int(layer_receipt["exact_replay"]["full"]["saved_bytes"])
    layer_required_bpm = float(layer_receipt["economics"]["required_incremental_bytes_per_1m"])
    layer_program_allowance = round((layer_required_bpm - TARGET_DEBT_BYTES / 1000) * 1000)
    hierarchy_endpoint_gain = int(endpoint_row["exact_saved_bytes"])
    hierarchy_layer_gain = int(layer_row["exact_saved_bytes"])
    if int(native_component["exact_replay"]["saved_bytes"]) != hierarchy_layer_gain:
        raise ValueError("native component replay differs from hierarchy screen")
    hierarchy_component_cost = int(
        native_component["sources"]["component_concatenated_gzip9_bytes"]
    )
    composite_gain = layer_gain + hierarchy_layer_gain
    composite_program_ceiling = layer_program_allowance + hierarchy_component_cost
    composite_score = CANONICAL_FORECAST_BYTES - composite_gain * 1000 + composite_program_ceiling
    target_substrate = {
        "endpoint428": {
            "locally_best_variant_id": endpoint_core["best_variant_id"],
            "frozen_incremental_exact_saved_bytes": hierarchy_endpoint_gain,
            "frozen_incremental_exact_saved_bytes_per_million": float(hierarchy_endpoint_gain),
            "positive_blocks": endpoint_row["positive_blocks"],
            "regressing_blocks": endpoint_row["regressing_blocks"],
            "block_qbits": endpoint_row["block_qbits"],
            "decision": "retire hierarchy directly over endpoint428; gain misses debt before code",
            "artifacts": {
                "endpoint_trace": overlay_artifact(overlay / "endpoint428.fx2pt", "endpoint428.fx2pt"),
                "wrt_store": overlay_artifact(overlay / "input.wrt.store", "input.wrt.store"),
                "trace_receipt": overlay_artifact(overlay / "trace_receipt.json", "trace_receipt.json"),
                "substrate_receipt": overlay_artifact(overlay / "substrate_receipt.json", "substrate_receipt.json"),
                "screen_receipt": artifact(root, endpoint_core_path),
            },
        },
        "layer0_composite": {
            "locally_best_variant_id": layer_core["best_variant_id"],
            "frozen_hierarchy_incremental_exact_saved_bytes": hierarchy_layer_gain,
            "layer0_existing_exact_saved_bytes": layer_gain,
            "combined_exact_saved_bytes_per_million": float(composite_gain),
            "positive_blocks": layer_row["positive_blocks"],
            "regressing_blocks": layer_row["regressing_blocks"],
            "block_qbits": layer_row["block_qbits"],
            "layer0_program_allowance_bytes": layer_program_allowance,
            "hierarchy_component_gzip_bytes": hierarchy_component_cost,
            "counterfactual_full_transfer_score_bytes": composite_score,
            "counterfactual_full_transfer_score_percent": round(
                composite_score / 1_000_000_000 * 100, 7
            ),
            "counterfactual_full_transfer_margin_bytes": TARGET_BYTES - composite_score,
            "counterfactual_is_not_forecast": True,
            "artifacts": {
                "layer0_p1": overlay_artifact(
                    overlay / "layer0_mixer10_over_endpoint428_nativeq16_v1.p1",
                    "layer0_mixer10_over_endpoint428_nativeq16_v1.p1",
                ),
                "layer0_trace": overlay_artifact(
                    overlay / "layer0_mixer10_over_endpoint428_nativeq16_v1.fx2pt",
                    "layer0_mixer10_over_endpoint428_nativeq16_v1.fx2pt",
                ),
                "layer0_trace_receipt": overlay_artifact(
                    overlay / "layer0_mixer10_over_endpoint428_nativeq16_v1_trace_receipt.json",
                    "layer0_mixer10_over_endpoint428_nativeq16_v1_trace_receipt.json",
                ),
                "layer0_receipt": overlay_artifact(
                    layer_receipt_path,
                    "layer0_mixer10_over_endpoint428_nativeq16_v1.json",
                ),
                "screen_receipt": artifact(root, layer_core_path),
                "native_component_receipt": artifact(root, native_component_path),
            },
        },
    }
    receipt = {
        "schema_version": 1,
        "receipt_type": "wrt_hierarchical_phase_residual_target_substrate_decision",
        "evidence_level": "causal_exact_target_substrate_probability_trace_shadow",
        "frozen_variant_id": FROZEN_VARIANT,
        "selection_rule": "maximum development qbits at offset 306000000 only",
        "confirmation_rule": "replay frozen ID and ignore confirmation-local selection",
        "source": {
            **artifact(root, source_path),
            "standalone_gzip9_bytes": gzip_bytes,
            "standalone_xz9_bytes": xz_bytes,
            "source_cost_boundary": "standalone compressed source is a conservative research ceiling, not measured endpoint428 incremental package cost",
        },
        "windows": windows,
        "target_substrate": target_substrate,
        "economics": {
            "hutter_target_bytes": TARGET_BYTES,
            "hutter_target_percent": TARGET_BYTES / 1_000_000_000 * 100,
            "canonical_counted_forecast_bytes": CANONICAL_FORECAST_BYTES,
            "canonical_counted_forecast_percent": CANONICAL_FORECAST_BYTES / 1_000_000_000 * 100,
            "endpoint428_remaining_debt_bytes": TARGET_DEBT_BYTES,
            "observed_min_exact_saved_bytes_per_million": min(rates),
            "observed_max_exact_saved_bytes_per_million": max(rates),
            "conservative_projected_gross_bytes_at_1g": conservative_gross,
            "conservative_projected_margin_after_debt_and_standalone_gzip_bytes": conservative_margin,
            "raw_fx2_counterfactual_full_transfer_score_bytes": counterfactual_score,
            "raw_fx2_counterfactual_full_transfer_score_percent": counterfactual_score / 1_000_000_000 * 100,
            "raw_fx2_counterfactual_full_transfer_margin_bytes": TARGET_BYTES - counterfactual_score,
            "raw_fx2_counterfactual_is_not_forecast": True,
            "endpoint428_exact_saved_bytes_per_million": float(hierarchy_endpoint_gain),
            "endpoint428_unchanged_target_closing_before_code": hierarchy_endpoint_gain > TARGET_DEBT_BYTES / 1000,
            "layer0_composite_exact_saved_bytes_per_million": float(composite_gain),
            "layer0_composite_program_ceiling_bytes": composite_program_ceiling,
            "layer0_composite_counterfactual_score_bytes": composite_score,
            "layer0_composite_counterfactual_score_percent": round(
                composite_score / 1_000_000_000 * 100, 7
            ),
            "layer0_composite_counterfactual_margin_bytes": TARGET_BYTES - composite_score,
            "counterfactual_is_not_forecast": True,
        },
        "decision": "retire hierarchy over endpoint428 alone; promote the layer0-plus-hierarchy composite to exact native-pair transfer",
        "next_action": "replay the frozen hierarchy over the exact native pair/layer0 candidate P1, then integrate only if combined counted economics remain target-closing",
        "claim_boundary": (
            "The layer0 composite is a same-stream arithmetic shadow, not the exact native pair/layer0 candidate. "
            "It does not prove native archive gain, roundtrip, determinism, runtime, or an official full-corpus score."
        ),
        "promotion_authorized": False,
    }
    output = args.output or base / "wrt-hierarchical-phase-residual-target-substrate-decision.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
