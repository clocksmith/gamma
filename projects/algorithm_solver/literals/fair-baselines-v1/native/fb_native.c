/* fair-baselines-v1 native helper.
 *
 * - archive reader for the uniform container described in fb_native.h
 * - zstd dictionary training, frame / lean-frame / raw-block encoders
 * - zstd frame parser used for measured framing accounting
 * - one timing loop shared by every method (and by candidate codecs)
 *
 * Built as a shared library and loaded from Python with ctypes.
 */
#define ZSTD_STATIC_LINKING_ONLY
#define ZDICT_STATIC_LINKING_ONLY
#define ZSTD_DISABLE_DEPRECATE_WARNINGS
#define ZDICT_DISABLE_DEPRECATE_WARNINGS

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <zdict.h>
#include <zlib.h>
#include <zstd.h>

#include "fb_native.h"

#define FB_ERR ((size_t)-1)

static char fb_err_buf[256];

static void fb_set_err(const char *what, const char *detail) {
    snprintf(fb_err_buf, sizeof(fb_err_buf), "%s%s%s", what, detail ? ": " : "", detail ? detail : "");
}

const char *fb_last_error(void) { return fb_err_buf; }
const char *fb_zstd_version(void) { return ZSTD_versionString(); }
const char *fb_zlib_version(void) { return zlibVersion(); }

int fb_has_fsst(void) {
#ifdef FB_NO_FSST
    return 0;
#else
    return 1;
#endif
}

/* ---------- counting allocator (reader heap accounting) ---------- */

#define FB_MEM_PAD 16

void *fb_mem_alloc(fb_mem *m, size_t size) {
    size_t *p = (size_t *)malloc(size + FB_MEM_PAD);
    if (!p) return NULL;
    p[0] = size;
    m->now += size;
    if (m->now > m->peak) m->peak = m->now;
    return (char *)p + FB_MEM_PAD;
}

void fb_mem_free(fb_mem *m, void *addr) {
    if (!addr) return;
    size_t *p = (size_t *)((char *)addr - FB_MEM_PAD);
    m->now -= p[0];
    free(p);
}

static void *fb_zstd_alloc(void *opaque, size_t size) { return fb_mem_alloc((fb_mem *)opaque, size); }
static void fb_zstd_free(void *opaque, void *addr) { fb_mem_free((fb_mem *)opaque, addr); }
static voidpf fb_zlib_alloc(voidpf opaque, uInt items, uInt size) {
    return fb_mem_alloc((fb_mem *)opaque, (size_t)items * (size_t)size);
}
static void fb_zlib_free(voidpf opaque, voidpf addr) { fb_mem_free((fb_mem *)opaque, addr); }

#ifdef FB_NO_FSST
size_t fb_fsst_decoder_sizeof(void) { return 0; }
unsigned fb_fsst_import(void *decoder, const uint8_t *buf) { (void)decoder; (void)buf; return 0; }
size_t fb_fsst_decode(void *ctx, uint32_t i, uint8_t *dst, size_t cap) {
    (void)ctx; (void)i; (void)dst; (void)cap;
    return FB_ERR;
}
#endif

/* ---------- per-method decode functions ---------- */

static size_t dec_raw(void *ctx, uint32_t i, uint8_t *dst, size_t cap) {
    const fb_reader *r = (const fb_reader *)ctx;
    uint64_t s, e;
    fb_unit_span(r, i, &s, &e);
    size_t n = (size_t)(e - s);
    if (n > cap) return FB_ERR;
    memcpy(dst, r->units + s, n);
    return n;
}

static size_t dec_zstd_frame(void *ctx, uint32_t i, uint8_t *dst, size_t cap) {
    fb_reader *r = (fb_reader *)ctx;
    uint64_t s, e;
    fb_unit_span(r, i, &s, &e);
    size_t res = r->zstd_ddict
        ? ZSTD_decompress_usingDDict((ZSTD_DCtx *)r->zstd_dctx, dst, cap, r->units + s, (size_t)(e - s),
                                     (const ZSTD_DDict *)r->zstd_ddict)
        : ZSTD_decompressDCtx((ZSTD_DCtx *)r->zstd_dctx, dst, cap, r->units + s, (size_t)(e - s));
    return ZSTD_isError(res) ? FB_ERR : res;
}

static size_t dec_zstd_block(void *ctx, uint32_t i, uint8_t *dst, size_t cap) {
    fb_reader *r = (fb_reader *)ctx;
    uint64_t s, e;
    fb_unit_span(r, i, &s, &e);
    size_t n = (size_t)(e - s);
    if (r->aux[i >> 3] & (1u << (i & 7))) {
        if (n > cap) return FB_ERR;
        memcpy(dst, r->units + s, n);
        return n;
    }
    size_t rc = ZSTD_decompressBegin_usingDDict((ZSTD_DCtx *)r->zstd_dctx, (const ZSTD_DDict *)r->zstd_ddict);
    if (ZSTD_isError(rc)) return FB_ERR;
    size_t res = ZSTD_decompressBlock((ZSTD_DCtx *)r->zstd_dctx, dst, cap, r->units + s, n);
    return ZSTD_isError(res) ? FB_ERR : res;
}

static size_t dec_deflate(void *ctx, uint32_t i, uint8_t *dst, size_t cap) {
    fb_reader *r = (fb_reader *)ctx;
    uint64_t s, e;
    fb_unit_span(r, i, &s, &e);
    z_stream *z = (z_stream *)r->zlib_strm;
    inflateReset(z);
    if (r->model_len > 0 && inflateSetDictionary(z, r->model, r->model_len) != Z_OK) return FB_ERR;
    z->next_in = (Bytef *)(uintptr_t)(r->units + s);
    z->avail_in = (uInt)(e - s);
    z->next_out = dst;
    z->avail_out = (uInt)cap;
    if (inflate(z, Z_FINISH) != Z_STREAM_END) return FB_ERR;
    return (size_t)z->total_out;
}

static size_t dec_zstd_group(void *ctx, uint32_t i, uint8_t *dst, size_t cap) {
    fb_reader *r = (fb_reader *)ctx;
    unsigned w = r->index_width;
    uint32_t b = i / r->per_block;
    uint32_t first = b * r->per_block;
    uint64_t s, e;
    fb_unit_span(r, b, &s, &e);
    uint64_t raw_base = first == 0 ? 0 : fb_rd_off(r->rec_index + (size_t)(first - 1) * w, w);
    uint64_t rs = i == 0 ? 0 : fb_rd_off(r->rec_index + (size_t)(i - 1) * w, w);
    uint64_t re = fb_rd_off(r->rec_index + (size_t)i * w, w);
    size_t res = r->zstd_ddict
        ? ZSTD_decompress_usingDDict((ZSTD_DCtx *)r->zstd_dctx, r->scratch, r->scratch_cap, r->units + s,
                                     (size_t)(e - s), (const ZSTD_DDict *)r->zstd_ddict)
        : ZSTD_decompressDCtx((ZSTD_DCtx *)r->zstd_dctx, r->scratch, r->scratch_cap, r->units + s, (size_t)(e - s));
    if (ZSTD_isError(res)) return FB_ERR;
    size_t n = (size_t)(re - rs);
    if (n > cap || (rs - raw_base) + n > res) return FB_ERR;
    memcpy(dst, r->scratch + (rs - raw_base), n);
    return n;
}

static size_t dec_partitioned(void *ctx, uint32_t i, uint8_t *dst, size_t cap) {
    fb_reader *r = (fb_reader *)ctx;
    uint32_t p = 0;
    while (i >= r->part_end[p]) p++;
    fb_reader *sub = r->parts[p];
    return sub->decode(sub, i - (p ? r->part_end[p - 1] : 0), dst, cap);
}

/* ---------- reader ---------- */

static uint32_t rd32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

void fb_close(fb_reader *r);

static fb_reader *fb_open_impl(const uint8_t *buf, size_t len, int copy) {
    if (len < FB_HEADER_BYTES || memcmp(buf, "FBA1", 4) != 0) {
        fb_set_err("bad archive header", NULL);
        return NULL;
    }
    fb_reader *r = (fb_reader *)calloc(1, sizeof(*r));
    if (!r) return NULL;
    r->mem.now = r->mem.peak = sizeof(*r);
    r->owns_archive = copy;
    if (copy) {
        r->archive = (uint8_t *)malloc(len ? len : 1);
        if (!r->archive) { free(r); return NULL; }
        memcpy(r->archive, buf, len);
    } else {
        r->archive = (uint8_t *)(uintptr_t)buf;
    }
    r->archive_len = len;
    const uint8_t *a = r->archive;
    r->method = a[4];
    r->index_width = a[5];
    r->model_kind = a[6];
    r->per_block = a[7];
    r->n_records = rd32(a + 8);
    r->model_len = rd32(a + 12);
    size_t pos = FB_HEADER_BYTES;

    if (r->method == FB_M_PARTITIONED) {
        r->n_parts = r->per_block;
        if (r->n_parts == 0 || pos + (size_t)r->n_parts * 8 > len) goto bad;
        r->parts = (fb_reader **)fb_mem_alloc(&r->mem, r->n_parts * sizeof(fb_reader *));
        r->part_end = (uint32_t *)fb_mem_alloc(&r->mem, r->n_parts * sizeof(uint32_t));
        if (!r->parts || !r->part_end) goto bad;
        memset(r->parts, 0, r->n_parts * sizeof(fb_reader *));
        size_t sub_pos = pos + (size_t)r->n_parts * 8;
        uint32_t total = 0;
        for (uint32_t p = 0; p < r->n_parts; p++) {
            uint32_t cnt = rd32(a + pos + (size_t)p * 8);
            uint32_t sub_len = rd32(a + pos + (size_t)p * 8 + 4);
            if (sub_pos + sub_len > len) goto bad;
            r->parts[p] = fb_open_impl(a + sub_pos, sub_len, 0);
            if (!r->parts[p] || r->parts[p]->n_records != cnt) goto bad;
            total += cnt;
            r->part_end[p] = total;
            sub_pos += sub_len;
        }
        if (total != r->n_records || sub_pos != len) goto bad;
        r->decode = dec_partitioned;
        return r;
    }

    unsigned w = r->index_width;
    if (w < 1 || w > 8) goto bad;
    if (pos + r->model_len > len) goto bad;
    r->model = a + pos;
    pos += r->model_len;
    if (r->method == FB_M_ZSTD_LEAN_GROUP) {
        if (r->per_block == 0) goto bad;
        r->n_units = (r->n_records + r->per_block - 1) / r->per_block;
    } else {
        r->n_units = r->n_records;
    }
    if (pos + (size_t)r->n_units * w > len) goto bad;
    r->unit_index = a + pos;
    pos += (size_t)r->n_units * w;
    if (r->method == FB_M_ZSTD_LEAN_GROUP) {
        if (pos + (size_t)r->n_records * w > len) goto bad;
        r->rec_index = a + pos;
        pos += (size_t)r->n_records * w;
    }
    if (r->method == FB_M_ZSTD_BLOCK) {
        size_t aux_len = ((size_t)r->n_records + 7) / 8;
        if (pos + aux_len > len) goto bad;
        r->aux = a + pos;
        pos += aux_len;
    }
    r->units = a + pos;
    r->units_len = len - pos;
    {
        uint64_t last_end = r->n_units ? fb_rd_off(r->unit_index + (size_t)(r->n_units - 1) * w, w) : 0;
        if (last_end != r->units_len) goto bad;   /* every archive byte is accounted for */
        uint64_t prev = 0;
        for (uint32_t u = 0; u < r->n_units; u++) {
            uint64_t end = fb_rd_off(r->unit_index + (size_t)u * w, w);
            if (end < prev) goto bad;
            prev = end;
        }
    }

    ZSTD_customMem cm;
    cm.customAlloc = fb_zstd_alloc;
    cm.customFree = fb_zstd_free;
    cm.opaque = &r->mem;

    switch (r->method) {
    case FB_M_RAW:
        r->decode = dec_raw;
        break;
    case FB_M_ZSTD_FRAME:
    case FB_M_ZSTD_LEAN_FRAME:
    case FB_M_ZSTD_BLOCK:
    case FB_M_ZSTD_LEAN_GROUP: {
        ZSTD_DCtx *dctx = ZSTD_createDCtx_advanced(cm);
        if (!dctx) goto bad;
        r->zstd_dctx = dctx;
        if (r->method == FB_M_ZSTD_LEAN_FRAME || r->method == FB_M_ZSTD_LEAN_GROUP) {
            if (ZSTD_isError(ZSTD_DCtx_setParameter(dctx, ZSTD_d_format, ZSTD_f_zstd1_magicless))) goto bad;
        }
        if (r->model_len > 0) {
            ZSTD_dictContentType_e t = (r->model_kind == FB_MODEL_ZSTD_RAW) ? ZSTD_dct_rawContent : ZSTD_dct_fullDict;
            r->zstd_ddict = ZSTD_createDDict_advanced(r->model, r->model_len, ZSTD_dlm_byRef, t, cm);
            if (!r->zstd_ddict) goto bad;
        }
        if (r->method == FB_M_ZSTD_LEAN_GROUP) {
            size_t max_raw = 0;
            for (uint32_t b = 0; b < r->n_units; b++) {
                uint32_t first = b * r->per_block;
                uint32_t lastrec = first + r->per_block - 1;
                if (lastrec >= r->n_records) lastrec = r->n_records - 1;
                uint64_t base = first == 0 ? 0 : fb_rd_off(r->rec_index + (size_t)(first - 1) * w, w);
                uint64_t end = fb_rd_off(r->rec_index + (size_t)lastrec * w, w);
                if (end < base) goto bad;
                if ((size_t)(end - base) > max_raw) max_raw = (size_t)(end - base);
            }
            r->scratch_cap = max_raw + 8;
            r->scratch = (uint8_t *)fb_mem_alloc(&r->mem, r->scratch_cap);
            if (!r->scratch) goto bad;
            r->decode = dec_zstd_group;
        } else if (r->method == FB_M_ZSTD_BLOCK) {
            r->decode = dec_zstd_block;
        } else {
            r->decode = dec_zstd_frame;
        }
        break;
    }
    case FB_M_DEFLATE: {
        z_stream *z = (z_stream *)fb_mem_alloc(&r->mem, sizeof(z_stream));
        if (!z) goto bad;
        memset(z, 0, sizeof(*z));
        z->zalloc = fb_zlib_alloc;
        z->zfree = fb_zlib_free;
        z->opaque = &r->mem;
        if (inflateInit2(z, -15) != Z_OK) { fb_mem_free(&r->mem, z); goto bad; }
        r->zlib_strm = z;
        r->decode = dec_deflate;
        break;
    }
    case FB_M_FSST: {
        size_t dsz = fb_fsst_decoder_sizeof();
        if (dsz == 0) { fb_set_err("FSST support not built", NULL); goto bad_noerr; }
        r->fsst_decoder = fb_mem_alloc(&r->mem, dsz);
        if (!r->fsst_decoder) goto bad;
        unsigned used = fb_fsst_import(r->fsst_decoder, r->model);
        if (used == 0 || used != r->model_len) goto bad;
        r->decode = fb_fsst_decode;
        break;
    }
    default:
        goto bad;
    }
    return r;

bad:
    fb_set_err("malformed or unsupported archive", NULL);
bad_noerr:
    fb_close(r);
    return NULL;
}

fb_reader *fb_open(const uint8_t *archive, size_t len) { return fb_open_impl(archive, len, 1); }

void fb_close(fb_reader *r) {
    if (!r) return;
    if (r->parts) {
        for (uint32_t p = 0; p < r->n_parts; p++) fb_close(r->parts[p]);
        fb_mem_free(&r->mem, r->parts);
    }
    if (r->part_end) fb_mem_free(&r->mem, r->part_end);
    if (r->zstd_ddict) ZSTD_freeDDict((ZSTD_DDict *)r->zstd_ddict);
    if (r->zstd_dctx) ZSTD_freeDCtx((ZSTD_DCtx *)r->zstd_dctx);
    if (r->zlib_strm) {
        inflateEnd((z_stream *)r->zlib_strm);
        fb_mem_free(&r->mem, r->zlib_strm);
    }
    if (r->fsst_decoder) fb_mem_free(&r->mem, r->fsst_decoder);
    if (r->scratch) fb_mem_free(&r->mem, r->scratch);
    if (r->owns_archive) free(r->archive);
    free(r);
}

uint32_t fb_count(const fb_reader *r) { return r->n_records; }

size_t fb_decode(fb_reader *r, uint32_t i, uint8_t *dst, size_t cap) {
    if (i >= r->n_records) return FB_ERR;
    return r->decode(r, i, dst, cap);
}

/* Address of the method's decode function, for the shared timing loop. */
fb_decode_fn fb_reader_decode_fn(const fb_reader *r) { return r->decode; }

/* Peak heap bytes held by the reader (contexts, tables, scratch), archive copy excluded. */
size_t fb_reader_heap_peak(const fb_reader *r) {
    size_t total = r->mem.peak;
    for (uint32_t p = 0; p < r->n_parts; p++) total += fb_reader_heap_peak(r->parts[p]);
    return total;
}

/* ---------- zstd dictionary training ---------- */

/* kind 0: fastCover with the zstd CLI `--train` defaults (d=8, f=20, steps=4, split 0.75, accel 1).
 * kind 1: cover with parameter optimisation (`--train-cover` defaults; steps 0 means 40). */
size_t fb_zdict_train(int kind, const uint8_t *samples, const size_t *sizes, unsigned n, uint8_t *dict,
                      size_t cap, int level, unsigned steps) {
    size_t rc;
    if (kind == 0) {
        ZDICT_fastCover_params_t p;
        memset(&p, 0, sizeof(p));
        p.d = 8;
        p.f = 20;
        p.steps = steps ? steps : 4;
        p.splitPoint = 0.75;
        p.accel = 1;
        p.nbThreads = 1;
        p.zParams.compressionLevel = level;
        rc = ZDICT_optimizeTrainFromBuffer_fastCover(dict, cap, samples, sizes, n, &p);
    } else {
        ZDICT_cover_params_t p;
        memset(&p, 0, sizeof(p));
        p.steps = steps;
        p.nbThreads = 1;
        p.zParams.compressionLevel = level;
        rc = ZDICT_optimizeTrainFromBuffer_cover(dict, cap, samples, sizes, n, &p);
    }
    if (ZDICT_isError(rc)) {
        fb_set_err("zstd dictionary training failed", ZDICT_getErrorName(rc));
        return FB_ERR;
    }
    return rc;
}

size_t fb_zdict_header_size(const uint8_t *dict, size_t len) {
    size_t rc = ZDICT_getDictHeaderSize(dict, len);
    return ZDICT_isError(rc) ? FB_ERR : rc;
}

/* ---------- zstd encoders ---------- */

typedef struct fb_zenc {
    ZSTD_CCtx *cctx;
    ZSTD_CDict *cdict;
    ZSTD_compressionParameters cparams;
    int mode;   /* 0 standard frame, 1 lean frame, 2 raw block */
    uint8_t *dict;
    size_t dict_len;
} fb_zenc;

void fb_zenc_free(fb_zenc *e) {
    if (!e) return;
    if (e->cdict) ZSTD_freeCDict(e->cdict);
    if (e->cctx) ZSTD_freeCCtx(e->cctx);
    free(e->dict);
    free(e);
}

/* mode 0: standard frame (magic, content size, dictionary ID when the dictionary has one, no checksum)
 * mode 1: lean frame (magicless, no content size, no dictionary ID, no checksum)
 * mode 2: raw block (block-level API, no frame); max_src is the largest record to be encoded */
fb_zenc *fb_zenc_create(const uint8_t *dict, size_t dict_len, int dict_is_raw, int level, int mode, size_t max_src) {
    fb_zenc *e = (fb_zenc *)calloc(1, sizeof(*e));
    if (!e) return NULL;
    e->mode = mode;
    e->cctx = ZSTD_createCCtx();
    if (!e->cctx) goto fail;
    if (dict_len > 0) {
        e->dict = (uint8_t *)malloc(dict_len);
        if (!e->dict) goto fail;
        memcpy(e->dict, dict, dict_len);
        e->dict_len = dict_len;
    }
    ZSTD_dictContentType_e t = dict_is_raw ? ZSTD_dct_rawContent : ZSTD_dct_fullDict;
    if (mode == 0 || mode == 1) {
        size_t rc = ZSTD_CCtx_setParameter(e->cctx, ZSTD_c_compressionLevel, level);
        if (!ZSTD_isError(rc)) rc = ZSTD_CCtx_setParameter(e->cctx, ZSTD_c_checksumFlag, 0);
        if (!ZSTD_isError(rc)) rc = ZSTD_CCtx_setParameter(e->cctx, ZSTD_c_contentSizeFlag, mode == 0);
        if (!ZSTD_isError(rc)) rc = ZSTD_CCtx_setParameter(e->cctx, ZSTD_c_dictIDFlag, mode == 0);
        if (!ZSTD_isError(rc) && mode == 1) rc = ZSTD_CCtx_setParameter(e->cctx, ZSTD_c_format, ZSTD_f_zstd1_magicless);
        if (!ZSTD_isError(rc) && dict_len > 0)
            rc = ZSTD_CCtx_loadDictionary_advanced(e->cctx, e->dict, dict_len, ZSTD_dlm_byRef, t);
        if (ZSTD_isError(rc)) { fb_set_err("zstd encoder setup failed", ZSTD_getErrorName(rc)); goto fail_noerr; }
    } else {
        if (max_src > ZSTD_BLOCKSIZE_MAX) {
            fb_set_err("record larger than one zstd block (128 KiB)", NULL);
            goto fail_noerr;
        }
        e->cparams = ZSTD_getCParams(level, max_src ? max_src : 1, dict_len);
        if (dict_len > 0) {
            e->cdict = ZSTD_createCDict_advanced(e->dict, dict_len, ZSTD_dlm_byRef, t, e->cparams, ZSTD_defaultCMem);
            if (!e->cdict) { fb_set_err("zstd dictionary rejected", NULL); goto fail_noerr; }
        }
    }
    return e;
fail:
    fb_set_err("zstd encoder allocation failed", NULL);
fail_noerr:
    fb_zenc_free(e);
    return NULL;
}

static size_t fb_zenc_one(fb_zenc *e, const uint8_t *src, size_t n, uint8_t *dst, size_t cap) {
    size_t rc;
    if (e->mode != 2) {
        rc = ZSTD_compress2(e->cctx, dst, cap, src, n);
    } else {
        if (n == 0) return 0;
        if (e->cdict) {
            rc = ZSTD_compressBegin_usingCDict(e->cctx, e->cdict);
        } else {
            ZSTD_parameters p;
            memset(&p, 0, sizeof(p));
            p.cParams = e->cparams;
            rc = ZSTD_compressBegin_advanced(e->cctx, NULL, 0, p, ZSTD_CONTENTSIZE_UNKNOWN);
        }
        if (!ZSTD_isError(rc)) rc = ZSTD_compressBlock(e->cctx, dst, cap, src, n);
    }
    if (ZSTD_isError(rc)) {
        fb_set_err("zstd compression failed", ZSTD_getErrorName(rc));
        return FB_ERR;
    }
    return rc;
}

/* Compress n records given back to back in `src`. Writes the outputs back to back into `dst`
 * and each output size into out_sizes. In raw-block mode an output size of 0 means "store this
 * record uncompressed". Returns the total output bytes, or (size_t)-1. */
size_t fb_zenc_compress_many(fb_zenc *e, const uint8_t *src, const size_t *sizes, size_t n, uint8_t *dst,
                             size_t cap, size_t *out_sizes) {
    size_t in_pos = 0, out_pos = 0;
    for (size_t i = 0; i < n; i++) {
        size_t rc = fb_zenc_one(e, src + in_pos, sizes[i], dst + out_pos, cap - out_pos);
        if (rc == FB_ERR) return FB_ERR;
        out_sizes[i] = rc;
        out_pos += rc;
        in_pos += sizes[i];
    }
    return out_pos;
}

size_t fb_zstd_compress_bound(size_t n) { return ZSTD_compressBound(n); }

/* Measured framing of one zstd frame.
 * out[0] frame header bytes (magic included when present), out[1] block header bytes,
 * out[2] checksum bytes, out[3] block content bytes. Returns 0 when the four sum to len. */
int fb_zstd_frame_account(const uint8_t *f, size_t len, int magicless, uint32_t out[4]) {
    ZSTD_FrameHeader h;
    size_t rc = ZSTD_getFrameHeader_advanced(&h, f, len, magicless ? ZSTD_f_zstd1_magicless : ZSTD_f_zstd1);
    if (rc != 0) return -1;
    size_t pos = h.headerSize;
    uint32_t block_headers = 0, content = 0;
    for (;;) {
        if (pos + 3 > len) return -1;
        uint32_t bh = (uint32_t)f[pos] | ((uint32_t)f[pos + 1] << 8) | ((uint32_t)f[pos + 2] << 16);
        pos += 3;
        block_headers += 3;
        uint32_t type = (bh >> 1) & 3u;
        uint32_t size = bh >> 3;
        if (type == 3) return -1;
        uint32_t stored = (type == 1) ? 1u : size;
        if (pos + stored > len) return -1;
        pos += stored;
        content += stored;
        if (bh & 1u) break;
    }
    uint32_t checksum = h.checksumFlag ? 4u : 0u;
    if (pos + checksum != len) return -1;
    out[0] = (uint32_t)h.headerSize;
    out[1] = block_headers;
    out[2] = checksum;
    out[3] = content;
    return 0;
}

/* ---------- timing ---------- */

static inline uint64_t fb_now_ns(void) {
#ifdef __APPLE__
    return clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
#endif
}

/* Smallest non-zero step of the timer and the mean cost of one timer read. */
void fb_timer_probe(double *tick_ns, double *read_cost_ns) {
    enum { N = 200000 };
    uint64_t min_step = UINT64_MAX;
    uint64_t t_first = fb_now_ns(), prev = t_first, t = t_first;
    for (int k = 0; k < N; k++) {
        t = fb_now_ns();
        if (t != prev && t - prev < min_step) min_step = t - prev;
        prev = t;
    }
    *tick_ns = (min_step == UINT64_MAX) ? 0.0 : (double)min_step;
    *read_cost_ns = (double)(t - t_first) / (double)N;
}

static inline uint32_t fb_next_index(uint64_t *rng, uint32_t n) {
    uint64_t x = *rng;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *rng = x;
    return (uint32_t)((x * 0x2545F4914F6CDD1Dull) % n);
}

/* The one lookup loop used for every method. Everything is in memory.
 *
 *   pass 1  n_lookups pseudo-random single-record lookups with one timer read before and one
 *           after the whole pass: *loop_total_ns
 *   pass 2  the same sequence again, each lookup timed on its own: samples_ns[k]
 *   then    per-record means of the pass-2 samples in rec_sum_ns / rec_cnt. A sample longer than
 *           8x its record's plain mean plus 2000 ns is treated as an interrupted lookup and left
 *           out of that record's mean; *trimmed counts them. They stay in samples_ns.
 *
 * Returns 0, or -1 if any lookup fails. */
int fb_time_lookups(fb_decode_fn fn, void *ctx, uint32_t n_records, uint64_t n_lookups, uint64_t warmup,
                    uint64_t seed, size_t out_cap, uint32_t *samples_ns, double *rec_sum_ns, uint32_t *rec_cnt,
                    uint64_t *loop_total_ns, uint64_t *decoded_bytes, uint64_t *checksum, uint64_t *trimmed) {
    if (n_records == 0) return -1;
    uint8_t *out = (uint8_t *)calloc(1, out_cap + 64);
    if (!out) return -1;
    uint64_t rng = seed, csum = 0, bytes = 0;
    int rc = 0;
    for (uint64_t k = 0; k < warmup; k++) {
        uint32_t idx = fb_next_index(&rng, n_records);
        size_t got = fn(ctx, idx, out, out_cap);
        if (got == FB_ERR) { rc = -1; goto done; }
        csum += (uint64_t)out[got >> 1] + got;
    }
    rng = seed;
    uint64_t t0 = fb_now_ns();
    for (uint64_t k = 0; k < n_lookups; k++) {
        uint32_t idx = fb_next_index(&rng, n_records);
        size_t got = fn(ctx, idx, out, out_cap);
        if (got == FB_ERR) { rc = -1; goto done; }
        bytes += got;
        csum ^= (uint64_t)out[got >> 1] + got;
    }
    *loop_total_ns = fb_now_ns() - t0;
    rng = seed;
    for (uint64_t k = 0; k < n_lookups; k++) {
        uint32_t idx = fb_next_index(&rng, n_records);
        uint64_t a = fb_now_ns();
        size_t got = fn(ctx, idx, out, out_cap);
        uint64_t b = fb_now_ns();
        if (got == FB_ERR) { rc = -1; goto done; }
        uint64_t dt = b - a;
        samples_ns[k] = dt > UINT32_MAX ? UINT32_MAX : (uint32_t)dt;
        rec_sum_ns[idx] += (double)dt;
        rec_cnt[idx] += 1;
        csum ^= (uint64_t)out[got >> 1] + got;
    }
    {
        double *limit = (double *)malloc((size_t)n_records * sizeof(double));
        if (!limit) { rc = -1; goto done; }
        for (uint32_t r = 0; r < n_records; r++) {
            limit[r] = rec_cnt[r] ? 8.0 * (rec_sum_ns[r] / rec_cnt[r]) + 2000.0 : 0.0;
            rec_sum_ns[r] = 0.0;
            rec_cnt[r] = 0;
        }
        uint64_t cut = 0;
        rng = seed;
        for (uint64_t k = 0; k < n_lookups; k++) {
            uint32_t idx = fb_next_index(&rng, n_records);
            if ((double)samples_ns[k] > limit[idx]) { cut++; continue; }
            rec_sum_ns[idx] += (double)samples_ns[k];
            rec_cnt[idx] += 1;
        }
        *trimmed = cut;
        free(limit);
    }
    *decoded_bytes = bytes;
    *checksum = csum;
done:
    free(out);
    return rc;
}
