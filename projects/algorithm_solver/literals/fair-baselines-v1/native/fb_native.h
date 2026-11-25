/* fair-baselines-v1 native helper: shared declarations.
 *
 * One archive container is used by every baseline, so the byte accounting has the
 * same form for every method:
 *
 *   header   16 bytes   "FBA1", method, index_width, model_kind, records_per_block,
 *                       n_records (u32 LE), model_len (u32 LE)
 *   model    model_len  dictionary / symbol table (may be empty)
 *   index    n_units * index_width          end offset of each stored unit
 *            (+ n_records * index_width     raw end offset of each record, block method only)
 *   aux      ceil(n_records / 8)            stored-raw flags, raw-zstd-block method only
 *   units    the stored units (one per record, or one per block of records)
 *
 * A reader is opened on the serialized archive bytes only.
 */
#ifndef FB_NATIVE_H
#define FB_NATIVE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define FB_HEADER_BYTES 16

enum {
    FB_M_RAW = 0,              /* uncompressed records */
    FB_M_ZSTD_FRAME = 1,       /* one standard zstd frame per record */
    FB_M_ZSTD_LEAN_FRAME = 2,  /* one magicless zstd frame per record */
    FB_M_ZSTD_BLOCK = 3,       /* one raw zstd block per record, no frame */
    FB_M_DEFLATE = 4,          /* one raw DEFLATE stream per record */
    FB_M_FSST = 5,             /* reference FSST, one string per record */
    FB_M_ZSTD_LEAN_GROUP = 6,  /* one magicless zstd frame per block of N records */
    FB_M_PARTITIONED = 7       /* several sub-archives, one per record group */
};

enum {
    FB_MODEL_NONE = 0,
    FB_MODEL_ZSTD_DICT = 1,      /* dictionary in zstd dictionary format */
    FB_MODEL_ZSTD_RAW = 2,       /* raw-content zstd dictionary */
    FB_MODEL_DEFLATE_DICT = 3,   /* DEFLATE preset dictionary */
    FB_MODEL_FSST_TABLE = 4      /* fsst_export() bytes */
};

/* Decode record i into dst (capacity cap). Returns the record length, or (size_t)-1 on error.
 * A candidate codec that wants native timing exports a function with this signature. */
typedef size_t (*fb_decode_fn)(void *ctx, uint32_t i, uint8_t *dst, size_t cap);

typedef struct fb_mem {
    size_t now;
    size_t peak;
} fb_mem;

typedef struct fb_reader fb_reader;

struct fb_reader {
    uint8_t method;
    uint8_t index_width;
    uint8_t model_kind;
    uint8_t per_block;
    uint32_t n_records;
    uint32_t n_units;
    uint32_t model_len;
    const uint8_t *model;
    const uint8_t *unit_index;   /* n_units end offsets */
    const uint8_t *rec_index;    /* n_records raw end offsets (block method) */
    const uint8_t *aux;          /* stored-raw flags (raw zstd block method) */
    const uint8_t *units;
    size_t units_len;
    void *zstd_dctx;
    void *zstd_ddict;
    void *zlib_strm;
    void *fsst_decoder;
    uint8_t *scratch;
    size_t scratch_cap;
    /* partitioned archives */
    uint32_t n_parts;
    fb_reader **parts;
    uint32_t *part_end;          /* cumulative record counts */
    fb_decode_fn decode;
    fb_mem mem;                  /* heap used by the reader, archive copy excluded */
    uint8_t *archive;            /* private copy of the archive bytes */
    size_t archive_len;
    int owns_archive;
};

static inline uint64_t fb_rd_off(const uint8_t *p, unsigned w) {
    switch (w) {
    case 4: return (uint64_t)p[0] | ((uint64_t)p[1] << 8) | ((uint64_t)p[2] << 16) | ((uint64_t)p[3] << 24);
    case 2: return (uint64_t)p[0] | ((uint64_t)p[1] << 8);
    case 1: return (uint64_t)p[0];
    case 3: return (uint64_t)p[0] | ((uint64_t)p[1] << 8) | ((uint64_t)p[2] << 16);
    default: {
        uint64_t v = 0;
        for (unsigned k = 0; k < w; k++) v |= (uint64_t)p[k] << (8 * k);
        return v;
    }
    }
}

/* [start, end) of stored unit u */
static inline void fb_unit_span(const fb_reader *r, uint32_t u, uint64_t *s, uint64_t *e) {
    unsigned w = r->index_width;
    *s = (u == 0) ? 0 : fb_rd_off(r->unit_index + (size_t)(u - 1) * w, w);
    *e = fb_rd_off(r->unit_index + (size_t)u * w, w);
}

void *fb_mem_alloc(fb_mem *m, size_t size);
void fb_mem_free(fb_mem *m, void *addr);

/* Implemented in fb_fsst_shim.cpp when the reference FSST sources are available. */
size_t fb_fsst_decoder_sizeof(void);
unsigned fb_fsst_import(void *decoder, const uint8_t *buf);
size_t fb_fsst_decode(void *ctx, uint32_t i, uint8_t *dst, size_t cap);

#ifdef __cplusplus
}
#endif
#endif
