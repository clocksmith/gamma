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

constexpr uint32_t TOTAL = 1u << 16;
constexpr uint32_t MAX_CODE = 0xffffffffu;

struct Segment {
  uint64_t prompt_start;
  uint64_t end;
  uint64_t title_feature;
  uint64_t page_index;
};

struct RangeCounter {
  uint32_t x1 = 0;
  uint32_t x2 = MAX_CODE;
  uint64_t output_bytes = 0;

  void encode(int bit, uint32_t p1) {
    p1 = std::max<uint32_t>(1, std::min<uint32_t>(TOTAL - 1, p1));
    uint32_t delta = x2 - x1;
    uint64_t midpoint64 =
        static_cast<uint64_t>(x1) +
        static_cast<uint64_t>(delta >> 16) * p1 +
        ((static_cast<uint64_t>(delta & 0xffffu) * p1) >> 16);
    uint32_t midpoint = static_cast<uint32_t>(midpoint64);
    if (bit) {
      x2 = midpoint;
    } else {
      x1 = midpoint + 1;
    }
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      ++output_bytes;
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
  }

  uint64_t finish_bytes() {
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      ++output_bytes;
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
    ++output_bytes;
    return output_bytes;
  }
};

struct LabelModel {
  std::vector<std::array<uint64_t, 2>> counts;

  explicit LabelModel(int bits) : counts(static_cast<size_t>(bits), {1, 1}) {}

  uint32_t p1(int position) const {
    const auto &row = counts.at(static_cast<size_t>(position));
    return static_cast<uint32_t>((row[1] * TOTAL) / (row[0] + row[1]));
  }

  double cost_bits(int label) const {
    double result = 0.0;
    int bits = static_cast<int>(counts.size());
    for (int position = 0; position < bits; ++position) {
      int bit = (label >> (bits - 1 - position)) & 1;
      const auto &row = counts[static_cast<size_t>(position)];
      result -= std::log2(
          static_cast<double>(row[bit]) /
          static_cast<double>(row[0] + row[1]));
    }
    return result;
  }

  void encode_and_update(RangeCounter &coder, int label) {
    int bits = static_cast<int>(counts.size());
    for (int position = 0; position < bits; ++position) {
      int bit = (label >> (bits - 1 - position)) & 1;
      coder.encode(bit, p1(position));
      ++counts[static_cast<size_t>(position)][bit];
    }
  }

  void update(int label) {
    int bits = static_cast<int>(counts.size());
    for (int position = 0; position < bits; ++position) {
      int bit = (label >> (bits - 1 - position)) & 1;
      ++counts[static_cast<size_t>(position)][bit];
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

struct P1Trace {
  std::vector<uint8_t> bytes;
  uint64_t rows = 0;

  uint16_t at(uint64_t row) const {
    size_t offset = 16 + 2 * static_cast<size_t>(row);
    uint16_t value =
        bytes[offset] | (static_cast<uint16_t>(bytes[offset + 1]) << 8);
    if (value == 0) throw std::runtime_error("invalid zero P1");
    return value;
  }
};

P1Trace read_trace(const std::string &path, uint64_t expected_rows) {
  P1Trace trace{read_bytes(path), 0};
  if (trace.bytes.size() < 16) throw std::runtime_error("short P1 trace");
  const std::string magic(reinterpret_cast<char *>(trace.bytes.data()), 8);
  if (magic != std::string("FX2P1V1\0", 8) &&
      magic != std::string("CMX21P1\0", 8)) {
    throw std::runtime_error("invalid P1 trace magic");
  }
  for (int index = 0; index < 8; ++index) {
    trace.rows |= static_cast<uint64_t>(trace.bytes[8 + index]) << (8 * index);
  }
  if (trace.rows != expected_rows ||
      trace.bytes.size() != 16 + 2 * static_cast<size_t>(trace.rows)) {
    throw std::runtime_error("P1 trace does not align with WRT stream");
  }
  return trace;
}

int bit_at(const std::vector<uint8_t> &stream, uint64_t row) {
  return (stream[row >> 3] >> (7 - (row & 7))) & 1;
}

uint64_t qbits(int bit, uint32_t p1) {
  double probability =
      bit ? static_cast<double>(p1) / TOTAL
          : static_cast<double>(TOTAL - p1) / TOTAL;
  return static_cast<uint64_t>(-std::log2(probability) * 256.0 + 0.5);
}

int minimum_cost_expert(
    const std::vector<uint64_t> &costs,
    const LabelModel *labels) {
  double best = std::numeric_limits<double>::infinity();
  int selected = 0;
  for (size_t expert = 0; expert < costs.size(); ++expert) {
    double candidate = costs[expert] / 256.0;
    if (labels != nullptr) {
      candidate += labels->cost_bits(static_cast<int>(expert));
    }
    if (candidate < best) {
      best = candidate;
      selected = static_cast<int>(expert);
    }
  }
  return selected;
}

void write_array(std::ofstream &output, const std::vector<uint64_t> &values) {
  output << "[";
  for (size_t index = 0; index < values.size(); ++index) {
    if (index) output << ", ";
    output << values[index];
  }
  output << "]";
}

int main_impl(int argc, char **argv) {
  if (argc < 8) {
    throw std::runtime_error(
        "usage: helper STORE HEADER_BYTES SEGMENTS OUTPUT_JSON "
        "BASELINE_INDEX P1...");
  }
  const std::string store_path = argv[1];
  const size_t header_bytes = std::stoull(argv[2]);
  const std::string segment_path = argv[3];
  const std::string output_path = argv[4];
  const int baseline_index = std::stoi(argv[5]);
  const int expert_count = argc - 6;
  if (expert_count < 2 || expert_count > 16 ||
      baseline_index < 0 || baseline_index >= expert_count) {
    throw std::runtime_error("invalid expert family");
  }
  int label_bits = 0;
  while ((1 << label_bits) < expert_count) ++label_bits;

  auto stored = read_bytes(store_path);
  if (stored.size() < header_bytes) throw std::runtime_error("invalid header size");
  std::vector<uint8_t> stream(stored.begin() + header_bytes, stored.end());
  const uint64_t rows = static_cast<uint64_t>(stream.size()) * 8;
  std::vector<P1Trace> traces;
  traces.reserve(static_cast<size_t>(expert_count));
  for (int expert = 0; expert < expert_count; ++expert) {
    traces.push_back(read_trace(argv[6 + expert], rows));
  }

  auto segments = read_segments(segment_path);
  for (size_t index = 0; index < segments.size(); ++index) {
    if (segments[index].prompt_start > segments[index].end ||
        segments[index].end > rows ||
        (index && segments[index - 1].end > segments[index].prompt_start)) {
      throw std::runtime_error("invalid or overlapping prompt segments");
    }
  }

  std::vector<std::vector<uint64_t>> costs(
      segments.size(), std::vector<uint64_t>(static_cast<size_t>(expert_count)));
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
    for (int expert = 0; expert < expert_count; ++expert) {
      costs[segment_index][static_cast<size_t>(expert)] +=
          qbits(bit, traces[static_cast<size_t>(expert)].at(row));
    }
  }

  std::vector<int> gross(segments.size(), baseline_index);
  std::vector<int> paid(segments.size(), baseline_index);
  std::vector<uint64_t> gross_histogram(static_cast<size_t>(expert_count));
  std::vector<uint64_t> paid_histogram(static_cast<size_t>(expert_count));
  LabelModel paid_selection(label_bits);
  for (size_t page = 0; page < segments.size(); ++page) {
    gross[page] = minimum_cost_expert(costs[page], nullptr);
    paid[page] = minimum_cost_expert(costs[page], &paid_selection);
    ++gross_histogram[static_cast<size_t>(gross[page])];
    ++paid_histogram[static_cast<size_t>(paid[page])];
    paid_selection.update(paid[page]);
  }

  int global_expert = baseline_index;
  uint64_t global_best = std::numeric_limits<uint64_t>::max();
  for (int expert = 0; expert < expert_count; ++expert) {
    uint64_t total = 0;
    for (size_t page = 0; page < segments.size(); ++page) {
      if (segments[page].page_index % 5 == 3) {
        total += costs[page][static_cast<size_t>(expert)];
      }
    }
    if (total < global_best) {
      global_best = total;
      global_expert = expert;
    }
  }

  std::vector<int> shuffled = paid;
  if (shuffled.size() > 1) {
    std::rotate(shuffled.begin(), shuffled.begin() + 1, shuffled.end());
  }

  std::vector<int> predicted(segments.size(), baseline_index);
  std::map<uint64_t, std::vector<uint64_t>> feature_counts;
  std::vector<uint64_t> global_counts(static_cast<size_t>(expert_count));
  global_counts[static_cast<size_t>(baseline_index)] = 1;
  for (size_t page = 0; page < segments.size(); ++page) {
    auto found = feature_counts.find(segments[page].title_feature);
    const auto &available =
        found == feature_counts.end() ? global_counts : found->second;
    predicted[page] = static_cast<int>(
        std::distance(available.begin(),
                      std::max_element(available.begin(), available.end())));
    auto &feature = feature_counts[segments[page].title_feature];
    if (feature.empty()) feature.resize(static_cast<size_t>(expert_count));
    ++feature[static_cast<size_t>(paid[page])];
    ++global_counts[static_cast<size_t>(paid[page])];
  }

  RangeCounter base_coder;
  RangeCounter global_coder;
  RangeCounter gross_coder;
  RangeCounter fixed_coder;
  RangeCounter paid_coder;
  RangeCounter shuffled_coder;
  RangeCounter predicted_coder;
  LabelModel paid_labels(label_bits);
  LabelModel shuffled_labels(label_bits);
  segment_index = 0;
  for (uint64_t row = 0; row < rows; ++row) {
    while (segment_index < segments.size() && row >= segments[segment_index].end) {
      ++segment_index;
    }
    bool body = segment_index < segments.size() &&
                row >= segments[segment_index].prompt_start &&
                row < segments[segment_index].end;
    if (body && row == segments[segment_index].prompt_start) {
      int fixed_label = gross[segment_index];
      for (int position = 0; position < label_bits; ++position) {
        int bit = (fixed_label >> (label_bits - 1 - position)) & 1;
        fixed_coder.encode(bit, TOTAL / 2);
      }
      paid_labels.encode_and_update(paid_coder, paid[segment_index]);
      shuffled_labels.encode_and_update(
          shuffled_coder, shuffled[segment_index]);
    }
    int bit = bit_at(stream, row);
    int selected_gross = body ? gross[segment_index] : baseline_index;
    int selected_paid = body ? paid[segment_index] : baseline_index;
    int selected_shuffled = body ? shuffled[segment_index] : baseline_index;
    int selected_predicted = body ? predicted[segment_index] : baseline_index;
    uint16_t baseline_p1 = traces[static_cast<size_t>(baseline_index)].at(row);
    base_coder.encode(bit, baseline_p1);
    global_coder.encode(
        bit, body ? traces[static_cast<size_t>(global_expert)].at(row)
                  : baseline_p1);
    gross_coder.encode(
        bit, body ? traces[static_cast<size_t>(selected_gross)].at(row)
                  : baseline_p1);
    fixed_coder.encode(
        bit, body ? traces[static_cast<size_t>(selected_gross)].at(row)
                  : baseline_p1);
    paid_coder.encode(
        bit, body ? traces[static_cast<size_t>(selected_paid)].at(row)
                  : baseline_p1);
    shuffled_coder.encode(
        bit, body ? traces[static_cast<size_t>(selected_shuffled)].at(row)
                  : baseline_p1);
    predicted_coder.encode(
        bit, body ? traces[static_cast<size_t>(selected_predicted)].at(row)
                  : baseline_p1);
  }

  uint64_t base_bytes = base_coder.finish_bytes();
  uint64_t global_bytes = global_coder.finish_bytes();
  uint64_t gross_bytes = gross_coder.finish_bytes();
  uint64_t fixed_bytes = fixed_coder.finish_bytes();
  uint64_t paid_bytes = paid_coder.finish_bytes();
  uint64_t shuffled_bytes = shuffled_coder.finish_bytes();
  uint64_t predicted_bytes = predicted_coder.finish_bytes();

  std::array<int64_t, 3> gross_qbit_saved{};
  std::array<int64_t, 3> paid_qbit_saved{};
  for (size_t page = 0; page < segments.size(); ++page) {
    int split = segments[page].page_index % 5 == 3
                    ? 1
                    : (segments[page].page_index % 5 == 4 ? 2 : 0);
    gross_qbit_saved[static_cast<size_t>(split)] +=
        static_cast<int64_t>(costs[page][static_cast<size_t>(baseline_index)]) -
        static_cast<int64_t>(costs[page][static_cast<size_t>(gross[page])]);
    paid_qbit_saved[static_cast<size_t>(split)] +=
        static_cast<int64_t>(costs[page][static_cast<size_t>(baseline_index)]) -
        static_cast<int64_t>(costs[page][static_cast<size_t>(paid[page])]);
  }

  std::ofstream output(output_path);
  if (!output) throw std::runtime_error("cannot create output JSON");
  output << "{\n";
  output << "  \"schema\": \"seal2_route_a_multi_endpoint_helper_v1\",\n";
  output << "  \"probability_total\": " << TOTAL << ",\n";
  output << "  \"range_coder\": \"endpoint_uint16_byte_range_v1\",\n";
  output << "  \"rows\": " << rows << ",\n";
  output << "  \"wrt_stream_bytes\": " << stream.size() << ",\n";
  output << "  \"pages\": " << segments.size() << ",\n";
  output << "  \"expert_count\": " << expert_count << ",\n";
  output << "  \"baseline_index\": " << baseline_index << ",\n";
  output << "  \"global_expert\": " << global_expert << ",\n";
  output << "  \"label_bits\": " << label_bits << ",\n";
  output << "  \"exact_bytes\": {\n";
  output << "    \"BASE\": " << base_bytes << ",\n";
  output << "    \"GLOBAL\": " << global_bytes << ",\n";
  output << "    \"ORACLE_GROSS\": " << gross_bytes << ",\n";
  output << "    \"ORACLE_FIXED_LABEL\": " << fixed_bytes << ",\n";
  output << "    \"ORACLE_PAID\": " << paid_bytes << ",\n";
  output << "    \"SHUFFLED\": " << shuffled_bytes << ",\n";
  output << "    \"TITLE_PREDICTED\": " << predicted_bytes << "\n";
  output << "  },\n";
  output << "  \"saved_bytes\": {\n";
  output << "    \"GLOBAL\": " << static_cast<int64_t>(base_bytes - global_bytes) << ",\n";
  output << "    \"ORACLE_GROSS\": " << static_cast<int64_t>(base_bytes - gross_bytes) << ",\n";
  output << "    \"ORACLE_FIXED_LABEL\": " << static_cast<int64_t>(base_bytes - fixed_bytes) << ",\n";
  output << "    \"ORACLE_PAID\": " << static_cast<int64_t>(base_bytes - paid_bytes) << ",\n";
  output << "    \"SHUFFLED\": " << static_cast<int64_t>(base_bytes - shuffled_bytes) << ",\n";
  output << "    \"TITLE_PREDICTED\": " << static_cast<int64_t>(base_bytes - predicted_bytes) << "\n";
  output << "  },\n";
  output << "  \"gross_histogram\": ";
  write_array(output, gross_histogram);
  output << ",\n";
  output << "  \"paid_histogram\": ";
  write_array(output, paid_histogram);
  output << ",\n";
  output << "  \"split_qbit_saved\": {\n";
  output << "    \"gross\": ["
         << gross_qbit_saved[0] << ", " << gross_qbit_saved[1] << ", "
         << gross_qbit_saved[2] << "],\n";
  output << "    \"paid_payload_only\": ["
         << paid_qbit_saved[0] << ", " << paid_qbit_saved[1] << ", "
         << paid_qbit_saved[2] << "]\n";
  output << "  },\n";
  output << "  \"split_order\": [\"train\", \"development\", \"holdout\"]\n";
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
