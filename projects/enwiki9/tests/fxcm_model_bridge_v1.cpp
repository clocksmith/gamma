#include "../lib/forge_fxcm_raw_adapter_v1.hpp"
#include "../lib/fxcm_model_bridge_v1.hpp"
#include <cassert>
#include <cmath>
#include <cstring>
#include <cstdio>
#include <limits>
// The test runner extracts this unchanged pure function from authenticated
// upstream source. It does not instantiate the upstream predictor globals.
#include "squash.inc"

struct Legacy {
  mutable unsigned predictions=0;
  unsigned state=0,observations=0,bytes=0;
  mutable std::valarray<float> values=std::valarray<float>(0.5f,431);
  unsigned NumOutputs(){return 431;}
  const std::valarray<float>& Predict()const {
    ++predictions;
    for(unsigned i=0;i<431;++i)values[i]=float((state+i)%17)/16.0f;
    return values;
  }
  void Perceive(int b){state=(state*33)^unsigned(b);++observations;}
  void ByteUpdate(){++bytes;}
};
struct Raw {
  unsigned n=403,active=403,state=0,observations=0,bytes=0;
  short raw[403]{};
  bool absent=false;
  float override_p=-1;
  unsigned NumOutputs(){return n;}
  unsigned ActivePredictions(){return active;}
  const short* RawPredictions(){return absent?nullptr:raw;}
  float RawPredictionProbability(short v){return override_p==-1?squashc(v)*(1.0f/4095.0f):override_p;}
  void Predict()=delete;
  void Perceive(int bit){state=(state*33)^unsigned(bit);++observations;}
  void ByteUpdate(){++bytes;}
};
int main(){
  Raw m;
  std::array<float,403> a{},b{};
  unsigned endpoint_count=0,old_rejections=0;
  for(int raw=-2047;raw<=2047;++raw){
    m.raw[0]=raw;m.active=1;
    const float expected=m.RawPredictionProbability(raw);
    if(expected==1.0f)++endpoint_count;
    if(!gamma_forge::probabilities(m,403,a.data()))++old_rejections;
    assert(gamma_forge_v2::probabilities(m,403,b.data()));
    assert(std::memcmp(&b[0],&expected,sizeof(float))==0);
    for(unsigned i=1;i<403;++i)assert(b[i]==0.5f);
  }
  assert(endpoint_count>0 && old_rejections==endpoint_count);
  for(float p:{0.0f,1.0f}){m.override_p=p;assert(gamma_forge_v2::probabilities(m,403,b.data()) && b[0]==p);}
  auto saved=b;
  for(float p:{-0.1f,1.1f,std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::infinity()}){
    m.override_p=p;assert(!gamma_forge_v2::probabilities(m,403,b.data()));
    assert(std::memcmp(saved.data(),b.data(),sizeof(b))==0);
  }
  m.override_p=-1;m.raw[0]=2048;assert(!gamma_forge_v2::probabilities(m,403,b.data()));
  m.raw[0]=-2048;assert(!gamma_forge_v2::probabilities(m,403,b.data()));
  m.raw[0]=0;m.n=0;assert(!gamma_forge_v2::probabilities(m,403,b.data()));
  m.n=560;assert(!gamma_forge_v2::probabilities(m,403,b.data()));
  m.n=403;m.active=404;assert(!gamma_forge_v2::probabilities(m,403,b.data()));
  m.active=1;m.absent=true;assert(!gamma_forge_v2::probabilities(m,403,b.data()));
  m.active=0;assert(gamma_forge_v2::probabilities(m,403,b.data()));
  for(float p:b)assert(p==0.5f);
  assert(!gamma_forge_v2::probabilities(m,403,nullptr));
  Legacy parent;gamma_fxcm_bridge::Copy<Legacy> k;gamma_fxcm_bridge::Raw<Raw,403> d;
  for(unsigned i=0;i<4096;++i){
    const auto& p=parent.Predict();const auto& q=k.Predict();
    for(unsigned j=0;j<431;++j)assert(p[j]==q[j]);
    const auto& r=d.Predict();assert(r.size()==403);
    const int bit=(i^(i>>3))&1;
    parent.Perceive(bit);k.Perceive(bit);d.Perceive(bit);
    if(i%8==7){parent.ByteUpdate();k.ByteUpdate();d.ByteUpdate();}
    assert(parent.state==k.source_model().state && parent.state==d.source_model().state);
    assert(parent.observations==k.source_model().observations && parent.observations==d.source_model().observations);
    assert(parent.predictions==k.source_model().predictions && parent.bytes==k.source_model().bytes);
    assert(parent.bytes==d.source_model().bytes);
  }
  std::printf("raw_values=4095 endpoint_values=%u v1_rejections=%u bridge_updates=4096 exact=1\n",endpoint_count,old_rejections);
}
