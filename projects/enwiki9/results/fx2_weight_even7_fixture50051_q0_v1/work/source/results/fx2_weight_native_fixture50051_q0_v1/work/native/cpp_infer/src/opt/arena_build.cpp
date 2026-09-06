#include "arena_build.h"

#include <sys/mman.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

#include "../weights_io.h"
#include "glue.h"

namespace fx2 {
namespace opt {

namespace {

[[noreturn]] void die(const char* msg) {
  std::fprintf(stderr, "arena_build: %s\n", msg);
  std::exit(1);
}

constexpr size_t round64(size_t x) { return (x + 63) & ~size_t(63); }

}  // namespace

void HugeBuf::alloc(size_t n) {
  bytes = (n + (size_t(2) << 20) - 1) & ~((size_t(2) << 20) - 1);
  void* m = ::mmap(nullptr, bytes, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  if (m == MAP_FAILED) die("mmap failed");
  ::madvise(m, bytes, MADV_HUGEPAGE);
  std::memset(m, 0, bytes);  // touch every page
  p = static_cast<uint8_t*>(m);
}

HugeBuf::~HugeBuf() {
  if (p) ::munmap(p, bytes);
}

void OptModel::load(const char* weights_path) {
  // accept both the raw FX2TFW01 file and the losslessly compressed
  // FX2TFWC1/FX2TFWC2 files (bit-identical tensors either way)
  char magic[8] = {0};
  if (FILE* f = std::fopen(weights_path, "rb")) {
    if (std::fread(magic, 1, 8, f) != 8) magic[0] = 0;
    std::fclose(f);
  }
  WeightsFile wf = (std::memcmp(magic, "FX2TFWC", 7) == 0 ||
                    std::memcmp(magic, "GFX2MAR1", 8) == 0)
                       ? WeightsFile::load_compressed(weights_path)
                       : WeightsFile::load(weights_path);

  {  // config sanity (same checks as the naive loader)
    const WTensor& ci = wf.get("config.ints", DT_I32, {11});
    const int32_t want[11] = {V, D, NL, DH, NH, DMLP, 1024, DH, NH, 4, 10000};
    for (int i = 0; i < 11; i++)
      if (ci.i32()[i] != want[i]) die("config.ints mismatch");
    const WTensor& ck = wf.get("config.kimi", DT_I32, {NL});
    for (int i = 0; i < NL; i++)
      if ((ck.i32()[i] != 0) != KIMI_L[i]) die("config.kimi mismatch");
  }

  pool.alloc(size_t(16) << 20);
  size_t off = 0;
  auto take = [&](size_t n) -> uint8_t* {
    off = round64(off);
    uint8_t* q = pool.p + off;
    off += n;
    if (off + QMAT_TAIL_SLACK > pool.bytes) die("weight pool overflow");
    return q;
  };

  // dense arena site in stream order
  auto qsite = [&](const std::string& prefix, int d_out, int d_in,
                   bool biased) -> QSite {
    const WTensor& wq =
        wf.get(prefix + ".weight.q", DT_I8,
               {static_cast<uint32_t>(d_out), static_cast<uint32_t>(d_in)});
    const WTensor& ws = wf.get(prefix + ".weight.scale", DT_BF16,
                               {static_cast<uint32_t>(d_out)});
    const WTensor& sa =
        wf.get(prefix + ".quantize_activation.scale", DT_BF16, {1});
    QSite s;
    s.s_act = bf16_to_f32(sa.bf16_bits()[0]);
    if (!(s.s_act > 0.0f)) die("activation scale not positive");
    std::vector<float> fold(d_out);
    for (int o = 0; o < d_out; o++)
      fold[o] = s.s_act * bf16_to_f32(ws.bf16_bits()[o]);
    uint8_t* dst = take(qdense_bytes(d_out, d_in));
    s.m = qdense_build(dst, wq.i8(), fold.data(), d_out, d_in, biased);
    return s;
  };

  // int4 sparse-column arena site (d_out must be 192): [fold | cols]
  auto qsp4 = [&](const std::string& prefix, int d_in,
                  float* s_act_out) -> QSparse4 {
    const WTensor& wq =
        wf.get(prefix + ".weight.q", DT_I8,
               {static_cast<uint32_t>(D), static_cast<uint32_t>(d_in)});
    const WTensor& ws = wf.get(prefix + ".weight.scale", DT_BF16,
                               {static_cast<uint32_t>(D)});
    const WTensor& sa =
        wf.get(prefix + ".quantize_activation.scale", DT_BF16, {1});
    float s_act = bf16_to_f32(sa.bf16_bits()[0]);
    if (!(s_act > 0.0f)) die("activation scale not positive");
    *s_act_out = s_act;
    std::vector<float> fold(D);
    for (int o = 0; o < D; o++)
      fold[o] = s_act * bf16_to_f32(ws.bf16_bits()[o]);
    float* foldp = reinterpret_cast<float*>(take(sizeof(float) * D));
    uint8_t* cols = take(qsparse4_bytes(d_in));
    return qsparse4_build(cols, foldp, wq.i8(), fold.data(), D, d_in);
  };

  auto f32block = [&](const float* src, size_t n) -> float* {
    float* p = reinterpret_cast<float*>(take(sizeof(float) * n));
    std::memcpy(p, src, sizeof(float) * n);
    return p;
  };

  // ---- stream, in per-token consumption order ----
  prior = qsp4("prior_embedding", V, &prior_s_act);

  {
    const WTensor& sw = wf.get("skip_connection_weights.value", DT_F32, {6});
    for (int i = 0; i < 6; i++) skip_w[i] = sw.f32()[i];
  }

  int ki = 0, vi = 0;
  for (int l = 0; l < NL; l++) {
    std::string b = "blocks." + std::to_string(l) + ".";
    rsc[l] =
        wf.get(b + "residual_stream_coefficient.value", DT_F32, {1}).f32()[0];
    tec[l] =
        wf.get(b + "token_embedding_coefficient.value", DT_F32, {1}).f32()[0];
    std::string a = b + "attention.";

    if (KIMI_L[l]) {
      KimiArenas& L = kimi[ki];
      layer2kimi[l] = ki;
      L.qp = qsite(a + "query_projection", D, D, true);
      L.kp = qsite(a + "key_projection", D, D, true);
      L.vp = qsite(a + "value_projection", D, D, true);
      L.fg_up = qsite(a + "forget_gate_projection.up", DH, D, true);
      L.fg_down = qsite(a + "forget_gate_projection.down", D, DH, true);
      L.og_up = qsite(a + "output_gate_projection.up", DH, D, true);
      L.og_down = qsite(a + "output_gate_projection.down", D, DH, true);

      {
        const WTensor& bw =
            wf.get(a + "beta_projection.weight", DT_F32, {NH, D});
        L.beta_w = f32block(bw.f32(), size_t(NH) * D);
      }
      const char* convs[3] = {"query_convolution.weight",
                              "key_convolution.weight",
                              "value_convolution.weight"};
      for (int c = 0; c < 3; c++) {
        const WTensor& cw = wf.get(a + convs[c], DT_F32, {D, 4});
        float* wt = reinterpret_cast<float*>(take(sizeof(float) * 4 * D));
        for (int j = 0; j < 4; j++)  // tap-major repack, same as naive
          for (int ch = 0; ch < D; ch++) wt[j * D + ch] = cw.f32()[ch * 4 + j];
        L.kw.conv_w[c] = wt;
      }
      {
        const WTensor& dt = wf.get(a + "dt_bias", DT_F32, {D});
        L.kw.dt_bias = f32block(dt.f32(), D);
      }
      {
        const WTensor& gw =
            wf.get(a + "output_fused_norm_gate.weight", DT_F32, {DH});
        L.kw.gn_w = f32block(gw.f32(), DH);
      }
      {
        const WTensor& al = wf.get(a + "log_baseline_decay_rate", DT_F32, {NH});
        for (int h = 0; h < NH; h++) L.kw.a_neg[h] = -std::exp(al.f32()[h]);
      }
      L.op = qsite(a + "output_projection", D, D, true);
      ki++;
    } else {
      VanArenas& L = van[vi];
      layer2van[l] = vi;
      L.qp = qsite(a + "query_projection", D, D, true);
      L.kp = qsite(a + "key_projection", D, D, true);
      L.vp = qsite(a + "value_projection", D, D, true);
      L.op = qsite(a + "output_projection", D, D, true);
      const WTensor& qs = wf.get(a + "quantize_queries.scale", DT_BF16, {NH});
      const WTensor& ks = wf.get(a + "quantize_keys.scale", DT_BF16, {NH});
      const WTensor& vs = wf.get(a + "quantize_values.scale", DT_BF16, {NH});
      for (int h = 0; h < NH; h++) {
        L.sq[h] = bf16_to_f32(qs.bf16_bits()[h]);
        L.sk[h] = bf16_to_f32(ks.bf16_bits()[h]);
        L.sv[h] = bf16_to_f32(vs.bf16_bits()[h]);
        L.coef[h] = 0.125f * L.sq[h] * L.sk[h];
      }
      vi++;
    }

    mlp[l].up = qsite(b + "mlp.up", DMLP, D, true);
    mlp[l].down = qsp4(b + "mlp.down", DMLP, &mlp[l].down_s_act);
  }
  if (ki != 9 || vi != 3) die("layer pattern mismatch");

  unembed = qsite("unembedding", V, D, true);
  stream_bytes = round64(off);

  // ---- non-stream data: tail slack gap, then the normed embedding table ----
  off += QMAT_TAIL_SLACK;
  {
    const WTensor& eq = wf.get("embedding.weight.q", DT_I8, {V, D});
    const WTensor& es = wf.get("embedding.weight.scale", DT_BF16, {V});
    std::vector<float> rs(V);
    for (int c = 0; c < V; c++) rs[c] = bf16_to_f32(es.bf16_bits()[c]);
    float* table = reinterpret_cast<float*>(take(sizeof(float) * V * D));
    build_normed_embedding_table(eq.i8(), rs.data(), table);
    tok_table = table;
  }

  {
    const WTensor& fi = wf.get("rope.inv_freq", DT_F32, {32});
    std::memcpy(inv_freq, fi.f32(), sizeof(inv_freq));
    const WTensor& si = wf.get("rope.sin", DT_F32,
                               {static_cast<uint32_t>(ROPE_LEN), 32});
    const WTensor& co = wf.get("rope.cos", DT_F32,
                               {static_cast<uint32_t>(ROPE_LEN), 32});
    rope_sin.assign(si.f32(), si.f32() + size_t(ROPE_LEN) * 32);
    rope_cos.assign(co.f32(), co.f32() + size_t(ROPE_LEN) * 32);
  }
}

}  // namespace opt
}  // namespace fx2
