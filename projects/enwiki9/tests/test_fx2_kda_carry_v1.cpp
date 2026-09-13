#include "../lib/fx2_kda_carry_v1.hpp"
#include <cassert>
#include <cstdint>

struct alignas(64) State {
  float S[3][4096];
  float ring[3][4][192];
  uint32_t pos;
  uint32_t padding[15];
};
int main() {
  State original{};
  for (unsigned h=0; h<3; ++h)
    for (unsigned i=0; i<4096; ++i) original.S[h][i]=float(h*4096+i+1);
  std::memset(original.ring, 1, sizeof(original.ring)); original.pos=917;
  State p=original,k=original,d=original,s=original;
  gamma_kda_carry::reset(p,'P');gamma_kda_carry::reset(k,'K');
  assert(std::memcmp(&p,&k,sizeof(p))==0);
  State zero{};assert(std::memcmp(&p,&zero,sizeof(p))==0);
  gamma_kda_carry::reset(d,'D');gamma_kda_carry::reset(s,'S');
  for(unsigned h=0;h<3;++h) for(unsigned i=0;i<64;++i) for(unsigned j=0;j<64;++j) {
    assert(d.S[h][i*64+j]==original.S[h][i*64+j]/16);
    assert(s.S[h][i*64+j]==d.S[h][i*64+(j+1)%64]);
  }
  assert(d.pos==0 && s.pos==0);
  assert(std::memcmp(d.ring,zero.ring,sizeof(d.ring))==0);
  assert(std::memcmp(s.ring,zero.ring,sizeof(s.ring))==0);
  State repeated=original;gamma_kda_carry::reset(repeated,'D');
  assert(std::memcmp(&d,&repeated,sizeof(d))==0);
  gamma_kda_carry::reset(zero,'D');assert(std::memcmp(&p,&zero,sizeof(p))==0);
  gamma_kda_carry::reset(d,'D');
  assert(d.S[2][4095]==original.S[2][4095]/256);
  std::puts("PASS: P/K identity; fixed carry; rotated values; cold zero; ring/clock reset; deterministic repeated and chained reset");
}
