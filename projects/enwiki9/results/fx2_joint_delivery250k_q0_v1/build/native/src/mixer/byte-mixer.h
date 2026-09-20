#ifndef BYTE_MIXER_H
#define BYTE_MIXER_H
#include "../models/byte-model.h"
class ByteMixer:public ByteModel {
 public:
  explicit ByteMixer(const std::vector<bool>& vocab);
  void SetProbs(const float* vocab_probs);
};
#endif
