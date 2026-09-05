#ifndef BYTE_MODEL_H
#define BYTE_MODEL_H

#include "model.h"

#include <cstdint>
#include <valarray>
#include <vector>

class ByteModel : public Model {
 public:
  virtual ~ByteModel() {}
  ByteModel(const std::vector<bool>& vocab);
  const std::valarray<float>& BytePredict();
   std::valarray<float>& Predict() ;
  void Perceive(int bit);
  int ex;
  // Gamma synthetic gate: P remains the default; codec activation is separate.
  enum class GammaArgmaxArm { P, K, D, C };
  struct GammaArgmaxStats {
    std::uint64_t predict_calls = 0;
    std::uint64_t argmax_comparisons = 0;
    std::uint64_t scans = 0;
    std::uint64_t cache_hits = 0;
    std::uint64_t byte_updates = 0;
    std::uint64_t forced_invalidations = 0;
    std::uint64_t cache_range_misses = 0;
    std::uint64_t nan_bot_checks = 0;
    std::uint64_t nan_bot_fallbacks = 0;
  };
  void GammaSetArgmaxArm(GammaArgmaxArm arm) {
    gamma_argmax_arm_ = arm;
    gamma_argmax_valid_ = false;
  }
  GammaArgmaxArm GammaGetArgmaxArm() const { return gamma_argmax_arm_; }
#if defined(GAMMA_FX2_ARGMAX_INSTRUMENT) && GAMMA_FX2_ARGMAX_INSTRUMENT
  const GammaArgmaxStats& GammaArgmaxCounters() const { return gamma_argmax_stats_; }
#endif
 protected:
  void ByteUpdate();
  int top_, mid_, bot_;
  const std::vector<bool>& vocab_;
  std::valarray<float> probs_;
 private:
  GammaArgmaxArm gamma_argmax_arm_ = GammaArgmaxArm::P;
#if defined(GAMMA_FX2_ARGMAX_INSTRUMENT) && GAMMA_FX2_ARGMAX_INSTRUMENT
  GammaArgmaxStats gamma_argmax_stats_;
#endif
  int gamma_argmax_index_ = -1;
  bool gamma_argmax_valid_ = false;
};

#endif

