#include "../lib/wrt_support_native_v1.hpp"
#include <cassert>

int main(int argc,char** argv){
  if(argc==2){
    if(argv[1][0]<'0' || argv[1][0]>'2' || argv[1][1])return 4;
    gamma_wrt_support::Audit audit(argv[1][0]-'0');
    int byte;
    while((byte=std::getchar())!=EOF)for(int shift=7;shift>=0;--shift){
      unsigned p=audit.project(12345);unsigned char out[2]={(unsigned char)p,(unsigned char)(p>>8)};
      if(std::fwrite(out,1,2,stdout)!=2)return 3;
      audit.observe((byte>>shift)&1);
    }
    return 0;
  }
  if(argc!=1)return 4;
  gamma_wrt_support::State s;
  int c;
  while((c=std::getchar())!=EOF){
    for(int shift=7;shift>=0;--shift){
      unsigned char row[3]={(unsigned char)s.phase,(unsigned char)s.prefix,(unsigned char)(s.forced()+1)};
      if(std::fwrite(row,1,3,stdout)!=3)return 3;
      if(!s.observe((c>>shift)&1))return 2;
    }
  }
  if(!s.complete())return 2;
  // Bad truths are rejected without changing the complete neutral state.
  auto before=s;assert(!s.observe(2));assert(s.phase==before.phase && s.prefix==before.prefix);
}
