#ifndef GAMMA_FX2_HALF_TAIL_V1_HPP
#define GAMMA_FX2_HALF_TAIL_V1_HPP
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace gamma_half_tail {
struct Counts { uint64_t rows=0, subnormal=0, changes=0; };
inline bool apply(unsigned arm, const uint16_t* half, float* p, unsigned n,
                  bool transformer_output, Counts& counts) {
  if(arm>2 || !half || !p || n!=205)return false;
  if(transformer_output) {
    for(unsigned i=n&~7u;i<n;++i) {
      if(half[i]>0 && half[i]<1024) {
        const float corrected=p[i]*2.0f;
        ++counts.subnormal;
        const float before=p[i]<1e-6f?1e-6f:p[i];
        const float after=corrected<1e-6f?1e-6f:corrected;
        counts.changes+=before!=after;
        if(arm==2)p[i]=corrected;
      }
    }
  }
  ++counts.rows;
  return true;
}

class Audit {
  FILE* file_=nullptr;
  bool pending_=false;
  unsigned arm_;
  Counts counts_;
  void record(unsigned char kind,const uint16_t* h,unsigned n) {
    if(!file_)return;
    unsigned char b[421];b[0]=kind;b[1]=n;b[2]=n>>8;
    for(unsigned j=0;j<8;++j)b[3+j]=counts_.rows>>(8*j);
    for(unsigned i=0;i<n;++i){b[11+2*i]=h[i];b[12+2*i]=h[i]>>8;}
    if(std::fwrite(b,1,sizeof(b),file_)!=sizeof(b))std::abort();
  }
 public:
  explicit Audit(unsigned arm):arm_(arm) {
    if(arm>2)std::abort();
    if(const char* path=std::getenv("GAMMA_FX2_HALF_TRACE")) {
      file_=std::fopen(path,"wbx");if(!file_)std::abort();
    }
  }
  ~Audit() {
    if(pending_)std::abort();
    if(file_ && std::fclose(file_))std::abort();
    std::fprintf(stderr,"Gamma half arm=%c rows=%llu subnormal=%llu changes=%llu\n",
      "PKD"[arm_],(unsigned long long)counts_.rows,
      (unsigned long long)counts_.subnormal,(unsigned long long)counts_.changes);
  }
  bool prior(const uint16_t* h,unsigned n) {
    if(pending_ || !h || n!=205)return false;
    record('I',h,n);pending_=true;return true;
  }
  bool output(const uint16_t* h,float* p,unsigned n,bool transformer_output) {
    if(!pending_ || !h || !p || n!=205)return false;
    // Record all pre-conversion half outputs before the treatment writes floats.
    record(transformer_output?'O':'F',h,n);
    if(!apply(arm_,h,p,n,transformer_output,counts_))return false;
    pending_=false;return true;
  }
};
}
#endif
