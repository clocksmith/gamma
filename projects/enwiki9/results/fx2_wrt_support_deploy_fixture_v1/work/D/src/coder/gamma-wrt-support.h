#ifndef GAMMA_WRT_SUPPORT_DEPLOY_V1_HPP
#define GAMMA_WRT_SUPPORT_DEPLOY_V1_HPP
#include <cstdlib>
namespace gamma_wrt_support {
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
class Coder {
  State state_;
  bool pending_=false;
 public:
  unsigned project(unsigned p){
    if(pending_ || p<1 || p>65535)std::abort();
    int f=state_.forced();pending_=true;
    return f<0?p:f?65535:1;
  }
  void observe(unsigned bit){
    if(!pending_ || !state_.observe(bit))std::abort();
    pending_=false;
  }
  ~Coder(){if(pending_ || !state_.complete())std::abort();}
};
inline Coder& coder(){static Coder value;return value;}
}
#endif
