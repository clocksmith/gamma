#ifndef GAMMA_FX2_ATTENTION_ANCHOR_V1_H
#define GAMMA_FX2_ATTENTION_ANCHOR_V1_H
#include <cstdint>
// Mode 0: parent FIFO. Mode 1: retain article inputs 0..3.
// Mode 2: matched-capacity control retaining article inputs 4..7.
// Original post-RoPE keys, attention arithmetic and article resets are unchanged.
#ifndef GAMMA_ANCHOR_MODE
#error "GAMMA_ANCHOR_MODE must reach the attention translation unit"
#endif
static_assert(GAMMA_ANCHOR_MODE >= 0 && GAMMA_ANCHOR_MODE <= 2, "anchor mode");
inline int gamma_attention_slot(std::int64_t t) {
#if GAMMA_ANCHOR_MODE == 0
    return static_cast<int>(t % 1024);
#else
    if (t < 1024) return static_cast<int>(t);
    const int r = static_cast<int>((t - 1024) % 1020);
#if GAMMA_ANCHOR_MODE == 1
    return r + 4;
#else
    return r < 4 ? r : r + 4;
#endif
#endif
}
#endif
