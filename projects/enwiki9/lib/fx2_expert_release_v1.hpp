// Production realization of the frozen aligned expert mixture.
#ifndef GAMMA_EXPERT_RELEASE_V1_HPP
#define GAMMA_EXPERT_RELEASE_V1_HPP
#include <array>
#include <cstdint>
#include <cstdlib>
namespace gamma_expert_release {
constexpr uint64_t W=uint64_t(1)<<32;
struct Model {
  uint64_t position=0;
  std::array<std::array<uint64_t,4>,64> weights{};
  std::array<uint32_t,4> counts{};
  unsigned context=0;
  bool active=false,pending=false;
  Model(){for(auto& r:weights)r={W-3*(W/6),W/6,W/6,W/6};}
  __attribute__((noinline)) uint32_t predict(uint32_t p,
      const std::array<uint32_t,3>& e,bool enabled) {
    if(pending||!p||p>=65536)std::abort();
    pending=true;active=enabled;context=(position%8)*8;counts[0]=p;
    for(unsigned i=0;i<3;++i){
      if(!e[i]||e[i]>=65536)std::abort();
      context|=unsigned(e[i]>p)<<i;
      counts[i+1]=active?(3*p+e[i]+2)/4:p;
    }
    uint64_t total=0;
    for(unsigned i=0;i<4;++i)total+=weights[context][i]*counts[i];
    return uint32_t((total+W/2)/W);
  }
  __attribute__((noinline)) void observe(unsigned truth){
    if(!pending||truth>1)std::abort();
    if(active){
      auto& row=weights[context];
      uint64_t products[4],remainder[4],total=0,assigned=0;
      for(unsigned i=0;i<4;++i){
        products[i]=row[i]*(truth?counts[i]:65536-counts[i]);
        total+=products[i];
      }
      for(unsigned i=0;i<4;++i){
        __uint128_t scaled=__uint128_t(W-4)*products[i];
        row[i]=1+uint64_t(scaled/total);
        remainder[i]=uint64_t(scaled%total);assigned+=row[i];
      }
      // Each remainder is used at most once. Strict comparison breaks ties
      // toward the lower index, exactly as the frozen reference's sort does.
      unsigned used=0;
      for(uint64_t k=assigned;k<W;++k){
        unsigned best=4;
        for(unsigned i=0;i<4;++i)if(!(used&(1u<<i)) &&
          (best==4||remainder[i]>remainder[best]))best=i;
        if(best==4)std::abort();
        ++row[best];used|=1u<<best;
      }
    }
    ++position;pending=false;
  }
};
inline Model& model(){static Model m;return m;}
inline std::array<uint32_t,3>& features(){static std::array<uint32_t,3> e{};return e;}
inline bool& available(){static bool a=false;return a;}
inline void capture(float a,float b,float c,bool enabled){
  features()={uint32_t(1+65534*a),uint32_t(1+65534*b),uint32_t(1+65534*c)};
  available()=enabled;
}
inline uint32_t predict(uint32_t p){return model().predict(p,features(),available());}
inline void observe(unsigned truth){model().observe(truth);}
}
#endif
