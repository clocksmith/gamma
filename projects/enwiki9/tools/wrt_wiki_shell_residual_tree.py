#!/usr/bin/env python3
"""Compile a tiny WRT-shell residual decision tree against exact FX2 p1 rows."""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from typing import Any

import numpy as np
from sklearn.tree import DecisionTreeRegressor

from fx2_shadow_residual_coder import BinaryArithmeticEncoder


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_ROWS = (
    ROOT
    / "results"
    / "wrt_wiki_shell_v1"
    / "trace_1m_v1"
    / "residual_cache.tsv"
)
DEFAULT_OUT = (
    ROOT
    / "results"
    / "wrt_wiki_shell_v1"
    / "residual_tree_1m_v1.json"
)
BASELINE_SCORE = 110_181_114
TARGET_SCORE = 108_000_000
CALIBRATED_10M_TO_1G = 66.95533418670768
FEATURES = (
    "p1",
    "bit_pos",
    "wrt_stream_byte",
    "wrt_token_class",
    "wrt_token_id_low",
    "wrt_token_id_high",
    "wrt_dictionary_hit_type",
    "wrt_literal_phase",
    "wrt_decoded_chars",
    "wrt_page_boundary",
    "wrt_page_mode",
    "wrt_title_mode",
    "wrt_prose_mode",
    "wrt_ref_mode",
    "wrt_url_mode",
    "wrt_table_mode",
    "wrt_list_mode",
    "wrt_template_depth",
    "wrt_number_class",
    "wrt_section_state",
    "wrt_section_level",
    "wrt_title_hash_low",
    "wrt_template_hash_low",
    "wrt_ref_hash_low",
    "wrt_section_hash_low",
    "wrt_reconstructed_phase",
)


def qbits_array(bit: np.ndarray, p1: np.ndarray) -> np.ndarray:
    p = np.clip(p1.astype(np.float64), 1.0, 65535.0)
    probability = np.where(bit != 0, p, 65536.0 - p) / 65536.0
    return np.floor(-np.log2(probability) * 256.0 + 0.5).astype(np.int64)


def feature_row(values: list[str], indexes: dict[str, int]) -> tuple[int, ...]:
    token_id = int(values[indexes["wrt_token_id"]])
    return (
        int(values[indexes["p1"]]),
        int(values[indexes["bit_pos"]]),
        int(values[indexes["wrt_stream_byte"]]),
        int(values[indexes["wrt_token_class"]]),
        token_id & 255,
        (token_id >> 8) & 255,
        int(values[indexes["wrt_dictionary_hit_type"]]),
        int(values[indexes["wrt_literal_phase"]]),
        int(values[indexes["wrt_decoded_chars"]]),
        int(values[indexes["wrt_page_boundary"]]),
        int(values[indexes["wrt_page_mode"]]),
        int(values[indexes["wrt_title_mode"]]),
        int(values[indexes["wrt_prose_mode"]]),
        int(values[indexes["wrt_ref_mode"]]),
        int(values[indexes["wrt_url_mode"]]),
        int(values[indexes["wrt_table_mode"]]),
        int(values[indexes["wrt_list_mode"]]),
        int(values[indexes["wrt_template_depth"]]),
        int(values[indexes["wrt_number_class"]]),
        int(values[indexes["wrt_section_state"]]),
        int(values[indexes["wrt_section_level"]]),
        int(values[indexes["wrt_title_hash"]]) & 255,
        int(values[indexes["wrt_template_hash"]]) & 255,
        int(values[indexes["wrt_ref_hash"]]) & 255,
        int(values[indexes["wrt_section_hash"]]) & 255,
        int(values[indexes["wrt_reconstructed_bytes"]]) & 255,
    )


def load_rows(path: pathlib.Path, expected_rows: int) -> dict[str, np.ndarray]:
    x = np.empty((expected_rows, len(FEATURES)), dtype=np.int32)
    pos = np.empty(expected_rows, dtype=np.int32)
    bit = np.empty(expected_rows, dtype=np.uint8)
    p1 = np.empty(expected_rows, dtype=np.int32)
    baseline_qbits = np.empty(expected_rows, dtype=np.int32)
    with path.open("r", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader)
        required = {
            "pos",
            "bit",
            "baseline_qbits",
            "wrt_token_id",
            "wrt_title_hash",
            "wrt_template_hash",
            "wrt_ref_hash",
            "wrt_section_hash",
            "wrt_reconstructed_bytes",
            "wrt_literal_phase",
            *(name for name in FEATURES if not name.endswith(("_low", "_high", "_phase"))),
        }
        indexes = {name: header.index(name) for name in required}
        rows = 0
        for rows, values in enumerate(reader, start=1):
            index = rows - 1
            if index >= expected_rows:
                raise SystemExit("cache contains more rows than --expected-rows")
            x[index] = feature_row(values, indexes)
            pos[index] = int(values[indexes["pos"]])
            bit[index] = int(values[indexes["bit"]])
            p1[index] = int(values[indexes["p1"]])
            baseline_qbits[index] = int(values[indexes["baseline_qbits"]])
    if rows != expected_rows:
        raise SystemExit(f"expected {expected_rows} rows, loaded {rows}")
    return {
        "x": x,
        "pos": pos,
        "bit": bit,
        "p1": p1,
        "baseline_qbits": baseline_qbits,
    }


def score(
    model: DecisionTreeRegressor,
    rows: dict[str, np.ndarray],
    mask: np.ndarray,
    blend_ppm: int,
) -> dict[str, Any]:
    prediction = np.rint(model.predict(rows["x"][mask])).astype(np.int32)
    base = rows["p1"][mask]
    candidate = np.clip(
        base + np.rint(prediction * (blend_ppm / 1_000_000.0)).astype(np.int32),
        1,
        65535,
    )
    baseline = rows["baseline_qbits"][mask].astype(np.int64)
    candidate_qbits = qbits_array(rows["bit"][mask], candidate)
    gain_qbits = int(np.sum(baseline - candidate_qbits))
    return {
        "rows": int(np.sum(mask)),
        "gain_qbits": gain_qbits,
        "gain_bits": gain_qbits / 256.0,
        "gain_bytes": gain_qbits / 2048.0,
    }


def exact_confirmation(
    model: DecisionTreeRegressor,
    rows: dict[str, np.ndarray],
    mask: np.ndarray,
    blend_ppm: int,
    chunk_rows: int,
) -> dict[str, Any]:
    indexes = np.flatnonzero(mask)
    baseline = BinaryArithmeticEncoder()
    candidate = BinaryArithmeticEncoder()
    for start in range(0, len(indexes), chunk_rows):
        selected = indexes[start : start + chunk_rows]
        correction = np.rint(model.predict(rows["x"][selected])).astype(np.int32)
        base = rows["p1"][selected]
        corrected = np.clip(
            base
            + np.rint(correction * (blend_ppm / 1_000_000.0)).astype(np.int32),
            1,
            65535,
        )
        for actual, base_p1, candidate_p1 in zip(
            rows["bit"][selected], base, corrected, strict=True
        ):
            baseline.encode(int(actual), int(base_p1))
            candidate.encode(int(actual), int(candidate_p1))
    baseline.finish()
    candidate.finish()
    return {
        "rows": len(indexes),
        "baseline_bytes": baseline.byte_count,
        "candidate_bytes": candidate.byte_count,
        "saved_bytes": baseline.byte_count - candidate.byte_count,
        "saved_bits": baseline.bit_count - candidate.bit_count,
    }


def tree_payload(model: DecisionTreeRegressor) -> dict[str, Any]:
    tree = model.tree_
    return {
        "node_count": int(tree.node_count),
        "max_depth": int(tree.max_depth),
        "children_left": tree.children_left.astype(int).tolist(),
        "children_right": tree.children_right.astype(int).tolist(),
        "feature": tree.feature.astype(int).tolist(),
        "threshold": np.rint(tree.threshold).astype(int).tolist(),
        "leaf_correction_p1": np.rint(tree.value[:, 0, 0]).astype(int).tolist(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=pathlib.Path, default=DEFAULT_ROWS)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--expected-rows", type=int, default=4_805_936)
    parser.add_argument("--train-end", type=int, default=200_000)
    parser.add_argument("--selection-end", type=int, default=400_000)
    parser.add_argument("--raw-scope-bytes", type=int, default=1_000_000)
    parser.add_argument("--wrt-scope-bytes", type=int, default=600_742)
    parser.add_argument("--max-train-rows", type=int, default=1_000_000)
    parser.add_argument("--depths", default="6,8,10")
    parser.add_argument("--min-leaf", type=int, default=512)
    parser.add_argument("--blends", default="250000,500000,1000000")
    parser.add_argument("--node-bytes", type=int, default=16)
    parser.add_argument("--base-code-bytes", type=int, default=4096)
    parser.add_argument("--chunk-rows", type=int, default=100_000)
    parser.add_argument("--baseline-score", type=int, default=BASELINE_SCORE)
    parser.add_argument("--target-score", type=int, default=TARGET_SCORE)
    parser.add_argument("--calibrated-scale", type=float, default=CALIBRATED_10M_TO_1G)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    print(
        "[run-contract] run_name=wrt_wiki_shell_residual_tree_v1 "
        f"pairs_input_spec={args.rows} resume_from=none resume_stage=none "
        f"decode=greedy eval_dataset_paths={args.rows} device=cpu "
        "schedule=mixed_from_start runtime_mode=cpu",
        flush=True,
    )
    rows = load_rows(args.rows, args.expected_rows)
    train_mask = rows["pos"] < args.train_end
    selection_mask = (rows["pos"] >= args.train_end) & (
        rows["pos"] < args.selection_end
    )
    confirmation_mask = rows["pos"] >= args.selection_end
    train_indexes = np.flatnonzero(train_mask)
    stride = max(1, math.ceil(len(train_indexes) / args.max_train_rows))
    train_indexes = train_indexes[::stride][: args.max_train_rows]
    train_target = (
        rows["bit"][train_indexes].astype(np.int32) * 65536
        - rows["p1"][train_indexes]
    )
    depths = [int(value) for value in args.depths.split(",") if value]
    blends = [int(value) for value in args.blends.split(",") if value]
    models: list[tuple[DecisionTreeRegressor, dict[str, Any]]] = []
    selection_wrt_bytes = args.selection_end - args.train_end
    selection_raw_bytes = selection_wrt_bytes * args.raw_scope_bytes / args.wrt_scope_bytes
    for depth in depths:
        model = DecisionTreeRegressor(
            max_depth=depth,
            min_samples_leaf=args.min_leaf,
            random_state=923,
        )
        model.fit(rows["x"][train_indexes], train_target)
        node_count = int(model.tree_.node_count)
        program_bytes = args.base_code_bytes + node_count * args.node_bytes
        required_10m = (
            args.baseline_score - args.target_score + program_bytes
        ) / args.calibrated_scale
        for blend in blends:
            selection = score(model, rows, selection_mask, blend)
            projected_10m = selection["gain_bytes"] * 10_000_000 / selection_raw_bytes
            models.append(
                (
                    model,
                    {
                        "model_id": f"depth{depth}_blend{blend}",
                        "depth": depth,
                        "blend_ppm": blend,
                        "node_count": node_count,
                        "program_bytes": program_bytes,
                        "required_10m_gain_bytes": required_10m,
                        "selection": selection,
                        "selection_projected_10m_gain_bytes_non_proof": projected_10m,
                        "selection_margin_bytes_non_proof": projected_10m - required_10m,
                    },
                )
            )
    models.sort(
        key=lambda item: (
            -item[1]["selection_margin_bytes_non_proof"],
            item[1]["program_bytes"],
            item[1]["model_id"],
        )
    )
    winner_model, winner = models[0]
    selection_pass = winner["selection_margin_bytes_non_proof"] > 0
    if selection_pass:
        winner["confirmation_exact"] = exact_confirmation(
            winner_model,
            rows,
            confirmation_mask,
            winner["blend_ppm"],
            args.chunk_rows,
        )
        winner["tree"] = tree_payload(winner_model)
    else:
        winner["confirmation_exact"] = None
        winner["tree"] = None
    payload = {
        "receipt_type": "wrt_wiki_shell_residual_tree",
        "evidence_level": (
            "selection_distilled_confirmation_exact_shadow"
            if selection_pass
            else "selection_teacher_only"
        ),
        "claim_boundary": (
            "The tree is trained only on the first split and ranked only on the "
            "middle split. Confirmation opens only after the calibrated target gate. "
            "This is not a native archive or 10.95% claim."
        ),
        "runtime": {"python": sys.executable, "device": "cpu"},
        "input": str(args.rows),
        "features": list(FEATURES),
        "splits": {
            "train_end_wrt_pos": args.train_end,
            "selection_end_wrt_pos": args.selection_end,
            "confirmation_start_wrt_pos": args.selection_end,
            "training_rows_used": len(train_indexes),
            "training_stride": stride,
            "selection_rows": int(np.sum(selection_mask)),
            "confirmation_rows": int(np.sum(confirmation_mask)),
        },
        "accounting": {
            "node_bytes": args.node_bytes,
            "base_code_bytes": args.base_code_bytes,
            "calibrated_10m_to_1g": args.calibrated_scale,
            "selection_raw_scope_bytes": selection_raw_bytes,
        },
        "candidates": [item for _model, item in models],
        "winner": winner,
        "verdict": (
            "compile_tree_into_native_candidate"
            if selection_pass
            and winner["confirmation_exact"]
            and winner["confirmation_exact"]["saved_bytes"] > winner["program_bytes"]
            else "no_tree_clears_counted_target_gate"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(
            json.dumps(
                {
                    "winner": winner,
                    "verdict": payload["verdict"],
                    "output": str(args.output),
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
