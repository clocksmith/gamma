#pragma once
// Observation only: raw FP32 neural truth probability and final Q16 coder input.
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

namespace gamma_trajectory {
inline FILE *bits_file=nullptr,*neural_file=nullptr,*tokens_file=nullptr,*priors_file=nullptr;
inline uint64_t bits=0,rows=0;
inline std::array<float,205> next{};
inline bool ready=false,active=false;
inline void check(bool ok){if(!ok){std::fprintf(stderr,"trajectory capture invariant\n");std::abort();}}
inline void write(FILE* f,const void* p,size_t n){check(f&&std::fwrite(p,1,n,f)==n);}
inline void begin(){
  check(!active);const char* p=std::getenv("GAMMA_ATTRIBUTION_CAPTURE");check(p&&*p);
  std::string prefix=p;
  bits_file=std::fopen((prefix+".bits").c_str(),"wbx");
  neural_file=std::fopen((prefix+".neural").c_str(),"wbx");
  tokens_file=std::fopen((prefix+".tokens").c_str(),"wbx");
  priors_file=std::fopen((prefix+".priors").c_str(),"wbx");
  check(bits_file&&neural_file&&tokens_file&&priors_file);active=true;bits=rows=0;ready=false;
}
inline void bit(unsigned p,unsigned truth){
  check(active&&p>0&&p<65536&&truth<2);
  const uint8_t data[3]={uint8_t(p),uint8_t(p>>8),uint8_t(truth)};write(bits_file,data,3);++bits;
}
inline void row(unsigned token,unsigned marker,const uint16_t* prior){
  check(active&&token<205&&marker<3&&bits==8*(rows+1));
  const float probability=ready?next[token]:0.f;
  check(!ready||(std::isfinite(probability)&&probability>0&&probability<=1));
  uint8_t data[16]={};
  for(unsigned j=0;j<8;++j)data[j]=uint8_t(rows>>(8*j));
  data[8]=uint8_t(token);data[9]=uint8_t(marker);data[10]=ready;
  uint32_t raw;static_assert(sizeof(probability)==4);std::memcpy(&raw,&probability,4);
  for(unsigned j=0;j<4;++j)data[12+j]=uint8_t(raw>>(8*j));
  write(neural_file,data,16);write(tokens_file,data+8,2);
  uint8_t halves[410];for(unsigned j=0;j<205;++j){halves[2*j]=uint8_t(prior[j]);halves[2*j+1]=uint8_t(prior[j]>>8);}
  write(priors_file,halves,410);++rows;
}
inline void publish(const float* probabilities){
  check(active);if(!probabilities){ready=false;return;}
  std::memcpy(next.data(),probabilities,205*sizeof(float));ready=true;
}
inline void end(){
  check(active&&rows&&bits==8*rows);
  for(FILE* f:{bits_file,neural_file,tokens_file,priors_file})check(std::fclose(f)==0);
  bits_file=neural_file=tokens_file=priors_file=nullptr;active=ready=false;
}
}
