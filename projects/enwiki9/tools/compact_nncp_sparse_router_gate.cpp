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

constexpr int kFeatures = 6;
constexpr int kModelBytes = 3;
constexpr std::array<int, kFeatures> kCards{8, 8, 8, 3, 8, 17};

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

struct Row {
  uint16_t parent = 0;
  uint16_t auxiliary = 0;
  uint8_t truth = 0;
  std::array<uint8_t, kFeatures> features{};
};

struct Totals {
  int64_t parent_qbits = 0;
  int64_t auxiliary_qbits = 0;
};

struct Family {
  int first = 0;
  int second = -1;
  int categories = 0;
  std::vector<Totals> totals;
};

struct Rule {
  bool active = false;
  int family = -1;
  int category = -1;
  int64_t gain_qbits = 0;
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
  uint64_t value =
      static_cast<uint64_t>(std::llround(probability * 65536.0));
  value = std::max<uint64_t>(1, std::min<uint64_t>(65535, value));
  return static_cast<uint16_t>(value);
}

int QBits(uint16_t probability, int truth) {
  const double value =
      truth ? static_cast<double>(probability) / 65536.0
            : static_cast<double>(65536u - probability) / 65536.0;
  return static_cast<int>(std::llround(-std::log2(value) * 256.0));
}

int Category(const Family& family,
             const std::array<uint8_t, kFeatures>& features) {
  if (family.second < 0) return features[family.first];
  return features[family.first] * kCards[family.second] +
         features[family.second];
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 6) {
    std::cerr << "usage: compact_nncp_sparse_router_gate FX2PT WRT TRACE BURN_IN DECISION\n";
    return 2;
  }
  try {
    const auto fx2 = ReadFile(argv[1]);
    const auto wrt = ReadFile(argv[2]);
    const auto trace = ReadFile(argv[3]);
    const uint64_t burn_in = std::stoull(argv[4]);
    if (fx2.size() < 8 || std::memcmp(fx2.data(), "FX2PT01\n", 8) != 0 ||
        (fx2.size() - 8) % 3 != 0) {
      throw std::runtime_error("invalid FX2 trace");
    }
    if (trace.size() < 16 || std::memcmp(trace.data(), "NNTCHD2\0", 8) != 0)
      throw std::runtime_error("invalid NNCP trace");
    const uint64_t symbols = Load64(trace.data() + 8);
    if (burn_in >= symbols || symbols > wrt.size())
      throw std::runtime_error("invalid scope");
    if (trace.size() != 16 + symbols * (44 + 256 * 4))
      throw std::runtime_error("unexpected trace size");
    const uint64_t split_symbol = burn_in + (symbols - burn_in) / 2;

    std::vector<Row> rows;
    rows.reserve((symbols - burn_in) * 8);
    for (uint64_t symbol = 0; symbol < symbols; ++symbol) {
      const size_t offset = 16 + symbol * (44 + 256 * 4);
      if (Load64(trace.data() + offset) != symbol ||
          Load32(trace.data() + offset + 40) != 256) {
        throw std::runtime_error("trace alignment failure");
      }
      const uint16_t truth_symbol = static_cast<uint16_t>(
          trace[offset + 38] |
          (static_cast<uint16_t>(trace[offset + 39]) << 8));
      if (truth_symbol != wrt[symbol])
        throw std::runtime_error("symbol mismatch");
      std::array<double, 256> distribution{};
      double total = 0;
      for (int i = 0; i < 256; ++i) {
        uint32_t raw = Load32(trace.data() + offset + 44 + 4 * i);
        float value;
        std::memcpy(&value, &raw, sizeof(value));
        if (!(value > 0) || !std::isfinite(value))
          throw std::runtime_error("bad distribution");
        distribution[i] = value;
        total += value;
      }
      if (std::abs(total - 1.0) > 2e-5)
        throw std::runtime_error("distribution normalization failure");
      if (symbol < burn_in) continue;
      int lo = 0, hi = 256;
      const int previous =
          symbol == 0 ? 256 : static_cast<int>(wrt[symbol - 1]);
      for (int bit_position = 0; bit_position < 8; ++bit_position) {
        const int mid = (lo + hi) / 2;
        double denominator = 0, numerator = 0;
        for (int i = lo; i < hi; ++i) denominator += distribution[i];
        for (int i = mid; i < hi; ++i) numerator += distribution[i];
        const uint16_t auxiliary = Quantize(numerator / denominator);
        const uint64_t fx2_row = symbol * 8 + bit_position;
        const size_t fx2_offset = 8 + fx2_row * 3;
        const uint16_t parent = static_cast<uint16_t>(
            fx2[fx2_offset] |
            (static_cast<uint16_t>(fx2[fx2_offset + 1]) << 8));
        const int truth = fx2[fx2_offset + 2];
        const int parent_conf =
            std::min<uint32_t>(parent, 65536u - parent) >> 12;
        const int auxiliary_conf =
            std::min<uint32_t>(auxiliary, 65536u - auxiliary) >> 12;
        const int parent_modal = parent >= 32768;
        const int auxiliary_modal = auxiliary >= 32768;
        const int relation = parent_modal == auxiliary_modal
                                 ? 0
                                 : (parent_modal ? 1 : 2);
        const int gap =
            std::min<int>(7, std::abs(static_cast<int>(parent) -
                                     static_cast<int>(auxiliary)) >>
                                    13);
        Row row;
        row.parent = parent;
        row.auxiliary = auxiliary;
        row.truth = static_cast<uint8_t>(truth);
        row.features = {
            static_cast<uint8_t>(bit_position),
            static_cast<uint8_t>(std::min(7, parent_conf)),
            static_cast<uint8_t>(std::min(7, auxiliary_conf)),
            static_cast<uint8_t>(relation),
            static_cast<uint8_t>(gap),
            static_cast<uint8_t>(previous == 256 ? 16 : previous >> 4)};
        rows.push_back(row);
        if (truth) lo = mid;
        else hi = mid;
      }
    }

    std::vector<Family> families;
    for (int first = 0; first < kFeatures; ++first) {
      Family f;
      f.first = first;
      f.categories = kCards[first];
      f.totals.resize(f.categories);
      families.push_back(std::move(f));
    }
    for (int first = 0; first < kFeatures; ++first) {
      for (int second = first + 1; second < kFeatures; ++second) {
        Family f;
        f.first = first;
        f.second = second;
        f.categories = kCards[first] * kCards[second];
        f.totals.resize(f.categories);
        families.push_back(std::move(f));
      }
    }

    const size_t development_rows = (split_symbol - burn_in) * 8;
    for (size_t index = 0; index < development_rows; ++index) {
      const Row& row = rows[index];
      for (Family& family : families) {
        Totals& totals = family.totals[Category(family, row.features)];
        totals.parent_qbits += QBits(row.parent, row.truth);
        totals.auxiliary_qbits += QBits(row.auxiliary, row.truth);
      }
    }
    Rule rule;
    const int64_t price = kModelBytes * 8LL * 256;
    for (size_t family_index = 0; family_index < families.size(); ++family_index) {
      for (int category = 0; category < families[family_index].categories;
           ++category) {
        const Totals& totals = families[family_index].totals[category];
        const int64_t gain =
            totals.parent_qbits - totals.auxiliary_qbits - price;
        if (gain > rule.gain_qbits)
          rule = {true, static_cast<int>(family_index), category, gain};
      }
    }

    RangeEncoder parent_encoder, candidate_encoder;
    long double real_union = 0, shifted_union = 0;
    uint64_t fired = 0;
    const size_t holdout_begin = development_rows;
    const size_t holdout_count = rows.size() - holdout_begin;
    constexpr size_t shift = 257;
    for (size_t index = holdout_begin; index < rows.size(); ++index) {
      const Row& row = rows[index];
      const bool fire =
          rule.active &&
          Category(families[rule.family], row.features) == rule.category;
      const uint16_t q = fire ? row.auxiliary : row.parent;
      fired += fire;
      parent_encoder.Update(row.parent, row.truth);
      candidate_encoder.Update(q, row.truth);
      const int parent_qbits = QBits(row.parent, row.truth);
      const int auxiliary_qbits = QBits(row.auxiliary, row.truth);
      real_union +=
          static_cast<long double>(std::max(0, parent_qbits - auxiliary_qbits)) /
          256.0L;
      const Row& shifted =
          rows[holdout_begin + (index - holdout_begin + shift) % holdout_count];
      const int shifted_qbits = QBits(shifted.auxiliary, row.truth);
      shifted_union +=
          static_cast<long double>(std::max(0, parent_qbits - shifted_qbits)) /
          256.0L;
    }
    parent_encoder.Finish();
    candidate_encoder.Finish();
    const int64_t model_bytes = rule.active ? kModelBytes : 0;
    const int64_t net =
        static_cast<int64_t>(parent_encoder.output.size()) -
        static_cast<int64_t>(candidate_encoder.output.size()) - model_bytes;
    const double bpm =
        static_cast<double>(net) * 1000000.0 /
        static_cast<double>((symbols - split_symbol));
    const bool passes = bpm >= 2000.0 && real_union > shifted_union;

    std::ofstream out(argv[5]);
    if (!out) throw std::runtime_error("cannot write decision");
    out << "{\n"
        << "  \"id\": \"compact_nncp_sparse_router_10k_v1\",\n"
        << "  \"status\": \"" << (passes ? "promote_startup_only"
                                          : "terminal_negative")
        << "\",\n"
        << "  \"score_credit_bytes\": 0,\n"
        << "  \"symbols\": " << symbols << ",\n"
        << "  \"burn_in_symbols\": " << burn_in << ",\n"
        << "  \"development_symbols\": " << (split_symbol - burn_in) << ",\n"
        << "  \"holdout_symbols\": " << (symbols - split_symbol) << ",\n"
        << "  \"rule_active\": " << (rule.active ? "true" : "false") << ",\n"
        << "  \"family\": " << rule.family << ",\n"
        << "  \"category\": " << rule.category << ",\n"
        << "  \"development_gain_qbits_after_price\": " << rule.gain_qbits << ",\n"
        << "  \"fired_holdout_rows\": " << fired << ",\n"
        << "  \"real_union_gain_bits\": " << static_cast<double>(real_union) << ",\n"
        << "  \"shifted_union_gain_bits\": "
        << static_cast<double>(shifted_union) << ",\n"
        << "  \"parent_holdout_payload_bytes\": "
        << parent_encoder.output.size() << ",\n"
        << "  \"candidate_holdout_payload_bytes\": "
        << candidate_encoder.output.size() << ",\n"
        << "  \"model_bytes\": " << model_bytes << ",\n"
        << "  \"net_saved_bytes\": " << net << ",\n"
        << "  \"net_bytes_per_million_wrt\": " << bpm << ",\n"
        << "  \"decision\": \""
        << (passes ? "authorize_larger_sparse_router_trace"
                   : "retire_compact_nncp_sparse_router_startup")
        << "\"\n"
        << "}\n";
    out.close();
    std::cout << "rule=" << rule.active
              << " family=" << rule.family
              << " category=" << rule.category
              << " dev_gain_qbits=" << rule.gain_qbits
              << " fired=" << fired
              << " real_u0=" << static_cast<double>(real_union)
              << " shifted_u0=" << static_cast<double>(shifted_union)
              << " parent=" << parent_encoder.output.size()
              << " candidate=" << candidate_encoder.output.size()
              << " model=" << model_bytes
              << " net=" << net
              << " bpm=" << bpm << "\n";
    return 0;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
