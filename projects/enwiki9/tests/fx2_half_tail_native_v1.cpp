#include "../lib/fx2_half_tail_v1.hpp"
#include <array>
#include <cassert>
#include <immintrin.h>

int main() {
  using namespace gamma_half_tail;
  std::array<uint16_t,205> h{};
  std::array<float,205> p{},k{},d{},fallback{};
  Counts pc,kc,dc,fc;
  for(unsigned value=0;value<=0x3c00;++value) {
    h.fill(value);
    for(unsigned i=0;i<205;++i) {
      float exact=_cvtsh_ss(value);
      p[i]=i>=200 && value>0 && value<1024 ? exact*0.5f : exact;
    }
    k=d=fallback=p;
    assert(apply(0,h.data(),p.data(),205,true,pc));
    assert(apply(1,h.data(),k.data(),205,true,kc));
    assert(apply(2,h.data(),d.data(),205,true,dc));
    assert(apply(2,h.data(),fallback.data(),205,false,fc));
    assert(std::memcmp(p.data(),k.data(),sizeof(p))==0);
    assert(std::memcmp(p.data(),fallback.data(),sizeof(p))==0);
    for(unsigned i=0;i<205;++i)assert(d[i]==_cvtsh_ss(value));
  }
  assert(pc.rows==15361 && pc.subnormal==1023*5 && pc.changes==1007*5);
  assert(pc.subnormal==kc.subnormal && pc.subnormal==dc.subnormal);
  assert(pc.changes==kc.changes && pc.changes==dc.changes && fc.changes==0);
  auto saved=p;
  Counts invalid;
  assert(!apply(3,h.data(),p.data(),205,true,invalid));
  assert(!apply(2,nullptr,p.data(),205,true,invalid));
  assert(!apply(2,h.data(),nullptr,205,true,invalid));
  assert(!apply(2,h.data(),p.data(),204,true,invalid));
  assert(invalid.rows==0 && std::memcmp(p.data(),saved.data(),sizeof(p))==0);
  Audit audit(1);
  assert(!audit.output(h.data(),p.data(),205,true));
  assert(!audit.prior(h.data(),204));
  assert(audit.prior(h.data(),205));
  assert(!audit.prior(h.data(),205));
  assert(audit.output(h.data(),p.data(),205,true));
  assert(!audit.output(h.data(),p.data(),205,true));
  std::puts("patterns=15361 parent_copy_exact=1 corrected_tail_exact=1 fallback_exact=1 order_checks=1");
}
