#!/usr/bin/env python3
"""Distill coarse WRT copy residual rules and replay untouched confirmation."""

from __future__ import annotations

import argparse
import json
import pathlib
from dataclasses import dataclass, field
from typing import Any

from fx2_shadow_residual_coder import BinaryArithmeticEncoder, iter_rows
from streaming_retrieval_shadow import (
    PartialByteState,
    WrtCopyState,
    as_int,
    blend_probability,
    clamp_p1,
    prob_bucket,
    qbits_for,
    wrt_regime,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_ROWS = (
    ROOT
    / "results"
    / "wrt_wiki_shell_v1"
    / "trace_64k_entity_v2"
    / "residual_cache.tsv"
)
DEFAULT_OUT = (
    ROOT
    / "results"
    / "wrt_wiki_shell_v1"
    / "copy_rule_ledger_64k_v1.json"
)
FAMILIES = (
    "regime_bit",
    "support_bit",
    "regime_support",
    "base_copy",
    "regime_base_copy",
)
BANDS = ("copy_global", "copy_page", "copy_typed", "copy_title")


@dataclass
class Totals:
    rows: int = 0
    gain_qbits: int = 0


@dataclass
class RuleStats:
    selection: Totals = field(default_factory=Totals)
    confirmation: Totals = field(default_factory=Totals)


@dataclass
class Candidate:
    family: str
    blend_ppm: int
    rules: dict[tuple[Any, ...], RuleStats] = field(default_factory=dict)

    @property
    def model_id(self) -> str:
        return f"{self.family}_b{self.blend_ppm}"


def support_bucket(support: int) -> int:
    return min(7, max(0, support.bit_length() - 1))


def rule_key(
    family: str,
    band: str,
    row: dict[str, Any],
    bit_pos: int,
    base_p1: int,
    copy_p1: int,
    support: int,
) -> tuple[Any, ...]:
    regime = wrt_regime(row)
    support_bin = support_bucket(support)
    base_bin = prob_bucket(base_p1, 8)
    copy_bin = prob_bucket(copy_p1, 8)
    if family == "regime_bit":
        return band, regime, bit_pos
    if family == "support_bit":
        return band, support_bin, bit_pos
    if family == "regime_support":
        return band, regime, support_bin, bit_pos
    if family == "base_copy":
        return band, base_bin, copy_bin, bit_pos
    if family == "regime_base_copy":
        return band, regime, base_bin, copy_bin, bit_pos
    raise ValueError(f"unknown family: {family}")


def split_for(pos: int, warmup_end: int, selection_end: int) -> str:
    if pos < warmup_end:
        return "warmup"
    return "selection" if pos < selection_end else "confirmation"


def make_copy_state(args: argparse.Namespace) -> WrtCopyState:
    return WrtCopyState(
        min_match=args.copy_min_match,
        max_match=args.copy_max_match,
        candidates_per_key=args.copy_candidates,
        cap_entries=args.copy_index_cap_entries,
    )


def scan(args: argparse.Namespace, models: list[Candidate]) -> tuple[int, int]:
    copy_state = make_copy_state(args)
    partial = PartialByteState()
    rows = 0
    max_pos = -1
    for row in iter_rows(args.rows):
        bit = as_int(row, "bit", default=-1)
        pos = as_int(row, "pos", default=-1)
        bit_pos = as_int(row, "bit_pos", default=-1)
        if bit not in (0, 1) or pos < 0 or not 0 <= bit_pos <= 7:
            continue
        partial_len, partial_prefix = partial.advance_to(pos, bit_pos)
        copy_state.prepare(row)
        copy_candidates = copy_state.band_candidates(
            row,
            partial_len,
            partial_prefix,
            alpha_num=args.alpha2,
            bands=BANDS,
        )
        base_p1 = clamp_p1(as_int(row, "p1", default=32768))
        base_qbits = as_int(row, "baseline_qbits", default=qbits_for(bit, base_p1))
        split = split_for(pos, args.warmup_end, args.selection_end)
        if split != "warmup":
            for model in models:
                for band, (copy_p1, support) in copy_candidates.items():
                    key = rule_key(
                        model.family,
                        band,
                        row,
                        bit_pos,
                        base_p1,
                        copy_p1,
                        support,
                    )
                    corrected = blend_probability(base_p1, copy_p1, model.blend_ppm)
                    gain = base_qbits - qbits_for(bit, corrected)
                    totals = getattr(model.rules.setdefault(key, RuleStats()), split)
                    totals.rows += 1
                    totals.gain_qbits += gain
        partial.observe(pos, bit)
        if partial.length == 8:
            copy_state.observe_byte(partial.prefix, row)
        rows += 1
        max_pos = max(max_pos, pos)
    return rows, max_pos


def selected_rules(
    model: Candidate,
    min_rows: int,
    min_gain_qbits: int,
) -> dict[tuple[Any, ...], float]:
    return {
        key: stats.selection.gain_qbits / stats.selection.rows
        for key, stats in model.rules.items()
        if stats.selection.rows >= min_rows
        and stats.selection.gain_qbits >= min_gain_qbits
    }


def exact_replay(
    args: argparse.Namespace,
    models: list[Candidate],
    frozen: dict[str, dict[tuple[Any, ...], float]],
) -> dict[str, Any]:
    copy_state = make_copy_state(args)
    partial = PartialByteState()
    coders = {
        model.model_id: (BinaryArithmeticEncoder(), BinaryArithmeticEncoder())
        for model in models
    }
    block_qbits: dict[str, dict[int, int]] = {
        model.model_id: {} for model in models
    }
    confirmation_rows = 0
    for row in iter_rows(args.rows):
        bit = as_int(row, "bit", default=-1)
        pos = as_int(row, "pos", default=-1)
        bit_pos = as_int(row, "bit_pos", default=-1)
        if bit not in (0, 1) or pos < 0 or not 0 <= bit_pos <= 7:
            continue
        partial_len, partial_prefix = partial.advance_to(pos, bit_pos)
        copy_state.prepare(row)
        copy_candidates = copy_state.band_candidates(
            row,
            partial_len,
            partial_prefix,
            alpha_num=args.alpha2,
            bands=BANDS,
        )
        base_p1 = clamp_p1(as_int(row, "p1", default=32768))
        if pos >= args.selection_end:
            base_qbits = as_int(row, "baseline_qbits", default=qbits_for(bit, base_p1))
            for model in models:
                choices: list[tuple[float, int]] = []
                rules = frozen[model.model_id]
                for band, (copy_p1, support) in copy_candidates.items():
                    key = rule_key(
                        model.family,
                        band,
                        row,
                        bit_pos,
                        base_p1,
                        copy_p1,
                        support,
                    )
                    if key in rules:
                        choices.append((rules[key], copy_p1))
                chosen_p1 = max(choices, default=(0.0, base_p1))[1]
                corrected = (
                    blend_probability(base_p1, chosen_p1, model.blend_ppm)
                    if choices
                    else base_p1
                )
                baseline, candidate = coders[model.model_id]
                baseline.encode(bit, base_p1)
                candidate.encode(bit, corrected)
                block = pos // args.block_bytes
                block_qbits[model.model_id][block] = (
                    block_qbits[model.model_id].get(block, 0)
                    + base_qbits
                    - qbits_for(bit, corrected)
                )
            confirmation_rows += 1
        partial.observe(pos, bit)
        if partial.length == 8:
            copy_state.observe_byte(partial.prefix, row)

    output: dict[str, Any] = {}
    for model in models:
        baseline, candidate = coders[model.model_id]
        baseline.finish()
        candidate.finish()
        blocks = block_qbits[model.model_id]
        output[model.model_id] = {
            "confirmation_rows": confirmation_rows,
            "baseline_bytes": baseline.byte_count,
            "candidate_bytes": candidate.byte_count,
            "saved_bytes": baseline.byte_count - candidate.byte_count,
            "saved_bits": baseline.bit_count - candidate.bit_count,
            "positive_blocks": sum(value > 0 for value in blocks.values()),
            "regressing_blocks": sum(value < 0 for value in blocks.values()),
            "flat_blocks": sum(value == 0 for value in blocks.values()),
            "largest_regression_qbit_bytes": max(
                (-value / 2048.0 for value in blocks.values() if value < 0),
                default=0.0,
            ),
        }
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=pathlib.Path, default=DEFAULT_ROWS)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--blend-ppm", default="25000,50000,100000")
    parser.add_argument("--warmup-end", type=int, default=12_000)
    parser.add_argument("--selection-end", type=int, default=24_000)
    parser.add_argument("--min-selection-rows", type=int, default=64)
    parser.add_argument("--min-selection-gain-qbits", type=int, default=256)
    parser.add_argument("--rule-bytes", type=int, default=12)
    parser.add_argument("--base-code-bytes", type=int, default=4096)
    parser.add_argument("--block-bytes", type=int, default=4096)
    parser.add_argument("--alpha2", type=int, default=1)
    parser.add_argument("--copy-min-match", type=int, default=3)
    parser.add_argument("--copy-max-match", type=int, default=16)
    parser.add_argument("--copy-candidates", type=int, default=8)
    parser.add_argument("--copy-index-cap-entries", type=int, default=200_000)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.rows.exists():
        raise SystemExit(f"missing rows: {args.rows}")
    if not 0 <= args.warmup_end < args.selection_end:
        raise SystemExit("require 0 <= warmup-end < selection-end")
    if args.min_selection_rows <= 0 or args.min_selection_gain_qbits <= 0:
        raise SystemExit("selection support and gain thresholds must be positive")

    blends = [int(value) for value in args.blend_ppm.split(",") if value]
    models = [
        Candidate(family=family, blend_ppm=blend)
        for family in FAMILIES
        for blend in blends
    ]
    rows, max_pos = scan(args, models)
    frozen = {
        model.model_id: selected_rules(
            model,
            args.min_selection_rows,
            args.min_selection_gain_qbits,
        )
        for model in models
    }
    exact = exact_replay(args, models, frozen)
    ledger = []
    for model in models:
        rule_count = len(frozen[model.model_id])
        estimated_program_bytes = args.base_code_bytes + rule_count * args.rule_bytes
        exact_row = exact[model.model_id]
        ledger.append(
            {
                "model_id": model.model_id,
                "family": model.family,
                "blend_ppm": model.blend_ppm,
                "selected_rules": rule_count,
                "estimated_program_bytes": estimated_program_bytes,
                "confirmation": exact_row,
                "confirmation_net_bytes": exact_row["saved_bytes"]
                - estimated_program_bytes,
            }
        )
    ledger.sort(
        key=lambda item: (
            -item["confirmation"]["saved_bytes"],
            item["confirmation"]["regressing_blocks"],
            item["estimated_program_bytes"],
            item["model_id"],
        )
    )
    payload = {
        "receipt_type": "wrt_wiki_shell_copy_rule_ledger",
        "evidence_level": "selection_distilled_confirmation_exact_shadow",
        "claim_boundary": (
            "Rules are selected only from the middle trace split and exact-replayed "
            "on the untouched suffix. This is not a native archive or 10.80% claim."
        ),
        "input": str(args.rows),
        "rows": rows,
        "max_pos": max_pos,
        "split": {
            "warmup_end": args.warmup_end,
            "selection_end": args.selection_end,
            "confirmation_start": args.selection_end,
        },
        "selection_threshold": {
            "min_rows": args.min_selection_rows,
            "min_gain_qbits": args.min_selection_gain_qbits,
        },
        "copy_contract": {
            "bands": list(BANDS),
            "min_match": args.copy_min_match,
            "max_match": args.copy_max_match,
            "candidates_per_key": args.copy_candidates,
            "index_cap_entries": args.copy_index_cap_entries,
        },
        "ledger": ledger,
        "promotion_candidates": [
            item["model_id"]
            for item in ledger
            if item["confirmation_net_bytes"] > 0
            and item["confirmation"]["regressing_blocks"] == 0
        ],
        "verdict": (
            "compile_smallest_paying_rule_family"
            if any(
                item["confirmation_net_bytes"] > 0
                and item["confirmation"]["regressing_blocks"] == 0
                for item in ledger
            )
            else "no_copy_rule_family_clears_counted_confirmation"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(
            json.dumps(
                {
                    "rows": rows,
                    "top": ledger[0] if ledger else None,
                    "promotion_candidates": payload["promotion_candidates"],
                    "verdict": payload["verdict"],
                    "output": str(args.output),
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
