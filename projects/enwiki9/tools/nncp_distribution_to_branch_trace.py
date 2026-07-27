#!/usr/bin/env python3
"""Convert an NNCP full-distribution trace to exact branch-frequency targets."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
from pathlib import Path
import struct
import tarfile
import tempfile


INPUT_HEADER = struct.Struct("<8sQ")
INPUT_ROW = struct.Struct("<QQQQIHHI")
INPUT_MAGIC = b"NNTCHD2\0"
OUTPUT_HEADER = struct.Struct("<8sQQ")
OUTPUT_ROW = struct.Struct("<QQQHHB")
OUTPUT_BRANCH = struct.Struct("<HB")
OUTPUT_MAGIC = b"NNQBR1\0\0"
PROBABILITY_TOTAL = 32768


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f32(value: float) -> float:
    return ctypes.c_float(value).value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--source-package", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    source = args.trace.read_bytes()
    if len(source) < INPUT_HEADER.size:
        raise ValueError("truncated distribution trace")
    magic, row_count = INPUT_HEADER.unpack_from(source)
    if magic != INPUT_MAGIC or row_count <= 0:
        raise ValueError("invalid distribution trace")

    with tempfile.TemporaryDirectory(prefix="nncp-branch-convert-") as td:
        root = Path(td)
        with tarfile.open(args.source_package, "r:xz") as archive:
            member = archive.getmember("libnc.so")
            extracted = archive.extractfile(member)
            if extracted is None:
                raise ValueError("source package has no libnc.so payload")
            library_path = root / "libnc.so"
            library_path.write_bytes(extracted.read())
        library = ctypes.CDLL(str(library_path))
        library.vec_sum_f32.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_int,
        ]
        library.vec_sum_f32.restype = ctypes.c_float
        libm = ctypes.CDLL("libm.so.6")
        libm.lrintf.argtypes = [ctypes.c_float]
        libm.lrintf.restype = ctypes.c_long

        offset = INPUT_HEADER.size
        output = bytearray(OUTPUT_HEADER.pack(OUTPUT_MAGIC, row_count, 0))
        total_branches = 0
        minimum_probability = PROBABILITY_TOTAL
        maximum_probability = 0
        prior_after: int | None = None
        vocabularies: set[int] = set()
        for index in range(row_count):
            if offset + INPUT_ROW.size > len(source):
                raise ValueError("truncated distribution row")
            (
                original,
                execution,
                before,
                after,
                _local,
                _stream,
                symbol,
                vocabulary,
            ) = INPUT_ROW.unpack_from(source, offset)
            offset += INPUT_ROW.size
            if original != index or execution != index:
                raise ValueError("trace is not sequential batch-1 order")
            if prior_after is not None and before != prior_after:
                raise ValueError("coder counts are discontinuous")
            if after < before or symbol >= vocabulary:
                raise ValueError("invalid coder count or symbol")
            byte_count = 4 * vocabulary
            if offset + byte_count > len(source):
                raise ValueError("truncated probability vector")
            values = struct.unpack_from(f"<{vocabulary}f", source, offset)
            offset += byte_count
            if not all(math.isfinite(value) and value > 0 for value in values):
                raise ValueError("invalid teacher probability")
            probabilities = (ctypes.c_float * vocabulary)(*values)

            start, active = 0, vocabulary
            mass = f32(1.0)
            branches: list[tuple[int, int]] = []
            while active > 1:
                left = active >> 1
                pointer = ctypes.cast(
                    ctypes.byref(probabilities, start * ctypes.sizeof(ctypes.c_float)),
                    ctypes.POINTER(ctypes.c_float),
                )
                left_mass = float(library.vec_sum_f32(pointer, left))
                scaled = f32(f32(left_mass * PROBABILITY_TOTAL) / mass)
                probability = int(libm.lrintf(ctypes.c_float(scaled)))
                probability = max(1, min(PROBABILITY_TOTAL - 1, probability))
                bit = int(symbol >= start + left)
                branches.append((probability, bit))
                if bit:
                    start += left
                    active -= left
                    mass = f32(mass - left_mass)
                else:
                    active = left
                    mass = f32(left_mass)
            if start != symbol or len(branches) > 255:
                raise AssertionError("invalid derived branch path")

            output.extend(
                OUTPUT_ROW.pack(
                    execution,
                    before,
                    after,
                    symbol,
                    vocabulary,
                    len(branches),
                )
            )
            for probability, bit in branches:
                output.extend(OUTPUT_BRANCH.pack(probability, bit))
                minimum_probability = min(minimum_probability, probability)
                maximum_probability = max(maximum_probability, probability)
            total_branches += len(branches)
            prior_after = after
            vocabularies.add(vocabulary)

        if offset != len(source):
            raise ValueError("trailing distribution-trace bytes")
        OUTPUT_HEADER.pack_into(output, 0, OUTPUT_MAGIC, row_count, total_branches)
        args.output.write_bytes(output)
        receipt = {
            "branch_count": total_branches,
            "input_trace_bytes": len(source),
            "input_trace_sha256": sha256(source),
            "libnc_sha256": sha256(library_path.read_bytes()),
            "maximum_probability": maximum_probability,
            "minimum_probability": minimum_probability,
            "output_trace_bytes": len(output),
            "output_trace_sha256": sha256(output),
            "probability_total": PROBABILITY_TOTAL,
            "schema": "nncp_distribution_to_branch_trace_v1",
            "score_credit_bytes": 0,
            "symbol_count": row_count,
            "vocabularies": sorted(vocabularies),
        }
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
