#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <cmath>

namespace {

constexpr uint32_t kProbBits = 12;
constexpr uint32_t kProbTotal = 1u << kProbBits;
constexpr uint32_t kProbMax = kProbTotal - 1;
constexpr uint64_t kTopMask = 0xff00000000000000ULL;

#ifndef QM_TABLE_BITS
#define QM_TABLE_BITS 22
#endif

#ifndef QM_MIX_PROFILE
#define QM_MIX_PROFILE 1
#endif

#ifndef QM_MORPHIC_TRANSITIONS
#define QM_MORPHIC_TRANSITIONS 0
#endif

uint32_t clamp_prob(int32_t p) {
  if (p < 1) return 1;
  if (p > static_cast<int32_t>(kProbMax)) return kProbMax;
  return static_cast<uint32_t>(p);
}

struct IntegerMathLut {
  std::array<int16_t, kProbTotal> stretch{};
  std::array<uint16_t, 65536> squash{};

  IntegerMathLut() {
    stretch[0] = -32768;
    for (uint32_t p = 1; p < kProbTotal; ++p) {
      double v = std::log(static_cast<double>(p) /
                          static_cast<double>(kProbTotal - p)) * 256.0;
      if (v < -32768.0) v = -32768.0;
      if (v > 32767.0) v = 32767.0;
      stretch[p] = static_cast<int16_t>(v);
    }
    for (uint32_t i = 0; i < squash.size(); ++i) {
      int32_t x = static_cast<int32_t>(i) - 32768;
      double v = 1.0 / (1.0 + std::exp(-static_cast<double>(x) / 256.0));
      squash[i] = static_cast<uint16_t>(clamp_prob(static_cast<int32_t>(
          v * static_cast<double>(kProbTotal))));
    }
  }
};

const IntegerMathLut& lut() {
  static const IntegerMathLut instance;
  return instance;
}

struct ByteReader {
  const std::vector<uint8_t>& data;
  size_t pos = 0;

  uint8_t get() {
    if (pos >= data.size()) return 0;
    return data[pos++];
  }
};

struct RangeEncoder {
  uint64_t low = 0;
  uint64_t high = UINT64_MAX;
  std::vector<uint8_t> out;

  void encode_bit(uint32_t bit, uint32_t p1) {
    p1 = clamp_prob(static_cast<int32_t>(p1));
    uint32_t p0 = kProbTotal - p1;
    unsigned __int128 range =
        static_cast<unsigned __int128>(high) - low + 1u;
    uint64_t split = low + static_cast<uint64_t>(
        ((range * p0) >> kProbBits) - 1u);

    if (bit == 0) {
      high = split;
    } else {
      low = split + 1u;
    }

    while ((low & kTopMask) == (high & kTopMask)) {
      out.push_back(static_cast<uint8_t>(low >> 56));
      low <<= 8;
      high = (high << 8) | 0xffu;
    }
  }

  void finish() {
    for (int i = 0; i < 8; ++i) {
      out.push_back(static_cast<uint8_t>(low >> 56));
      low <<= 8;
    }
  }
};

struct RangeDecoder {
  uint64_t low = 0;
  uint64_t high = UINT64_MAX;
  uint64_t code = 0;
  ByteReader reader;

  explicit RangeDecoder(const std::vector<uint8_t>& data, size_t start)
      : reader{data, start} {
    for (int i = 0; i < 8; ++i) {
      code = (code << 8) | reader.get();
    }
  }

  uint32_t decode_bit(uint32_t p1) {
    p1 = clamp_prob(static_cast<int32_t>(p1));
    uint32_t p0 = kProbTotal - p1;
    unsigned __int128 range =
        static_cast<unsigned __int128>(high) - low + 1u;
    uint64_t split = low + static_cast<uint64_t>(
        ((range * p0) >> kProbBits) - 1u);
    uint32_t bit;

    if (code <= split) {
      bit = 0;
      high = split;
    } else {
      bit = 1;
      low = split + 1u;
    }

    while ((low & kTopMask) == (high & kTopMask)) {
      code = (code << 8) | reader.get();
      low <<= 8;
      high = (high << 8) | 0xffu;
    }
    return bit;
  }
};

uint32_t mix32(uint32_t x) {
  x ^= x >> 16;
  x *= 0x7feb352dU;
  x ^= x >> 15;
  x *= 0x846ca68bU;
  x ^= x >> 16;
  return x;
}

struct FiniteStateLexer {
  uint32_t state = 0;
  uint32_t utf8_remaining = 0;
  uint32_t xml_depth = 0;

  uint32_t context() const {
    return state | ((xml_depth & 31u) << 3) | ((utf8_remaining & 3u) << 8);
  }

  void update(uint8_t b) {
    if (utf8_remaining > 0) {
      --utf8_remaining;
      return;
    }
    if ((b & 0x80u) == 0) {
    } else if ((b & 0xe0u) == 0xc0u) {
      utf8_remaining = 1;
    } else if ((b & 0xf0u) == 0xe0u) {
      utf8_remaining = 2;
    } else if ((b & 0xf8u) == 0xf0u) {
      utf8_remaining = 3;
    }

    if (state == 0) {
      if (b == '<') {
        state = 1;
        if (xml_depth < 31) ++xml_depth;
      } else if (b == '[' || b == '{' || b == '|') {
        state = 2;
      }
    } else if (state == 1) {
      if (b == '>') state = 0;
      if (b == '/' && xml_depth > 0) --xml_depth;
    } else if (state == 2) {
      if (b == ']' || b == '}' || b == '\n') state = 0;
    }
  }
};

struct GrammarSidecar {
  static constexpr uint32_t kSize = 1u << 18;
  std::vector<uint32_t> table;
  uint32_t prev = 0;
  uint32_t signature = 0;
  uint32_t seen = 0;

  GrammarSidecar() : table(kSize, 0) {}

  uint32_t context() const {
    return signature ^ (seen * 0x9e3779b1U);
  }

  void update(uint8_t b) {
    uint32_t pair = (prev << 8) | b;
    uint32_t idx = mix32(pair) & (kSize - 1);
    uint32_t old = table[idx];
    if (old == pair + 1u) {
      signature = mix32(signature ^ pair ^ 0xa5a5a5a5U);
    } else {
      table[idx] = pair + 1u;
      signature = mix32(signature + pair + 0x632be59bU);
    }
    prev = b;
    if (seen < UINT32_MAX) ++seen;
  }
};

struct FixedPointSsm {
  static constexpr int kDim = 16;
  std::array<int16_t, kDim> hidden{};
  std::array<std::array<int16_t, kDim>, kDim> wx{};
  std::array<std::array<int16_t, kDim>, kDim> wh{};
  std::array<std::array<int16_t, kDim>, 256> emb{};
  std::array<int16_t, kDim> out{};

  FixedPointSsm() {
    uint32_t seed = 42;
    auto next = [&]() -> int16_t {
      seed = seed * 1103515245u + 12345u;
      return static_cast<int16_t>(((seed >> 16) & 511u) - 256);
    };
    for (int i = 0; i < kDim; ++i) {
      out[i] = next();
      for (int j = 0; j < kDim; ++j) {
        wx[i][j] = next();
        wh[i][j] = next();
      }
    }
    for (int v = 0; v < 256; ++v) {
      for (int i = 0; i < kDim; ++i) emb[v][i] = next();
    }
  }

  uint32_t predict() const {
    int32_t sum = 0;
    for (int i = 0; i < kDim; ++i) {
      sum += static_cast<int32_t>(out[i]) * hidden[i];
    }
    int32_t idx = ((sum >> 7) + 32768);
    if (idx < 0) idx = 0;
    if (idx > 65535) idx = 65535;
    return lut().squash[static_cast<uint32_t>(idx)];
  }

  void update(uint8_t b) {
    std::array<int16_t, kDim> next{};
    for (int i = 0; i < kDim; ++i) {
      int32_t sum = 0;
      for (int j = 0; j < kDim; ++j) {
        sum += static_cast<int32_t>(wx[i][j]) * emb[b][j];
        sum += static_cast<int32_t>(wh[i][j]) * hidden[j];
      }
      sum >>= 9;
      if (sum < -32768) sum = -32768;
      if (sum > 32767) sum = 32767;
      next[i] = static_cast<int16_t>(sum);
    }
    hidden = next;
  }
};

struct LocalContextTracks {
  static constexpr uint32_t kBits = QM_TABLE_BITS;
  static constexpr uint32_t kSize = 1u << kBits;
  static constexpr uint32_t kMask = kSize - 1;
  std::vector<uint8_t> states;
  std::array<std::array<uint8_t, 2>, 256> transition{};
#if QM_MORPHIC_TRANSITIONS
  std::array<std::array<uint8_t, 2>, 256> transition_fast{};
  std::array<std::array<uint8_t, 2>, 256> transition_slow{};
  uint64_t bit_window = 0;
  uint32_t bit_count = 0;
  bool use_slow = false;
#endif
  std::array<uint16_t, 256> prob{};

  LocalContextTracks() : states(kSize, 128) {
    for (int s = 0; s < 256; ++s) {
      int down = s - std::max(1, s >> 5);
      int up = s + std::max(1, (255 - s) >> 5);
      if (down < 0) down = 0;
      if (up > 255) up = 255;
      transition[s][0] = static_cast<uint8_t>(down);
      transition[s][1] = static_cast<uint8_t>(up);
#if QM_MORPHIC_TRANSITIONS
      int fast_down = s - std::max(4, s >> 3);
      int fast_up = s + std::max(4, (255 - s) >> 3);
      int slow_down = s - std::max(1, s >> 7);
      int slow_up = s + std::max(1, (255 - s) >> 7);
      if (fast_down < 0) fast_down = 0;
      if (fast_up > 255) fast_up = 255;
      if (slow_down < 0) slow_down = 0;
      if (slow_up > 255) slow_up = 255;
      transition_fast[s][0] = static_cast<uint8_t>(fast_down);
      transition_fast[s][1] = static_cast<uint8_t>(fast_up);
      transition_slow[s][0] = static_cast<uint8_t>(slow_down);
      transition_slow[s][1] = static_cast<uint8_t>(slow_up);
#endif
      prob[s] = static_cast<uint16_t>(1 + ((s * (kProbTotal - 2)) / 255));
    }
  }

#if QM_MORPHIC_TRANSITIONS
  void observe_bit(uint32_t bit) {
    bit_window = (bit_window << 1) | (bit & 1u);
    if (bit_count < 64) ++bit_count;
    const uint32_t ones = static_cast<uint32_t>(__builtin_popcountll(bit_window));
    const uint32_t zeros = bit_count - ones;
    use_slow = bit_count >= 16 && (ones * 8 <= bit_count || zeros * 8 <= bit_count);
  }
#endif

  uint32_t predict(uint32_t key) const {
    return prob[states[key & kMask]];
  }

  void update(uint32_t key, uint32_t bit) {
    uint8_t& s = states[key & kMask];
#if QM_MORPHIC_TRANSITIONS
    s = use_slow ? transition_slow[s][bit & 1u] : transition_fast[s][bit & 1u];
#else
    s = transition[s][bit & 1u];
#endif
  }
};

struct Mixer {
  static constexpr int kModels = 7;
  std::array<int32_t, kModels> weights{};

  Mixer() {
#if QM_MIX_PROFILE == 2
    weights = {1500, 1400, 1200, 900, 500, 500, 0};
#else
    weights.fill(512);
    weights[0] = 900;
    weights[1] = 800;
#endif
  }

  uint32_t blend(const std::array<uint32_t, kModels>& p) const {
    int32_t sum = 0;
    const auto& l = lut();
    for (int i = 0; i < kModels; ++i) {
      sum += weights[i] * l.stretch[clamp_prob(static_cast<int32_t>(p[i]))];
    }
    sum >>= 10;
    int32_t idx = sum + 32768;
    if (idx < 0) idx = 0;
    if (idx > 65535) idx = 65535;
    return l.squash[static_cast<uint32_t>(idx)];
  }

  void update(const std::array<uint32_t, kModels>& p, uint32_t mixed,
              uint32_t bit) {
    int32_t target = bit ? static_cast<int32_t>(kProbTotal) : 0;
    int32_t err = target - static_cast<int32_t>(mixed);
    const auto& l = lut();
    for (int i = 0; i < kModels; ++i) {
      int32_t x = l.stretch[clamp_prob(static_cast<int32_t>(p[i]))];
#if QM_MIX_PROFILE == 2
      if (i == 6) x >>= 3;
#endif
      weights[i] += (err * x) >> 19;
      if (weights[i] < -4096) weights[i] = -4096;
      if (weights[i] > 4096) weights[i] = 4096;
    }
  }
};

struct Model {
  FiniteStateLexer lexer;
  GrammarSidecar grammar;
  FixedPointSsm ssm;
  LocalContextTracks tracks;
  Mixer mixer;
  uint32_t bit_context = 1;
  uint32_t last1 = 0;
  uint32_t last2 = 0;
  uint32_t last4 = 0;
  uint8_t current_byte = 0;

  uint32_t key(uint32_t model, uint32_t extra) const {
    return mix32((model * 0x9e3779b1U) ^ (bit_context * 257U) ^ extra);
  }

  std::array<uint32_t, Mixer::kModels> probs() const {
    std::array<uint32_t, Mixer::kModels> p{};
    p[0] = tracks.predict(key(0, 0));
    p[1] = tracks.predict(key(1, last1));
    p[2] = tracks.predict(key(2, (last2 << 8) ^ last1));
    p[3] = tracks.predict(key(3, last4));
    p[4] = tracks.predict(key(4, lexer.context()));
    p[5] = tracks.predict(key(5, grammar.context()));
    p[6] = ssm.predict();
    return p;
  }

  uint32_t predict() const {
    return mixer.blend(probs());
  }

  void update_bit(uint32_t bit) {
#if QM_MORPHIC_TRANSITIONS
    tracks.observe_bit(bit);
#endif
    auto p = probs();
    uint32_t mixed = mixer.blend(p);
    tracks.update(key(0, 0), bit);
    tracks.update(key(1, last1), bit);
    tracks.update(key(2, (last2 << 8) ^ last1), bit);
    tracks.update(key(3, last4), bit);
    tracks.update(key(4, lexer.context()), bit);
    tracks.update(key(5, grammar.context()), bit);
    mixer.update(p, mixed, bit);
    bit_context = ((bit_context << 1) | bit) & 255u;
    current_byte = static_cast<uint8_t>((current_byte << 1) | bit);
  }

  void finish_byte() {
    uint8_t b = current_byte;
    lexer.update(b);
    grammar.update(b);
    ssm.update(b);
    last4 = ((last4 << 8) ^ b) & 0xffffffffU;
    last2 = ((last2 << 8) ^ b) & 0xffffU;
    last1 = b;
    bit_context = 1;
    current_byte = 0;
  }
};

std::vector<uint8_t> read_file(const std::string& path) {
  std::ifstream f(path, std::ios::binary);
  if (!f) {
    std::cerr << "open failed: " << path << "\n";
    std::exit(2);
  }
  return std::vector<uint8_t>((std::istreambuf_iterator<char>(f)),
                              std::istreambuf_iterator<char>());
}

void write_file(const std::string& path, const std::vector<uint8_t>& data) {
  std::ofstream f(path, std::ios::binary);
  if (!f) {
    std::cerr << "write failed: " << path << "\n";
    std::exit(2);
  }
  f.write(reinterpret_cast<const char*>(data.data()),
          static_cast<std::streamsize>(data.size()));
}

std::vector<uint8_t> compress_data(const std::vector<uint8_t>& input) {
  Model model;
  RangeEncoder enc;
  std::vector<uint8_t> header;
  header.push_back('Q');
  header.push_back('M');
  header.push_back('1');
  header.push_back(0);
  uint64_t n = input.size();
  for (int i = 0; i < 8; ++i) header.push_back((n >> (8 * i)) & 0xffu);

  for (uint8_t b : input) {
    for (int bit_idx = 7; bit_idx >= 0; --bit_idx) {
      uint32_t bit = (b >> bit_idx) & 1u;
      uint32_t p1 = model.predict();
      enc.encode_bit(bit, p1);
      model.update_bit(bit);
    }
    model.finish_byte();
  }
  enc.finish();
  header.insert(header.end(), enc.out.begin(), enc.out.end());
  return header;
}

std::vector<uint8_t> decompress_data(const std::vector<uint8_t>& input) {
  if (input.size() < 12 || input[0] != 'Q' || input[1] != 'M' ||
      input[2] != '1') {
    std::cerr << "bad archive\n";
    std::exit(3);
  }
  uint64_t n = 0;
  for (int i = 0; i < 8; ++i) n |= static_cast<uint64_t>(input[4 + i]) << (8 * i);

  Model model;
  RangeDecoder dec(input, 12);
  std::vector<uint8_t> out;
  out.reserve(static_cast<size_t>(n));
  for (uint64_t i = 0; i < n; ++i) {
    uint8_t b = 0;
    for (int bit_idx = 7; bit_idx >= 0; --bit_idx) {
      uint32_t p1 = model.predict();
      uint32_t bit = dec.decode_bit(p1);
      b = static_cast<uint8_t>((b << 1) | bit);
      model.update_bit(bit);
    }
    model.finish_byte();
    out.push_back(b);
  }
  return out;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: qm_context_codec_v1 -c|-d input output\n";
    return 2;
  }
  std::vector<uint8_t> input = read_file(argv[2]);
  std::vector<uint8_t> output;
  if (std::strcmp(argv[1], "-c") == 0) {
    output = compress_data(input);
  } else if (std::strcmp(argv[1], "-d") == 0) {
    output = decompress_data(input);
  } else {
    std::cerr << "unknown mode\n";
    return 2;
  }
  write_file(argv[3], output);
  return 0;
}
