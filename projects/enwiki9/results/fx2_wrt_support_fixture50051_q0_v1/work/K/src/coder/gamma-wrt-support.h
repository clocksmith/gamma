#ifndef GAMMA_WRT_SUPPORT_NATIVE_V1_HPP
#define GAMMA_WRT_SUPPORT_NATIVE_V1_HPP
#include <cstdint>
#include <cstdio>
#include <cstdlib>

namespace gamma_wrt_support {
// One encode_text body including its mode byte; the outer TEXT header is paid
// separately by the authenticated GFV1 frontend. No future event length used.
struct State {
  enum Phase { Mode, Neutral, Short, Long, Third, Escape, Disabled };
  unsigned phase=Mode, prefix=1;
  int forced() const {
    if(phase!=Short && phase!=Long && phase!=Third)return -1;
    unsigned length=0;
    for(unsigned n=prefix;n>1;n>>=1)++length;
    const unsigned width=1u<<(7-length);
    const unsigned start=(prefix-(1u<<length))*(width*2);
    const unsigned high=phase==Long?239:207;
    const bool zero=start<=high && start+width-1>=128;
    const bool one=start+width<=high && start+width*2-1>=128;
    if(!zero && !one)std::abort();
    return zero && one ? -1 : int(one);
  }
  bool observe(unsigned bit) {
    if(bit>1)return false;
    int f=forced();if(f>=0 && unsigned(f)!=bit)return false;
    unsigned next=prefix*2+bit;
    if(next<256){prefix=next;return true;}
    unsigned byte=next-256, p=phase;
    if(p==Mode){if(byte!=0 && byte!=7)return false;p=byte?Neutral:Disabled;}
    else if(p==Short || p==Third || p==Escape)p=Neutral;
    else if(p==Long)p=byte>=208?Third:Neutral;
    else if(p==Neutral){if(byte==12)p=Escape;else if(byte>=240)p=Long;else if(byte>=208)p=Short;}
    phase=p;prefix=1;return true;
  }
  bool complete() const {return prefix==1 && (phase==Neutral || phase==Disabled);}
};

class Audit {
  State state_;
  unsigned arm_;
  bool pending_=false;
  FILE* file_=nullptr;
  uint64_t bits_=0, forced_=0, changes_=0;
 public:
  explicit Audit(unsigned arm):arm_(arm) {
    if(arm>2)std::abort();
    if(const char* path=std::getenv("GAMMA_FX2_WRT_TRACE")){
      file_=std::fopen(path,"wbx");if(!file_)std::abort();
    }
  }
  unsigned project(unsigned p) {
    if(pending_ || p<1 || p>65535)std::abort();
    const int f=state_.forced();
    unsigned q=f<0?p:f?65535:1;
    if(file_){
      unsigned words[4]={state_.phase,state_.prefix,p,unsigned(f+1)};
      unsigned char bytes[16];
      for(unsigned i=0;i<4;++i)for(unsigned j=0;j<4;++j)bytes[4*i+j]=words[i]>>(8*j);
      if(std::fwrite(bytes,1,16,file_)!=16)std::abort();
    }
    forced_+=f>=0;changes_+=q!=p;pending_=true;
    return arm_==2?q:p;
  }
  void observe(unsigned bit){
    if(!pending_ || !state_.observe(bit))std::abort();
    ++bits_;pending_=false;
  }
  ~Audit(){
    if(pending_ || !state_.complete())std::abort();
    if(file_ && std::fclose(file_))std::abort();
    std::fprintf(stderr,"Gamma WRT arm=%c bits=%llu forced=%llu changes=%llu\n","PKD"[arm_],
      (unsigned long long)bits_,(unsigned long long)forced_,(unsigned long long)changes_);
  }
};
#ifdef GAMMA_FXCM_ARM
inline Audit& audit(){static Audit instance(GAMMA_FXCM_ARM);return instance;}
#endif
}
#endif
