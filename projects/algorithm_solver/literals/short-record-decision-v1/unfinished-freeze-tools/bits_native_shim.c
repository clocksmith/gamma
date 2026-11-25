/* UNFINISHED. Part of a short-record-decision freeze that was paused before FREEZE.json was written.
 * Nothing here is pinned. See ../FREEZE-PROGRESS.md. */
/* Native plug-in for the BIT3 candidate (short-record-decision-v1).
 *
 * The lane's decoder lives in ../rung2-short-ra-bench-v1/ra_codecs_bench.c, which is a
 * stand-alone benchmark program: its reader functions are `static` and it has its own main().
 * This file includes that source unmodified (its main() is renamed and never called) and
 * exports the three functions the fair-baselines harness expects from a candidate:
 *
 *   void  *bits_bit3_open(const uint8_t *archive, size_t len);
 *   size_t bits_bit3_decode(void *ctx, uint32_t i, uint8_t *dst, size_t cap);
 *   void   bits_bit3_close(void *ctx);
 *
 * A lookup is one call of the lane's `bit3_decode_one`. Nothing of the decode loop is
 * reimplemented here.
 *
 * Build (done by bits_adapter.py, outside the repository):
 *   cc -O3 -fPIC -shared -I<zstd prefix>/include \
 *      -DBITS_LANE_SOURCE='"<...>/rung2-short-ra-bench-v1/ra_codecs_bench.c"' \
 *      bits_native_shim.c -L<zstd prefix>/lib -lzstd -lz -o libbits3.<ext>
 * zstd and zlib are linked only because the lane's file also holds its ZST3 and DFL3 readers.
 *
 * Three things about the lane's reader that this wrapper has to work around, none of them in
 * the timed path:
 *   1. `bit3_decode_one` reads up to 12 bytes past the end of the bit stream (it refills a
 *      64-bit buffer in 8- and 4-byte steps). The lane's program pads the file it loads with
 *      64 zero bytes; `bits_bit3_open` does the same on a private copy of the archive.
 *   2. `init_bit3` calls exit() on a bad magic and does not bound-check the header, and its
 *      tables are fixed arrays of MAX_SYMS (4,100) symbols including the end-of-record
 *      symbol. `bits_bit3_open` checks the header first and returns NULL instead.
 *   3. `bit3_decode_one` takes no output capacity. The harness always passes a buffer larger
 *      than the longest record; the capacity is compared with the returned length afterwards,
 *      which reports an overrun but cannot prevent one.
 */
#ifndef BITS_LANE_SOURCE
#error "define BITS_LANE_SOURCE as the quoted path of the lane's ra_codecs_bench.c"
#endif

#define main bits_lane_bench_main
#include BITS_LANE_SOURCE
#undef main

typedef struct {
    Bit3Archive arc;   /* the lane's reader state (dictionary copy, two decode tables) */
    uint8_t *buf;      /* private copy of the archive, zero-padded */
    size_t len;
} bits_ctx;

void *bits_bit3_open(const uint8_t *archive, size_t len) {
    if (!archive || len < 9 || memcmp(archive, "BIT3", 4) != 0) return NULL;
    uint16_t n_entries = rd_u16(archive + 4);
    uint16_t n_files = rd_u16(archive + 6);
    uint8_t n_tables = archive[8];
    if (n_tables != 1 && n_tables != 2) return NULL;
    if ((size_t)n_entries + 1 > MAX_SYMS) return NULL;
    size_t pos = 9;
    for (uint16_t i = 0; i < n_entries; i++) {
        if (pos >= len) return NULL;
        pos += 1 + (size_t)archive[pos];
    }
    pos += (size_t)n_tables * ((size_t)n_entries + 1) + (size_t)n_files * 4 + (n_tables == 2 ? 4 : 0);
    if (pos > len) return NULL;
    if (n_tables == 2 && (size_t)rd_u32(archive + pos - 4) > len - pos) return NULL;

    bits_ctx *c = (bits_ctx *)calloc(1, sizeof(*c));
    if (!c) return NULL;
    c->buf = (uint8_t *)malloc(len + 64);
    if (!c->buf) { free(c); return NULL; }
    memcpy(c->buf, archive, len);
    memset(c->buf + len, 0, 64);
    c->len = len;
    init_bit3(&c->arc, c->buf, len);
    return c;
}

size_t bits_bit3_decode(void *ctx, uint32_t i, uint8_t *dst, size_t cap) {
    const bits_ctx *c = (const bits_ctx *)ctx;
    size_t n = bit3_decode_one(&c->arc, i, dst);
    return n <= cap ? n : (size_t)-1;
}

void bits_bit3_close(void *ctx) {
    bits_ctx *c = (bits_ctx *)ctx;
    if (!c) return;
    free(c->buf);
    free(c);
}

/* Reporting only. */
uint32_t bits_bit3_count(void *ctx) { return ((const bits_ctx *)ctx)->arc.n_files; }

/* Heap held by one open reader: the lane's fixed-size reader state plus the padded archive copy. */
size_t bits_bit3_reader_heap_bytes(void *ctx) {
    const bits_ctx *c = (const bits_ctx *)ctx;
    return sizeof(bits_ctx) + c->len + 64;
}

size_t bits_bit3_reader_state_bytes(void) { return sizeof(bits_ctx); }
