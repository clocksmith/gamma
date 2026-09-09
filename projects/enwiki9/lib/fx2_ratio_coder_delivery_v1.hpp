// Stateless final-Q16 delivery of a decoder-derived residual ratio.
// This supplies no parent predictor, trained model, or arithmetic coder.
#ifndef GAMMA_FX2_RATIO_CODER_DELIVERY_V1_HPP
#define GAMMA_FX2_RATIO_CODER_DELIVERY_V1_HPP
#include <cstdint>
#include <cstring>
#include <limits>

namespace gamma_ratio_delivery {
constexpr uint64_t UNIT = UINT64_C(1) << 45;
using Wide = unsigned __int128;

inline bool units(float value, bool corrected, uint64_t& result) {
  static_assert(sizeof(float)==4 && std::numeric_limits<float>::is_iec559,
                "IEEE binary32 required");
  uint32_t bits; std::memcpy(&bits,&value,4);
  const uint32_t low=corrected ? 0x348637bdU : 0x358637bdU;
  const uint32_t high=corrected ? 0x40800000U : 0x3f800000U;
  if(bits<low || bits>high)return false;
  // Every permitted binary32 value is an integral multiple of2^-45.
  result=uint64_t((bits&0x7fffffU)|0x800000U)<<(((bits>>23)&255)-105);
  return true;
}

inline unsigned rounded_q16(Wide numerator,Wide denominator) {
  // The validated bounds give denominator<2^125. Each doubled remainder
  // and the tie comparison fit128 bits; numerator*65536 need not fit.
  unsigned result=0;
  for(unsigned i=0;i<16;++i) {
    numerator<<=1;result<<=1;
    if(numerator>=denominator){numerator-=denominator;++result;}
  }
  const Wide twice=numerator<<1;
  if(twice>denominator || (twice==denominator && (result&1)))++result;
  return result<1 ? 1 : result>65535 ? 65535 : result;
}

inline bool correct(unsigned parent,unsigned prefix,const uint8_t* vocabulary,
                    const uint64_t* base,const uint64_t* calibrated,unsigned n,
                    unsigned& output) {
  if(parent<1 || parent>65535 || prefix<1 || prefix>255 || n>256)return false;
  if(n==0){output=parent;return true;} // No row before the first modeled byte.
  if(n<2 || !vocabulary || !base || !calibrated)return false;
  unsigned depth=0;
  for(unsigned v=prefix;v>1;v>>=1)++depth;
  const unsigned width=1U<<(8-depth);
  const unsigned start=(prefix-(1U<<depth))*width;
  uint64_t p[2]={},q[2]={};
  for(unsigned i=0;i<n;++i) {
    if((i && vocabulary[i]<=vocabulary[i-1]) || !base[i] || base[i]>UNIT ||
        !calibrated[i] || calibrated[i]>4*UNIT)return false;
    const unsigned v=vocabulary[i];
    if(v>=start && v<start+width) {
      const unsigned bit=v>=start+width/2;
      p[bit]+=base[i];q[bit]+=calibrated[i];
    }
  }
  if(!p[0] || !p[1]){output=parent;return true;}
  const Wide a=Wide(parent)*q[1]*p[0];
  const Wide b=Wide(65536-parent)*p[1]*q[0];
  output=rounded_q16(a,a+b);return true;
}
} // namespace gamma_ratio_delivery
#endif
