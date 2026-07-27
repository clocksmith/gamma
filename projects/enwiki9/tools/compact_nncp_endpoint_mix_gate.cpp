#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr uint32_t kPriorAuxWeight = 4096;

struct RangeEncoder {
  uint32_t x1 = 0;
  uint32_t x2 = 0xffffffffu;
  std::vector<uint8_t> output;
  void Update(uint16_t p1, int bit) {
    const uint32_t delta = x2 - x1;
    const uint32_t midpoint =
        x1 + (delta >> 16) * p1 + ((delta & 0xffffu) * p1 >> 16);
    if (bit) x2 = midpoint;
    else x1 = midpoint + 1;
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      output.push_back(static_cast<uint8_t>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
  }
  void Finish() {
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      output.push_back(static_cast<uint8_t>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
    output.push_back(static_cast<uint8_t>(x2 >> 24));
  }
};

std::vector<uint8_t> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

uint64_t Load64(const uint8_t* data) {
  uint64_t value = 0;
  for (int i = 7; i >= 0; --i) value = (value << 8) | data[i];
  return value;
}

uint32_t Load32(const uint8_t* data) {
  uint32_t value = 0;
  for (int i = 3; i >= 0; --i) value = (value << 8) | data[i];
  return value;
}

uint16_t Quantize(double probability) {
  uint64_t value = static_cast<uint64_t>(
      std::llround(probability * 65536.0));
  value = std::max<uint64_t>(1, std::min<uint64_t>(65535, value));
  return static_cast<uint16_t>(value);
}

uint16_t Mix(uint16_t parent, uint16_t auxiliary, uint32_t weight) {
  uint64_t value =
      (static_cast<uint64_t>(65536u - weight) * parent +
       static_cast<uint64_t>(weight) * auxiliary) >>
      16;
  value = std::max<uint64_t>(1, std::min<uint64_t>(65535, value));
  return static_cast<uint16_t>(value);
}

uint32_t UpdateWeight(uint32_t weight, uint16_t parent, uint16_t auxiliary,
                      int bit) {
  const uint32_t pp = bit ? parent : 65536u - parent;
  const uint32_t pa = bit ? auxiliary : 65536u - auxiliary;
  const uint64_t a = static_cast<uint64_t>(weight) * pa;
  const uint64_t b = static_cast<uint64_t>(65536u - weight) * pp;
  if (a + b == 0) return weight;
  uint64_t value = (a * 65536u + (a + b) / 2) / (a + b);
  return static_cast<uint32_t>(
      std::max<uint64_t>(1, std::min<uint64_t>(65535, value)));
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5 && argc != 6) {
    std::cerr << "usage: compact_nncp_endpoint_mix_gate FX2PT WRT NNCP_TRACE DECISION [BURN_IN_SYMBOLS]\n";
    return 2;
  }
  try {
    const auto fx2 = ReadFile(argv[1]);
    const auto wrt = ReadFile(argv[2]);
    const auto trace = ReadFile(argv[3]);
    if (fx2.size() < 8 || std::memcmp(fx2.data(), "FX2PT01\n", 8) != 0 ||
        (fx2.size() - 8) % 3 != 0) {
      throw std::runtime_error("invalid FX2 trace");
    }
    if (trace.size() < 16 || std::memcmp(trace.data(), "NNTCHD2\0", 8) != 0)
      throw std::runtime_error("invalid NNCP trace");
    const uint64_t symbols = Load64(trace.data() + 8);
    const uint64_t burn_in =
        argc == 6 ? static_cast<uint64_t>(std::stoull(argv[5])) : 0;
    if (symbols == 0 || symbols > wrt.size())
      throw std::runtime_error("invalid symbol count");
    if (burn_in >= symbols) throw std::runtime_error("invalid burn-in");
    const size_t expected_trace_size = 16 + symbols * (44 + 256 * 4);
    if (trace.size() != expected_trace_size)
      throw std::runtime_error("unexpected NNCP trace size");
    if ((fx2.size() - 8) / 3 < symbols * 8)
      throw std::runtime_error("FX2 trace too short");

    std::array<uint32_t, 8> weights{};
    weights.fill(kPriorAuxWeight);
    RangeEncoder parent_encoder, auxiliary_encoder, mixture_encoder;
    long double parent_loss = 0;
    long double auxiliary_loss = 0;
    long double mixture_loss = 0;
    long double union_gain = 0;
    uint64_t mixed_rows = 0;
    for (uint64_t symbol_index = 0; symbol_index < symbols; ++symbol_index) {
      const size_t row_offset = 16 + symbol_index * (44 + 256 * 4);
      const uint64_t original = Load64(trace.data() + row_offset);
      const uint16_t truth_symbol = static_cast<uint16_t>(
          trace[row_offset + 38] |
          (static_cast<uint16_t>(trace[row_offset + 39]) << 8));
      const uint32_t vocabulary = Load32(trace.data() + row_offset + 40);
      if (original != symbol_index || vocabulary != 256 ||
          truth_symbol != wrt[symbol_index]) {
        throw std::runtime_error("NNCP/WRT alignment failure");
      }
      std::array<double, 256> distribution{};
      double total = 0;
      const uint8_t* probability_bytes = trace.data() + row_offset + 44;
      for (int i = 0; i < 256; ++i) {
        uint32_t raw = Load32(probability_bytes + 4 * i);
        float value;
        std::memcpy(&value, &raw, sizeof(value));
        if (!(value > 0) || !std::isfinite(value))
          throw std::runtime_error("invalid NNCP probability");
        distribution[i] = value;
        total += value;
      }
      if (std::abs(total - 1.0) > 2e-5)
        throw std::runtime_error("NNCP distribution not normalized");
      if (symbol_index < burn_in) continue;

      int lo = 0;
      int hi = 256;
      for (int bit_position = 0; bit_position < 8; ++bit_position) {
        const int mid = (lo + hi) / 2;
        double denominator = 0;
        double numerator = 0;
        for (int i = lo; i < hi; ++i) denominator += distribution[i];
        for (int i = mid; i < hi; ++i) numerator += distribution[i];
        const uint16_t auxiliary = Quantize(numerator / denominator);
        const uint64_t fx2_row = symbol_index * 8 + bit_position;
        const size_t fx2_offset = 8 + fx2_row * 3;
        const uint16_t parent = static_cast<uint16_t>(
            fx2[fx2_offset] |
            (static_cast<uint16_t>(fx2[fx2_offset + 1]) << 8));
        const int bit = fx2[fx2_offset + 2];
        const int expected_bit =
            (truth_symbol >> (7 - bit_position)) & 1;
        if (bit != expected_bit) throw std::runtime_error("bit alignment failure");
        const uint16_t mixture =
            Mix(parent, auxiliary, weights[bit_position]);
        mixed_rows += mixture != parent;
        parent_encoder.Update(parent, bit);
        auxiliary_encoder.Update(auxiliary, bit);
        mixture_encoder.Update(mixture, bit);
        const long double pp =
            bit ? static_cast<long double>(parent) / 65536.0L
                : static_cast<long double>(65536u - parent) / 65536.0L;
        const long double pa =
            bit ? static_cast<long double>(auxiliary) / 65536.0L
                : static_cast<long double>(65536u - auxiliary) / 65536.0L;
        const long double pm =
            bit ? static_cast<long double>(mixture) / 65536.0L
                : static_cast<long double>(65536u - mixture) / 65536.0L;
        const long double lp = -std::log2(pp);
        const long double la = -std::log2(pa);
        parent_loss += lp;
        auxiliary_loss += la;
        mixture_loss -= std::log2(pm);
        union_gain += lp - std::min(lp, la);
        weights[bit_position] =
            UpdateWeight(weights[bit_position], parent, auxiliary, bit);
        if (bit) lo = mid;
        else hi = mid;
      }
    }
    parent_encoder.Finish();
    auxiliary_encoder.Finish();
    mixture_encoder.Finish();

    const int64_t net =
        static_cast<int64_t>(parent_encoder.output.size()) -
        static_cast<int64_t>(mixture_encoder.output.size());
    const uint64_t evaluated_symbols = symbols - burn_in;
    const double projected_bpm =
        static_cast<double>(net) * 1000000.0 / evaluated_symbols;
    const bool passes_gate = projected_bpm >= 2000.0;
    std::ofstream out(argv[4]);
    if (!out) throw std::runtime_error("cannot write decision");
    out << "{\n"
        << "  \"id\": \"compact_nncp_endpoint_mix_v1\",\n"
        << "  \"status\": \"" << (passes_gate ? "promote_startup_only"
                                               : "startup_negative")
        << "\",\n"
        << "  \"score_credit_bytes\": 0,\n"
        << "  \"symbols\": " << symbols << ",\n"
        << "  \"burn_in_symbols\": " << burn_in << ",\n"
        << "  \"evaluated_symbols\": " << evaluated_symbols << ",\n"
        << "  \"coded_bits\": " << evaluated_symbols * 8 << ",\n"
        << "  \"mixed_rows\": " << mixed_rows << ",\n"
        << "  \"parent_ideal_bits\": " << static_cast<double>(parent_loss) << ",\n"
        << "  \"auxiliary_ideal_bits\": "
        << static_cast<double>(auxiliary_loss) << ",\n"
        << "  \"mixture_ideal_bits\": " << static_cast<double>(mixture_loss) << ",\n"
        << "  \"unrestricted_union_gain_bits\": "
        << static_cast<double>(union_gain) << ",\n"
        << "  \"parent_payload_bytes\": " << parent_encoder.output.size() << ",\n"
        << "  \"auxiliary_payload_bytes\": "
        << auxiliary_encoder.output.size() << ",\n"
        << "  \"mixture_payload_bytes\": " << mixture_encoder.output.size() << ",\n"
        << "  \"net_saved_bytes\": " << net << ",\n"
        << "  \"naive_projected_bytes_per_million_wrt\": " << projected_bpm << ",\n"
        << "  \"final_aux_weights_q16\": [";
    for (size_t i = 0; i < weights.size(); ++i) {
      if (i) out << ", ";
      out << weights[i];
    }
    out << "],\n"
        << "  \"claim_boundary\": \"Sequential startup WRT shadow only; no mature, raw-byte, package, runtime, or score claim.\",\n"
        << "  \"decision\": \""
        << (passes_gate ? "authorize_larger_compact_nncp_trace"
                        : "do_not_scale_unchanged_startup_expert")
        << "\"\n"
        << "}\n";
    out.close();

    std::cout << "symbols=" << symbols
              << " parent=" << parent_encoder.output.size()
              << " auxiliary=" << auxiliary_encoder.output.size()
              << " mixture=" << mixture_encoder.output.size()
              << " net=" << net
              << " projected_bpm=" << projected_bpm
              << " weights=";
    for (uint32_t weight : weights) std::cout << weight << ",";
    std::cout << "\n";
    return 0;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
