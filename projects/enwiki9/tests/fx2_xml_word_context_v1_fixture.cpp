#include "../lib/fx2_xml_word_context_v1.hpp"
#include "models/indirect.h"
#include "contexts/sparse.h"
#include <cassert>
#include <iostream>

struct States {
  float InitProbability(int x) const { return (x + 1.f) / 257.f; }
  int Next(int state, int bit) const { return (state * 3 + bit + 1) & 255; }
};

int main() {
  const std::vector<std::string> words{"title"};
  std::string raw="<title>"+std::string(4200,'a')+"</title><id>123</id>";
  gamma_xml_word::Context k,d,s,repeat;
  for (auto pair : {std::make_pair(&k,'K'),{&d,'D'},{&s,'S'},{&repeat,'D'}})
    assert(pair.first->begin(words,raw.size(),pair.second));
  std::vector<uint8_t> fields;
  std::string restored;
  gamma_xml_field::Bytes emitted;
  uint64_t kc=0,dc=0,sc=0,rc=0;
  for (size_t i=0; i<=raw.size(); ++i) {
    const uint8_t byte=i ? gamma_xml_field::unswap(uint8_t(raw[i-1])) : 7;
    const uint64_t parent=UINT64_C(0xfefefefefefefefe)*i;
    assert(k.observe(byte,parent,kc,emitted));
    restored.append(emitted.begin(),emitted.end());
    assert(d.observe(byte,parent,dc,emitted));
    assert(s.observe(byte,parent,sc,emitted));
    assert(repeat.observe(byte,parent,rc,emitted));
    assert(kc==parent && dc==rc && d.state()==repeat.state());
    assert(d.field()==k.field() && d.field()==s.field());
    assert(s.delayed()==(i<4096 ? 0 : fields[i-4096]));
    assert(dc==(parent^(uint64_t(d.field())*UINT64_C(0x9e3779b97f4a7c15))));
    assert(sc==(parent^(uint64_t(s.delayed())*UINT64_C(0x9e3779b97f4a7c15))));
    assert(k.state().size()==4204);
    fields.push_back(d.field());
  }
  assert(restored==raw && k.finish() && d.finish() && s.finish() && repeat.finish());
  assert(d.state()==repeat.state());
  assert(!d.observe(1,0,dc,emitted));
  gamma_xml_word::Context invalid;
  assert(!invalid.begin(words,1,'P'));
  assert(!invalid.begin({std::string(4097,'a')},1,'D'));

  // Actual parent Sparse/Indirect implementation: identical random seed and
  // capacity, but K refers to a dedicated scalar. Simulate pretraining and live
  // byte boundaries, proving field-zero predictions and learned map identity.
  States state;
  unsigned bit_context=1;
  std::vector<unsigned long long> recent(8,0);
  Sparse original(recent,{0});
  unsigned long long scalar=0;
  std::vector<unsigned char> pmap(4096,0), kmap(4096,0);
  std::srand(923);
  Indirect<States> parent(state,original.GetContext(),bit_context,200,pmap);
  std::srand(923);
  Indirect<States> bookkeeping(state,scalar,bit_context,200,kmap);
  for (unsigned i=0; i<256; ++i) {
    for (int bit=7; bit>=0; --bit) {
      assert(parent.Predict()[0]==bookkeeping.Predict()[0]);
      parent.Perceive((i>>bit)&1); bookkeeping.Perceive((i>>bit)&1);
      bit_context=2*bit_context+((i>>bit)&1);
    }
    recent[0]=recent[0]*997*16+i;
    original.Update(); scalar=recent[0];
    parent.ByteUpdate(); bookkeeping.ByteUpdate(); bit_context=1;
    assert(pmap==kmap);
  }
  std::cout << "context law, delayed control, replay and native Sparse/Indirect parity pass\n";
}
