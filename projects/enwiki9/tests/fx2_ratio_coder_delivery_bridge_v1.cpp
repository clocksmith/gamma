#include "../lib/fx2_ratio_coder_delivery_v1.hpp"
extern "C" {
int delivery_correct(unsigned p,unsigned prefix,const uint8_t* vocabulary,
                     const uint64_t* base,const uint64_t* calibrated,unsigned n) {
  unsigned out=0;
  return gamma_ratio_delivery::correct(p,prefix,vocabulary,base,calibrated,n,out) ? int(out) : -1;
}
uint64_t delivery_units(uint32_t bits,int corrected) {
  float value;std::memcpy(&value,&bits,4);uint64_t out=0;
  return gamma_ratio_delivery::units(value,corrected!=0,out) ? out : 0;
}
}
