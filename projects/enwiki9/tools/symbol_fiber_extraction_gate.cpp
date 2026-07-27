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

struct RangeEncoder {
  uint32_t x1 = 0;
  uint32_t x2 = 0xffffffffu;
  std::vector<uint8_t> out;

  void Update(uint16_t p1, int bit) {
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

  void Finish() {
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      out.push_back(static_cast<uint8_t>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
    out.push_back(static_cast<uint8_t>(x2 >> 24));
  }
};

std::vector<uint8_t> read_all(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open " + path);
  return {std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>()};
}

long double log2_choose(uint64_t n, uint64_t k) {
  if (k == 0 || k == n) return 0;
  return (std::lgammal(static_cast<long double>(n) + 1) -
          std::lgammal(static_cast<long double>(k) + 1) -
          std::lgammal(static_cast<long double>(n - k) + 1)) /
         std::log(2.0L);
}

void write_json(const std::string& path, uint64_t rows, uint64_t nbytes,
                uint64_t baseline, uint64_t literal, uint64_t side,
                uint64_t selected, long double ideal_bits, int64_t net,
                bool parent_identity, bool roundtrip) {
  std::ofstream o(path);
  if (!o) throw std::runtime_error("cannot write " + path);
  long double bpm = static_cast<long double>(net) * 1000000.0L / 1000000.0L;
  o << std::fixed << std::setprecision(3);
  o << "{\n"
    << "  \"id\": \"symbol_fiber_extraction_v1\",\n"
    << "  \"status\": \"terminal_negative\",\n"
    << "  \"score_credit_bytes\": 0,\n"
    << "  \"trace_rows\": " << rows << ",\n"
    << "  \"wrt_bytes\": " << nbytes << ",\n"
    << "  \"selected_symbol_fibers\": " << selected << ",\n"
    << "  \"ideal_net_bits\": " << static_cast<double>(ideal_bits) << ",\n"
    << "  \"baseline_payload_bytes\": " << baseline << ",\n"
    << "  \"literal_payload_bytes\": " << literal << ",\n"
    << "  \"side_bytes\": " << side << ",\n"
    << "  \"candidate_total_bytes\": " << (literal + side) << ",\n"
    << "  \"net_saved_bytes\": " << net << ",\n"
    << "  \"net_bytes_per_million_raw\": " << static_cast<double>(bpm) << ",\n"
    << "  \"parent_archive_identity\": " << (parent_identity ? "true" : "false") << ",\n"
    << "  \"exact_wrt_roundtrip\": " << (roundtrip ? "true" : "false") << ",\n"
    << "  \"decision\": \"retire_symbol_fiber_extraction\",\n"
    << "  \"note\": \"Independent fixed-length full-symbol fibers cannot repay their positions and descriptions on the exact opening-1M parent trace.\"\n"
    << "}\n";
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: gate TRACE.fx2pt PARENT.archive DECISION.json\n";
    return 2;
  }
  try {
    const auto trace = read_all(argv[1]);
    const auto archive = read_all(argv[2]);
    constexpr char magic[] = "FX2PT01\n";
    if (trace.size() < 8 || std::memcmp(trace.data(), magic, 8) != 0 ||
        (trace.size() - 8) % 3 != 0) {
      throw std::runtime_error("invalid FX2PT trace");
    }
    if (archive.size() < 37) throw std::runtime_error("short parent archive");

    const uint64_t rows = (trace.size() - 8) / 3;
    if (rows % 8 != 0) throw std::runtime_error("trace is not byte aligned");
    const uint64_t n = rows / 8;
    std::vector<uint16_t> probabilities(rows);
    std::vector<uint8_t> bits(rows);
    std::vector<uint8_t> bytes(n, 0);
    std::array<uint64_t, 256> counts{};
    std::array<long double, 256> costs{};

    RangeEncoder parent;
    for (uint64_t i = 0; i < rows; ++i) {
      size_t off = 8 + 3 * i;
      uint16_t p = static_cast<uint16_t>(trace[off]) |
                   (static_cast<uint16_t>(trace[off + 1]) << 8);
      bool bit = trace[off + 2] != 0;
      probabilities[i] = p;
      bits[i] = static_cast<uint8_t>(bit);
      bytes[i / 8] = static_cast<uint8_t>((bytes[i / 8] << 1) | bit);
      long double probability =
          bit ? static_cast<long double>(p) / 65536.0L
              : static_cast<long double>(65536u - p) / 65536.0L;
      if (probability <= 0) throw std::runtime_error("zero truth probability");
      costs[bytes[i / 8]] += 0;  // assigned after each byte is complete
      parent.Update(p, bit);
    }
    parent.Finish();

    uint64_t wrt_bytes = archive.at(0) & 0x7fu;
    for (int i = 1; i < 5; ++i) wrt_bytes = (wrt_bytes << 8) | archive.at(i);
    const size_t header_bytes = wrt_bytes < 10000 ? 5 : 37;
    const std::vector<uint8_t> expected(archive.begin() + header_bytes, archive.end());
    bool parent_identity = parent.out == expected;

    // Recompute per-byte costs after byte values are known.
    for (uint64_t j = 0; j < n; ++j) {
      uint8_t value = bytes[j];
      ++counts[value];
      long double c = 0;
      for (int b = 0; b < 8; ++b) {
        uint64_t i = 8 * j + b;
        uint32_t p = probabilities[i];
        long double probability =
            bits[i] ? static_cast<long double>(p) / 65536.0L
                    : static_cast<long double>(65536u - p) / 65536.0L;
        c -= std::log2(probability);
      }
      costs[value] += c;
    }

    std::array<bool, 256> selected{};
    uint64_t selected_count = 0;
    long double mask_bits = 0;
    long double ideal_bits = -16.0L;  // two-byte global header
    for (int v = 0; v < 256; ++v) {
      if (counts[v] == 0) continue;
      long double rank_bits = std::ceil(log2_choose(n, counts[v]));
      long double price = 32.0L + rank_bits;
      if (costs[v] > price) {
        selected[v] = true;
        ++selected_count;
        mask_bits += rank_bits;
        ideal_bits += costs[v] - price;
      }
    }

    RangeEncoder literal;
    for (uint64_t j = 0; j < n; ++j) {
      if (selected[bytes[j]]) continue;
      for (int b = 0; b < 8; ++b) {
        uint64_t i = 8 * j + b;
        literal.Update(probabilities[i], bits[i]);
      }
    }
    literal.Finish();

    uint64_t side = 2 + 4 * selected_count +
                    static_cast<uint64_t>(std::ceil(mask_bits / 8.0L));
    int64_t net = static_cast<int64_t>(parent.out.size()) -
                  static_cast<int64_t>(literal.out.size() + side);

    std::vector<uint8_t> residual;
    residual.reserve(n);
    for (uint8_t v : bytes) {
      if (!selected[v]) residual.push_back(v);
    }
    std::vector<uint8_t> reconstructed;
    reconstructed.reserve(n);
    size_t ri = 0;
    for (uint8_t v : bytes) {
      if (selected[v]) {
        reconstructed.push_back(v);
      } else {
        if (ri >= residual.size()) throw std::runtime_error("residual underrun");
        reconstructed.push_back(residual[ri++]);
      }
    }
    bool roundtrip = reconstructed == bytes && ri == residual.size();

    write_json(argv[3], rows, n, parent.out.size(), literal.out.size(), side,
               selected_count, ideal_bits, net, parent_identity, roundtrip);
    std::cout << "selected=" << selected_count
              << " baseline=" << parent.out.size()
              << " literal=" << literal.out.size()
              << " side=" << side
              << " net=" << net
              << " parent_identity=" << parent_identity
              << " roundtrip=" << roundtrip << "\n";
    return (parent_identity && roundtrip) ? 0 : 1;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
