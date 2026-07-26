#!/usr/bin/env python3
"""Rank tiny causal Wiki/XML residual corrections on an exact FX2 trace.

The broad search phase uses rounded qbit loss to rank a small, fixed family of
decoder-visible state keys. Only the selection winners receive an exact binary
arithmetic replay. Every correction is causal: its residual counter and local
regret are read before the current bit and updated after it. The gate abstains
until that context's hypothetical correction has beaten the base probability
on prior rows.

This is a shadow evidence tool. It never claims a constructive Hutter score.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from dataclasses import dataclass, field
from typing import Any, Iterable

from fx2_shadow_residual_coder import BinaryArithmeticEncoder, TOTAL, clamp_p1


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_ROWS = ROOT / "results" / "fx2_residual_cache" / "apm1m_full_4805936.tsv"
DEFAULT_OUT = ROOT / "results" / "fx2_residual_xml_ledger" / "apm1m_v1.json"

BASELINE_SCORE = 110_181_114
TARGET_SCORE = 109_000_000
CALIBRATED_10M_TO_1G = 66.95533418670768

TRACE_FIELDS = (
    "pos",
    "bit_pos",
    "bit",
    "p1",
    "baseline_qbits",
    "field",
    "mode",
    "slot",
    "page_kind",
    "char_class",
    "template_depth",
    "in_tag",
    "ref",
    "url",
    "number_class",
    "word_len",
    "col_bucket",
    "page_bucket",
    "category_state",
    "template_arg",
    "link_recency",
    "title_hash",
    "template_hash",
    "link_hash",
    "entity_hash",
    "word_hash",
    "pair_sig",
    "wrt_stream_byte",
    "wrt_token_class",
    "wrt_token_id",
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
    "wrt_title_hash",
    "wrt_template_hash",
    "wrt_ref_hash",
    "wrt_section_hash",
    "wrt_reconstructed_bytes",
)

STATE_SPECS: dict[str, tuple[str, ...]] = {
    "calibration": (),
    "lexer": ("mode",),
    "tag": ("in_tag",),
    "template": ("template_depth_bucket",),
    "number": ("number_class",),
    "word": ("word_len_bucket",),
    "layout": ("col_bucket", "page_bucket"),
    "lexer_char": ("mode", "char_class"),
    "template_char": ("template_depth_bucket", "char_class"),
    "template_layout": ("template_depth_bucket", "col_bucket"),
    "xml_compact": ("mode", "in_tag", "char_class"),
    "wiki_compact": (
        "mode",
        "char_class",
        "template_depth_bucket",
        "number_class",
    ),
    "ref_url": ("ref", "url"),
    "page_kind": ("page_kind",),
    "template_arg": ("template_depth_bucket", "template_arg"),
    "title_echo": ("title_echo",),
    "wrt_token": (
        "wrt_token_class",
        "wrt_dictionary_hit_type",
        "wrt_literal_phase",
        "wrt_token_id_bucket",
    ),
    "wrt_regime": ("wrt_regime",),
    "wrt_layout": (
        "wrt_table_mode",
        "wrt_list_mode",
        "wrt_section_state",
        "wrt_section_level_bucket",
    ),
    "wrt_schema": (
        "wrt_template_depth_bucket",
        "wrt_ref_mode",
        "wrt_token_class",
        "wrt_dictionary_hit_type",
    ),
    "wrt_title_memory": (
        "wrt_title_mode",
        "wrt_title_hash_bucket",
        "wrt_token_id_bucket",
    ),
    "wrt_ref_memory": (
        "wrt_ref_mode",
        "wrt_ref_hash_bucket",
        "wrt_token_id_bucket",
    ),
    "wrt_template_memory": (
        "wrt_template_depth_bucket",
        "wrt_template_hash_bucket",
        "wrt_token_id_bucket",
    ),
    "wrt_section_memory": (
        "wrt_section_state",
        "wrt_section_hash_bucket",
        "wrt_token_id_bucket",
    ),
    "wrt_router": (
        "wrt_regime",
        "wrt_token_class",
        "wrt_dictionary_hit_type",
        "wrt_number_class",
    ),
    "wrt_router_memory": (
        "wrt_regime",
        "wrt_token_class",
        "wrt_dictionary_hit_type",
        "wrt_number_class",
        "wrt_active_memory_bucket",
    ),
}

LEGACY_FAMILIES = tuple(
    name for name in STATE_SPECS if not name.startswith("wrt_")
)
WRT_SHELL_FAMILIES = (
    "calibration",
    "wrt_token",
    "wrt_regime",
    "wrt_layout",
    "wrt_schema",
    "wrt_title_memory",
    "wrt_ref_memory",
    "wrt_template_memory",
    "wrt_section_memory",
    "wrt_router",
    "wrt_router_memory",
)

STATE_SOURCE_FIELDS: dict[str, tuple[str, ...]] = {
    "template_depth_bucket": ("template_depth",),
    "word_len_bucket": ("word_len",),
    "title_echo": ("title_hash", "word_hash"),
    "wrt_token_id_bucket": ("wrt_token_id",),
    "wrt_regime": ("wrt_page_mode", "wrt_prose_mode", "wrt_ref_mode"),
    "wrt_section_level_bucket": ("wrt_section_level",),
    "wrt_template_depth_bucket": ("wrt_template_depth",),
    "wrt_title_hash_bucket": ("wrt_title_hash",),
    "wrt_template_hash_bucket": ("wrt_template_hash",),
    "wrt_ref_hash_bucket": ("wrt_ref_hash",),
    "wrt_section_hash_bucket": ("wrt_section_hash",),
    "wrt_active_memory_bucket": (
        "wrt_title_hash",
        "wrt_template_hash",
        "wrt_ref_hash",
        "wrt_section_hash",
    ),
}

OBSERVABILITY_FIELDS = (
    "field",
    "mode",
    "slot",
    "page_kind",
    "char_class",
    "template_depth",
    "in_tag",
    "ref",
    "url",
    "number_class",
    "word_len",
    "col_bucket",
    "page_bucket",
    "category_state",
    "template_arg",
    "link_recency",
    "title_hash",
    "template_hash",
    "link_hash",
    "entity_hash",
    "word_hash",
    "pair_sig",
    "wrt_stream_byte",
    "wrt_token_class",
    "wrt_token_id",
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
    "wrt_title_hash",
    "wrt_template_hash",
    "wrt_ref_hash",
    "wrt_section_hash",
    "wrt_reconstructed_bytes",
)


def qbits_for(bit: int, p1: int) -> int:
    p1 = clamp_p1(p1)
    probability = p1 / TOTAL if bit else (TOTAL - p1) / TOTAL
    return int(-math.log2(probability) * 256.0 + 0.5)


def prob_bucket(p1: int, buckets: int) -> int:
    return min(buckets - 1, (clamp_p1(p1) * buckets) >> 16)


def fast_rows(path: pathlib.Path) -> Iterable[dict[str, int]]:
    """Read the fixed residual-cache TSV without allocating csv DictReaders."""

    with path.open("r", errors="replace") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        indexes = {name: header.index(name) for name in TRACE_FIELDS if name in header}
        required = {"pos", "bit_pos", "bit", "p1"}
        missing = sorted(required - indexes.keys())
        if missing:
            raise SystemExit(f"trace is missing required fields: {', '.join(missing)}")
        for line in handle:
            values = line.rstrip("\n").split("\t")
            row: dict[str, int] = {}
            for name, index in indexes.items():
                try:
                    row[name] = int(values[index])
                except (IndexError, ValueError):
                    row[name] = 0
            yield row


def state_value(row: dict[str, int], name: str) -> int:
    if name == "template_depth_bucket":
        return min(row.get("template_depth", 0), 3)
    if name == "word_len_bucket":
        return min(row.get("word_len", 0), 15)
    if name == "title_echo":
        title = row.get("title_hash", 0)
        word = row.get("word_hash", 0)
        return int(title != 0 and title == word)
    if name == "wrt_token_id_bucket":
        return row.get("wrt_token_id", 0) & 255
    if name == "wrt_section_level_bucket":
        return min(row.get("wrt_section_level", 0), 6)
    if name == "wrt_template_depth_bucket":
        return min(row.get("wrt_template_depth", 0), 3)
    if name.endswith("_hash_bucket"):
        return row.get(name.removesuffix("_bucket"), 0) & 255
    if name == "wrt_regime":
        ordered_modes = (
            "wrt_title_mode",
            "wrt_ref_mode",
            "wrt_url_mode",
            "wrt_table_mode",
            "wrt_list_mode",
            "wrt_template_depth",
            "wrt_section_state",
            "wrt_prose_mode",
            "wrt_page_mode",
        )
        for regime, field_name in enumerate(ordered_modes, start=1):
            if row.get(field_name, 0):
                return regime
        return 0
    if name == "wrt_active_memory_bucket":
        if row.get("wrt_ref_mode", 0):
            value = row.get("wrt_ref_hash", 0)
        elif row.get("wrt_template_depth", 0):
            value = row.get("wrt_template_hash", 0)
        elif row.get("wrt_title_mode", 0):
            value = row.get("wrt_title_hash", 0)
        else:
            value = row.get("wrt_section_hash", 0)
        return value & 255
    return row.get(name, 0)


def split_name(pos: int, warmup_bytes: int, selection_end_bytes: int) -> str:
    if pos < warmup_bytes:
        return "warmup"
    if pos < selection_end_bytes:
        return "selection"
    return "confirmation"


@dataclass
class Context:
    count: int = 0
    residual_sum: int = 0
    hypothetical_gain_qbits: int = 0

    def corrected_p1(self, base_p1: int, blend_ppm: int) -> int:
        if self.count <= 0:
            return base_p1
        delta = (self.residual_sum * blend_ppm) // (self.count * 1_000_000)
        return clamp_p1(base_p1 + delta)

    def update(self, bit: int, base_p1: int, base_qbits: int, corrected_qbits: int) -> None:
        self.hypothetical_gain_qbits += base_qbits - corrected_qbits
        self.residual_sum += TOTAL - base_p1 if bit else -base_p1
        self.count += 1


@dataclass
class SplitTotals:
    rows: int = 0
    applied_rows: int = 0
    base_qbits: int = 0
    candidate_qbits: int = 0

    @property
    def saved_qbits(self) -> int:
        return self.base_qbits - self.candidate_qbits

    @property
    def saved_bytes(self) -> float:
        return self.saved_qbits / 2048.0


@dataclass
class ResidualModel:
    name: str
    fields: tuple[str, ...]
    p_buckets: int
    blend_ppm: int
    min_support: int
    regret_margin_qbits: int
    contexts: dict[tuple[int, ...], Context] = field(default_factory=dict)
    splits: dict[str, SplitTotals] = field(
        default_factory=lambda: {
            "warmup": SplitTotals(),
            "selection": SplitTotals(),
            "confirmation": SplitTotals(),
        }
    )
    confirmation_blocks: dict[int, int] = field(default_factory=dict)

    @property
    def model_id(self) -> str:
        return f"{self.name}_b{self.blend_ppm}_p{self.p_buckets}"

    def key(self, row: dict[str, int], base_p1: int) -> tuple[int, ...]:
        return (
            prob_bucket(base_p1, self.p_buckets),
            row.get("bit_pos", 0),
            *(state_value(row, name) for name in self.fields),
        )

    def predict(self, row: dict[str, int], base_p1: int) -> tuple[int, Context, bool, int]:
        context = self.contexts.setdefault(self.key(row, base_p1), Context())
        corrected = context.corrected_p1(base_p1, self.blend_ppm)
        apply = (
            context.count >= self.min_support
            and context.hypothetical_gain_qbits > self.regret_margin_qbits
        )
        return (corrected if apply else base_p1), context, apply, corrected

    def update(
        self,
        row: dict[str, int],
        bit: int,
        base_p1: int,
        base_qbits: int,
        split: str,
        block_id: int | None,
    ) -> None:
        predicted, context, applied, hypothetical = self.predict(row, base_p1)
        candidate_qbits = qbits_for(bit, predicted)
        hypothetical_qbits = qbits_for(bit, hypothetical)
        totals = self.splits[split]
        totals.rows += 1
        totals.applied_rows += int(applied)
        totals.base_qbits += base_qbits
        totals.candidate_qbits += candidate_qbits
        if split == "confirmation" and block_id is not None:
            self.confirmation_blocks[block_id] = (
                self.confirmation_blocks.get(block_id, 0) + base_qbits - candidate_qbits
            )
        context.update(bit, base_p1, base_qbits, hypothetical_qbits)


@dataclass
class Observability:
    rows: int = 0
    nonzero: dict[str, int] = field(
        default_factory=lambda: {name: 0 for name in OBSERVABILITY_FIELDS}
    )
    distinct: dict[str, set[int]] = field(
        default_factory=lambda: {name: set() for name in OBSERVABILITY_FIELDS}
    )

    def update(self, row: dict[str, int]) -> None:
        self.rows += 1
        for name in OBSERVABILITY_FIELDS:
            value = row.get(name, 0)
            self.nonzero[name] += int(value != 0)
            if len(self.distinct[name]) <= 256:
                self.distinct[name].add(value)

    def payload(self) -> dict[str, Any]:
        return {
            name: {
                "nonzero_rows": self.nonzero[name],
                "nonzero_fraction": self.nonzero[name] / self.rows if self.rows else 0.0,
                "distinct_values_capped": len(self.distinct[name]),
                "observable": len(self.distinct[name]) > 1,
            }
            for name in OBSERVABILITY_FIELDS
        }


def build_models(args: argparse.Namespace) -> list[ResidualModel]:
    default_families = (
        WRT_SHELL_FAMILIES if args.profile == "wrt-shell" else LEGACY_FAMILIES
    )
    requested = args.family or list(default_families)
    unknown = sorted(set(requested) - STATE_SPECS.keys())
    if unknown:
        raise SystemExit(f"unknown state families: {', '.join(unknown)}")
    blends = [int(value) for value in args.blend_ppm.split(",") if value]
    return [
        ResidualModel(
            name=name,
            fields=STATE_SPECS[name],
            p_buckets=args.p_buckets,
            blend_ppm=blend,
            min_support=args.min_support,
            regret_margin_qbits=args.regret_margin_qbits,
        )
        for name in requested
        for blend in blends
    ]


def qbit_scan(args: argparse.Namespace) -> tuple[list[ResidualModel], Observability, int, int]:
    models = build_models(args)
    observability = Observability()
    max_pos = -1
    rows = 0
    for row in fast_rows(args.rows):
        bit = row.get("bit", -1)
        base_p1 = row.get("p1", 0)
        if bit not in (0, 1) or not (0 < base_p1 < TOTAL):
            continue
        pos = row.get("pos", 0)
        max_pos = max(max_pos, pos)
        split = split_name(pos, args.warmup_bytes, args.selection_end_bytes)
        base_qbits = row.get("baseline_qbits", qbits_for(bit, base_p1))
        block_id = pos // args.block_bytes if split == "confirmation" else None
        observability.update(row)
        for model in models:
            model.update(row, bit, base_p1, base_qbits, split, block_id)
        rows += 1
        if args.max_rows > 0 and rows >= args.max_rows:
            break
    return models, observability, rows, max_pos


def fresh_model(model: ResidualModel) -> ResidualModel:
    return ResidualModel(
        name=model.name,
        fields=model.fields,
        p_buckets=model.p_buckets,
        blend_ppm=model.blend_ppm,
        min_support=model.min_support,
        regret_margin_qbits=model.regret_margin_qbits,
    )


def exact_replay(
    args: argparse.Namespace,
    selected: list[ResidualModel],
) -> dict[str, dict[str, Any]]:
    states = {model.model_id: fresh_model(model) for model in selected}
    coders: dict[str, dict[str, tuple[BinaryArithmeticEncoder, BinaryArithmeticEncoder]]] = {
        model_id: {
            "selection": (BinaryArithmeticEncoder(), BinaryArithmeticEncoder()),
            "confirmation": (BinaryArithmeticEncoder(), BinaryArithmeticEncoder()),
        }
        for model_id in states
    }
    blocks: dict[str, dict[int, tuple[BinaryArithmeticEncoder, BinaryArithmeticEncoder]]] = {
        model_id: {} for model_id in states
    }
    rows = 0
    for row in fast_rows(args.rows):
        bit = row.get("bit", -1)
        base_p1 = row.get("p1", 0)
        if bit not in (0, 1) or not (0 < base_p1 < TOTAL):
            continue
        pos = row.get("pos", 0)
        split = split_name(pos, args.warmup_bytes, args.selection_end_bytes)
        base_qbits = row.get("baseline_qbits", qbits_for(bit, base_p1))
        for model_id, model in states.items():
            predicted, context, _applied, hypothetical = model.predict(row, base_p1)
            if split in {"selection", "confirmation"}:
                base_coder, candidate_coder = coders[model_id][split]
                base_coder.encode(bit, base_p1)
                candidate_coder.encode(bit, predicted)
            if split == "confirmation":
                block_id = pos // args.block_bytes
                base_coder, candidate_coder = blocks[model_id].setdefault(
                    block_id, (BinaryArithmeticEncoder(), BinaryArithmeticEncoder())
                )
                base_coder.encode(bit, base_p1)
                candidate_coder.encode(bit, predicted)
            context.update(bit, base_p1, base_qbits, qbits_for(bit, hypothetical))
        rows += 1
        if args.max_rows > 0 and rows >= args.max_rows:
            break

    output: dict[str, dict[str, Any]] = {}
    for model_id in states:
        split_payload: dict[str, Any] = {}
        for split, (base_coder, candidate_coder) in coders[model_id].items():
            base_coder.finish()
            candidate_coder.finish()
            split_payload[split] = {
                "baseline_bits": base_coder.bit_count,
                "candidate_bits": candidate_coder.bit_count,
                "saved_bits": base_coder.bit_count - candidate_coder.bit_count,
                "baseline_bytes": base_coder.byte_count,
                "candidate_bytes": candidate_coder.byte_count,
                "saved_bytes": base_coder.byte_count - candidate_coder.byte_count,
            }
        block_rows = []
        for block_id, (base_coder, candidate_coder) in sorted(blocks[model_id].items()):
            base_coder.finish()
            candidate_coder.finish()
            block_rows.append(
                {
                    "block_id": block_id,
                    "baseline_bytes": base_coder.byte_count,
                    "candidate_bytes": candidate_coder.byte_count,
                    "saved_bytes": base_coder.byte_count - candidate_coder.byte_count,
                }
            )
        output[model_id] = {
            "splits": split_payload,
            "confirmation_blocks": block_rows,
            "confirmation_block_regressions": sum(
                row["saved_bytes"] < 0 for row in block_rows
            ),
            "confirmation_positive_blocks": sum(
                row["saved_bytes"] > 0 for row in block_rows
            ),
        }
    return output


def model_payload(model: ResidualModel, estimated_program_bytes: int) -> dict[str, Any]:
    blocks = model.confirmation_blocks
    return {
        "model_id": model.model_id,
        "family": model.name,
        "fields": ["p_bucket", "bit_pos", *model.fields],
        "p_buckets": model.p_buckets,
        "blend_ppm": model.blend_ppm,
        "min_support": model.min_support,
        "regret_margin_qbits": model.regret_margin_qbits,
        "estimated_program_bytes": estimated_program_bytes,
        "contexts": len(model.contexts),
        "splits": {
            name: {
                "rows": totals.rows,
                "applied_rows": totals.applied_rows,
                "applied_fraction": totals.applied_rows / totals.rows if totals.rows else 0.0,
                "saved_qbits": totals.saved_qbits,
                "saved_bytes": totals.saved_bytes,
            }
            for name, totals in model.splits.items()
        },
        "confirmation_qbit_blocks": {
            "blocks": len(blocks),
            "positive": sum(value > 0 for value in blocks.values()),
            "flat": sum(value == 0 for value in blocks.values()),
            "regressions": sum(value < 0 for value in blocks.values()),
            "largest_regression_bytes": (
                max((-value / 2048.0 for value in blocks.values() if value < 0), default=0.0)
            ),
        },
    }


def family_is_observable(name: str, observability: dict[str, Any]) -> bool:
    if name == "calibration":
        return True
    for field_name in STATE_SPECS[name]:
        source_fields = STATE_SOURCE_FIELDS.get(field_name, (field_name,))
        if not all(observability[field]["observable"] for field in source_fields):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank causal Wiki/XML FX2 residual rules.")
    parser.add_argument("--rows", type=pathlib.Path, default=DEFAULT_ROWS)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--family", action="append", default=[])
    parser.add_argument("--profile", choices=("legacy", "wrt-shell"), default="legacy")
    parser.add_argument("--discovery-only", action="store_true")
    parser.add_argument("--p-buckets", type=int, default=64)
    parser.add_argument("--blend-ppm", default="25000,50000")
    parser.add_argument("--min-support", type=int, default=16)
    parser.add_argument("--regret-margin-qbits", type=int, default=256)
    parser.add_argument("--warmup-bytes", type=int, default=200_000)
    parser.add_argument("--selection-end-bytes", type=int, default=400_000)
    parser.add_argument("--block-bytes", type=int, default=16_384)
    parser.add_argument("--exact-top", type=int, default=3)
    parser.add_argument("--added-program-bytes", type=int, default=12_000)
    parser.add_argument("--baseline-score", type=int, default=BASELINE_SCORE)
    parser.add_argument("--target-score", type=int, default=TARGET_SCORE)
    parser.add_argument("--calibrated-scale", type=float, default=CALIBRATED_10M_TO_1G)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.rows.exists():
        raise SystemExit(f"missing rows: {args.rows}")
    if not 0 <= args.warmup_bytes < args.selection_end_bytes:
        raise SystemExit("require 0 <= warmup-bytes < selection-end-bytes")
    if args.block_bytes <= 0 or args.p_buckets <= 0 or args.exact_top < 0:
        raise SystemExit("block-bytes and p-buckets must be positive; exact-top must be non-negative")
    if args.added_program_bytes < 0 or args.calibrated_scale <= 0:
        raise SystemExit("added-program-bytes must be non-negative and calibrated-scale positive")

    models, observability, rows, max_pos = qbit_scan(args)
    observable = observability.payload()
    calibration = {
        model.blend_ppm: model for model in models if model.name == "calibration"
    }

    def incremental_qbits(model: ResidualModel, split: str) -> int:
        control = calibration.get(model.blend_ppm)
        control_qbits = control.splits[split].saved_qbits if control else 0
        return model.splits[split].saved_qbits - control_qbits

    ranked = sorted(
        models,
        key=lambda model: (
            -int(family_is_observable(model.name, observable)),
            -incremental_qbits(model, "selection"),
            -incremental_qbits(model, "confirmation"),
            len(model.contexts),
            model.model_id,
        ),
    )
    exact_state_winners = [
        model
        for model in ranked
        if model.name != "calibration"
        and family_is_observable(model.name, observable)
        and incremental_qbits(model, "selection") > 0
    ][: args.exact_top]
    exact_control_blends = {model.blend_ppm for model in exact_state_winners}
    exact_selected = [
        model
        for model in models
        if model.name == "calibration" and model.blend_ppm in exact_control_blends
    ] + exact_state_winners
    exact = exact_replay(args, exact_selected) if exact_selected else {}

    required_10m_gain = (
        args.baseline_score - args.target_score + args.added_program_bytes
    ) / args.calibrated_scale
    confirmation_scope = max(0, max_pos + 1 - args.selection_end_bytes)
    ledger = [model_payload(model, args.added_program_bytes) for model in ranked]
    for row in ledger:
        model = next(model for model in models if model.model_id == row["model_id"])
        row["family_observable"] = family_is_observable(model.name, observable)
        row["incremental_vs_calibration_qbit_bytes"] = {
            split: incremental_qbits(model, split) / 2048.0
            for split in ("selection", "confirmation")
        }
        exact_row = exact.get(row["model_id"])
        row["exact_shadow"] = exact_row
        if exact_row and confirmation_scope > 0:
            saved = exact_row["splits"]["confirmation"]["saved_bytes"]
            projected_10m = saved * 10_000_000 / confirmation_scope
            projected_full = projected_10m * args.calibrated_scale
            row["target_gate"] = {
                "confirmation_scope_bytes": confirmation_scope,
                "confirmation_saved_bytes": saved,
                "projected_10m_gain_bytes": projected_10m,
                "required_10m_gain_bytes": required_10m_gain,
                "projected_full_gain_bytes": projected_full,
                "projected_full_net_after_program_bytes": (
                    projected_full - args.added_program_bytes
                ),
                "confirmation_block_regressions": exact_row[
                    "confirmation_block_regressions"
                ],
                "promotion_eligible": (
                    not args.discovery_only
                    and args.profile == "wrt-shell"
                    and saved > 0
                    and projected_10m >= required_10m_gain
                    and exact_row["confirmation_block_regressions"] == 0
                ),
            }
        else:
            row["target_gate"] = None

    if args.profile == "wrt-shell":
        requested_feature_observability = {
            name.removeprefix("wrt_"): observable[name]["observable"]
            for name in (
                "wrt_token_class",
                "wrt_dictionary_hit_type",
                "wrt_literal_phase",
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
                "wrt_title_hash",
                "wrt_template_hash",
                "wrt_ref_hash",
                "wrt_section_hash",
            )
        }
        unobservable_requested_states = [
            name
            for name, is_observable in requested_feature_observability.items()
            if not is_observable
        ]
    else:
        requested_feature_observability = {
            "tag": observable["in_tag"]["observable"],
            "section": False,
            "template": observable["template_depth"]["observable"],
            "ref": observable["ref"]["observable"],
            "url": observable["url"]["observable"],
            "table": False,
            "list": False,
            "title_echo": (
                observable["title_hash"]["observable"]
                and observable["word_hash"]["observable"]
            ),
        }
        unobservable_requested_states = [
            name
            for name in ("page_kind", "ref", "url", "category_state", "template_arg")
            if not observable[name]["observable"]
        ]

    payload = {
        "receipt_type": (
            "wrt_wiki_shell_v1_residual_ledger"
            if args.profile == "wrt-shell"
            else "fx2_residual_xml_ledger"
        ),
        "evidence_level": "exact_fx2_trace_shadow_only",
        "claim_boundary": (
            "This ledger ranks causal shadow corrections. It is not a native archive, "
            "roundtrip receipt, constructive score, or 10.95% claim."
        ),
        "input": str(args.rows),
        "rows": rows,
        "position_span": {"min_pos": 0 if rows else None, "max_pos": max_pos},
        "split_contract": {
            "warmup_end_bytes": args.warmup_bytes,
            "selection_end_bytes": args.selection_end_bytes,
            "confirmation_start_bytes": args.selection_end_bytes,
            "confirmation_scope_bytes": confirmation_scope,
            "selection_ranks_models": True,
            "confirmation_is_not_used_for_ranking": True,
        },
        "causality": (
            "keys use current decoder-visible state and base p1; counters, hypothetical "
            "loss, and regret update only after the current decoded bit"
        ),
        "abstention": (
            "a context uses its residual correction only after prior hypothetical gain "
            "exceeds the configured regret margin and minimum support"
        ),
        "target": {
            "baseline_score": args.baseline_score,
            "target_score": args.target_score,
            "forecast_debt_bytes": args.baseline_score - args.target_score,
            "added_program_bytes": args.added_program_bytes,
            "calibrated_10m_to_1g_scale": args.calibrated_scale,
            "required_10m_gain_bytes": required_10m_gain,
            "formula": "(baseline_score - target_score + added_program_bytes) / calibrated_scale",
            "discovery_only": args.discovery_only,
        },
        "observability": observable,
        "requested_feature_observability": requested_feature_observability,
        "unobservable_requested_states": unobservable_requested_states,
        "models_tested": len(ledger),
        "exact_models_replayed": len(exact_selected),
        "exact_state_models_replayed": len(exact_state_winners),
        "ledger": ledger,
        "promotion_candidates": [
            row["model_id"]
            for row in ledger
            if row.get("target_gate") and row["target_gate"]["promotion_eligible"]
        ],
        "verdict": (
            "discovery_trace_only"
            if args.discovery_only
            else
            "compile_smallest_paying_family"
            if any(
                row.get("target_gate") and row["target_gate"]["promotion_eligible"]
                for row in ledger
            )
            else "no_state_family_clears_counted_target_gate"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(
            json.dumps(
                {
                    "rows": rows,
                    "models_tested": len(ledger),
                    "exact_models_replayed": len(exact_selected),
                    "required_10m_gain_bytes": required_10m_gain,
                    "top_selection_model": ledger[0]["model_id"] if ledger else None,
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
