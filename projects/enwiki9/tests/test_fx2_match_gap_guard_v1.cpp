// GPL-3.0-or-later. Independent chronological reference for the sealed guard.
#include "../lib/fx2_match_gap_observer_v1.hpp"
#include <algorithm>
#include <cstdio>
int main() {
  gamma_gap::enabled=true;
  unsigned long long cases=0;
  for(unsigned h=4;h<=48;++h) for(unsigned total=0;total<4*h;++total) {
    // Store actual preceding positions, then locate the cursor by enumeration.
    std::vector<unsigned char> history(h,0xee);
    for(unsigned position=0;position<total;++position)history[position%h]=position%251;
    std::vector<unsigned> past;
    for(unsigned position=0;position<total;++position)
      if(total-position<h)past.push_back(position);
    for(unsigned cursor=0;cursor<h;++cursor) {
      bool expected=false;unsigned a=0,s=0;
      for(unsigned position:past)if(position%h==cursor && position+2<total) {
        expected=true;a=(position+1)%251;s=(position+2)%251;
      }
      gamma_gap::clear();gamma_gap::consider(80,true,cursor,total,history);
      if(bool(gamma_gap::run)!=expected || (expected && (gamma_gap::aligned!=a || gamma_gap::shifted!=s)))return 1;
      ++cases;
    }
  }
  std::printf("{\"status\":\"passed\",\"chronological_reference_cases\":%llu}\n",cases);
}
