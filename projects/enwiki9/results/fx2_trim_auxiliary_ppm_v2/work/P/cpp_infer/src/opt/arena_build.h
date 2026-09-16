// arena_build.h — integration loader: reads weights.bin (SPEC section 4 via
// weights_io) and repacks every quantized matmul into the qmat.h arenas laid
// out CONTIGUOUSLY IN EXACT PER-TOKEN CONSUMPTION ORDER, so the whole weight
// stream is one big sequential read per token (hardware prefetch friendly;
// the kernels' prefetcht0 +2KB runs across arena boundaries into the next
// matmul's stream, which is exactly what we want).
//
// Stream order (must equal the call order in model_opt.cpp):
//   [prior fold|cols int4]                                  (sparse, raw u8)
//   per layer l = 0..11:
//     kimi:  [qp][kp][vp][fg_up][fg_down][og_up][og_down]
//            [beta_w f32][conv_q f32][conv_k f32][conv_v f32][dt_bias][gn_w]
//            [out_proj]
//     van:   [qp][kp][vp][out_proj]
//     both:  [mlp.up][mlp.down fold|cols int4]
//   [unembed]
// The fp32 KDA weights sit inside the stream at their consumption point.
// The pool has QMAT_TAIL_SLACK mapped past the last arena (prefetch overrun),
// then the normed token-embedding table (random-access, not part of the
// stream). RoPE tables (32 MB, 256 B/token) live in separate heap vectors.
#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

#include "kda.h"
#include "qmat.h"

namespace fx2 {
namespace opt {

// mmap'd, hugepage-advised (MADV_HUGEPAGE), zero-initialized buffer
struct HugeBuf {
  uint8_t* p = nullptr;
  size_t bytes = 0;
  void alloc(size_t n);
  ~HugeBuf();
  HugeBuf() = default;
  HugeBuf(const HugeBuf&) = delete;
  HugeBuf& operator=(const HugeBuf&) = delete;
};

// one dense matmul site: arena descriptor + this site's activation scale
struct QSite {
  QDense m;
  float s_act = 0.0f;
};

struct KimiArenas {
  QSite qp, kp, vp;        // 192x192, biased-u8 input
  QSite fg_up, og_up;      // 64x192, biased (consumed via quant_bias epilogue)
  QSite fg_down, og_down;  // 192x64, biased
  QSite op;                // 192x192, biased
  const float* beta_w = nullptr;  // [3][192] fp32 (in the stream)
  KdaWeights kw;                  // conv/dt_bias/gn_w point into the stream
};

struct VanArenas {
  QSite qp, kp, vp, op;  // 192x192, biased
  float sq[3] = {}, sk[3] = {}, sv[3] = {};
  float coef[3] = {};  // 0.125f * sq[h] * sk[h] (same fp order as naive)
};

struct MlpArenas {
  QSite up;                  // 768x192, biased; relu2q epilogue s_next below
  QSparse4 down;             // int4 columns, raw-u8 input (relu^2 output)
  float down_s_act = 0.0f;   // = mlp.down activation scale (relu2q s_next)
};

struct OptModel {
  static constexpr int V = 205, D = 192, NL = 12, DH = 64, NH = 3,
                       DMLP = 768, ROPE_LEN = 131072;
  static constexpr bool KIMI_L[NL] = {true, true, true,  false, true, true,
                                      true, false, true, true,  true, false};

  HugeBuf pool;          // weight stream + tok table
  size_t stream_bytes = 0;  // bytes of the per-token weight stream

  QSparse4 prior;        // 192x205, raw-u8 quantized prior
  float prior_s_act = 0.0f;
  KimiArenas kimi[9];
  VanArenas van[3];
  MlpArenas mlp[NL];
  QSite unembed;         // 205x192 (rows_padded 208), biased

  int layer2kimi[NL] = {};
  int layer2van[NL] = {};
  float rsc[NL] = {}, tec[NL] = {}, skip_w[6] = {};
  const float* tok_table = nullptr;  // 205x192 normed embedding rows
  std::vector<float> rope_sin, rope_cos;  // 131072 x 32 each
  float inv_freq[32] = {};

  void load(const char* weights_path);
};

}  // namespace opt
}  // namespace fx2
