#!/usr/bin/env python3
"""Offline I-SSA shadow search over fx2 residual logs.

This tests the Integer State-Space Attractor idea without running a compressor.
It consumes existing per-bit fx2 residual rows, keeps a tiny deterministic
integer state vector derived only from prior decoded bits/fields, and measures
whether that state improves an exact binary arithmetic shadow coder.

The correction is deliberately conservative: a causal residual-bias table keyed
by p_bucket, bit_pos, and the attractor bucket. Counters update only after the
current bit is encoded.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from dataclasses import dataclass
from typing import Any, Iterable

from fx2_shadow_residual_coder import (
    BinaryArithmeticEncoder,
    TOTAL,
    as_int,
    clamp_p1,
    iter_rows,
    prob_bucket,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "issa_shadow_search.json"


def clip_i8(value: int) -> int:
    return max(-128, min(127, value))


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


def signed_weight(seed: int, span: int) -> tuple[int, int]:
    seed = xorshift32(seed)
    return (seed % (2 * span + 1)) - span, seed


def iter_limited_rows(path: pathlib.Path, max_rows: int) -> Iterable[dict[str, Any]]:
    rows = 0
    for row in iter_rows(path):
        bit = as_int(row, "bit", default=-1)
        p1 = as_int(row, "p1", default=0)
        if bit not in (0, 1) or not (0 < p1 < TOTAL):
            continue
        rows += 1
        yield row
        if max_rows > 0 and rows >= max_rows:
            return


def load_rows(path: pathlib.Path, max_rows: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_limited_rows(path, max_rows):
        bit = as_int(row, "bit", default=-1)
        p1 = as_int(row, "p1", default=0)
        if bit in (0, 1) and 0 < p1 < TOTAL:
            rows.append(row)
    return rows


@dataclass(frozen=True)
class IssaProjection:
    seed: int
    state_count: int
    state_buckets: int
    p_buckets: int
    shift: int
    a: tuple[tuple[int, ...], ...]
    b: tuple[tuple[int, ...], ...]
    bias: tuple[int, ...]

    @staticmethod
    def build(
        seed: int,
        state_count: int,
        state_buckets: int,
        p_buckets: int,
        shift: int,
        weight_span: int,
    ) -> "IssaProjection":
        rng = mix32(seed)
        a_rows: list[tuple[int, ...]] = []
        b_rows: list[tuple[int, ...]] = []
        bias: list[int] = []
        for i in range(state_count):
            a_row: list[int] = []
            for j in range(state_count):
                if i == j:
                    weight = (1 << shift) - 1
                else:
                    weight, rng = signed_weight(rng + i * 17 + j, weight_span)
                a_row.append(weight)
            b_row: list[int] = []
            for j in range(8):
                weight, rng = signed_weight(rng + i * 31 + j * 7, weight_span)
                b_row.append(weight)
            offset, rng = signed_weight(rng + i * 101, 32)
            bias.append(offset)
            a_rows.append(tuple(a_row))
            b_rows.append(tuple(b_row))
        return IssaProjection(
            seed=seed,
            state_count=state_count,
            state_buckets=state_buckets,
            p_buckets=p_buckets,
            shift=shift,
            a=tuple(a_rows),
            b=tuple(b_rows),
            bias=tuple(bias),
        )

    def features(self, row: dict[str, Any], bit: int, p1: int) -> tuple[int, ...]:
        return (
            1 if bit else -1,
            (as_int(row, "bit_pos", default=0) & 7) - 3,
            prob_bucket(p1, self.p_buckets) - (self.p_buckets // 2),
            (as_int(row, "field", default=0) & 15) - 7,
            (as_int(row, "mode", default=0) & 15) - 7,
            (as_int(row, "char_class", default=0) & 15) - 7,
            (as_int(row, "template_depth", default=0) & 15) - 3,
            (as_int(row, "word_len", default=0) & 31) - 8,
        )

    def update(self, state: tuple[int, ...], row: dict[str, Any], bit: int, p1: int) -> tuple[int, ...]:
        x = self.features(row, bit, p1)
        out: list[int] = []
        for i in range(self.state_count):
            acc = self.bias[i]
            for j, value in enumerate(state):
                acc += self.a[i][j] * value
            for j, value in enumerate(x):
                acc += self.b[i][j] * value
            out.append(clip_i8(acc >> self.shift))
        return tuple(out)

    def bucket(self, state: tuple[int, ...]) -> int:
        h = mix32(self.seed ^ 0x9E3779B9)
        for i, value in enumerate(state):
            h = mix32(h ^ ((value + 128 + 257 * i) * 0x45D9F3B))
        return h % self.state_buckets

    def to_json(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "state_count": self.state_count,
            "state_buckets": self.state_buckets,
            "p_buckets": self.p_buckets,
            "shift": self.shift,
            "a": self.a,
            "b": self.b,
            "bias": self.bias,
        }


@dataclass
class BiasCounter:
    count: int = 0
    residual_sum: int = 0

    def correction(self, p1: int, blend_ppm: int) -> int:
        if self.count <= 0 or blend_ppm <= 0:
            return p1
        delta = (self.residual_sum * blend_ppm) // (self.count * 1_000_000)
        return clamp_p1(p1 + delta)

    def update(self, bit: int, p1: int) -> None:
        if bit:
            self.residual_sum += TOTAL - p1
        else:
            self.residual_sum -= p1
        self.count += 1


@dataclass
class TrialResult:
    projection: IssaProjection
    rows: int
    baseline_bits: int
    shadow_bits: int
    baseline_bytes: int
    shadow_bytes: int
    heldout_rows: int
    heldout_baseline_bits: int
    heldout_shadow_bits: int
    heldout_baseline_bytes: int
    heldout_shadow_bytes: int

    @property
    def saved_bits(self) -> int:
        return self.baseline_bits - self.shadow_bits

    @property
    def saved_bytes(self) -> int:
        return self.baseline_bytes - self.shadow_bytes

    @property
    def heldout_saved_bits(self) -> int:
        return self.heldout_baseline_bits - self.heldout_shadow_bits

    @property
    def heldout_saved_bytes(self) -> int:
        return self.heldout_baseline_bytes - self.heldout_shadow_bytes

    def sort_key(self) -> tuple[int, int, int]:
        return (self.heldout_saved_bits, self.saved_bits, -self.shadow_bits)

    def to_json(self) -> dict[str, Any]:
        return {
            "projection": self.projection.to_json(),
            "rows": self.rows,
            "baseline_bits": self.baseline_bits,
            "shadow_bits": self.shadow_bits,
            "saved_bits": self.saved_bits,
            "baseline_bytes": self.baseline_bytes,
            "shadow_bytes": self.shadow_bytes,
            "saved_bytes": self.saved_bytes,
            "heldout_rows": self.heldout_rows,
            "heldout_baseline_bits": self.heldout_baseline_bits,
            "heldout_shadow_bits": self.heldout_shadow_bits,
            "heldout_saved_bits": self.heldout_saved_bits,
            "heldout_baseline_bytes": self.heldout_baseline_bytes,
            "heldout_shadow_bytes": self.heldout_shadow_bytes,
            "heldout_saved_bytes": self.heldout_saved_bytes,
        }


def is_heldout(row: dict[str, Any], row_index: int, train_bytes: int, train_rows: int) -> bool:
    if train_bytes > 0:
        return as_int(row, "pos", default=0) >= train_bytes
    if train_rows > 0:
        return row_index > train_rows
    return False


def score_projection(
    rows_in: list[dict[str, Any]],
    projection: IssaProjection,
    blend_ppm: int,
    train_bytes: int,
    train_rows: int,
) -> TrialResult:
    baseline = BinaryArithmeticEncoder()
    shadow = BinaryArithmeticEncoder()
    heldout_baseline = BinaryArithmeticEncoder()
    heldout_shadow = BinaryArithmeticEncoder()
    table: dict[tuple[int, int, int], BiasCounter] = {}
    state = tuple(0 for _ in range(projection.state_count))
    rows = 0
    heldout_rows = 0

    for row in rows_in:
        bit = as_int(row, "bit", default=0)
        p1 = clamp_p1(as_int(row, "p1", default=0))
        row_index = rows + 1
        heldout = is_heldout(row, row_index, train_bytes, train_rows)
        key = (
            prob_bucket(p1, projection.p_buckets),
            as_int(row, "bit_pos", default=0) & 7,
            projection.bucket(state),
        )
        counter = table.get(key)
        corrected_p1 = counter.correction(p1, blend_ppm) if counter is not None else p1

        baseline.encode(bit, p1)
        shadow.encode(bit, corrected_p1)
        if heldout:
            heldout_rows += 1
            heldout_baseline.encode(bit, p1)
            heldout_shadow.encode(bit, corrected_p1)

        if counter is None:
            counter = BiasCounter()
            table[key] = counter
        counter.update(bit, p1)
        state = projection.update(state, row, bit, p1)
        rows += 1

    baseline.finish()
    shadow.finish()
    if heldout_rows:
        heldout_baseline.finish()
        heldout_shadow.finish()

    return TrialResult(
        projection=projection,
        rows=rows,
        baseline_bits=baseline.bit_count,
        shadow_bits=shadow.bit_count,
        baseline_bytes=baseline.byte_count,
        shadow_bytes=shadow.byte_count,
        heldout_rows=heldout_rows,
        heldout_baseline_bits=heldout_baseline.bit_count if heldout_rows else 0,
        heldout_shadow_bits=heldout_shadow.bit_count if heldout_rows else 0,
        heldout_baseline_bytes=heldout_baseline.byte_count if heldout_rows else 0,
        heldout_shadow_bytes=heldout_shadow.byte_count if heldout_rows else 0,
    )


def run_search(args: argparse.Namespace) -> dict[str, Any]:
    path = pathlib.Path(args.residual_log)
    rows = load_rows(path, args.max_rows)
    results: list[TrialResult] = []
    for trial in range(args.trials):
        seed = mix32(args.seed + trial * 0x9E3779B9)
        projection = IssaProjection.build(
            seed=seed,
            state_count=args.state_count,
            state_buckets=args.state_buckets,
            p_buckets=args.p_buckets,
            shift=args.shift,
            weight_span=args.weight_span,
        )
        results.append(
            score_projection(
                rows_in=rows,
                projection=projection,
                blend_ppm=args.blend_ppm,
                train_bytes=args.train_bytes,
                train_rows=args.train_rows,
            )
        )
    results.sort(key=lambda result: result.sort_key(), reverse=True)
    return {
        "input": str(path),
        "method": "issa_residual_bias_shadow",
        "rows_scored": results[0].rows if results else 0,
        "params": {
            "trials": args.trials,
            "seed": args.seed,
            "state_count": args.state_count,
            "state_buckets": args.state_buckets,
            "p_buckets": args.p_buckets,
            "shift": args.shift,
            "weight_span": args.weight_span,
            "blend_ppm": args.blend_ppm,
            "train_bytes": args.train_bytes,
            "train_rows": args.train_rows,
            "max_rows": args.max_rows,
        },
        "best": results[0].to_json() if results else None,
        "top": [result.to_json() for result in results[: args.top]],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search tiny integer state-space attractors over fx2 residual logs."
    )
    parser.add_argument("residual_log")
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    parser.add_argument("--trials", type=int, default=32)
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0x51A7E)
    parser.add_argument("--state-count", type=int, default=4)
    parser.add_argument("--state-buckets", type=int, default=64)
    parser.add_argument("--p-buckets", type=int, default=16)
    parser.add_argument("--shift", type=int, default=4)
    parser.add_argument("--weight-span", type=int, default=3)
    parser.add_argument("--blend-ppm", type=int, default=50_000)
    parser.add_argument("--train-bytes", type=int, default=0)
    parser.add_argument("--train-rows", type=int, default=0)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if args.trials <= 0:
        raise SystemExit("--trials must be positive")
    if args.top <= 0:
        raise SystemExit("--top must be positive")
    if args.state_count <= 0 or args.state_count > 8:
        raise SystemExit("--state-count must be between 1 and 8")
    if args.state_buckets <= 0:
        raise SystemExit("--state-buckets must be positive")
    if args.p_buckets <= 0:
        raise SystemExit("--p-buckets must be positive")
    if args.shift <= 0:
        raise SystemExit("--shift must be positive")
    if args.weight_span < 0:
        raise SystemExit("--weight-span must be non-negative")
    if args.blend_ppm < 0 or args.blend_ppm > 1_000_000:
        raise SystemExit("--blend-ppm must be between 0 and 1000000")

    payload = run_search(args)
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        best = payload.get("best")
        if best is None or best.get("rows", 0) <= 0:
            print(json.dumps({"status": "no_rows"}))
        else:
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "rows": best["rows"],
                        "saved_bits": best["saved_bits"],
                        "saved_bytes": best["saved_bytes"],
                        "heldout_rows": best["heldout_rows"],
                        "heldout_saved_bits": best["heldout_saved_bits"],
                        "heldout_saved_bytes": best["heldout_saved_bytes"],
                        "seed": best["projection"]["seed"],
                    },
                    sort_keys=True,
                )
            )


if __name__ == "__main__":
    main()
