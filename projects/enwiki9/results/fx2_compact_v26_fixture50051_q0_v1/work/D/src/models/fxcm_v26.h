#ifndef FXCM_V26_H
#define FXCM_V26_H

#include "model.h"
#include <vector>
#include <memory>

namespace fxcmv26 {
  class Predictor{

public:
  Predictor();
  int p() ;
  void update();
  void FreeMemory();
};
}

class FXCMV26 : public Model {
 public:
  FXCMV26();
  const std::valarray<float>& Predict() const;
  const short* RawPredictions() const;
  const unsigned char* PredictionMask() const;
  unsigned int ActivePredictions() const;
  float RawPredictionProbability(short raw) const;
  unsigned int NumOutputs();
  void Perceive(int bit);
  void ByteUpdate() {};
  void FreeMemory();

 private:
  std::unique_ptr<fxcmv26::Predictor> predictor_;
};

#endif
