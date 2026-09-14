#include "fx2_expert_mix_v1.hpp"
#include <cassert>
#include <iostream>
using namespace gamma_expert_mix;
static uint64_t get(const std::vector<uint8_t>& b,size_t p,unsigned n=8){
  uint64_t x=0;for(unsigned i=0;i<n;++i)x|=uint64_t(b[p+i])<<(8*i);return x;
}
int main(){
  Model p('P'),k('K'),d('D'),repeat('D'),s('S');
  uint64_t random=17; unsigned changed=0,control=0;
  for(unsigned t=0;t<20000;++t){
    random=random*6364136223846793005ULL+1;
    uint32_t q=1+uint32_t((random>>32)%65535);
    std::array<uint32_t,3> e{Q-q,32768,1+uint32_t((random>>17)%65535)};
    bool active=t%29!=0;
    auto a=p.predict(q,e,active), b=k.predict(q,e,active),c=d.predict(q,e,active);
    assert(a==q && b==q && c==repeat.predict(q,e,active));
    auto z=s.predict(q,e,active);changed+=c!=q;control+=z!=c;
    assert(c>0 && c<Q && z>0 && z<Q);if(!active)assert(c==q && z==q);
    unsigned truth=unsigned(random>>63);
    p.observe(truth);k.observe(truth);d.observe(truth);repeat.observe(truth);s.observe(truth);
    assert(k.state()==d.state() && d.state()==repeat.state());
    auto state=d.state();assert(state.size()==2152 && get(state,0)==t+1);
    for(unsigned context=0;context<64;++context){uint64_t sum=0;
      for(unsigned i=0;i<4;++i){auto w=get(state,8+context*32+i*8);assert(w>0);sum+=w;}assert(sum==W);}
  }
  assert(changed && control);
  // Identity experts leave predictions exact, even after posterior rounding.
  Model identity;
  for(uint32_t q=1;q<Q;++q){assert(identity.predict(q,{q,q,q})==q);identity.observe(q&1);}
  // Recompute the first posterior independently with integer remainders.
  Model exact;uint32_t q=12345;std::array<uint32_t,3> e{60000,400,50000};
  auto answer=exact.predict(q,e);Row prior{W-3*(W/6),W/6,W/6,W/6};
  std::array<uint32_t,4> c{q,(3*q+e[0]+2)/4,(3*q+e[1]+2)/4,(3*q+e[2]+2)/4};
  uint64_t mass=0;for(unsigned i=0;i<4;++i)mass+=prior[i]*c[i];assert(answer==(mass+W/2)/W);
  exact.observe(1);auto state=exact.state();uint64_t floor_sum=0;Row expected{};
  std::array<uint64_t,4> rem{};for(unsigned i=0;i<4;++i){auto numerator=__uint128_t(W-4)*prior[i]*c[i];expected[i]=1+uint64_t(numerator/mass);rem[i]=uint64_t(numerator%mass);floor_sum+=expected[i];}
  for(uint64_t n=floor_sum;n<W;++n){unsigned best=0;for(unsigned i=1;i<4;++i)if(rem[i]>rem[best])best=i;++expected[best];rem[best]=0;}
  for(unsigned i=0;i<4;++i)assert(get(state,8+5*32+i*8)==expected[i]);
  std::cout<<"PASS: 20000 synchronized events, 65535 identity counts, positive conserved weights, delayed-control separation, exact posterior reference\n";
}
