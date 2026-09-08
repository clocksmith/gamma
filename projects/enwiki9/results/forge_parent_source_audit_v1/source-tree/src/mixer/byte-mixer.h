#ifndef BYTE_MIXER_H
#define BYTE_MIXER_H

#include <vector>
#include <memory>

#include "../models/byte-model.h"
#include "lstm.h"

class ByteMixer : public ByteModel {
 public:
  ByteMixer(unsigned int num_models, const unsigned int& bit_context,
      const std::vector<bool>& vocab, unsigned int vocab_size, Lstm* lstm);
  void SetInput(int index, float val);
  void ByteUpdate();
  float LastActualProb() const { return last_actual_prob_; }
  bool LastActualInVocab() const { return last_actual_in_vocab_; }

 private:
  std::unique_ptr<Lstm> lstm_;
  const unsigned int& byte_;
  std::valarray<int> byte_map_;
  std::valarray<float> inputs_;
  unsigned int num_models_, vocab_size_, offset_;
  unsigned long long byte_update_count_;
  float last_actual_prob_;
  bool last_actual_in_vocab_;
};

#endif
