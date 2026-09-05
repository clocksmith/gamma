#pragma once

// Gamma's native Q16 binary arithmetic boundary. The arithmetic follows
// lib/predictor.py, but checkpoints include every future-affecting coder byte.
// This is reusable implementation infrastructure, not compression evidence.

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace gamma_enwiki9::midas_codec {

using Bytes = std::vector<std::uint8_t>;

inline void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}

inline void put(Bytes& out, std::uint64_t value, unsigned width) {
  require(width <= 8, "invalid integer width");
  for (unsigned i = 0; i != width; ++i)
    out.push_back(static_cast<std::uint8_t>(value >> (8 * i)));
}

class Reader {
 public:
  explicit Reader(const Bytes& bytes) : bytes_(bytes) {}
  std::uint64_t get(unsigned width) {
    require(width <= 8 && width <= remaining(), "truncated integer");
    std::uint64_t result = 0;
    for (unsigned i = 0; i != width; ++i)
      result |= std::uint64_t(bytes_[cursor_++]) << (8 * i);
    return result;
  }
  Bytes take(std::size_t count) {
    require(count <= remaining(), "truncated byte vector");
    Bytes result(bytes_.begin() + cursor_, bytes_.begin() + cursor_ + count);
    cursor_ += count;
    return result;
  }
  void magic(const char* expected, std::size_t length) {
    require(length <= remaining(), "truncated magic");
    for (std::size_t i = 0; i != length; ++i)
      require(bytes_[cursor_++] == static_cast<std::uint8_t>(expected[i]),
              "wrong format magic");
  }
  std::size_t remaining() const { return bytes_.size() - cursor_; }
  void end() const { require(remaining() == 0, "unexpected trailing bytes"); }

 private:
  const Bytes& bytes_;
  std::size_t cursor_ = 0;
};

inline std::uint32_t crc32(const Bytes& data) {
  std::uint32_t value = 0xffffffffU;
  for (std::uint8_t byte : data) {
    value ^= byte;
    for (unsigned bit = 0; bit != 8; ++bit)
      value = (value >> 1) ^ (0xedb88320U & (0U - (value & 1U)));
  }
  return ~value;
}

// The frontend is explicitly the identity on raw bytes, in MSB-first order.
// No WRT, NNCP vocabulary, or hidden dictionary can be substituted for it.
struct Frame {
  static constexpr std::uint8_t raw_byte_identity_v1 = 1;
  std::uint32_t model_tag = 0;
  std::uint8_t arm = 0;  // 0=P/K, 1=F, 2=S; bookkeeping is never transmitted.
  std::uint64_t raw_bytes = 0;
  std::uint32_t raw_crc32 = 0;
  Bytes payload;
};

inline Bytes frame(const Bytes& raw, const Bytes& payload,
                   std::uint32_t model_tag, std::uint8_t arm) {
  require(arm <= 2, "unknown causal arm");
  Bytes out{'G', 'M', 'A', 'C', 1, Frame::raw_byte_identity_v1, arm, 0};
  put(out, model_tag, 4);
  put(out, raw.size(), 8);
  put(out, payload.size(), 8);
  put(out, crc32(raw), 4);
  put(out, crc32(payload), 4);
  out.insert(out.end(), payload.begin(), payload.end());
  return out;
}

inline Frame unframe(const Bytes& bytes, std::uint32_t expected_model_tag,
                     std::uint64_t maximum_raw_bytes,
                     std::uint64_t maximum_payload_bytes) {
  Reader in(bytes);
  in.magic("GMAC", 4);
  require(in.get(1) == 1, "unsupported archive version");
  require(in.get(1) == Frame::raw_byte_identity_v1, "frontend mismatch");
  Frame result;
  result.arm = static_cast<std::uint8_t>(in.get(1));
  require(result.arm <= 2 && in.get(1) == 0, "invalid archive flags");
  result.model_tag = static_cast<std::uint32_t>(in.get(4));
  require(result.model_tag == expected_model_tag, "model identity mismatch");
  result.raw_bytes = in.get(8);
  const std::uint64_t payload_bytes = in.get(8);
  require(result.raw_bytes <= maximum_raw_bytes, "decoded-size budget exceeded");
  require(payload_bytes <= maximum_payload_bytes, "payload budget exceeded");
  result.raw_crc32 = static_cast<std::uint32_t>(in.get(4));
  const auto payload_crc = static_cast<std::uint32_t>(in.get(4));
  require(payload_bytes == in.remaining(), "payload length mismatch");
  result.payload = in.take(static_cast<std::size_t>(payload_bytes));
  require(crc32(result.payload) == payload_crc, "payload checksum mismatch");
  in.end();
  return result;
}

inline void verify_inverse(const Frame& frame, const Bytes& raw) {
  require(raw.size() == frame.raw_bytes, "inverse length mismatch");
  require(crc32(raw) == frame.raw_crc32, "inverse checksum mismatch");
}

// Backend contract: install one pre-truth distribution, consume exactly eight
// decoded bits, then notify the backend of the returned byte. Midpoint learning
// belongs in that backend notification, never in a pre-truth prediction call.
class BytePrefix {
 public:
  using Counts = std::array<std::uint32_t, 256>;

  void begin_byte(const Counts& counts) {
    require(!active_ && !pending_, "previous byte is incomplete");
    validate_counts(counts);
    counts_ = counts;
    prefix_ = 0; depth_ = 0; active_ = true;
  }
  std::uint16_t predict() {
    require(active_, "install a pre-truth byte distribution first");
    require(!pending_, "observe the pending bit before predicting again");
    probability_ = conditional(); pending_ = true;
    return probability_;
  }
  std::optional<std::uint8_t> observe(unsigned bit) {
    require(active_ && pending_, "prediction must precede observation");
    require(bit <= 1, "decoded bit must be zero or one");
    require(position_ != std::numeric_limits<std::uint64_t>::max(),
            "predictor position overflow");
    prefix_ = static_cast<std::uint8_t>((prefix_ << 1) | bit);
    ++depth_; ++position_; pending_ = false; probability_ = 0;
    if (depth_ != 8) return std::nullopt;
    const auto byte = prefix_;
    active_ = false; prefix_ = 0; depth_ = 0; counts_.fill(0);
    return byte;
  }
  std::uint64_t position() const { return position_; }
  bool active() const { return active_; }
  Bytes serialize() const {
    Bytes out{'M', 'B', 'Y', 'T', 1};
    put(out, position_, 8); put(out, prefix_, 1); put(out, depth_, 1);
    put(out, active_, 1); put(out, pending_, 1); put(out, probability_, 2);
    for (const auto count : counts_) put(out, count, 4);
    return out;
  }
  static BytePrefix restore(const Bytes& bytes) {
    Reader in(bytes); in.magic("MBYT\1", 5);
    BytePrefix p;
    p.position_ = in.get(8);
    p.prefix_ = static_cast<std::uint8_t>(in.get(1));
    p.depth_ = static_cast<std::uint8_t>(in.get(1));
    const auto active = in.get(1), pending = in.get(1);
    require(active <= 1 && pending <= 1, "invalid predictor state flags");
    p.active_ = active != 0; p.pending_ = pending != 0;
    p.probability_ = static_cast<std::uint16_t>(in.get(2));
    for (auto& count : p.counts_) count = static_cast<std::uint32_t>(in.get(4));
    in.end();
    require(p.depth_ < 8 && p.position_ % 8 == p.depth_,
            "predictor depth and position disagree");
    require(p.prefix_ < (1U << p.depth_), "invalid decoded prefix");
    if (p.active_) {
      validate_counts(p.counts_);
      require(p.pending_ ? p.probability_ == p.conditional() : p.probability_ == 0,
              "pending probability disagrees with pre-truth distribution");
    } else {
      require(p.depth_ == 0 && p.prefix_ == 0 && !p.pending_ && p.probability_ == 0 &&
              std::all_of(p.counts_.begin(), p.counts_.end(),
                          [](auto count) { return count == 0; }),
              "inactive byte predictor retains noncanonical state");
    }
    return p;
  }

 private:
  Counts counts_{};
  std::uint64_t position_ = 0;
  std::uint8_t prefix_ = 0, depth_ = 0;
  bool active_ = false, pending_ = false;
  std::uint16_t probability_ = 0;

  static void validate_counts(const Counts& counts) {
    std::uint64_t sum = 0;
    for (auto count : counts) {
      require(count > 0 && count <= 65536, "invalid byte probability count");
      sum += count;
    }
    require(sum == 65536, "byte probabilities must sum exactly to Q16 unity");
  }
  std::uint16_t conditional() const {
    const unsigned width = 1U << (8 - depth_);
    const unsigned begin = unsigned(prefix_) * width, middle = begin + width / 2;
    std::uint64_t total = 0, one = 0;
    for (unsigned i = begin; i != begin + width; ++i) {
      total += counts_[i];
      if (i >= middle) one += counts_[i];
    }
    return static_cast<std::uint16_t>(
        std::clamp<std::uint64_t>(one * 65536 / total, 1, 65535));
  }
};

struct CoderState {
  std::uint32_t low = 0, high = 0xffffffffU;
  std::uint64_t pending = 0, emitted_bits = 0, symbols = 0;
  std::uint8_t accumulator = 0, used = 0;
  bool finished = false;

  Bytes serialize() const {
    Bytes out{'M', 'I', 'N', 'T', 1};
    put(out, low, 4); put(out, high, 4); put(out, pending, 8);
    put(out, emitted_bits, 8); put(out, symbols, 8);
    put(out, accumulator, 1); put(out, used, 1); put(out, finished, 1);
    return out;
  }

  static CoderState restore(const Bytes& bytes) {
    Reader in(bytes);
    in.magic("MINT\1", 5);
    CoderState s;
    s.low = static_cast<std::uint32_t>(in.get(4));
    s.high = static_cast<std::uint32_t>(in.get(4));
    s.pending = in.get(8); s.emitted_bits = in.get(8); s.symbols = in.get(8);
    s.accumulator = static_cast<std::uint8_t>(in.get(1));
    s.used = static_cast<std::uint8_t>(in.get(1));
    const auto finished = in.get(1);
    require(finished <= 1, "invalid finish marker");
    s.finished = finished != 0;
    in.end();
    require(s.low <= s.high, "invalid arithmetic interval");
    require(s.used < 8 && s.used == s.emitted_bits % 8,
            "invalid bit accumulator position");
    require(s.accumulator < (1U << s.used), "invalid bit accumulator");
    require(s.low < 0x80000000U && s.high >= 0x80000000U &&
            !(s.low >= 0x40000000U && s.high < 0xc0000000U),
            "checkpoint is not at a normalized boundary");
    return s;
  }
};

class ArithmeticBase {
 public:
  const CoderState& state() const { return state_; }
  Bytes comparison_state() const { return state_.serialize(); }

 protected:
  static constexpr std::uint32_t half = 0x80000000U;
  static constexpr std::uint32_t quarter = 0x40000000U;
  static constexpr std::uint32_t three_quarters = 0xc0000000U;
  CoderState state_;

  std::uint32_t split(std::uint16_t probability_one) const {
    require(probability_one != 0, "Q16 probability must be in 1..65535");
    const std::uint64_t range = std::uint64_t(state_.high) - state_.low + 1;
    const auto result = state_.low + range * (65536U - probability_one) / 65536U - 1;
    require(result >= state_.low && result < state_.high,
            "arithmetic interval cannot represent probability");
    return static_cast<std::uint32_t>(result);
  }

  template<class ByteSink>
  void emit(unsigned bit, ByteSink&& sink) {
    require(state_.emitted_bits != std::numeric_limits<std::uint64_t>::max(),
            "output bit count overflow");
    state_.accumulator = static_cast<std::uint8_t>((state_.accumulator << 1) | bit);
    ++state_.used; ++state_.emitted_bits;
    if (state_.used == 8) {
      sink(state_.accumulator);
      state_.used = 0; state_.accumulator = 0;
    }
  }

  template<class ByteSink>
  void resolve(unsigned bit, ByteSink&& sink) {
    emit(bit, sink);
    while (state_.pending) {
      emit(1U - bit, sink);
      --state_.pending;
    }
  }

  // Decoder code/input cursor are role-specific. The independently maintained
  // common state includes interval, E3 debt, normalized output and bit count.
  template<class ByteSink, class BitSource>
  void consume(unsigned bit, std::uint16_t probability_one, ByteSink&& sink,
               std::uint32_t* decoder_code, BitSource&& source) {
    require(!state_.finished, "coder already finalized");
    require(bit <= 1, "decoded bit must be zero or one");
    require(state_.symbols != std::numeric_limits<std::uint64_t>::max(),
            "coded-symbol count overflow");
    const auto middle = split(probability_one);
    if (bit) state_.low = middle + 1; else state_.high = middle;
    ++state_.symbols;
    for (;;) {
      std::uint32_t subtract = 0;
      if (state_.high < half) {
        resolve(0, sink);
      } else if (state_.low >= half) {
        resolve(1, sink);
        subtract = half;
      } else if (state_.low >= quarter && state_.high < three_quarters) {
        require(state_.pending != std::numeric_limits<std::uint64_t>::max(),
                "arithmetic underflow debt overflow");
        ++state_.pending;
        subtract = quarter;
      } else break;
      state_.low = (state_.low - subtract) << 1;
      state_.high = ((state_.high - subtract) << 1) | 1U;
      if (decoder_code) *decoder_code = ((*decoder_code - subtract) << 1) | source();
    }
    if (decoder_code)
      require(*decoder_code >= state_.low && *decoder_code <= state_.high,
              "decoder code outside normalized interval");
  }

  template<class ByteSink>
  void finalize(ByteSink&& sink) {
    require(!state_.finished, "coder finalized twice");
    require(state_.pending != std::numeric_limits<std::uint64_t>::max(),
            "arithmetic underflow debt overflow");
    ++state_.pending;
    resolve(state_.low < quarter ? 0 : 1, sink);
    while (state_.used) emit(0, sink);
    // Explicit finite lookahead, checked by the decoder, not fabricated input.
    for (unsigned bit = 0; bit != 32; ++bit) emit(0, sink);
    state_.finished = true;
  }
};

class Encoder : public ArithmeticBase {
 public:
  void encode(unsigned bit, std::uint16_t probability_one) {
    consume(bit, probability_one,
            [this](std::uint8_t b) { payload_.push_back(b); }, nullptr,
            []() -> unsigned { throw std::logic_error("encoder read input"); });
  }
  Bytes finish() {
    finalize([this](std::uint8_t b) { payload_.push_back(b); });
    return payload_;
  }
  Bytes serialize() const {
    Bytes out{'M', 'E', 'N', 'C', 1};
    const auto state = state_.serialize();
    put(out, state.size(), 8); out.insert(out.end(), state.begin(), state.end());
    put(out, payload_.size(), 8); out.insert(out.end(), payload_.begin(), payload_.end());
    return out;
  }
  static Encoder restore(const Bytes& bytes) {
    Reader in(bytes); in.magic("MENC\1", 5);
    const auto state_bytes = in.get(8);
    require(state_bytes <= in.remaining(), "invalid coder checkpoint length");
    Encoder result;
    result.state_ = CoderState::restore(in.take(static_cast<std::size_t>(state_bytes)));
    const auto payload_bytes = in.get(8);
    require(payload_bytes <= in.remaining(), "invalid checkpoint payload length");
    result.payload_ = in.take(static_cast<std::size_t>(payload_bytes));
    in.end();
    require(result.payload_.size() == result.state_.emitted_bits / 8,
            "checkpoint payload and writer disagree");
    return result;
  }

 private:
  Bytes payload_;
};

class Decoder : public ArithmeticBase {
 public:
  explicit Decoder(Bytes payload) : payload_(std::move(payload)) {
    require(payload_.size() >= 5, "truncated arithmetic payload");
    for (unsigned bit = 0; bit != 32; ++bit) code_ = (code_ << 1) | take();
  }
  unsigned decode(std::uint16_t probability_one) {
    const unsigned bit = code_ > split(probability_one);
    consume(bit, probability_one, [this](std::uint8_t b) { check_output(b); },
            &code_, [this]() { return take(); });
    return bit;
  }
  void finish() {
    finalize([this](std::uint8_t b) { check_output(b); });
    require(checked_bytes_ == payload_.size(), "noncanonical trailing payload");
  }
  Bytes serialize() const {
    Bytes out{'M', 'D', 'E', 'C', 1};
    const auto state = state_.serialize();
    put(out, state.size(), 8); out.insert(out.end(), state.begin(), state.end());
    put(out, code_, 4); put(out, cursor_, 8); put(out, checked_bytes_, 8);
    put(out, payload_.size(), 8); out.insert(out.end(), payload_.begin(), payload_.end());
    return out;
  }
  static Decoder restore(const Bytes& bytes) {
    Reader in(bytes); in.magic("MDEC\1", 5);
    const auto state_bytes = in.get(8);
    require(state_bytes <= in.remaining(), "invalid decoder checkpoint length");
    const auto state = CoderState::restore(in.take(static_cast<std::size_t>(state_bytes)));
    const auto code = static_cast<std::uint32_t>(in.get(4));
    const auto cursor = in.get(8), checked = in.get(8), length = in.get(8);
    require(length <= in.remaining(), "invalid decoder payload length");
    Decoder result(in.take(static_cast<std::size_t>(length)));
    in.end();
    require(result.payload_.size() <= std::numeric_limits<std::uint64_t>::max() / 8,
            "decoder payload bit length overflow");
    require(cursor >= 32 && cursor <= result.payload_.size() * 8ULL,
            "invalid decoder input cursor");
    require(checked == state.emitted_bits / 8 && checked <= result.payload_.size(),
            "invalid decoder normalized output cursor");
    require(code >= state.low && code <= state.high,
            "checkpoint code outside interval");
    result.state_ = state; result.code_ = code;
    result.cursor_ = cursor; result.checked_bytes_ = static_cast<std::size_t>(checked);
    return result;
  }

 private:
  Bytes payload_;
  std::uint32_t code_ = 0;
  std::uint64_t cursor_ = 0;
  std::size_t checked_bytes_ = 0;

  unsigned take() {
    require(cursor_ / 8 < payload_.size(), "arithmetic lookahead exhausted");
    const unsigned bit = (payload_[static_cast<std::size_t>(cursor_ / 8)] >>
                          (7 - cursor_ % 8)) & 1U;
    ++cursor_;
    return bit;
  }
  void check_output(std::uint8_t expected) {
    require(checked_bytes_ < payload_.size() && payload_[checked_bytes_] == expected,
            "noncanonical arithmetic payload");
    ++checked_bytes_;
  }
};

struct Difference {
  bool equal = true;
  std::string component;
  std::size_t offset = 0;
  int expected = -1, actual = -1;
};

inline Difference first_difference(const std::string& component,
                                   const Bytes& expected, const Bytes& actual) {
  const auto common = std::min(expected.size(), actual.size());
  std::size_t offset = 0;
  while (offset < common && expected[offset] == actual[offset]) ++offset;
  if (offset == common && expected.size() == actual.size()) return {};
  return {false, component, offset,
          offset < expected.size() ? expected[offset] : -1,
          offset < actual.size() ? actual[offset] : -1};
}

}  // namespace gamma_enwiki9::midas_codec
