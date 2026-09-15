// Article-local projected multinomial correction of frozen transformer logits.
#ifndef GAMMA_FX2_ONLINE_HEAD_V1_HPP
#define GAMMA_FX2_ONLINE_HEAD_V1_HPP
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <vector>
namespace gamma_online_head {
constexpr unsigned D=192,V=205;
inline void require(bool ok){if(!ok)std::abort();}
inline char configured_arm(){const char* p=std::getenv("GAMMA_FX2_HEAD_ARM");require(p&&p[0]&&!p[1]);return p[0];}
class Model {
 public:
  char arm;
  bool pending=false;
  uint64_t observations=0,predictions=0,updates=0,resets=0,local_updates=0;
  std::array<float,D*V> weights{};
  std::array<float,D> features{};
  std::array<float,V> probabilities{};
  explicit Model(char a):arm(a){require(a=='P'||a=='K'||a=='D'||a=='S');}
  void reset(){
    require(!pending);weights.fill(0);features.fill(0);probabilities.fill(0);
    local_updates=0;++resets;
  }
  void predict(const float* normalized_hidden,const float* capped_logits,
               const float* base_probability,float* output){
    require(!pending);
    double norm2=1;
    for(unsigned i=0;i<D;++i){require(std::isfinite(normalized_hidden[i]));norm2+=double(normalized_hidden[i])*normalized_hidden[i];}
    double inv=1/std::sqrt(norm2);
    for(unsigned i=0;i<D;++i)features[i]=float(normalized_hidden[i]*inv);
    if(local_updates==0){
      for(unsigned j=0;j<V;++j)probabilities[j]=base_probability[j];
    }else{
      std::array<double,V> logits{},mass{};
      double maximum=-INFINITY,total=0;
      for(unsigned j=0;j<V;++j){
        double correction=0;
        for(unsigned i=0;i<D;++i)correction+=double(weights[j*D+i])*features[i];
        require(std::isfinite(correction)&&std::fabs(correction)<=4.00001);
        logits[j]=double(capped_logits[j])+correction;
        if(logits[j]>maximum)maximum=logits[j];
      }
      for(unsigned j=0;j<V;++j){mass[j]=std::exp(logits[j]-maximum);total+=mass[j];}
      require(std::isfinite(total)&&total>0);
      for(unsigned j=0;j<V;++j)probabilities[j]=float(mass[j]/total);
    }
    for(unsigned j=0;j<V;++j){
      require(std::isfinite(probabilities[j])&&probabilities[j]>=0&&probabilities[j]<=1);
      output[j]=(arm=='P'||arm=='K')?base_probability[j]:probabilities[j];
    }
    ++predictions;pending=true;
  }
  void observe(unsigned truth){
    require(truth<V);++observations;
    if(!pending)return; // PPM-only first token of each piece has no head prediction.
    if(arm!='P'){
      if(arm=='S')truth=(truth+1)%V;
      double norm2=0;
      for(unsigned j=0;j<V;++j){
        const double residual=double(j==truth)-probabilities[j];
        for(unsigned i=0;i<D;++i){
          float w=float(double(weights[j*D+i])+0.25*residual*features[i]);
          weights[j*D+i]=w;norm2+=double(w)*w;
        }
      }
      require(std::isfinite(norm2));
      if(norm2>16){
        // A small interior margin covers the final binary32 materialization.
        const double scale=3.999999/std::sqrt(norm2);
        for(auto& w:weights)w=float(w*scale);
      }
      ++updates;++local_updates;
    }
    pending=false;
  }
  std::vector<uint8_t> state()const{
    std::vector<uint8_t> out;
    auto put=[&](uint64_t x,unsigned n){for(unsigned j=0;j<n;++j)out.push_back(uint8_t(x>>(8*j)));};
    for(uint64_t x:{observations,predictions,updates,resets,local_updates})put(x,8);
    put(pending,1);
    auto floats=[&](const auto& a){for(float f:a){uint32_t b;std::memcpy(&b,&f,4);put(b,4);}};
    floats(weights);floats(features);floats(probabilities);
    return out;
  }
};
}
#endif
