#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr uint32_t TOTAL = 1u << 16;
constexpr uint32_t MAX_CODE = 0xffffffffu;
constexpr size_t PAIR_HEADER_BYTES = 16;
constexpr size_t PAIR_ROW_BYTES = 4;
constexpr size_t P1_HEADER_BYTES = 16;
constexpr size_t STORE_HEADER_BYTES = 5;
constexpr size_t EXPERTS = 3;
constexpr size_t CONTEXTS = 8 * 128 * 8 * 4;
constexpr uint64_t MAP_HEADER_BYTES = 16;
constexpr uint64_t MAP_ENTRY_BYTES = 9;

struct Row {
  uint16_t compact;
  uint16_t endpoint;
  uint16_t hybrid;
  uint8_t bit;
};

struct RangeCounter {
  uint32_t x1 = 0;
  uint32_t x2 = MAX_CODE;
  uint64_t bytes = 0;

  void encode(uint8_t bit, uint32_t p1) {
    p1 = std::max<uint32_t>(1, std::min<uint32_t>(TOTAL - 1, p1));
    const uint32_t delta = x2 - x1;
    const uint64_t midpoint64 =
        static_cast<uint64_t>(x1) +
        static_cast<uint64_t>(delta >> 16) * p1 +
        ((static_cast<uint64_t>(delta & 0xffffu) * p1) >> 16);
    const uint32_t midpoint = static_cast<uint32_t>(midpoint64);
    if (bit) {
      x2 = midpoint;
    } else {
      x1 = midpoint + 1;
    }
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      ++bytes;
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
  }

  uint64_t finish() {
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      ++bytes;
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
    ++bytes;
    return bytes;
  }
};

uint16_t read_u16(const std::vector<uint8_t> &data, size_t offset) {
  return static_cast<uint16_t>(data.at(offset)) |
         static_cast<uint16_t>(data.at(offset + 1) << 8);
}

uint64_t read_u64(const std::vector<uint8_t> &data, size_t offset) {
  uint64_t value = 0;
  for (int i = 0; i < 8; ++i) {
    value |= static_cast<uint64_t>(data.at(offset + i)) << (8 * i);
  }
  return value;
}

std::vector<uint8_t> read_binary(const std::string &path) {
  std::ifstream source(path, std::ios::binary);
  if (!source) {
    throw std::runtime_error("cannot open input: " + path);
  }
  source.seekg(0, std::ios::end);
  const std::streamoff size = source.tellg();
  source.seekg(0, std::ios::beg);
  std::vector<uint8_t> data(static_cast<size_t>(size));
  if (!data.empty()) {
    source.read(reinterpret_cast<char *>(data.data()), size);
  }
  if (!source) {
    throw std::runtime_error("cannot read input: " + path);
  }
  return data;
}

std::vector<Row> read_pair_trace(const std::string &pair_path,
                                 const std::string &p1_path,
                                 const std::string &store_path) {
  const std::vector<uint8_t> pair = read_binary(pair_path);
  const std::vector<uint8_t> p1 = read_binary(p1_path);
  const std::vector<uint8_t> store = read_binary(store_path);
  if (pair.size() < PAIR_HEADER_BYTES ||
      std::memcmp(pair.data(), "CMXAUX1\0", 8) != 0) {
    throw std::runtime_error("invalid CMXAUX1 header");
  }
  const uint64_t count = read_u64(pair, 8);
  if (count == 0 || count % 8 != 0 ||
      pair.size() != PAIR_HEADER_BYTES + count * PAIR_ROW_BYTES) {
    throw std::runtime_error("invalid CMXAUX1 row count");
  }
  const bool p1_magic =
      p1.size() >= P1_HEADER_BYTES &&
      (std::memcmp(p1.data(), "CMX21P1\0", 8) == 0 ||
       std::memcmp(p1.data(), "FX2P1V1\0", 8) == 0);
  if (!p1_magic || read_u64(p1, 8) != count ||
      p1.size() != P1_HEADER_BYTES + count * 2) {
    throw std::runtime_error("invalid final-P1 binding");
  }
  if (store.size() != STORE_HEADER_BYTES + count / 8) {
    throw std::runtime_error("invalid WRT truth-stream binding");
  }
  std::vector<Row> rows;
  rows.reserve(static_cast<size_t>(count));
  for (uint64_t i = 0; i < count; ++i) {
    const size_t pair_offset =
        PAIR_HEADER_BYTES + static_cast<size_t>(i) * PAIR_ROW_BYTES;
    const size_t p1_offset = P1_HEADER_BYTES + static_cast<size_t>(i) * 2;
    const uint8_t byte = store.at(STORE_HEADER_BYTES + i / 8);
    const uint8_t bit = static_cast<uint8_t>((byte >> (7 - i % 8)) & 1);
    const Row row{read_u16(pair, pair_offset),
                  read_u16(pair, pair_offset + 2), read_u16(p1, p1_offset),
                  bit};
    if (row.compact == 0 || row.endpoint == 0 || row.hybrid == 0 ||
        row.bit > 1) {
      throw std::runtime_error("invalid probability or truth bit");
    }
    rows.push_back(row);
  }
  return rows;
}

uint16_t probability(const Row &row, size_t expert) {
  if (expert == 0) {
    return row.hybrid;
  }
  if (expert == 1) {
    return row.compact;
  }
  return row.endpoint;
}

uint32_t outcome(uint16_t p1, uint8_t bit) {
  return bit ? p1 : TOTAL - p1;
}

long double loss_bits(uint16_t p1, uint8_t bit) {
  return -std::log2(static_cast<long double>(outcome(p1, bit)) /
                    static_cast<long double>(TOTAL));
}

uint64_t baseline_bytes(const std::vector<Row> &rows, size_t begin,
                        size_t end) {
  RangeCounter coder;
  for (size_t i = begin; i < end; ++i) {
    coder.encode(rows[i].bit, rows[i].hybrid);
  }
  return coder.finish();
}

uint64_t oracle_bytes(const std::vector<Row> &rows,
                      const std::vector<size_t> *null_index = nullptr) {
  RangeCounter coder;
  for (size_t i = 0; i < rows.size(); ++i) {
    const Row &truth_row = rows[i];
    size_t best = 0;
    uint32_t best_value = outcome(truth_row.hybrid, truth_row.bit);
    const Row &expert_row =
        null_index == nullptr ? truth_row : rows[null_index->at(i)];
    for (size_t expert = 1; expert < EXPERTS; ++expert) {
      const uint16_t p1 = probability(expert_row, expert);
      const uint32_t candidate = outcome(p1, truth_row.bit);
      if (candidate > best_value) {
        best = expert;
        best_value = candidate;
      }
    }
    const uint16_t selected =
        best == 0 ? truth_row.hybrid : probability(expert_row, best);
    coder.encode(truth_row.bit, selected);
  }
  return coder.finish();
}

std::vector<size_t> circular_index(size_t rows, size_t shift_rows) {
  std::vector<size_t> result(rows);
  shift_rows %= rows;
  for (size_t i = 0; i < rows; ++i) {
    result[i] = (i + shift_rows) % rows;
  }
  return result;
}

int confidence_bin(uint16_t p1) {
  const int distance = std::abs(static_cast<int>(p1) - 32768);
  return std::min(7, distance * 8 / 32768);
}

std::vector<size_t> conditional_index(const std::vector<Row> &rows) {
  std::array<std::array<std::vector<size_t>, 8>, 8> groups;
  for (size_t i = 0; i < rows.size(); ++i) {
    groups[i % 8][confidence_bin(rows[i].hybrid)].push_back(i);
  }
  std::vector<size_t> result(rows.size());
  constexpr size_t ROTATION = 1009;
  for (auto &by_position : groups) {
    for (auto &group : by_position) {
      if (group.empty()) {
        continue;
      }
      const size_t shift = ROTATION % group.size();
      for (size_t i = 0; i < group.size(); ++i) {
        result[group[i]] = group[(i + shift) % group.size()];
      }
    }
  }
  return result;
}

size_t context_key(const Row &row, size_t bit_position, uint8_t prefix) {
  const int confidence = confidence_bin(row.hybrid);
  const int disagreement =
      (row.compact > row.hybrid ? 1 : 0) |
      (row.endpoint > row.hybrid ? 2 : 0);
  return ((((bit_position * 128) + prefix) * 8 +
           static_cast<size_t>(confidence)) *
              4 +
          static_cast<size_t>(disagreement));
}

std::vector<size_t> context_keys(const std::vector<Row> &rows) {
  std::vector<size_t> keys(rows.size());
  uint8_t prefix = 0;
  for (size_t i = 0; i < rows.size(); ++i) {
    const size_t bit_position = i % 8;
    keys[i] = context_key(rows[i], bit_position, prefix);
    prefix = static_cast<uint8_t>((prefix << 1) | rows[i].bit);
    if (bit_position == 7) {
      prefix = 0;
    }
  }
  return keys;
}

struct RouterResult {
  uint64_t baseline = 0;
  uint64_t candidate = 0;
  uint64_t active_entries = 0;
  uint64_t description_bytes = 0;
};

RouterResult static_router(const std::vector<Row> &rows) {
  const size_t train_end = rows.size() * 3 / 5;
  const size_t development_end = rows.size() * 4 / 5;
  const std::vector<size_t> keys = context_keys(rows);
  std::array<std::vector<long double>, EXPERTS> train_loss;
  for (auto &loss : train_loss) {
    loss.assign(CONTEXTS, 0.0L);
  }
  for (size_t i = 0; i < train_end; ++i) {
    for (size_t expert = 0; expert < EXPERTS; ++expert) {
      train_loss[expert][keys[i]] +=
          loss_bits(probability(rows[i], expert), rows[i].bit);
    }
  }
  std::vector<uint8_t> selected(CONTEXTS, 0);
  for (size_t key = 0; key < CONTEXTS; ++key) {
    for (size_t expert = 1; expert < EXPERTS; ++expert) {
      if (train_loss[expert][key] < train_loss[selected[key]][key]) {
        selected[key] = static_cast<uint8_t>(expert);
      }
    }
  }
  std::vector<long double> development_gain(CONTEXTS, 0.0L);
  for (size_t i = train_end; i < development_end; ++i) {
    const uint8_t expert = selected[keys[i]];
    development_gain[keys[i]] +=
        loss_bits(rows[i].hybrid, rows[i].bit) -
        loss_bits(probability(rows[i], expert), rows[i].bit);
  }
  uint64_t active = 0;
  for (size_t key = 0; key < CONTEXTS; ++key) {
    if (selected[key] != 0 && development_gain[key] > 72.0L) {
      ++active;
    } else {
      selected[key] = 0;
    }
  }
  RangeCounter base_coder;
  RangeCounter router_coder;
  for (size_t i = development_end; i < rows.size(); ++i) {
    base_coder.encode(rows[i].bit, rows[i].hybrid);
    router_coder.encode(rows[i].bit,
                        probability(rows[i], selected[keys[i]]));
  }
  return RouterResult{base_coder.finish(), router_coder.finish(), active,
                      MAP_HEADER_BYTES + active * MAP_ENTRY_BYTES};
}

struct PaidResult {
  size_t block_bytes = 0;
  uint64_t blocks = 0;
  uint64_t baseline = 0;
  uint64_t candidate = 0;
};

PaidResult paid_selector(const std::vector<Row> &rows, size_t block_bytes,
                         uint64_t full_baseline) {
  const size_t block_rows = block_bytes * 8;
  RangeCounter candidate;
  uint64_t blocks = 0;
  for (size_t begin = 0; begin < rows.size(); begin += block_rows) {
    const size_t end = std::min(rows.size(), begin + block_rows);
    std::array<long double, EXPERTS> losses{};
    for (size_t i = begin; i < end; ++i) {
      for (size_t expert = 0; expert < EXPERTS; ++expert) {
        losses[expert] +=
            loss_bits(probability(rows[i], expert), rows[i].bit);
      }
    }
    size_t selected = 0;
    for (size_t expert = 1; expert < EXPERTS; ++expert) {
      if (losses[expert] < losses[selected]) {
        selected = expert;
      }
    }
    candidate.encode(static_cast<uint8_t>((selected >> 1) & 1), 32768);
    candidate.encode(static_cast<uint8_t>(selected & 1), 32768);
    for (size_t i = begin; i < end; ++i) {
      candidate.encode(rows[i].bit, probability(rows[i], selected));
    }
    ++blocks;
  }
  return PaidResult{block_bytes, blocks, full_baseline, candidate.finish()};
}

int64_t saved(uint64_t baseline, uint64_t candidate) {
  return static_cast<int64_t>(baseline) - static_cast<int64_t>(candidate);
}

void print_paid(const PaidResult &result) {
  std::cout << "{\"block_bytes\":" << result.block_bytes
            << ",\"blocks\":" << result.blocks
            << ",\"baseline_bytes\":" << result.baseline
            << ",\"candidate_bytes\":" << result.candidate
            << ",\"saved_bytes\":"
            << saved(result.baseline, result.candidate) << '}';
}

} // namespace

int main(int argc, char **argv) {
  try {
    if (argc != 6) {
      throw std::runtime_error(
          "usage: mixregret PAIR_TRACE FINAL_P1 WRT_STORE EXPECTED_PAYLOAD "
          "RAW_SCOPE");
    }
    const std::vector<Row> rows = read_pair_trace(argv[1], argv[2], argv[3]);
    const uint64_t expected_payload = std::stoull(argv[4]);
    const uint64_t raw_scope = std::stoull(argv[5]);
    const uint64_t baseline = baseline_bytes(rows, 0, rows.size());
    const uint64_t real_u0 = oracle_bytes(rows);

    const std::array<size_t, 3> circular_shifts = {
        1024 * 8, 17 * 1024 * 8, 8191 * 8};
    std::array<uint64_t, 4> null_bytes{};
    for (size_t i = 0; i < circular_shifts.size(); ++i) {
      const std::vector<size_t> index =
          circular_index(rows.size(), circular_shifts[i]);
      null_bytes[i] = oracle_bytes(rows, &index);
    }
    const std::vector<size_t> matched_index = conditional_index(rows);
    null_bytes[3] = oracle_bytes(rows, &matched_index);

    const RouterResult router = static_router(rows);
    const std::array<size_t, 3> block_sizes = {1024, 4096, 16384};
    std::array<PaidResult, 3> paid{};
    for (size_t i = 0; i < block_sizes.size(); ++i) {
      paid[i] = paid_selector(rows, block_sizes[i], baseline);
    }

    int64_t best_null_saved = std::numeric_limits<int64_t>::min();
    for (uint64_t candidate : null_bytes) {
      best_null_saved =
          std::max(best_null_saved, saved(baseline, candidate));
    }
    const int64_t u0_saved = saved(baseline, real_u0);
    const int64_t null_adjusted = u0_saved - best_null_saved;
    const int64_t router_gross = saved(router.baseline, router.candidate);
    const int64_t router_net =
        router_gross - static_cast<int64_t>(router.description_bytes);
    const uint64_t holdout_raw = raw_scope / 5;
    const long double router_net_bpm =
        static_cast<long double>(router_net) * 1000000.0L /
        static_cast<long double>(holdout_raw);
    int64_t best_paid = std::numeric_limits<int64_t>::min();
    for (const PaidResult &result : paid) {
      best_paid = std::max(best_paid, saved(result.baseline, result.candidate));
    }
    const bool gate_valid = baseline == expected_payload;
    const bool authorize =
        gate_valid && u0_saved >= 6000 && null_adjusted >= 3000 &&
        router_net_bpm >= 3000.0L && best_paid >= 2500;

    std::cout << '{';
    std::cout << "\"schema\":\"mixregret_pair_closure_v1\",";
    std::cout << "\"evidence_tier\":\"causal_shadow\",";
    std::cout << "\"rows\":" << rows.size() << ',';
    std::cout << "\"wrt_bytes\":" << rows.size() / 8 << ',';
    std::cout << "\"raw_scope_bytes\":" << raw_scope << ',';
    std::cout << "\"baseline_payload_bytes\":" << baseline << ',';
    std::cout << "\"expected_baseline_payload_bytes\":" << expected_payload
              << ',';
    std::cout << "\"baseline_identity\":" << (gate_valid ? "true" : "false")
              << ',';
    std::cout << "\"u0_bytes\":" << real_u0 << ',';
    std::cout << "\"u0_saved_bytes\":" << u0_saved << ',';
    std::cout << "\"null_bytes\":[" << null_bytes[0] << ',' << null_bytes[1]
              << ',' << null_bytes[2] << ',' << null_bytes[3] << "],";
    std::cout << "\"best_null_saved_bytes\":" << best_null_saved << ',';
    std::cout << "\"null_adjusted_u0_saved_bytes\":" << null_adjusted << ',';
    std::cout << "\"r1\":{\"holdout_baseline_bytes\":" << router.baseline
              << ",\"holdout_candidate_bytes\":" << router.candidate
              << ",\"gross_saved_bytes\":" << router_gross
              << ",\"active_entries\":" << router.active_entries
              << ",\"description_bytes\":" << router.description_bytes
              << ",\"net_saved_bytes\":" << router_net
              << ",\"net_saved_bytes_per_million\":"
              << static_cast<double>(router_net_bpm) << "},";
    std::cout << "\"paid\":[";
    for (size_t i = 0; i < paid.size(); ++i) {
      if (i != 0) {
        std::cout << ',';
      }
      print_paid(paid[i]);
    }
    std::cout << "],";
    std::cout << "\"gate_valid\":" << (gate_valid ? "true" : "false") << ',';
    std::cout << "\"authorize_full_component_trace\":"
              << (authorize ? "true" : "false") << ',';
    std::cout << "\"decision\":\""
              << (authorize ? "authorize_full_component_trace"
                            : "close_pair_routing_neighborhood")
              << "\"";
    std::cout << "}\n";
    return gate_valid ? 0 : 2;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
