#include "fx2_expert_release_v1.hpp"
#include "fx2_expert_mix_v1.hpp"
#include <cassert>
#include <cstdio>
#include <cstring>
int main(){
  gamma_expert_release::Model release;
  gamma_expert_mix::Model reference('D');
  uint64_t rng=923;
  auto next=[&](){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return rng;};
  for(unsigned t=0;t<100000;++t){
    uint32_t p=1+next()%65535;
    std::array<uint32_t,3> e{uint32_t(1+next()%65535),uint32_t(1+next()%65535),uint32_t(1+next()%65535)};
    bool active=t%17;
    assert(release.predict(p,e,active)==reference.predict(p,e,active));
    unsigned truth=next()%2;
    release.observe(truth);reference.observe(truth);
    auto state=reference.state();
    assert(release.position==reference.position());
    for(unsigned i=0;i<256;++i){
      uint64_t w=0;for(unsigned j=0;j<8;++j)w|=uint64_t(state[8+i*8+j])<<(8*j);
      assert(w==release.weights[i/4][i%4]);
    }
  }
  for(uint32_t p=1;p<65536;++p){
    assert(release.predict(p,{p,p,p},true)==p);release.observe(p&1);
  }
  puts("PASS:100000 differential events and states;65535 identity counts");
}
