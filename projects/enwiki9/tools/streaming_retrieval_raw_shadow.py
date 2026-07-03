#!/usr/bin/env python3
"""Raw byte-aligned SRSTC shadow probe.

This lock-safe probe tests the streaming retrieval idea on the actual raw
`enwik9` bitstream instead of cached residual rows. It is not a submission
compressor: the baseline is a small adaptive bit context model, and the
candidate adds SRSTC-style retrieval priors on top of that same baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from fx2_shadow_residual_coder import TOTAL, BinaryArithmeticEncoder, clamp_p1, prob_bucket
from streaming_retrieval_shadow import (
    BandRouter,
    BitCounts,
    BoundedCounterTable,
    PartialByteState,
    RetrievalState,
    SplitTotals,
    band_retrieval_p1,
    blend_probability,
    block_id,
    make_keys,
    qbits_for,
    retrieval_p1,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT = ROOT / "results" / "streaming_retrieval_shadow" / "raw_latest.json"
DEFAULT_BASELINE_SCORE = 110_181_114
DEFAULT_TARGET_SCORE = 109_500_000
DEFAULT_SCOPE_BYTES = 1_000_000_000


@dataclass
class RawContextModel:
    cap_entries: int
    p_buckets: int
    order: int
    table: BoundedCounterTable = field(init=False)

    def __post_init__(self) -> None:
        self.table = BoundedCounterTable(cap_entries=self.cap_entries)

    def key(self, history: bytes, bit_pos: int, partial_len: int, partial_prefix: int) -> tuple[Any, ...]:
        if self.order <= 0:
            suffix: tuple[int, ...] = ()
        else:
            suffix = tuple(history[-self.order:])
        return ("raw_base", bit_pos, partial_len, partial_prefix, suffix)

    def predict(
        self,
        history: bytes,
        bit_pos: int,
        partial_len: int,
        partial_prefix: int,
        alpha2: int,
    ) -> int:
        counter = self.table.get(self.key(history, bit_pos, partial_len, partial_prefix))
        if counter is None:
            return TOTAL // 2
        total = counter.total
        denom = 2 * total + 2 * alpha2
        numer = (2 * counter.ones + alpha2) * TOTAL
        return clamp_p1(numer // denom)

    def update(self, history: bytes, bit_pos: int, partial_len: int, partial_prefix: int, bit: int) -> None:
        self.table.update(self.key(history, bit_pos, partial_len, partial_prefix), bit)


@dataclass
class BoundedByteTable:
    """Bounded LRU table from causal sketch keys to observed next-byte counts."""

    cap_entries: int
    counters: dict[tuple[Any, ...], Counter[int]] = field(default_factory=dict)
    order: list[tuple[Any, ...]] = field(default_factory=list)
    cursor: int = 0

    def get(self, key: tuple[Any, ...]) -> Counter[int] | None:
        return self.counters.get(key)

    def update(self, key: tuple[Any, ...], byte_value: int) -> None:
        counter = self.counters.get(key)
        if counter is None:
            if self.cap_entries > 0 and len(self.counters) >= self.cap_entries:
                while self.cursor < len(self.order):
                    old = self.order[self.cursor]
                    self.cursor += 1
                    if old in self.counters:
                        del self.counters[old]
                        break
                if self.cursor > 4096 and self.cursor * 2 > len(self.order):
                    self.order = self.order[self.cursor :]
                    self.cursor = 0
            counter = Counter()
            self.counters[key] = counter
            self.order.append(key)
        counter[byte_value & 0xFF] += 1


def make_byte_keys(features: dict[str, Any]) -> list[tuple[Any, ...]]:
    return [
        ("byte_suffix", features["suffix_hash"]),
        ("byte_sim0", features["sim_band0"]),
        ("byte_sim1", features["sim_band1"]),
        ("byte_schema", features["schema_hash"]),
        ("byte_hybrid", features["field"], features["mode"], features["sim_band0"]),
        (
            "byte_schema_word",
            features["schema_hash"],
            features["word_len_bucket"],
            features["word_class"],
        ),
    ]


def byte_prior_p1(
    table: BoundedByteTable,
    keys: list[tuple[Any, ...]],
    partial_len: int,
    partial_prefix: int,
    min_support: int,
    alpha_num: int,
) -> tuple[int | None, int, int]:
    zeros = 0
    ones = 0
    hits = 0
    mask_shift = 8 - partial_len
    prefix = partial_prefix & ((1 << partial_len) - 1) if partial_len else 0
    for key in keys:
        counter = table.get(key)
        if counter is None:
            continue
        for byte_value, count in counter.items():
            if partial_len and (byte_value >> mask_shift) != prefix:
                continue
            bit = (byte_value >> (7 - partial_len)) & 1
            if bit:
                ones += count
            else:
                zeros += count
            hits += count
    total = zeros + ones
    if total < min_support:
        return None, hits, total
    denom = 2 * total + 2 * alpha_num
    numer = (2 * ones + alpha_num) * TOTAL
    return clamp_p1(numer // denom), hits, total


def iter_raw_bits(data: bytes, limit_bytes: int) -> tuple[int, int, int]:
    end = len(data) if limit_bytes <= 0 else min(len(data), limit_bytes)
    for pos in range(end):
        byte = data[pos]
        for bit_pos in range(8):
            yield pos, bit_pos, (byte >> (7 - bit_pos)) & 1


def split_for(pos: int, train_bytes: int) -> str:
    if train_bytes <= 0:
        return "all"
    return "train" if pos < train_bytes else "test"


def run(args: argparse.Namespace) -> dict[str, Any]:
    data = args.data.read_bytes()
    if args.limit_bytes > 0:
        data = data[: args.limit_bytes]

    state = RetrievalState(data=data, suffix_len=args.suffix_len, sketch_len=args.sketch_len)
    partial_state = PartialByteState()
    base_model = RawContextModel(
        cap_entries=args.base_table_cap_entries,
        p_buckets=args.p_buckets,
        order=args.base_order,
    )
    retrieval_table = BoundedCounterTable(cap_entries=args.retrieval_table_cap_entries)
    byte_table = BoundedByteTable(cap_entries=args.byte_table_cap_entries)
    router = BandRouter(decay_shift=args.router_decay_shift)

    baseline = BinaryArithmeticEncoder()
    candidate = BinaryArithmeticEncoder()
    heldout_baseline = BinaryArithmeticEncoder()
    heldout_candidate = BinaryArithmeticEncoder()

    totals = {name: SplitTotals() for name in ("train", "test", "all")}
    block_qbits: dict[int, SplitTotals] = {}
    selected_band_counts: Counter[str] = Counter()

    encoded_rows = 0
    retrieval_rows = 0
    retrieval_hits = 0
    byte_prior_rows = 0
    byte_prior_hits = 0
    partial_key_rows = 0

    for pos, bit_pos, bit in iter_raw_bits(data, args.limit_bytes):
        if args.max_rows > 0 and encoded_rows >= args.max_rows:
            break
        state.advance_to(pos)
        features = state.features()
        partial_len, partial_prefix = partial_state.advance_to(pos, bit_pos)
        history = bytes(state.tail)
        base_p1 = base_model.predict(
            history,
            bit_pos,
            partial_len,
            partial_prefix,
            args.alpha2,
        )
        keys = make_keys(
            features,
            bit_pos,
            base_p1,
            args.p_buckets,
            partial_len,
            partial_prefix,
            args.partial_byte_family,
        )
        byte_keys = make_byte_keys(features)

        selected_band: str | None = None
        if args.expert_mode in {"best_band", "best_band_abstain"}:
            band_candidates, hits, _support = band_retrieval_p1(
                retrieval_table,
                keys,
                min_support=args.min_support,
                alpha_num=args.alpha2,
            )
            corrected_p1, selected_band = router.choose(
                band_candidates,
                base_p1,
                args.blend_ppm,
                args.expert_mode == "best_band_abstain",
                args.router_abstain_margin_qbits,
            )
            prior_used = selected_band not in {None, "base"}
        else:
            prior_p1, hits, _support = retrieval_p1(
                retrieval_table,
                keys,
                min_support=args.min_support,
                alpha_num=args.alpha2,
            )
            corrected_p1 = blend_probability(base_p1, prior_p1, args.blend_ppm)
            prior_used = prior_p1 is not None

        byte_prior, byte_hits, _byte_support = byte_prior_p1(
            byte_table,
            byte_keys,
            partial_len,
            partial_prefix,
            min_support=args.byte_min_support,
            alpha_num=args.alpha2,
        )
        if args.byte_prior_blend_ppm > 0:
            corrected_p1 = blend_probability(corrected_p1, byte_prior, args.byte_prior_blend_ppm)

        baseline.encode(bit, base_p1)
        candidate.encode(bit, corrected_p1)
        split = split_for(pos, args.train_bytes)
        if split == "test":
            heldout_baseline.encode(bit, base_p1)
            heldout_candidate.encode(bit, corrected_p1)

        if prior_used:
            retrieval_rows += 1
            retrieval_hits += hits
        if byte_prior is not None:
            byte_prior_rows += 1
            byte_prior_hits += byte_hits
        if selected_band is not None:
            selected_band_counts[selected_band] += 1
        if partial_len > 0 and args.partial_byte_family != "none":
            partial_key_rows += 1

        base_qbits = qbits_for(bit, base_p1)
        candidate_qbits = qbits_for(bit, corrected_p1)
        for name in (split, "all"):
            total = totals[name]
            total.rows += 1
            total.baseline_qbits += base_qbits
            total.candidate_qbits += candidate_qbits
            if split == "all":
                break
        block = block_qbits.setdefault(block_id(pos, args.block_bytes), SplitTotals())
        block.rows += 1
        block.baseline_qbits += base_qbits
        block.candidate_qbits += candidate_qbits

        base_model.update(history, bit_pos, partial_len, partial_prefix, bit)
        for key in keys:
            retrieval_table.update(key, bit)
        if args.expert_mode in {"best_band", "best_band_abstain"}:
            router.update(bit, band_candidates, base_p1, args.blend_ppm)
        partial_state.observe(pos, bit)
        if partial_state.length == 8:
            for key in byte_keys:
                byte_table.update(key, partial_state.prefix)
        encoded_rows += 1

    baseline.finish()
    candidate.finish()
    heldout_rows = totals["test"].rows
    if heldout_rows:
        heldout_baseline.finish()
        heldout_candidate.finish()

    block_rows = []
    largest_regression = 0.0
    positive_block_count = 0
    block_regression_count = 0
    positive_block_gain_bytes = 0.0
    for bid, total in sorted(block_qbits.items()):
        gain_bytes = total.gain_bytes
        if gain_bytes < 0:
            largest_regression = max(largest_regression, -gain_bytes)
            block_regression_count += 1
        elif gain_bytes > 0:
            positive_block_count += 1
            positive_block_gain_bytes += gain_bytes
        block_rows.append({"block_id": bid, "rows": total.rows, "gain_bytes": gain_bytes})
    block_rows.sort(key=lambda item: item["gain_bytes"])

    heldout_saved_bytes = (
        heldout_baseline.byte_count - heldout_candidate.byte_count if heldout_rows else None
    )
    shadow_saved_bytes = baseline.byte_count - candidate.byte_count
    net_saved_bytes = (
        heldout_saved_bytes
        - args.added_code_bytes_estimate
        - args.added_static_table_bytes
        if heldout_saved_bytes is not None
        else None
    )
    if encoded_rows == 0:
        verdict = "incomplete"
    elif net_saved_bytes is not None and net_saved_bytes > 0:
        verdict = "positive_shadow_only"
    elif heldout_saved_bytes is not None and heldout_saved_bytes > 0:
        verdict = "positive_shadow_only"
    elif heldout_saved_bytes is None and shadow_saved_bytes > 0:
        verdict = "positive_shadow_only"
    elif heldout_saved_bytes is not None and heldout_saved_bytes < 0:
        verdict = "negative_shadow"
    elif heldout_saved_bytes == 0:
        verdict = "flat_shadow"
    else:
        verdict = "incomplete"

    bands = ["suffix", "sim0", "sim1", "schema", "hybrid"]
    if args.partial_byte_family in {"direct", "all"}:
        bands.extend(["partial", "partial_pbin", "partial_mode", "partial_field"])
    if args.partial_byte_family in {"sketch", "all"}:
        bands.extend(["partial_suffix", "partial_sim0", "partial_schema", "partial_hybrid"])

    sketch_schema = {
        "feature_source": "raw_data",
        "suffix_len": args.suffix_len,
        "sketch_len": args.sketch_len,
        "p_buckets": args.p_buckets,
        "min_support": args.min_support,
        "blend_ppm": args.blend_ppm,
        "base_order": args.base_order,
        "base_table_cap_entries": args.base_table_cap_entries,
        "retrieval_table_cap_entries": args.retrieval_table_cap_entries,
        "byte_table_cap_entries": args.byte_table_cap_entries,
        "partial_byte_family": args.partial_byte_family,
        "byte_prior_blend_ppm": args.byte_prior_blend_ppm,
        "byte_min_support": args.byte_min_support,
        "expert_mode": args.expert_mode,
        "router_decay_shift": args.router_decay_shift,
        "router_abstain_margin_qbits": args.router_abstain_margin_qbits,
        "bands": bands,
    }
    sketch_schema_hash = hashlib.sha256(
        json.dumps(sketch_schema, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return {
        "receipt_type": "streaming_retrieval_shadow",
        "trace_version": "raw_enwik9_bits_msb_v1",
        "method": "streaming_retrieval_raw_shadow_v1",
        "base_trace": "raw_enwik9_bits_msb",
        "data": str(args.data),
        "data_sha256": hashlib.sha256(data).hexdigest(),
        "data_bytes_loaded": len(data),
        "scope_bytes": args.scope_bytes,
        "target": {
            "baseline_score": args.baseline_score,
            "target_score": args.target_score,
            "required_net_gain_bytes": args.baseline_score - args.target_score,
        },
        "position_span": {"min_pos": 0 if encoded_rows else None, "max_pos": (encoded_rows - 1) // 8 if encoded_rows else None},
        "rows": encoded_rows,
        "encoded_rows": encoded_rows,
        "ignored_rows": 0,
        "train_bytes": args.train_bytes,
        "feature_source": "raw_data",
        "trace_data_alignment": {
            "complete_bytes_checked": min(len(data), args.limit_bytes if args.limit_bytes > 0 else len(data)),
            "best_order": "msb",
            "best_match_rate": 1.0,
            "warning": None,
        },
        "sketch_schema": sketch_schema,
        "sketch_schema_hash": sketch_schema_hash,
        "retrieval_table_cap_entries": args.retrieval_table_cap_entries,
        "retrieved_neighbors_per_bit": {
            "retrieval_rows": retrieval_rows,
            "mean_hits_when_used": retrieval_hits / retrieval_rows if retrieval_rows else 0.0,
            "partial_key_rows": partial_key_rows,
            "byte_prior_rows": byte_prior_rows,
            "mean_byte_hits_when_used": byte_prior_hits / byte_prior_rows if byte_prior_rows else 0.0,
            "selected_band_counts": dict(sorted(selected_band_counts.items())),
            "router_base_loss_qbits": router.base_loss_qbits,
            "router_loss_qbits": dict(sorted(router.losses_qbits.items())),
            "router_regret_qbits": dict(sorted(router.regrets_qbits.items())),
        },
        "base_shadow_bytes": baseline.byte_count,
        "candidate_shadow_bytes": candidate.byte_count,
        "shadow_saved_bytes": shadow_saved_bytes,
        "heldout_shadow_bytes": heldout_candidate.byte_count if heldout_rows else None,
        "heldout_base_shadow_bytes": heldout_baseline.byte_count if heldout_rows else None,
        "heldout_shadow_saved_bytes": heldout_saved_bytes,
        "added_code_bytes_estimate": args.added_code_bytes_estimate,
        "added_static_table_bytes": args.added_static_table_bytes,
        "max_online_state_bytes": (
            args.base_table_cap_entries * 32
            + args.retrieval_table_cap_entries * 32
            + args.byte_table_cap_entries * 96
        ),
        "largest_block_regression_bytes": largest_regression,
        "block_regression_count": block_regression_count,
        "positive_block_count": positive_block_count,
        "positive_block_gain_bytes": positive_block_gain_bytes,
        "positive_block_gain_share": (
            positive_block_gain_bytes / shadow_saved_bytes
            if shadow_saved_bytes > 0
            else None
        ),
        "net_saved_bytes": net_saved_bytes,
        "block_rows": block_rows,
        "split_qbit_totals": {
            name: {
                "rows": total.rows,
                "gain_bits": total.gain_bits,
                "gain_bytes": total.gain_bytes,
            }
            for name, total in totals.items()
        },
        "worst_blocks_by_qbit_loss": block_rows[:10],
        "exact_shadow_arithmetic": {
            "baseline_same_coder": {
                "encoded_bits": baseline.bit_count,
                "archive_bytes": baseline.byte_count,
            },
            "shadow_coder": {
                "encoded_bits": candidate.bit_count,
                "archive_bytes": candidate.byte_count,
            },
            "same_coder_delta": {
                "saved_bits": baseline.bit_count - candidate.bit_count,
                "saved_bytes": shadow_saved_bytes,
            },
            "heldout_same_coder_delta": {
                "saved_bits": heldout_baseline.bit_count - heldout_candidate.bit_count
                if heldout_rows
                else None,
                "saved_bytes": heldout_saved_bytes,
            },
        },
        "causality": (
            "raw bits are emitted MSB-first from data bytes; all base and retrieval "
            "counters are updated only after encoding the current bit"
        ),
        "verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a raw byte-aligned SRSTC shadow probe.")
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--limit-bytes", type=int, default=64_000)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--train-bytes", type=int, default=8_000)
    parser.add_argument("--suffix-len", type=int, default=32)
    parser.add_argument("--sketch-len", type=int, default=96)
    parser.add_argument("--base-order", type=int, default=2)
    parser.add_argument("--p-buckets", type=int, default=32)
    parser.add_argument("--min-support", type=int, default=8)
    parser.add_argument("--blend-ppm", type=int, default=10_000)
    parser.add_argument("--alpha2", type=int, default=1)
    parser.add_argument("--base-table-cap-entries", type=int, default=200_000)
    parser.add_argument("--retrieval-table-cap-entries", type=int, default=200_000)
    parser.add_argument("--byte-table-cap-entries", type=int, default=100_000)
    parser.add_argument(
        "--partial-byte-family",
        choices=("none", "sketch", "direct", "all"),
        default="sketch",
    )
    parser.add_argument(
        "--expert-mode",
        choices=("aggregate", "best_band", "best_band_abstain"),
        default="best_band_abstain",
    )
    parser.add_argument("--byte-prior-blend-ppm", type=int, default=0)
    parser.add_argument("--byte-min-support", type=int, default=4)
    parser.add_argument("--router-decay-shift", type=int, default=6)
    parser.add_argument("--router-abstain-margin-qbits", type=int, default=128)
    parser.add_argument("--block-bytes", type=int, default=16_384)
    parser.add_argument("--scope-bytes", type=int, default=DEFAULT_SCOPE_BYTES)
    parser.add_argument("--baseline-score", type=int, default=DEFAULT_BASELINE_SCORE)
    parser.add_argument("--target-score", type=int, default=DEFAULT_TARGET_SCORE)
    parser.add_argument("--added-code-bytes-estimate", type=int, default=12_288)
    parser.add_argument("--added-static-table-bytes", type=int, default=0)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"missing data: {args.data}")
    if args.limit_bytes <= 0:
        raise SystemExit("--limit-bytes must be positive")
    if args.train_bytes < 0:
        raise SystemExit("--train-bytes must be nonnegative")
    if args.base_order < 0:
        raise SystemExit("--base-order must be nonnegative")
    if args.p_buckets <= 0 or args.min_support <= 0:
        raise SystemExit("--p-buckets and --min-support must be positive")
    if args.base_table_cap_entries <= 0 or args.retrieval_table_cap_entries <= 0:
        raise SystemExit("table caps must be positive")
    if args.byte_table_cap_entries <= 0 or args.byte_min_support <= 0:
        raise SystemExit("byte table cap and byte min support must be positive")
    if args.byte_prior_blend_ppm < 0 or args.byte_prior_blend_ppm > 1_000_000:
        raise SystemExit("--byte-prior-blend-ppm must be between 0 and 1000000")
    if args.router_decay_shift < 0 or args.router_abstain_margin_qbits < 0:
        raise SystemExit("router settings must be nonnegative")

    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(f"encoded_rows={result['encoded_rows']}")
        print(f"shadow_saved_bytes={result['shadow_saved_bytes']}")
        print(f"heldout_shadow_saved_bytes={result['heldout_shadow_saved_bytes']}")
        print(f"net_saved_bytes={result['net_saved_bytes']}")
        print(f"verdict={result['verdict']}")
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
