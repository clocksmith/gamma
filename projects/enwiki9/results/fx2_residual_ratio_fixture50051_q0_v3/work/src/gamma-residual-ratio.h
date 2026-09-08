// Native residual-ratio boundary v1. No model, frontend, or coder is supplied.
#ifndef GAMMA_FX2_RESIDUAL_RATIO_V1_HPP
#define GAMMA_FX2_RESIDUAL_RATIO_V1_HPP
#include <algorithm>
#include <array>
#include <cfenv>
#include <cstdint>
#include <cstring>
#include <limits>
#include <vector>

namespace gamma_ratio {
class Ratio {
 public:
  static constexpr uint32_t Q = 65536, prior = 32 * Q;
  bool configure(unsigned size, char arm) {
    if (size < 2 || size > 256 || !valid_arm(arm)) return false;
    *this = Ratio(); n_ = size; arm_ = arm; return true;
  }
  static bool units(float p, uint64_t& value) {
    static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559,
                  "IEEE float32 required");
    uint32_t bits; std::memcpy(&bits, &p, 4);
    // Includes the exact native float32 floor 1e-6, not its nearest half.
    if (bits < UINT32_C(0x358637bd) || bits > UINT32_C(0x3f800000)) return false;
    unsigned exp = (bits >> 23) & 255;
    value = uint64_t((bits & 0x7fffff) | 0x800000) << (exp - 107);
    return true;
  }
  bool predict(float* probabilities) {
    if (!n_ || pending_ || !probabilities || position_ >= (UINT64_C(1) << 63)-1 ||
        std::fegetround() != FE_TONEAREST) return false;
    std::array<uint64_t,256> mass{}, remainders{};
    std::array<uint32_t,256> expected{};
    std::array<unsigned,256> order{};
    uint64_t total = 0;
    for (unsigned i=0; i<n_; ++i) {
      if (!units(probabilities[i], mass[i])) return false;
      total += mass[i]; order[i] = i;
    }
    uint32_t assigned = 0;
    for (unsigned i=0; i<n_; ++i) {
      uint64_t scaled = mass[i] * Q;  // <= 2^59.
      expected[i] = uint32_t(scaled / total);
      remainders[i] = scaled % total; assigned += expected[i];
    }
    std::sort(order.begin(), order.begin()+n_, [&](unsigned a, unsigned b) {
      return remainders[a] != remainders[b] ? remainders[a] > remainders[b] : a < b;
    });
    for (unsigned i=0; i<Q-assigned; ++i) ++expected[order[i]];
    if (arm_ == 'D' || arm_ == 'S') {
      for (unsigned i=0; i<n_; ++i) {
        uint64_t scale = uint64_t(prior+observed_[i]) * Q / (prior+expected_[i]);
        scale = std::max(uint64_t(Q/4), std::min(uint64_t(Q*4), scale));
        // Product has <= 43 significant bits, exactly representable in double.
        // The sole rounded step is the cast to float with nearest-even mode.
        probabilities[i] = float(double(probabilities[i]) * double(scale) / double(Q));
      }
    }
    pending_expected_ = expected; pending_ = true; return true;
  }
  bool observe(unsigned symbol) {
    if (!pending_ || symbol >= n_) return false;
    if (arm_ != 'P') {
      for (unsigned i=0; i<n_; ++i) expected_[i] += pending_expected_[i];
      observed_[arm_ == 'S' ? (symbol+1)%n_ : symbol] += Q;
      if ((position_+1)%256 == 0) {
        for (unsigned i=0; i<n_; ++i) { observed_[i] /= 2; expected_[i] /= 2; }
      }
    }
    ++position_; pending_ = false; pending_expected_.fill(0); return true;
  }
  bool pending() const { return pending_; }
  uint64_t position() const { return position_; }
  std::vector<uint8_t> serialize() const {
    std::vector<uint8_t> bytes{'G','R','R','1'};
    put(bytes, n_, 2); put(bytes, uint8_t(arm_), 1); put(bytes, pending_, 1);
    put(bytes, position_, 8);
    for (unsigned i=0; i<n_; ++i) {
      put(bytes, observed_[i], 4); put(bytes, expected_[i], 4); put(bytes, pending_expected_[i], 4);
    }
    return bytes;
  }
  bool restore(const uint8_t* bytes, size_t length) {
    if (!bytes || length < 40 || length > 3088 || std::memcmp(bytes,"GRR1",4)) return false;
    unsigned n = get(bytes+4,2); char arm = char(bytes[6]); unsigned pending = bytes[7];
    if (n_ && (n != n_ || arm != arm_)) return false;
    Ratio next;
    if (!next.configure(n,arm) || length != 16+12*n || pending > 1) return false;
    next.pending_ = pending; next.position_ = get(bytes+8,8);
    if (next.position_ >= (UINT64_C(1)<<63) ||
        (pending && next.position_ == (UINT64_C(1)<<63)-1)) return false;
    uint64_t observed=0, expected=0, waiting=0;
    for (unsigned i=0; i<n; ++i) {
      next.observed_[i] = get(bytes+16+12*i,4);
      next.expected_[i] = get(bytes+20+12*i,4);
      next.pending_expected_[i] = get(bytes+24+12*i,4);
      if (next.observed_[i] > 512*Q || next.expected_[i] > 512*Q || next.pending_expected_[i] > Q) return false;
      observed += next.observed_[i]; expected += next.expected_[i]; waiting += next.pending_expected_[i];
    }
    if (waiting != (pending ? Q : 0) || !next.valid_total(observed) || !next.valid_total(expected)) return false;
    *this = next; return true;
  }
 private:
  unsigned n_=0; char arm_='P'; bool pending_=false; uint64_t position_=0;
  std::array<uint32_t,256> observed_{}, expected_{}, pending_expected_{};
  static bool valid_arm(char arm) { return arm=='P' || arm=='K' || arm=='D' || arm=='S'; }
  bool valid_total(uint64_t total) const {
    if (arm_=='P') return total==0;
    if (position_<256) return total==position_*Q;
    uint64_t phase=position_%256;
    return total >= (phase+128)*Q-2*n_ && total <= (phase+256)*Q;
  }
  static void put(std::vector<uint8_t>& bytes, uint64_t v, unsigned n) {
    for (unsigned i=0;i<n;++i) bytes.push_back(uint8_t(v>>(8*i)));
  }
  static uint64_t get(const uint8_t* bytes, unsigned n) {
    uint64_t v=0; for(unsigned i=0;i<n;++i) v |= uint64_t(bytes[i])<<(8*i); return v;
  }
};
}  // namespace gamma_ratio
#endif
