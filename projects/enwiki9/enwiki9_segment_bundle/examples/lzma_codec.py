#!/usr/bin/env python3
"""Deterministic demonstration codec only; it does not meet the target budgets."""

from __future__ import annotations
import lzma
from pathlib import Path
import shutil
import sys


def compress(source: Path, destination: Path) -> None:
    with source.open("rb") as src, lzma.open(
        destination,
        "wb",
        format=lzma.FORMAT_XZ,
        check=lzma.CHECK_CRC64,
        preset=9,
    ) as dst:
        shutil.copyfileobj(src, dst, 1 << 20)


def decompress(source: Path, destination: Path) -> None:
    with lzma.open(source, "rb", format=lzma.FORMAT_XZ) as src, destination.open("wb") as dst:
        shutil.copyfileobj(src, dst, 1 << 20)


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] not in {"compress", "decompress"}:
        print("usage: codec.py compress|decompress INPUT OUTPUT", file=sys.stderr)
        return 2
    operation, source, destination = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if operation == "compress":
        compress(source, destination)
    else:
        decompress(source, destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
