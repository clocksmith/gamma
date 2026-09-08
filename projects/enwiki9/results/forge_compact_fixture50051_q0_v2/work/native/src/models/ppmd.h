#ifndef PPMD_H
#define PPMD_H

#include "byte-model.h"

#ifndef FX3_ENABLE_CMIX_LEX_PPMD_PREDICT
#define FX3_ENABLE_CMIX_LEX_PPMD_PREDICT 0
#endif
#if FX3_ENABLE_CMIX_LEX_PPMD_PREDICT != 0 && \
    FX3_ENABLE_CMIX_LEX_PPMD_PREDICT != 1
#error "FX3_ENABLE_CMIX_LEX_PPMD_PREDICT must be 0 or 1"
#endif

#if FX3_ENABLE_CMIX_LEX_PPMD_PREDICT
#include <array>
#endif
#include <memory>
#if FX3_ENABLE_CMIX_LEX_PPMD_PREDICT
#include <vector>
#endif

namespace PPMD {

struct ppmd_Model;

class PPMD : public ByteModel {
 public:
  PPMD(int order, int memory, const unsigned int& bit_context,
      const std::vector<bool>& vocab);
  ~PPMD();
#if FX3_ENABLE_CMIX_LEX_PPMD_PREDICT
  std::valarray<float>& Predict();
  void Perceive(int bit);
#endif
  void ByteUpdate();
 private:
  const unsigned int& byte_;
  std::unique_ptr<ppmd_Model> ppmd_model_;
  std::valarray<int> byte_map_;
#if FX3_ENABLE_CMIX_LEX_PPMD_PREDICT
  std::array<unsigned int, 256> tree_zero_;
  std::array<unsigned int, 256> tree_total_;
  std::vector<unsigned char> disabled_bytes_;
  unsigned int tree_context_ = 1;
  bool vocab_full_ = false;
#endif
};

} // namespace PPMD

#endif
