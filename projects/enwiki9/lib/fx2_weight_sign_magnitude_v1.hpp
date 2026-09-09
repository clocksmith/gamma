// Exact INT4 magnitude/shared-sign model. Preserve inherited GPLv3 provenance.
#pragma once
#include "fx2_weight_format_v1.hpp"
namespace fx2_weights_v1 {
struct SignMagnitudeCounts {
  std::array<uint32_t, 8> magnitude{{1,2,2,2,2,2,2,2}};
  std::array<uint32_t, 2> sign{{1,1}}; // zero: positive; one: negative
  uint32_t magnitude_total = 15, sign_total = 2;
  template<size_t N> static std::array<uint16_t,N> tree(const std::array<uint32_t,N>& row) {
    std::array<uint64_t,2*N> totals{};
    std::array<uint16_t,N> result{};
    for (size_t i=0;i<N;++i) totals[N+i]=row[i];
    result.fill(1024);
    for (size_t i=N-1;i;--i) {
      const uint64_t left=totals[2*i], total=left+totals[2*i+1];
      totals[i]=total;
      require(total>0,"empty magnitude/sign model");
      result[i]=uint16_t(std::clamp<uint64_t>((2048*left+total/2)/total,1,2047));
    }
    return result;
  }
  Bytes state() const {
    Bytes out;
    for (auto n:magnitude) append_u32(out,n);
    for (auto n:sign) append_u32(out,n);
    append_u32(out,magnitude_total);append_u32(out,sign_total);
    return out;
  }
  template<size_t N> static void update(std::array<uint32_t,N>& row,uint32_t& total,unsigned symbol) {
    ++row[symbol];
    if (++total>=65536) {
      total=0;
      for (auto& n:row) {n=(n+1)/2;total+=n;}
    }
  }
  void observe(uint8_t symbol) {
    require(symbol<15,"invalid signed weight");
    const unsigned m=symbol<7 ? 7-symbol : symbol-7;
    update(magnitude,magnitude_total,m);
    if (m) update(sign,sign_total,symbol<7);
  }
};
using SignMagnitudeWitness = void (*)(const SignMagnitudeCounts&,uint8_t);
}
