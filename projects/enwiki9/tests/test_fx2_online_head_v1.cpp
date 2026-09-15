#include "fx2_online_head_v1.hpp"
#include <cassert>
#include <cstdio>
using namespace gamma_online_head;
int main(){
  Model p('P'),k('K'),d('D'),s('S'),repeat('D');
  std::array<float,D> h{};std::array<float,V> logits{},base{},op{},ok{},od{},os{},orr{};
  base.fill(1.0f/V);
  // A first token has no predecessor distribution, hence no update.
  for(Model* m:{&p,&k,&d,&s,&repeat})m->observe(7);
  assert(d.updates==0);
  uint64_t rng=923;auto next=[&](){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return rng;};
  bool changed=false,control_distinct=false;
  for(unsigned t=0;t<1200;++t){
    if(t%97==0)for(Model* m:{&p,&k,&d,&s,&repeat})m->reset();
    for(auto& x:h)x=float(int(next()%2001)-1000)/128;
    p.predict(h.data(),logits.data(),base.data(),op.data());
    k.predict(h.data(),logits.data(),base.data(),ok.data());
    d.predict(h.data(),logits.data(),base.data(),od.data());
    s.predict(h.data(),logits.data(),base.data(),os.data());
    repeat.predict(h.data(),logits.data(),base.data(),orr.data());
    assert(op==base&&ok==base&&od==orr&&k.state()==d.state());
    changed|=od!=base;control_distinct|=od!=os;
    double total=0;for(auto q:od)total+=q;assert(std::fabs(total-1)<1e-6);
    unsigned truth=next()%V;for(Model* m:{&p,&k,&d,&s,&repeat})m->observe(truth);
    assert(d.state()==repeat.state()&&k.state()==d.state());
    double norm=0;for(auto w:d.weights)norm+=double(w)*w;assert(norm<=16.00001);
  }
  assert(changed&&control_distinct&&d.updates==1200&&p.updates==0);
  for(Model* m:{&p,&k,&d,&s,&repeat})m->reset();
  for(float w:d.weights)assert(w==0);
  Model projected('D');h.fill(0);h[0]=1000000;
  for(unsigned t=0;t<600;++t){
    projected.predict(h.data(),logits.data(),base.data(),od.data());
    projected.observe(0);
    if(t==0){
      assert(std::fabs(projected.weights[0]-0.25*(1-double(base[0])))<1e-7);
      assert(std::fabs(projected.weights[D]+0.25*base[1])<1e-9);
    }
  }
  double norm=0;for(float w:projected.weights)norm+=double(w)*w;
  assert(norm>15.99&&norm<=16.00001);
  puts("PASS:1200 causal events;K/D/repeat complete state;P/K identity;600 forced-projection updates;independent first-step formula;control;reset;missing predecessor");
}
