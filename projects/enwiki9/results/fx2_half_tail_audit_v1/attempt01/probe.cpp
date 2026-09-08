#include <cstdint>
#include <cstring>
#include <cstdio>
#include <cassert>
#include <immintrin.h>
float HalfToFloat(uint16_t h) {
  uint32_t sign = (uint32_t)(h & 0x8000) << 16;
  uint32_t exp = (h >> 10) & 0x1F;
  uint32_t mant = h & 0x3FF;
  uint32_t x;
  if (exp == 0) {
    if (mant == 0) {
      x = sign;
    } else {  // subnormal half: normalize
      int e = 0;
      while (!(mant & 0x400)) {
        mant <<= 1;
        ++e;
      }
      mant &= 0x3FF;
      x = sign | ((uint32_t)(112 - e) << 23) | (mant << 13);
    }
  } else if (exp == 31) {
    x = sign | 0x7F800000 | (mant << 13);
  } else {
    x = sign | ((exp + 112) << 23) | (mant << 13);
  }
  float f;
  memcpy(&f, &x, 4);
  return f;
}
float ExactScalar(uint16_t h) {
  uint32_t sign = (uint32_t)(h & 0x8000) << 16;
  uint32_t exp = (h >> 10) & 0x1F;
  uint32_t mant = h & 0x3FF;
  uint32_t x;
  if (exp == 0) {
    if (mant == 0) {
      x = sign;
    } else {  // subnormal half: normalize
      int e = 0;
      while (!(mant & 0x400)) {
        mant <<= 1;
        ++e;
      }
      mant &= 0x3FF;
      x = sign | ((uint32_t)(113 - e) << 23) | (mant << 13);
    }
  } else if (exp == 31) {
    x = sign | 0x7F800000 | (mant << 13);
  } else {
    x = sign | ((exp + 112) << 23) | (mant << 13);
  }
  float f;
  memcpy(&f, &x, 4);
  return f;
}
int main() {
  unsigned changed=0, floor_changed=0;
  for(unsigned h=0;h<=0x3c00;++h) {
    float legacy=HalfToFloat(h), corrected=ExactScalar(h), reference=_cvtsh_ss(h);
    assert(std::memcmp(&corrected,&reference,4)==0);
    if(h>0 && h<1024) { assert(legacy*2==corrected); ++changed; }
    else assert(std::memcmp(&legacy,&corrected,4)==0);
    const float p=legacy<1e-6f?1e-6f:legacy;
    const float q=corrected<1e-6f?1e-6f:corrected;
    if(p!=q)++floor_changed;
  }
  std::printf("{\"probability_patterns\":15361,\"scalar_disagreements\":%u,\"after_floor_disagreements\":%u,\"exact_scalar_matches_f16c\":true}\n",changed,floor_changed);
}
