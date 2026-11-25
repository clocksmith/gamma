/* Native C Random-Access Single-Record Benchmark for BIT3, FSST-255, ZST3, and DFL3 (-15).
 *
 * Compiles with:
 *   cc -O3 -Wall -Wextra -I/opt/homebrew/include -L/opt/homebrew/lib ra_codecs_bench.c -lzstd -lz -o ra_codecs_bench
 *
 * Guarantees identical single-record random-access semantics across all four formats:
 *   1. Loads the serialized archive into memory ONCE and builds any static decode structures
 *      (`BIT3` 12-bit canonical Huffman LUT, `FSST` 8-byte symbol table, `ZSTD_DCtx` + `ZSTD_DDict`,
 *      or `zlib` raw `-15` `z_stream`).
 *   2. Verifies 100% byte-for-byte equality on EVERY document `0..M-1` in reverse order (`M-1..0`)
 *      against `raw_verify.bin` before starting the timer.
 *   3. Executes `num_seeks` pseudo-random single-document seeks (`xorshift64*`, seed `0x9E3779B97F4A7C15`),
 *      accumulating a live byte checksum so `-O3` cannot elide decoding, and prints JSON metrics:
 *      `ns_per_seek`, `seeks_per_sec`, `decoded_mib_per_sec`.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <zlib.h>
#include <zstd.h>

#define LUT_BITS 12
#define LUT_SIZE (1u << LUT_BITS)
#define MAX_SYMS 4100
#define MAX_TREE_NODES 16384

static const uint8_t BITS_EOF_BYTES[13] = {
    0x00, '_', '_', 'B', 'I', 'T', 'S', '_', 'E', 'O', 'F', '_', '_'
};

typedef struct {
    uint32_t m_docs;
    uint32_t *ends;
    uint8_t *concat;
    size_t total_raw;
} RawCorpus;

static uint8_t *slurp_file(const char *path, size_t *out_len) {
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); exit(2); }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *buf = (uint8_t *)malloc((size_t)sz + 64);
    if (!buf) exit(2);
    memset(buf + sz, 0, 64);
    if (sz > 0 && fread(buf, 1, (size_t)sz, f) != (size_t)sz) exit(2);
    fclose(f);
    *out_len = (size_t)sz;
    return buf;
}

static RawCorpus load_raw_corpus(const char *path) {
    size_t len = 0;
    uint8_t *buf = slurp_file(path, &len);
    if (len < 4) exit(2);
    RawCorpus rc;
    memcpy(&rc.m_docs, buf, 4);
    rc.ends = (uint32_t *)malloc(rc.m_docs * sizeof(uint32_t));
    memcpy(rc.ends, buf + 4, rc.m_docs * sizeof(uint32_t));
    size_t hdr = 4 + (size_t)rc.m_docs * 4;
    rc.total_raw = len - hdr;
    rc.concat = (uint8_t *)malloc(rc.total_raw + 16);
    memcpy(rc.concat, buf + hdr, rc.total_raw);
    free(buf);
    return rc;
}

static uint16_t rd_u16(const uint8_t *p) {
    uint16_t v;
    memcpy(&v, p, 2);
    return v;
}

static uint32_t rd_u32(const uint8_t *p) {
    uint32_t v;
    memcpy(&v, p, 4);
    return v;
}

static uint64_t rd_be64(const uint8_t *p) {
    uint64_t v;
    memcpy(&v, p, 8);
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    return __builtin_bswap64(v);
#else
    return v;
#endif
}

/* ==================== 1. BIT3 Fast 12-bit LUT + Overflow Tree Decoder ==================== */

typedef struct {
    uint16_t sym_idx;
    uint8_t bit_len;
    const uint8_t *bytes;
    uint8_t byte_len;
} CanonItem;

static int cmp_canon_item(const void *a, const void *b) {
    const CanonItem *x = (const CanonItem *)a;
    const CanonItem *y = (const CanonItem *)b;
    if (x->bit_len != y->bit_len) return (int)x->bit_len - (int)y->bit_len;
    uint8_t mn = x->byte_len < y->byte_len ? x->byte_len : y->byte_len;
    int c = memcmp(x->bytes, y->bytes, mn);
    if (c != 0) return c;
    return (int)x->byte_len - (int)y->byte_len;
}

typedef struct {
    int32_t child[2];
    int32_t sym_idx; /* -1 if internal */
} TreeNode;

typedef struct {
    /* Packed LUT entry: bit 31 = slow_flag; if 0: bits 30..16 = bit_len, bits 15..0 = sym_idx */
    uint32_t lut[LUT_SIZE];
    TreeNode nodes[MAX_TREE_NODES];
    int32_t n_nodes;
    uint16_t eof_sym_idx;
} HuffTableFast;

typedef struct {
    uint16_t n_entries;
    uint16_t n_files;
    uint8_t n_tables;
    uint8_t sym_len[MAX_SYMS];
    uint8_t sym_bytes[MAX_SYMS][256];
    HuffTableFast tables[2];
    const uint32_t *index_words;
    const uint8_t *streams[2];
    size_t stream_lens[2];
} Bit3Archive;

static void build_huff_fast(
    HuffTableFast *ht,
    uint16_t n_entries,
    const uint8_t sym_len[MAX_SYMS],
    const uint8_t sym_bytes[MAX_SYMS][256],
    const uint8_t *code_lengths
) {
    CanonItem items[MAX_SYMS];
    int cnt = 0;
    uint16_t eof_idx = n_entries;
    ht->eof_sym_idx = eof_idx;

    for (uint16_t i = 0; i < n_entries; i++) {
        if (code_lengths[i] > 0) {
            items[cnt].sym_idx = i;
            items[cnt].bit_len = code_lengths[i];
            items[cnt].bytes = sym_bytes[i];
            items[cnt].byte_len = sym_len[i];
            cnt++;
        }
    }
    uint8_t eof_bl = code_lengths[n_entries];
    items[cnt].sym_idx = eof_idx;
    items[cnt].bit_len = eof_bl;
    items[cnt].bytes = BITS_EOF_BYTES;
    items[cnt].byte_len = 13;
    cnt++;

    qsort(items, (size_t)cnt, sizeof(CanonItem), cmp_canon_item);

    for (uint32_t i = 0; i < LUT_SIZE; i++) ht->lut[i] = 0x80000000u;
    ht->n_nodes = 1;
    ht->nodes[0].child[0] = -1;
    ht->nodes[0].child[1] = -1;
    ht->nodes[0].sym_idx = -1;

    uint32_t code = 0;
    uint8_t prev_len = 0;
    for (int i = 0; i < cnt; i++) {
        uint8_t bl = items[i].bit_len;
        code <<= (bl - prev_len);
        prev_len = bl;

        /* Insert into fallback tree (also handles >12-bit codewords) */
        int32_t cur = 0;
        for (int s = (int)bl - 1; s >= 0; s--) {
            int bit = (code >> s) & 1;
            int32_t nxt = ht->nodes[cur].child[bit];
            if (nxt < 0) {
                nxt = ht->n_nodes++;
                if (nxt >= MAX_TREE_NODES) { fprintf(stderr, "tree overflow\n"); exit(2); }
                ht->nodes[nxt].child[0] = -1;
                ht->nodes[nxt].child[1] = -1;
                ht->nodes[nxt].sym_idx = -1;
                ht->nodes[cur].child[bit] = nxt;
            }
            cur = nxt;
        }
        ht->nodes[cur].sym_idx = items[i].sym_idx;

        if (bl <= LUT_BITS) {
            uint32_t fill = 1u << (LUT_BITS - bl);
            uint32_t base = code << (LUT_BITS - bl);
            uint32_t packed = ((uint32_t)bl << 16) | (uint32_t)items[i].sym_idx;
            for (uint32_t k = 0; k < fill; k++) {
                ht->lut[base + k] = packed;
            }
        }
        code += 1;
    }
}

static void init_bit3(Bit3Archive *b, const uint8_t *buf, size_t len) {
    if (len < 9 || memcmp(buf, "BIT3", 4) != 0) { fprintf(stderr, "bad BIT3 magic\n"); exit(2); }
    b->n_entries = rd_u16(buf + 4);
    b->n_files = rd_u16(buf + 6);
    b->n_tables = buf[8];
    size_t pos = 9;
    for (uint16_t i = 0; i < b->n_entries; i++) {
        uint8_t sl = buf[pos++];
        b->sym_len[i] = sl;
        memcpy(b->sym_bytes[i], buf + pos, sl);
        pos += sl;
    }
    for (uint8_t t = 0; t < b->n_tables; t++) {
        build_huff_fast(&b->tables[t], b->n_entries, b->sym_len, b->sym_bytes, buf + pos);
        pos += (size_t)b->n_entries + 1;
    }
    b->index_words = (const uint32_t *)(buf + pos);
    pos += (size_t)b->n_files * 4;
    if (b->n_tables == 1) {
        b->streams[0] = buf + pos;
        b->stream_lens[0] = len - pos;
        b->streams[1] = NULL;
        b->stream_lens[1] = 0;
    } else {
        uint32_t l1 = rd_u32(buf + pos);
        pos += 4;
        b->streams[0] = buf + pos;
        b->stream_lens[0] = l1;
        b->streams[1] = buf + pos + l1;
        b->stream_lens[1] = len - (pos + l1);
    }
}

static size_t bit3_decode_one(const Bit3Archive *b, uint32_t doc_idx, uint8_t *out) {
    uint32_t idx_word;
    memcpy(&idx_word, &b->index_words[doc_idx], 4);
    uint32_t stream_id = (b->n_tables == 2) ? ((idx_word >> 31) & 1u) : 0u;
    uint32_t bit_off = (b->n_tables == 2) ? (idx_word & 0x7FFFFFFFu) : idx_word;

    const HuffTableFast *ht = &b->tables[stream_id];
    const uint8_t *stream = b->streams[stream_id];
    size_t byte_pos = bit_off >> 3;
    int avail = 64 - (int)(bit_off & 7u);
    uint64_t bitbuf = rd_be64(stream + byte_pos) << (bit_off & 7u);
    byte_pos += 8;

    uint8_t *dst = out;
    const uint16_t eof_sym = ht->eof_sym_idx;

    for (;;) {
        if (avail < 32) {
            uint64_t next32 = (uint64_t)__builtin_bswap32(rd_u32(stream + byte_pos));
            bitbuf |= next32 << (32 - avail);
            avail += 32;
            byte_pos += 4;
        }
        uint32_t top = (uint32_t)(bitbuf >> (64 - LUT_BITS));
        uint32_t entry = ht->lut[top];
        uint16_t sym;
        uint8_t bl;
        if ((entry & 0x80000000u) == 0) {
            sym = (uint16_t)(entry & 0xFFFFu);
            bl = (uint8_t)(entry >> 16);
            bitbuf <<= bl;
            avail -= bl;
        } else {
            int32_t cur = 0;
            bl = 0;
            while (ht->nodes[cur].sym_idx < 0) {
                if (avail == 0) {
                    uint64_t next32 = (uint64_t)__builtin_bswap32(rd_u32(stream + byte_pos));
                    bitbuf = next32 << 32;
                    avail = 32;
                    byte_pos += 4;
                }
                int bit = (int)(bitbuf >> 63);
                bitbuf <<= 1;
                avail -= 1;
                cur = ht->nodes[cur].child[bit];
            }
            sym = (uint16_t)ht->nodes[cur].sym_idx;
        }
        if (sym == eof_sym) break;
        uint8_t sl = b->sym_len[sym];
        memcpy(dst, b->sym_bytes[sym], sl);
        dst += sl;
    }
    return (size_t)(dst - out);
}

/* ==================== 2. FSST-255 Fast 8-Byte Word Decoder ==================== */

typedef struct {
    uint16_t n_syms;
    uint16_t n_docs;
    uint8_t sym_len[256];
    uint64_t sym_word[256];
    const uint32_t *ends;
    const uint8_t *payload;
} FsstArchive;

static void init_fsst(FsstArchive *f, const uint8_t *buf, size_t len) {
    if (len < 8 || memcmp(buf, "FSST", 4) != 0) { fprintf(stderr, "bad FSST magic\n"); exit(2); }
    f->n_syms = rd_u16(buf + 4);
    f->n_docs = rd_u16(buf + 6);
    memset(f->sym_len, 0, sizeof(f->sym_len));
    memset(f->sym_word, 0, sizeof(f->sym_word));
    size_t pos = 8;
    for (uint16_t i = 0; i < f->n_syms; i++) f->sym_len[i] = buf[pos++];
    for (uint16_t i = 0; i < f->n_syms; i++) {
        uint8_t sl = f->sym_len[i];
        memcpy(&f->sym_word[i], buf + pos, sl);
        pos += sl;
    }
    f->ends = (const uint32_t *)(buf + pos);
    pos += (size_t)f->n_docs * 4;
    f->payload = buf + pos;
}

static size_t fsst_decode_one(const FsstArchive *f, uint32_t doc_idx, uint8_t *out) {
    uint32_t s_off = (doc_idx == 0) ? 0u : rd_u32((const uint8_t *)&f->ends[doc_idx - 1]);
    uint32_t e_off = rd_u32((const uint8_t *)&f->ends[doc_idx]);
    const uint8_t *p = f->payload + s_off;
    const uint8_t *end = f->payload + e_off;
    uint8_t *dst = out;
    while (p < end) {
        uint8_t code = *p++;
        if (code == 255u) {
            *dst++ = *p++;
        } else {
            uint64_t w = f->sym_word[code];
            memcpy(dst, &w, 8);
            dst += f->sym_len[code];
        }
    }
    return (size_t)(dst - out);
}

/* ==================== 3. ZST3 Reused DCtx + DDict Decoder ==================== */

typedef struct {
    uint32_t dict_len;
    uint16_t n_docs;
    const uint32_t *ends;
    const uint8_t *frames;
    ZSTD_DCtx *dctx;
    ZSTD_DDict *ddict;
} Zst3Archive;

static void init_zst3(Zst3Archive *z, const uint8_t *buf, size_t len) {
    if (len < 10 || memcmp(buf, "ZST3", 4) != 0) { fprintf(stderr, "bad ZST3 magic\n"); exit(2); }
    z->dict_len = rd_u32(buf + 4);
    z->n_docs = rd_u16(buf + 8);
    const uint8_t *dict_ptr = buf + 10;
    size_t pos = 10 + (size_t)z->dict_len;
    z->ends = (const uint32_t *)(buf + pos);
    pos += (size_t)z->n_docs * 4;
    z->frames = buf + pos;
    z->dctx = ZSTD_createDCtx();
    z->ddict = (z->dict_len > 0) ? ZSTD_createDDict(dict_ptr, z->dict_len) : NULL;
}

static size_t zst3_decode_one(const Zst3Archive *z, uint32_t doc_idx, uint8_t *out, size_t out_cap) {
    uint32_t s_off = (doc_idx == 0) ? 0u : rd_u32((const uint8_t *)&z->ends[doc_idx - 1]);
    uint32_t e_off = rd_u32((const uint8_t *)&z->ends[doc_idx]);
    size_t res = z->ddict
        ? ZSTD_decompress_usingDDict(z->dctx, out, out_cap, z->frames + s_off, e_off - s_off, z->ddict)
        : ZSTD_decompressDCtx(z->dctx, out, out_cap, z->frames + s_off, e_off - s_off);
    if (ZSTD_isError(res)) {
        fprintf(stderr, "ZSTD decode error: %s\n", ZSTD_getErrorName(res));
        exit(2);
    }
    return res;
}

/* ==================== 4. DFL3 Raw Headerless DEFLATE (-15) + ZDICT Decoder ==================== */

typedef struct {
    uint32_t dict_len;
    uint16_t n_docs;
    const uint8_t *dict_ptr;
    const uint32_t *ends;
    const uint8_t *blocks;
    z_stream strm;
} Dfl3Archive;

static void init_dfl3(Dfl3Archive *d, const uint8_t *buf, size_t len) {
    if (len < 10 || memcmp(buf, "DFL3", 4) != 0) { fprintf(stderr, "bad DFL3 magic\n"); exit(2); }
    d->dict_len = rd_u32(buf + 4);
    d->n_docs = rd_u16(buf + 8);
    d->dict_ptr = buf + 10;
    size_t pos = 10 + (size_t)d->dict_len;
    d->ends = (const uint32_t *)(buf + pos);
    pos += (size_t)d->n_docs * 4;
    d->blocks = buf + pos;
    memset(&d->strm, 0, sizeof(d->strm));
    if (inflateInit2(&d->strm, -15) != Z_OK) { fprintf(stderr, "inflateInit2 failed\n"); exit(2); }
}

static size_t dfl3_decode_one(Dfl3Archive *d, uint32_t doc_idx, uint8_t *out, size_t out_cap) {
    uint32_t s_off = (doc_idx == 0) ? 0u : rd_u32((const uint8_t *)&d->ends[doc_idx - 1]);
    uint32_t e_off = rd_u32((const uint8_t *)&d->ends[doc_idx]);
    inflateReset(&d->strm);
    if (d->dict_len > 0) {
        if (inflateSetDictionary(&d->strm, d->dict_ptr, d->dict_len) != Z_OK) {
            fprintf(stderr, "inflateSetDictionary failed\n");
            exit(2);
        }
    }
    d->strm.next_in = (Bytef *)(uintptr_t)(d->blocks + s_off);
    d->strm.avail_in = e_off - s_off;
    d->strm.next_out = out;
    d->strm.avail_out = (uInt)out_cap;
    int rc = inflate(&d->strm, Z_FINISH);
    if (rc != Z_STREAM_END) {
        fprintf(stderr, "raw deflate inflate failed rc=%d\n", rc);
        exit(2);
    }
    return d->strm.total_out;
}

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

int main(int argc, char **argv) {
    if (argc != 5) {
        fprintf(stderr, "usage: %s <BIT3|FSST|ZST3|DFL3> <archive.bin> <raw_verify.bin> <num_seeks>\n", argv[0]);
        return 2;
    }
    const char *kind = argv[1];
    size_t arc_len = 0;
    uint8_t *arc_buf = slurp_file(argv[2], &arc_len);
    RawCorpus rc = load_raw_corpus(argv[3]);
    uint64_t num_seeks = (uint64_t)strtoull(argv[4], NULL, 10);

    size_t max_doc = 64;
    for (uint32_t i = 0; i < rc.m_docs; i++) {
        uint32_t s = (i == 0) ? 0u : rc.ends[i - 1];
        uint32_t l = rc.ends[i] - s;
        if (l > max_doc) max_doc = l;
    }
    size_t out_cap = max_doc + 64;
    uint8_t *out = (uint8_t *)malloc(out_cap);

    Bit3Archive *b3 = (Bit3Archive *)calloc(1, sizeof(Bit3Archive));
    FsstArchive *fs = (FsstArchive *)calloc(1, sizeof(FsstArchive));
    Zst3Archive *zs = (Zst3Archive *)calloc(1, sizeof(Zst3Archive));
    Dfl3Archive *df = (Dfl3Archive *)calloc(1, sizeof(Dfl3Archive));
    int mode = 0;

    if (strcmp(kind, "BIT3") == 0) { mode = 1; init_bit3(b3, arc_buf, arc_len); }
    else if (strcmp(kind, "FSST") == 0) { mode = 2; init_fsst(fs, arc_buf, arc_len); }
    else if (strcmp(kind, "ZST3") == 0) { mode = 3; init_zst3(zs, arc_buf, arc_len); }
    else if (strcmp(kind, "DFL3") == 0) { mode = 4; init_dfl3(df, arc_buf, arc_len); }
    else { fprintf(stderr, "unknown codec %s\n", kind); return 2; }

    /* Step 1: Byte-for-byte reverse-order random-access verification across ALL M documents */
    for (int64_t i = (int64_t)rc.m_docs - 1; i >= 0; i--) {
        uint32_t idx = (uint32_t)i;
        size_t got = 0;
        if (mode == 1) got = bit3_decode_one(b3, idx, out);
        else if (mode == 2) got = fsst_decode_one(fs, idx, out);
        else if (mode == 3) got = zst3_decode_one(zs, idx, out, out_cap);
        else got = dfl3_decode_one(df, idx, out, out_cap);

        uint32_t s = (idx == 0) ? 0u : rc.ends[idx - 1];
        uint32_t exp_len = rc.ends[idx] - s;
        if (got != exp_len || memcmp(out, rc.concat + s, exp_len) != 0) {
            fprintf(stderr, "%s mismatch at doc %u (got %zu vs exp %u)\n", kind, idx, got, exp_len);
            return 1;
        }
    }

    /* Step 2: Warmup (2,000 seeks) + Timed pseudo-random single-document seek loop */
    uint64_t rng = 0x9E3779B97F4A7C15ull;
    uint64_t csum = 0;
    for (uint32_t w = 0; w < 2000; w++) {
        rng ^= rng >> 12; rng ^= rng << 25; rng ^= rng >> 27;
        uint32_t idx = (uint32_t)((rng * 0x2545F4914F6CDD1Dull) % rc.m_docs);
        size_t got = (mode == 1) ? bit3_decode_one(b3, idx, out)
                   : (mode == 2) ? fsst_decode_one(fs, idx, out)
                   : (mode == 3) ? zst3_decode_one(zs, idx, out, out_cap)
                                 : dfl3_decode_one(df, idx, out, out_cap);
        csum += out[0] + out[got - 1] + got;
    }

    rng = 0x9E3779B97F4A7C15ull;
    uint64_t decoded_bytes = 0;
    uint64_t t0 = now_ns();
    for (uint64_t k = 0; k < num_seeks; k++) {
        rng ^= rng >> 12; rng ^= rng << 25; rng ^= rng >> 27;
        uint32_t idx = (uint32_t)((rng * 0x2545F4914F6CDD1Dull) % rc.m_docs);
        size_t got = (mode == 1) ? bit3_decode_one(b3, idx, out)
                   : (mode == 2) ? fsst_decode_one(fs, idx, out)
                   : (mode == 3) ? zst3_decode_one(zs, idx, out, out_cap)
                                 : dfl3_decode_one(df, idx, out, out_cap);
        decoded_bytes += got;
        csum ^= (uint64_t)out[got >> 1] + (uint64_t)got;
    }
    uint64_t elapsed_ns = now_ns() - t0;
    double ns_per_seek = (double)elapsed_ns / (double)num_seeks;
    double seeks_per_sec = ((double)num_seeks * 1e9) / (double)elapsed_ns;
    double mib_per_sec = ((double)decoded_bytes / (1024.0 * 1024.0)) / ((double)elapsed_ns * 1e-9);

    printf(
        "{\"codec\":\"%s\",\"verified_docs\":%u,\"archive_bytes\":%zu,\"num_seeks\":%llu,"
        "\"decoded_bytes\":%llu,\"elapsed_ns\":%llu,\"ns_per_seek\":%.2f,"
        "\"seeks_per_sec\":%.1f,\"decoded_mib_per_sec\":%.2f,\"checksum\":%llu}\n",
        kind, rc.m_docs, arc_len, (unsigned long long)num_seeks,
        (unsigned long long)decoded_bytes, (unsigned long long)elapsed_ns,
        ns_per_seek, seeks_per_sec, mib_per_sec, (unsigned long long)csum
    );

    if (mode == 3) {
        if (zs->ddict) ZSTD_freeDDict(zs->ddict);
        ZSTD_freeDCtx(zs->dctx);
    } else if (mode == 4) {
        inflateEnd(&df->strm);
    }
    free(b3); free(fs); free(zs); free(df);
    free(out);
    free(rc.ends);
    free(rc.concat);
    free(arc_buf);
    return 0;
}
