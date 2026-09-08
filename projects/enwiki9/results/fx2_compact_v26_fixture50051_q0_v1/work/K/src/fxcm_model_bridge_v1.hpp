// Explicit compile-time model interfaces; the native integration selects P/K/D.
#ifndef GAMMA_FXCM_MODEL_BRIDGE_V1_HPP
#define GAMMA_FXCM_MODEL_BRIDGE_V1_HPP
#include "forge_fxcm_raw_adapter_v2.hpp"
#include <cstdlib>
#include <valarray>

namespace gamma_fxcm_bridge {
// P is the original model type. K copies its floats without recalibration.
template<class Model> class Copy {
  mutable Model model_;
  mutable std::valarray<float> values_;
 public:
  Copy():values_(0.5f,model_.NumOutputs()){}
  unsigned NumOutputs(){return model_.NumOutputs();}
  const std::valarray<float>& Predict() const {
    const auto& source=model_.Predict();
    if(source.size()!=values_.size())std::abort();
    for(unsigned i=0;i<values_.size();++i)values_[i]=source[i];
    return values_;
  }
  void Perceive(int bit){model_.Perceive(bit);}
  void ByteUpdate(){model_.ByteUpdate();}
  const Model& source_model()const{return model_;}
};

// D reads the live raw interface. Its neutral legacy Predict is never called.
template<class Model,unsigned Outputs> class Raw {
  mutable Model model_;
  mutable std::valarray<float> values_;
 public:
  Raw():values_(0.5f,Outputs){}
  unsigned NumOutputs(){return model_.NumOutputs();}
  const std::valarray<float>& Predict() const {
    std::array<float,Outputs> next{};
    if(!gamma_forge_v2::probabilities(model_,Outputs,next.data()))std::abort();
    for(unsigned i=0;i<Outputs;++i)values_[i]=next[i];
    return values_;
  }
  void Perceive(int bit){model_.Perceive(bit);}
  void ByteUpdate(){model_.ByteUpdate();}
  const Model& source_model()const{return model_;}
};
}
#endif
