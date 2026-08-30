#include <algorithm>
#include <array>
#include <cerrno>
#include <cmath>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

namespace {

constexpr uint64_t kStreamBytes = 647798592ULL;
constexpr uint64_t kTraceRows = kStreamBytes * 8ULL;
constexpr uint64_t kActiveBytes = 2331505ULL;
constexpr uint64_t kManifestHeaderBytes = 32ULL;
constexpr uint64_t kManifestRecordBytes = 13ULL;
constexpr uint64_t kTraceHeaderBytes = 16ULL;
constexpr uint64_t kMixScale = 1ULL << 63U;
constexpr double kGrossGateBits = 40163160.0;
constexpr std::array<uint8_t, 8> kManifestMagic{{'G','H','O','R','A','1',0,0}};
constexpr std::array<uint8_t, 8> kTraceMagic{{'C','M','X','2','1','P','1',0}};
__extension__ typedef unsigned __int128 Wide;

[[noreturn]] void Fail(const char* message) {
  std::fprintf(stderr, "horizon retained-parent analysis failure: %s errno=%d\n",
               message, errno);
  std::exit(1);
}

uint64_t ReadLe64(const uint8_t* input) {
  uint64_t value = 0;
  for (unsigned int index = 0; index < 8; ++index) {
    value |= static_cast<uint64_t>(input[index]) << (8U * index);
  }
  return value;
}

uint16_t ReadLe16(const uint8_t* input) {
  return static_cast<uint16_t>(input[0]) |
      static_cast<uint16_t>(static_cast<uint16_t>(input[1]) << 8U);
}

struct Mapping {
  int fd = -1;
  uint64_t bytes = 0;
  const uint8_t* data = nullptr;

  explicit Mapping(const char* path) {
    fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) Fail("open mapping");
    struct stat metadata{};
    if (fstat(fd, &metadata) != 0 || !S_ISREG(metadata.st_mode) ||
        metadata.st_size <= 0) {
      Fail("mapping metadata");
    }
    bytes = static_cast<uint64_t>(metadata.st_size);
    void* mapped = mmap(nullptr, static_cast<size_t>(bytes), PROT_READ,
                        MAP_PRIVATE, fd, 0);
    if (mapped == MAP_FAILED) Fail("mmap");
    data = static_cast<const uint8_t*>(mapped);
  }

  ~Mapping() {
    if (data != nullptr) munmap(const_cast<uint8_t*>(data), static_cast<size_t>(bytes));
    if (fd >= 0) close(fd);
  }

  Mapping(const Mapping&) = delete;
  Mapping& operator=(const Mapping&) = delete;
};

struct KtState {
  uint64_t correct = 0;
  uint64_t incorrect = 0;
};

struct Arm {
  std::array<KtState, 3> kt{};
  uint64_t parent_weight = kMixScale / 2ULL;
  double raw_bits = 0.0;
  double mixture_bits = 0.0;
  std::array<double, 3> raw_by_third{};
  std::array<double, 3> mixture_by_third{};
};

double TruthBits(uint16_t p1, uint8_t truth) {
  const uint32_t count = truth != 0 ? static_cast<uint32_t>(p1)
                                    : 65536U - static_cast<uint32_t>(p1);
  if (count == 0) Fail("zero truth probability");
  return 16.0 - std::log2(static_cast<double>(count));
}

uint16_t CandidateP1(const KtState& state, uint8_t donor,
                     uint8_t prefix, unsigned int bit_index) {
  const uint64_t donor_mass = (2ULL * state.correct + 1ULL) * 255ULL;
  const uint64_t other_mass = 2ULL * state.incorrect + 1ULL;
  const unsigned int prefix_length = bit_index;
  const uint64_t group_size = 1ULL << (8U - prefix_length);
  const uint64_t ones_size = group_size >> 1U;
  const bool donor_in_prefix = prefix_length == 0U ||
      (static_cast<unsigned int>(donor) >> (8U - prefix_length)) == prefix;
  const bool donor_in_ones = donor_in_prefix &&
      (((static_cast<unsigned int>(donor) >> (7U - bit_index)) & 1U) != 0U);
  const uint64_t adjustment = donor_mass - other_mass;
  const uint64_t total = other_mass * group_size +
      (donor_in_prefix ? adjustment : 0ULL);
  const uint64_t ones = other_mass * ones_size +
      (donor_in_ones ? adjustment : 0ULL);
  uint64_t quantized = (ones * 65536ULL + total / 2ULL) / total;
  quantized = std::max<uint64_t>(1ULL, std::min<uint64_t>(65535ULL, quantized));
  return static_cast<uint16_t>(quantized);
}

uint16_t MixtureP1(uint64_t parent_weight, uint16_t parent_p1,
                   uint16_t candidate_p1) {
  const Wide weighted = static_cast<Wide>(parent_weight) * parent_p1 +
      static_cast<Wide>(kMixScale - parent_weight) * candidate_p1;
  uint64_t value = static_cast<uint64_t>(
      (weighted + static_cast<Wide>(kMixScale / 2ULL)) / kMixScale);
  value = std::max<uint64_t>(1ULL, std::min<uint64_t>(65535ULL, value));
  return static_cast<uint16_t>(value);
}

uint64_t PosteriorParentWeight(uint64_t parent_weight, uint32_t parent_truth,
                               uint32_t candidate_truth) {
  const Wide parent_mass = static_cast<Wide>(parent_weight) * parent_truth;
  const Wide candidate_mass =
      static_cast<Wide>(kMixScale - parent_weight) * candidate_truth;
  const Wide total = parent_mass + candidate_mass;
  if (total == 0) Fail("zero posterior mass");

  const long double ratio = static_cast<long double>(parent_mass) /
      static_cast<long double>(total);
  const long double scaled = ratio * static_cast<long double>(kMixScale);
  if (scaled <= 1.0L) return 1ULL;
  if (scaled >= static_cast<long double>(kMixScale - 1ULL)) {
    return kMixScale - 1ULL;
  }
  return static_cast<uint64_t>(std::floor(scaled + 0.5L));
}

size_t Third(uint64_t coordinate) {
  return std::min<size_t>(
      2U, static_cast<size_t>((coordinate * 3ULL) / kStreamBytes));
}

void ObserveArm(Arm* arm, size_t third, uint8_t donor, uint8_t truth,
                const std::array<uint16_t, 8>& parent_p1) {
  uint8_t prefix = 0;
  for (unsigned int bit_index = 0; bit_index < 8U; ++bit_index) {
    const uint8_t truth_bit =
        static_cast<uint8_t>((truth >> (7U - bit_index)) & 1U);
    const uint16_t candidate_p1 =
        CandidateP1(arm->kt[third], donor, prefix, bit_index);
    const uint16_t mixture_p1 =
        MixtureP1(arm->parent_weight, parent_p1[bit_index], candidate_p1);
    const double raw = TruthBits(candidate_p1, truth_bit);
    const double mixed = TruthBits(mixture_p1, truth_bit);
    arm->raw_bits += raw;
    arm->mixture_bits += mixed;
    arm->raw_by_third[third] += raw;
    arm->mixture_by_third[third] += mixed;
    const uint32_t parent_truth = truth_bit != 0
        ? parent_p1[bit_index]
        : 65536U - parent_p1[bit_index];
    const uint32_t candidate_truth = truth_bit != 0
        ? candidate_p1
        : 65536U - candidate_p1;
    arm->parent_weight = PosteriorParentWeight(
        arm->parent_weight, parent_truth, candidate_truth);
    prefix = static_cast<uint8_t>((prefix << 1U) | truth_bit);
  }
  if (donor == truth) {
    ++arm->kt[third].correct;
  } else {
    ++arm->kt[third].incorrect;
  }
}

void WriteArray(FILE* output, const std::array<double, 3>& values) {
  std::fprintf(output, "[%.9f,%.9f,%.9f]", values[0], values[1], values[2]);
}

void WriteArm(FILE* output, const char* id, const Arm& arm,
              double parent_bits,
              const std::array<double, 3>& parent_by_third) {
  std::array<double, 3> raw_gain{};
  std::array<double, 3> mixture_gain{};
  for (size_t index = 0; index < 3; ++index) {
    raw_gain[index] = parent_by_third[index] - arm.raw_by_third[index];
    mixture_gain[index] = parent_by_third[index] - arm.mixture_by_third[index];
  }
  std::fprintf(output,
      "\"%s\":{\"raw_truth_bits\":%.9f,\"mixture_truth_bits\":%.9f,"
      "\"raw_gain_bits\":%.9f,\"mixture_gain_bits\":%.9f,"
      "\"raw_gain_by_third\":",
      id, arm.raw_bits, arm.mixture_bits, parent_bits - arm.raw_bits,
      parent_bits - arm.mixture_bits);
  WriteArray(output, raw_gain);
  std::fprintf(output, ",\"mixture_gain_by_third\":");
  WriteArray(output, mixture_gain);
  std::fprintf(output, ",\"terminal_parent_weight_q63\":\"%" PRIu64 "\"}",
               arm.parent_weight);
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::fprintf(stderr, "usage: %s P1_TRACE A_MANIFEST OUTPUT_JSON\n", argv[0]);
    return 64;
  }
  Mapping trace(argv[1]);
  Mapping manifest(argv[2]);
  const uint64_t expected_trace_bytes = kTraceHeaderBytes + 2ULL * kTraceRows;
  const uint64_t expected_manifest_bytes =
      kManifestHeaderBytes + kManifestRecordBytes * kActiveBytes;
  if (trace.bytes != expected_trace_bytes ||
      !std::equal(kTraceMagic.begin(), kTraceMagic.end(), trace.data) ||
      ReadLe64(trace.data + 8) != kTraceRows) {
    Fail("trace geometry");
  }
  if (manifest.bytes != expected_manifest_bytes ||
      !std::equal(kManifestMagic.begin(), kManifestMagic.end(), manifest.data) ||
      ReadLe64(manifest.data + 8) != kActiveBytes ||
      ReadLe64(manifest.data + 16) != kStreamBytes ||
      ReadLe64(manifest.data + 24) != kManifestRecordBytes) {
    Fail("manifest geometry");
  }
  (void)madvise(const_cast<uint8_t*>(trace.data), static_cast<size_t>(trace.bytes),
                MADV_RANDOM);
  (void)madvise(const_cast<uint8_t*>(manifest.data),
                static_cast<size_t>(manifest.bytes), MADV_SEQUENTIAL);

  std::array<double, 3> parent_by_third{};
  double parent_bits = 0.0;
  std::array<Arm, 4> arms{};
  uint64_t prior_coordinate = 0;
  uint64_t coordinate_hash = 1469598103934665603ULL;
  for (uint64_t row_index = 0; row_index < kActiveBytes; ++row_index) {
    const uint8_t* row = manifest.data + kManifestHeaderBytes +
        row_index * kManifestRecordBytes;
    const uint64_t coordinate = ReadLe64(row);
    if (coordinate >= kStreamBytes ||
        (row_index != 0 && coordinate <= prior_coordinate)) {
      Fail("manifest coordinate order");
    }
    prior_coordinate = coordinate;
    for (unsigned int byte = 0; byte < 8; ++byte) {
      coordinate_hash = (coordinate_hash ^ static_cast<uint8_t>(coordinate >>
          (8U * byte))) * 1099511628211ULL;
    }
    const uint8_t donors[4] = {row[8], row[9], row[10], row[11]};
    const uint8_t truth = row[12];
    std::array<uint16_t, 8> probabilities{};
    const uint8_t* probability_row =
        trace.data + kTraceHeaderBytes + coordinate * 16ULL;
    const size_t third = Third(coordinate);
    for (unsigned int bit_index = 0; bit_index < 8U; ++bit_index) {
      probabilities[bit_index] = ReadLe16(probability_row + 2U * bit_index);
      if (probabilities[bit_index] == 0) Fail("illegal parent probability");
      const uint8_t truth_bit =
          static_cast<uint8_t>((truth >> (7U - bit_index)) & 1U);
      const double bits = TruthBits(probabilities[bit_index], truth_bit);
      parent_bits += bits;
      parent_by_third[third] += bits;
    }
    for (size_t arm = 0; arm < arms.size(); ++arm) {
      ObserveArm(&arms[arm], third, donors[arm], truth, probabilities);
    }
  }

  std::array<double, 4> gains{};
  std::array<std::array<double, 3>, 4> gains_by_third{};
  for (size_t arm = 0; arm < arms.size(); ++arm) {
    gains[arm] = parent_bits - arms[arm].mixture_bits;
    for (size_t third = 0; third < 3; ++third) {
      gains_by_third[arm][third] =
          parent_by_third[third] - arms[arm].mixture_by_third[third];
    }
  }
  double minimum_third = std::numeric_limits<double>::infinity();
  double minimum_control_margin = gains[0] -
      std::max({gains[1], gains[2], gains[3]});
  for (size_t third = 0; third < 3; ++third) {
    minimum_third = std::min(minimum_third, gains_by_third[0][third]);
    minimum_control_margin = std::min(
        minimum_control_margin,
        gains_by_third[0][third] - std::max({gains_by_third[1][third],
                                             gains_by_third[2][third],
                                             gains_by_third[3][third]}));
  }
  const bool pass = gains[0] >= kGrossGateBits && minimum_third > 0.0 &&
      minimum_control_margin > 0.0;

  const int fd = open(argv[3], O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC |
                      O_NOFOLLOW, 0600);
  if (fd < 0) Fail("create output");
  FILE* output = fdopen(fd, "wb");
  if (output == nullptr) Fail("fdopen output");
  std::fprintf(output,
      "{\n\"schema\":\"gamma.enwiki9.horizon-retained-parent-analysis.v1\","
      "\n\"active_bytes\":%" PRIu64 ",\n\"parent_trace_rows\":%" PRIu64
      ",\n\"parent_truth_bits\":%.9f,\n\"parent_truth_bits_by_third\":",
      kActiveBytes, kTraceRows, parent_bits);
  WriteArray(output, parent_by_third);
  std::fprintf(output, ",\n\"arms\":{");
  WriteArm(output, "D", arms[0], parent_bits, parent_by_third);
  std::fprintf(output, ",");
  WriteArm(output, "S", arms[1], parent_bits, parent_by_third);
  std::fprintf(output, ",");
  WriteArm(output, "R", arms[2], parent_bits, parent_by_third);
  std::fprintf(output, ",");
  WriteArm(output, "N", arms[3], parent_bits, parent_by_third);
  std::fprintf(output,
      "},\n\"minimum_third_mixture_gain_bits\":%.9f,"
      "\n\"minimum_control_margin_bits\":%.9f,"
      "\n\"gross_gate_bits\":%.9f,"
      "\n\"coordinate_fnv1a64\":\"%016" PRIx64 "\","
      "\n\"promotion_pass\":%s,\n\"archive_authority\":false,"
      "\n\"score_credit_bytes\":0\n}\n",
      minimum_third, minimum_control_margin, kGrossGateBits, coordinate_hash,
      pass ? "true" : "false");
  if (std::fflush(output) != 0 || fsync(fd) != 0 || std::fclose(output) != 0) {
    Fail("close output");
  }
  return 0;
}
