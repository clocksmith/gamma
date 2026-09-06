#include "model.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

#include "kernels.h"
#include "weights_io.h"

namespace fx2 {

namespace {

constexpr int V = 205, D = 192, NL = 12, DH = 64, NH = 3, DMLP = 768;
constexpr int WIN = 1024;
constexpr int ROPE_LEN = 131072;
constexpr int PRIOR_STRIDE = 208;  // 205 padded to a multiple of 16
constexpr bool KIMI[NL] = {true, true, true,  false, true, true,
                           true, false, true, true,  true, false};

[[noreturn]] void die(const char* msg) {
  std::fprintf(stderr, "model: %s\n", msg);
  std::exit(1);
}

// 64B-aligned bump arena for repacked weights
struct Arena {
  uint8_t* base = nullptr;
  size_t cap = 0, used = 0;

  void init(size_t bytes) {
    bytes = (bytes + 63) & ~size_t(63);
    base = static_cast<uint8_t*>(std::aligned_alloc(64, bytes));
    if (!base) die("out of memory");
    cap = bytes;
    used = 0;
  }
  void* take(size_t bytes) {
    used = (used + 63) & ~size_t(63);
    if (used + bytes > cap) die("arena overflow");
    void* p = base + used;
    used += bytes;
    return p;
  }
  ~Arena() { std::free(base); }
};

}  // namespace

// quantized linear: int8 rows (padded stride) + folded per-row fp32 scales
struct QLinear {
  const int8_t* w = nullptr;
  const float* fold = nullptr;  // s_act * s_w[o]
  float s_act = 0.0f;
  int d_out = 0, d_in = 0, stride = 0;
};

struct KimiLayer {
  QLinear qp, kp, vp, fg_up, fg_down, og_up, og_down, op;
  const float* wt_q = nullptr;  // conv weights, tap-major [4][192]
  const float* wt_k = nullptr;
  const float* wt_v = nullptr;
  const float* beta_w = nullptr;   // [3][192]
  const float* dt_bias = nullptr;  // [192]
  const float* gn_w = nullptr;     // [64]
  float a_neg[NH] = {};            // -exp(A_log[h])
};

struct VanLayer {
  QLinear qp, kp, vp, op;
  float sq[NH] = {}, sk[NH] = {}, sv[NH] = {};
  float coef[NH] = {};  // 0.125 * sq[h] * sk[h]
};

struct MlpW {
  QLinear up, down;
};

struct KimiState {
  alignas(64) float S[NH][DH * DH];  // [head][k*64 + v]
  alignas(64) float hist[3][3][D];   // [conv q/k/v][tap: 0=t-3,1=t-2,2=t-1][ch]
};

struct VanState {
  alignas(64) int8_t kring[WIN][D];
  alignas(64) int8_t vring[WIN][D];
};

struct TransformerImpl {
  Arena wa, fa;

  QLinear prior_lin, unembed;
  KimiLayer kimi[9];
  VanLayer van[3];
  MlpW mlp[NL];
  int layer2kimi[NL] = {};
  int layer2van[NL] = {};
  float rsc[NL] = {}, tec[NL] = {};
  float skip_w[6] = {};
  const float* tok_table = nullptr;  // 205 x 192 normed embedding rows
  const float* rope_sin = nullptr;   // 131072 x 32
  const float* rope_cos = nullptr;
  float inv_freq[32] = {};

  // streaming state
  KimiState kst[9];
  VanState vst[3];
  float skip_store[6][D] = {};
  int64_t t = 0;
  int64_t rope_off = 0;
  bool lowprob_skip = false;
  float lowprob_threshold = 21.0f;

  alignas(64) float logits[V] = {};
  Transformer::CaptureFn cap_fn;
  Transformer::BlockInputOverrideFn override_fn;

  // scratch
  alignas(64) int8_t q8[DMLP] = {};
  alignas(64) float xb[D] = {}, xnb[D] = {}, yb[D] = {}, h768[DMLP] = {};
  alignas(64) float prior_f32[PRIOR_STRIDE] = {};

  void load(const char* path);
  QLinear load_qlinear(const WeightsFile& wf, const std::string& prefix,
                       int d_out, int d_in);
  void begin(int64_t rope_position_offset);
  void step(uint8_t token, const float* prior, float* probs_out);
  void kimi_attention(int ki, int l, const float* xn, float* y);
  void van_attention(int vi, int l, const float* xn, float* y);

  void cap(const char* name, const float* d, int n) {
    if (cap_fn) cap_fn(name, d, n);
  }
  void capL(int l, const char* comp, const float* d, int n) {
    if (!cap_fn) return;
    char nm[64];
    std::snprintf(nm, sizeof nm, "%02d_%s", l, comp);
    cap_fn(nm, d, n);
  }
};

QLinear TransformerImpl::load_qlinear(const WeightsFile& wf,
                                      const std::string& prefix, int d_out,
                                      int d_in) {
  const WTensor& wq =
      wf.get(prefix + ".weight.q", DT_I8,
             {static_cast<uint32_t>(d_out), static_cast<uint32_t>(d_in)});
  const WTensor& ws = wf.get(prefix + ".weight.scale", DT_BF16,
                             {static_cast<uint32_t>(d_out)});
  const WTensor& sa =
      wf.get(prefix + ".quantize_activation.scale", DT_BF16, {1});

  QLinear ql;
  ql.d_out = d_out;
  ql.d_in = d_in;
  ql.stride = (d_in + 15) & ~15;
  int8_t* w = static_cast<int8_t*>(wa.take(size_t(d_out) * ql.stride));
  const int8_t* src = wq.i8();
  for (int o = 0; o < d_out; o++) {
    std::memcpy(w + size_t(o) * ql.stride, src + size_t(o) * d_in, d_in);
    std::memset(w + size_t(o) * ql.stride + d_in, 0,
                size_t(ql.stride - d_in));
  }
  for (size_t i = 0; i < wq.numel; i++)
    if (src[i] < -7 || src[i] > 7) die("weight int out of [-7,7]");

  float* fold = static_cast<float*>(fa.take(sizeof(float) * d_out));
  ql.s_act = bf16_to_f32(sa.bf16_bits()[0]);
  if (!(ql.s_act > 0.0f)) die("activation scale not positive");
  for (int o = 0; o < d_out; o++)
    fold[o] = ql.s_act * bf16_to_f32(ws.bf16_bits()[o]);
  ql.w = w;
  ql.fold = fold;
  return ql;
}

void TransformerImpl::load(const char* path) {
  WeightsFile wf = WeightsFile::load(path);

  // config sanity
  {
    const WTensor& ci = wf.get("config.ints", DT_I32, {11});
    const int32_t want[11] = {V, D, NL, DH, NH, DMLP, WIN, DH, NH, 4, 10000};
    for (int i = 0; i < 11; i++)
      if (ci.i32()[i] != want[i]) die("config.ints mismatch");
    const WTensor& ck = wf.get("config.kimi", DT_I32, {NL});
    for (int i = 0; i < NL; i++)
      if ((ck.i32()[i] != 0) != KIMI[i]) die("config.kimi mismatch");
  }

  wa.init(size_t(8) << 20);
  fa.init(size_t(40) << 20);

  // normed token embedding table
  {
    const WTensor& eq = wf.get("embedding.weight.q", DT_I8, {V, D});
    const WTensor& es = wf.get("embedding.weight.scale", DT_BF16, {V});
    float* table = static_cast<float*>(fa.take(sizeof(float) * V * D));
    for (int c = 0; c < V; c++) {
      float s = bf16_to_f32(es.bf16_bits()[c]);
      float* row = table + size_t(c) * D;
      for (int i = 0; i < D; i++)
        row[i] = static_cast<float>(eq.i8()[c * D + i]) * s;
      rms_norm_vec(row, row, D);
    }
    tok_table = table;
  }

  prior_lin = load_qlinear(wf, "prior_embedding", D, V);
  unembed = load_qlinear(wf, "unembedding", V, D);

  {
    const WTensor& sw = wf.get("skip_connection_weights.value", DT_F32, {6});
    for (int i = 0; i < 6; i++) skip_w[i] = sw.f32()[i];
  }

  int ki = 0, vi = 0;
  for (int l = 0; l < NL; l++) {
    std::string b = "blocks." + std::to_string(l) + ".";
    rsc[l] = wf.get(b + "residual_stream_coefficient.value", DT_F32, {1}).f32()[0];
    tec[l] = wf.get(b + "token_embedding_coefficient.value", DT_F32, {1}).f32()[0];
    std::string a = b + "attention.";

    if (KIMI[l]) {
      KimiLayer& L = kimi[ki];
      layer2kimi[l] = ki;
      L.qp = load_qlinear(wf, a + "query_projection", D, D);
      L.kp = load_qlinear(wf, a + "key_projection", D, D);
      L.vp = load_qlinear(wf, a + "value_projection", D, D);
      L.fg_up = load_qlinear(wf, a + "forget_gate_projection.up", DH, D);
      L.fg_down = load_qlinear(wf, a + "forget_gate_projection.down", D, DH);
      L.og_up = load_qlinear(wf, a + "output_gate_projection.up", DH, D);
      L.og_down = load_qlinear(wf, a + "output_gate_projection.down", D, DH);
      L.op = load_qlinear(wf, a + "output_projection", D, D);

      const char* convs[3] = {"query_convolution.weight",
                              "key_convolution.weight",
                              "value_convolution.weight"};
      const float* dst[3];
      for (int c = 0; c < 3; c++) {
        const WTensor& cw = wf.get(a + convs[c], DT_F32, {D, 4});
        float* wt = static_cast<float*>(fa.take(sizeof(float) * 4 * D));
        for (int j = 0; j < 4; j++)
          for (int ch = 0; ch < D; ch++) wt[j * D + ch] = cw.f32()[ch * 4 + j];
        dst[c] = wt;
      }
      L.wt_q = dst[0];
      L.wt_k = dst[1];
      L.wt_v = dst[2];

      {
        const WTensor& bw = wf.get(a + "beta_projection.weight", DT_F32, {NH, D});
        float* p = static_cast<float*>(fa.take(sizeof(float) * NH * D));
        std::memcpy(p, bw.f32(), sizeof(float) * NH * D);
        L.beta_w = p;
      }
      {
        const WTensor& dt = wf.get(a + "dt_bias", DT_F32, {D});
        float* p = static_cast<float*>(fa.take(sizeof(float) * D));
        std::memcpy(p, dt.f32(), sizeof(float) * D);
        L.dt_bias = p;
      }
      {
        const WTensor& gw =
            wf.get(a + "output_fused_norm_gate.weight", DT_F32, {DH});
        float* p = static_cast<float*>(fa.take(sizeof(float) * DH));
        std::memcpy(p, gw.f32(), sizeof(float) * DH);
        L.gn_w = p;
      }
      {
        const WTensor& al = wf.get(a + "log_baseline_decay_rate", DT_F32, {NH});
        for (int h = 0; h < NH; h++) L.a_neg[h] = -std::exp(al.f32()[h]);
      }
      ki++;
    } else {
      VanLayer& L = van[vi];
      layer2van[l] = vi;
      L.qp = load_qlinear(wf, a + "query_projection", D, D);
      L.kp = load_qlinear(wf, a + "key_projection", D, D);
      L.vp = load_qlinear(wf, a + "value_projection", D, D);
      L.op = load_qlinear(wf, a + "output_projection", D, D);
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

    mlp[l].up = load_qlinear(wf, b + "mlp.up", DMLP, D);
    mlp[l].down = load_qlinear(wf, b + "mlp.down", D, DMLP);
  }
  if (ki != 9 || vi != 3) die("layer pattern mismatch");

  {
    const WTensor& fi = wf.get("rope.inv_freq", DT_F32, {32});
    std::memcpy(inv_freq, fi.f32(), sizeof(inv_freq));
    const WTensor& si = wf.get("rope.sin", DT_F32, {ROPE_LEN, 32});
    const WTensor& co = wf.get("rope.cos", DT_F32, {ROPE_LEN, 32});
    float* s = static_cast<float*>(fa.take(sizeof(float) * ROPE_LEN * 32));
    float* c = static_cast<float*>(fa.take(sizeof(float) * ROPE_LEN * 32));
    std::memcpy(s, si.f32(), sizeof(float) * ROPE_LEN * 32);
    std::memcpy(c, co.f32(), sizeof(float) * ROPE_LEN * 32);
    rope_sin = s;
    rope_cos = c;
  }

  std::memset(kst, 0, sizeof(kst));
  std::memset(vst, 0, sizeof(vst));
}

void TransformerImpl::begin(int64_t rope_position_offset) {
  std::memset(kst, 0, sizeof(kst));  // KDA states and conv histories to zero
  t = 0;                             // invalidates the KV rings
  rope_off = rope_position_offset;
}

void TransformerImpl::kimi_attention(int ki, int l, const float* xn, float* y) {
  KimiLayer& L = kimi[ki];
  KimiState& st = kst[ki];
  alignas(32) float bq[D], bk[D], bv[D], cq[D], ck[D], cv[D];
  alignas(32) float fu[DH], graw[D], og192[D], braw[NH];
  alignas(32) float o192[D], gn[D];

  quantize_i8(xn, D, D, L.qp.s_act, q8);
  qmatvec(L.qp.w, L.qp.stride, L.qp.fold, D, q8, bq);
  quantize_i8(xn, D, D, L.kp.s_act, q8);
  qmatvec(L.kp.w, L.kp.stride, L.kp.fold, D, q8, bk);
  quantize_i8(xn, D, D, L.vp.s_act, q8);
  qmatvec(L.vp.w, L.vp.stride, L.vp.fold, D, q8, bv);

  conv4_silu(L.wt_q, st.hist[0][0], st.hist[0][1], st.hist[0][2], bq, cq, D);
  conv4_silu(L.wt_k, st.hist[1][0], st.hist[1][1], st.hist[1][2], bk, ck, D);
  conv4_silu(L.wt_v, st.hist[2][0], st.hist[2][1], st.hist[2][2], bv, cv, D);
  // shift conv histories (input of the conv, i.e. the projection outputs)
  const float* newest[3] = {bq, bk, bv};
  for (int c = 0; c < 3; c++) {
    std::memmove(st.hist[c][0], st.hist[c][1], sizeof(float) * 2 * D);
    std::memcpy(st.hist[c][2], newest[c], sizeof(float) * D);
  }
  capL(l, "kimi_conv_q", cq, D);
  capL(l, "kimi_conv_k", ck, D);
  capL(l, "kimi_conv_v", cv, D);

  quantize_i8(xn, D, D, L.fg_up.s_act, q8);
  qmatvec(L.fg_up.w, L.fg_up.stride, L.fg_up.fold, DH, q8, fu);
  quantize_i8(fu, DH, DH, L.fg_down.s_act, q8);
  qmatvec(L.fg_down.w, L.fg_down.stride, L.fg_down.fold, D, q8, graw);
  capL(l, "kimi_g_raw", graw, D);

  for (int h = 0; h < NH; h++)
    braw[h] = dot_f32(xn, L.beta_w + size_t(h) * D, D);
  capL(l, "kimi_beta_raw", braw, NH);

  quantize_i8(xn, D, D, L.og_up.s_act, q8);
  qmatvec(L.og_up.w, L.og_up.stride, L.og_up.fold, DH, q8, fu);
  quantize_i8(fu, DH, DH, L.og_down.s_act, q8);
  qmatvec(L.og_down.w, L.og_down.stride, L.og_down.fold, D, q8, og192);
  capL(l, "kimi_out_gate", og192, D);
  capL(l, "kimi_gate_in", og192, D);

  for (int h = 0; h < NH; h++)
    kda_head_step(st.S[h], cq + h * DH, ck + h * DH, cv + h * DH,
                  graw + h * DH, L.dt_bias + h * DH, L.a_neg[h],
                  sigmoid1f(braw[h]), o192 + h * DH);
  capL(l, "kimi_kda_out", o192, D);

  for (int h = 0; h < NH; h++)
    gated_rms_norm64(o192 + h * DH, og192 + h * DH, L.gn_w, gn + h * DH);
  capL(l, "kimi_gated_norm_out", gn, D);

  quantize_i8(gn, D, D, L.op.s_act, q8);
  qmatvec(L.op.w, L.op.stride, L.op.fold, D, q8, y);
}

void TransformerImpl::van_attention(int vi, int l, const float* xn, float* y) {
  VanLayer& L = van[vi];
  VanState& st = vst[vi];
  alignas(32) float q[D], k[D], v[D], pre[D];
  alignas(32) int8_t qq[D], kk[D], vv[D];

  quantize_i8(xn, D, D, L.qp.s_act, q8);
  qmatvec(L.qp.w, L.qp.stride, L.qp.fold, D, q8, q);
  quantize_i8(xn, D, D, L.kp.s_act, q8);
  qmatvec(L.kp.w, L.kp.stride, L.kp.fold, D, q8, k);
  quantize_i8(xn, D, D, L.vp.s_act, q8);
  qmatvec(L.vp.w, L.vp.stride, L.vp.fold, D, q8, v);

  for (int h = 0; h < NH; h++) rms_norm_vec(q + h * DH, q + h * DH, DH);
  for (int h = 0; h < NH; h++) rms_norm_vec(k + h * DH, k + h * DH, DH);

  int64_t pos = rope_off + t;
  const float *sp, *cp;
  float sbuf[32], cbuf[32];
  if (pos < ROPE_LEN) {
    sp = rope_sin + size_t(pos) * 32;
    cp = rope_cos + size_t(pos) * 32;
  } else {
    float fpos = static_cast<float>(pos);
    for (int i = 0; i < 32; i++) {
      float ang = fpos * inv_freq[i];
      sbuf[i] = std::sin(ang);
      cbuf[i] = std::cos(ang);
    }
    sp = sbuf;
    cp = cbuf;
  }
  rope_apply(q, sp, cp);
  rope_apply(k, sp, cp);

  for (int h = 0; h < NH; h++) {
    quantize_i8(q + h * DH, DH, DH, L.sq[h], qq + h * DH);
    quantize_i8(k + h * DH, DH, DH, L.sk[h], kk + h * DH);
    quantize_i8(v + h * DH, DH, DH, L.sv[h], vv + h * DH);
  }
  if (cap_fn) {
    alignas(32) float fq[D];
    const struct {
      const char* quant;
      const char* ints;
      const int8_t* qv;
      const float* sc;
    } items[3] = {{"attn_q_quant", "attn_q_int8", qq, L.sq},
                  {"attn_k_quant", "attn_k_int8", kk, L.sk},
                  {"attn_v_quant", "attn_v_int8", vv, L.sv}};
    for (const auto& it : items) {
      for (int h = 0; h < NH; h++)
        for (int i = 0; i < DH; i++)
          fq[h * DH + i] =
              it.sc[h] * static_cast<float>(it.qv[h * DH + i]);
      capL(l, it.quant, fq, D);
      for (int i = 0; i < D; i++) fq[i] = static_cast<float>(it.qv[i]);
      capL(l, it.ints, fq, D);
    }
  }

  int slot = static_cast<int>(t % WIN);
  std::memcpy(st.kring[slot], kk, D);
  std::memcpy(st.vring[slot], vv, D);

  float thr = lowprob_skip ? lowprob_threshold : 0.0f;
  int64_t n_valid = t + 1;
  if (n_valid < WIN)
    attention_step_var(qq, st.kring[0], st.vring[0], L.coef, L.sv,
                       static_cast<int>(n_valid), pre, thr);
  else
    attention_step_fixed(qq, st.kring[0], st.vring[0], L.coef, L.sv, pre, thr);
  capL(l, "attn_pre_oproj", pre, D);

  quantize_i8(pre, D, D, L.op.s_act, q8);
  qmatvec(L.op.w, L.op.stride, L.op.fold, D, q8, y);
}

void TransformerImpl::step(uint8_t token, const float* prior,
                           float* probs_out) {
  if (token >= V) die("token out of range");
  const float* tok = tok_table + size_t(token) * D;
  float* x = xb;
  float* xn = xnb;

  // embedding path: x0 = normed token row + normed prior embedding
  quantize_i8(prior, V, PRIOR_STRIDE, prior_lin.s_act, q8);
  qmatvec(prior_lin.w, prior_lin.stride, prior_lin.fold, D, q8, yb);
  rms_norm_vec(yb, yb, D);
  for (int i = 0; i < D; i++) x[i] = tok[i] + yb[i];
  cap("00_x0", x, D);

  for (int l = 0; l < NL; l++) {
    if (l >= 6) {  // skip connections: 6<-5, 7<-4, ..., 11<-0
      const float* s = skip_store[11 - l];
      float w = skip_w[l - 6];
      for (int i = 0; i < D; i++) x[i] += w * s[i];
    }
    if (override_fn) {  // debug teacher-forcing
      const float* forced = override_fn(l);
      if (forced) std::memcpy(x, forced, sizeof(float) * D);
    }
    capL(l, "block_input", x, D);

    {  // token-embedding connection
      float a = rsc[l], bcoef = tec[l];
      for (int i = 0; i < D; i++) x[i] = a * x[i] + bcoef * tok[i];
    }

    rms_norm_vec(x, xn, D);
    if (KIMI[l])
      kimi_attention(layer2kimi[l], l, xn, yb);
    else
      van_attention(layer2van[l], l, xn, yb);
    capL(l, "attn_out", yb, D);
    for (int i = 0; i < D; i++) x[i] += yb[i];

    rms_norm_vec(x, xn, D);
    const MlpW& m = mlp[l];
    quantize_i8(xn, D, D, m.up.s_act, q8);
    qmatvec(m.up.w, m.up.stride, m.up.fold, DMLP, q8, h768);
    for (int j = 0; j < DMLP; j++) {
      float hj = h768[j];
      h768[j] = hj > 0.0f ? hj * hj : 0.0f;  // relu^2
    }
    quantize_i8(h768, DMLP, DMLP, m.down.s_act, q8);
    qmatvec(m.down.w, m.down.stride, m.down.fold, D, q8, yb);
    capL(l, "mlp_out", yb, D);
    for (int i = 0; i < D; i++) x[i] += yb[i];
    capL(l, "block_output", x, D);

    if (l < 6) std::memcpy(skip_store[l], x, sizeof(float) * D);
  }

  rms_norm_vec(x, xn, D);
  cap("12_final_norm", xn, D);
  quantize_i8(xn, D, D, unembed.s_act, q8);
  qmatvec(unembed.w, unembed.stride, unembed.fold, V, q8, logits);
  for (int i = 0; i < V; i++)
    logits[i] = 15.0f * std::tanh(logits[i] / 15.0f);  // logit softcap
  cap("12_logits", logits, V);

  float m = logits[0];
  for (int i = 1; i < V; i++)
    if (logits[i] > m) m = logits[i];
  float den = 0.0f;
  for (int i = 0; i < V; i++) {
    float e = std::exp(logits[i] - m);
    probs_out[i] = e;
    den += e;
  }
  for (int i = 0; i < V; i++) probs_out[i] /= den;
  cap("12_probabilities", probs_out, V);

  t++;
}

Transformer::Transformer(const char* weights_path)
    : impl(new TransformerImpl()) {
  impl->load(weights_path);
}

Transformer::~Transformer() = default;

void Transformer::begin_article(int64_t rope_position_offset) {
  impl->begin(rope_position_offset);
}

void Transformer::step(uint8_t token, const uint16_t* prior_f16,
                       float* probs_out) {
  f16_to_f32(prior_f16, impl->prior_f32, V);
  for (int i = V; i < PRIOR_STRIDE; i++) impl->prior_f32[i] = 0.0f;
  impl->step(token, impl->prior_f32, probs_out);
}

void Transformer::step(uint8_t token, const float* prior205,
                       float* probs_out) {
  impl->step(token, prior205, probs_out);
}

const float* Transformer::last_logits() const { return impl->logits; }

void Transformer::set_attention_lowprob_skip(bool enabled, float threshold) {
  impl->lowprob_skip = enabled;
  impl->lowprob_threshold = threshold;
}

void Transformer::set_capture(CaptureFn fn) { impl->cap_fn = std::move(fn); }

void Transformer::set_block_input_override(BlockInputOverrideFn fn) {
  impl->override_fn = std::move(fn);
}

}  // namespace fx2
