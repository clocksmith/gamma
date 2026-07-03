#include <cstdint>
#include <cstdio>
#include "encoder.h"

Encoder::Encoder(std::ofstream* os, Predictor* p) : os_(os), x1_(0),
    x2_(0xffffffff), p_(p)
#ifdef CMIX_TRACE_ROWS
    , bit_count_(0)
#endif
    {}

void Encoder::WriteByte(unsigned int byte) {
  os_->put(byte);
}

unsigned int Encoder::Discretize(float p) {
  return 1 + 65534 * p;
}

void Encoder::Encode(int bit) {
  const unsigned int p = Discretize(p_->Predict());
#ifdef CMIX_TRACE_ROWS
  std::fprintf(stderr, "CMIX_RESIDUAL_ROW pos=%llu bit_pos=%d bit=%d p1=%u\n",
      bit_count_ / 8, static_cast<int>(bit_count_ & 7), bit, p);
#endif
  const unsigned int xmid = x1_ + ((x2_ - x1_) >> 16) * p +
      (((x2_ - x1_) & 0xffff) * p >> 16);
  if (bit) {
    x2_ = xmid;
  } else {
    x1_ = xmid + 1;
  }
  p_->Perceive(bit);
#ifdef CMIX_TRACE_ROWS
  ++bit_count_;
#endif

  while (((x1_^x2_) & 0xff000000) == 0) {
    WriteByte(x2_ >> 24);
    x1_ <<= 8;
    x2_ = (x2_ << 8) + 255;
  }
}

void Encoder::Flush() {
  while (((x1_^x2_) & 0xff000000) == 0) {
    WriteByte(x2_ >> 24);
    x1_ <<= 8;
    x2_ = (x2_ << 8) + 255;
  }
  WriteByte(x2_ >> 24);
}
