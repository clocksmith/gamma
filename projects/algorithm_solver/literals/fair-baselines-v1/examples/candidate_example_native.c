/* Native decoder for the example plug-in (examples/candidate_example.py).
 * Shows the three functions a candidate exports to be timed in the harness's shared loop. */
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    const uint8_t *index;
    const uint8_t *body;
    uint32_t count;
} xor_ctx;

static uint32_t rd32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

/* The harness keeps the archive bytes alive until xor_close(). */
void *xor_open(const uint8_t *archive, size_t len) {
    if (len < 8 || memcmp(archive, "XOR1", 4) != 0) return NULL;
    xor_ctx *c = (xor_ctx *)malloc(sizeof(*c));
    if (!c) return NULL;
    c->count = rd32(archive + 4);
    if (8 + (size_t)c->count * 4 > len) { free(c); return NULL; }
    c->index = archive + 8;
    c->body = archive + 8 + (size_t)c->count * 4;
    return c;
}

size_t xor_decode(void *ctx, uint32_t i, uint8_t *dst, size_t cap) {
    const xor_ctx *c = (const xor_ctx *)ctx;
    uint32_t start = i ? rd32(c->index + (size_t)(i - 1) * 4) : 0;
    uint32_t end = rd32(c->index + (size_t)i * 4);
    size_t n = end - start;
    if (n > cap) return (size_t)-1;
    for (size_t k = 0; k < n; k++) dst[k] = c->body[start + k] ^ 0x5A;
    return n;
}

void xor_close(void *ctx) { free(ctx); }
