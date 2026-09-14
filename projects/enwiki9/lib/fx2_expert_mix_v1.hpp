// Decoder-synchronized posterior mixture over the unchanged FX2 predictor.
#ifndef GAMMA_FX2_EXPERT_MIX_V1_HPP
#define GAMMA_FX2_EXPERT_MIX_V1_HPP
#include <array>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

namespace gamma_expert_mix {
constexpr uint32_t Q=65536;
constexpr uint64_t W=uint64_t(1)<<32;
using Row=std::array<uint64_t,4>;
inline void require(bool ok) { if (!ok) std::abort(); }

class Model {
 public:
  explicit Model(char arm='D'): arm_(arm) {
    require(arm=='P'||arm=='K'||arm=='D'||arm=='S');
    for(auto& row:weights_) row={W-3*(W/6),W/6,W/6,W/6};
  }
  uint32_t predict(uint32_t parent, std::array<uint32_t,3> expert, bool active=true) {
    require(!pending_ && parent>0 && parent<Q);
    for(auto x:expert) require(x>0 && x<Q);
    pending_=true; active_=active; current_=expert;
    unsigned bit=unsigned(position_%8);
    if(arm_=='S') {
      if(position_<8) expert={parent,parent,parent};
      else expert=delayed_[bit];
    }
    context_=bit*8;
    counts_[0]=parent;
    for(unsigned i=0;i<3;++i) {
      context_ |= unsigned(expert[i]>parent)<<i;
      counts_[i+1]=(3*parent+expert[i]+2)/4;
    }
    if(!active_) counts_.fill(parent);
    uint64_t sum=0;
    for(unsigned i=0;i<4;++i) sum+=weights_[context_][i]*counts_[i];
    uint32_t mixed=uint32_t((sum+W/2)/W);
    require(mixed>0 && mixed<Q);
    return arm_=='D'||arm_=='S' ? mixed : parent;
  }
  void observe(unsigned truth) {
    require(pending_ && truth<2);
    if(active_ && arm_!='P') {
      auto& row=weights_[context_];
      std::array<uint64_t,4> products{},remainders{};
      uint64_t total=0,assigned=0;
      for(unsigned i=0;i<4;++i) {
        products[i]=row[i]*(truth ? counts_[i] : Q-counts_[i]);
        total+=products[i];
      }
      for(unsigned i=0;i<4;++i) {
        __uint128_t scaled=__uint128_t(W-4)*products[i];
        row[i]=1+uint64_t(scaled/total);
        remainders[i]=uint64_t(scaled%total); assigned+=row[i];
      }
      std::array<unsigned,4> order{0,1,2,3};
      std::sort(order.begin(),order.end(),[&](unsigned a,unsigned b){
        return remainders[a]!=remainders[b] ? remainders[a]>remainders[b] : a<b;
      });
      require(assigned<=W && W-assigned<4);
      for(unsigned i=0;i<W-assigned;++i) ++row[order[i]];
    }
    delayed_[position_%8]=current_; ++position_; pending_=false;
  }
  // Explicit byte order, no struct padding, no arm tag: K and D can be compared.
  std::vector<uint8_t> state() const {
    require(!pending_);
    std::vector<uint8_t> out;
    auto put=[&](uint64_t x,unsigned n){for(unsigned j=0;j<n;++j)out.push_back(uint8_t(x>>(8*j)));};
    put(position_,8);
    for(const auto& row:weights_) for(auto w:row)put(w,8);
    for(const auto& row:delayed_) for(auto c:row)put(c,4);
    return out;
  }
  uint64_t position() const {return position_;}
 private:
  char arm_; bool pending_=false,active_=false;
  uint64_t position_=0; unsigned context_=0;
  std::array<Row,64> weights_{};
  std::array<std::array<uint32_t,3>,8> delayed_{};
  std::array<uint32_t,3> current_{};
  std::array<uint32_t,4> counts_{};
};

inline Model& model() {
  static Model instance([](){const char* s=std::getenv("GAMMA_FX2_EXPERT_ARM");
    require(s && s[0] && !s[1]);return s[0];}());
  return instance;
}
inline std::array<uint32_t,3>& features() {static std::array<uint32_t,3> a{32768,32768,32768};return a;}
inline bool& available() {static bool a=false;return a;}
inline uint32_t quantize(float p) {require(p>=0 && p<=1);return uint32_t(1+65534*p);}
inline void capture(float ppm,float neural,float fxcm,bool active) {
  features()={quantize(ppm),quantize(neural),quantize(fxcm)};available()=active;
}
inline uint32_t predict(uint32_t p) {return model().predict(p,features(),available());}
class Audit {
 public:
  Audit() {const char* p=std::getenv("GAMMA_FX2_EXPERT_TRACE");if(p&&*p){f_=std::fopen(p,"wbx");require(f_);}}
  ~Audit(){if(f_){write();require(std::fclose(f_)==0);}}
  void write(){if(f_){auto a=model().state();require(std::fwrite(a.data(),1,a.size(),f_)==a.size());}}
 private: std::FILE* f_=nullptr;
};
inline Audit& audit(){static Audit sink;return sink;}
inline void observe(unsigned bit) {
  model().observe(bit);
  if(model().position()%2048==0) audit().write();
}
inline void finish(){audit().write();}
} // namespace gamma_expert_mix
#endif
