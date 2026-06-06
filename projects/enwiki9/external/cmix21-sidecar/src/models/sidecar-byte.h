#ifndef SIDECAR_BYTE_H
#define SIDECAR_BYTE_H

#include "byte-model.h"

#include <algorithm>
#include <initializer_list>
#include <vector>

class SidecarByteModel : public ByteModel {
 public:
  SidecarByteModel(const unsigned int& byte, const std::vector<bool>& vocab,
      std::initializer_list<const unsigned long long*> contexts,
      unsigned int rows)
      : ByteModel(vocab),
        byte_(byte),
        contexts_(contexts),
        rows_(rows),
        row_mask_(rows - 1),
        counts_(contexts_.size() * rows * 256, 0),
        totals_(contexts_.size() * rows, 0),
        last_rows_(contexts_.size(), 0) {
    for (unsigned int i = 0; i < contexts_.size(); ++i) {
      last_rows_[i] = RowFor(i);
    }
  }

  void ByteUpdate() {
    for (unsigned int i = 0; i < contexts_.size(); ++i) {
      UpdateRow(i, last_rows_[i], byte_);
      last_rows_[i] = RowFor(i);
    }
    BuildPrediction();
    ByteModel::ByteUpdate();
    float sum = probs_.sum();
    if (sum > 0) probs_ /= sum;
  }

 private:
  unsigned int RowFor(unsigned int table) const {
    unsigned long long x = *contexts_[table];
    x ^= (x >> 33);
    x *= 0xff51afd7ed558ccdULL;
    x ^= (x >> 33);
    x *= 0xc4ceb9fe1a85ec53ULL;
    x ^= (x >> 33);
    x += 0x9e3779b97f4a7c15ULL * (table + 1);
    return (unsigned int)x & row_mask_;
  }

  void UpdateRow(unsigned int table, unsigned int row, unsigned int c) {
    unsigned int key = table * rows_ + row;
    unsigned int base = key * 256;
    if (totals_[key] >= 4096) {
      unsigned int total = 0;
      for (unsigned int i = 0; i < 256; ++i) {
        counts_[base + i] = (counts_[base + i] + 1) >> 1;
        total += counts_[base + i];
      }
      totals_[key] = total;
    }
    if (counts_[base + c] < 65535) {
      ++counts_[base + c];
      ++totals_[key];
    }
  }

  void BuildPrediction() {
#ifndef SIDECAR_BYTE_PRIOR
#define SIDECAR_BYTE_PRIOR 1.0f
#endif
    probs_ = SIDECAR_BYTE_PRIOR;
    for (unsigned int table = 0; table < contexts_.size(); ++table) {
      unsigned int key = table * rows_ + last_rows_[table];
      unsigned int total = totals_[key];
      if (total == 0) continue;
      float confidence = std::min(total, 2048u) * (1.0f / 2048.0f);
      float denom = 256.0f / (total + 256.0f);
      unsigned int base = key * 256;
      for (unsigned int c = 0; c < 256; ++c) {
        probs_[c] += confidence * (counts_[base + c] + 1) * denom;
      }
    }
  }

  const unsigned int& byte_;
  std::vector<const unsigned long long*> contexts_;
  unsigned int rows_, row_mask_;
  std::vector<unsigned short> counts_;
  std::vector<unsigned int> totals_, last_rows_;
};

#endif
