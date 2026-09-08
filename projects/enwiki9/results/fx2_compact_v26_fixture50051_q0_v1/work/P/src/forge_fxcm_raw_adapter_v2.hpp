// Preserve upstream model probabilities, including endpoints accepted by FX2.
#ifndef GAMMA_FORGE_FXCM_RAW_ADAPTER_V2_HPP
#define GAMMA_FORGE_FXCM_RAW_ADAPTER_V2_HPP
#include <array>

namespace gamma_forge_v2 {
template<class Model>
bool probabilities(Model& model, unsigned expected_outputs, float* output) {
  const unsigned n=model.NumOutputs(), active=model.ActivePredictions();
  if (!output || !n || n>560 || n!=expected_outputs || active>n) return false;
  const short* raw=model.RawPredictions();
  if (active && !raw) return false;
  std::array<float,560> next{};
  for (unsigned i=0;i<n;++i) {
    float p=0.5f;
    if (i<active) {
      if (raw[i]<-2047 || raw[i]>2047) return false;
      p=model.RawPredictionProbability(raw[i]);
      // These are mixer inputs, not arithmetic-coder frequency counts.
      // FX2's sigmoid table handles both endpoints. NaN still fails closed.
      if (!(p>=0.0f && p<=1.0f)) return false;
    }
    next[i]=p;
  }
  for (unsigned i=0;i<n;++i) output[i]=next[i];
  return true;
}
}
#endif
