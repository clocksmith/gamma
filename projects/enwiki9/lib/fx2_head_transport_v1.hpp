// Optional odds correction; every original predictor update remains authoritative.
#ifndef GAMMA_FX2_HEAD_TRANSPORT_V1_HPP
#define GAMMA_FX2_HEAD_TRANSPORT_V1_HPP
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
namespace gamma_head_transport {
constexpr uint32_t Q=65536;
constexpr uint64_t W=uint64_t(1)<<32;
inline void require(bool x){if(!x)std::abort();}
inline uint32_t count(float p){require(p>=0&&p<=1);return uint32_t(1+65534*p);}
inline uint32_t transport(uint32_t p,uint32_t a,uint32_t b){
  require(p&&p<Q&&a&&a<Q&&b&&b<Q);
  if(a==b)return p;
  uint64_t n=uint64_t(p)*a*(Q-b);
  uint64_t den=n+uint64_t(Q-p)*(Q-a)*b;
  uint64_t q=uint64_t((__uint128_t(Q)*n+den/2)/den);
  return uint32_t(q<1?1:q>=Q?Q-1:q);
}
struct Model {
  char arm;
  uint64_t position=0;
  std::array<std::array<uint64_t,2>,8> weights{};
  std::array<float,256> base{},adapted{};
  unsigned bot=0,top=255,context=0;
  bool pending=false,active=false;
  uint32_t native=32768;
  std::array<uint32_t,2> counts{};
  explicit Model(char a):arm(a){
    require(a=='P'||a=='K'||a=='D'||a=='S');
    for(auto& w:weights)w={W/2,W/2};
    base.fill(1.0f/256);adapted=base;
  }
  void set(const std::vector<int>& vocab,const float* p,const float* q){
    require(!pending&&position%8==0&&bot==0&&top==255);
    base.fill(0);adapted.fill(0);
    for(unsigned i=0;i<vocab.size();++i){
      require(vocab[i]>=0&&vocab[i]<256&&p[i]>=0&&q[i]>=0);
      base[vocab[i]]=p[i];adapted[vocab[i]]=q[i];
    }
  }
  float bit_probability(const std::array<float,256>& p)const{
    unsigned mid=bot+(top-bot)/2;float n=0;
    for(unsigned i=mid+1;i<=top;++i)n+=p[i];
    float d=n;for(unsigned i=bot;i<=mid;++i)d+=p[i];
    return d==0?0.5f:n/d;
  }
  void capture(float parent_neural,bool enabled){native=count(parent_neural);active=enabled;}
  uint32_t predict(uint32_t p){
    require(!pending&&p&&p<Q);
    const uint32_t b=count(bit_probability(base)),a=count(bit_probability(adapted));
    require(b==native); // Reconstruct the actual frozen ByteModel bit probability.
    counts={p,active?transport(p,a,b):p};context=position%8;pending=true;
    uint64_t n=weights[context][0]*counts[0]+weights[context][1]*counts[1];
    uint32_t result=uint32_t((n+W/2)/W);
    return arm=='P'||arm=='K'?p:result;
  }
  void observe(unsigned truth){
    require(pending&&truth<2);
    if(active&&arm!='P'){
      auto& w=weights[context];uint64_t prod[2],rem[2],total=0,assigned=0;
      for(unsigned i=0;i<2;++i){prod[i]=w[i]*(truth?counts[i]:Q-counts[i]);total+=prod[i];}
      for(unsigned i=0;i<2;++i){
        __uint128_t scaled=__uint128_t(W-2)*prod[i];w[i]=1+uint64_t(scaled/total);
        rem[i]=uint64_t(scaled%total);assigned+=w[i];
      }
      require(assigned<=W&&W-assigned<2);
      if(assigned<W)++w[rem[1]>rem[0]?1:0];
    }
    unsigned mid=bot+(top-bot)/2;if(truth)bot=mid+1;else top=mid;
    ++position;if(position%8==0){bot=0;top=255;}pending=false;
  }
  std::vector<uint8_t> state()const{
    require(!pending);std::vector<uint8_t> s;
    auto put=[&](uint64_t x,unsigned n){for(unsigned j=0;j<n;++j)s.push_back(uint8_t(x>>(8*j)));};
    put(position,8);for(auto w:weights)for(auto x:w)put(x,8);
    for(const auto* p:{&base,&adapted})for(float f:*p){uint32_t x;std::memcpy(&x,&f,4);put(x,4);}
    for(unsigned x:{bot,top,context,native,counts[0],counts[1]})put(x,4);
    put(active,1);return s;
  }
};
inline Model& model(){static Model m([](){const char* p=std::getenv("GAMMA_FX2_HEAD_ARM");require(p&&p[0]&&!p[1]);return p[0];}());return m;}
inline void set(const std::vector<int>& v,const float* b,const float* a){model().set(v,b,a);}
inline void capture(float n,bool active){model().capture(n,active);}
inline uint32_t predict(uint32_t p){return model().predict(p);}
struct Audit {
  FILE* f=nullptr;
  Audit(){if(const char* p=std::getenv("GAMMA_FX2_TRANSPORT_STATE")){f=std::fopen(p,"wbx");require(f);}}
  ~Audit(){if(f){write();require(std::fclose(f)==0);}}
  void write(){if(f){auto s=model().state();require(std::fwrite(s.data(),1,s.size(),f)==s.size());}}
};
inline Audit& audit(){static Audit a;return a;}
inline void observe(unsigned t){model().observe(t);if(model().position%2048==0)audit().write();}
}
#endif
