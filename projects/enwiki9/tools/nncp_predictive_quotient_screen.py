#!/usr/bin/env python3
"""Screen fixed-budget causal symbol quotients against an NNCP teacher."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from radix_island_oracle import artifact
from verify_nncp_teacher_distribution import rows


TOTAL = 65536
VOCAB = 336
TABLE_BYTES = VOCAB * 2
KEY_BYTES = 2
HEADER_BYTES = 64


def quantize(values: np.ndarray) -> np.ndarray:
    values = np.maximum(values.astype(np.float64), 1e-12)
    values /= values.sum()
    available = TOTAL - len(values)
    scaled = values * available
    base = np.floor(scaled).astype(np.int64) + 1
    remainder = TOTAL - int(base.sum())
    if remainder:
        order = np.argsort(-(scaled - np.floor(scaled)))
        base[order[:remainder]] += 1
    if int(base.sum()) != TOTAL or np.any(base <= 0):
        raise ValueError("invalid quantized distribution")
    return base


def qbits(freq: int) -> int:
    return int(round(-math.log2(freq / TOTAL) * 256))


def evaluate(
    true_symbols: np.ndarray,
    prior_symbols: np.ndarray,
    base: np.ndarray,
    tables: dict[int, np.ndarray],
    lo: int,
    hi: int,
) -> int:
    total = 0
    for index in range(lo, hi):
        table = tables.get(int(prior_symbols[index]), base)
        total += qbits(int(table[int(true_symbols[index])]))
    return total


def run(args: argparse.Namespace) -> dict[str, Any]:
    trace = list(rows(args.teacher_trace))
    vocabularies = {fixed[-1] for fixed, _ in trace}
    if vocabularies != {VOCAB}:
        raise ValueError(f"unexpected vocabularies: {vocabularies}")
    if any(fixed[0] != index for index, (fixed, _) in enumerate(trace)):
        raise ValueError("teacher trace is not causal symbol order")
    true_symbols = np.array([fixed[6] for fixed, _ in trace], dtype=np.int32)
    distributions = np.stack([distribution for _, distribution in trace])
    prior_symbols = np.zeros(len(trace), dtype=np.int32)
    prior_symbols[1:] = true_symbols[:-1]
    train_end = len(trace) * 3 // 5
    development_end = len(trace) * 4 // 5
    soft_base = distributions[:train_end].sum(axis=0)
    base = quantize(soft_base)
    contexts: dict[int, np.ndarray] = defaultdict(
        lambda: np.zeros(VOCAB, dtype=np.float64)
    )
    support: Counter[int] = Counter()
    for index in range(train_end):
        key = int(prior_symbols[index])
        contexts[key] += distributions[index]
        support[key] += 1
    ranked = [key for key, _ in support.most_common()]
    teacher_qbits = np.rint(
        -np.log2(
            distributions[np.arange(len(trace)), true_symbols].astype(np.float64)
        )
        * 256
    ).astype(np.int64)
    base_dev = evaluate(
        true_symbols, prior_symbols, base, {}, train_end, development_end
    )
    base_holdout = evaluate(
        true_symbols, prior_symbols, base, {}, development_end, len(trace)
    )
    teacher_dev = int(teacher_qbits[train_end:development_end].sum())
    teacher_holdout = int(teacher_qbits[development_end:].sum())
    candidates: dict[str, Any] = {}
    for budget in args.budgets:
        max_contexts = max(0, (budget - HEADER_BYTES - TABLE_BYTES) // (
            TABLE_BYTES + KEY_BYTES
        ))
        selected = ranked[:max_contexts]
        tables = {key: quantize(contexts[key]) for key in selected}
        package = HEADER_BYTES + TABLE_BYTES + len(tables) * (
            TABLE_BYTES + KEY_BYTES
        )
        dev = evaluate(
            true_symbols,
            prior_symbols,
            base,
            tables,
            train_end,
            development_end,
        )
        holdout = evaluate(
            true_symbols,
            prior_symbols,
            base,
            tables,
            development_end,
            len(trace),
        )
        denominator = base_holdout - teacher_holdout
        retention = (
            (base_holdout - holdout) / denominator if denominator > 0 else 0.0
        )
        candidates[str(budget)] = {
            "budget_bytes": budget,
            "serialized_bytes": package,
            "context_tables": len(tables),
            "development_qbits": dev,
            "development_saved_vs_base_bytes": (base_dev - dev) / 2048.0,
            "holdout_qbits": holdout,
            "holdout_saved_vs_base_bytes": (base_holdout - holdout) / 2048.0,
            "holdout_teacher_gap_bytes": denominator / 2048.0,
            "holdout_teacher_gap_retention": retention,
            "two_part_holdout_bytes": holdout / 2048.0 + package,
            "passes_80_percent_retention": retention >= 0.8,
        }
    winner = max(
        candidates,
        key=lambda key: (
            candidates[key]["holdout_teacher_gap_retention"],
            -candidates[key]["serialized_bytes"],
        ),
    )
    passed = candidates[winner]["passes_80_percent_retention"]
    return {
        "schema": "nncp_predictive_quotient_screen_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "bounded_decoder_visible_integer_student_shadow_zero_credit",
        "artifacts": {"teacher_trace": artifact(args.teacher_trace)},
        "scope": {
            "rows": len(trace),
            "training_rows": train_end,
            "development_rows": development_end - train_end,
            "holdout_rows": len(trace) - development_end,
            "vocabulary": VOCAB,
        },
        "controls": {
            "base_development_qbits": base_dev,
            "base_holdout_qbits": base_holdout,
            "teacher_development_qbits": teacher_dev,
            "teacher_holdout_qbits": teacher_holdout,
        },
        "candidates": candidates,
        "gate": {
            "winner_budget": int(winner),
            "passed": passed,
            "verdict": (
                "bounded_quotient_retains_teacher_gap"
                if passed
                else "bounded_quotient_fails_retention_gate"
            ),
        },
        "claim_boundary": (
            "Chronological student shadow only. Package bytes are explicit, "
            "but no arithmetic archive, raw roundtrip, Gamma integration, "
            "distant transfer, runtime, or score credit is established."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teacher-trace", type=Path, required=True)
    parser.add_argument(
        "--budgets", type=int, nargs="+", default=[65536, 131072, 262144]
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
