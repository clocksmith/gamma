#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr uint32_t TOTAL = 4096;
constexpr uint32_t HALF = 0x80000000u;
constexpr uint32_t FIRST_QUARTER = 0x40000000u;
constexpr uint32_t THIRD_QUARTER = 0xc0000000u;

struct Segment {
  uint64_t prompt_start;
  uint64_t end;
  uint64_t title_feature;
  uint64_t page_index;
};

struct ArithmeticCounter {
  uint32_t low = 0;
  uint32_t high = 0xffffffffu;
  uint64_t pending = 0;
  uint64_t output_bits = 0;

  void emit() {
    ++output_bits;
    output_bits += pending;
    pending = 0;
  }

  void encode(int bit, uint32_t p1) {
    p1 = std::max<uint32_t>(1, std::min<uint32_t>(TOTAL - 1, p1));
    uint64_t range = static_cast<uint64_t>(high) - low + 1;
    uint32_t cut = low + static_cast<uint32_t>((range * (TOTAL - p1)) / TOTAL);
    if (cut <= low) cut = low + 1;
    if (cut > high) cut = high;
    if (bit) {
      low = cut;
    } else {
      high = cut - 1;
    }
    for (;;) {
      if (high < HALF) {
        emit();
      } else if (low >= HALF) {
        emit();
        low -= HALF;
        high -= HALF;
      } else if (low >= FIRST_QUARTER && high < THIRD_QUARTER) {
        ++pending;
        low -= FIRST_QUARTER;
        high -= FIRST_QUARTER;
      } else {
        break;
      }
      low <<= 1;
      high = (high << 1) | 1u;
    }
  }

  uint64_t finish_bytes() {
    ++pending;
    emit();
    return (output_bits + 7) / 8;
  }
};

struct LabelModel {
  std::array<std::array<uint64_t, 2>, 4> counts{};

  LabelModel() {
    for (auto &row : counts) row = {1, 1};
  }

  uint32_t p1(int position) const {
    const auto &row = counts[position];
    return static_cast<uint32_t>((row[1] * TOTAL) / (row[0] + row[1]));
  }

  double cost_bits(int label) const {
    double result = 0.0;
    for (int position = 0; position < 4; ++position) {
      int bit = (label >> (3 - position)) & 1;
      const auto &row = counts[position];
      result -= std::log2(
          static_cast<double>(row[bit]) /
          static_cast<double>(row[0] + row[1]));
    }
    return result;
  }

  void encode_and_update(ArithmeticCounter &coder, int label) {
    for (int position = 0; position < 4; ++position) {
      int bit = (label >> (3 - position)) & 1;
      coder.encode(bit, p1(position));
      ++counts[position][bit];
    }
  }

  void update(int label) {
    for (int position = 0; position < 4; ++position) {
      int bit = (label >> (3 - position)) & 1;
      ++counts[position][bit];
    }
  }
};

template <typename T>
T read_scalar(std::ifstream &source) {
  T value{};
  source.read(reinterpret_cast<char *>(&value), sizeof(value));
  if (!source) throw std::runtime_error("short binary input");
  return value;
}

std::vector<uint8_t> read_bytes(const std::string &path) {
  std::ifstream source(path, std::ios::binary);
  if (!source) throw std::runtime_error("cannot open " + path);
  source.seekg(0, std::ios::end);
  auto size = source.tellg();
  source.seekg(0);
  std::vector<uint8_t> value(static_cast<size_t>(size));
  source.read(reinterpret_cast<char *>(value.data()), size);
  if (!source) throw std::runtime_error("cannot read " + path);
  return value;
}

std::vector<Segment> read_segments(const std::string &path) {
  std::ifstream source(path, std::ios::binary);
  if (!source) throw std::runtime_error("cannot open segment input");
  uint64_t count = read_scalar<uint64_t>(source);
  std::vector<Segment> rows;
  rows.reserve(count);
  for (uint64_t index = 0; index < count; ++index) {
    rows.push_back({
        read_scalar<uint64_t>(source),
        read_scalar<uint64_t>(source),
        read_scalar<uint64_t>(source),
        read_scalar<uint64_t>(source),
    });
  }
  return rows;
}

std::array<std::pair<double, double>, 16> curve_specs() {
  return {{
      {1.00, 0.00},
      {0.65, 0.00},
      {0.75, 0.00},
      {0.85, 0.00},
      {0.93, 0.00},
      {1.07, 0.00},
      {1.15, 0.00},
      {1.30, 0.00},
      {1.00, -0.50},
      {1.00, -0.25},
      {1.00, -0.125},
      {1.00, 0.125},
      {1.00, 0.25},
      {1.00, 0.50},
      {0.85, -0.25},
      {0.85, 0.25},
  }};
}

int bit_at(const std::vector<uint8_t> &stream, uint64_t row) {
  return (stream[row >> 3] >> (7 - (row & 7))) & 1;
}

uint32_t calibrated(
    const std::array<std::array<uint16_t, TOTAL>, 16> &tables,
    int curve,
    uint16_t base) {
  return tables[curve][base];
}

uint64_t qbits(int bit, uint32_t p1) {
  double probability =
      bit ? static_cast<double>(p1) / TOTAL
          : static_cast<double>(TOTAL - p1) / TOTAL;
  return static_cast<uint64_t>(-std::log2(probability) * 256.0 + 0.5);
}

int main_impl(int argc, char **argv) {
  if (argc != 6) {
    throw std::runtime_error(
        "usage: helper STORE HEADER_BYTES P1 SEGMENTS OUTPUT_JSON");
  }
  const std::string store_path = argv[1];
  const size_t header_bytes = std::stoull(argv[2]);
  const std::string p1_path = argv[3];
  const std::string segment_path = argv[4];
  const std::string output_path = argv[5];

  auto stored = read_bytes(store_path);
  if (stored.size() < header_bytes) throw std::runtime_error("invalid header size");
  std::vector<uint8_t> stream(stored.begin() + header_bytes, stored.end());
  auto trace = read_bytes(p1_path);
  if (trace.size() < 16) throw std::runtime_error("short P1 trace");
  const std::string magic(reinterpret_cast<char *>(trace.data()), 8);
  if (magic != std::string("FX2P1V1\0", 8) &&
      magic != std::string("CMX21P1\0", 8)) {
    throw std::runtime_error("invalid P1 trace magic");
  }
  uint64_t rows = 0;
  for (int index = 0; index < 8; ++index) {
    rows |= static_cast<uint64_t>(trace[8 + index]) << (8 * index);
  }
  if (rows != stream.size() * 8 ||
      trace.size() != 16 + 2 * rows) {
    throw std::runtime_error("P1 trace and WRT stream do not align");
  }
  auto p1_at = [&](uint64_t row) -> uint16_t {
    size_t offset = 16 + 2 * row;
    uint16_t value = trace[offset] | (static_cast<uint16_t>(trace[offset + 1]) << 8);
    if (value == 0 || value >= TOTAL) throw std::runtime_error("invalid P1");
    return value;
  };
  auto segments = read_segments(segment_path);
  for (size_t index = 0; index < segments.size(); ++index) {
    if (segments[index].prompt_start > segments[index].end ||
        segments[index].end > rows ||
        (index && segments[index - 1].end > segments[index].prompt_start)) {
      throw std::runtime_error("invalid or overlapping prompt segments");
    }
  }

  auto specs = curve_specs();
  std::array<std::array<uint16_t, TOTAL>, 16> tables{};
  for (int curve = 0; curve < 16; ++curve) {
    for (uint32_t p1 = 1; p1 < TOTAL; ++p1) {
      if (curve == 0) {
        tables[curve][p1] = p1;
        continue;
      }
      double probability = static_cast<double>(p1) / TOTAL;
      double logit = std::log(probability / (1.0 - probability));
      double mapped = 1.0 / (1.0 + std::exp(-(specs[curve].first * logit +
                                              specs[curve].second)));
      auto quantized = static_cast<int>(std::llround(mapped * TOTAL));
      tables[curve][p1] = static_cast<uint16_t>(
          std::max(1, std::min(static_cast<int>(TOTAL - 1), quantized)));
    }
  }

  std::vector<std::array<uint64_t, 16>> costs(segments.size());
  size_t segment_index = 0;
  for (uint64_t row = 0; row < rows; ++row) {
    while (segment_index < segments.size() && row >= segments[segment_index].end) {
      ++segment_index;
    }
    if (segment_index >= segments.size() ||
        row < segments[segment_index].prompt_start) {
      continue;
    }
    int bit = bit_at(stream, row);
    uint16_t base = p1_at(row);
    for (int curve = 0; curve < 16; ++curve) {
      costs[segment_index][curve] += qbits(bit, calibrated(tables, curve, base));
    }
  }

  std::vector<int> oracle(segments.size(), 0);
  LabelModel selection_labels;
  std::array<uint64_t, 16> histogram{};
  for (size_t page = 0; page < segments.size(); ++page) {
    double best = std::numeric_limits<double>::infinity();
    int selected = 0;
    for (int curve = 0; curve < 16; ++curve) {
      double candidate = costs[page][curve] / 256.0 +
                         selection_labels.cost_bits(curve);
      if (candidate < best) {
        best = candidate;
        selected = curve;
      }
    }
    oracle[page] = selected;
    ++histogram[selected];
    selection_labels.update(selected);
  }

  int global_curve = 0;
  uint64_t global_best = std::numeric_limits<uint64_t>::max();
  for (int curve = 0; curve < 16; ++curve) {
    uint64_t total = 0;
    for (size_t page = 0; page < segments.size(); ++page) {
      if (segments[page].page_index % 5 == 3) total += costs[page][curve];
    }
    if (total < global_best) {
      global_best = total;
      global_curve = curve;
    }
  }

  std::vector<int> shuffled = oracle;
  if (shuffled.size() > 1) {
    std::rotate(shuffled.begin(), shuffled.begin() + 1, shuffled.end());
  }
  std::vector<int> predicted(segments.size(), 0);
  std::map<uint64_t, std::array<uint64_t, 16>> feature_counts;
  std::array<uint64_t, 16> global_counts{};
  global_counts[0] = 1;
  for (size_t page = 0; page < segments.size(); ++page) {
    auto found = feature_counts.find(segments[page].title_feature);
    const auto &counts_for_prediction =
        found == feature_counts.end() ? global_counts : found->second;
    int selected = 0;
    for (int curve = 1; curve < 16; ++curve) {
      if (counts_for_prediction[curve] > counts_for_prediction[selected]) {
        selected = curve;
      }
    }
    predicted[page] = selected;
    ++feature_counts[segments[page].title_feature][oracle[page]];
    ++global_counts[oracle[page]];
  }

  ArithmeticCounter z0, z1, z16_gross, z16, zr, zp;
  LabelModel z16_labels, zr_labels;
  segment_index = 0;
  for (uint64_t row = 0; row < rows; ++row) {
    while (segment_index < segments.size() && row >= segments[segment_index].end) {
      ++segment_index;
    }
    bool body = segment_index < segments.size() &&
                row >= segments[segment_index].prompt_start &&
                row < segments[segment_index].end;
    if (body && row == segments[segment_index].prompt_start) {
      z16_labels.encode_and_update(z16, oracle[segment_index]);
      zr_labels.encode_and_update(zr, shuffled[segment_index]);
    }
    int bit = bit_at(stream, row);
    uint16_t base = p1_at(row);
    z0.encode(bit, base);
    z1.encode(bit, body ? calibrated(tables, global_curve, base) : base);
    z16_gross.encode(
        bit, body ? calibrated(tables, oracle[segment_index], base) : base);
    z16.encode(
        bit, body ? calibrated(tables, oracle[segment_index], base) : base);
    zr.encode(
        bit, body ? calibrated(tables, shuffled[segment_index], base) : base);
    zp.encode(
        bit, body ? calibrated(tables, predicted[segment_index], base) : base);
  }
  uint64_t z0_bytes = z0.finish_bytes();
  uint64_t z1_bytes = z1.finish_bytes();
  uint64_t z16_gross_bytes = z16_gross.finish_bytes();
  uint64_t z16_bytes = z16.finish_bytes();
  uint64_t zr_bytes = zr.finish_bytes();
  uint64_t zp_bytes = zp.finish_bytes();

  std::ofstream output(output_path);
  if (!output) throw std::runtime_error("cannot create output JSON");
  output << "{\n";
  output << "  \"schema\": \"endpoint_page_prompt_exact_helper_v1\",\n";
  output << "  \"rows\": " << rows << ",\n";
  output << "  \"wrt_stream_bytes\": " << stream.size() << ",\n";
  output << "  \"pages\": " << segments.size() << ",\n";
  output << "  \"global_curve\": " << global_curve << ",\n";
  output << "  \"exact_bytes\": {\n";
  output << "    \"Z0\": " << z0_bytes << ",\n";
  output << "    \"Z1\": " << z1_bytes << ",\n";
  output << "    \"Z16_GROSS\": " << z16_gross_bytes << ",\n";
  output << "    \"Z16\": " << z16_bytes << ",\n";
  output << "    \"ZR\": " << zr_bytes << ",\n";
  output << "    \"ZP\": " << zp_bytes << "\n";
  output << "  },\n";
  output << "  \"saved_bytes\": {\n";
  output << "    \"Z1\": " << static_cast<int64_t>(z0_bytes - z1_bytes) << ",\n";
  output << "    \"Z16_GROSS\": "
         << static_cast<int64_t>(z0_bytes - z16_gross_bytes) << ",\n";
  output << "    \"Z16\": " << static_cast<int64_t>(z0_bytes - z16_bytes) << ",\n";
  output << "    \"ZR\": " << static_cast<int64_t>(z0_bytes - zr_bytes) << ",\n";
  output << "    \"ZP\": " << static_cast<int64_t>(z0_bytes - zp_bytes) << "\n";
  output << "  },\n";
  output << "  \"label_histogram\": [";
  for (int curve = 0; curve < 16; ++curve) {
    if (curve) output << ", ";
    output << histogram[curve];
  }
  output << "],\n";
  output << "  \"curve_specs\": [";
  for (int curve = 0; curve < 16; ++curve) {
    if (curve) output << ", ";
    output << "{\"scale\":" << specs[curve].first
           << ",\"bias\":" << specs[curve].second << "}";
  }
  output << "]\n";
  output << "}\n";
  return 0;
}

}  // namespace

int main(int argc, char **argv) {
  try {
    return main_impl(argc, argv);
  } catch (const std::exception &error) {
    std::cerr << error.what() << "\n";
    return 1;
  }
}
