// Paid final-count correction and read-only causal feature observation.
#ifndef GAMMA_FX2_RESIDUAL_PROJECTION_V1_HPP
#define GAMMA_FX2_RESIDUAL_PROJECTION_V1_HPP
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <limits>

namespace gamma_residual {
constexpr std::int64_t Q=65536, S=32768, RADIUS=S/2;
inline void fail(const char* s) {
  std::fprintf(stderr,"Gamma residual projection: %s\n",s); std::_Exit(125);
}
inline unsigned count(unsigned c, int k) {
  if(c==0 || c>=Q || k < -RADIUS || k>RADIUS) fail("invalid count/correction");
  // Round the complete positive count, nearest with ties toward +infinity.
  const std::int64_t den=Q*S;
  const std::int64_t n=std::int64_t(c)*den+std::int64_t(c)*(Q-c)*k;
  const auto out=(n+den/2)/den;
  return unsigned(out<1 ? 1 : out>=Q ? Q-1 : out);
}
inline std::uint64_t project(const float* h) {
  static_assert(sizeof(float)==4 && std::numeric_limits<float>::is_iec559,"binary32 required");
  std::uint64_t packed=0;
  for(unsigned j=0;j<32;++j) {
    double sum=0;
    for(unsigned i=0;i<6;++i) {
      const float v=h[6*j+i];
      if(!std::isfinite(v)) fail("nonfinite hidden coordinate");
      sum=sum+double(v);
    }
    packed |= std::uint64_t(sum>0 ? 1 : sum<0 ? 2 : 0)<<(2*j);
  }
  return packed;
}
struct Features { std::uint64_t packed=0; bool valid=false; };
inline Features& features() { static Features f; return f; }
inline void capture(const float* h) { features()={project(h),true}; }
inline void invalidate() { features()={0,false}; }
class Sink {
 public:
  Sink() {
    const char* p=std::getenv("GAMMA_RESIDUAL_FEATURE_TRACE");
    if(p && *p) { file=std::fopen(p,"wbx"); if(!file) fail("exclusive trace creation failed"); }
  }
  ~Sink() { if(file && std::fclose(file)) fail("trace close failed"); }
  void write(std::uint64_t f,unsigned c,unsigned position,unsigned y,bool valid) {
    if(!file) return;
    unsigned char b[12];
    for(unsigned i=0;i<8;++i) b[i]=static_cast<unsigned char>(f>>(8*i));
    b[8]=c&255; b[9]=c>>8; b[10]=position|(valid?8:0); b[11]=y;
    if(std::fwrite(b,1,sizeof(b),file)!=sizeof(b)) fail("trace write failed");
  }
 private: std::FILE* file=nullptr;
};
inline Sink& sink() { static Sink s; return s; }
inline std::uint64_t& clock() { static std::uint64_t n=0; return n; }
class Record {
 public:
  explicit Record(unsigned c):f(features()),p(c),position(clock()%8) {
    if(!c || c>=Q || (!f.valid && f.packed)) fail("invalid pre-truth state");
  }
  void finish(unsigned y) {
    if(y>1 || done) fail("invalid or repeated observation");
    sink().write(f.packed,p,position,y,f.valid); ++clock(); done=true;
  }
 private: Features f; unsigned p,position; bool done=false;
};
} // namespace gamma_residual
#endif
