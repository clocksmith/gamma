#include "fx2_closing_replay_v1.hpp"
#include <cassert>
#include <iostream>
#include <string>

// Inputs here are literal stored WRT spelling fragments: L is <, N is >.
static void feed(gamma_closing::Replay& p,const std::string& stored) {
  for(uint8_t c:stored)p.observe(c);
}
static void consume(gamma_closing::Replay& p,const std::string& stored) {
  for(uint8_t c:stored) {
    uint8_t donor=0;assert(p.predict(donor));assert(donor==c);p.observe(c);
  }
}
int main() {
  {
    gamma_closing::Replay p;
    const std::string name(64,'a');feed(p,"L"+name+"NxL/");consume(p,name);
    uint8_t donor=0;assert(!p.predict(donor));p.observe('N');
  }
  {
    gamma_closing::Replay p;
    for(int i=0;i<16;++i)feed(p,"LaN");
    for(int i=0;i<16;++i) {feed(p,"L/");consume(p,"a");p.observe('N');}
    feed(p,"L/");uint8_t donor=0;assert(!p.predict(donor));
  }
  {
    gamma_closing::Replay p;
    std::string name;name+=char(64);name+=char(0xd0);name+=char(0x80);
    feed(p,"L"+name+"NxL/");consume(p,name);p.observe('N');
    feed(p,"LaaN");p.observe(12);p.observe('L');feed(p,"/aaN");
    uint8_t donor=0;assert(!p.predict(donor));
  }
  {
    gamma_closing::Replay a,b;
    feed(a,"LaaaNLinnerNxL/");feed(b,"LbbbNLinnerNxL/");
    uint8_t da=0,db=0;assert(a.predict(da)&&b.predict(db)&&da==db);
    assert(a.state()!=b.state());
    consume(a,"inner");consume(b,"inner");feed(a,"NL/");feed(b,"NL/");
    assert(a.predict(da)&&b.predict(db)&&da=='a'&&db=='b');
  }
  std::cout<<"four boundary groups passed\n";
}
