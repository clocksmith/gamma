#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr uint32_t kProbTotal = 65536;
constexpr size_t kContextCount = 65536;
constexpr size_t kAlphabet = 256;

struct RangeEncoder {
  uint32_t x1 = 0;
  uint32_t x2 = 0xffffffffu;
  std::vector<uint8_t> out;

  void update(uint16_t p1, int bit) {
    const uint32_t delta = x2 - x1;
    const uint32_t midpoint =
        x1 + (delta >> 16) * p1 + ((delta & 0xffffu) * p1 >> 16);
    if (bit) x2 = midpoint;
    else x1 = midpoint + 1;
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      out.push_back(static_cast<uint8_t>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
  }

  void finish() {
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      out.push_back(static_cast<uint8_t>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
    out.push_back(static_cast<uint8_t>(x2 >> 24));
  }
};

struct RangeDecoder {
  const std::vector<uint8_t>& input;
  size_t position = 0;
  uint32_t x1 = 0;
  uint32_t x2 = 0xffffffffu;
  uint32_t x = 0;

  explicit RangeDecoder(const std::vector<uint8_t>& data) : input(data) {
    for (int i = 0; i < 4; ++i) x = (x << 8) + read_byte();
  }

  uint8_t read_byte() {
    return position < input.size() ? input[position++] : 0;
  }

  int decode(uint16_t p1) {
    const uint32_t delta = x2 - x1;
    const uint32_t midpoint =
        x1 + (delta >> 16) * p1 + ((delta & 0xffffu) * p1 >> 16);
    int bit;
    if (x <= midpoint) {
      bit = 1;
      x2 = midpoint;
    } else {
      bit = 0;
      x1 = midpoint + 1;
    }
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
      x = (x << 8) + read_byte();
    }
    return bit;
  }
};

std::vector<uint8_t> read_all(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open " + path);
  return {std::istreambuf_iterator<char>(in),
          std::istreambuf_iterator<char>()};
}

struct Trace {
  std::vector<uint16_t> probabilities;
  std::vector<uint8_t> bits;
};

Trace read_trace(const std::string& path,
                 const std::vector<uint8_t>& wrt) {
  std::ifstream in(path);
  if (!in) throw std::runtime_error("cannot open " + path);
  std::string line;
  if (!std::getline(in, line) ||
      line.rfind("pos\tbit_pos\tbit\tp1\t", 0) != 0) {
    throw std::runtime_error("invalid residual-cache header");
  }
  Trace trace;
  trace.probabilities.reserve(wrt.size() * 8);
  trace.bits.reserve(wrt.size() * 8);
  uint64_t row = 0;
  while (std::getline(in, line)) {
    size_t t1 = line.find('\t');
    size_t t2 = line.find('\t', t1 + 1);
    size_t t3 = line.find('\t', t2 + 1);
    size_t t4 = line.find('\t', t3 + 1);
    if (t1 == std::string::npos || t2 == std::string::npos ||
        t3 == std::string::npos || t4 == std::string::npos) {
      throw std::runtime_error("short residual-cache row");
    }
    uint64_t pos = std::stoull(line.substr(0, t1));
    int bit_pos = std::stoi(line.substr(t1 + 1, t2 - t1 - 1));
    int bit = std::stoi(line.substr(t2 + 1, t3 - t2 - 1));
    unsigned long probability =
        std::stoul(line.substr(t3 + 1, t4 - t3 - 1));
    if (pos != row / 8 || bit_pos != static_cast<int>(row % 8) ||
        pos >= wrt.size() || probability < 1 || probability > 65535) {
      throw std::runtime_error("trace alignment failure");
    }
    if (bit != ((wrt[pos] >> (7 - bit_pos)) & 1)) {
      throw std::runtime_error("trace truth mismatch");
    }
    trace.probabilities.push_back(static_cast<uint16_t>(probability));
    trace.bits.push_back(static_cast<uint8_t>(bit));
    ++row;
  }
  if (row != wrt.size() * 8) throw std::runtime_error("incomplete trace");
  return trace;
}

uint16_t ratio_probability(uint64_t ones, uint64_t total) {
  if (ones == 0 || ones == total || total == 0) {
    throw std::runtime_error("invalid coding ratio");
  }
  uint64_t q = (ones * kProbTotal + total / 2) / total;
  return static_cast<uint16_t>(
      std::max<uint64_t>(1, std::min<uint64_t>(65535, q)));
}

struct SymbolTree {
  std::array<uint64_t, 512> count{};

  explicit SymbolTree(const std::array<uint32_t, 256>& source) {
    for (size_t i = 0; i < 256; ++i) count[256 + i] = source[i];
    for (size_t i = 256; i-- > 1;) {
      count[i] = count[2 * i] + count[2 * i + 1];
    }
  }

  void decrement(uint16_t symbol) {
    size_t node = 256 + symbol;
    if (count[node] == 0) throw std::runtime_error("symbol count underrun");
    --count[node];
    while ((node >>= 1) != 0) {
      count[node] = count[2 * node] + count[2 * node + 1];
    }
  }
};

void encode_symbol(SymbolTree& tree, uint8_t symbol, RangeEncoder& encoder) {
  size_t node = 1;
  size_t lo = 0;
  size_t hi = 256;
  while (hi - lo > 1) {
    size_t mid = (lo + hi) / 2;
    uint64_t left = tree.count[2 * node];
    uint64_t right = tree.count[2 * node + 1];
    if (left == 0) {
      node = 2 * node + 1;
      lo = mid;
    } else if (right == 0) {
      node = 2 * node;
      hi = mid;
    } else {
      bool bit = symbol >= mid;
      encoder.update(ratio_probability(right, left + right), bit);
      if (bit) {
        node = 2 * node + 1;
        lo = mid;
      } else {
        node = 2 * node;
        hi = mid;
      }
    }
  }
  if (lo != symbol) throw std::runtime_error("symbol tree mismatch");
  tree.decrement(symbol);
}

uint8_t decode_symbol(SymbolTree& tree, RangeDecoder& decoder) {
  size_t node = 1;
  size_t lo = 0;
  size_t hi = 256;
  while (hi - lo > 1) {
    size_t mid = (lo + hi) / 2;
    uint64_t left = tree.count[2 * node];
    uint64_t right = tree.count[2 * node + 1];
    if (left == 0) {
      node = 2 * node + 1;
      lo = mid;
    } else if (right == 0) {
      node = 2 * node;
      hi = mid;
    } else if (decoder.decode(ratio_probability(right, left + right))) {
      node = 2 * node + 1;
      lo = mid;
    } else {
      node = 2 * node;
      hi = mid;
    }
  }
  tree.decrement(lo);
  return static_cast<uint8_t>(lo);
}

bool nonempty_side_control() {
  std::array<uint32_t, 256> counts{};
  counts[3] = 3;
  counts[19] = 2;
  counts[240] = 1;
  const std::vector<uint8_t> symbols{3, 19, 3, 240, 19, 3};
  SymbolTree encode_tree(counts);
  RangeEncoder encoder;
  for (uint8_t symbol : symbols) encode_symbol(encode_tree, symbol, encoder);
  encoder.finish();
  SymbolTree decode_tree(counts);
  RangeDecoder decoder(encoder.out);
  std::vector<uint8_t> decoded;
  for (size_t i = 0; i < symbols.size(); ++i) {
    decoded.push_back(decode_symbol(decode_tree, decoder));
  }
  return decoded == symbols;
}

struct ContextStats {
  std::array<uint32_t, 256> counts{};
  uint64_t total = 0;
  long double parent_cost = 0;
  uint16_t support = 0;
  long double ideal_contribution = 0;
  bool selected = false;
};

void write_json(
    const std::string& path, uint64_t rows, uint64_t n, uint64_t baseline,
    uint64_t residual, uint64_t side_payload, uint64_t model_bytes,
    uint64_t selected_contexts, uint64_t selected_occurrences,
    uint64_t support_entries, long double ideal_gain,
    long double best_context_gain, int64_t net, bool parent_identity,
    bool side_control, bool side_roundtrip, bool residual_roundtrip,
    bool wrt_roundtrip) {
  std::ofstream o(path);
  if (!o) throw std::runtime_error("cannot write " + path);
  o << std::fixed << std::setprecision(6);
  o << "{\n"
    << "  \"schema\": \"paid_conditional_multinomial_v1\",\n"
    << "  \"id\": \"paid_conditional_multinomial_c2_v1\",\n"
    << "  \"status\": \""
    << (net >= 2000 ? "promotion_threshold_pass" : "terminal_negative")
    << "\",\n"
    << "  \"evidence_level\": \"causal_shadow\",\n"
    << "  \"score_credit_bytes\": 0,\n"
    << "  \"trace_rows\": " << rows << ",\n"
    << "  \"wrt_bytes\": " << n << ",\n"
    << "  \"context_length_bytes\": 2,\n"
    << "  \"selected_contexts\": " << selected_contexts << ",\n"
    << "  \"selected_occurrences\": " << selected_occurrences << ",\n"
    << "  \"selected_support_entries\": " << support_entries << ",\n"
    << "  \"ideal_net_bits\": " << static_cast<double>(ideal_gain) << ",\n"
    << "  \"best_single_context_ideal_bits\": "
    << static_cast<double>(best_context_gain) << ",\n"
    << "  \"baseline_payload_bytes\": " << baseline << ",\n"
    << "  \"residual_payload_bytes\": " << residual << ",\n"
    << "  \"side_range_payload_bytes\": " << side_payload << ",\n"
    << "  \"side_model_and_frame_bytes\": " << model_bytes << ",\n"
    << "  \"candidate_total_bytes\": "
    << (residual + side_payload + model_bytes) << ",\n"
    << "  \"net_saved_bytes\": " << net << ",\n"
    << "  \"net_bytes_per_million_raw\": "
    << static_cast<double>(net) << ",\n"
    << "  \"parent_archive_identity\": "
    << (parent_identity ? "true" : "false") << ",\n"
    << "  \"nonempty_side_coder_control\": "
    << (side_control ? "true" : "false") << ",\n"
    << "  \"side_coder_roundtrip\": "
    << (side_roundtrip ? "true" : "false") << ",\n"
    << "  \"residual_coder_roundtrip\": "
    << (residual_roundtrip ? "true" : "false") << ",\n"
    << "  \"exact_wrt_roundtrip\": "
    << (wrt_roundtrip ? "true" : "false") << ",\n"
    << "  \"promotion_floor_bytes_per_million_raw\": 2000,\n"
    << "  \"decision\": \""
    << (net >= 2000 ? "authorize_native_integration"
                    : "retire_context2_conditional_multinomial")
    << "\",\n"
    << "  \"claim_boundary\": \"Exact opening-1M context-two conditional "
       "multinomial shadow; no native or full-corpus score credit.\"\n"
    << "}\n";
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: gate RESIDUAL_CACHE.tsv WRT.bin PARENT.cmix "
                 "DECISION.json\n";
    return 2;
  }
  try {
    const std::vector<uint8_t> wrt = read_all(argv[2]);
    const std::vector<uint8_t> archive = read_all(argv[3]);
    const Trace trace = read_trace(argv[1], wrt);
    if (archive.size() < 37 || wrt.size() < 2) {
      throw std::runtime_error("short frozen input");
    }
    const bool side_control = nonempty_side_control();
    if (!side_control) throw std::runtime_error("side control failed");

    std::vector<ContextStats> stats(kContextCount);
    RangeEncoder parent;
    for (size_t i = 0; i < wrt.size(); ++i) {
      uint16_t context = 0;
      if (i >= 2) {
        context = static_cast<uint16_t>(
            (static_cast<uint16_t>(wrt[i - 2]) << 8) | wrt[i - 1]);
        ++stats[context].counts[wrt[i]];
        ++stats[context].total;
      }
      for (int b = 0; b < 8; ++b) {
        size_t row = 8 * i + b;
        uint16_t p = trace.probabilities[row];
        int bit = trace.bits[row];
        parent.update(p, bit);
        if (i >= 2) {
          long double truth_probability =
              bit ? static_cast<long double>(p) / kProbTotal
                  : static_cast<long double>(kProbTotal - p) / kProbTotal;
          stats[context].parent_cost -= std::log2(truth_probability);
        }
      }
    }
    parent.finish();

    uint64_t encoded_wrt = archive.at(0) & 0x7fu;
    for (int i = 1; i < 5; ++i) {
      encoded_wrt = (encoded_wrt << 8) | archive.at(i);
    }
    if (encoded_wrt != wrt.size()) {
      throw std::runtime_error("archive WRT length mismatch");
    }
    const size_t header_bytes = encoded_wrt < 10000 ? 5 : 37;
    const std::vector<uint8_t> expected(
        archive.begin() + header_bytes, archive.end());
    const bool parent_identity = parent.out == expected;

    const long double inv_log2 = 1.0L / std::log(2.0L);
    long double positive_sum = 0;
    long double best_context_gain =
        -std::numeric_limits<long double>::infinity();
    for (ContextStats& context : stats) {
      if (context.total == 0) continue;
      long double log_multinomial =
          std::lgammal(static_cast<long double>(context.total) + 1) * inv_log2;
      for (uint32_t count : context.counts) {
        if (count != 0) {
          ++context.support;
          log_multinomial -=
              std::lgammal(static_cast<long double>(count) + 1) * inv_log2;
        }
      }
      uint64_t description_bytes = 4 + 4 * context.support;
      context.ideal_contribution =
          context.parent_cost - 8.0L * description_bytes - log_multinomial;
      best_context_gain =
          std::max(best_context_gain, context.ideal_contribution);
      if (context.ideal_contribution > 0) {
        context.selected = true;
        positive_sum += context.ideal_contribution;
      }
    }
    long double ideal_gain = positive_sum - 64.0L;
    if (ideal_gain <= 0) {
      for (ContextStats& context : stats) context.selected = false;
      ideal_gain = 0;
    }

    uint64_t selected_contexts = 0;
    uint64_t selected_occurrences = 0;
    uint64_t support_entries = 0;
    std::array<int32_t, kContextCount> model_index{};
    model_index.fill(-1);
    std::vector<SymbolTree> encode_models;
    for (size_t c = 0; c < stats.size(); ++c) {
      if (!stats[c].selected) continue;
      model_index[c] = static_cast<int32_t>(encode_models.size());
      encode_models.emplace_back(stats[c].counts);
      ++selected_contexts;
      selected_occurrences += stats[c].total;
      support_entries += stats[c].support;
    }

    if (selected_contexts == 0) {
      write_json(argv[4], trace.bits.size(), wrt.size(), parent.out.size(),
                 parent.out.size(), 0, 0, 0, 0, 0, ideal_gain,
                 best_context_gain, 0, parent_identity, side_control, true,
                 true, true);
      std::cout << "selected_contexts=0 baseline=" << parent.out.size()
                << " candidate=" << parent.out.size() << " net=0\n";
      return parent_identity ? 0 : 1;
    }

    RangeEncoder side_encoder;
    for (size_t i = 2; i < wrt.size(); ++i) {
      uint16_t context = static_cast<uint16_t>(
          (static_cast<uint16_t>(wrt[i - 2]) << 8) | wrt[i - 1]);
      int32_t index = model_index[context];
      if (index >= 0) {
        encode_symbol(encode_models[index], wrt[i], side_encoder);
      }
    }
    side_encoder.finish();

    RangeEncoder residual_encoder;
    for (size_t i = 0; i < wrt.size(); ++i) {
      bool selected = false;
      if (i >= 2) {
        uint16_t context = static_cast<uint16_t>(
            (static_cast<uint16_t>(wrt[i - 2]) << 8) | wrt[i - 1]);
        selected = model_index[context] >= 0;
      }
      if (selected) continue;
      for (int b = 0; b < 8; ++b) {
        size_t row = 8 * i + b;
        residual_encoder.update(trace.probabilities[row], trace.bits[row]);
      }
    }
    residual_encoder.finish();

    std::vector<SymbolTree> decode_models;
    for (const ContextStats& context : stats) {
      if (context.selected) decode_models.emplace_back(context.counts);
    }
    RangeDecoder side_decoder(side_encoder.out);
    RangeDecoder residual_decoder(residual_encoder.out);
    std::vector<uint8_t> reconstructed;
    reconstructed.reserve(wrt.size());
    bool side_roundtrip = true;
    bool residual_roundtrip = true;
    for (size_t i = 0; i < wrt.size(); ++i) {
      bool selected = false;
      int32_t index = -1;
      if (i >= 2) {
        uint16_t context = static_cast<uint16_t>(
            (static_cast<uint16_t>(reconstructed[i - 2]) << 8) |
            reconstructed[i - 1]);
        index = model_index[context];
        selected = index >= 0;
      }
      uint8_t value = 0;
      if (selected) {
        value = decode_symbol(decode_models[index], side_decoder);
        if (value != wrt[i]) side_roundtrip = false;
      } else {
        for (int b = 0; b < 8; ++b) {
          size_t row = 8 * i + b;
          int bit = residual_decoder.decode(trace.probabilities[row]);
          value = static_cast<uint8_t>((value << 1) | bit);
          if (bit != trace.bits[row]) residual_roundtrip = false;
        }
      }
      reconstructed.push_back(value);
    }
    const bool wrt_roundtrip = reconstructed == wrt;
    const uint64_t model_bytes =
        8 + 4 * selected_contexts + 4 * support_entries;
    const uint64_t candidate_total =
        residual_encoder.out.size() + side_encoder.out.size() + model_bytes;
    const int64_t net = static_cast<int64_t>(parent.out.size()) -
                        static_cast<int64_t>(candidate_total);

    write_json(
        argv[4], trace.bits.size(), wrt.size(), parent.out.size(),
        residual_encoder.out.size(), side_encoder.out.size(), model_bytes,
        selected_contexts, selected_occurrences, support_entries, ideal_gain,
        best_context_gain, net, parent_identity, side_control, side_roundtrip,
        residual_roundtrip, wrt_roundtrip);
    std::cout << "selected_contexts=" << selected_contexts
              << " selected_occurrences=" << selected_occurrences
              << " baseline=" << parent.out.size()
              << " residual=" << residual_encoder.out.size()
              << " side=" << side_encoder.out.size()
              << " model=" << model_bytes
              << " candidate=" << candidate_total
              << " net=" << net
              << " parent_identity=" << parent_identity
              << " side_roundtrip=" << side_roundtrip
              << " residual_roundtrip=" << residual_roundtrip
              << " wrt_roundtrip=" << wrt_roundtrip << "\n";
    return (parent_identity && side_control && side_roundtrip &&
            residual_roundtrip && wrt_roundtrip)
               ? 0
               : 1;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
