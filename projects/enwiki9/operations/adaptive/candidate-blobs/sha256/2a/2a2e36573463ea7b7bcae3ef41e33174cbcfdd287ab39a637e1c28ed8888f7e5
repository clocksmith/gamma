#!/usr/bin/env python3
"""Retain the exact RMSNorm branch in F32 through the residual join."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


PARENT_SHA256 = "6104703ab36bf71f310417fb8c7a3d05e6302a8701505d3f29ac42aa02fdfed7"
OLD_ROUND = """        for (std::size_t feature = 0; feature < kWidth; ++feature) {
            destination[feature] = round_bf16(destination[feature]);
            result.input_bias_projection[feature] += destination[feature];
        }
"""
NEW_ROUND = """        for (std::size_t feature = 0; feature < kWidth; ++feature) {
            result.input_bias_projection[feature] +=
                round_bf16(destination[feature]);
        }
"""
OLD_CONTROL = "        write_bf16(argv[10], control.input_residual);"
NEW_CONTROL = "        write_bf16(argv[10], control_total);"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"raw-join {label} boundary is not unique")
    return source.replace(old, new)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if sha256(args.parent) != PARENT_SHA256:
        raise ValueError("output-order RMSNorm backward digest differs")
    source = args.parent.read_text()
    source = replace_once(source, OLD_ROUND, NEW_ROUND, "branch-conversion")
    source = replace_once(source, OLD_CONTROL, NEW_CONTROL, "negative-control")
    args.output.write_text(source)
    print(sha256(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
