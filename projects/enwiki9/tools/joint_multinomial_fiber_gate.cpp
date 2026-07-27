#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
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

struct RangeEncoder {
  uint32_t x1 = 0;
  uint32_t x2 = 0xffffffffu;
  std::vector<uint8_t> out;

  void update(uint16_t p1, int bit) {
    const uint32_t delta = x2 - x1;
    const uint32_t midpoint =
        x1 + (delta >> 16) * p1 + ((delta & 0xffffu) * p1 >> 16);
    if (bit) {
      x2 = midpoint;
    } else {
      x1 = midpoint + 1;
    }
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
    if (position >= input.size()) return 0;
    return input[position++];
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
    size_t p0 = 0;
    size_t p1 = line.find('\t', p0);
    size_t p2 = line.find('\t', p1 + 1);
    size_t p3 = line.find('\t', p2 + 1);
    size_t p4 = line.find('\t', p3 + 1);
    if (p1 == std::string::npos || p2 == std::string::npos ||
        p3 == std::string::npos || p4 == std::string::npos) {
      throw std::runtime_error("short residual-cache row");
    }
    uint64_t pos = std::stoull(line.substr(p0, p1 - p0));
    int bit_pos = std::stoi(line.substr(p1 + 1, p2 - p1 - 1));
    int bit = std::stoi(line.substr(p2 + 1, p3 - p2 - 1));
    unsigned long probability =
        std::stoul(line.substr(p3 + 1, p4 - p3 - 1));
    if (pos != row / 8 || bit_pos != static_cast<int>(row % 8) ||
        pos >= wrt.size() || probability < 1 || probability > 65535) {
      throw std::runtime_error("residual-cache alignment failure");
    }
    int expected = (wrt[pos] >> (7 - bit_pos)) & 1;
    if (bit != expected) {
      throw std::runtime_error("truth/WRT mismatch");
    }
    trace.probabilities.push_back(static_cast<uint16_t>(probability));
    trace.bits.push_back(static_cast<uint8_t>(bit));
    ++row;
  }
  if (row != wrt.size() * 8) {
    throw std::runtime_error("incomplete residual-cache trace");
  }
  return trace;
}

uint16_t ratio_probability(uint64_t ones, uint64_t total) {
  if (ones == 0 || ones == total || total == 0) {
    throw std::runtime_error("noncoding ratio requested");
  }
  uint64_t q = (ones * kProbTotal + total / 2) / total;
  q = std::max<uint64_t>(1, std::min<uint64_t>(65535, q));
  return static_cast<uint16_t>(q);
}

struct CountTree {
  size_t leaf_count = 1;
  std::vector<uint64_t> tree;

  explicit CountTree(const std::vector<uint64_t>& counts) {
    while (leaf_count < counts.size()) leaf_count <<= 1;
    tree.assign(2 * leaf_count, 0);
    for (size_t i = 0; i < counts.size(); ++i) {
      tree[leaf_count + i] = counts[i];
    }
    for (size_t i = leaf_count; i-- > 1;) {
      tree[i] = tree[2 * i] + tree[2 * i + 1];
    }
  }

  void decrement(size_t category) {
    size_t node = leaf_count + category;
    if (tree[node] == 0) throw std::runtime_error("category count underrun");
    --tree[node];
    while ((node >>= 1) != 0) {
      tree[node] = tree[2 * node] + tree[2 * node + 1];
    }
  }
};

std::vector<uint8_t> encode_categories(
    const std::vector<uint16_t>& categories,
    const std::vector<uint64_t>& counts) {
  CountTree counts_tree(counts);
  RangeEncoder encoder;
  for (uint16_t category : categories) {
    size_t node = 1;
    size_t lo = 0;
    size_t hi = counts_tree.leaf_count;
    while (hi - lo > 1) {
      size_t mid = (lo + hi) / 2;
      uint64_t left = counts_tree.tree[2 * node];
      uint64_t right = counts_tree.tree[2 * node + 1];
      if (left == 0) {
        node = 2 * node + 1;
        lo = mid;
      } else if (right == 0) {
        node = 2 * node;
        hi = mid;
      } else {
        bool bit = category >= mid;
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
    if (lo != category) throw std::runtime_error("category tree mismatch");
    counts_tree.decrement(category);
  }
  encoder.finish();
  return encoder.out;
}

std::vector<uint16_t> decode_categories(
    size_t length, const std::vector<uint64_t>& counts,
    const std::vector<uint8_t>& payload) {
  CountTree counts_tree(counts);
  RangeDecoder decoder(payload);
  std::vector<uint16_t> categories;
  categories.reserve(length);
  for (size_t i = 0; i < length; ++i) {
    size_t node = 1;
    size_t lo = 0;
    size_t hi = counts_tree.leaf_count;
    while (hi - lo > 1) {
      size_t mid = (lo + hi) / 2;
      uint64_t left = counts_tree.tree[2 * node];
      uint64_t right = counts_tree.tree[2 * node + 1];
      if (left == 0) {
        node = 2 * node + 1;
        lo = mid;
      } else if (right == 0) {
        node = 2 * node;
        hi = mid;
      } else {
        int bit = decoder.decode(ratio_probability(right, left + right));
        if (bit) {
          node = 2 * node + 1;
          lo = mid;
        } else {
          node = 2 * node;
          hi = mid;
        }
      }
    }
    categories.push_back(static_cast<uint16_t>(lo));
    counts_tree.decrement(lo);
  }
  return categories;
}

bool nonempty_side_coder_control() {
  const std::vector<uint64_t> counts{5, 3, 2};
  const std::vector<uint16_t> categories{0, 1, 0, 2, 1, 0, 2, 0, 1, 0};
  const std::vector<uint8_t> payload =
      encode_categories(categories, counts);
  return decode_categories(categories.size(), counts, payload) == categories;
}

void set_choice(std::vector<uint64_t>& bits, size_t index) {
  bits[index >> 6] |= uint64_t{1} << (index & 63);
}

bool get_choice(const std::vector<uint64_t>& bits, size_t index) {
  return (bits[index >> 6] >> (index & 63)) & 1u;
}

void write_json(
    const std::string& path, uint64_t rows, uint64_t n,
    uint64_t baseline, uint64_t literal, uint64_t side_payload,
    uint64_t side_model, const std::vector<uint8_t>& selected,
    long double ideal_gain, long double best_nonempty_ideal_gain, int64_t net,
    bool parent_identity, bool side_roundtrip, bool side_control,
    bool literal_roundtrip, bool wrt_roundtrip) {
  std::ofstream o(path);
  if (!o) throw std::runtime_error("cannot write " + path);
  o << std::fixed << std::setprecision(6);
  o << "{\n"
    << "  \"schema\": \"joint_multinomial_fiber_v1\",\n"
    << "  \"id\": \"joint_multinomial_fiber_v1\",\n"
    << "  \"status\": \""
    << (net >= 2000 ? "promotion_threshold_pass" : "terminal_negative")
    << "\",\n"
    << "  \"evidence_level\": \"causal_shadow\",\n"
    << "  \"score_credit_bytes\": 0,\n"
    << "  \"trace_rows\": " << rows << ",\n"
    << "  \"wrt_bytes\": " << n << ",\n"
    << "  \"selected_symbol_count\": " << selected.size() << ",\n"
    << "  \"selected_symbols\": [";
  for (size_t i = 0; i < selected.size(); ++i) {
    if (i) o << ", ";
    o << static_cast<unsigned>(selected[i]);
  }
  o << "],\n"
    << "  \"ideal_net_bits\": " << static_cast<double>(ideal_gain) << ",\n"
    << "  \"best_nonempty_ideal_net_bits\": "
    << static_cast<double>(best_nonempty_ideal_gain) << ",\n"
    << "  \"baseline_payload_bytes\": " << baseline << ",\n"
    << "  \"residual_payload_bytes\": " << literal << ",\n"
    << "  \"side_range_payload_bytes\": " << side_payload << ",\n"
    << "  \"side_model_and_frame_bytes\": " << side_model << ",\n"
    << "  \"candidate_total_bytes\": "
    << (literal + side_payload + side_model) << ",\n"
    << "  \"net_saved_bytes\": " << net << ",\n"
    << "  \"net_bytes_per_million_raw\": "
    << static_cast<double>(net) << ",\n"
    << "  \"parent_archive_identity\": "
    << (parent_identity ? "true" : "false") << ",\n"
    << "  \"side_coder_roundtrip\": "
    << (side_roundtrip ? "true" : "false") << ",\n"
    << "  \"nonempty_side_coder_control\": "
    << (side_control ? "true" : "false") << ",\n"
    << "  \"residual_coder_roundtrip\": "
    << (literal_roundtrip ? "true" : "false") << ",\n"
    << "  \"exact_wrt_roundtrip\": "
    << (wrt_roundtrip ? "true" : "false") << ",\n"
    << "  \"promotion_floor_bytes_per_million_raw\": 2000,\n"
    << "  \"decision\": \""
    << (net >= 2000 ? "authorize_native_integration"
                    : "retire_joint_full_symbol_fibers")
    << "\",\n"
    << "  \"claim_boundary\": \"Exact opening-1M joint-fiber shadow with "
       "integer side coding and parent probability replay; no native or "
       "full-corpus score credit.\"\n"
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
    if (archive.size() < 37) throw std::runtime_error("short parent archive");
    const Trace trace = read_trace(argv[1], wrt);
    const uint64_t rows = trace.bits.size();
    const uint64_t n = wrt.size();
    const bool side_control = nonempty_side_coder_control();
    if (!side_control) {
      throw std::runtime_error("nonempty side-coder control failed");
    }

    RangeEncoder parent;
    std::array<uint64_t, 256> symbol_counts{};
    std::array<long double, 256> symbol_costs{};
    for (uint64_t j = 0; j < n; ++j) {
      uint8_t value = wrt[j];
      ++symbol_counts[value];
      for (int b = 0; b < 8; ++b) {
        uint64_t i = 8 * j + b;
        uint16_t p = trace.probabilities[i];
        int bit = trace.bits[i];
        parent.update(p, bit);
        long double truth_probability =
            bit ? static_cast<long double>(p) / kProbTotal
                : static_cast<long double>(kProbTotal - p) / kProbTotal;
        symbol_costs[value] -= std::log2(truth_probability);
      }
    }
    parent.finish();

    uint64_t wrt_bytes = archive.at(0) & 0x7fu;
    for (int i = 1; i < 5; ++i) wrt_bytes = (wrt_bytes << 8) | archive.at(i);
    if (wrt_bytes != n) throw std::runtime_error("archive WRT length mismatch");
    const size_t header_bytes = wrt_bytes < 10000 ? 5 : 37;
    const std::vector<uint8_t> expected(
        archive.begin() + header_bytes, archive.end());
    const bool parent_identity = parent.out == expected;

    const long double inv_log2 = 1.0L / std::log(2.0L);
    const long double log_n_factorial =
        std::lgammal(static_cast<long double>(n) + 1) * inv_log2;
    const long double neg_inf =
        -std::numeric_limits<long double>::infinity();
    std::vector<long double> dp(n + 1, neg_inf);
    dp[0] = 0;
    const size_t choice_words = (n + 64) / 64;
    std::array<std::vector<uint64_t>, 256> choices;
    for (auto& row : choices) row.assign(choice_words, 0);

    for (int value = 0; value < 256; ++value) {
      uint64_t count = symbol_counts[value];
      if (count == 0) continue;
      long double item =
          symbol_costs[value] - 32.0L +
          std::lgammal(static_cast<long double>(count) + 1) * inv_log2;
      for (uint64_t k = n - count + 1; k-- > 0;) {
        if (!std::isfinite(dp[k])) continue;
        long double candidate = dp[k] + item;
        if (candidate > dp[k + count]) {
          dp[k + count] = candidate;
          set_choice(choices[value], k + count);
        }
      }
    }

    long double best_gain = 0;
    uint64_t best_k = 0;
    long double best_nonempty_gain = neg_inf;
    for (uint64_t k = 1; k <= n; ++k) {
      if (!std::isfinite(dp[k])) continue;
      long double log_falling =
          log_n_factorial -
          std::lgammal(static_cast<long double>(n - k) + 1) * inv_log2;
      long double gain = dp[k] - 48.0L - log_falling;
      if (gain > best_nonempty_gain) best_nonempty_gain = gain;
      if (gain > best_gain) {
        best_gain = gain;
        best_k = k;
      }
    }

    std::array<bool, 256> is_selected{};
    uint64_t backtrack_k = best_k;
    for (int value = 255; value >= 0; --value) {
      uint64_t count = symbol_counts[value];
      if (count != 0 && backtrack_k >= count &&
          get_choice(choices[value], backtrack_k)) {
        is_selected[value] = true;
        backtrack_k -= count;
      }
    }
    if (backtrack_k != 0) throw std::runtime_error("knapsack backtrack failed");

    std::vector<uint8_t> selected;
    std::array<uint16_t, 256> category_of{};
    for (int value = 0; value < 256; ++value) {
      if (is_selected[value]) {
        selected.push_back(static_cast<uint8_t>(value));
        category_of[value] = static_cast<uint16_t>(selected.size());
      }
    }

    if (selected.empty()) {
      write_json(argv[4], rows, n, parent.out.size(), parent.out.size(), 0, 0,
                 selected, best_gain, best_nonempty_gain, 0, parent_identity,
                 true, side_control, true, true);
      std::cout << "selected=0 baseline=" << parent.out.size()
                << " candidate=" << parent.out.size() << " net=0\n";
      return parent_identity ? 0 : 1;
    }

    std::vector<uint64_t> category_counts(selected.size() + 1, 0);
    category_counts[0] = n - best_k;
    for (size_t i = 0; i < selected.size(); ++i) {
      category_counts[i + 1] = symbol_counts[selected[i]];
    }
    std::vector<uint16_t> categories;
    categories.reserve(n);
    for (uint8_t value : wrt) categories.push_back(category_of[value]);

    const std::vector<uint8_t> side_payload =
        encode_categories(categories, category_counts);
    const std::vector<uint16_t> decoded_categories =
        decode_categories(n, category_counts, side_payload);
    const bool side_roundtrip = decoded_categories == categories;

    RangeEncoder literal;
    for (uint64_t j = 0; j < n; ++j) {
      if (categories[j] != 0) continue;
      for (int b = 0; b < 8; ++b) {
        uint64_t i = 8 * j + b;
        literal.update(trace.probabilities[i], trace.bits[i]);
      }
    }
    literal.finish();

    RangeDecoder literal_decoder(literal.out);
    std::vector<uint8_t> reconstructed;
    reconstructed.reserve(n);
    bool literal_roundtrip = true;
    for (uint64_t j = 0; j < n; ++j) {
      uint16_t category = decoded_categories[j];
      if (category != 0) {
        if (category > selected.size()) {
          throw std::runtime_error("decoded category out of range");
        }
        reconstructed.push_back(selected[category - 1]);
      } else {
        uint8_t value = 0;
        for (int b = 0; b < 8; ++b) {
          uint64_t i = 8 * j + b;
          int bit = literal_decoder.decode(trace.probabilities[i]);
          value = static_cast<uint8_t>((value << 1) | bit);
          if (bit != trace.bits[i]) literal_roundtrip = false;
        }
        reconstructed.push_back(value);
      }
    }
    const bool wrt_roundtrip = reconstructed == wrt;
    const uint64_t side_model = 6 + 4 * selected.size();
    const uint64_t candidate_total =
        literal.out.size() + side_payload.size() + side_model;
    const int64_t net = static_cast<int64_t>(parent.out.size()) -
                        static_cast<int64_t>(candidate_total);

    write_json(argv[4], rows, n, parent.out.size(), literal.out.size(),
               side_payload.size(), side_model, selected, best_gain,
               best_nonempty_gain, net, parent_identity, side_roundtrip,
               side_control, literal_roundtrip,
               wrt_roundtrip);
    std::cout << "selected=" << selected.size()
              << " extracted=" << best_k
              << " baseline=" << parent.out.size()
              << " residual=" << literal.out.size()
              << " side_payload=" << side_payload.size()
              << " side_model=" << side_model
              << " candidate=" << candidate_total
              << " net=" << net
              << " parent_identity=" << parent_identity
              << " side_roundtrip=" << side_roundtrip
              << " literal_roundtrip=" << literal_roundtrip
              << " wrt_roundtrip=" << wrt_roundtrip << "\n";
    return (parent_identity && side_roundtrip && literal_roundtrip &&
            wrt_roundtrip)
               ? 0
               : 1;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
