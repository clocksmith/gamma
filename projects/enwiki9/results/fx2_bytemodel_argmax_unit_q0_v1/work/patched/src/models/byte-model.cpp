#include "byte-model.h"

#include <cstring>
#include <numeric>

namespace {
bool GammaArgmaxBotIsNaN(float value) {
  static_assert(sizeof(float) == sizeof(std::uint32_t), "binary32 required");
  std::uint32_t bits;
  std::memcpy(&bits, &value, sizeof(bits));
  // Inspect bits so a finite-math optimization cannot remove this guard.
  return (bits & 0x7fffffffU) > 0x7f800000U;
}
}  // namespace

#if defined(GAMMA_FX2_ARGMAX_INSTRUMENT) && GAMMA_FX2_ARGMAX_INSTRUMENT
#define GAMMA_ARGMAX_COUNT(field, amount) (gamma_argmax_stats_.field += (amount))
#else
#define GAMMA_ARGMAX_COUNT(field, amount) ((void)0)
#endif

ByteModel::ByteModel(const std::vector<bool>& vocab) : ex(0),top_(255), mid_(0),
    bot_(0),  vocab_(vocab), probs_(1.0 / 256, 256) {}

 std::valarray<float>& ByteModel::Predict()  {
  auto mid = bot_ + ((top_ - bot_) / 2);
  float num = std::accumulate(&probs_[mid + 1], &probs_[top_ + 1], 0.0f);
  float denom = std::accumulate(&probs_[bot_], &probs_[mid + 1], num);
  GAMMA_ARGMAX_COUNT(predict_calls, 1);
  bool gamma_reuse = false;
  if (gamma_argmax_arm_ != GammaArgmaxArm::P) {
    if (gamma_argmax_arm_ == GammaArgmaxArm::C) {
      gamma_argmax_valid_ = false;
      GAMMA_ARGMAX_COUNT(forced_invalidations, 1);
    }
    if (gamma_argmax_valid_ && gamma_argmax_index_ >= bot_ &&
        gamma_argmax_index_ <= top_) {
      GAMMA_ARGMAX_COUNT(nan_bot_checks, 1);
      if (GammaArgmaxBotIsNaN(probs_[bot_])) {
        // Upstream pins ex to bot when its first value is NaN. Rescan exactly.
        GAMMA_ARGMAX_COUNT(nan_bot_fallbacks, 1);
      } else if (gamma_argmax_arm_ == GammaArgmaxArm::D) {
        gamma_reuse = true;
      }
    } else {
      GAMMA_ARGMAX_COUNT(cache_range_misses, 1);
    }
  }
  if (gamma_reuse) {
    ex = gamma_argmax_index_;
    GAMMA_ARGMAX_COUNT(cache_hits, 1);
  } else {
  ex = bot_;
    float max_prob_val = probs_[bot_];
    for (int i = bot_ + 1; i <= top_; i++) {
      if (probs_[i] > max_prob_val) {
        max_prob_val = probs_[i];
        ex = i;
      }
    }
    GAMMA_ARGMAX_COUNT(scans, 1);
    GAMMA_ARGMAX_COUNT(argmax_comparisons, top_ - bot_);
  }
  if (gamma_argmax_arm_ != GammaArgmaxArm::P) {
    gamma_argmax_index_ = ex;
    gamma_argmax_valid_ = true;
  }
  if (denom == 0) outputs_[0] = 0.5;
  else outputs_[0] = num / denom;
  return outputs_;
}

const std::valarray<float>& ByteModel::BytePredict() {
  return probs_;
}

void ByteModel::Perceive(int bit) {
  mid_ = bot_ + ((top_ - bot_) / 2);
  if (bit) {
    bot_ = mid_ + 1;
  } else {
    top_ = mid_;
  }
}

void ByteModel::ByteUpdate() {
  // PPMD still normalizes after this base call; seed only in the next Predict.
  gamma_argmax_valid_ = false;
  GAMMA_ARGMAX_COUNT(byte_updates, 1);
  top_ = 255;
  bot_ = 0;
  for (int i = 0; i < 256; ++i) {
    if (!vocab_[i]) probs_[i] = 0;
  }
}

#undef GAMMA_ARGMAX_COUNT

