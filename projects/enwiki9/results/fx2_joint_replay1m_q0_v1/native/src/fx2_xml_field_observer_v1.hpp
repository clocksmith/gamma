#ifndef GAMMA_FX2_XML_FIELD_OBSERVER_V1_HPP
#define GAMMA_FX2_XML_FIELD_OBSERVER_V1_HPP

#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace gamma_xml_field {
using Bytes = std::vector<uint8_t>;

// Exact spellings from the standalone opcode field repair. This is a suffix
// recognizer, not an XML validator: malformed/unrecognized bytes stay literal.
class RawField {
 public:
  uint8_t field() const { return field_; }
  void observe(uint8_t byte) {
    for (size_t i = 1; i < tail_.size(); ++i) tail_[i - 1] = tail_[i];
    tail_.back() = byte;
    if (used_ < tail_.size()) ++used_;
    if (byte != '>') return;
    static constexpr std::string_view markers[] = {
      "<title>", "</title>", "<id>", "</id>",
      "<timestamp>", "</timestamp>", "<username>", "</username>",
      "<comment>", "</comment>", "<text xml:space=\"preserve\">", "</text>"};
    for (unsigned i = 0; i < 12; ++i) {
      const auto marker = markers[i];
      if (marker.size() > used_) continue;
      bool equal = true;
      for (size_t j = 0; j < marker.size(); ++j)
        equal = equal && tail_[tail_.size() - marker.size() + j] == uint8_t(marker[j]);
      if (equal) { field_ = i % 2 ? 0 : uint8_t(i / 2 + 1); break; }
    }
  }
  Bytes state() const {
    Bytes out{field_, used_};
    out.insert(out.end(), tail_.begin(), tail_.end());
    return out;
  }
 private:
  uint8_t field_ = 0, used_ = 0;
  std::array<uint8_t, sizeof("<text xml:space=\"preserve\">") - 1> tail_{};
};

inline uint8_t unswap(uint8_t value) {
  if (value >= '{' && value < 127) value -= 43;
  else if (value >= 'P' && value < 'T') value += 43;
  else if ((value >= ':' && value <= '?') || (value >= 'J' && value <= 'O')) value ^= 0x70;
  if (value == 'X' || value == '`') value ^= 'X' ^ '`';
  return value;
}

// One modeled WRT text segment: flag 7 then encoded events, no outer header.
// The immutable dictionary is an external, hash-bound dependency. Construct
// only at the real segment boundary, never while pretraining the native model.
// No state becomes visible until a complete event has been decoded.
class Observer {
 public:
  explicit Observer(const std::vector<std::string>& words, uint64_t raw_limit)
      : words_(words), raw_limit_(raw_limit) {
    uint64_t bytes = 0;
    failed_ = raw_limit > 1000000000 || words.size() > 44880;
    for (const auto& word : words) {
      bytes += word.size();
      if (word.empty() || word.size() > 4096) failed_ = true;
      for (unsigned char c : word) if (c < 'a' || c > 'z') failed_ = true;
    }
    if (bytes > 16 * 1024 * 1024) failed_ = true;
  }
  uint8_t field() const { return raw_.field(); }
  uint64_t raw_count() const { return raw_count_; }
  bool failed() const { return failed_; }

  // emitted is replaced only on success. Controls/partial tokens emit nothing.
  bool observe(uint8_t stored, Bytes& emitted) {
    if (failed_ || finished_ || modeled_count_ >= 4 * raw_limit_ + 4096) return fail();
    ++modeled_count_;
    if (!flag_seen_) {
      if (stored != 7) return fail();
      flag_seen_ = true; emitted.clear(); return true;
    }
    const uint8_t c = unswap(stored);
    pending_[pending_size_++] = c;
    const uint8_t first = pending_[0];
    Bytes result;
    bool next_upper = upper_, next_capital = capital_;
    if (first == 12) {
      if (pending_size_ == 1) { emitted.clear(); return true; }
      next_upper = false; result.push_back(c);
    } else if (first == 7 || first == 6 || first == 64) {
      if (first == 64) next_capital = true;
      else next_upper = first == 7;
    } else if (first >= 128) {
      uint32_t index = first - 128;
      if (first > 207) {
        if (pending_size_ == 1) { emitted.clear(); return true; }
        const uint8_t second = pending_[1];
        if (second < 128) return fail();
        if (second > 207) {
          if (first < 240 || second > 239) return fail();
          if (pending_size_ == 2) { emitted.clear(); return true; }
          if (c < 128 || c > 207) return fail();
          index = 3920 + (first - 240) * 32 * 80 + (second - 208) * 80 + c - 128;
        } else index = 80 + (first - 208) * 80 + second - 128;
      }
      if (index >= words_.size()) return fail();
      const auto& word = words_[index];
      for (size_t i = 0; i < word.size(); ++i) {
        uint8_t value = uint8_t(word[i]);
        // Preserve the existing WRT inverse's simultaneous-case semantics.
        if (i == 0 && next_capital) { value -= 32; next_capital = false; }
        if (next_upper) value -= 32;
        result.push_back(value);
      }
    } else {
      uint8_t value = first;
      if (!((value >= 'a' && value <= 'z') || (value >= 'A' && value <= 'Z')))
        next_upper = false;
      if (next_capital || next_upper) value -= 32;
      next_capital = false;
      result.push_back(value);
    }
    if (result.size() > raw_limit_ - raw_count_) return fail();
    for (uint8_t value : result) raw_.observe(value);
    raw_count_ += result.size(); upper_ = next_upper; capital_ = next_capital;
    pending_ = {}; pending_size_ = 0;
    emitted.swap(result);
    return true;
  }
  bool finish() {
    if (failed_ || finished_ || !flag_seen_ || pending_size_ || raw_count_ != raw_limit_) return fail();
    finished_ = true; return true;
  }
  // Canonical little-endian state for external cryptographic hashing. Dictionary
  // identity must be bound alongside these bytes; it is not reserialized here.
  Bytes state() const {
    Bytes out{'X','F','O','1', uint8_t(flag_seen_), uint8_t(failed_),
              uint8_t(finished_), uint8_t(upper_), uint8_t(capital_), pending_size_};
    out.insert(out.end(), pending_.begin(), pending_.end());
    for (uint64_t value : {raw_limit_, raw_count_, modeled_count_})
      for (unsigned shift = 0; shift < 64; shift += 8) out.push_back(uint8_t(value >> shift));
    const auto raw = raw_.state(); out.insert(out.end(), raw.begin(), raw.end());
    return out;
  }
 private:
  bool fail() { failed_ = true; return false; }
  const std::vector<std::string> words_;
  const uint64_t raw_limit_;
  uint64_t raw_count_ = 0, modeled_count_ = 0;
  bool flag_seen_ = false, failed_ = false, finished_ = false, upper_ = false, capital_ = false;
  std::array<uint8_t, 3> pending_{};
  uint8_t pending_size_ = 0;
  RawField raw_;
};
}  // namespace gamma_xml_field
#endif
