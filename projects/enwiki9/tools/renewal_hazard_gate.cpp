#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

constexpr int kBuckets = 13;
constexpr int kTotal = 1 << 16;
constexpr int kLambdaScale = 1 << 12;
constexpr uint32_t kMaxCode = 0xffffffffU;
constexpr double kTargetBpm = 2000.0;
constexpr char kMagic[] = "FX2PT01\n";

struct RangeEncoder {
  uint32_t x1 = 0;
  uint32_t x2 = kMaxCode;
  std::vector<unsigned char> output;

  void Update(uint16_t p1, int bit) {
    const uint32_t delta = x2 - x1;
    const uint32_t midpoint =
        x1 + (delta >> 16) * p1 + ((delta & 0xffffU) * p1 >> 16);
    if (bit) {
      x2 = midpoint;
    } else {
      x1 = midpoint + 1;
    }
    while (((x1 ^ x2) & 0xff000000U) == 0) {
      output.push_back(static_cast<unsigned char>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
  }

  void Finish() {
    while (((x1 ^ x2) & 0xff000000U) == 0) {
      output.push_back(static_cast<unsigned char>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
    output.push_back(static_cast<unsigned char>(x2 >> 24));
  }
};

struct Row {
  uint16_t p1;
  int bit;
};

Row ReadRow(std::ifstream& input) {
  unsigned char bytes[3];
  input.read(reinterpret_cast<char*>(bytes), 3);
  if (!input) throw std::runtime_error("truncated row");
  const uint16_t p1 =
      static_cast<uint16_t>(bytes[0] | (static_cast<uint16_t>(bytes[1]) << 8));
  if (p1 == 0 || bytes[2] > 1) throw std::runtime_error("invalid row");
  return {p1, static_cast<int>(bytes[2])};
}

int Bucket(uint32_t age) {
  if (age <= 3) return static_cast<int>(age);
  if (age >= 1024) return 12;
  int bucket = 4;
  uint32_t upper = 7;
  while (age > upper) {
    ++bucket;
    upper = (upper << 1) | 1U;
  }
  return bucket;
}

uint16_t ErrorProbability(uint16_t p1) {
  return p1 >= kTotal / 2 ? static_cast<uint16_t>(kTotal - p1) : p1;
}

uint16_t CorrectError(uint16_t error, int lambda_q12) {
  const uint64_t numerator = static_cast<uint64_t>(lambda_q12) * error;
  const uint64_t denominator =
      static_cast<uint64_t>(kLambdaScale) * (kTotal - error) + numerator;
  uint64_t q =
      (static_cast<uint64_t>(kTotal) * numerator + denominator / 2) / denominator;
  q = std::max<uint64_t>(1, std::min<uint64_t>(kTotal - 1, q));
  return static_cast<uint16_t>(q);
}

double Loss(const std::vector<std::pair<uint16_t, unsigned char>>& records,
            int lambda_q12) {
  double loss = 0.0;
  for (const auto& record : records) {
    const double q =
        static_cast<double>(CorrectError(record.first, lambda_q12)) / kTotal;
    loss -= record.second ? std::log2(q) : std::log2(1.0 - q);
  }
  return loss;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: renewal_hazard_gate TRACE RAW_BYTES OUTPUT\n";
    return 2;
  }
  const std::string trace_path = argv[1];
  const uint64_t raw_bytes = std::stoull(argv[2]);
  const std::string output_path = argv[3];

  std::ifstream input(trace_path, std::ios::binary | std::ios::ate);
  if (!input) throw std::runtime_error("cannot open trace");
  const uint64_t size = static_cast<uint64_t>(input.tellg());
  if (size < 8 || (size - 8) % 3 != 0) throw std::runtime_error("bad size");
  const uint64_t rows = (size - 8) / 3;
  uint64_t split = rows / 2;
  split -= split % 8;
  input.seekg(0);
  char magic[8];
  input.read(magic, 8);
  if (!input || !std::equal(magic, magic + 8, kMagic)) {
    throw std::runtime_error("bad magic");
  }

  std::array<std::vector<std::pair<uint16_t, unsigned char>>, kBuckets> groups;
  uint32_t age = 1024;
  for (uint64_t index = 0; index < split; ++index) {
    const Row row = ReadRow(input);
    const bool modal_one = row.p1 >= kTotal / 2;
    const unsigned char residual = static_cast<unsigned char>(row.bit ^ modal_one);
    groups[Bucket(age)].push_back({ErrorProbability(row.p1), residual});
    age = residual ? 0 : std::min<uint32_t>(1024, age + 1);
  }

  std::array<int, kBuckets> multipliers{};
  for (int bucket = 0; bucket < kBuckets; ++bucket) {
    const auto& records = groups[bucket];
    if (records.empty()) {
      multipliers[bucket] = kLambdaScale;
      continue;
    }
    double theta = 0.0;
    for (int iteration = 0; iteration < 30; ++iteration) {
      double gradient = 0.0;
      double hessian = 0.0;
      for (const auto& record : records) {
        const double e = static_cast<double>(record.first) / kTotal;
        const double z = std::log(e / (1.0 - e)) + theta;
        const double q = 1.0 / (1.0 + std::exp(-z));
        gradient += q - record.second;
        hessian += q * (1.0 - q);
      }
      if (hessian == 0.0) break;
      const double step = gradient / hessian;
      theta = std::max(-8.0, std::min(2.7, theta - step));
      if (std::abs(step) < 1e-12) break;
    }
    const double continuous = std::exp(theta) * kLambdaScale;
    int center = static_cast<int>(std::llround(continuous));
    center = std::max(1, std::min(65535, center));
    int best = center;
    double best_loss = std::numeric_limits<double>::infinity();
    for (int candidate = std::max(1, center - 3);
         candidate <= std::min(65535, center + 3); ++candidate) {
      const double candidate_loss = Loss(records, candidate);
      if (candidate_loss < best_loss ||
          (candidate_loss == best_loss && candidate < best)) {
        best_loss = candidate_loss;
        best = candidate;
      }
    }
    multipliers[bucket] = best;
  }

  RangeEncoder baseline;
  RangeEncoder candidate;
  const uint64_t holdout_rows = rows - split;
  for (uint64_t index = split; index < rows; ++index) {
    const Row row = ReadRow(input);
    const bool modal_one = row.p1 >= kTotal / 2;
    const uint16_t adjusted_error =
        CorrectError(ErrorProbability(row.p1), multipliers[Bucket(age)]);
    const uint16_t adjusted_p1 = modal_one
        ? static_cast<uint16_t>(kTotal - adjusted_error)
        : adjusted_error;
    baseline.Update(row.p1, row.bit);
    candidate.Update(adjusted_p1, row.bit);
    const int residual = row.bit ^ modal_one;
    age = residual ? 0 : std::min<uint32_t>(1024, age + 1);
  }
  baseline.Finish();
  candidate.Finish();

  constexpr int model_bytes = 2 * kBuckets;
  const int64_t gross =
      static_cast<int64_t>(baseline.output.size()) -
      static_cast<int64_t>(candidate.output.size());
  const int64_t net = gross - model_bytes;
  const double holdout_raw =
      static_cast<double>(raw_bytes) * holdout_rows / rows;
  const double net_bpm = net * 1000000.0 / holdout_raw;
  const bool pass = net_bpm >= kTargetBpm;

  std::ofstream output(output_path);
  if (!output) throw std::runtime_error("cannot create output");
  output << "{\n";
  output << "  \"schema\": \"renewal_hazard_gate_v1\",\n";
  output << "  \"candidate\": \"renewal_hazard_q12_v1\",\n";
  output << "  \"rows\": " << rows << ",\n";
  output << "  \"train_rows\": " << split << ",\n";
  output << "  \"holdout_rows\": " << holdout_rows << ",\n";
  output << "  \"buckets\": " << kBuckets << ",\n";
  output << "  \"multipliers_q12\": [";
  for (int index = 0; index < kBuckets; ++index) {
    if (index) output << ", ";
    output << multipliers[index];
  }
  output << "],\n";
  output << "  \"model_bytes\": " << model_bytes << ",\n";
  output << "  \"baseline_payload_bytes\": " << baseline.output.size() << ",\n";
  output << "  \"candidate_payload_bytes\": " << candidate.output.size() << ",\n";
  output << "  \"gross_saved_bytes\": " << gross << ",\n";
  output << "  \"net_saved_bytes\": " << net << ",\n";
  output << "  \"net_saved_bpm\": " << net_bpm << ",\n";
  output << "  \"required_net_saved_bpm\": " << kTargetBpm << ",\n";
  output << "  \"pass\": " << (pass ? "true" : "false") << ",\n";
  output << "  \"decision\": \""
         << (pass ? "promote_renewal_hazard_to_distant_gate"
                  : "retire_renewal_hazard_q12")
         << "\",\n";
  output << "  \"score_credit_bytes\": 0,\n";
  output << "  \"claim_boundary\": \"Chronological exact range replay with "
            "twenty-six model bytes; native and distant evidence absent.\"\n";
  output << "}\n";
  std::cout << "net_bpm=" << net_bpm
            << " decision=" << (pass ? "promote" : "retire") << "\n";
  return 0;
}
