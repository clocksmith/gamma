// weights_io_compressed: decoder for the losslessly compressed weights files
// written by pysrc/weights_compress.py (must stay in exact sync with it).
//
// format v1, magic FX2TFWC1: same container as FX2TFW01 but every DT_I8
// payload (quantized weights, 15 possible values in [-7, 7]) is range-coded
// with a uniform 1/15 model, i.e. log2(15) = 3.907 bits per weight; all other
// payloads and the metadata are raw.
//
// format v2, magic FX2TFWC2: one range-coded stream with adaptive binary
// models (LZMA-style 11-bit probabilities); rope.sin/rope.cos are not stored
// but recomputed with a bit-exact host port of CUDA libdevice
// __nv_sinf/__nv_cosf; DT_I8 uses an adaptive 15-symbol tree, DT_BF16 hi/lo
// byte models, DT_F32/DT_I32 per-byte-plane models, names an order-2
// character model and metadata an order-1 byte model.

#include "weights_io.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace fx2 {

namespace {

[[noreturn]] void die(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  std::fprintf(stderr, "weights_io_compressed: ");
  std::vfprintf(stderr, fmt, ap);
  std::fprintf(stderr, "\n");
  va_end(ap);
  std::exit(1);
}

size_t dtype_size(uint8_t dtype) {
  switch (dtype) {
    case DT_I8:
      return 1;
    case DT_BF16:
      return 2;
    case DT_F32:
      return 4;
    case DT_I32:
      return 4;
    default:
      die("unknown dtype code %u", unsigned(dtype));
  }
}

struct Reader {
  const uint8_t* p;
  size_t left;
  const char* path;

  void need(size_t n) {
    if (left < n) die("%s: truncated file (need %zu more bytes)", path, n);
  }
  void read(void* dst, size_t n) {
    need(n);
    std::memcpy(dst, p, n);
    p += n;
    left -= n;
  }
  uint32_t u32() {
    uint32_t v;
    read(&v, 4);
    return v;
  }
  uint8_t u8() {
    uint8_t v;
    read(&v, 1);
    return v;
  }
};

// byte-wise range decoder matching pysrc/weights_compress.py RangeDecoder
// (LZMA-style: 32-bit range, renormalization below 2^24)
struct RangeDecoder {
  const uint8_t* p;
  const uint8_t* end;
  uint32_t range = 0xFFFFFFFFu;
  uint32_t code = 0;

  RangeDecoder(const uint8_t* data, size_t len) : p(data), end(data + len) {
    p++;  // the first byte is the encoder's initial zero cache
    for (int i = 0; i < 4; i++) code = (code << 8) | byte();
  }
  uint8_t byte() { return p < end ? *p++ : 0; }
  void normalize() {
    while (range < (1u << 24)) {
      code = (code << 8) | byte();
      range <<= 8;
    }
  }
  uint32_t decode_uniform(uint32_t tot) {
    uint32_t r = range / tot;
    uint32_t s = code / r;
    if (s > tot - 1) s = tot - 1;
    code -= r * s;
    range = r;
    normalize();
    return s;
  }
};

void decode_i8_uniform15(const uint8_t* stream, size_t stream_len, int8_t* out,
                         size_t count) {
  RangeDecoder rd(stream, stream_len);
  for (size_t i = 0; i < count; i++)
    out[i] = int8_t(int(rd.decode_uniform(15)) - 7);
}

// ---------------------------------------------------------------------------
// format v2
// ---------------------------------------------------------------------------

// payload encodings (pysrc/weights_compress.py)
enum : uint8_t {
  ENC_RAW = 0,
  ENC_INT4 = 1,
  ENC_BF16 = 2,
  ENC_PLANE4 = 3,
  ENC_ROPE_SIN = 4,
  ENC_ROPE_COS = 5,
};

// --- bit-exact host port of CUDA libdevice __nv_sinf/__nv_cosf --------------
// transcribed from the __nv_sinf/__nv_cosf LLVM IR of CUDA 13.0's
// libdevice.10.bc; verified bit-identical to the rope tables computed by
// torch.sin/cos on CUDA over all 8388608 table entries (incl. 25457
// Payne-Hanek slowpath arguments).  cos(a) is sin's body with quadrant + 1.

inline float fbits(uint32_t u) {
  float f;
  std::memcpy(&f, &u, 4);
  return f;
}

const uint32_t kI2OverPi[6] = {0x3C439041u, 0xDB629599u, 0xF534DDC0u,
                               0xFC2757D1u, 0x4E441529u, 0xA2F9836Eu};

// __internal_trig_reduction_slowpath: Payne-Hanek for |a| >= 105615
float trig_slowpath(float a, int* quadrant) {
  uint32_t ia;
  std::memcpy(&ia, &a, 4);
  uint32_t sign = ia & 0x80000000u;
  int32_t e = (int32_t)((ia >> 23) & 0xffu) - 128;
  ia = (ia << 8) | 0x80000000u;

  uint32_t result[7];
  uint32_t hi = 0;
  for (int k = 0; k < 6; k++) {
    uint64_t p = (uint64_t)kI2OverPi[k] * ia + hi;
    result[k] = (uint32_t)p;
    hi = (uint32_t)(p >> 32);
  }
  result[6] = hi;

  int idx = 4 - ((uint32_t)e >> 5);  // e >= 16 on this path
  int sh = e & 31;
  uint32_t rhi = result[idx + 2], rlo = result[idx + 1];
  if (sh) {
    rhi = (result[idx + 2] << sh) + (result[idx + 1] >> (32 - sh));
    rlo = (result[idx + 1] << sh) + (result[idx] >> (32 - sh));
  }
  uint32_t q = rhi >> 30;
  uint32_t nhi = (rhi << 2) + (rlo >> 30);
  uint32_t nlo = rlo << 2;
  uint32_t top = nhi >> 31;
  q += top;
  int32_t qi = (int32_t)q;
  if (sign) qi = -qi;
  uint32_t s2 = sign;
  if (top) {
    nhi = ~nhi;
    nlo = ~nlo;
    s2 = sign ^ 0x80000000u;
  }
  *quadrant = qi;
  int64_t prod = (int64_t)(((uint64_t)nhi << 32) | nlo);
  double dscale;
  uint64_t dbits = 0x3BF921FB54442D19ull;  // pi/2 * 2^-64
  std::memcpy(&dscale, &dbits, 8);
  float r = (float)((double)prod * dscale);
  if (s2) r = -r;
  return r;
}

// __nv_sinf(a) for cos_bias 0, __nv_cosf(a) for cos_bias 1
float sincosf_cuda(float a, int cos_bias) {
  int i = (int)lrintf(a * fbits(0x3F22F983u));  // __float2int_rn(a * 2/pi)
  float j = (float)i;
  float t = fmaf(j, fbits(0xBFC90FDAu), a);
  t = fmaf(j, fbits(0xB3A22168u), t);
  t = fmaf(j, fbits(0xA7C234C5u), t);
  if (fabsf(a) >= 105615.0f) {
    if (std::isinf(a)) {
      t = a * 0.0f;
      i = 0;
    } else {
      t = trig_slowpath(a, &i);
    }
  }
  i += cos_bias;
  float x2 = t * t;
  float base = (i & 1) ? 1.0f : t;
  float p = fmaf(x2, base, 0.0f);
  float c = (i & 1) ? fmaf(fbits(0x37CBAC00u), x2, fbits(0xBAB607EDu))
                    : fbits(0xB94D4153u);
  c = fmaf(c, x2, (i & 1) ? fbits(0x3D2AAABBu) : fbits(0x3C0885E4u));
  c = fmaf(c, x2, (i & 1) ? fbits(0xBEFFFFFFu) : fbits(0xBE2AAAA8u));
  float z = fmaf(c, p, base);
  if (i & 2) z = fmaf(z, -1.0f, 0.0f);
  return z;
}

// --- adaptive binary range decoder (LZMA-style, 11-bit probs, shift-5) ------

// Gamma GFX2MAR1 loader, derived from the pinned public FX2 coder and
// Gamma's measured fx2_weight_format_v1.hpp. Preserve upstream GPLv3 LICENSE.
// No generic transcoder or predictor changes are linked into this loader.
constexpr uint64_t kGammaExpandedLimit = 128ull << 20;
constexpr size_t kGammaFileLimit = size_t(8) << 20;
constexpr uint32_t kGammaTensorLimit = 4096;
using GammaHistogram = std::array<uint32_t, 15>;
struct GammaHistogramRecord { uint32_t index; GammaHistogram counts; };
struct GammaMarginal {
  unsigned mode = 0;
  GammaHistogram global{};
  std::vector<GammaHistogramRecord> records;
};

GammaMarginal gamma_read_marginal(Reader& r, uint32_t count) {
  GammaMarginal result;
  result.mode = r.u8();
  if (result.mode != 1 && result.mode != 2) die("%s: invalid marginal mode", r.path);
  const uint32_t n = r.u32();
  if (count > kGammaTensorLimit || n > count) die("%s: marginal tensor count exceeds bound", r.path);
  r.need(size_t(60) + size_t(n) * 64 + 5);
  for (unsigned s = 0; s < 15; ++s) result.global[s] = r.u32();
  std::array<uint64_t, 15> sums{};
  uint64_t total = 0;
  for (uint32_t k = 0; k < n; ++k) {
    GammaHistogramRecord record{r.u32(), {}};
    if (record.index >= count || (k && record.index <= result.records.back().index))
      die("%s: marginal indices must be unique, ordered and in range", r.path);
    for (unsigned s = 0; s < 15; ++s) {
      record.counts[s] = r.u32();
      total += record.counts[s];
      sums[s] += record.counts[s];
      if (total > kGammaExpandedLimit) die("%s: marginal histogram exceeds bound", r.path);
    }
    result.records.push_back(record);
  }
  for (unsigned s = 0; s < 15; ++s)
    if (sums[s] != result.global[s]) die("%s: marginal global/local counts differ", r.path);
  return result;
}

std::array<uint16_t, 16> gamma_fixed_tree(const GammaHistogram& counts) {
  std::array<uint64_t, 32> totals{};
  for (unsigned s = 0; s < 15; ++s) totals[16 + s] = counts[s];
  std::array<uint16_t, 16> tree{};
  tree.fill(1024);
  for (unsigned node = 15; node; --node) {
    const uint64_t left = totals[2 * node], total = left + totals[2 * node + 1];
    totals[node] = total;
    if (total) tree[node] = uint16_t(std::max<uint64_t>(1, std::min<uint64_t>(2047,
        (2048 * left + total / 2) / total)));
  }
  return tree;
}

// D/G-only streaming canonicality check: independently re-encode each decoded
// bit at its original probability, comparing emitted bytes directly to input.
// This retains upstream decoder zero extension but rejects absent flush and
// trailing bytes without buffering a second model or duplicating tensor logic.
struct GammaCanonicalRange {
  const uint8_t* expected;
  size_t length, position = 0;
  bool enabled;
  uint64_t low = 0, cache_size = 1;
  uint32_t range = 0xffffffffu;
  uint8_t cache = 0;
  GammaCanonicalRange(const uint8_t* data, size_t size, bool active)
      : expected(data), length(size), enabled(active) {}
  void emit(uint8_t value) {
    if (position >= length || expected[position] != value)
      die("noncanonical marginal range stream at byte %zu", position);
    ++position;
  }
  void shift_low() {
    if (low < 0xff000000ull || low > 0xffffffffull) {
      const uint32_t carry = uint32_t(low >> 32);
      emit(uint8_t(cache + carry));
      for (uint64_t k = 1; k < cache_size; ++k) emit(uint8_t(0xffu + carry));
      cache = uint8_t(low >> 24);
      cache_size = 0;
    }
    ++cache_size;
    low = uint32_t(low << 8);
  }
  void bit(uint16_t probability, unsigned value) {
    if (!enabled) return;
    const uint32_t bound = (range >> 11) * probability;
    if (value) { low += bound; range -= bound; }
    else range = bound;
    while (range < (1u << 24)) { range <<= 8; shift_low(); }
  }
  void finish() {
    if (!enabled) return;
    for (unsigned k = 0; k < 5; ++k) shift_low();
    if (position != length) die("trailing marginal range bytes at byte %zu", position);
  }
};

struct BinDecoder {
  const uint8_t* p;
  const uint8_t* end;
  uint32_t range = 0xFFFFFFFFu;
  uint32_t code = 0;

  GammaCanonicalRange gamma_check;
  BinDecoder(const uint8_t* data, size_t len, bool canonical = false)
      : p(data), end(data + len), gamma_check(data, len, canonical) {
    if (canonical && (len < 5 || data[0] != 0)) die("invalid marginal range cache or length");
    p++;  // the first byte is the encoder's initial zero cache
    for (int i = 0; i < 4; i++) code = (code << 8) | byte();
  }
  uint8_t byte() { return p < end ? *p++ : 0; }
  int decode_bit(uint16_t* prob, bool adaptive = true) {
    const uint16_t original_probability = *prob;
    uint32_t bound = (range >> 11) * *prob;
    int bit;
    if (code < bound) {
      range = bound;
      if (adaptive) *prob = uint16_t(*prob + ((2048 - *prob) >> 5));
      bit = 0;
    } else {
      code -= bound;
      range -= bound;
      if (adaptive) *prob = uint16_t(*prob - (*prob >> 5));
      bit = 1;
    }
    gamma_check.bit(original_probability, unsigned(bit));
    while (range < (1u << 24)) {
      code = (code << 8) | byte();
      range <<= 8;
    }
    return bit;
  }
  // probs: (1 << nbits) entries, indices 1.. used
  uint32_t decode_tree(uint16_t* probs, int nbits, bool adaptive = true) {
    uint32_t node = 1;
    for (int k = 0; k < nbits; k++) node = (node << 1) | decode_bit(&probs[node], adaptive);
    return node - (1u << nbits);
  }
};

// the adaptive model set of the v2 stream (pysrc/weights_compress.py _Models)
struct ModelsV2 {
  std::vector<uint16_t> meta;     // order-1: prev byte -> byte tree
  uint8_t meta_prev = 0;
  std::vector<uint16_t> name;     // order-2: (prev2, prev1) -> byte tree
  std::vector<uint16_t> raw;      // order-0 byte tree
  std::vector<uint16_t> int4;     // 4-bit tree, symbols 0..14
  std::vector<uint16_t> bf16_hi;  // byte tree
  std::vector<uint16_t> bf16_lo;  // hi byte -> byte tree
  std::vector<uint16_t> plane;    // 4 byte trees (byte position mod 4)

  ModelsV2()
      : meta(256 * 256, 1024),
        name(size_t(65536) * 256, 1024),
        raw(256, 1024),
        int4(16, 1024),
        bf16_hi(256, 1024),
        bf16_lo(256 * 256, 1024),
        plane(4 * 256, 1024) {}
};

WeightsFile load_v2(Reader& r, const char* path, bool marginal = false) {
  uint32_t n_tensors = r.u32();
  const char* bookkeeping_env = std::getenv("GAMMA_FX2_WEIGHT_BOOKKEEPING");
  const bool bookkeeping = bookkeeping_env && std::strcmp(bookkeeping_env, "1") == 0;
  const bool track_histograms = marginal || bookkeeping;
  if (track_histograms && n_tensors > kGammaTensorLimit) die("%s: tensor count exceeds bound", path);
  GammaMarginal gamma;
  if (marginal) gamma = gamma_read_marginal(r, n_tensors);
  size_t gamma_used = 0, gamma_histogram_tensors = 0;
  uint64_t gamma_represented = 0, gamma_symbols = 0;
  std::array<uint64_t, 15> gamma_actual_global{};
  BinDecoder dec(r.p, r.left, marginal);
  ModelsV2 m;

  auto get_meta = [&]() -> uint8_t {
    uint8_t b = uint8_t(dec.decode_tree(&m.meta[size_t(m.meta_prev) * 256], 8));
    m.meta_prev = b;
    return b;
  };

  WeightsFile wf;
  wf.tensors.reserve(n_tensors);
  for (uint32_t i = 0; i < n_tensors; i++) {
    uint32_t name_len = get_meta();
    std::string name(name_len, '\0');
    uint32_t c2 = 0, c1 = 0;
    for (uint32_t k = 0; k < name_len; k++) {
      uint32_t ch = dec.decode_tree(&m.name[size_t((c2 << 8) | c1) * 256], 8);
      name[k] = char(ch);
      c2 = c1;
      c1 = ch;
    }

    WTensor t;
    t.dtype = get_meta();
    dtype_size(t.dtype);  // validates the code
    uint32_t ndim = get_meta();
    if (ndim > 8) die("%s: %s: absurd ndim %u", path, name.c_str(), ndim);
    t.shape.resize(ndim);
    size_t numel = 1;
    for (uint32_t d = 0; d < ndim; d++) {
      uint32_t v = 0;
      for (int k = 0; k < 4; k++) v |= uint32_t(get_meta()) << (8 * k);
      t.shape[d] = v;
      if (track_histograms && v && numel > kGammaExpandedLimit / v)
        die("%s: %s: tensor extent exceeds bound", path, name.c_str());
      numel *= v;
    }
    t.numel = numel;
    const size_t element_bytes = dtype_size(t.dtype);
    if (track_histograms && numel > kGammaExpandedLimit / element_bytes)
      die("%s: %s: tensor byte size exceeds bound", path, name.c_str());
    size_t bytes = numel * element_bytes;
    if (track_histograms) {
      if (gamma_represented > kGammaExpandedLimit - bytes)
        die("%s: total tensor storage exceeds bound", path);
      gamma_represented += bytes;
      if (name == "rope.inv_freq" && (t.dtype != DT_F32 || ndim != 1))
        die("%s: RoPE frequency must be an F32 vector", path);
    }
    t.data.resize(bytes);
    uint8_t encoding = get_meta();

    switch (encoding) {
      case ENC_INT4: {
        if (t.dtype != DT_I8) die("%s: %s: ENC_INT4 on dtype %u", path,
                                  name.c_str(), unsigned(t.dtype));
        int8_t* out = reinterpret_cast<int8_t*>(t.data.data());
        const GammaHistogram* wanted = nullptr;
        GammaHistogram actual{};
        std::array<uint16_t, 16> fixed{};
        if (marginal) {
          if (gamma_used >= gamma.records.size() || gamma.records[gamma_used].index != i)
            die("%s: missing histogram at tensor %u", path, i);
          wanted = &gamma.records[gamma_used++].counts;
          uint64_t expected_symbols = 0;
          for (uint32_t n : *wanted) expected_symbols += n;
          if (expected_symbols != numel) die("%s: histogram total differs from tensor shape", path);
          fixed = gamma_fixed_tree(gamma.mode == 1 ? *wanted : gamma.global);
        }
        for (size_t k = 0; k < numel; k++) {
          const uint32_t symbol = dec.decode_tree(marginal ? fixed.data() : m.int4.data(), 4, !marginal);
          if (track_histograms) {
            if (symbol >= 15) die("%s: invalid INT4 symbol", path);
            ++actual[symbol];
            ++gamma_actual_global[symbol];
          }
          out[k] = int8_t(int(symbol) - 7);
        }
        if (track_histograms) { ++gamma_histogram_tensors; gamma_symbols += numel; }
        if (wanted && actual != *wanted) die("%s: decoded local histogram differs", path);
        break;
      }
      case ENC_BF16: {
        if (t.dtype != DT_BF16) die("%s: %s: ENC_BF16 on dtype %u", path,
                                    name.c_str(), unsigned(t.dtype));
        uint16_t* out = reinterpret_cast<uint16_t*>(t.data.data());
        for (size_t k = 0; k < numel; k++) {
          uint32_t hi = dec.decode_tree(m.bf16_hi.data(), 8);
          uint32_t lo = dec.decode_tree(&m.bf16_lo[hi * 256], 8);
          out[k] = uint16_t((hi << 8) | lo);
        }
        break;
      }
      case ENC_PLANE4: {
        if (dtype_size(t.dtype) != 4)
          die("%s: %s: ENC_PLANE4 on dtype %u", path, name.c_str(),
              unsigned(t.dtype));
        for (size_t k = 0; k < bytes; k++)
          t.data[k] = uint8_t(dec.decode_tree(&m.plane[(k & 3) * 256], 8));
        break;
      }
      case ENC_ROPE_SIN:
      case ENC_ROPE_COS: {
        if (t.dtype != DT_F32 || ndim != 2)
          die("%s: %s: bad rope tensor", path, name.c_str());
        if (track_histograms && name != (encoding == ENC_ROPE_SIN ? "rope.sin" : "rope.cos"))
          die("%s: generated RoPE tag/name mismatch", path);
        if (!wf.has("rope.inv_freq"))
          die("%s: %s: rope.inv_freq not decoded yet", path, name.c_str());
        const WTensor& inv = wf.get("rope.inv_freq");
        if (inv.dtype != DT_F32 || inv.numel != t.shape[1])
          die("%s: %s: rope.inv_freq mismatch", path, name.c_str());
        const float* invf = inv.f32();
        float* out = reinterpret_cast<float*>(t.data.data());
        int cos_bias = encoding == ENC_ROPE_COS ? 1 : 0;
        for (size_t pos = 0; pos < t.shape[0]; pos++)
          for (size_t col = 0; col < t.shape[1]; col++)
            out[pos * t.shape[1] + col] =
                sincosf_cuda(float(pos) * invf[col], cos_bias);
        break;
      }
      case ENC_RAW: {
        for (size_t k = 0; k < bytes; k++)
          t.data[k] = uint8_t(dec.decode_tree(m.raw.data(), 8));
        break;
      }
      default:
        die("%s: %s: unknown encoding %u", path, name.c_str(),
            unsigned(encoding));
    }

    if (!wf.tensors.emplace(name, std::move(t)).second)
      die("%s: duplicate tensor %s", path, name.c_str());
  }
  if (marginal) {
    if (gamma_used != gamma.records.size()) die("%s: unused marginal histogram records", path);
    for (unsigned s = 0; s < 15; ++s)
      if (gamma_actual_global[s] != gamma.global[s]) die("%s: decoded global histogram differs", path);
    dec.gamma_check.finish();
  }
  const char selected = marginal ? (gamma.mode == 1 ? 'D' : 'G') : bookkeeping ? 'K' : 'P';
  if (std::fprintf(stderr, "\nGamma weight loader selected=%c tensors=%u histogram_tensors=%zu histogram_symbols=%llu side_information_bytes=%zu canonical=%d\n",
      selected, n_tensors, gamma_histogram_tensors, static_cast<unsigned long long>(gamma_symbols),
      marginal ? size_t(65) + gamma.records.size() * 64 : size_t(0), marginal ? 1 : 0) < 0 || std::fflush(stderr) != 0)
    die("loader diagnostic flush failed");
  return wf;
}

}  // namespace

WeightsFile WeightsFile::load_compressed(const char* path) {
  FILE* f = std::fopen(path, "rb");
  if (!f) die("cannot open %s", path);
  std::fseek(f, 0, SEEK_END);
  long size = std::ftell(f);
  std::fseek(f, 0, SEEK_SET);
  if (size < 12) die("%s: too small", path);
  if (static_cast<unsigned long>(size) > kGammaFileLimit) {
    char prefix[8];
    if (std::fread(prefix, 1, 8, f) != 8 || std::fseek(f, 0, SEEK_SET) != 0)
      die("%s: header read failed", path);
    if (std::memcmp(prefix, "GFX2MAR1", 8) == 0) die("%s: marginal file exceeds bound", path);
  }
  std::vector<uint8_t> buf(static_cast<size_t>(size));
  if (std::fread(buf.data(), 1, buf.size(), f) != buf.size())
    die("%s: short read", path);
  std::fclose(f);

  Reader r{buf.data(), buf.size(), path};
  char magic[8];
  r.read(magic, 8);
  if (std::memcmp(magic, "GFX2MAR1", 8) == 0) return load_v2(r, path, true);
  if (std::memcmp(magic, "FX2TFWC2", 8) == 0) return load_v2(r, path);
  if (std::memcmp(magic, "FX2TFWC1", 8) != 0) die("%s: bad magic", path);

  uint32_t n_tensors = r.u32();
  WeightsFile wf;
  wf.tensors.reserve(n_tensors);
  for (uint32_t i = 0; i < n_tensors; i++) {
    uint32_t name_len = r.u32();
    if (name_len > 4096) die("%s: absurd name length %u", path, name_len);
    std::string name(name_len, '\0');
    r.read(&name[0], name_len);

    WTensor t;
    t.dtype = r.u8();
    dtype_size(t.dtype);  // validates the code
    uint32_t ndim = r.u32();
    if (ndim > 8) die("%s: %s: absurd ndim %u", path, name.c_str(), ndim);
    t.shape.resize(ndim);
    size_t numel = 1;
    for (uint32_t d = 0; d < ndim; d++) {
      t.shape[d] = r.u32();
      numel *= t.shape[d];
    }
    t.numel = numel;
    size_t bytes = numel * dtype_size(t.dtype);
    t.data.resize(bytes);
    if (t.dtype == DT_I8) {
      uint32_t stream_len = r.u32();
      r.need(stream_len);
      decode_i8_uniform15(r.p, stream_len,
                          reinterpret_cast<int8_t*>(t.data.data()), numel);
      r.p += stream_len;
      r.left -= stream_len;
    } else {
      r.read(t.data.data(), bytes);
    }

    if (!wf.tensors.emplace(name, std::move(t)).second)
      die("%s: duplicate tensor %s", path, name.c_str());
  }
  if (r.left != 0)
    die("%s: %zu trailing bytes after last tensor", path, r.left);
  return wf;
}

}  // namespace fx2
