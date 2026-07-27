#!/usr/bin/env python3
"""Materialize an archive-neutral NNCP full-distribution observer patch."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path


PUT_SYMB = """static void put_symb(DataSymbol *buf, int stride, int rem,
                    int stream_idx, int pos, int c)
{
    int e;
    
    e = (stream_idx < rem);
    if (pos < 0 || pos >= (stride + e))
        abort();
    buf[stride * stream_idx + min_int(rem, stream_idx) + pos] = c;
}
"""

OBSERVER = r"""
/* Observation-only full-distribution trace. Logging occurs after write_sym and
   does not alter the coder's probability table, counts, or update order. */
static FILE *teacher_trace_file;
static uint64_t teacher_trace_rows;

static void teacher_trace_put_le(uint8_t *buf, uint64_t value, int bytes)
{
    int i;
    for(i = 0; i < bytes; i++)
        buf[i] = value >> (8 * i);
}

static void teacher_trace_close(void)
{
    uint8_t buf[8];
    if (!teacher_trace_file)
        return;
    if (fseek(teacher_trace_file, 8, SEEK_SET) != 0)
        abort();
    teacher_trace_put_le(buf, teacher_trace_rows, 8);
    if (fwrite(buf, 1, 8, teacher_trace_file) != 8)
        abort();
    if (fclose(teacher_trace_file) != 0)
        abort();
    teacher_trace_file = NULL;
}

static void teacher_trace_init(void)
{
    const char *filename;
    uint8_t zero[8] = { 0 };
    if (teacher_trace_file)
        return;
    filename = getenv("NNCP_TEACHER_TRACE");
    if (!filename || filename[0] == '\0')
        return;
    teacher_trace_file = fopen(filename, "wb");
    if (!teacher_trace_file)
        abort();
    if (fwrite("NNTCHD2\0", 1, 8, teacher_trace_file) != 8 ||
        fwrite(zero, 1, 8, teacher_trace_file) != 8)
        abort();
    if (atexit(teacher_trace_close) != 0)
        abort();
}

static void write_sym_traced(PutBitState *pb, const float *prob_table,
                             int n_symbols, int symbol,
                             uint64_t original_symbol_index,
                             uint32_t local_position, uint16_t stream_index)
{
    uint8_t row[44], value_buf[4];
    uint64_t execution_row, before, after;
    union { float f; uint32_t u; } probability;
    int i;

    teacher_trace_init();
    execution_row = teacher_trace_rows;
    before = put_bit_get_bit_count(pb);
    write_sym(pb, prob_table, n_symbols, symbol);
    after = put_bit_get_bit_count(pb);
    if (!teacher_trace_file)
        return;

    teacher_trace_put_le(row + 0, original_symbol_index, 8);
    teacher_trace_put_le(row + 8, execution_row, 8);
    teacher_trace_put_le(row + 16, before, 8);
    teacher_trace_put_le(row + 24, after, 8);
    teacher_trace_put_le(row + 32, local_position, 4);
    teacher_trace_put_le(row + 36, stream_index, 2);
    teacher_trace_put_le(row + 38, symbol, 2);
    teacher_trace_put_le(row + 40, n_symbols, 4);
    if (fwrite(row, 1, sizeof(row), teacher_trace_file) != sizeof(row))
        abort();
    for(i = 0; i < n_symbols; i++) {
        probability.f = prob_table[i];
        teacher_trace_put_le(value_buf, probability.u, 4);
        if (fwrite(value_buf, 1, sizeof(value_buf), teacher_trace_file) !=
            sizeof(value_buf))
            abort();
    }
    teacher_trace_rows++;
}
"""


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count < 1:
        raise ValueError(f"missing source anchor: {label}")
    return source.replace(old, new, 1)


def materialize(source_path: Path, patch_path: Path) -> None:
    original = source_path.read_text()
    source = original
    if "write_sym_traced" in source:
        raise ValueError("source is already instrumented")

    source = replace_once(source, PUT_SYMB, PUT_SYMB + OBSERVER, "put_symb")
    source = replace_once(
        source,
        "    int block_stride, n_streams, block_rem, seg_len1, seg_len2;\n"
        "    float *output, lr;",
        "    int block_stride, n_streams, block_rem, seg_len1, seg_len2;\n"
        "    uint64_t block_base;\n"
        "    float *output, lr;",
        "block_base declaration",
    )
    source = replace_once(
        source,
        "    block_stride = block_len / n_streams;\n"
        "    block_rem = block_len % n_streams;\n",
        "    block_stride = block_len / n_streams;\n"
        "    block_rem = block_len % n_streams;\n"
        "    block_base = st->n_input_bytes;\n",
        "block_base initialization",
    )

    scalar = (
        "                        write_sym(pb, output + stream_idx * stride, "
        "s->n_symbols, c);"
    )
    source = replace_once(
        source,
        scalar,
        """                        write_sym_traced(
                            pb, output + stream_idx * stride, s->n_symbols, c,
                            block_base + block_stride * stream_idx +
                                min_int(block_rem, stream_idx) +
                                block_idx + cur_state,
                            block_idx + cur_state, stream_idx);""",
        "normal scalar write",
    )
    source = replace_once(
        source,
        """                    write_sym(pb, output + (cur_state * n_streams + stream_idx) * stride, s->n_symbols, c);""",
        """                    write_sym_traced(
                        pb,
                        output + (cur_state * n_streams + stream_idx) * stride,
                        s->n_symbols, c,
                        block_base + block_stride * stream_idx +
                            min_int(block_rem, stream_idx) +
                            block_idx + cur_state,
                        block_idx + cur_state, stream_idx);""",
        "normal encode-only write",
    )
    source = replace_once(
        source,
        scalar,
        """                        write_sym_traced(
                            pb, output + stream_idx * stride, s->n_symbols, c,
                            block_base + block_stride * stream_idx +
                                min_int(block_rem, stream_idx) +
                                block_idx + cur_state,
                            block_idx + cur_state, stream_idx);""",
        "remainder scalar write",
    )
    source = replace_once(
        source,
        """                        write_sym(pb, output +
                                  (cur_state * n_streams + stream_idx) *
                                  stride, s->n_symbols, c);""",
        """                        write_sym_traced(
                            pb, output +
                                (cur_state * n_streams + stream_idx) * stride,
                            s->n_symbols, c,
                            block_base + block_stride * stream_idx +
                                min_int(block_rem, stream_idx) +
                                block_idx + cur_state,
                            block_idx + cur_state, stream_idx);""",
        "remainder encode-only write",
    )

    if source.count("write_sym_traced(") != 5:
        raise ValueError("observer wrapper/call count is not five")
    if source.count("write_sym(pb,") != 1:
        raise ValueError("unwrapped encoder call remains")

    patch = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            source.splitlines(keepends=True),
            fromfile="a/nncp.c",
            tofile="b/nncp.c",
        )
    )
    if not patch:
        raise ValueError("materialized patch is empty")
    source_path.write_text(source)
    patch_path.write_text(patch)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("patch", type=Path)
    args = parser.parse_args()
    materialize(args.source, args.patch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
