#include "../lib/forge_fxcm_raw_adapter_v1.hpp"
#include <cassert>
#include <limits>
#include <cstring>

struct Fixture {
  unsigned n=403,active=3,calls=0;
  short raw[3]={-2047,0,2047};
  bool absent=false,invalid=false;
  unsigned NumOutputs(){return n;}
  unsigned ActivePredictions(){return active;}
  const short* RawPredictions(){return absent?nullptr:raw;}
  float RawPredictionProbability(short value){
    ++calls;
    if(invalid)return std::numeric_limits<float>::quiet_NaN();
    return value<0?0.125f:value==0?0.5f:0.875f;
  }
  // Any accidental use of the historical interface fails compilation.
  void Predict()=delete;
};

int main(){
  Fixture m;std::array<float,560> out{};
  assert(gamma_forge::probabilities(m,403,out.data()));
  assert(m.calls==3 && out[0]==0.125f && out[1]==0.5f && out[2]==0.875f);
  for(unsigned i=3;i<403;++i)assert(out[i]==0.5f);
  auto saved=out;
  for(unsigned scenario=0;scenario<6;++scenario){
    Fixture bad;
    if(scenario==0)bad.n=560;
    if(scenario==1)bad.active=404;
    if(scenario==2)bad.absent=true;
    if(scenario==3)bad.raw[1]=2048;
    if(scenario==4)bad.raw[1]=-2048;
    if(scenario==5)bad.invalid=true;
    assert(!gamma_forge::probabilities(bad,403,out.data()));
    assert(std::memcmp(saved.data(),out.data(),sizeof(out))==0);
  }
  m.active=0;m.absent=true;m.calls=0;
  assert(gamma_forge::probabilities(m,403,out.data()));
  assert(m.calls==0);
  for(unsigned i=0;i<403;++i)assert(out[i]==0.5f);
  assert(!gamma_forge::probabilities(m,403,nullptr));
}
