#include "safe-mix.h"

#include <cstdint>
#include <cstdio>

namespace {

bool IsPoisoned(const GammaSafeMix& mix) {
  return !mix.valid() && !mix.event_pending();
}

bool InvalidInitializationRejected() {
  GammaSafeMix mix;
  return !mix.Reset(2) && IsPoisoned(mix);
}

bool RepeatedResetRejected() {
  GammaSafeMix mix;
  return mix.Reset(4096) && !mix.Reset(4096) && IsPoisoned(mix);
}

bool NestedMixRejected() {
  GammaSafeMix mix;
  std::uint32_t output = 0;
  return mix.Reset(4096) &&
      mix.MixCount(1000, 2000, &output) &&
      !mix.MixCount(1000, 2000, &output) &&
      IsPoisoned(mix);
}

bool ObserveWithoutMixRejected() {
  GammaSafeMix mix;
  return mix.Reset(4096) && !mix.Observe(true, 1000, 2000) && IsPoisoned(mix);
}

bool MismatchedObserveRejected() {
  GammaSafeMix mix;
  std::uint32_t output = 0;
  return mix.Reset(4096) &&
      mix.MixCount(1000, 2000, &output) &&
      !mix.Observe(true, 1001, 2000) &&
      IsPoisoned(mix);
}

bool NullOutputRejected() {
  GammaSafeMix mix;
  return mix.Reset(4096) && !mix.MixCount(1000, 2000, 0) && IsPoisoned(mix);
}

bool InvalidParentCountRejected() {
  GammaSafeMix mix;
  std::uint32_t output = 0;
  return mix.Reset(4096) && !mix.MixCount(0, 2000, &output) && IsPoisoned(mix);
}

bool InvalidTreatmentCountRejected() {
  GammaSafeMix mix;
  std::uint32_t output = 0;
  return mix.Reset(4096) && !mix.MixCount(1000, 4096, &output) && IsPoisoned(mix);
}

bool PendingStateDigestBound() {
  GammaSafeMix mix;
  std::uint32_t output = 0;
  if (!mix.Reset(4096)) return false;
  const std::uint64_t clean = mix.StateDigest();
  if (!mix.MixCount(1234, 1234, &output)) return false;
  const std::uint64_t pending = mix.StateDigest();
  if (pending == clean || !mix.event_pending()) return false;
  if (!mix.Observe(true, 1234, 1234)) return false;
  return !mix.event_pending() && mix.StateDigest() == clean;
}

bool IdentityControlPasses() {
  static const std::uint32_t counts[] = {1, 17, 1024, 2048, 3071, 4095};
  static const bool truths[] = {false, true, false, true, true, false};
  GammaSafeMix mix;
  if (!mix.Reset(4096)) return false;
  for (unsigned int index = 0; index < sizeof(counts) / sizeof(counts[0]); ++index) {
    std::uint32_t output = 0;
    const std::uint64_t weight = mix.parent_weight();
    if (!mix.MixCount(counts[index], counts[index], &output) ||
        output != counts[index] ||
        !mix.Observe(truths[index], counts[index], counts[index]) ||
        mix.parent_weight() != weight ||
        mix.event_pending()) {
      return false;
    }
  }
  return mix.parent_weight() == GammaSafeMix::kInitialParentWeight;
}

}  // namespace

int main() {
  const bool invalid_initialization = InvalidInitializationRejected();
  const bool repeated_reset = RepeatedResetRejected();
  const bool nested_mix = NestedMixRejected();
  const bool observe_without_mix = ObserveWithoutMixRejected();
  const bool mismatched_observe = MismatchedObserveRejected();
  const bool null_output = NullOutputRejected();
  const bool invalid_parent_count = InvalidParentCountRejected();
  const bool invalid_treatment_count = InvalidTreatmentCountRejected();
  const bool pending_state_digest = PendingStateDigestBound();
  const bool identity = IdentityControlPasses();
  const bool all = invalid_initialization && repeated_reset && nested_mix &&
      observe_without_mix && mismatched_observe && null_output &&
      invalid_parent_count && invalid_treatment_count &&
      pending_state_digest && identity;
  std::printf(
      "{\"schema\":\"gamma.enwiki9.safe-mix-negative-controls-receipt.v1\"," 
      "\"candidate_id\":\"gamma_safe_mix_v1\",\"probability_scale\":4096,"
      "\"controls\":{"
      "\"invalid_initialization\":%s,\"repeated_reset\":%s,"
      "\"nested_mix\":%s,\"observe_without_mix\":%s,"
      "\"mismatched_observe\":%s,\"null_output\":%s,"
      "\"invalid_parent_count\":%s,\"invalid_treatment_count\":%s},"
      "\"pending_state_digest_pass\":%s,\"identity_control_pass\":%s,"
      "\"all_controls_pass\":%s,\"execution_authority\":false,"
      "\"archive_authority\":false,\"score_credit_bytes\":0}\n",
      invalid_initialization ? "true" : "false",
      repeated_reset ? "true" : "false",
      nested_mix ? "true" : "false",
      observe_without_mix ? "true" : "false",
      mismatched_observe ? "true" : "false",
      null_output ? "true" : "false",
      invalid_parent_count ? "true" : "false",
      invalid_treatment_count ? "true" : "false",
      pending_state_digest ? "true" : "false",
      identity ? "true" : "false",
      all ? "true" : "false");
  return all ? 0 : 2;
}
