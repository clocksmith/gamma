#include "safe-mix.h"

#include <limits>

GammaSafeMix::GammaSafeMix()
    : probability_scale_(0),
      parent_weight_(kInitialParentWeight),
      pending_parent_count_(0),
      pending_treatment_count_(0),
      event_pending_(false) {}

bool GammaSafeMix::Reset(std::uint32_t probability_scale) {
  if (probability_scale_ != 0 || probability_scale < 3) {
    Fault();
    return false;
  }
  probability_scale_ = probability_scale;
  parent_weight_ = kInitialParentWeight;
  pending_parent_count_ = 0;
  pending_treatment_count_ = 0;
  event_pending_ = false;
  return true;
}

void GammaSafeMix::Fault() {
  probability_scale_ = 1;
  pending_parent_count_ = 0;
  pending_treatment_count_ = 0;
  event_pending_ = false;
}

bool GammaSafeMix::CountsValid(
    std::uint32_t scale,
    std::uint32_t parent_count,
    std::uint32_t treatment_count) {
  return scale >= 3 &&
      parent_count > 0 && parent_count < scale &&
      treatment_count > 0 && treatment_count < scale;
}

std::uint64_t GammaSafeMix::RoundDivide(
    U128 numerator, std::uint64_t denominator) {
  const U128 divisor = static_cast<U128>(denominator);
  std::uint64_t quotient = static_cast<std::uint64_t>(numerator / divisor);
  const U128 remainder = numerator % divisor;
  const U128 twice_remainder = remainder << 1;
  if (twice_remainder > divisor ||
      (twice_remainder == divisor && (quotient & 1) != 0)) {
    ++quotient;
  }
  return quotient;
}

std::uint64_t GammaSafeMix::RoundRatioToWeight(
    U128 numerator, U128 denominator) {
  if (numerator == 0) return 1;
  if (numerator >= denominator) return kWeightTotal - 1;

  U128 remainder = numerator;
  std::uint64_t quotient = 0;
  for (unsigned int bit = 0; bit < 63; ++bit) {
    remainder <<= 1;
    quotient <<= 1;
    if (remainder >= denominator) {
      remainder -= denominator;
      quotient |= 1;
    }
  }

  if (remainder >= numerator) {
    remainder -= numerator;
  } else {
    --quotient;
    remainder = remainder + denominator - numerator;
  }

  const U128 twice_remainder = remainder << 1;
  if (twice_remainder > denominator ||
      (twice_remainder == denominator && (quotient & 1) != 0)) {
    ++quotient;
  }
  if (quotient == 0) return 1;
  if (quotient >= kWeightTotal) return kWeightTotal - 1;
  return quotient;
}

bool GammaSafeMix::MixCount(
    std::uint32_t parent_count,
    std::uint32_t treatment_count,
    std::uint32_t* mixed_count) {
  if (event_pending_ || mixed_count == 0 ||
      !CountsValid(probability_scale_, parent_count, treatment_count)) {
    Fault();
    return false;
  }
  const U128 numerator =
      static_cast<U128>(parent_weight_) * parent_count +
      static_cast<U128>(kWeightTotal - parent_weight_) * treatment_count;
  std::uint64_t mixed = RoundDivide(numerator, kWeightTotal);
  if (mixed == 0) mixed = 1;
  if (mixed >= probability_scale_) mixed = probability_scale_ - 1;
  *mixed_count = static_cast<std::uint32_t>(mixed);
  pending_parent_count_ = parent_count;
  pending_treatment_count_ = treatment_count;
  event_pending_ = true;
  return true;
}

bool GammaSafeMix::Observe(
    bool truth,
    std::uint32_t parent_count,
    std::uint32_t treatment_count) {
  if (!event_pending_ ||
      parent_count != pending_parent_count_ ||
      treatment_count != pending_treatment_count_ ||
      !CountsValid(probability_scale_, parent_count, treatment_count)) {
    Fault();
    return false;
  }
  const std::uint32_t parent_truth =
      truth ? parent_count : probability_scale_ - parent_count;
  const std::uint32_t treatment_truth =
      truth ? treatment_count : probability_scale_ - treatment_count;
  const U128 parent_mass =
      static_cast<U128>(parent_weight_) * parent_truth;
  const U128 treatment_mass =
      static_cast<U128>(kWeightTotal - parent_weight_) * treatment_truth;
  parent_weight_ = RoundRatioToWeight(
      parent_mass, parent_mass + treatment_mass);
  pending_parent_count_ = 0;
  pending_treatment_count_ = 0;
  event_pending_ = false;
  return true;
}

void GammaSafeMix::HashByte(
    std::uint64_t* hash, unsigned char value) {
  *hash ^= value;
  *hash *= UINT64_C(1099511628211);
}

std::uint64_t GammaSafeMix::StateDigest() const {
  std::uint64_t hash = UINT64_C(1469598103934665603);
  for (unsigned int shift = 0; shift < 32; shift += 8) {
    HashByte(
        &hash,
        static_cast<unsigned char>((probability_scale_ >> shift) & 0xff));
  }
  for (unsigned int shift = 0; shift < 64; shift += 8) {
    HashByte(
        &hash,
        static_cast<unsigned char>((parent_weight_ >> shift) & 0xff));
  }
  for (unsigned int shift = 0; shift < 32; shift += 8) {
    HashByte(
        &hash,
        static_cast<unsigned char>((pending_parent_count_ >> shift) & 0xff));
  }
  for (unsigned int shift = 0; shift < 32; shift += 8) {
    HashByte(
        &hash,
        static_cast<unsigned char>((pending_treatment_count_ >> shift) & 0xff));
  }
  HashByte(&hash, event_pending_ ? 1 : 0);
  return hash;
}
