#!/usr/bin/env python3
"""Materialize an archive-neutral NNCP branch trace with original ordinals."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path

from materialize_nncp_native_trace_observer import materialize as materialize_base


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"expected one source anchor for {label}")
    return source.replace(old, new, 1)


def instrument_cp_utils(source_root: Path) -> None:
    source_path = source_root / "cp_utils.c"
    traced_path = source_root / "cp_utils.c.native_base"
    temporary_patch = source_root / "cp_utils.native_base.patch"
    materialize_base(source_path, traced_path, temporary_patch)
    source = traced_path.read_text()
    source = replace_once(
        source,
        "static uint64_t native_trace_checkpoint_rows, native_trace_prefix_bytes;\n"
        "static BOOL native_trace_initialized;",
        "static uint64_t native_trace_checkpoint_rows, native_trace_prefix_bytes;\n"
        "static uint64_t native_trace_original_index;\n"
        "static BOOL native_trace_initialized;\n\n"
        "void native_trace_set_original_index(uint64_t value)\n"
        "{\n"
        "    native_trace_original_index = value;\n"
        "}",
        "native original-index state",
    )
    source = replace_once(
        source, 'fwrite("NNNTR3\\0", 1, 8, native_trace_file)',
        'fwrite("NNNTR4\\0", 1, 8, native_trace_file)',
        "indexed trace magic",
    )
    source = replace_once(
        source,
        "uint16_t trace_prob[16];\n"
        "    uint8_t trace_bit[16], row[63], branch[3], tree_count[2];",
        "uint16_t trace_prob[16];\n"
        "    uint8_t trace_bit[16], row[71], branch[3], tree_count[2];",
        "indexed trace row size",
    )
    old_rows = """    native_trace_put_le(row + 0, native_trace_rows, 8);
    native_trace_put_le(row + 8, before_bits, 8);
    native_trace_put_le(row + 16, after_bits, 8);
    native_trace_put_le(row + 24, before_bytes, 8);
    native_trace_put_le(row + 32, after_bytes, 8);
    native_trace_put_le(row + 40, exact_archive_bits, 8);
    native_trace_put_le(row + 48, exact_archive_bytes, 8);
    native_trace_put_le(row + 56, sym, 2);
    native_trace_put_le(row + 58, n_symb, 2);
    row[60] = trace_count;
    row[61] = full_tree;
    row[62] = checkpoint;"""
    new_rows = """    native_trace_put_le(row + 0, native_trace_original_index, 8);
    native_trace_put_le(row + 8, native_trace_rows, 8);
    native_trace_put_le(row + 16, before_bits, 8);
    native_trace_put_le(row + 24, after_bits, 8);
    native_trace_put_le(row + 32, before_bytes, 8);
    native_trace_put_le(row + 40, after_bytes, 8);
    native_trace_put_le(row + 48, exact_archive_bits, 8);
    native_trace_put_le(row + 56, exact_archive_bytes, 8);
    native_trace_put_le(row + 64, sym, 2);
    native_trace_put_le(row + 66, n_symb, 2);
    row[68] = trace_count;
    row[69] = full_tree;
    row[70] = checkpoint;"""
    source = replace_once(source, old_rows, new_rows, "indexed trace row")
    source_path.write_text(source)
    traced_path.unlink()
    temporary_patch.unlink()


def instrument_header(source_root: Path) -> None:
    path = source_root / "cp_utils.h"
    source = path.read_text()
    source = replace_once(
        source,
        "void write_sym(PutBitState *pb, const float *prob_table, int n_symb, int sym);",
        "void native_trace_set_original_index(uint64_t value);\n"
        "void write_sym(PutBitState *pb, const float *prob_table, int n_symb, int sym);",
        "native original-index prototype",
    )
    path.write_text(source)


def indexed_write(expression: str, call: str, indent: str) -> str:
    return (
        f"{indent}native_trace_set_original_index(\n"
        f"{indent}    {expression});\n"
        f"{indent}{call}"
    )


def instrument_nncp(source_root: Path) -> None:
    path = source_root / "nncp.c"
    source = path.read_text()
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
    source = source.replace(scalar, scalar_replacement, 1)
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
    source = source.replace(scalar, scalar_replacement, 1)
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
    if source.count("native_trace_set_original_index(") != 4:
        raise ValueError("expected four indexed encoder writes")
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
