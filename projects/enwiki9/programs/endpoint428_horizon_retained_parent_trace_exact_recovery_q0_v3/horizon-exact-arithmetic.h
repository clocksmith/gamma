#ifndef HORIZON_EXACT_ARITHMETIC_H
#define HORIZON_EXACT_ARITHMETIC_H

#include <cstdint>

namespace horizon_exact {

__extension__ typedef unsigned __int128 Wide;

constexpr std::uint64_t kWeightTotal = UINT64_C(1) << 63U;
constexpr std::uint64_t kInitialParentWeight = UINT64_C(1) << 62U;
constexpr std::uint32_t kProbabilityScale = 65536U;

// Returns round-half-up(numerator * 2^bits / denominator), clamped to
// [1, 2^bits - 1]. A zero return reports an invalid precondition.
inline std::uint64_t RoundRatioPowerOfTwo(
    Wide numerator, Wide denominator, unsigned int bits) {
  if (bits == 0U || bits > 63U || denominator == 0 ||
      numerator == 0 || numerator >= denominator) {
    return 0;
  }
  const std::uint64_t total = UINT64_C(1) << bits;
  Wide remainder = numerator;
  std::uint64_t quotient = 0;
  for (unsigned int bit = 0; bit < bits; ++bit) {
    remainder <<= 1U;
    quotient <<= 1U;
    if (remainder >= denominator) {
      remainder -= denominator;
      quotient |= 1U;
    }
  }
  if ((remainder << 1U) >= denominator) ++quotient;
  if (quotient == 0) return 1;
  if (quotient >= total) return total - 1U;
  return quotient;
}

inline std::uint64_t PosteriorParentWeight(
    std::uint64_t parent_weight, std::uint32_t parent_truth,
    std::uint32_t candidate_truth) {
  if (parent_weight == 0 || parent_weight >= kWeightTotal ||
      parent_truth == 0 || parent_truth >= kProbabilityScale ||
      candidate_truth == 0 || candidate_truth >= kProbabilityScale) {
    return 0;
  }
  const Wide parent_mass = static_cast<Wide>(parent_weight) * parent_truth;
  const Wide candidate_mass =
      static_cast<Wide>(kWeightTotal - parent_weight) * candidate_truth;
  return RoundRatioPowerOfTwo(parent_mass, parent_mass + candidate_mass, 63U);
}

inline std::uint32_t MixCountPowerOfTwo(
    unsigned int weight_bits, std::uint32_t probability_scale,
    std::uint64_t parent_weight, std::uint32_t parent_count,
    std::uint32_t candidate_count) {
  if (weight_bits == 0U || weight_bits > 63U || probability_scale < 3U) {
    return 0;
  }
  const std::uint64_t total = UINT64_C(1) << weight_bits;
  if (parent_weight == 0 || parent_weight >= total ||
      parent_count == 0 || parent_count >= probability_scale ||
      candidate_count == 0 || candidate_count >= probability_scale) {
    return 0;
  }
  const Wide weighted = static_cast<Wide>(parent_weight) * parent_count +
      static_cast<Wide>(total - parent_weight) * candidate_count;
  std::uint64_t result = static_cast<std::uint64_t>(
      (weighted + static_cast<Wide>(total / 2U)) / total);
  if (result == 0) result = 1;
  if (result >= probability_scale) result = probability_scale - 1U;
  return static_cast<std::uint32_t>(result);
}

inline std::uint16_t MixtureP1(
    std::uint64_t parent_weight, std::uint16_t parent_p1,
    std::uint16_t candidate_p1) {
  return static_cast<std::uint16_t>(MixCountPowerOfTwo(
      63U, kProbabilityScale, parent_weight, parent_p1, candidate_p1));
}

}  // namespace horizon_exact

#endif
