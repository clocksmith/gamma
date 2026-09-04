#include "horizon-exact-arithmetic.h"

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

constexpr std::uint64_t kStreamBytes = 647798592ULL;
constexpr std::uint64_t kTraceRows = kStreamBytes * 8ULL;
constexpr std::uint64_t kActiveBytes = 2331505ULL;
constexpr std::uint64_t kManifestHeaderBytes = 32ULL;
constexpr std::uint64_t kManifestRecordBytes = 13ULL;
constexpr std::uint64_t kTraceHeaderBytes = 16ULL;
constexpr double kGrossGateBits = 40163160.0;
constexpr std::array<std::uint8_t, 8> kManifestMagic{{
    'G','H','O','R','A','1',0,0}};
constexpr std::array<std::uint8_t, 8> kTraceMagic{{
    'C','M','X','2','1','P','1',0}};

[[noreturn]] void Fail(const char* message) {
  std::fprintf(stderr,
      "horizon exact retained-parent analysis failure: %s errno=%d\n",
      message, errno);
  std::exit(1);
}

std::uint64_t ReadLe64(const std::uint8_t* input) {
  std::uint64_t value = 0;
  for (unsigned int index = 0; index < 8U; ++index) {
    value |= static_cast<std::uint64_t>(input[index]) << (8U * index);
  }
  return value;
}

std::uint16_t ReadLe16(const std::uint8_t* input) {
  return static_cast<std::uint16_t>(input[0]) |
      static_cast<std::uint16_t>(
          static_cast<std::uint16_t>(input[1]) << 8U);
}

struct Mapping {
  int fd = -1;
  std::uint64_t bytes = 0;
  const std::uint8_t* data = nullptr;

  explicit Mapping(const char* path) {
    fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) Fail("open mapping");
    struct stat metadata {};
    if (fstat(fd, &metadata) != 0 || !S_ISREG(metadata.st_mode) ||
        metadata.st_size <= 0) {
      Fail("mapping metadata");
    }
    bytes = static_cast<std::uint64_t>(metadata.st_size);
    void* mapped = mmap(nullptr, static_cast<std::size_t>(bytes), PROT_READ,
                        MAP_PRIVATE, fd, 0);
    if (mapped == MAP_FAILED) Fail("mmap");
    data = static_cast<const std::uint8_t*>(mapped);
  }

  ~Mapping() {
    if (data != nullptr) {
      munmap(const_cast<std::uint8_t*>(data),
             static_cast<std::size_t>(bytes));
    }
    if (fd >= 0) close(fd);
  }

  Mapping(const Mapping&) = delete;
  Mapping& operator=(const Mapping&) = delete;
};

struct KtState {
  std::uint64_t correct = 0;
  std::uint64_t incorrect = 0;
};

struct Divergence {
  bool present = false;
  char arm = '?';
  std::uint64_t coordinate = 0;
  unsigned int bit_index = 0;
  std::uint8_t truth = 0;
  std::uint16_t parent_p1 = 0;
  std::uint16_t candidate_p1 = 0;
  std::uint32_t parent_truth = 0;
  std::uint32_t candidate_truth = 0;
  std::uint64_t prior_exact_weight = 0;
  std::uint64_t prior_legacy_weight = 0;
  std::uint64_t exact_weight_after = 0;
  std::uint64_t legacy_weight_after = 0;
};

struct Arm {
  std::array<KtState, 3> kt{};
  std::array<KtState, 3> legacy_kt{};
  std::uint64_t parent_weight = horizon_exact::kInitialParentWeight;
  std::uint64_t legacy_parent_weight = horizon_exact::kInitialParentWeight;
  double raw_bits = 0.0;
  double mixture_bits = 0.0;
  double legacy_mixture_bits = 0.0;
  std::array<double, 3> raw_by_third{};
  std::array<double, 3> mixture_by_third{};
  std::array<double, 3> legacy_mixture_by_third{};
};

double TruthBits(std::uint16_t p1, std::uint8_t truth) {
  const std::uint32_t count = truth != 0
      ? static_cast<std::uint32_t>(p1)
      : 65536U - static_cast<std::uint32_t>(p1);
  if (count == 0) Fail("zero truth probability");
  return 16.0 - std::log2(static_cast<double>(count));
}

std::uint16_t CandidateP1(const KtState& state, std::uint8_t donor,
                          std::uint8_t prefix, unsigned int bit_index) {
  const std::uint64_t donor_mass = (2ULL * state.correct + 1ULL) * 255ULL;
  const std::uint64_t other_mass = 2ULL * state.incorrect + 1ULL;
  const unsigned int prefix_length = bit_index;
  const std::uint64_t group_size = 1ULL << (8U - prefix_length);
  const std::uint64_t ones_size = group_size >> 1U;
  const bool donor_in_prefix = prefix_length == 0U ||
      (static_cast<unsigned int>(donor) >> (8U - prefix_length)) == prefix;
  const bool donor_in_ones = donor_in_prefix &&
      (((static_cast<unsigned int>(donor) >> (7U - bit_index)) & 1U) != 0U);
  const std::uint64_t adjustment = donor_mass - other_mass;
  const std::uint64_t total = other_mass * group_size +
      (donor_in_prefix ? adjustment : 0ULL);
  const std::uint64_t ones = other_mass * ones_size +
      (donor_in_ones ? adjustment : 0ULL);
  std::uint64_t quantized = (ones * 65536ULL + total / 2ULL) / total;
  quantized = std::max<std::uint64_t>(
      1ULL, std::min<std::uint64_t>(65535ULL, quantized));
  return static_cast<std::uint16_t>(quantized);
}

std::uint64_t LegacyPosteriorParentWeight(
    std::uint64_t parent_weight, std::uint32_t parent_truth,
    std::uint32_t candidate_truth) {
  const horizon_exact::Wide parent_mass =
      static_cast<horizon_exact::Wide>(parent_weight) * parent_truth;
  const horizon_exact::Wide candidate_mass =
      static_cast<horizon_exact::Wide>(
          horizon_exact::kWeightTotal - parent_weight) * candidate_truth;
  const horizon_exact::Wide total = parent_mass + candidate_mass;
  if (total == 0) Fail("zero legacy posterior mass");
  const long double ratio = static_cast<long double>(parent_mass) /
      static_cast<long double>(total);
  const long double scaled = ratio *
      static_cast<long double>(horizon_exact::kWeightTotal);
  if (scaled <= 1.0L) return 1ULL;
  if (scaled >= static_cast<long double>(
          horizon_exact::kWeightTotal - 1ULL)) {
    return horizon_exact::kWeightTotal - 1ULL;
  }
  return static_cast<std::uint64_t>(std::floor(scaled + 0.5L));
}

std::size_t Third(std::uint64_t coordinate) {
  return std::min<std::size_t>(
      2U, static_cast<std::size_t>((coordinate * 3ULL) / kStreamBytes));
}

void ObserveArm(Arm* arm, char arm_id, std::uint64_t coordinate,
                std::size_t third, std::uint8_t donor, std::uint8_t truth,
                const std::array<std::uint16_t, 8>& parent_p1,
                Divergence* first_divergence) {
  std::uint8_t prefix = 0;
  for (unsigned int bit_index = 0; bit_index < 8U; ++bit_index) {
    const std::uint8_t truth_bit = static_cast<std::uint8_t>(
        (truth >> (7U - bit_index)) & 1U);
    const std::uint16_t candidate_p1 =
        CandidateP1(arm->kt[third], donor, prefix, bit_index);
    const std::uint16_t legacy_candidate_p1 =
        CandidateP1(arm->legacy_kt[third], donor, prefix, bit_index);
    if (candidate_p1 != legacy_candidate_p1) {
      Fail("legacy and exact KT state diverged");
    }
    const std::uint16_t mixture_p1 = horizon_exact::MixtureP1(
        arm->parent_weight, parent_p1[bit_index], candidate_p1);
    const std::uint16_t legacy_mixture_p1 = horizon_exact::MixtureP1(
        arm->legacy_parent_weight, parent_p1[bit_index], candidate_p1);
    if (mixture_p1 == 0 || legacy_mixture_p1 == 0) {
      Fail("invalid mixture count");
    }
    const double raw = TruthBits(candidate_p1, truth_bit);
    const double mixed = TruthBits(mixture_p1, truth_bit);
    const double legacy_mixed = TruthBits(legacy_mixture_p1, truth_bit);
    arm->raw_bits += raw;
    arm->mixture_bits += mixed;
    arm->legacy_mixture_bits += legacy_mixed;
    arm->raw_by_third[third] += raw;
    arm->mixture_by_third[third] += mixed;
    arm->legacy_mixture_by_third[third] += legacy_mixed;
    const std::uint32_t parent_truth = truth_bit != 0
        ? parent_p1[bit_index]
        : 65536U - parent_p1[bit_index];
    const std::uint32_t candidate_truth = truth_bit != 0
        ? candidate_p1
        : 65536U - candidate_p1;
    const std::uint64_t prior_exact = arm->parent_weight;
    const std::uint64_t prior_legacy = arm->legacy_parent_weight;
    const std::uint64_t exact_after =
        horizon_exact::PosteriorParentWeight(
            prior_exact, parent_truth, candidate_truth);
    const std::uint64_t legacy_after = LegacyPosteriorParentWeight(
        prior_legacy, parent_truth, candidate_truth);
    if (exact_after == 0 || legacy_after == 0) {
      Fail("invalid posterior weight");
    }
    if (!first_divergence->present && exact_after != legacy_after) {
      *first_divergence = Divergence{
          true, arm_id, coordinate, bit_index, truth_bit,
          parent_p1[bit_index], candidate_p1,
          parent_truth, candidate_truth, prior_exact, prior_legacy,
          exact_after, legacy_after};
    }
    arm->parent_weight = exact_after;
    arm->legacy_parent_weight = legacy_after;
    prefix = static_cast<std::uint8_t>((prefix << 1U) | truth_bit);
  }
  if (donor == truth) {
    ++arm->kt[third].correct;
    ++arm->legacy_kt[third].correct;
  } else {
    ++arm->kt[third].incorrect;
    ++arm->legacy_kt[third].incorrect;
  }
}

void WriteArray(FILE* output, const std::array<double, 3>& values) {
  std::fprintf(output, "[%.9f,%.9f,%.9f]",
               values[0], values[1], values[2]);
}

void WriteKt(FILE* output, const std::array<KtState, 3>& states) {
  std::fprintf(output, "[");
  for (std::size_t index = 0; index < states.size(); ++index) {
    if (index != 0) std::fprintf(output, ",");
    std::fprintf(output,
        "{\"correct\":%" PRIu64 ",\"incorrect\":%" PRIu64 "}",
        states[index].correct, states[index].incorrect);
  }
  std::fprintf(output, "]");
}

bool KtIdentity(const Arm& arm) {
  for (std::size_t index = 0; index < arm.kt.size(); ++index) {
    if (arm.kt[index].correct != arm.legacy_kt[index].correct ||
        arm.kt[index].incorrect != arm.legacy_kt[index].incorrect) {
      return false;
    }
  }
  return true;
}

void WriteArm(FILE* output, const char* id, const Arm& arm,
              double parent_bits,
              const std::array<double, 3>& parent_by_third) {
  std::array<double, 3> raw_gain{};
  std::array<double, 3> mixture_gain{};
  std::array<double, 3> legacy_mixture_gain{};
  for (std::size_t index = 0; index < 3; ++index) {
    raw_gain[index] = parent_by_third[index] - arm.raw_by_third[index];
    mixture_gain[index] =
        parent_by_third[index] - arm.mixture_by_third[index];
    legacy_mixture_gain[index] =
        parent_by_third[index] - arm.legacy_mixture_by_third[index];
  }
  std::fprintf(output,
      "\"%s\":{\"raw_truth_bits\":%.9f,"
      "\"mixture_truth_bits\":%.9f,"
      "\"legacy_mixture_truth_bits\":%.9f,"
      "\"raw_gain_bits\":%.9f,\"mixture_gain_bits\":%.9f,"
      "\"legacy_mixture_gain_bits\":%.9f,\"raw_gain_by_third\":",
      id, arm.raw_bits, arm.mixture_bits, arm.legacy_mixture_bits,
      parent_bits - arm.raw_bits, parent_bits - arm.mixture_bits,
      parent_bits - arm.legacy_mixture_bits);
  WriteArray(output, raw_gain);
  std::fprintf(output, ",\"mixture_gain_by_third\":");
  WriteArray(output, mixture_gain);
  std::fprintf(output, ",\"legacy_mixture_gain_by_third\":");
  WriteArray(output, legacy_mixture_gain);
  std::fprintf(output, ",\"kt_by_third\":");
  WriteKt(output, arm.kt);
  std::fprintf(output,
      ",\"legacy_exact_kt_identity_pass\":%s,"
      "\"terminal_parent_weight_q63\":\"%" PRIu64 "\","
      "\"terminal_legacy_parent_weight_q63\":\"%" PRIu64 "\"}",
      KtIdentity(arm) ? "true" : "false",
      arm.parent_weight, arm.legacy_parent_weight);
}

void WriteDivergence(FILE* output, const Divergence& divergence) {
  if (!divergence.present) {
    std::fprintf(output, "null");
    return;
  }
  std::fprintf(output,
      "{\"arm\":\"%c\",\"coordinate\":%" PRIu64
      ",\"bit_index\":%u,\"truth\":%u,\"parent_p1\":%" PRIu16
      ",\"candidate_p1\":%" PRIu16
      ",\"parent_truth_count\":%" PRIu32
      ",\"candidate_truth_count\":%" PRIu32
      ",\"prior_exact_parent_weight\":\"%" PRIu64 "\""
      ",\"prior_legacy_parent_weight\":\"%" PRIu64 "\""
      ",\"exact_parent_weight_after\":\"%" PRIu64 "\""
      ",\"legacy_parent_weight_after\":\"%" PRIu64 "\"}",
      divergence.arm, divergence.coordinate, divergence.bit_index,
      static_cast<unsigned int>(divergence.truth), divergence.parent_p1,
      divergence.candidate_p1, divergence.parent_truth,
      divergence.candidate_truth, divergence.prior_exact_weight,
      divergence.prior_legacy_weight, divergence.exact_weight_after,
      divergence.legacy_weight_after);
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::fprintf(stderr,
        "usage: %s P1_TRACE A_MANIFEST OUTPUT_JSON\n", argv[0]);
    return 64;
  }
  Mapping trace(argv[1]);
  Mapping manifest(argv[2]);
  const std::uint64_t expected_trace_bytes =
      kTraceHeaderBytes + 2ULL * kTraceRows;
  const std::uint64_t expected_manifest_bytes =
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
  (void)madvise(const_cast<std::uint8_t*>(trace.data),
                static_cast<std::size_t>(trace.bytes), MADV_RANDOM);
  (void)madvise(const_cast<std::uint8_t*>(manifest.data),
                static_cast<std::size_t>(manifest.bytes), MADV_SEQUENTIAL);

  std::array<double, 3> parent_by_third{};
  double parent_bits = 0.0;
  std::array<Arm, 4> arms{};
  constexpr std::array<char, 4> arm_ids{{'D', 'S', 'R', 'N'}};
  Divergence first_divergence{};
  std::uint64_t prior_coordinate = 0;
  std::uint64_t coordinate_hash = 1469598103934665603ULL;
  for (std::uint64_t row_index = 0; row_index < kActiveBytes; ++row_index) {
    const std::uint8_t* row = manifest.data + kManifestHeaderBytes +
        row_index * kManifestRecordBytes;
    const std::uint64_t coordinate = ReadLe64(row);
    if (coordinate >= kStreamBytes ||
        (row_index != 0 && coordinate <= prior_coordinate)) {
      Fail("manifest coordinate order");
    }
    prior_coordinate = coordinate;
    for (unsigned int byte = 0; byte < 8U; ++byte) {
      coordinate_hash = (coordinate_hash ^ static_cast<std::uint8_t>(
          coordinate >> (8U * byte))) * 1099511628211ULL;
    }
    const std::uint8_t donors[4] = {row[8], row[9], row[10], row[11]};
    const std::uint8_t truth = row[12];
    std::array<std::uint16_t, 8> probabilities{};
    const std::uint8_t* probability_row =
        trace.data + kTraceHeaderBytes + coordinate * 16ULL;
    const std::size_t third = Third(coordinate);
    for (unsigned int bit_index = 0; bit_index < 8U; ++bit_index) {
      probabilities[bit_index] =
          ReadLe16(probability_row + 2U * bit_index);
      if (probabilities[bit_index] == 0) {
        Fail("illegal parent probability");
      }
      const std::uint8_t truth_bit = static_cast<std::uint8_t>(
          (truth >> (7U - bit_index)) & 1U);
      const double bits = TruthBits(probabilities[bit_index], truth_bit);
      parent_bits += bits;
      parent_by_third[third] += bits;
    }
    for (std::size_t arm = 0; arm < arms.size(); ++arm) {
      ObserveArm(&arms[arm], arm_ids[arm], coordinate, third,
                 donors[arm], truth, probabilities, &first_divergence);
    }
  }

  std::array<double, 4> gains{};
  std::array<double, 4> legacy_gains{};
  std::array<std::array<double, 3>, 4> gains_by_third{};
  std::array<std::array<double, 3>, 4> legacy_gains_by_third{};
  bool kt_identity = true;
  for (std::size_t arm = 0; arm < arms.size(); ++arm) {
    gains[arm] = parent_bits - arms[arm].mixture_bits;
    legacy_gains[arm] = parent_bits - arms[arm].legacy_mixture_bits;
    kt_identity = kt_identity && KtIdentity(arms[arm]);
    for (std::size_t third = 0; third < 3; ++third) {
      gains_by_third[arm][third] =
          parent_by_third[third] - arms[arm].mixture_by_third[third];
      legacy_gains_by_third[arm][third] = parent_by_third[third] -
          arms[arm].legacy_mixture_by_third[third];
    }
  }
  double minimum_third = std::numeric_limits<double>::infinity();
  double minimum_control_margin = gains[0] -
      std::max({gains[1], gains[2], gains[3]});
  double legacy_minimum_third = std::numeric_limits<double>::infinity();
  double legacy_minimum_control_margin = legacy_gains[0] -
      std::max({legacy_gains[1], legacy_gains[2], legacy_gains[3]});
  for (std::size_t third = 0; third < 3; ++third) {
    minimum_third = std::min(minimum_third, gains_by_third[0][third]);
    minimum_control_margin = std::min(
        minimum_control_margin,
        gains_by_third[0][third] -
            std::max({gains_by_third[1][third],
                      gains_by_third[2][third],
                      gains_by_third[3][third]}));
    legacy_minimum_third = std::min(
        legacy_minimum_third, legacy_gains_by_third[0][third]);
    legacy_minimum_control_margin = std::min(
        legacy_minimum_control_margin,
        legacy_gains_by_third[0][third] -
            std::max({legacy_gains_by_third[1][third],
                      legacy_gains_by_third[2][third],
                      legacy_gains_by_third[3][third]}));
  }
  const bool pass = gains[0] >= kGrossGateBits && minimum_third > 0.0 &&
      minimum_control_margin > 0.0 && kt_identity;

  const int fd = open(argv[3], O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC |
                      O_NOFOLLOW, 0600);
  if (fd < 0) Fail("create output");
  FILE* output = fdopen(fd, "wb");
  if (output == nullptr) Fail("fdopen output");
  std::fprintf(output,
      "{\n\"schema\":\"gamma.enwiki9.horizon-retained-parent-exact-analysis.v1\","
      "\n\"active_bytes\":%" PRIu64
      ",\n\"parent_trace_rows\":%" PRIu64
      ",\n\"parent_truth_bits\":%.9f,"
      "\n\"parent_truth_bits_by_third\":",
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
      "\n\"legacy_minimum_third_mixture_gain_bits\":%.9f,"
      "\n\"legacy_minimum_control_margin_bits\":%.9f,"
      "\n\"gross_gate_bits\":%.9f,"
      "\n\"coordinate_fnv1a64\":\"%016" PRIx64 "\","
      "\n\"legacy_exact_kt_identity_pass\":%s,"
      "\n\"first_legacy_divergence\":",
      minimum_third, minimum_control_margin, legacy_minimum_third,
      legacy_minimum_control_margin, kGrossGateBits, coordinate_hash,
      kt_identity ? "true" : "false");
  WriteDivergence(output, first_divergence);
  std::fprintf(output,
      ",\n\"promotion_pass\":%s,\n\"archive_authority\":false,"
      "\n\"score_credit_bytes\":0\n}\n",
      pass ? "true" : "false");
  if (std::fflush(output) != 0 || fsync(fd) != 0 ||
      std::fclose(output) != 0) {
    Fail("close output");
  }
  return 0;
}
