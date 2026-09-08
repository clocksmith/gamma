#include "../lib/wrt_support_deploy_v1.hpp"
#include <cstdio>

int main(){
  gamma_wrt_support::Coder coder;
  unsigned char bytes[28];
  for(;;){
    size_t n=std::fread(bytes,1,28,stdin);
    if(!n)break;
    if(n!=28)return 2;
    unsigned p=0,bit=0;
    for(unsigned i=0;i<4;++i){p|=unsigned(bytes[4+i])<<(8*i);bit|=unsigned(bytes[24+i])<<(8*i);}
    unsigned q=coder.project(p);unsigned char out[2]={(unsigned char)q,(unsigned char)(q>>8)};
    if(std::fwrite(out,1,2,stdout)!=2)return 3;
    coder.observe(bit);
  }
}
