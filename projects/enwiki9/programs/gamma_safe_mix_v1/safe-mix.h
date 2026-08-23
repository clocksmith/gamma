#ifndef GAMMA_SAFE_MIX_H
#define GAMMA_SAFE_MIX_H

#include <cstdint>

class GammaSafeMix {
 public:
  static const std::uint64_t kWeightTotal = UINT64_C(9223372036854775807);
  static const std::uint64_t kInitialParentWeight =
      UINT64_C(4611686018427387903);

  GammaSafeMix();

  bool Reset(std::uint32_t probability_scale);
  bool MixCount(
      std::uint32_t parent_count,
      std::uint32_t treatment_count,
      std::uint32_t* mixed_count);
  bool Observe(
      bool truth,
      std::uint32_t parent_count,
      std::uint32_t treatment_count);

  bool valid() const { return probability_scale_ >= 3; }
  bool event_pending() const { return event_pending_; }
  std::uint32_t probability_scale() const { return probability_scale_; }
  std::uint64_t parent_weight() const { return parent_weight_; }
  std::uint64_t StateDigest() const;

 private:
  typedef unsigned __int128 U128;

  static bool CountsValid(
      std::uint32_t scale,
      std::uint32_t parent_count,
      std::uint32_t treatment_count);
  static std::uint64_t RoundRatioToWeight(U128 numerator, U128 denominator);
  static std::uint64_t RoundDivide(U128 numerator, std::uint64_t denominator);
  static void HashByte(std::uint64_t* hash, unsigned char value);
  void Fault();

  std::uint32_t probability_scale_;
  std::uint64_t parent_weight_;
  std::uint32_t pending_parent_count_;
  std::uint32_t pending_treatment_count_;
  bool event_pending_;
};

#endif
