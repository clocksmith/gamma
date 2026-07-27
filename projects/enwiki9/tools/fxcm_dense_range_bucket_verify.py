#!/usr/bin/env python3
"""Finite verifier for the DRB-1 dense range-bucket construction."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Config:
    w: int
    n: int
    cell_bytes: int
    usable_bytes: int
    guard_cells: int
    alignment_bytes: int
    add: int
    mul1: int
    mul2: int
    shift1: int
    shift2: int
    shift3: int
    salt: int


def xorshift_right(value: int, shift: int, mask: int) -> int:
    return (value ^ (value >> shift)) & mask


def permute(value: int, config: Config) -> int:
    mask = (1 << config.w) - 1
    value = (value + config.add) & mask
    value = xorshift_right(value, config.shift1, mask)
    value = (value * config.mul1) & mask
    value = xorshift_right(value, config.shift2, mask)
    value = (value * config.mul2) & mask
    return xorshift_right(value, config.shift3, mask)


def bucket(value: int, config: Config) -> int:
    q = 1 << config.w
    mask = q - 1
    mixed = permute((value + config.salt) & mask, config)
    return (mixed * config.n) >> config.w


def verify(config: Config, enumerate_words: bool) -> dict[str, object]:
    q_words = 1 << config.w
    if not 1 <= config.n <= q_words:
        raise ValueError("n must lie in [1, 2^w]")
    if config.cell_bytes <= 0 or config.usable_bytes < 0:
        raise ValueError("invalid byte accounting")
    if config.usable_bytes // config.cell_bytes != config.n:
        raise ValueError("n is not the dense capacity of the usable budget")
    if config.mul1 % 2 == 0 or config.mul2 % 2 == 0:
        raise ValueError("multipliers must be odd")
    for shift in (config.shift1, config.shift2, config.shift3):
        if not 0 < shift < config.w:
            raise ValueError("shift outside the DRB-1 domain")

    quotient, remainder = divmod(q_words, config.n)
    expected_collision_numerator = (
        remainder * (quotient + 1) ** 2
        + (config.n - remainder) * quotient**2
    )
    allocation_bytes = (
        config.cell_bytes * (config.n + config.guard_cells)
        + config.alignment_bytes
    )

    result: dict[str, object] = {
        "schema": "fxcm_dense_range_bucket_verifier_v1",
        "config": asdict(config),
        "word_count": q_words,
        "quotient": quotient,
        "remainder": remainder,
        "allocation_bytes": allocation_bytes,
        "unused_usable_bytes": (
            config.usable_bytes - config.cell_bytes * config.n
        ),
        "collision_numerator": expected_collision_numerator,
        "collision_denominator": q_words**2,
        "enumerated": enumerate_words,
    }

    if enumerate_words:
        images = [permute(value, config) for value in range(q_words)]
        if len(set(images)) != q_words:
            raise AssertionError("fixed-width scrambler is not a permutation")

        counts = [0] * config.n
        for value in range(q_words):
            index = bucket(value, config)
            if not 0 <= index < config.n:
                raise AssertionError("range index outside table")
            counts[index] += 1

        if min(counts) != quotient or max(counts) != quotient + (remainder > 0):
            raise AssertionError("range-index preimages are not balanced")
        if sum(count * count for count in counts) != expected_collision_numerator:
            raise AssertionError("collision numerator does not match theorem")

        result.update(
            {
                "permutation_ok": True,
                "balance_ok": True,
                "collision_identity_ok": True,
                "minimum_preimages": min(counts),
                "maximum_preimages": max(counts),
                "nonempty_buckets": sum(count > 0 for count in counts),
                "test_vector_count": q_words,
                "boundary_vectors": {
                    "zero": bucket(0, config),
                    "maximum": bucket(q_words - 1, config),
                    "salt_wrap_left": bucket((-config.salt) & (q_words - 1), config),
                    "salt_wrap_right": bucket(
                        (-config.salt - 1) & (q_words - 1), config
                    ),
                },
            }
        )
    return result


def self_test() -> dict[str, object]:
    old_cells = 1 << 8
    usable_bytes = 128 * old_cells
    dense_cells = usable_bytes // 96
    config = Config(
        w=16,
        n=dense_cells,
        cell_bytes=96,
        usable_bytes=usable_bytes,
        guard_cells=128,
        alignment_bytes=127,
        add=0xB7E1,
        mul1=0x9E37,
        mul2=0x85EB,
        shift1=7,
        shift2=5,
        shift3=8,
        salt=0xC2A5,
    )
    result = verify(config, enumerate_words=True)
    result["old_cells"] = old_cells
    result["dense_cells"] = dense_cells
    result["capacity_ratio_numerator"] = dense_cells
    result["capacity_ratio_denominator"] = old_cells
    if dense_cells != (4 * old_cells) // 3:
        raise AssertionError("dense capacity formula failed")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--w", type=int)
    parser.add_argument("--n", type=int)
    parser.add_argument("--cell-bytes", type=int, default=96)
    parser.add_argument("--usable-bytes", type=int)
    parser.add_argument("--guard-cells", type=int, default=0)
    parser.add_argument("--alignment-bytes", type=int, default=0)
    parser.add_argument("--add", type=lambda value: int(value, 0), default=0x9E3779B9)
    parser.add_argument("--mul1", type=lambda value: int(value, 0), default=0x7FEB352D)
    parser.add_argument("--mul2", type=lambda value: int(value, 0), default=0x846CA68B)
    parser.add_argument("--shift1", type=int, default=16)
    parser.add_argument("--shift2", type=int, default=15)
    parser.add_argument("--shift3", type=int, default=16)
    parser.add_argument("--salt", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--enumerate", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        result = self_test()
    else:
        required = (args.w, args.n, args.usable_bytes)
        if any(value is None for value in required):
            parser.error("--w, --n, and --usable-bytes are required")
        result = verify(
            Config(
                w=args.w,
                n=args.n,
                cell_bytes=args.cell_bytes,
                usable_bytes=args.usable_bytes,
                guard_cells=args.guard_cells,
                alignment_bytes=args.alignment_bytes,
                add=args.add,
                mul1=args.mul1,
                mul2=args.mul2,
                shift1=args.shift1,
                shift2=args.shift2,
                shift3=args.shift3,
                salt=args.salt,
            ),
            enumerate_words=args.enumerate,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
