// Exact next-byte constraints for the pinned WRT format. No learned parameters.
#ifndef GAMMA_WRT_NATIVE_V1_HPP
#define GAMMA_WRT_NATIVE_V1_HPP
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
#ifdef GAMMA_WRT_OBSERVE
#include "gamma-wrt-observer.h"
#endif
namespace gamma_wrt {
inline void fail() { std::fputs("invalid WRT constraint state\n", stderr); std::_Exit(125); }
inline unsigned swap(unsigned c) {
  if (c >= 123 && c < 127) c -= 43;
  else if (c >= 80 && c < 84) c += 43;
  else if ((c >= 58 && c <= 63) || (c >= 74 && c <= 79)) c ^= 112;
  if (c == 88 || c == 96) c ^= 56;
  return c;
}
class Grammar {
 public:
  uint64_t seen = 0;
  unsigned prefix = 1, count = 0, length = 0, pending[2] = {};
  bool escape = false, word = false;
  unsigned char vocab[256] = {}, tree[512] = {};
  void init(unsigned n, const std::vector<bool>& v) {
    if (!n || n > 44880 || v.size() != 256) fail();
    *this = Grammar(); count = n;
    for (unsigned c = 0; c < 256; ++c) vocab[c] = v[c];
    rebuild();
  }
  bool allowed(unsigned c) const {
    if (!seen) return c == 7;
    c = swap(c);
    if (escape) return c == 6 || c == 7 || c == 12 || c == 64 || c >= 128;
    if (length == 2)
      return c >= 128 && c < 208 &&
        3920 + (pending[0]-240)*2560 + (pending[1]-208)*80 + c-128 < count;
    if (length == 1) {
      if (c >= 128 && c < 208) return 80 + (pending[0]-208)*80 + c-128 < count;
      return pending[0] >= 240 && c >= 208 && c < 240 &&
        3920 + (pending[0]-240)*2560 + (c-208)*80 < count;
    }
    if (c < 128) return !word || (c >= 97 && c <= 122);
    if (c < 208) return c-128 < count;
    return 80 + (c-208)*80 < count ||
      (c >= 240 && 3920 + (c-240)*2560 < count);
  }
  void rebuild() {
    for (unsigned c = 0; c < 256; ++c) tree[256+c] = vocab[c] && allowed(c);
    for (unsigned p = 255; p; --p) tree[p] = tree[2*p] | tree[2*p+1];
    if (!tree[1]) fail();
  }
  int forced() const {
    bool z = tree[2*prefix], o = tree[2*prefix+1];
    if (!z && !o) fail();
    return z && o ? -1 : int(o);
  }
  void state(unsigned char* out) const {
    for (unsigned i = 0; i < 8; ++i) out[i] = seen >> (8*i);
    out[8] = prefix; out[9] = prefix >> 8;
    out[10] = escape; out[11] = word; out[12] = length;
    out[13] = length ? pending[0] : 0;
    out[14] = length == 2 ? pending[1] : 0; out[15] = 0;
  }
  void observe(unsigned y) {
    if (y > 1 || !tree[2*prefix+y]) fail();
    prefix = 2*prefix+y;
    if (prefix < 256) return;
    unsigned c = swap(prefix-256); prefix = 1;
    if (!seen++) { rebuild(); return; }
    if (escape) escape = false;
    else if (length) {
      if (c < 208) { length = 0; word = false; }
      else pending[length++] = c;
    } else if (c == 12) escape = true;
    else if (c == 6 || c == 7 || c == 64) word = true;
    else {
      if (c >= 208) { pending[0] = c; length = 1; }
      word = false;
    }
    rebuild();
  }
  void finish() const { if (!seen || prefix != 1 || length || escape || word) fail(); }
};
inline Grammar grammar;
inline void init(FILE* dictionary, const std::vector<bool>& vocab) {
  if (!dictionary) fail();
  long old = std::ftell(dictionary); std::rewind(dictionary);
  unsigned n = 0; bool word = false; int c;
  while ((c = std::getc(dictionary)) != EOF) {
    if (c >= 'a' && c <= 'z') word = true;
    else if (word) { ++n; word = false; }
  }
  if (std::ferror(dictionary) || old < 0 || std::fseek(dictionary, old, SEEK_SET)) fail();
  grammar.init(n, vocab);
}
inline int forced() {
  int bit = grammar.forced();
#ifdef GAMMA_WRT_BOOKKEEPING
  return -1;
#else
  return bit;
#endif
}
inline void observe(unsigned bit, unsigned parent, int forced_bit) {
  grammar.observe(bit);
#ifdef GAMMA_WRT_OBSERVE
  unsigned char row[20]; row[0] = parent; row[1] = parent >> 8;
  row[2] = bit; row[3] = forced_bit < 0 ? 2 : forced_bit;
  grammar.state(row+4); gamma_wrt_observer::write(row);
#endif
}
} // namespace gamma_wrt
#endif
