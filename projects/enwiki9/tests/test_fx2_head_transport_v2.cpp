#include "fx2_head_transport_v2.hpp"
#include "../results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/work/src/models/byte-model.h"
#include <cassert>
#include <cstdio>
struct Native:ByteModel {
  explicit Native(const std::vector<bool>& v):ByteModel(v){}
  void load(const float* p){for(unsigned i=0;i<256;++i)probs_[i]=p[i];ByteUpdate();}
};
int main(){
  using gamma_head_transport::transport;
  uint64_t rng=923;auto next=[&](){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return rng;};
  for(uint32_t p=1;p<65536;++p){uint32_t b=1+next()%65535;assert(transport(p,b,b)==p);}
  for(unsigned i=0;i<100000;++i){
    uint32_t p=1+next()%65535,a=1+next()%65535,b=1+next()%65535;
    long double odds=static_cast<long double>(p)/(65536-p)*a/(65536-a)*(65536-b)/b;
    uint64_t expected=uint64_t(65536*odds/(1+odds)+0.5L);
    expected=std::max(uint64_t(1),std::min(uint64_t(65535),expected));
    assert(transport(p,a,b)==expected);
  }
  std::vector<bool> vocab(256,true);std::vector<int> ids(256);for(int i=0;i<256;++i)ids[i]=i;
  // Exercise the real caller's sentinel before the first native Perceive.
  for(char arm: {'P','K','D','S'}) {
    Native first(vocab);gamma_head_transport::Model m(arm);
    const auto prior=m.weights;
    m.capture(0.0f,false);assert(m.predict(1)==1);m.observe(0);first.Perceive(0);
    assert(m.weights==prior);
    for(unsigned i=1;i<8;++i){
      float f=first.Predict()[0];m.capture(f,true);
      assert(m.predict(32768)==32768);m.observe(i%2);first.Perceive(i%2);
    }
  }
  Native native(vocab);gamma_head_transport::Model p('P'),k('K'),d('D');
  std::array<float,256> b{},a{};bool differs=false;
  for(unsigned byte=0;byte<1000;++byte){
    for(unsigned i=0;i<256;++i){b[i]=float(1+next()%65535)/65536;a[i]=float(1+next()%65535)/65536;}
    native.load(b.data());for(auto* m:{&p,&k,&d})m->set(ids,b.data(),a.data());
    for(unsigned bit=0;bit<8;++bit){
      float n=native.Predict()[0];bool active=(byte*8+bit)%29;
      for(auto* m:{&p,&k,&d})m->capture(n,active);
      uint32_t parent=1+next()%65535;
      assert(p.predict(parent)==parent&&k.predict(parent)==parent);
      auto mixed=d.predict(parent);differs|=mixed!=parent;assert(active||mixed==parent);
      unsigned truth=next()%2;for(auto* m:{&p,&k,&d})m->observe(truth);native.Perceive(truth);
      assert(k.state()==d.state());
      for(auto w:d.weights)assert(w[0]>0&&w[1]>0&&w[0]+w[1]==gamma_head_transport::W);
    }
  }
  assert(differs);
  std::printf("PASS:startup sentinel and seven subsequent native bits in all arms;65535 identity counts;100000 independent odds comparisons;8000 native ByteModel prefix comparisons and K/D complete states;posterior/override invariants;state_bytes=%zu\n",d.state().size());
}
