// fx2-cmix transformer: single-thread streaming inference (SPEC.md section 6)
#pragma once

#include <cstdint>
#include <functional>
#include <memory>

namespace fx2 {

struct TransformerImpl;

struct Transformer {
  explicit Transformer(const char* weights_path);
  ~Transformer();
  Transformer(const Transformer&) = delete;
  Transformer& operator=(const Transformer&) = delete;

  // resets KV rings, KDA states and conv histories; rope positions for the
  // article are rope_position_offset + local position (0-based)
  void begin_article(int64_t rope_position_offset = 0);

  // feed input token t and its prior (205 float16 values); fills
  // probs_out[205] with the fp32 distribution over the NEXT token
  void step(uint8_t token, const uint16_t* prior_f16, float* probs_out);
  // same with an fp32 prior row
  void step(uint8_t token, const float* prior205, float* probs_out);

  // the 205 post-softcap logits of the last step (valid until the next step)
  const float* last_logits() const;

  // optional approximation (default OFF = exact math): in vanilla attention,
  // skip positions whose score is more than `threshold` below the max
  // (excluded from the softmax denominator too). SPEC default threshold 21.
  // NOTE: measured score spreads on the test set stay below ~15, so at
  // threshold 21 nothing is ever skipped and the output is bit-identical.
  void set_attention_lowprob_skip(bool enabled, float threshold = 21.0f);

  // debug capture: when set, called during step() with the values of every
  // named intermediate (names match the dump component files, e.g. "00_x0",
  // "03_attn_q_int8", "12_logits"); int8 intermediates are passed as floats
  using CaptureFn = std::function<void(const char* name, const float* data, int n)>;
  void set_capture(CaptureFn fn);

  // debug teacher-forcing: when set, called at the top of every block (after
  // the skip-connection add); a non-null return replaces the residual stream
  // with the given 192 floats (e.g. the reference block_input dump), so each
  // block is tested against exact reference inputs without chained divergence
  using BlockInputOverrideFn = std::function<const float*(int layer)>;
  void set_block_input_override(BlockInputOverrideFn fn);

 private:
  std::unique_ptr<TransformerImpl> impl;
};

}  // namespace fx2
