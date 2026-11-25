// fair-baselines-v1: thin C-ABI shim over the reference FSST library (github.com/cwida/fsst, MIT).
// Compiled only when the reference sources are available; they are not vendored here.
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "fsst.h"

#include "fb_native.h"

extern "C" {

size_t fb_fsst_decoder_sizeof(void) { return sizeof(fsst_decoder_t); }

unsigned fb_fsst_import(void *decoder, const uint8_t *buf) {
    return fsst_import(static_cast<fsst_decoder_t *>(decoder), buf);
}

// Decode function used by the reader; fsst_decompress() is the reference inline decoder.
size_t fb_fsst_decode(void *ctx, uint32_t i, uint8_t *dst, size_t cap) {
    const fb_reader *r = static_cast<const fb_reader *>(ctx);
    uint64_t s, e;
    fb_unit_span(r, i, &s, &e);
    size_t n = fsst_decompress(static_cast<const fsst_decoder_t *>(r->fsst_decoder), static_cast<size_t>(e - s),
                               r->units + s, cap, dst);
    return n > cap ? static_cast<size_t>(-1) : n;
}

// Build a symbol table from n strings given back to back in `concat`.
void *fb_fsst_train(const uint8_t *concat, const size_t *lens, size_t n) {
    std::vector<const unsigned char *> ptrs(n ? n : 1);
    size_t pos = 0;
    for (size_t i = 0; i < n; i++) {
        ptrs[i] = concat + pos;
        pos += lens[i];
    }
    return fsst_create(n, lens, ptrs.data(), 0);
}

size_t fb_fsst_max_header(void) { return FSST_MAXHEADER; }

// Serialized symbol table exactly as fsst_export() writes it.
size_t fb_fsst_export(void *encoder, uint8_t *buf) {
    return fsst_export(static_cast<fsst_encoder_t *>(encoder), buf);
}

void fb_fsst_destroy(void *encoder) { fsst_destroy(static_cast<fsst_encoder_t *>(encoder)); }

// Compress n strings. Outputs are written back to back into `out`; len_out[i] is each size.
// Returns the total output bytes, or (size_t)-1 if the output buffer was too small.
size_t fb_fsst_compress(void *encoder, const uint8_t *concat, const size_t *lens, size_t n, uint8_t *out,
                        size_t out_cap, size_t *len_out) {
    std::vector<const unsigned char *> in_ptrs(n ? n : 1);
    std::vector<unsigned char *> out_ptrs(n ? n : 1);
    size_t pos = 0;
    for (size_t i = 0; i < n; i++) {
        in_ptrs[i] = concat + pos;
        pos += lens[i];
    }
    size_t done = fsst_compress(static_cast<fsst_encoder_t *>(encoder), n, lens, in_ptrs.data(), out_cap, out,
                                len_out, out_ptrs.data());
    if (done != n) return static_cast<size_t>(-1);
    size_t total = 0;
    for (size_t i = 0; i < n; i++) {
        // the reference writes outputs contiguously in input order; check rather than assume
        if (out_ptrs[i] != out + total) return static_cast<size_t>(-1);
        total += len_out[i];
    }
    return total;
}

}  // extern "C"
