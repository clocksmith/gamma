#!/usr/bin/env python3
"""Search fixed-point sphere/torus residual buckets for fx2 outer SSE.

This is the offline half of the manifold plan. It consumes raw
FX2_RESIDUAL_ROW logs, builds deterministic integer projections from causal
wiki/XML state into a small manifold bucket, and scores a tiny causal KT
correction table keyed by:

    p_bucket x bit_pos x manifold_bucket

The search may be stochastic through seeded projection generation, but every
candidate it emits is a frozen integer rule suitable for a deterministic C++
outer SSE/APM patch. Counters update only after the current bit is scored.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterable


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "manifold_outer_sse_search.json"

PAIR_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([^ \t]+)")
FX2_PREFIX = "FX2_RESIDUAL_ROW "
TOTAL = 1 << 16
MAX_CODE = (1 << 32) - 1
HALF = 1 << 31
FIRST_QTR = 1 << 30
THIRD_QTR = FIRST_QTR * 3

DEFAULT_FEATURES = (
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
    "pos_phase",
)

SPHERE_FEATURES = {
    "field",
    "mode",
    "slot",
    "page_kind",
    "char_class",
    "number_class",
    "word_len",
    "title_hash",
    "template_hash",
    "link_hash",
    "entity_hash",
    "word_hash",
}
TORUS_FEATURES = {
    "bit_pos",
    "template_depth",
    "in_tag",
    "ref",
    "url",
    "col_bucket",
    "page_bucket",
    "category_state",
    "template_arg",
    "link_recency",
    "pair_sig",
    "pos_phase",
}


def parse_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def parse_line(line: str) -> dict[str, Any] | None:
    if FX2_PREFIX not in line:
        return None
    payload = line.split(FX2_PREFIX, 1)[1]
    pairs = PAIR_RE.findall(payload)
    if not pairs:
        return None
    return {key: parse_value(value) for key, value in pairs}


def iter_rows(path: pathlib.Path, max_rows: int = 0) -> Iterable[dict[str, Any]]:
    rows = 0
    with path.open("r", errors="replace") as f:
        for line in f:
            row = parse_line(line)
            if row is None:
                continue
            rows += 1
            yield row
            if max_rows > 0 and rows >= max_rows:
                return


def as_int(row: dict[str, Any], key: str, default: int = 0) -> int:
    value = row.get(key, default)
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp_p1(p1: int) -> int:
    return max(1, min(TOTAL - 1, int(p1)))


def prob_bucket(p1: int, buckets: int) -> int:
    if buckets <= 1:
        return 0
    return min(buckets - 1, (clamp_p1(p1) * buckets) >> 16)


def qbits_for(bit: int, p1: int | float) -> int:
    p1 = max(1.0, min(65535.0, float(p1)))
    prob = p1 / 65536.0 if bit else (65536.0 - p1) / 65536.0
    return int((-math.log2(prob)) * 256.0 + 0.5)


def mix32(x: int) -> int:
    x &= 0xFFFFFFFF
    x ^= x >> 16
    x = (x * 0x7FEB352D) & 0xFFFFFFFF
    x ^= x >> 15
    x = (x * 0x846CA68B) & 0xFFFFFFFF
    x ^= x >> 16
    return x & 0xFFFFFFFF


def xorshift32(x: int) -> int:
    x &= 0xFFFFFFFF
    x ^= (x << 13) & 0xFFFFFFFF
    x ^= x >> 17
    x ^= (x << 5) & 0xFFFFFFFF
    return x & 0xFFFFFFFF


def feature_value(row: dict[str, Any], name: str, pos_shift: int) -> int:
    if name == "bit_pos":
        return as_int(row, "bit_pos") & 7
    if name == "pos_phase":
        return (as_int(row, "pos") >> pos_shift) & 255
    if name == "depth_phase":
        return (as_int(row, "template_depth") + 3 * as_int(row, "slot")) & 31
    return as_int(row, name) & 1023


@dataclass(frozen=True)
class Projection:
    seed: int
    sphere_bins: int
    torus_bins: int
    pos_shift: int
    sphere_bias: int
    torus_bias: int
    weights: dict[str, int]

    @property
    def bucket_count(self) -> int:
        return self.sphere_bins * self.torus_bins

    @property
    def name(self) -> str:
        return (
            f"s{self.seed:x}_sph{self.sphere_bins}_tor{self.torus_bins}"
            f"_ps{self.pos_shift}"
        )

    def bucket(self, row: dict[str, Any]) -> int:
        sphere = self.sphere_bias
        torus = self.torus_bias
        for name, weight in self.weights.items():
            value = feature_value(row, name, self.pos_shift)
            term = (value + 1) * weight
            if name in TORUS_FEATURES:
                torus = (torus + term) & 0xFFFFFFFF
            if name in SPHERE_FEATURES or name not in TORUS_FEATURES:
                sphere = mix32(sphere ^ term)

        sphere_bucket = sphere % self.sphere_bins
        torus_bucket = mix32(torus) % self.torus_bins
        return sphere_bucket * self.torus_bins + torus_bucket

    def to_json(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "sphere_bins": self.sphere_bins,
            "torus_bins": self.torus_bins,
            "bucket_count": self.bucket_count,
            "pos_shift": self.pos_shift,
            "sphere_bias": self.sphere_bias,
            "torus_bias": self.torus_bias,
            "weights": self.weights,
            "fixed_point_rule": (
                "bucket = sphere_hash(causal_features) * torus_bins + "
                "torus_phase(causal_features)"
            ),
        }


def make_projection(
    *,
    seed: int,
    trial: int,
    features: tuple[str, ...],
    sphere_bins: int,
    torus_bins: int,
    pos_shift: int,
) -> Projection:
    state = mix32(seed ^ (trial * 0x9E3779B9) ^ (sphere_bins << 8) ^ torus_bins)
    weights: dict[str, int] = {}
    for name in features:
        state = xorshift32(state or 0xA5A5A5A5)
        weights[name] = (state | 1) & 0xFFFF
    state = xorshift32(state)
    sphere_bias = state
    state = xorshift32(state)
    torus_bias = state
    return Projection(
        seed=mix32(seed ^ trial),
        sphere_bins=sphere_bins,
        torus_bins=torus_bins,
        pos_shift=pos_shift,
        sphere_bias=sphere_bias,
        torus_bias=torus_bias,
        weights=weights,
    )


@dataclass
class Counter:
    zeros: int = 0
    ones: int = 0
    residual_sum: int = 0

    def kt_p1(self) -> int:
        denom = 2 * (self.zeros + self.ones + 1)
        numer = (2 * self.ones + 1) * TOTAL
        return clamp_p1(numer // denom)

    def bias_p1(self, base_p1: int, blend_ppm: int) -> int:
        count = self.zeros + self.ones
        if count <= 0:
            return base_p1
        mean_delta = self.residual_sum / count
        corrected = base_p1 + (mean_delta * blend_ppm) / 1_000_000.0
        return clamp_p1(int(corrected + (0.5 if corrected >= 0 else -0.5)))

    def update(self, bit: int, base_p1: int = 32768) -> None:
        if bit:
            self.ones += 1
            self.residual_sum += TOTAL - base_p1
        else:
            self.zeros += 1
            self.residual_sum -= base_p1


@dataclass
class Totals:
    rows: int = 0
    baseline_qbits: int = 0
    corrected_qbits: int = 0

    @property
    def gain_bits(self) -> float:
        return (self.baseline_qbits - self.corrected_qbits) / 256.0

    @property
    def gain_bytes(self) -> float:
        return self.gain_bits / 8.0

    @property
    def gain_bits_per_bit(self) -> float:
        return self.gain_bits / self.rows if self.rows else 0.0

    def to_json(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "baseline_bits": self.baseline_qbits / 256.0,
            "corrected_bits": self.corrected_qbits / 256.0,
            "gain_bits": self.gain_bits,
            "gain_bytes": self.gain_bytes,
            "gain_bits_per_bit": self.gain_bits_per_bit,
        }


@dataclass
class Model:
    projection: Projection
    p_buckets: int
    blend_ppm: int
    correction: str
    counters: dict[tuple[int, int, int], Counter] = field(default_factory=dict)
    totals: dict[str, Totals] = field(
        default_factory=lambda: {"train": Totals(), "test": Totals(), "all": Totals()}
    )

    def update(self, row: dict[str, Any], train_bytes: int) -> None:
        bit = as_int(row, "bit", -1)
        if bit not in {0, 1}:
            return
        base_p1 = clamp_p1(as_int(row, "p1", 32768))
        bit_pos = as_int(row, "bit_pos") & 7
        key = (
            prob_bucket(base_p1, self.p_buckets),
            bit_pos,
            self.projection.bucket(row),
        )
        counter = self.counters.setdefault(key, Counter())
        blend = max(0, min(1_000_000, self.blend_ppm))
        if self.correction == "bias":
            corrected_p1 = counter.bias_p1(base_p1, blend)
        else:
            kt_p1 = counter.kt_p1()
            corrected_p1 = clamp_p1(
                (base_p1 * (1_000_000 - blend) + kt_p1 * blend) // 1_000_000
            )
        base_qbits = as_int(row, "baseline_qbits", qbits_for(bit, base_p1))
        corrected_qbits = qbits_for(bit, corrected_p1)
        split = "train" if train_bytes > 0 and as_int(row, "pos") < train_bytes else "test"
        if train_bytes <= 0:
            split = "all"

        for name in ((split,) if split == "all" else (split, "all")):
            self.totals[name].rows += 1
            self.totals[name].baseline_qbits += base_qbits
            self.totals[name].corrected_qbits += corrected_qbits
        counter.update(bit, base_p1)

    def to_json(self) -> dict[str, Any]:
        return {
            "projection": self.projection.to_json(),
            "p_buckets": self.p_buckets,
            "blend_ppm": self.blend_ppm,
            "correction": self.correction,
            "unique_contexts": len(self.counters),
            "key": "p_bucket,bit_pos,manifold_bucket",
            "splits": {name: total.to_json() for name, total in self.totals.items()},
        }


class BitCounter:
    def __init__(self) -> None:
        self.bits = 0

    def write_bit(self, _bit: int) -> None:
        self.bits += 1

    @property
    def bytes(self) -> int:
        return (self.bits + 7) // 8


class BinaryArithmeticEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.high = MAX_CODE
        self.pending = 0
        self.out = BitCounter()

    def _bit_plus_follow(self, bit: int) -> None:
        self.out.write_bit(bit)
        while self.pending:
            self.out.write_bit(1 - bit)
            self.pending -= 1

    def encode(self, bit: int, p1: int) -> None:
        p1 = clamp_p1(p1)
        zeros = TOTAL - p1
        span = self.high - self.low + 1
        split = self.low + (span * zeros) // TOTAL
        if bit:
            self.low = split
        else:
            self.high = split - 1

        while True:
            if self.high < HALF:
                self._bit_plus_follow(0)
            elif self.low >= HALF:
                self._bit_plus_follow(1)
                self.low -= HALF
                self.high -= HALF
            elif self.low >= FIRST_QTR and self.high < THIRD_QTR:
                self.pending += 1
                self.low -= FIRST_QTR
                self.high -= FIRST_QTR
            else:
                break
            self.low = (self.low << 1) & MAX_CODE
            self.high = ((self.high << 1) & MAX_CODE) | 1

    def finish(self) -> None:
        self.pending += 1
        if self.low < FIRST_QTR:
            self._bit_plus_follow(0)
        else:
            self._bit_plus_follow(1)

    @property
    def bit_count(self) -> int:
        return self.out.bits

    @property
    def byte_count(self) -> int:
        return self.out.bytes


def exact_shadow(
    log: pathlib.Path,
    model_json: dict[str, Any],
    max_rows: int,
    train_bytes: int = 0,
) -> dict[str, Any]:
    projection_payload = model_json["projection"]
    projection = Projection(
        seed=int(projection_payload["seed"]),
        sphere_bins=int(projection_payload["sphere_bins"]),
        torus_bins=int(projection_payload["torus_bins"]),
        pos_shift=int(projection_payload["pos_shift"]),
        sphere_bias=int(projection_payload["sphere_bias"]),
        torus_bias=int(projection_payload["torus_bias"]),
        weights={k: int(v) for k, v in projection_payload["weights"].items()},
    )
    p_buckets = int(model_json["p_buckets"])
    blend_ppm = int(model_json["blend_ppm"])
    correction = str(model_json.get("correction", "kt"))
    counters: dict[tuple[int, int, int], Counter] = {}
    baseline = BinaryArithmeticEncoder()
    shadow = BinaryArithmeticEncoder()
    heldout_baseline = BinaryArithmeticEncoder()
    heldout_shadow = BinaryArithmeticEncoder()
    rows = 0
    heldout_rows = 0

    for row in iter_rows(log, max_rows=max_rows):
        bit = as_int(row, "bit", -1)
        if bit not in {0, 1}:
            continue
        base_p1 = clamp_p1(as_int(row, "p1", 32768))
        key = (
            prob_bucket(base_p1, p_buckets),
            as_int(row, "bit_pos") & 7,
            projection.bucket(row),
        )
        counter = counters.setdefault(key, Counter())
        if correction == "bias":
            corrected_p1 = counter.bias_p1(base_p1, blend_ppm)
        else:
            kt_p1 = counter.kt_p1()
            corrected_p1 = clamp_p1(
                (base_p1 * (1_000_000 - blend_ppm) + kt_p1 * blend_ppm) // 1_000_000
            )
        baseline.encode(bit, base_p1)
        shadow.encode(bit, corrected_p1)
        if train_bytes > 0 and as_int(row, "pos") >= train_bytes:
            heldout_baseline.encode(bit, base_p1)
            heldout_shadow.encode(bit, corrected_p1)
            heldout_rows += 1
        counter.update(bit, base_p1)
        rows += 1

    baseline.finish()
    shadow.finish()
    payload = {
        "encoded_rows": rows,
        "baseline_archive_bytes": baseline.byte_count,
        "shadow_archive_bytes": shadow.byte_count,
        "saved_bits": baseline.bit_count - shadow.bit_count,
        "saved_bytes": baseline.byte_count - shadow.byte_count,
        "unique_contexts": len(counters),
    }
    if heldout_rows > 0:
        heldout_baseline.finish()
        heldout_shadow.finish()
        payload["heldout_encoded_rows"] = heldout_rows
        payload["heldout_baseline_archive_bytes"] = heldout_baseline.byte_count
        payload["heldout_shadow_archive_bytes"] = heldout_shadow.byte_count
        payload["heldout_saved_bits"] = (
            heldout_baseline.bit_count - heldout_shadow.bit_count
        )
        payload["heldout_saved_bytes"] = (
            heldout_baseline.byte_count - heldout_shadow.byte_count
        )
    return payload


def parse_int_list(value: str) -> list[int]:
    return [int(part) for part in value.split(",") if part]


def run_search(args: argparse.Namespace) -> dict[str, Any]:
    features = tuple(args.feature) if args.feature else DEFAULT_FEATURES
    sphere_bins = parse_int_list(args.sphere_bins)
    torus_bins = parse_int_list(args.torus_bins)
    pos_shifts = parse_int_list(args.pos_shifts)
    blends = parse_int_list(args.blend_ppm)

    models: list[Model] = []
    trial = 0
    for trial_index in range(args.trials):
        for sph in sphere_bins:
            for tor in torus_bins:
                for pos_shift in pos_shifts:
                    projection = make_projection(
                        seed=args.seed,
                        trial=trial,
                        features=features,
                        sphere_bins=sph,
                        torus_bins=tor,
                        pos_shift=pos_shift,
                    )
                    for blend in blends:
                        models.append(
                            Model(
                                projection=projection,
                                p_buckets=args.p_buckets,
                                blend_ppm=blend,
                                correction=args.correction,
                            )
                        )
                    trial += 1
    if not models:
        raise SystemExit("no projection models generated")

    rows = 0
    exact_rows = 0
    for row in iter_rows(args.log, max_rows=args.max_rows):
        rows += 1
        if as_int(row, "bit", -1) in {0, 1} and as_int(row, "p1", -1) > 0:
            exact_rows += 1
        for model in models:
            model.update(row, args.train_bytes)

    rank_split = args.rank_split
    if args.train_bytes <= 0 and rank_split in {"train", "test"}:
        rank_split = "all"
    ranked = [model.to_json() for model in models]
    ranked.sort(
        key=lambda item: (
            -float(item["splits"][rank_split]["gain_bits"]),
            int(item["unique_contexts"]),
            item["projection"]["seed"],
            int(item["blend_ppm"]),
        )
    )
    top = ranked[: args.top]

    shadow_top = []
    for item in top[: args.shadow_top]:
        shadow = exact_shadow(args.log, item, args.max_rows, args.train_bytes)
        enriched = dict(item)
        enriched["exact_shadow_arithmetic"] = shadow
        shadow_top.append(enriched)

    shadow_ranked = []
    if args.shadow_rerank_top > 0:
        for item in ranked[: args.shadow_rerank_top]:
            shadow = exact_shadow(args.log, item, args.max_rows, args.train_bytes)
            enriched = dict(item)
            enriched["exact_shadow_arithmetic"] = shadow
            shadow_ranked.append(enriched)
        shadow_ranked.sort(
            key=lambda item: (
                -int(
                    item["exact_shadow_arithmetic"].get(
                        "heldout_saved_bits",
                        item["exact_shadow_arithmetic"]["saved_bits"],
                    )
                ),
                int(item["unique_contexts"]),
                item["projection"]["seed"],
                int(item["blend_ppm"]),
            )
        )

    required_net_gain_bytes = args.baseline_score - args.target_score
    return {
        "tool": "fx2_manifold_outer_sse_search.py",
        "input_log": str(args.log),
        "rows_seen": rows,
        "exact_rows": exact_rows,
        "features": list(features),
        "train_bytes": args.train_bytes,
        "rank_split": rank_split,
        "models_tested": len(ranked),
        "target": {
            "baseline_score": args.baseline_score,
            "target_score": args.target_score,
            "required_net_gain_bytes": required_net_gain_bytes,
            "required_net_gain_bits": required_net_gain_bytes * 8,
            "scope_bytes": args.scope_bytes,
            "linear_required_gain_bytes_at_scope": (
                required_net_gain_bytes * rows / (args.scope_bytes * 8)
                if args.scope_bytes > 0
                else None
            ),
        },
        "candidate_family": {
            "id": "fx2__manifold_outer_sse__sphere_torus_residual__v01",
            "key": "p_bucket,bit_pos,manifold_bucket",
            "causality": (
                "projection uses only fields present on FX2_RESIDUAL_ROW at the "
                "current bit boundary; counters update after the current bit"
            ),
            "online_form": "fixed-point integer projection plus tiny KT/APM table",
            "correction": args.correction,
        },
        "top": top,
        "shadow_top": shadow_top,
        "shadow_ranked": shadow_ranked,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=0x5EED1234)
    parser.add_argument("--trials", type=int, default=16)
    parser.add_argument("--sphere-bins", default="4,8")
    parser.add_argument("--torus-bins", default="4,8")
    parser.add_argument("--pos-shifts", default="8,10,12")
    parser.add_argument("--p-buckets", type=int, default=32)
    parser.add_argument("--blend-ppm", default="25000,50000,125000")
    parser.add_argument("--correction", choices=["kt", "bias"], default="kt")
    parser.add_argument("--train-bytes", type=int, default=0)
    parser.add_argument("--rank-split", choices=["all", "train", "test"], default="test")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--shadow-top", type=int, default=3)
    parser.add_argument(
        "--shadow-rerank-top",
        type=int,
        default=0,
        help="rerank this many proxy winners by exact shadow arithmetic",
    )
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--feature", action="append", default=[])
    parser.add_argument("--baseline-score", type=int, default=110_181_114)
    parser.add_argument("--target-score", type=int, default=108_000_000)
    parser.add_argument("--scope-bytes", type=int, default=1_000_000_000)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"missing log: {args.log}")
    if args.trials <= 0:
        raise SystemExit("--trials must be positive")
    if args.p_buckets <= 0:
        raise SystemExit("--p-buckets must be positive")
    if args.scope_bytes <= 0:
        raise SystemExit("--scope-bytes must be positive")

    payload = run_search(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(
            f"rows={payload['rows_seen']} exact_rows={payload['exact_rows']} "
            f"models={payload['models_tested']} rank_split={payload['rank_split']}"
        )
        for i, item in enumerate(payload["top"][:10], 1):
            split = item["splits"][payload["rank_split"]]
            proj = item["projection"]
            print(
                f"{i}. seed={proj['seed']} sph={proj['sphere_bins']} "
                f"tor={proj['torus_bins']} pos_shift={proj['pos_shift']} "
                f"blend={item['blend_ppm']} gain_bits={split['gain_bits']:.6f} "
                f"gain_bytes={split['gain_bytes']:.6f} "
                f"contexts={item['unique_contexts']}"
            )
        if payload["shadow_top"]:
            best = payload["shadow_top"][0]["exact_shadow_arithmetic"]
            print(
                "best_shadow_saved_bytes="
                f"{best['saved_bytes']} archive={best['shadow_archive_bytes']}"
            )
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
