#include "../lib/fx2_ratio_coder_state_v1.hpp"
using gamma_ratio_delivery::State;
extern "C" {
void* state_new(unsigned n,char arm,const int* vocabulary) {
  if(!vocabulary || n>256)return nullptr;
  State* s=new State;
  if(!s->configure(n,arm,std::vector<int>(vocabulary,vocabulary+n))){delete s;return nullptr;}
  return s;
}
void state_delete(void* p){delete static_cast<State*>(p);}
int state_predict(void* p,const uint32_t* bits) {
  float row[256];std::memcpy(row,bits,sizeof(row));
  return static_cast<State*>(p)->predict(row);
}
int state_observe(void* p,unsigned symbol){return static_cast<State*>(p)->observe(symbol);}
int state_correct(void* p,unsigned parent,unsigned prefix) {
  unsigned out=0;return static_cast<State*>(p)->final_probability(parent,prefix,out)?int(out):-1;
}
unsigned state_save(void* p,uint8_t* out) {
  auto bytes=static_cast<State*>(p)->serialize();std::memcpy(out,bytes.data(),bytes.size());return bytes.size();
}
}
