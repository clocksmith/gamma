// Causal delivery state. Original expert rows are read-only.
#ifndef GAMMA_FX2_RATIO_CODER_STATE_V1_HPP
#define GAMMA_FX2_RATIO_CODER_STATE_V1_HPP
#include "fx2_residual_ratio_v1.hpp"
#include "fx2_ratio_coder_delivery_v1.hpp"

namespace gamma_ratio_delivery {
class State {
 public:
  bool configure(unsigned n,char arm,const std::vector<int>& vocabulary) {
    if(n<2 || n>256 || vocabulary.size()!=n || (arm!='P' && arm!='K' && arm!='D' && arm!='S'))return false;
    State next;next.n_=n;next.arm_=arm;
    for(unsigned i=0;i<n;++i) {
      if(vocabulary[i]<0 || vocabulary[i]>255 || (i && vocabulary[i]<=vocabulary[i-1]))return false;
      next.vocabulary_[i]=uint8_t(vocabulary[i]);
    }
    if(!next.ratio_.configure(n,arm=='K'?'D':arm))return false;
    *this=next;return true;
  }
  bool predict(const float* original) {
    if(!n_ || !original || ratio_.pending())return false;
    State next=*this;std::array<float,256> corrected{};
    for(unsigned i=0;i<n_;++i) {
      if(!units(original[i],false,next.base_[i]))return false;
      corrected[i]=original[i];
    }
    if(!next.ratio_.predict(corrected.data()))return false;
    for(unsigned i=0;i<n_;++i)
      if(!units(corrected[i],true,next.corrected_[i]))return false;
    next.ready_=true;*this=next;return true;
  }
  bool pending() const { return ratio_.pending(); }
  bool observe(unsigned symbol) { return ready_ && ratio_.observe(symbol); }
  bool final_probability(unsigned parent,unsigned prefix,unsigned& output) const {
    if(!n_ || (ready_ && !ratio_.pending()))return false;
    unsigned candidate=0;
    if(!correct(parent,prefix,vocabulary_.data(),base_.data(),corrected_.data(),ready_?n_:0,candidate))return false;
    // K must compute the shadow even when its returned probability is parent.
    const volatile unsigned witnessed=candidate;
    output=(arm_=='D' || arm_=='S') ? witnessed : parent;
    return true;
  }
  std::vector<uint8_t> serialize() const {
    std::vector<uint8_t> out{'G','R','D','2'};
    put(out,n_,2);put(out,uint8_t(arm_),1);put(out,ready_,1);
    const auto ratio=ratio_.serialize();put(out,ratio.size(),2);
    out.insert(out.end(),ratio.begin(),ratio.end());
    for(unsigned i=0;i<n_;++i) {
      put(out,vocabulary_[i],1);put(out,base_[i],8);put(out,corrected_[i],8);
    }
    return out;
  }
 private:
  unsigned n_=0;char arm_='P';bool ready_=false;
  gamma_ratio::Ratio ratio_;
  std::array<uint8_t,256> vocabulary_{};
  std::array<uint64_t,256> base_{},corrected_{};
  static void put(std::vector<uint8_t>& out,uint64_t x,unsigned bytes) {
    for(unsigned i=0;i<bytes;++i)out.push_back(uint8_t(x>>(8*i)));
  }
};
} // namespace gamma_ratio_delivery
#endif
