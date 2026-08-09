#!/usr/bin/env python3
"""Instrument midpoint-patched NNCP with archive-neutral original-index traces."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path

from materialize_nncp_native_indexed_trace_observer import (
    indexed_write,
    instrument_cp_utils,
    instrument_header,
    replace_once,
)


def instrument_nncp(source_root: Path) -> None:
    path = source_root / "nncp.c"
    source = path.read_text()
    if source.count("if (s->midsegment32)") < 2:
        raise ValueError("source does not contain the midpoint schedule patch")
    source = replace_once(
        source,
        "    int block_stride, n_streams, block_rem, seg_len1, seg_len2;\n"
        "    float *output, lr;",
        "    int block_stride, n_streams, block_rem, seg_len1, seg_len2;\n"
        "    uint64_t block_base;\n"
        "    float *output, lr;",
        "block-base declaration",
    )
    source = replace_once(
        source,
        "    block_stride = block_len / n_streams;\n"
        "    block_rem = block_len % n_streams;\n",
        "    block_stride = block_len / n_streams;\n"
        "    block_rem = block_len % n_streams;\n"
        "    block_base = st->n_input_bytes;\n",
        "block-base initialization",
    )
    original_index = (
        "block_base + block_stride * stream_idx +\n"
        "                                min_int(block_rem, stream_idx) +\n"
        "                                block_idx + cur_state"
    )

    scalar = (
        "                        write_sym(pb, output + stream_idx * stride, "
        "s->n_symbols, c);"
    )
    scalar_replacement = indexed_write(
        original_index,
        "write_sym(pb, output + stream_idx * stride, s->n_symbols, c);",
        "                        ",
    )
    scalar_count = source.count(scalar)
    if scalar_count != 2:
        raise ValueError(
            "expected exactly two inherited scalar encoder writes, "
            f"found {scalar_count}"
        )
    source = source.replace(scalar, scalar_replacement)

    normal_vector = (
        "                    write_sym(pb, output + "
        "(cur_state * n_streams + stream_idx) * stride, s->n_symbols, c);"
    )
    normal_vector_replacement = indexed_write(
        "block_base + block_stride * stream_idx +\n"
        "                            min_int(block_rem, stream_idx) +\n"
        "                            block_idx + cur_state",
        "write_sym(pb, output + (cur_state * n_streams + stream_idx) * "
        "stride, s->n_symbols, c);",
        "                    ",
    )
    source = replace_once(
        source,
        normal_vector,
        normal_vector_replacement,
        "normal encode-only write",
    )

    remainder_vector = """                        write_sym(pb, output +
                                  (cur_state * n_streams + stream_idx) *
                                  stride, s->n_symbols, c);"""
    remainder_vector_replacement = indexed_write(
        "block_base + block_stride * stream_idx +\n"
        "                                min_int(block_rem, stream_idx) +\n"
        "                                block_idx + cur_state",
        "write_sym(pb, output +\n"
        "                                  (cur_state * n_streams + stream_idx) *\n"
        "                                  stride, s->n_symbols, c);",
        "                        ",
    )
    source = replace_once(
        source,
        remainder_vector,
        remainder_vector_replacement,
        "remainder encode-only write",
    )

    midpoint = """                        write_sym(pb, output + stream_idx * stride,
                                  s->n_symbols, c);"""
    midpoint_replacement = indexed_write(
        original_index,
        "write_sym(pb, output + stream_idx * stride,\n"
        "                                  s->n_symbols, c);",
        "                        ",
    )
    midpoint_count = source.count(midpoint)
    if midpoint_count != 2:
        raise ValueError(
            "expected exactly two midpoint encoder writes, "
            f"found {midpoint_count}"
        )
    source = source.replace(midpoint, midpoint_replacement)

    if source.count("native_trace_set_original_index(") != 6:
        raise ValueError("expected six indexed encoder writes")
    path.write_text(source)


def materialize(source_root: Path, patch_path: Path) -> None:
    paths = [source_root / name for name in ("cp_utils.c", "cp_utils.h", "nncp.c")]
    originals = {path: path.read_text() for path in paths}
    instrument_cp_utils(source_root)
    instrument_header(source_root)
    instrument_nncp(source_root)
    chunks: list[str] = []
    for path in paths:
        chunks.extend(
            difflib.unified_diff(
                originals[path].splitlines(keepends=True),
                path.read_text().splitlines(keepends=True),
                fromfile=f"a/{path.name}",
                tofile=f"b/{path.name}",
            )
        )
    patch_path.write_text("".join(chunks))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("patch", type=Path)
    args = parser.parse_args()
    materialize(args.source_root, args.patch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
