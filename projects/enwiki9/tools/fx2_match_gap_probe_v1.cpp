// GPL-3.0-or-later. Differential original-Match state fixture.
#include <vector>
#include <array>
#include <valarray>
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <algorithm>
#define private public
#include "match.h"
#undef private
#ifdef GAP_OBSERVER
#include "gamma-gap-observer.h"
#endif
void put(uint64_t n,unsigned bytes){for(unsigned i=0;i<bytes;++i)std::putchar((n>>(8*i))&255);}
void state(const Match& m) {
  put(m.history_pos_,8);put(m.cur_match_,8);put(m.cur_byte_,1);put(m.bit_pos_,1);put(m.match_length_,1);
  for(float f:m.predictions_){uint32_t v;std::memcpy(&v,&f,4);put(v,4);}
  for(int c:m.counts_)put(c,4);
  for(unsigned c:m.map_)put(c,4);
}
int main(){
  std::vector<unsigned char> history(128);unsigned long long context=0,longest=0,total=0;
  unsigned int prefix=1;Match model(history,context,prefix,200,0.5f,256,&longest);
#ifdef GAP_OBSERVER
  // Exhaustively compare ring availability against absolute decoded positions.
  gamma_gap::begin();
  for(uint64_t size=4;size<20;++size)for(uint64_t t=0;t<3*size;++t)for(uint64_t c=0;c<size;++c){
    std::vector<unsigned char> h(size);for(unsigned i=0;i<size;++i)h[i]=i;
    gamma_gap::clear();gamma_gap::consider(64,true,c,t,h);
    uint64_t distance=(t%size+size-c)%size;
    bool valid=distance>=3 && distance<=t && distance<size;
    if(bool(gamma_gap::run)!=valid) return 2;
    if(valid&&(gamma_gap::aligned!=(c+1)%size||gamma_gap::shifted!=(c+2)%size))return 3;
  }
  gamma_gap::clear();gamma_gap::consider(63,true,0,8,history);if(gamma_gap::run)return 4;
  gamma_gap::consider(64,false,0,8,history);if(gamma_gap::run)return 5;
  gamma_gap::consider(65,true,0,8,history);unsigned a=gamma_gap::aligned;
  gamma_gap::consider(65,true,1,8,history);if(gamma_gap::aligned!=a)return 6;
  gamma_gap::clear();
#endif
  for(unsigned block=0;block<12;++block)for(unsigned j=0;j<32;++j){
    unsigned byte='A'+j;if(block%3==2&&j==12)byte='!';
    for(int b=7;b>=0;--b){
      int truth=(byte>>b)&1;float p=model.Predict()[0];uint32_t v;std::memcpy(&v,&p,4);put(v,4);
#ifdef GAP_OBSERVER
      gamma_gap::Record record(32768);record.finish(truth);
#endif
      model.Perceive(truth);prefix=prefix*2+truth;
      if(prefix>=256){
        prefix-=256;history[total++%history.size()]=prefix;context=prefix;longest=0;
#ifdef GAP_OBSERVER
        gamma_gap::clear();
#endif
        model.ByteUpdate();prefix=1;
      }
      state(model);put(longest,8);
    }
  }
#ifdef GAP_OBSERVER
  gamma_gap::finish();
#endif
  return std::ferror(stdout)?7:0;
}
