#ifndef GAMMA_FX2_TITLE_MEMORY_V1_HPP
#define GAMMA_FX2_TITLE_MEMORY_V1_HPP

#include "../fx2_xml_field_observer_v1.hpp"
#include <algorithm>

namespace gamma_title_memory {
constexpr size_t kCapacity = 128;
constexpr size_t kVocabulary = 205;
constexpr std::array<uint8_t, 256> token_map() {
  constexpr uint8_t bits[32] = {232,22,4,0,255,255,255,3,1,252,15,249,254,255,255,7,
                                255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255};
  std::array<uint8_t, 256> result{};
  uint8_t index = 0;
  for (unsigned byte = 0; byte < 256; ++byte)
    result[byte] = bits[byte / 8] & (1 << (byte % 8)) ? index++ : 255;
  return result;
}
inline constexpr auto kTokenMap = token_map();

struct Features {
  uint8_t count = 0;
  std::array<uint8_t, kVocabulary> aligned{}, wrong{};
  gamma_xml_field::Bytes bytes() const {
    gamma_xml_field::Bytes result{count};
    result.insert(result.end(), aligned.begin(), aligned.end());
    result.insert(result.end(), wrong.begin(), wrong.end());
    return result;
  }
};

// Keep the first128 modeled tokens belonging to complete title-content
// emissions. Publish only after the complete closing title tag. Input tokens
// are native205 vocabulary indices; the WRT observer consumes stored bytes.
// A feature is a bag of these tokens: word/token order is intentionally lost.
// The same shared neural embeddings can describe this bounded past context.
class Memory {
 public:
  Memory(const std::vector<std::string>& words, uint64_t raw_limit)
      : inverse_(words, raw_limit) {}

  bool observe(uint8_t stored, uint8_t token, gamma_xml_field::Bytes& raw) {
    if (token >= kVocabulary || token != kTokenMap[stored] || failed_) { failed_ = true; return false; }
    if (pending_.size() == kCapacity) pending_.erase(pending_.begin());
    pending_.push_back(token);
    if (!inverse_.observe(stored, raw)) { failed_ = true; return false; }
    if (raw.empty()) return true;
    const bool content = fields_.field() == 1 && collecting_ && raw.front() != '<';
    if (content) {
      const size_t n = std::min(kCapacity - building_.size(), pending_.size());
      building_.insert(building_.end(), pending_.begin(), pending_.begin() + n);
    }
    for (uint8_t c : raw) {
      const uint8_t before = fields_.field();
      fields_.observe(c);
      const uint8_t after = fields_.field();
      if (before != 1 && after == 1) {
        building_.clear(); collecting_ = true;
      } else if (before == 1) {
        if (c == '<') collecting_ = false;
        if (after == 0) {
          previous_ = current_;
          current_ = building_;
          building_.clear(); collecting_ = false;
        }
      }
    }
    pending_.clear();
    if (fields_.field() != inverse_.field()) { failed_ = true; return false; }
    return true;
  }

  Features features() const {
    Features result;
    if (failed_ || fields_.field() != 6) return result;
    const size_t n = std::min(current_.size(), previous_.size());
    if (n < 3) return result;
    result.count = uint8_t(n);
    // Same prefix length and capacities, different completed titles. These
    // donors can be related; this control is causal, not statistically random.
    for (size_t i = 0; i < n; ++i) {
      ++result.aligned[current_[i]];
      ++result.wrong[previous_[i]];
    }
    return result;
  }

  bool finish() { return !failed_ && inverse_.finish(); }

  gamma_xml_field::Bytes state() const {
    auto result = inverse_.state();
    const auto fields = fields_.state();
    result.insert(result.end(), fields.begin(), fields.end());
    result.push_back(uint8_t(collecting_)); result.push_back(uint8_t(failed_));
    for (const auto* values : {&pending_, &building_, &current_, &previous_}) {
      result.push_back(uint8_t(values->size()));
      result.insert(result.end(), values->begin(), values->end());
    }
    return result;
  }

 private:
  gamma_xml_field::Observer inverse_;
  gamma_xml_field::RawField fields_;
  bool collecting_ = false, failed_ = false;
  gamma_xml_field::Bytes pending_, building_, current_, previous_;
};
}  // namespace gamma_title_memory
#endif
