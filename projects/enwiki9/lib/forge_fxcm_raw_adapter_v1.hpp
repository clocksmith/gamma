// Gamma interface adapter for the pinned forge-cmix raw-output model.
// The model, its tables, initialization, and updates remain upstream inputs.
#ifndef GAMMA_FORGE_FXCM_RAW_ADAPTER_V1_HPP
#define GAMMA_FORGE_FXCM_RAW_ADAPTER_V1_HPP
#include <array>

namespace gamma_forge {
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
      if (!(p>0.0f && p<1.0f)) return false;
    }
    next[i]=p;
  }
  // Invalid interfaces leave caller state untouched. This adapter never
  // observes a bit, mutates model state, or reads the neutral legacy Predict().
  for (unsigned i=0;i<n;++i) output[i]=next[i];
  return true;
}
}
#endif
