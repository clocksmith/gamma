#ifndef GAMMA_FX2_XML_WORD_CONTEXT_V1_HPP
#define GAMMA_FX2_XML_WORD_CONTEXT_V1_HPP
#include "fx2_xml_field_observer_v1.hpp"
#include <memory>

namespace gamma_xml_word {
using gamma_xml_field::Bytes;
// This component changes one existing byte context; it adds no predictor or
// model allocation. The native adapter owns the referenced context scalar.
class Context {
 public:
  bool begin(const std::vector<std::string>& words, uint64_t raw_bytes, char arm) {
    if (active_ || (arm != 'K' && arm != 'D' && arm != 'S')) return false;
    // Bound the copy made by the immutable observer before constructing it.
    if (raw_bytes > 1000000000 || words.size() > 44880) return false;
    size_t total = 0;
    for (const auto& word : words) {
      if (word.empty() || word.size() > 4096) return false;
      total += word.size();
      for (unsigned char c : word) if (c < 'a' || c > 'z') return false;
    }
    if (total > 16 * 1024 * 1024) return false;
    observer_.reset(new gamma_xml_field::Observer(words, raw_bytes));
    arm_ = arm; active_ = true;
    return true;
  }
  bool observe(uint8_t modeled_byte, uint64_t parent_context,
               uint64_t& context, Bytes& raw) {
    if (!active_ || finished_ || !observer_->observe(modeled_byte, raw)) return false;
    current_ = observer_->field(); delayed_ = ring_[position_];
    ring_[position_] = current_; position_ = (position_ + 1) % ring_.size();
    ++count_;
    effective_ = arm_ == 'D' ? current_ : arm_ == 'S' ? delayed_ : 0;
    parent_ = parent_context;
    context_ = parent_ ^ (uint64_t(effective_) * UINT64_C(0x9e3779b97f4a7c15));
    context = context_;
    return true;
  }
  bool finish() {
    if (!active_ || finished_ || !observer_->finish()) return false;
    finished_ = true; return true;
  }
  uint8_t field() const { return current_; }
  uint8_t delayed() const { return delayed_; }
  Bytes state() const {
    Bytes out{'X','W','C','1', uint8_t(arm_), uint8_t(active_), uint8_t(finished_),
              current_, delayed_, effective_};
    for (uint64_t value : {count_, uint64_t(position_), parent_, context_})
      for (unsigned shift = 0; shift < 64; shift += 8) out.push_back(uint8_t(value >> shift));
    out.insert(out.end(), ring_.begin(), ring_.end());
    if (observer_) {
      const auto state = observer_->state(); out.insert(out.end(), state.begin(), state.end());
    }
    return out;
  }
 private:
  std::unique_ptr<gamma_xml_field::Observer> observer_;
  std::array<uint8_t,4096> ring_{};
  size_t position_ = 0;
  uint64_t count_ = 0, parent_ = 0, context_ = 0;
  char arm_ = 'K';
  bool active_ = false, finished_ = false;
  uint8_t current_ = 0, delayed_ = 0, effective_ = 0;
};
}  // namespace gamma_xml_word
#endif
