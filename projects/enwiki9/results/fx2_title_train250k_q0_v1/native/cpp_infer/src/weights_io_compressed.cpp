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

struct BinDecoder {
  const uint8_t* p;
  const uint8_t* end;
  uint32_t range = 0xFFFFFFFFu;
  uint32_t code = 0;

  BinDecoder(const uint8_t* data, size_t len) : p(data), end(data + len) {
    p++;  // the first byte is the encoder's initial zero cache
    for (int i = 0; i < 4; i++) code = (code << 8) | byte();
  }
  uint8_t byte() { return p < end ? *p++ : 0; }
  int decode_bit(uint16_t* prob) {
    uint32_t bound = (range >> 11) * *prob;
    int bit;
    if (code < bound) {
      range = bound;
      *prob = uint16_t(*prob + ((2048 - *prob) >> 5));
      bit = 0;
    } else {
      code -= bound;
      range -= bound;
      *prob = uint16_t(*prob - (*prob >> 5));
      bit = 1;
    }
    while (range < (1u << 24)) {
      code = (code << 8) | byte();
      range <<= 8;
    }
    return bit;
  }
  // probs: (1 << nbits) entries, indices 1.. used
  uint32_t decode_tree(uint16_t* probs, int nbits) {
    uint32_t node = 1;
    for (int k = 0; k < nbits; k++) node = (node << 1) | decode_bit(&probs[node]);
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

WeightsFile load_v2(Reader& r, const char* path) {
  uint32_t n_tensors = r.u32();
  BinDecoder dec(r.p, r.left);
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
      numel *= v;
    }
    t.numel = numel;
    size_t bytes = numel * dtype_size(t.dtype);
    t.data.resize(bytes);
    uint8_t encoding = get_meta();

    switch (encoding) {
      case ENC_INT4: {
        if (t.dtype != DT_I8) die("%s: %s: ENC_INT4 on dtype %u", path,
                                  name.c_str(), unsigned(t.dtype));
        int8_t* out = reinterpret_cast<int8_t*>(t.data.data());
        for (size_t k = 0; k < numel; k++)
          out[k] = int8_t(int(dec.decode_tree(m.int4.data(), 4)) - 7);
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
  std::vector<uint8_t> buf(static_cast<size_t>(size));
  if (std::fread(buf.data(), 1, buf.size(), f) != buf.size())
    die("%s: short read", path);
  std::fclose(f);

  Reader r{buf.data(), buf.size(), path};
  char magic[8];
  r.read(magic, 8);
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
