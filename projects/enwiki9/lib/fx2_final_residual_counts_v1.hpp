// Synthetic-stage successor: learn residuals of the final parent probability.
// No frontend, model, corpus reader, or arithmetic archive is supplied.
#ifndef GAMMA_FX2_FINAL_RESIDUAL_COUNTS_V1_HPP
#define GAMMA_FX2_FINAL_RESIDUAL_COUNTS_V1_HPP
#include "fx2_ratio_coder_delivery_v1.hpp"
#include <algorithm>
#include <array>
#include <vector>

namespace gamma_final_counts {
class Model {
 public:
  static constexpr uint32_t Q=65536, PRIOR=32*Q, LIMIT=512*Q;
  static constexpr size_t STATE_BYTES=22+255*18;
  bool configure(char arm) {
    if(!valid_arm(arm))return false;
    *this=Model();arm_=arm;configured_=true;return true;
  }
  bool predict(unsigned parent,unsigned& output) {
    if(!configured_ || pending_ || parent<1 || parent>=Q ||
       position_>=(UINT64_C(1)<<63)-1)return false;
    const auto& c=counts_[prefix_-1];
    const uint64_t s1=scale(c.o1,c.e1),s0=scale(c.o0,c.e0);
    const uint64_t a=parent*s1,b=(Q-parent)*s0;
    const unsigned corrected=gamma_ratio_delivery::rounded_q16(a,a+b);
    output=(arm_=='P' || arm_=='K') ? parent : corrected;
    parent_=parent;pending_=true;return true;
  }
  bool observe(unsigned truth) {
    if(!pending_ || truth>1)return false;
    if(arm_!='P') {
      auto& c=counts_[prefix_-1];
      const unsigned label=arm_=='S' ? 1-truth : truth;
      c.e1+=parent_;c.e0+=Q-parent_;
      if(label)c.o1+=Q;else c.o0+=Q;
      if(++c.visits==256) {
        c.o1/=2;c.o0/=2;c.e1/=2;c.e0/=2;c.visits=0;
      }
    }
    prefix_=2*prefix_+truth;if(prefix_>=256)prefix_=1;
    ++position_;parent_=0;pending_=false;return true;
  }
  std::vector<uint8_t> serialize() const {
    std::vector<uint8_t> out{'G','F','C','1'};
    put(out,uint8_t(arm_),1);put(out,configured_,1);put(out,pending_,1);
    put(out,0,1);put(out,position_,8);put(out,prefix_,2);put(out,parent_,4);
    for(const auto& c:counts_) {
      put(out,c.o1,4);put(out,c.e1,4);put(out,c.o0,4);put(out,c.e0,4);
      put(out,c.visits,2);
    }
    return out;
  }
  bool restore(const uint8_t* bytes,size_t size) {
    if(!bytes || size!=STATE_BYTES || std::memcmp(bytes,"GFC1",4) ||
       bytes[5]!=1 || bytes[6]>1 || bytes[7])return false;
    Model next;if(!next.configure(char(bytes[4])))return false;
    if(configured_ && arm_!=next.arm_)return false;
    next.pending_=bytes[6];next.position_=get(bytes+8,8);
    next.prefix_=get(bytes+16,2);next.parent_=get(bytes+18,4);
    if(next.position_>=(UINT64_C(1)<<63) || next.prefix_<1 || next.prefix_>255 ||
       (next.pending_ && (next.parent_<1 || next.parent_>=Q ||
                         next.position_==(UINT64_C(1)<<63)-1)) ||
       (!next.pending_ && next.parent_))return false;
    unsigned depth=0;for(unsigned p=next.prefix_;p>1;p>>=1)++depth;
    if(depth!=next.position_%8)return false;
    for(unsigned i=0;i<255;++i) {
      auto& c=next.counts_[i];const auto* p=bytes+22+18*i;
      c.o1=get(p,4);c.e1=get(p+4,4);c.o0=get(p+8,4);c.e0=get(p+12,4);
      c.visits=get(p+16,2);
      if(c.o1>LIMIT || c.e1>LIMIT || c.o0>LIMIT || c.e0>LIMIT ||
         uint64_t(c.o1)+c.o0>LIMIT || uint64_t(c.e1)+c.e0>LIMIT ||
         c.visits>=256 || (next.arm_=='P' && (c.o1 || c.e1 || c.o0 || c.e0 || c.visits)))return false;
    }
    *this=next;return true;
  }
 private:
  struct Counts {uint32_t o1=0,e1=0,o0=0,e0=0;uint16_t visits=0;};
  std::array<Counts,255> counts_{};
  char arm_='P';bool configured_=false,pending_=false;
  uint64_t position_=0;unsigned prefix_=1,parent_=0;
  static bool valid_arm(char arm){return arm=='P'||arm=='K'||arm=='D'||arm=='S';}
  static uint64_t scale(uint32_t observed,uint32_t expected) {
    return std::max(uint64_t(Q/4),std::min(uint64_t(4*Q),
      uint64_t(PRIOR+observed)*Q/(PRIOR+expected)));
  }
  static void put(std::vector<uint8_t>& out,uint64_t v,unsigned n) {
    for(unsigned i=0;i<n;++i)out.push_back(uint8_t(v>>(8*i)));
  }
  static uint64_t get(const uint8_t* p,unsigned n) {
    uint64_t v=0;for(unsigned i=0;i<n;++i)v|=uint64_t(p[i])<<(8*i);return v;
  }
};
} // namespace gamma_final_counts
#endif
