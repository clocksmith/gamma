#include "horizon-exact-arithmetic.h"

#include <array>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <unistd.h>

namespace {

using horizon_exact::Wide;

[[noreturn]] void Fail(const char* message) {
  std::fprintf(stderr, "horizon exact fixture failure: %s\n", message);
  std::exit(1);
}

void PrintWide(FILE* output, Wide value) {
  std::fprintf(output, "%" PRIu64 ":%" PRIu64,
      static_cast<std::uint64_t>(value >> 64U),
      static_cast<std::uint64_t>(value));
}

void Direct(FILE* output, const char* label, Wide numerator, Wide denominator) {
  const std::uint64_t value =
      horizon_exact::RoundRatioPowerOfTwo(numerator, denominator, 63U);
  std::fprintf(output, "D %s ", label);
  PrintWide(output, numerator);
  std::fprintf(output, " ");
  PrintWide(output, denominator);
  std::fprintf(output, " %" PRIu64 "\n", value);
}

void Posterior(FILE* output, const char* label, std::uint64_t weight,
               std::uint32_t parent_truth,
               std::uint32_t candidate_truth) {
  std::fprintf(output,
      "P %s %" PRIu64 " %" PRIu32 " %" PRIu32 " %" PRIu64 "\n",
      label, weight, parent_truth, candidate_truth,
      horizon_exact::PosteriorParentWeight(
          weight, parent_truth, candidate_truth));
}

void Mixture(FILE* output, const char* label, std::uint64_t weight,
             std::uint16_t parent_count, std::uint16_t candidate_count) {
  std::fprintf(output,
      "M %s %" PRIu64 " %" PRIu16 " %" PRIu16 " %" PRIu16 "\n",
      label, weight, parent_count, candidate_count,
      horizon_exact::MixtureP1(weight, parent_count, candidate_count));
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 2) {
    std::fprintf(stderr, "usage: %s OUTPUT_TSV\n", argv[0]);
    return 64;
  }
  const int fd = open(argv[1], O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC |
                      O_NOFOLLOW, 0600);
  if (fd < 0) Fail("create output");
  FILE* output = fdopen(fd, "wb");
  if (output == nullptr) Fail("fdopen output");
  constexpr std::uint64_t total = horizon_exact::kWeightTotal;
  std::fprintf(output, "H horizon-exact-arithmetic-fixture-v1\n");
  Direct(output, "half_at_zero", 1, static_cast<Wide>(1) << 64U);
  Direct(output, "one_and_half", 3, static_cast<Wide>(1) << 64U);
  Direct(output, "half_below_total",
         (static_cast<Wide>(1) << 64U) - 1,
         static_cast<Wide>(1) << 64U);
  Direct(output, "minimum_ratio", 1,
         static_cast<Wide>(total) * 65535U);
  Direct(output, "maximum_ratio",
         static_cast<Wide>(total) * 65535U - 1,
         static_cast<Wide>(total) * 65535U);

  Posterior(output, "equal_low", total / 2U, 1, 1);
  Posterior(output, "equal_high", total / 2U, 65535, 65535);
  Posterior(output, "candidate_wins", total / 2U, 1, 65535);
  Posterior(output, "parent_wins", total / 2U, 65535, 1);
  Posterior(output, "low_clamp", 1, 1, 65535);
  Posterior(output, "high_clamp", total - 1U, 65535, 1);

  Mixture(output, "parent_low", total - 1U, 1, 65535);
  Mixture(output, "candidate_low", 1, 65535, 1);
  Mixture(output, "equal_counts", total / 2U, 32768, 32768);
  Mixture(output, "half_up", total / 2U, 1, 2);

  constexpr std::uint32_t probability_scale = 16U;
  for (unsigned int bits = 2U; bits <= 8U; ++bits) {
    const std::uint64_t weight_total = UINT64_C(1) << bits;
    for (std::uint64_t weight = 1; weight < weight_total; ++weight) {
      for (std::uint32_t parent_count = 1;
           parent_count < probability_scale; ++parent_count) {
        for (std::uint32_t candidate_count = 1;
             candidate_count < probability_scale; ++candidate_count) {
          const std::uint32_t mixed = horizon_exact::MixCountPowerOfTwo(
              bits, probability_scale, weight, parent_count, candidate_count);
          for (std::uint32_t truth = 0; truth <= 1U; ++truth) {
            const std::uint32_t parent_truth = truth != 0U
                ? parent_count : probability_scale - parent_count;
            const std::uint32_t candidate_truth = truth != 0U
                ? candidate_count : probability_scale - candidate_count;
            const Wide parent_mass =
                static_cast<Wide>(weight) * parent_truth;
            const Wide candidate_mass =
                static_cast<Wide>(weight_total - weight) * candidate_truth;
            const std::uint64_t posterior =
                horizon_exact::RoundRatioPowerOfTwo(
                    parent_mass, parent_mass + candidate_mass, bits);
            std::fprintf(output,
                "R %u %" PRIu64 " %" PRIu32 " %" PRIu32 " %" PRIu32
                " %" PRIu32 " %" PRIu64 "\n",
                bits, weight, parent_count, candidate_count, truth, mixed,
                posterior);
          }
        }
      }
    }
  }
  if (std::fflush(output) != 0 || fsync(fd) != 0 ||
      std::fclose(output) != 0) {
    Fail("close output");
  }
  return 0;
}
