#!/usr/bin/env python3
"""Materialize the NNCP native branch observer from a clean cp_utils.c."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path


TRACE_SUPPORT = r'''
/* Observation-only trace of the exact integer probabilities consumed by
   put_bit. Complete trees are derived with the same recursive float
   arithmetic but are never consumed by the coder. */
static FILE *native_trace_file;
static uint64_t native_trace_rows, native_trace_branches, native_trace_trees;
static uint64_t native_trace_checkpoint_rows, native_trace_prefix_bytes;
static BOOL native_trace_initialized;

typedef struct {
    uint64_t start;
    uint64_t end;
} NativeTraceWindow;

static NativeTraceWindow native_trace_windows[32];
static int native_trace_window_count;
static uint64_t native_trace_checkpoints[32];
static int native_trace_checkpoint_count;

static void native_trace_put_le(uint8_t *buf, uint64_t value, int bytes)
{
    int i;
    for(i = 0; i < bytes; i++)
        buf[i] = value >> (8 * i);
}

static void native_trace_parse_windows(const char *value)
{
    char *end;
    uint64_t start, stop;
    while(value && *value) {
        if (native_trace_window_count >= 32)
            abort();
        start = strtoull(value, &end, 10);
        if (end == value || *end != ':')
            abort();
        value = end + 1;
        stop = strtoull(value, &end, 10);
        if (end == value || stop <= start)
            abort();
        native_trace_windows[native_trace_window_count].start = start;
        native_trace_windows[native_trace_window_count].end = stop;
        native_trace_window_count++;
        if (*end == '\0')
            break;
        if (*end != ',')
            abort();
        value = end + 1;
    }
}

static BOOL native_trace_full(uint64_t row)
{
    int i;
    for(i = 0; i < native_trace_window_count; i++) {
        if (row >= native_trace_windows[i].start &&
            row < native_trace_windows[i].end)
            return TRUE;
    }
    return FALSE;
}

static void native_trace_parse_checkpoints(const char *value)
{
    char *end;
    uint64_t checkpoint;
    while(value && *value) {
        if (native_trace_checkpoint_count >= 32)
            abort();
        checkpoint = strtoull(value, &end, 10);
        if (end == value || checkpoint == 0)
            abort();
        native_trace_checkpoints[native_trace_checkpoint_count++] = checkpoint;
        if (*end == '\0')
            break;
        if (*end != ',')
            abort();
        value = end + 1;
    }
}

static BOOL native_trace_checkpoint(uint64_t completed_rows)
{
    int i;
    for(i = 0; i < native_trace_checkpoint_count; i++) {
        if (completed_rows == native_trace_checkpoints[i])
            return TRUE;
    }
    return FALSE;
}

static void native_trace_close(void)
{
    uint8_t buf[8];
    if (!native_trace_file)
        return;
    if (fseek(native_trace_file, 8, SEEK_SET) != 0)
        abort();
    native_trace_put_le(buf, native_trace_rows, 8);
    if (fwrite(buf, 1, 8, native_trace_file) != 8)
        abort();
    native_trace_put_le(buf, native_trace_branches, 8);
    if (fwrite(buf, 1, 8, native_trace_file) != 8)
        abort();
    native_trace_put_le(buf, native_trace_trees, 8);
    if (fwrite(buf, 1, 8, native_trace_file) != 8)
        abort();
    native_trace_put_le(buf, native_trace_checkpoint_rows, 8);
    if (fwrite(buf, 1, 8, native_trace_file) != 8)
        abort();
    if (fclose(native_trace_file) != 0)
        abort();
    native_trace_file = NULL;
}

static void native_trace_init(void)
{
    const char *filename;
    uint8_t zero[32] = { 0 };
    if (native_trace_initialized)
        return;
    native_trace_initialized = TRUE;
    filename = getenv("NNCP_NATIVE_TRACE");
    if (!filename || !filename[0])
        return;
    native_trace_file = fopen(filename, "wb");
    if (!native_trace_file)
        abort();
    if (fwrite("NNNTR3\0", 1, 8, native_trace_file) != 8 ||
        fwrite(zero, 1, sizeof(zero), native_trace_file) != sizeof(zero))
        abort();
    native_trace_parse_windows(getenv("NNCP_NATIVE_TRACE_FULL_WINDOWS"));
    native_trace_parse_checkpoints(getenv("NNCP_NATIVE_TRACE_CHECKPOINTS"));
    if (atexit(native_trace_close) != 0)
        abort();
}

static void native_trace_discard(void *opaque, const uint8_t *buf,
                                 size_t buf_size)
{
    (void)opaque;
    (void)buf;
    (void)buf_size;
}

static void native_trace_finalize_clone(PutBitState *pb,
                                        uint64_t *archive_bits,
                                        uint64_t *archive_bytes)
{
    PutBitState clone;
    uint8_t *buffer;
    int64_t payload_bits;
    clone = *pb;
    buffer = malloc(pb->buf_size);
    if (!buffer)
        abort();
    memcpy(buffer, pb->buf, pb->buf_size);
    clone.buf = buffer;
    clone.write_func = native_trace_discard;
    clone.opaque = NULL;
    payload_bits = put_bit_flush(&clone);
    if (payload_bits < 0)
        abort();
    *archive_bits = native_trace_prefix_bytes * 8 + payload_bits;
    *archive_bytes = native_trace_prefix_bytes + clone.byte_count;
    free(buffer);
}

static void native_trace_tree(const float *prob_table, int start, int range,
                              float p)
{
    int left, prob0;
    float p0;
    uint8_t value[2];
    if (range <= 1)
        return;
    left = range >> 1;
    p0 = vec_sum_f32(prob_table + start, left);
    prob0 = lrintf(p0 * PROB_UNIT / p);
    prob0 = clamp_int(prob0, 1, PROB_UNIT - 1);
    native_trace_put_le(value, prob0, 2);
    if (fwrite(value, 1, sizeof(value), native_trace_file) != sizeof(value))
        abort();
    native_trace_tree(prob_table, start, left, p0);
    native_trace_tree(prob_table, start + left, range - left, p - p0);
}
'''


ORIGINAL = r'''void write_sym(PutBitState *pb, const float *prob_table, int n_symb, int sym)
{
    int start, range, prob0, bit, range0;
    float p, p0;
    
    start = 0;
    range = n_symb;
    p = 1.0; /* invariant: p=sum(prob_table[start...start + range]) */
    while (range > 1) {
        range0 = range >> 1;
        p0 = vec_sum_f32(prob_table + start, range0);
        prob0 = lrintf(p0 * PROB_UNIT / p);
        prob0 = clamp_int(prob0, 1, PROB_UNIT - 1);
        bit = sym >= (start + range0);
        put_bit(pb, prob0, bit);
        if (bit) {
            start += range0;
            range = range - range0;
            p = p - p0;
        } else {
            p = p0;
            range = range0;
        }
    }
}'''


REPLACEMENT = r'''void write_sym(PutBitState *pb, const float *prob_table, int n_symb, int sym)
{
    int start, range, prob0, bit, range0, trace_count, i;
    float p, p0;
    uint16_t trace_prob[16];
    uint8_t trace_bit[16], row[63], branch[3], tree_count[2];
    uint64_t before_bits, after_bits, before_bytes, after_bytes;
    uint64_t exact_archive_bits, exact_archive_bytes;
    BOOL full_tree, checkpoint;
    int64_t archive_position;

    native_trace_init();
    full_tree = native_trace_file && native_trace_full(native_trace_rows);
    checkpoint = native_trace_file &&
        native_trace_checkpoint(native_trace_rows + 1);
    exact_archive_bits = 0;
    exact_archive_bytes = 0;
    if (native_trace_file && native_trace_rows == 0) {
        archive_position = ftello((FILE *)pb->opaque);
        if (archive_position < 0)
            abort();
        native_trace_prefix_bytes = archive_position;
    }
    before_bits = native_trace_file ? put_bit_get_bit_count(pb) : 0;
    before_bytes = native_trace_file ? pb->byte_count + pb->idx : 0;
    trace_count = 0;
    start = 0;
    range = n_symb;
    p = 1.0; /* invariant: p=sum(prob_table[start...start + range]) */
    while (range > 1) {
        range0 = range >> 1;
        p0 = vec_sum_f32(prob_table + start, range0);
        prob0 = lrintf(p0 * PROB_UNIT / p);
        prob0 = clamp_int(prob0, 1, PROB_UNIT - 1);
        bit = sym >= (start + range0);
        if (native_trace_file) {
            if (trace_count >= 16)
                abort();
            trace_prob[trace_count] = prob0;
            trace_bit[trace_count] = bit;
            trace_count++;
        }
        put_bit(pb, prob0, bit);
        if (bit) {
            start += range0;
            range = range - range0;
            p = p - p0;
        } else {
            p = p0;
            range = range0;
        }
    }
    if (!native_trace_file)
        return;
    after_bits = put_bit_get_bit_count(pb);
    after_bytes = pb->byte_count + pb->idx;
    if (checkpoint) {
        native_trace_finalize_clone(
            pb, &exact_archive_bits, &exact_archive_bytes);
        native_trace_checkpoint_rows++;
    }
    native_trace_put_le(row + 0, native_trace_rows, 8);
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
    row[62] = checkpoint;
    if (fwrite(row, 1, sizeof(row), native_trace_file) != sizeof(row))
        abort();
    for(i = 0; i < trace_count; i++) {
        native_trace_put_le(branch, trace_prob[i], 2);
        branch[2] = trace_bit[i];
        if (fwrite(branch, 1, sizeof(branch), native_trace_file) !=
            sizeof(branch))
            abort();
    }
    if (full_tree) {
        if (n_symb > 65536)
            abort();
        native_trace_put_le(tree_count, n_symb - 1, 2);
        if (fwrite(tree_count, 1, sizeof(tree_count), native_trace_file) !=
            sizeof(tree_count))
            abort();
        native_trace_tree(prob_table, 0, n_symb, 1.0);
        native_trace_trees++;
    }
    native_trace_rows++;
    native_trace_branches += trace_count;
}'''


def materialize(source: Path, output: Path, patch: Path) -> None:
    original = source.read_text()
    if ORIGINAL not in original:
        raise ValueError("clean NNCP write_sym implementation not found")
    include_anchor = '#include "cp_utils.h"\n'
    if include_anchor not in original:
        raise ValueError("cp_utils include anchor not found")
    modified = original.replace(
        include_anchor, include_anchor + TRACE_SUPPORT, 1
    ).replace(ORIGINAL, REPLACEMENT, 1)
    output.write_text(modified)
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile="a/cp_utils.c",
        tofile="b/cp_utils.c",
    )
    patch.write_text("".join(diff))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--patch", required=True, type=Path)
    args = parser.parse_args()
    materialize(args.source, args.output, args.patch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
