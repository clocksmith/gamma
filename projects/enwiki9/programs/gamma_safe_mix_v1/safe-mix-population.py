#!/usr/bin/env python3
"""Materialize frozen SAFE-MIX integer-oracle populations without authority."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any


MASK64 = (1 << 64) - 1
TRAJECTORY_SEED = 0x6A09E667F3BCC909
TRAJECTORY_MULTIPLIER = 6_364_136_223_846_793_005
TRAJECTORY_INCREMENT = 1_442_695_040_888_963_407

POPULATIONS = {
    "exhaustive_scale17": {"scale": 17, "events": 512},
    "boundary_scale3": {"scale": 3, "events": 8},
    "boundary_scale4096": {"scale": 4096, "events": 72},
    "boundary_scale4294967295": {"scale": 4_294_967_295, "events": 72},
    "trajectory_scale4096": {"scale": 4096, "events": 65_536},
}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def row(parent: int, scale: int, treatment: int, truth: bool) -> bytes:
    return canonical({
        "parent_count": parent,
        "scale": scale,
        "treatment_count": treatment,
        "truth": truth,
    })


def paired_counts(scale: int, values: tuple[int, ...]) -> Iterator[bytes]:
    for parent in values:
        for treatment in values:
            for truth in (False, True):
                yield row(parent, scale, treatment, truth)


def population(population_id: str) -> Iterator[bytes]:
    if population_id == "exhaustive_scale17":
        yield from paired_counts(17, tuple(range(1, 17)))
        return
    if population_id == "boundary_scale3":
        yield from paired_counts(3, (1, 2))
        return
    if population_id == "boundary_scale4096":
        yield from paired_counts(4096, (1, 2, 2047, 2048, 4094, 4095))
        return
    if population_id == "boundary_scale4294967295":
        yield from paired_counts(
            4_294_967_295,
            (1, 2, 2_147_483_647, 2_147_483_648, 4_294_967_293, 4_294_967_294),
        )
        return
    if population_id == "trajectory_scale4096":
        state = TRAJECTORY_SEED
        for event in range(65_536):
            state = (state * TRAJECTORY_MULTIPLIER + TRAJECTORY_INCREMENT) & MASK64
            parent = 1 + ((state >> 16) % 4095)
            state = (state * TRAJECTORY_MULTIPLIER + TRAJECTORY_INCREMENT) & MASK64
            treatment = 1 + ((state >> 16) % 4095)
            if event % 257 == 0:
                treatment = parent
            state = (state * TRAJECTORY_MULTIPLIER + TRAJECTORY_INCREMENT) & MASK64
            yield row(parent, 4096, treatment, bool(state & 1))
        return
    raise ValueError(f"unknown population: {population_id}")


def open_parent(path: Path) -> int:
    if path.name in {"", ".", ".."}:
        raise ValueError("output must name one new regular file")
    parts = path.parent.parts
    if path.is_absolute():
        directory = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        parts = parts[1:]
    else:
        directory = os.open(".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in parts:
            if part in {"", "."}:
                continue
            if part == "..":
                raise ValueError("parent traversal is forbidden")
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=directory,
            )
            os.close(directory)
            directory = child
        return directory
    except BaseException:
        os.close(directory)
        raise


def write_population(path: Path, population_id: str) -> int:
    directory = open_parent(path)
    try:
        descriptor = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
    except BaseException:
        os.close(directory)
        raise
    try:
        count = 0
        try:
            for data in population(population_id):
                cursor = 0
                while cursor < len(data):
                    written = os.write(descriptor, data[cursor:])
                    if written <= 0:
                        raise OSError("short population write")
                    cursor += written
                count += 1
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(directory)
    finally:
        os.close(directory)
    expected = POPULATIONS[population_id]["events"]
    if count != expected:
        raise RuntimeError(f"population cardinality mismatch: {count} != {expected}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--population-id", choices=sorted(POPULATIONS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_population(args.output, args.population_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
