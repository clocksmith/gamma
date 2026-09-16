// Optional observation only; disabled observation never supplies model input.
#pragma once
#include "gamma-final-bit-head.h"
#include <cstdio>
#include <x86intrin.h>
namespace gamma_final_bit_head {
constexpr unsigned V = 205;
namespace sha_blocks {
#pragma GCC push_options
#pragma GCC target("sha,ssse3,sse4.1")
#include "gamma-observer-sha.c"
#pragma GCC pop_options
}
inline std::array<uint8_t,32> digest(const std::vector<uint8_t>& input){
  require(__builtin_cpu_supports("sha")&&__builtin_cpu_supports("ssse3")&&__builtin_cpu_supports("sse4.1"));
  std::array<uint32_t,8> s{0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
  size_t full=input.size()&~size_t(63);if(full)sha_blocks::sha256_process_x86(s.data(),input.data(),uint32_t(full));
  std::array<uint8_t,128> tail{};size_t remaining=input.size()-full;
  if(remaining)std::memcpy(tail.data(),input.data()+full,remaining);
  tail[remaining]=0x80;size_t padded=remaining<56?64:128;uint64_t bits=uint64_t(input.size())*8;
  for(unsigned i=0;i<8;++i)tail[padded-1-i]=uint8_t(bits>>(8*i));
  sha_blocks::sha256_process_x86(s.data(),tail.data(),uint32_t(padded));
  std::array<uint8_t,32> out{};for(unsigned i=0;i<32;++i)out[i]=uint8_t(s[i/4]>>(24-8*(i%4)));
  return out;
}
class Audit {
 public:
  Model& model;
  FILE *state_file=nullptr,*base_file=nullptr;
  std::vector<uint8_t> block;
  uint64_t base_events=0;
  explicit Audit(Model& m):model(m){
    if(const char* p=std::getenv("GAMMA_FX2_FINAL_BIT_STATE")){state_file=std::fopen(p,"wbx");require(state_file);}
    if(const char* p=std::getenv("GAMMA_FX2_FINAL_BIT_BASE")){base_file=std::fopen(p,"wbx");require(base_file);}
  }
  ~Audit(){
    if(base_file){flush_base();require(std::fclose(base_file)==0);}
    if(state_file){write_state();require(std::fclose(state_file)==0);}
  }
  void write_state(){if(state_file){auto bytes=model.state();require(std::fwrite(bytes.data(),1,bytes.size(),state_file)==bytes.size());}}
  void after_observe(){if(model.position%16384==0)write_state();}
  void base(const float* features,const float* logits){
    if(!base_file)return;
    for(unsigned k=0;k<D+V;++k){uint32_t x;float f=k<D?features[k]:logits[k-D];std::memcpy(&x,&f,4);for(unsigned j=0;j<4;++j)block.push_back(uint8_t(x>>(8*j)));}
    ++base_events;if(base_events%1024==0)flush_base();
  }
  void flush_base(){
    if(block.empty())return;
    uint8_t count[8];for(unsigned j=0;j<8;++j)count[j]=uint8_t(base_events>>(8*j));
    auto h=digest(block);require(std::fwrite(count,1,8,base_file)==8 && std::fwrite(h.data(),1,32,base_file)==32);block.clear();
  }
};
}

namespace gamma_final_bit_head {
inline Model& model() {
  static Model m([](){
    const char* p=std::getenv("GAMMA_FX2_FINAL_BIT_ARM");
    require(p && p[0] && !p[1]); return p[0];
  }());
  return m;
}
inline Audit& audit() { static Audit a(model()); return a; }
inline void capture(const float* h, const float* logits) {
  audit().base(h,logits); model().capture(h);
}
inline void reset_article() { model().reset_article(); }
inline void invalidate() { model().invalidate_feature(); }
inline uint32_t predict(uint32_t p) { (void)audit(); return model().predict(p); }
inline void observe(unsigned y) { model().observe(y); audit().after_observe(); }
}
