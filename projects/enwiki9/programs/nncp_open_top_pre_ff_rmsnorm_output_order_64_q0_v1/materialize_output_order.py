#!/usr/bin/env python3
"""Materialize the LibNC output-order pre-FF RMSNorm backward."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


PARENT_SHA256 = "3cc3e11f52fc976e7ac68a9e6d6c96fd274c37314ec9c6fecf7b8c541e0db187"
OLD_SCALARS = """        const float upstream_sum = reduce_products(
            upstream.data(), ones.data());
        const float product_sum = reduce_streaming_products(
            upstream.data(), unit.data());
"""
NEW_SCALARS = """        const float product_sum = reduce_streaming_products(
            upstream.data(), unit.data());
        const float mean_product =
            product_sum / static_cast<float>(kWidth);
"""
OLD_CENTER = """            __m256 centered = _mm256_fmsub_ps(
                current, _mm256_set1_ps(static_cast<float>(kWidth)),
                _mm256_set1_ps(upstream_sum));
            centered = _mm256_fnmadd_ps(
                normalized, _mm256_set1_ps(product_sum), centered);
            const __m256 values = _mm256_mul_ps(
                _mm256_set1_ps(
                    inverse / static_cast<float>(kWidth)), centered);
"""
NEW_CENTER = """            const __m256 centered = _mm256_fnmadd_ps(
                normalized, _mm256_set1_ps(mean_product), current);
            const __m256 values = _mm256_mul_ps(
                _mm256_set1_ps(inverse), centered);
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"output-order {label} boundary is not unique")
    return source.replace(old, new)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if sha256(args.parent) != PARENT_SHA256:
        raise ValueError("state-reduced pre-FF backward digest differs")
    source = args.parent.read_text()
    source = replace_once(
        source,
        "        const std::vector<float> norm_input = read_norm_inputs(argv[2]);",
        "        const std::vector<float> norm_input = read_bf16(\n"
        "            argv[2], kSamples * kWidth);",
        "sealed-input",
    )
    source = replace_once(source, OLD_SCALARS, NEW_SCALARS, "scalars")
    source = replace_once(source, OLD_CENTER, NEW_CENTER, "backward-order")
    source = replace_once(
        source,
        "        write_bf16(argv[10], control_total);",
        "        write_bf16(argv[10], control.input_residual);",
        "negated-control",
    )
    source = source.replace(
        "OPEN_ROOT NORM_ADJOINT", "SEALED_INPUT NORM_ADJOINT"
    )
    args.output.write_text(source)
    print(sha256(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
