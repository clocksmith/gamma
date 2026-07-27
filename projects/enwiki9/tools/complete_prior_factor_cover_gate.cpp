#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr int kScale = 256;
constexpr int kMinLength = 8;
constexpr int kMaxLength = 255;
constexpr int kCommandBytes = 7;
constexpr int kHeaderBytes = 4;

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

struct RMQ {
  int size = 1;
  std::vector<int> tree;
  explicit RMQ(const std::vector<int>& values) {
    while (size < static_cast<int>(values.size())) size <<= 1;
    tree.assign(2 * size, std::numeric_limits<int>::max());
    for (size_t i = 0; i < values.size(); ++i) tree[size + i] = values[i];
    for (int i = size - 1; i; --i) tree[i] = std::min(tree[2 * i], tree[2 * i + 1]);
  }
  int Query(int left, int right) const {
    int result = std::numeric_limits<int>::max();
    for (left += size, right += size; left < right; left >>= 1, right >>= 1) {
      if (left & 1) result = std::min(result, tree[left++]);
      if (right & 1) result = std::min(result, tree[--right]);
    }
    return result;
  }
};

struct Back {
  int previous = -1;
  int length = 0;
  int source = -1;
};

struct Command {
  int target = 0;
  int source = 0;
  int length = 0;
};

std::vector<uint8_t> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

std::vector<int> BuildSuffixArray(const std::vector<uint8_t>& text) {
  const int n = static_cast<int>(text.size());
  std::vector<int> sa(n), rank(n), next(n);
  std::iota(sa.begin(), sa.end(), 0);
  for (int i = 0; i < n; ++i) rank[i] = text[i];
  for (int width = 1; width < n; width <<= 1) {
    std::sort(sa.begin(), sa.end(), [&](int a, int b) {
      if (rank[a] != rank[b]) return rank[a] < rank[b];
      const int ra = a + width < n ? rank[a + width] : -1;
      const int rb = b + width < n ? rank[b + width] : -1;
      return ra < rb;
    });
    next[sa[0]] = 0;
    for (int i = 1; i < n; ++i) {
      const int a = sa[i - 1], b = sa[i];
      const bool different =
          rank[a] != rank[b] ||
          (a + width < n ? rank[a + width] : -1) !=
              (b + width < n ? rank[b + width] : -1);
      next[b] = next[a] + different;
    }
    rank.swap(next);
    if (rank[sa.back()] == n - 1) break;
  }
  return sa;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: complete_prior_factor_cover_gate TRACE ARCHIVE DECISION\n";
    return 2;
  }
  try {
    const auto trace = ReadFile(argv[1]);
    const auto archive = ReadFile(argv[2]);
    constexpr char magic[] = "FX2PT01\n";
    if (trace.size() < 8 || std::memcmp(trace.data(), magic, 8) != 0 ||
        (trace.size() - 8) % 3 != 0) {
      throw std::runtime_error("invalid trace");
    }
    const int64_t rows = static_cast<int64_t>((trace.size() - 8) / 3);
    if (rows % 8) throw std::runtime_error("unaligned trace");
    const int n = static_cast<int>(rows / 8);
    std::vector<uint16_t> probabilities(rows);
    std::vector<uint8_t> truth(rows), bytes(n);
    std::vector<int64_t> byte_qbits(n, 0), prefix(n + 1, 0);
    RangeEncoder baseline;
    for (int byte = 0; byte < n; ++byte) {
      uint8_t value = 0;
      for (int bit_index = 0; bit_index < 8; ++bit_index) {
        const int64_t row = static_cast<int64_t>(byte) * 8 + bit_index;
        const size_t offset = 8 + static_cast<size_t>(row) * 3;
        const uint16_t p1 = static_cast<uint16_t>(
            trace[offset] | (static_cast<uint16_t>(trace[offset + 1]) << 8));
        const int bit = trace[offset + 2];
        if (p1 == 0 || bit > 1) throw std::runtime_error("invalid row");
        probabilities[row] = p1;
        truth[row] = static_cast<uint8_t>(bit);
        value = static_cast<uint8_t>((value << 1) | bit);
        const double probability =
            bit ? static_cast<double>(p1) / 65536.0
                : 1.0 - static_cast<double>(p1) / 65536.0;
        byte_qbits[byte] += static_cast<int64_t>(
            std::llround(-std::log2(probability) * kScale));
        baseline.Update(p1, bit);
      }
      bytes[byte] = value;
      prefix[byte + 1] = prefix[byte] + byte_qbits[byte];
    }
    baseline.Finish();

    uint64_t wrt_bytes = archive.at(0) & 0x7fu;
    for (int i = 1; i < 5; ++i) wrt_bytes = (wrt_bytes << 8) | archive.at(i);
    const size_t header_bytes = wrt_bytes < 10000 ? 5 : 37;
    const std::vector<uint8_t> parent_payload(
        archive.begin() + static_cast<std::ptrdiff_t>(header_bytes),
        archive.end());
    const bool parent_identity = parent_payload == baseline.output;

    const auto sa = BuildSuffixArray(bytes);
    std::vector<int> inverse(n), lcp(n, 0);
    for (int rank = 0; rank < n; ++rank) inverse[sa[rank]] = rank;
    int common = 0;
    for (int i = 0; i < n; ++i) {
      const int rank = inverse[i];
      if (rank == 0) continue;
      const int j = sa[rank - 1];
      while (i + common < n && j + common < n &&
             bytes[i + common] == bytes[j + common]) {
        ++common;
      }
      lcp[rank] = common;
      if (common) --common;
    }
    const RMQ rmq(lcp);
    auto lcp_ranks = [&](int left, int right) {
      if (left == right) return n - sa[left];
      if (left > right) std::swap(left, right);
      return rmq.Query(left + 1, right + 1);
    };

    std::vector<int> lpf(n, 0), source(n, -1);
    std::set<int> active;
    for (int i = 0; i < n; ++i) {
      const int rank = inverse[i];
      auto it = active.lower_bound(rank);
      auto consider = [&](int neighbor_rank) {
        int length = std::min({lcp_ranks(rank, neighbor_rank),
                               kMaxLength, n - i});
        const int candidate_source = sa[neighbor_rank];
        if (length > lpf[i] ||
            (length == lpf[i] && length > 0 &&
             candidate_source < source[i])) {
          lpf[i] = length;
          source[i] = candidate_source;
        }
      };
      if (it != active.end()) consider(*it);
      if (it != active.begin()) consider(*std::prev(it));
      active.insert(rank);
    }

    const int64_t negative = std::numeric_limits<int64_t>::min() / 4;
    std::vector<int64_t> dp(n + 1, negative);
    std::vector<int> commands(n + 1, std::numeric_limits<int>::max());
    std::vector<Back> back(n + 1);
    dp[0] = 0;
    commands[0] = 0;
    auto improve = [&](int at, int64_t value, int command_count,
                       Back candidate) {
      if (value > dp[at] ||
          (value == dp[at] && command_count < commands[at])) {
        dp[at] = value;
        commands[at] = command_count;
        back[at] = candidate;
      }
    };
    for (int i = 0; i < n; ++i) {
      improve(i + 1, dp[i], commands[i], {i, 0, -1});
      for (int length = kMinLength; length <= lpf[i]; ++length) {
        const int64_t weight =
            prefix[i + length] - prefix[i] -
            static_cast<int64_t>(kCommandBytes * 8 * kScale);
        improve(i + length, dp[i] + weight, commands[i] + 1,
                {i, length, source[i]});
      }
    }

    std::vector<Command> selected;
    for (int at = n; at > 0;) {
      const Back b = back[at];
      if (b.previous < 0) throw std::runtime_error("broken DP backpointer");
      if (b.length > 0) selected.push_back({b.previous, b.source, b.length});
      at = b.previous;
    }
    std::reverse(selected.begin(), selected.end());

    std::vector<int> command_at(n, -1);
    std::vector<uint8_t> covered(n, 0);
    for (size_t i = 0; i < selected.size(); ++i) {
      const auto& command = selected[i];
      command_at[command.target] = static_cast<int>(i);
      for (int j = 0; j < command.length; ++j) {
        if (covered[command.target + j])
          throw std::runtime_error("overlapping cover");
        covered[command.target + j] = 1;
      }
    }

    RangeEncoder literal_encoder;
    std::vector<uint8_t> literals;
    for (int byte = 0; byte < n; ++byte) {
      if (covered[byte]) continue;
      literals.push_back(bytes[byte]);
      for (int bit = 0; bit < 8; ++bit) {
        const int64_t row = static_cast<int64_t>(byte) * 8 + bit;
        literal_encoder.Update(probabilities[row], truth[row]);
      }
    }
    literal_encoder.Finish();

    std::vector<uint8_t> reconstructed;
    reconstructed.reserve(n);
    size_t literal_index = 0;
    int target = 0;
    while (target < n) {
      const int id = command_at[target];
      if (id >= 0) {
        const auto& command = selected[id];
        if (command.source >= target)
          throw std::runtime_error("noncausal command");
        for (int j = 0; j < command.length; ++j) {
          const int source_index = command.source + j;
          if (source_index >= static_cast<int>(reconstructed.size()))
            throw std::runtime_error("invalid overlapping copy");
          reconstructed.push_back(reconstructed[source_index]);
        }
        target += command.length;
      } else {
        if (literal_index >= literals.size())
          throw std::runtime_error("literal underrun");
        reconstructed.push_back(literals[literal_index++]);
        ++target;
      }
    }
    const bool roundtrip =
        reconstructed == bytes && literal_index == literals.size();
    const int64_t side_bytes =
        kHeaderBytes + static_cast<int64_t>(selected.size()) * kCommandBytes;
    const int64_t candidate_bytes =
        static_cast<int64_t>(literal_encoder.output.size()) + side_bytes;
    const int64_t net =
        static_cast<int64_t>(baseline.output.size()) - candidate_bytes;
    const bool passes_gate = net >= 2000;

    std::ofstream out(argv[3]);
    if (!out) throw std::runtime_error("cannot write decision");
    out << "{\n"
        << "  \"id\": \"complete_prior_factor_cover_v1\",\n"
        << "  \"status\": \"" << (passes_gate ? "promote" : "terminal_negative")
        << "\",\n"
        << "  \"score_credit_bytes\": 0,\n"
        << "  \"wrt_bytes\": " << n << ",\n"
        << "  \"selected_commands\": " << selected.size() << ",\n"
        << "  \"covered_bytes\": "
        << std::count(covered.begin(), covered.end(), 1) << ",\n"
        << "  \"baseline_payload_bytes\": " << baseline.output.size() << ",\n"
        << "  \"literal_payload_bytes\": " << literal_encoder.output.size() << ",\n"
        << "  \"side_bytes\": " << side_bytes << ",\n"
        << "  \"candidate_total_bytes\": " << candidate_bytes << ",\n"
        << "  \"net_saved_bytes\": " << net << ",\n"
        << "  \"net_bytes_per_million_raw\": " << net << ",\n"
        << "  \"target_gate_bytes_per_million\": 2000,\n"
        << "  \"parent_archive_identity\": "
        << (parent_identity ? "true" : "false") << ",\n"
        << "  \"exact_wrt_roundtrip\": " << (roundtrip ? "true" : "false") << ",\n"
        << "  \"decision\": \""
        << (passes_gate ? "authorize_distant_complete_copy_cover"
                        : "retire_fixed_price_exact_copy_sidecars")
        << "\"\n"
        << "}\n";
    out.close();

    std::cout << "commands=" << selected.size()
              << " covered="
              << std::count(covered.begin(), covered.end(), 1)
              << " baseline=" << baseline.output.size()
              << " literal=" << literal_encoder.output.size()
              << " side=" << side_bytes
              << " net=" << net
              << " parent_identity=" << parent_identity
              << " roundtrip=" << roundtrip << "\n";
    return (parent_identity && roundtrip) ? 0 : 1;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
