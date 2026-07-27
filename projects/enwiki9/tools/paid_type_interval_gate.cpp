#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr int kScale = 256;
constexpr int kCells = 256;
constexpr int kStrata = 8;
constexpr int kDescriptorBits = 72;
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

struct Stats {
  int64_t n = 0;
  int64_t e = 0;
  int64_t qbits = 0;
};

struct Interval {
  int stratum = 0;
  int lo = 0;
  int hi = 0;
  int64_t n = 0;
  int64_t e = 0;
  int64_t rank_bits = 0;
  int64_t weight_qbits = 0;
};

std::vector<uint8_t> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

long double Log2Choose(int64_t n, int64_t k) {
  if (k == 0 || k == n) return 0;
  return (std::lgammal(static_cast<long double>(n) + 1) -
          std::lgammal(static_cast<long double>(k) + 1) -
          std::lgammal(static_cast<long double>(n - k) + 1)) /
         std::log(2.0L);
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: paid_type_interval_gate TRACE ARCHIVE DECISION\n";
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
    std::vector<uint16_t> probabilities(rows);
    std::vector<uint8_t> truth(rows);
    std::array<std::array<Stats, kCells>, kStrata> cells{};
    RangeEncoder baseline;

    for (int64_t row = 0; row < rows; ++row) {
      const size_t offset = 8 + static_cast<size_t>(row) * 3;
      const uint16_t p1 = static_cast<uint16_t>(
          trace[offset] | (static_cast<uint16_t>(trace[offset + 1]) << 8));
      const int bit = trace[offset + 2];
      if (p1 == 0 || bit > 1) throw std::runtime_error("invalid trace row");
      probabilities[row] = p1;
      truth[row] = static_cast<uint8_t>(bit);
      const int stratum = static_cast<int>(row & 7);
      const int cell = p1 >> 8;
      const int modal = p1 >= 32768 ? 1 : 0;
      const double probability =
          bit ? static_cast<double>(p1) / 65536.0
              : 1.0 - static_cast<double>(p1) / 65536.0;
      Stats& s = cells[stratum][cell];
      ++s.n;
      s.e += bit != modal;
      s.qbits += static_cast<int64_t>(
          std::llround(-std::log2(probability) * kScale));
      baseline.Update(p1, bit);
    }
    baseline.Finish();

    uint64_t wrt_bytes = archive.at(0) & 0x7fu;
    for (int i = 1; i < 5; ++i) wrt_bytes = (wrt_bytes << 8) | archive.at(i);
    const size_t header_bytes = wrt_bytes < 10000 ? 5 : 37;
    const std::vector<uint8_t> parent_payload(
        archive.begin() + static_cast<std::ptrdiff_t>(header_bytes),
        archive.end());
    const bool parent_identity = parent_payload == baseline.output;

    std::vector<Interval> selected;
    for (int stratum = 0; stratum < kStrata; ++stratum) {
      std::array<int64_t, kCells + 1> pn{}, pe{}, pq{};
      for (int j = 0; j < kCells; ++j) {
        pn[j + 1] = pn[j] + cells[stratum][j].n;
        pe[j + 1] = pe[j] + cells[stratum][j].e;
        pq[j + 1] = pq[j] + cells[stratum][j].qbits;
      }
      std::array<int64_t, kCells + 1> dp{};
      std::array<int, kCells + 1> pred{};
      std::array<int, kCells + 1> take_lo{};
      take_lo.fill(-1);
      for (int t = 1; t <= kCells; ++t) {
        dp[t] = dp[t - 1];
        pred[t] = t - 1;
        for (int lo = 0; lo < t; ++lo) {
          const int64_t n = pn[t] - pn[lo];
          if (n == 0) continue;
          const int64_t e = pe[t] - pe[lo];
          const int64_t rank_bits =
              static_cast<int64_t>(std::ceil(Log2Choose(n, e)));
          const int64_t weight =
              pq[t] - pq[lo] -
              static_cast<int64_t>(kScale) *
                  (kDescriptorBits + rank_bits);
          const int64_t candidate = dp[lo] + weight;
          if (candidate > dp[t]) {
            dp[t] = candidate;
            pred[t] = lo;
            take_lo[t] = lo;
          }
        }
      }
      int t = kCells;
      std::vector<Interval> reversed;
      while (t > 0) {
        if (take_lo[t] < 0) {
          t = pred[t];
          continue;
        }
        const int lo = take_lo[t];
        const int64_t n = pn[t] - pn[lo];
        const int64_t e = pe[t] - pe[lo];
        const int64_t rank_bits =
            static_cast<int64_t>(std::ceil(Log2Choose(n, e)));
        reversed.push_back(
            {stratum, lo, t - 1, n, e, rank_bits,
             pq[t] - pq[lo] -
                 static_cast<int64_t>(kScale) *
                     (kDescriptorBits + rank_bits)});
        t = lo;
      }
      std::reverse(reversed.begin(), reversed.end());
      selected.insert(selected.end(), reversed.begin(), reversed.end());
    }

    std::array<std::array<int, kCells>, kStrata> selected_id{};
    for (auto& row : selected_id) row.fill(-1);
    for (size_t i = 0; i < selected.size(); ++i) {
      const auto& interval = selected[i];
      for (int cell = interval.lo; cell <= interval.hi; ++cell) {
        if (selected_id[interval.stratum][cell] >= 0)
          throw std::runtime_error("overlapping selected intervals");
        selected_id[interval.stratum][cell] = static_cast<int>(i);
      }
    }

    std::vector<std::vector<uint8_t>> error_streams(selected.size());
    std::vector<uint8_t> literal_truth;
    literal_truth.reserve(rows);
    RangeEncoder literal;
    for (int64_t row = 0; row < rows; ++row) {
      const int stratum = static_cast<int>(row & 7);
      const int cell = probabilities[row] >> 8;
      const int id = selected_id[stratum][cell];
      if (id >= 0) {
        const int modal = probabilities[row] >= 32768 ? 1 : 0;
        error_streams[id].push_back(
            static_cast<uint8_t>(truth[row] != modal));
      } else {
        literal_truth.push_back(truth[row]);
        literal.Update(probabilities[row], truth[row]);
      }
    }
    literal.Finish();

    int64_t total_rank_bits = 0;
    for (size_t i = 0; i < selected.size(); ++i) {
      const auto ones = static_cast<int64_t>(
          std::count(error_streams[i].begin(), error_streams[i].end(), 1));
      if (static_cast<int64_t>(error_streams[i].size()) != selected[i].n ||
          ones != selected[i].e) {
        throw std::runtime_error("selected stream count mismatch");
      }
      total_rank_bits += selected[i].rank_bits;
    }
    const int64_t side_bytes =
        kHeaderBytes +
        static_cast<int64_t>(selected.size()) * (kDescriptorBits / 8) +
        (total_rank_bits + 7) / 8;
    const int64_t candidate_bytes =
        static_cast<int64_t>(literal.output.size()) + side_bytes;
    const int64_t net =
        static_cast<int64_t>(baseline.output.size()) - candidate_bytes;

    std::vector<size_t> stream_index(selected.size(), 0);
    size_t literal_index = 0;
    bool roundtrip = true;
    for (int64_t row = 0; row < rows; ++row) {
      const int stratum = static_cast<int>(row & 7);
      const int cell = probabilities[row] >> 8;
      const int id = selected_id[stratum][cell];
      uint8_t decoded = 0;
      if (id >= 0) {
        if (stream_index[id] >= error_streams[id].size()) {
          roundtrip = false;
          break;
        }
        const int modal = probabilities[row] >= 32768 ? 1 : 0;
        decoded = static_cast<uint8_t>(
            modal ^ error_streams[id][stream_index[id]++]);
      } else {
        if (literal_index >= literal_truth.size()) {
          roundtrip = false;
          break;
        }
        decoded = literal_truth[literal_index++];
      }
      if (decoded != truth[row]) {
        roundtrip = false;
        break;
      }
    }
    if (literal_index != literal_truth.size()) roundtrip = false;
    for (size_t i = 0; i < selected.size(); ++i) {
      if (stream_index[i] != error_streams[i].size()) roundtrip = false;
    }

    const bool passes_gate = net >= 2000;
    std::ofstream out(argv[3]);
    if (!out) throw std::runtime_error("cannot write decision");
    out << std::fixed << std::setprecision(3);
    out << "{\n"
        << "  \"id\": \"paid_type_interval_v1\",\n"
        << "  \"status\": \"" << (passes_gate ? "promote" : "terminal_negative")
        << "\",\n"
        << "  \"score_credit_bytes\": 0,\n"
        << "  \"trace_rows\": " << rows << ",\n"
        << "  \"selected_intervals\": " << selected.size() << ",\n"
        << "  \"rank_bits\": " << total_rank_bits << ",\n"
        << "  \"baseline_payload_bytes\": " << baseline.output.size() << ",\n"
        << "  \"literal_payload_bytes\": " << literal.output.size() << ",\n"
        << "  \"side_bytes\": " << side_bytes << ",\n"
        << "  \"candidate_total_bytes\": " << candidate_bytes << ",\n"
        << "  \"net_saved_bytes\": " << net << ",\n"
        << "  \"net_bytes_per_million_raw\": " << net << ",\n"
        << "  \"target_gate_bytes_per_million\": 2000,\n"
        << "  \"parent_archive_identity\": "
        << (parent_identity ? "true" : "false") << ",\n"
        << "  \"exact_logical_roundtrip\": "
        << (roundtrip ? "true" : "false") << ",\n"
        << "  \"decision\": \""
        << (passes_gate ? "authorize_distant_paid_type_interval"
                        : "retire_paid_type_interval")
        << "\"\n"
        << "}\n";
    out.close();

    std::cout << "intervals=" << selected.size()
              << " rank_bits=" << total_rank_bits
              << " baseline=" << baseline.output.size()
              << " literal=" << literal.output.size()
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
