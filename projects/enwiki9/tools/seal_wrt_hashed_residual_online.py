#!/usr/bin/env python3
"""Seal the two-window decision for causal WRT residual SSE."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


FROZEN_VARIANT = "h19_p256_s250000_m201"
TARGET_DEBT_BYTES_PER_MILLION = 57.404


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def artifact(root: Path, path: Path) -> dict[str, Any]:
    return {
        "path": relative(root, path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def frozen_row(receipt: dict[str, Any], path: Path) -> dict[str, Any]:
    if receipt.get("schema_version") != 2:
        raise ValueError(f"unsupported core receipt schema in {path}")
    rows = [row for row in receipt.get("variants", []) if row.get("variant_id") == FROZEN_VARIANT]
    if len(rows) != 1:
        raise ValueError(f"expected one {FROZEN_VARIANT} row in {path}")
    return rows[0]


def window(
    root: Path,
    *,
    phase: str,
    offset: int,
    scope_bytes: int,
    core_path: Path,
    raw_path: Path,
    trace_path: Path,
    store_path: Path,
) -> dict[str, Any]:
    core = load_json(core_path)
    row = frozen_row(core, core_path)
    if phase == "selection" and core.get("best_variant_id") != FROZEN_VARIANT:
        raise ValueError("selection receipt does not select the frozen variant")
    exact_saved = int(row["exact_saved_bytes"])
    return {
        "phase": phase,
        "offset": offset,
        "scope_bytes": scope_bytes,
        "selection_applied": phase == "selection",
        "locally_best_variant_id": core.get("best_variant_id"),
        "frozen_variant": {
            "variant_id": FROZEN_VARIANT,
            "feature_mask": row["feature_mask"],
            "state_bytes": row["state_bytes"],
            "train_qbits": row["train_qbits"],
            "development_qbits": row["development_qbits"],
            "holdout_qbits": row["holdout_qbits"],
            "exact_saved_bytes": exact_saved,
            "exact_saved_bytes_per_million": exact_saved * 1_000_000 / scope_bytes,
            "baseline_payload_bytes": core["baseline_payload_bytes"],
            "candidate_payload_bytes": row["candidate_payload_bytes"],
            "positive_blocks": row["positive_blocks"],
            "regressing_blocks": row["regressing_blocks"],
            "block_qbits": row["block_qbits"],
        },
        "artifacts": {
            "raw_input": artifact(root, raw_path),
            "probability_trace": artifact(root, trace_path),
            "wrt_store": artifact(root, store_path),
            "core_receipt": artifact(root, core_path),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = (args.repo_root or Path(__file__).resolve().parents[3]).resolve()
    base = root / "projects/enwiki9/results/fx2_reference_residual_v1"
    selection_trace = base / "trace/reference-dense-500000-0"
    confirmation_trace = (
        root
        / "projects/enwiki9/results/random_window_novelty_v1/"
        "wrt_title_token_automaton_v1/selection-500000-0"
    )
    windows = [
        window(
            root,
            phase="selection",
            offset=306_000_000,
            scope_bytes=500_000,
            core_path=base / "wrt-hashed-residual-online-selection-500000-306000000.json",
            raw_path=selection_trace / "input.raw",
            trace_path=selection_trace / "probability.trace",
            store_path=selection_trace / "input.wrt.store",
        ),
        window(
            root,
            phase="confirmation",
            offset=205_537_142,
            scope_bytes=500_000,
            core_path=base / "wrt-hashed-residual-online-confirmation-500000-205537142.json",
            raw_path=confirmation_trace / "input.raw",
            trace_path=confirmation_trace / "probability.trace",
            store_path=confirmation_trace / "input.wrt.store",
        ),
    ]
    rates = [item["frozen_variant"]["exact_saved_bytes_per_million"] for item in windows]
    receipt = {
        "schema_version": 1,
        "receipt_type": "wrt_hashed_residual_online_two_window_decision",
        "evidence_level": "causal_exact_raw_fx2_probability_trace_shadow",
        "frozen_variant_id": FROZEN_VARIANT,
        "selection_rule": "maximum development qbits on the offset-306000000 window only",
        "confirmation_rule": "replay the frozen variant; ignore confirmation-local selection",
        "source": artifact(root, root / "projects/enwiki9/tools/wrt_hashed_residual_online_screen.cpp"),
        "windows": windows,
        "economics": {
            "endpoint428_remaining_debt_bytes_per_million": TARGET_DEBT_BYTES_PER_MILLION,
            "observed_min_exact_saved_bytes_per_million": min(rates),
            "observed_max_exact_saved_bytes_per_million": max(rates),
            "incremental_source_cost_bytes": None,
            "target_closing_before_source_cost": min(rates) > TARGET_DEBT_BYTES_PER_MILLION,
        },
        "decision": "retire unchanged endpoint; retain event-phase residual SSE as a positive primitive",
        "next_action": "test a causal hierarchical event-phase backoff endpoint; require target-paying exact gain before endpoint428 integration",
        "claim_boundary": (
            "Two raw-FX2 trace shadows do not prove endpoint428 transfer, counted source economics, "
            "native integration, or a full-corpus Hutter score."
        ),
        "promotion_authorized": False,
    }
    output = args.output or base / "wrt-hashed-residual-online-two-window-decision.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
