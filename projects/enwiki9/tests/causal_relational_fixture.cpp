#include "predictors/causal_relational_v1.hpp"
#include <iostream>
#include <cassert>
#include <cmath>
using namespace gamma_relational;
int main(int argc,char**){
 if(argc>1){std::array<uint64_t,4>w{};std::array<uint32_t,4>p{};unsigned bit;while(std::cin>>w[0]>>w[1]>>w[2]>>w[3]>>p[0]>>p[1]>>p[2]>>p[3]>>bit){std::cout<<marginal(w,p);update(w,p,bit);for(auto v:w)std::cout<<' '<<v;std::cout<<'\n';}return 0;}
 std::string text;
 for(int i=0;i<110;++i)text+="<title>alpha delta gamma theta</title><text xml:space=\"preserve\">alpha alpha [[delta]] theta theta</text>";
 Bytes tape{7};for(unsigned char c:text)tape.push_back(gamma_xml_field::unswap(c));
 Model a({},text.size(),'S'),b({},text.size(),'S'),k({},text.size(),'K');Bytes ra,rb,rk;std::string restored;uint64_t position=0;
 for(uint8_t c:tape){for(unsigned bit=0;bit<8;++bit){uint32_t p=uint32_t(1+(position*1237)%65534);auto x=a.predict(p);assert(b.predict(p)==x);assert(k.predict(p)==p);unsigned truth=(c>>(7-bit))&1;assert(a.observe(truth,ra));assert(b.observe(truth,rb));assert(k.observe(truth,rk));assert(ra==rb&&ra==rk);assert(a.state()==b.state()&&a.state()==k.state());assert(a.state().size()<24000);restored.append(ra.begin(),ra.end());++position;}}
 assert(restored==text&&a.finish()&&b.finish()&&k.finish());assert(a.active_bits>0&&a.pairs>0);
 // Multi-byte WRT emission must remain invisible until completed.
 std::vector<std::string> words(81,"cat");Model partial(words,3,'S');Bytes raw;
 for(uint8_t c:{uint8_t(7),uint8_t(208)})for(unsigned j=0;j<8;++j){partial.predict(32768);assert(partial.observe((c>>(7-j))&1,raw));assert(raw.empty());}
 for(unsigned j=0;j<8;++j){partial.predict(32768);assert(partial.observe((128>>(7-j))&1,raw));if(j<7)assert(raw.empty());}
 assert(std::string(raw.begin(),raw.end())=="cat"&&partial.finish());
 Binding shared,independent;shared.count=independent.count=4;
 for(size_t i=0;i<4;++i){shared.donors[i].right.stored={uint8_t(32+i*51)};independent.donors[i]=shared.donors[i];}
 long double shared_loss=0,independent_loss=0;
 for(unsigned mention=0;mention<8;++mention){shared.start(false);independent.start(true);
   for(unsigned bit=0;bit<8;++bit){unsigned truth=(32>>(7-bit))&1;
     uint32_t sp=shared.predict(32768,bit,false),ip=independent.predict(32768,bit,false);
     shared_loss-=std::log2((long double)(truth?sp:65536-sp)/65536);
     independent_loss-=std::log2((long double)(truth?ip:65536-ip)/65536);
     shared.observe(truth,bit,false);independent.observe(truth,bit,false);
   }
 }
 assert(shared_loss+1<independent_loss); // actual fixed-point binding kernel
 std::cout<<"causal state parity, bounded memory, complete emissions, active persistent donors\n";
}
