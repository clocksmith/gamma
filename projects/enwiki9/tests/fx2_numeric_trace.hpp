// Diagnostic observation only. Never supplies values to the deployed predictor.
#pragma once
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <string>
#include "cpp_infer/src/opt/qmat_dense.h"
#include "cpp_infer/src/opt/qmat_sparse.h"
namespace gamma_numeric {
inline FILE* sink = nullptr;
inline uint32_t row = 0, limit = 64;
inline int layer = 0;
inline bool active() { return sink && row < limit; }
inline std::string block(const char* suffix) { return "blocks." + std::to_string(layer) + "." + suffix; }
inline void emit(const std::string& key, const float* p, uint32_t n) {
  if (!active()) return;
  const uint32_t header[3] = {row, uint32_t(key.size()), n};
  if (std::fwrite(header, sizeof(header), 1, sink)!=1 ||
      std::fwrite(key.data(),1,key.size(),sink)!=key.size() ||
      std::fwrite(p,sizeof(float),n,sink)!=n) std::abort();
}
inline void quant(const std::string& key, const float* input, const float* scales,
                  int group, const void* q, int bias, bool signed_q, int n) {
  if (!active()) return;
  alignas(64) float scaled[768], integer[768], scale[768];
  for (int i=0;i<n;++i) {
    scale[i]=scales[i/group]; scaled[i]=input[i]/scale[i];
    integer[i]=signed_q ? float(static_cast<const int8_t*>(q)[i]) : float(static_cast<const uint8_t*>(q)[i])-bias;
  }
  emit(key+".input",input,n); emit(key+".scale",scale,n);
  emit(key+".scaled",scaled,n); emit(key+".integer",integer,n);
}
inline void dense(const std::string& key, const fx2::opt::QDense& m,
                  const float* input, float scale, const uint8_t* q) {
  if (!active()) return;
  quant(key+".quantize_activation",input,&scale,m.d_in,q,128,false,m.d_in);
  alignas(64) int32_t dots[768]; alignas(64) float values[768], as_float[768];
  fx2::opt::qgemv_i32(m,q,dots); fx2::opt::qgemv_f32(m,q,values);
  for(int i=0;i<m.d_out;++i) as_float[i]=float(dots[i]);
  emit(key+".accumulator",as_float,m.d_out); emit(key+".output",values,m.d_out);
}
inline void sparse(const std::string& key, const fx2::opt::QSparse4& m,
                   const float* input, float scale, const uint8_t* q, int n) {
  if (!active()) return;
  quant(key+".quantize_activation",input,&scale,n,q,0,false,n);
  alignas(64) int32_t dots[192]; alignas(64) float values[192], as_float[192];
  fx2::opt::qsparse4_dense_i32(m,q,dots); fx2::opt::qsparse4_dense_f32(m,q,values);
  for(int i=0;i<192;++i) as_float[i]=float(dots[i]);
  emit(key+".accumulator",as_float,192); emit(key+".output",values,192);
}
}
