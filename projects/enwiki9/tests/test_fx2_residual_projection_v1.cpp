#include "fx2_residual_projection_v1.hpp"
#include <cassert>
#include <iostream>
int main(int argc,char**) {
  using namespace gamma_residual;
  if(argc>1) {
    unsigned c;int k;
    while(std::cin>>c>>k) std::cout<<count(c,k)<<'\n';
    return 0;
  }
  for(unsigned c=1;c<Q;++c) {
    assert(count(c,0)==c);
    assert(count(c,-RADIUS)<=c && count(c,RADIUS)>=c);
    for(int k:{-int(RADIUS),-1,0,1,int(RADIUS)}) {
      const auto n=__int128(c)*Q*S+__int128(c)*(Q-c)*k;
      const auto den=__int128(Q)*S;
      auto expected=(2*n+den)/(2*den);
      if(expected<1)expected=1;
      if(expected>=Q)expected=Q-1;
      assert(count(c,k)==expected);
    }
  }
  float h[192]={};assert(project(h)==0);
  h[0]=1;h[6]=-1;h[12]=1;h[13]=-1;
  assert(project(h)==9);
  capture(h);assert(features().valid && features().packed==9);
  invalidate();assert(!features().valid && features().packed==0);
  std::cout<<"65535 identity counts,327675 wide-integer comparisons,feature grouping and reset passed\n";
}
