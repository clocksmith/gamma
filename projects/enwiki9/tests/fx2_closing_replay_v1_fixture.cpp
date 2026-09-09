#include "fx2_closing_replay_v1.hpp"
#include <cassert>
#include <iostream>
#include <string>

static uint8_t swap(uint8_t c) {
  if(c>='{'&&c<127)c-=43; else if(c>='P'&&c<'T')c+=43;
  else if((c>=':'&&c<='?')||(c>='J'&&c<='O'))c^=0x70;
  if(c=='X'||c=='`')c^='X'^'`';
  return c;
}
struct Outcome { std::string donors; unsigned trials=0,correct=0; uint64_t hash=14695981039346656037ULL; };
static Outcome scan(const std::string& raw) {
  gamma_closing::Replay a,b;
  Outcome out;
  for(uint8_t truth:raw) {
    uint8_t pa=0,pb=0;
    const bool active=a.predict(pa);
    assert(active==b.predict(pb));
    assert(!active||pa==pb);
    if(active) { ++out.trials; out.correct+=pa==swap(truth); out.donors+=char(swap(pa)); }
    a.observe(swap(truth)); b.observe(swap(truth));
    assert(a.state()==b.state());
    assert(a.state().size()==1124);
    for(auto c:a.state()) { out.hash^=c; out.hash*=1099511628211ULL; }
  }
  return out;
}
int main(int argc,char** argv) {
  assert(argc==2);
  std::string test=argv[1]; Outcome o;
  if(test=="causality") {
    gamma_closing::Replay p; uint8_t donor=0;
    for(uint8_t c:std::string("<title>x<")) { assert(!p.predict(donor)); p.observe(swap(c)); }
    assert(!p.predict(donor));
    p.observe('/'); assert(p.predict(donor)&&donor=='t');
    o=scan("<title>x</title>"); assert(o.trials==5&&o.correct==5&&o.donors=="title");
  } else if(test=="nested") {
    o=scan("<page><title>x</title><text>y</text></page>");
    assert(o.donors=="titletextpage"&&o.trials==13&&o.correct==13);
  } else if(test=="attributes") {
    o=scan("<outer><empty a='>'/><inner x=\"a/>\">x</inner> </outer>");
    assert(o.donors=="innerouter"&&o.correct==10&&o.trials==10);
  } else if(test=="mismatch") {
    o=scan("<abc>x</axc></abc>"); assert(o.donors=="ab"&&o.trials==2&&o.correct==1);
  } else if(test=="bounds") {
    auto a=scan("<"+std::string(65,'a')+">x</aaa>"); assert(a.trials==0);
    std::string deep;for(int i=0;i<17;++i)deep+="<a>";
    o=scan(deep+"</a>"); assert(o.trials==0);
  } else if(test=="uncertain") {
    assert(scan("<abc><?ignored></abc>").trials==0);
    assert(scan(std::string("<abc>")+char(12)+"x</abc>").trials==0);
    o=scan("<abc>x</abc   >");assert(o.donors=="abc"&&o.correct==3);
  } else if(test=="stored_tokens") {
    gamma_closing::Replay p;
    for(uint8_t c:std::string("L")+char(0xd0)+char(0x80)+"NbodyL/")p.observe(c);
    uint8_t donor=0; assert(p.predict(donor)&&donor==0xd0);p.observe(0xd0);
    assert(p.predict(donor)&&donor==0x80);p.observe(0x80);assert(!p.predict(donor));
    p.observe('N');assert(!p.predict(donor));o=scan("<a></a>");
  } else return 2;
  std::cout<<test<<" trials="<<o.trials<<" correct="<<o.correct<<" state="<<o.hash<<"\n";
}
