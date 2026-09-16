#include "encoder.h"
#include "../gamma-final-bit-head-audit.h"
#include "../gamma-coder-trace.h"
#ifdef GAMMA_EXPERT_RELEASE
#include "../gamma-expert-release.h"
#endif

Encoder::Encoder(std::ofstream* os, Predictor* p) : os_(os), x1_(0),
    x2_(0xffffffff), p_(p) {}

void Encoder::WriteByte(unsigned int byte) {
  out_.push_back(byte);
}

unsigned int Encoder::Discretize(float p) {
  return 1 + 65534 * p;
}

void Encoder::Encode(int bit) {
  const float gamma_parent_probability = p_->Predict();
  const unsigned int p = gamma_final_bit_head::predict(Discretize(gamma_parent_probability));
  gamma_fx2_trace::Record gamma_coder(gamma_parent_probability,p,x1_,x2_);
#ifdef GAMMA_EXPERT_RELEASE
  p = gamma_expert_release::predict(p);
#endif
  const unsigned int xmid = x1_ + ((x2_ - x1_) >> 16) * p +
      (((x2_ - x1_) & 0xffff) * p >> 16);
  if (bit) {
    x2_ = xmid;
  } else {
    x1_ = xmid + 1;
  }

#ifdef GAMMA_EXPERT_RELEASE
  gamma_expert_release::observe(bit);
#endif
  gamma_final_bit_head::observe(bit);
  p_->Perceive(bit);

  while (((x1_^x2_) & 0xff000000) == 0) {
    WriteByte(x2_ >> 24);
    x1_ <<= 8;
    x2_ = (x2_ << 8) + 255;
  }
  gamma_coder.Finish(bit,x1_,x2_);
}

void Encoder::Flush() {
  while (((x1_^x2_) & 0xff000000) == 0) {
    WriteByte(x2_ >> 24);
    x1_ <<= 8;
    x2_ = (x2_ << 8) + 255;
  }
  WriteByte(x2_ >> 24);

  auto* data = reinterpret_cast<const char*>(out_.data());
  os_->write(data, out_.size());
}

