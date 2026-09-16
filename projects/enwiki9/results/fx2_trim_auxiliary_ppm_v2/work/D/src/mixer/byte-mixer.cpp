#include "byte-mixer.h"
ByteMixer::ByteMixer(const std::vector<bool>& vocab):ByteModel(vocab){}
void ByteMixer::SetProbs(const float* vocab_probs) {
  unsigned int k = 0;
  for (int i = 0; i < 256; ++i) {
    if (vocab_[i]) {
      probs_[i] = vocab_probs[k];
      ++k;
    } else {
      probs_[i] = 0;
    }
  }
  ByteModel::ByteUpdate();
}

