#include "fx2_final_residual_counts_v1.hpp"
using gamma_final_counts::Model;
extern "C" {
void* model_new(char arm){auto* m=new Model();if(!m->configure(arm)){delete m;return nullptr;}return m;}
void model_delete(void* m){delete static_cast<Model*>(m);}
int model_predict(void* m,unsigned p){unsigned q=0;return static_cast<Model*>(m)->predict(p,q)?int(q):-1;}
int model_observe(void* m,unsigned y){return static_cast<Model*>(m)->observe(y);}
unsigned model_state(void* m,unsigned char* out){auto s=static_cast<Model*>(m)->serialize();std::memcpy(out,s.data(),s.size());return s.size();}
int model_restore(void* m,const unsigned char* in,unsigned n){return static_cast<Model*>(m)->restore(in,n);}
}
