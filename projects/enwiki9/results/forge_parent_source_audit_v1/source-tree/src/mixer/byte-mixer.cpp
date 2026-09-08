#include "byte-mixer.h"
#include "../profile-timer.h"

#ifndef FX3_BYTE_MIXER_INPUT_SCALE
#define FX3_BYTE_MIXER_INPUT_SCALE 2.0f
#endif
#ifndef FX3_LSTM_TRAIN_MIN_ACTUAL_PROB
#define FX3_LSTM_TRAIN_MIN_ACTUAL_PROB 0.0f
#endif
#ifndef FX3_LSTM_TRAIN_MAX_ACTUAL_PROB
#define FX3_LSTM_TRAIN_MAX_ACTUAL_PROB 1.0f
#endif
#ifndef FX3_LSTM_TRAIN_STRIDE
#define FX3_LSTM_TRAIN_STRIDE 1
#endif
#ifndef FX3_LSTM_TRAIN_OFFSET
#define FX3_LSTM_TRAIN_OFFSET 0
#endif
#ifndef FX3_LSTM_LOWPROB_INPUT_THRESHOLD
#define FX3_LSTM_LOWPROB_INPUT_THRESHOLD 0.0f
#endif
#ifndef FX3_LSTM_LOWPROB_INPUT_SCALE
#define FX3_LSTM_LOWPROB_INPUT_SCALE 1.0f
#endif
#ifndef FX3_LSTM_INPUT_UNIFORM_BLEND
#define FX3_LSTM_INPUT_UNIFORM_BLEND 0.0f
#endif
#ifndef FX3_LSTM_INPUT_CENTER_SCALE
#define FX3_LSTM_INPUT_CENTER_SCALE 1.0f
#endif
static_assert(FX3_LSTM_LOWPROB_INPUT_THRESHOLD >= 0.0f &&
              FX3_LSTM_LOWPROB_INPUT_THRESHOLD <= 1.0f,
              "FX3_LSTM_LOWPROB_INPUT_THRESHOLD must be in [0, 1]");
static_assert(FX3_LSTM_LOWPROB_INPUT_SCALE >= 0.0f,
              "FX3_LSTM_LOWPROB_INPUT_SCALE must be >= 0");
static_assert(FX3_LSTM_INPUT_UNIFORM_BLEND >= 0.0f &&
              FX3_LSTM_INPUT_UNIFORM_BLEND < 1.0f,
              "FX3_LSTM_INPUT_UNIFORM_BLEND must be in [0, 1)");
static_assert(FX3_LSTM_INPUT_CENTER_SCALE >= 0.0f &&
              FX3_LSTM_INPUT_CENTER_SCALE <= 4.0f,
              "FX3_LSTM_INPUT_CENTER_SCALE must be in [0, 4]");
static_assert(FX3_LSTM_TRAIN_MIN_ACTUAL_PROB >= 0.0f &&
              FX3_LSTM_TRAIN_MIN_ACTUAL_PROB <= 1.0f,
              "FX3_LSTM_TRAIN_MIN_ACTUAL_PROB must be in [0, 1]");
static_assert(FX3_LSTM_TRAIN_MAX_ACTUAL_PROB >= 0.0f &&
              FX3_LSTM_TRAIN_MAX_ACTUAL_PROB <= 1.0f,
              "FX3_LSTM_TRAIN_MAX_ACTUAL_PROB must be in [0, 1]");
static_assert(FX3_LSTM_TRAIN_MIN_ACTUAL_PROB <=
              FX3_LSTM_TRAIN_MAX_ACTUAL_PROB,
              "LSTM train probability gate min must be <= max");
#if FX3_LSTM_TRAIN_STRIDE < 1 || FX3_LSTM_TRAIN_STRIDE > 1024
#error "FX3_LSTM_TRAIN_STRIDE must be in [1, 1024]"
#endif
#if FX3_LSTM_TRAIN_OFFSET < 0 || FX3_LSTM_TRAIN_OFFSET >= FX3_LSTM_TRAIN_STRIDE
#error "FX3_LSTM_TRAIN_OFFSET must be in [0, FX3_LSTM_TRAIN_STRIDE)"
#endif

ByteMixer::ByteMixer(unsigned int num_models, const unsigned int& bit_context,
    const std::vector<bool>& vocab, unsigned int vocab_size, Lstm* lstm) :
    ByteModel(vocab), lstm_(lstm), byte_(bit_context), byte_map_(0, 256),
    inputs_(0.0, vocab_size), num_models_(num_models), vocab_size_(vocab_size),
    offset_(0), byte_update_count_(0), last_actual_prob_(1.0f),
    last_actual_in_vocab_(true) {
  for (int i = 0; i < 256; ++i) {
    byte_map_[i] = offset_;
    if (vocab_[i]) ++offset_;
  }
  offset_ = 0;
}

void ByteMixer::SetInput(int index, float val) {
  if (!vocab_[index]) return;
  inputs_[offset_] += val;
  ++offset_;
  if (offset_ == vocab_size_) offset_ = 0;
}

void ByteMixer::ByteUpdate() {
  FX3_PROFILE_SCOPE("byte_mixer.byte_update.total");
  float actual_prob = 0.0f;
  const bool actual_in_vocab = vocab_[byte_];
  if (actual_in_vocab) {
    actual_prob = inputs_[byte_map_[byte_]] / num_models_;
  }
  last_actual_prob_ = actual_prob;
  last_actual_in_vocab_ = actual_in_vocab;
  float input_scale = FX3_BYTE_MIXER_INPUT_SCALE;
  if (actual_in_vocab && FX3_LSTM_LOWPROB_INPUT_THRESHOLD > 0.0f &&
      actual_prob < FX3_LSTM_LOWPROB_INPUT_THRESHOLD) {
    input_scale *= FX3_LSTM_LOWPROB_INPUT_SCALE;
  }
  if (FX3_LSTM_INPUT_UNIFORM_BLEND > 0.0f) {
    const float uniform_mass = static_cast<float>(num_models_) / vocab_size_;
    inputs_ = inputs_ * (1.0f - FX3_LSTM_INPUT_UNIFORM_BLEND) +
        uniform_mass * FX3_LSTM_INPUT_UNIFORM_BLEND;
  }
  const float input_center_scale = FX3_LSTM_INPUT_CENTER_SCALE;
  if (input_center_scale != 1.0f) {
    const float uniform_mass = static_cast<float>(num_models_) / vocab_size_;
    double sum = 0.0;
    for (int i = 0; i < vocab_size_; ++i) {
      const float centered = uniform_mass +
          (inputs_[i] - uniform_mass) * input_center_scale;
      inputs_[i] = centered > 0.0f ? centered : 0.0f;
      sum += inputs_[i];
    }
    if (sum > 0.0) {
      inputs_ *= static_cast<float>(num_models_ / sum);
    }
  }
  inputs_ *= input_scale / num_models_;
  lstm_->SetInput(inputs_);
  inputs_ = 0;
  const bool train_this_byte =
      actual_prob >= FX3_LSTM_TRAIN_MIN_ACTUAL_PROB &&
      actual_prob <= FX3_LSTM_TRAIN_MAX_ACTUAL_PROB &&
      (byte_update_count_ % FX3_LSTM_TRAIN_STRIDE) == FX3_LSTM_TRAIN_OFFSET;
  ++byte_update_count_;
  const auto& output = lstm_->Perceive(byte_map_[byte_], train_this_byte);
  offset_ = 0;
  for (int i = 0; i < 256; ++i) {
    if (vocab_[i]) {
      probs_[i] = output[offset_];
      ++offset_;
    } else {
      probs_[i] = 0;
    }
  }
  offset_ = 0;
  ByteModel::ByteUpdate();
}
