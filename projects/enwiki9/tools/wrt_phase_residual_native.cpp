#include "wrt_phase_residual_native.h"

#include <algorithm>
#include <limits>

WrtPhaseResidual::WrtPhaseResidual() {
  for (std::size_t level = 0; level < kLevelSizes.size(); ++level) {
    counts_[level].assign(kLevelSizes[level], 0);
    sums_[level].assign(kLevelSizes[level], 0);
  }
}

unsigned char WrtPhaseResidual::WrtTransform(unsigned char value) {
  if (value >= static_cast<unsigned char>('{') && value < 127) {
    value += static_cast<unsigned char>('P' - '{');
  } else if (value >= static_cast<unsigned char>('P') && value < static_cast<unsigned char>('T')) {
    value -= static_cast<unsigned char>('P' - '{');
  } else if ((value >= ':' && value <= '?') || (value >= 'J' && value <= 'O')) {
    value ^= 0x70;
  }
  if (value == 'X' || value == '`') value ^= static_cast<unsigned char>('X' ^ '`');
  return value;
}

std::uint32_t WrtPhaseResidual::Bucket(std::uint16_t base) {
  const bool upper = base >= 32768;
  const std::uint32_t distance = upper ? kTotal - base : base;
  unsigned int exponent = 0;
  for (std::uint32_t value = distance; value > 1; value >>= 1) ++exponent;
  const std::uint32_t normalized = distance << (15 - exponent);
  const std::uint32_t mantissa = (normalized >> 13) & 3u;
  return (upper ? 64u : 0u) + exponent * 4 + mantissa;
}

std::uint16_t WrtPhaseResidual::Predict(std::uint16_t base) {
  const std::uint32_t bucket = Bucket(base);
  const std::uint32_t bit_position = row_ & 7;
  const std::uint32_t position = event_size_ * 8 + bit_position;
  indices_[0] = position * 128 + bucket;
  indices_[1] = (position * 4 + (current_byte_ & 3u)) * 128 + bucket;
  indices_[2] = (position * 16 + (current_byte_ & 15u)) * 128 + bucket;
  indices_[3] = (position * 256 + current_byte_) * 128 + bucket;
  std::int64_t posterior = 0;
  for (std::size_t level = 0; level < kLevelSizes.size(); ++level) {
    const std::size_t index = indices_[level];
    posterior = (sums_[level][index] + static_cast<std::int64_t>(kPrior) * posterior) /
        static_cast<std::int64_t>(counts_[level][index] + kPrior);
  }
  base_ = base;
  const std::int64_t correction = posterior * kStrengthPpm / 1000000;
  return static_cast<std::uint16_t>(std::max<std::int64_t>(
      1, std::min<std::int64_t>(kTotal - 1, static_cast<std::int64_t>(base) + correction)));
}

void WrtPhaseResidual::Perceive(int bit) {
  const std::int64_t residual = (bit ? static_cast<std::int64_t>(kTotal) : 0) - base_;
  for (std::size_t level = 0; level < kLevelSizes.size(); ++level) {
    const std::size_t index = indices_[level];
    if (counts_[level][index] != std::numeric_limits<std::uint32_t>::max()) {
      ++counts_[level][index];
    }
    sums_[level][index] += residual;
  }
  current_byte_ = static_cast<unsigned char>((current_byte_ << 1) | bit);
  ++row_;
  if ((row_ & 7) == 0) {
    if (row_ / 8 > 6) ObserveByte(current_byte_);
    current_byte_ = 0;
  }
}

void WrtPhaseResidual::ObserveByte(unsigned char value) {
  event_buffer_[event_size_++] = value;
  if (event_size_ == 1) {
    const unsigned char first = WrtTransform(event_buffer_[0]);
    expected_event_size_ = (first == 0x0c || first > 0xcf) ? 2 : 1;
  } else if (event_size_ == 2 && WrtTransform(event_buffer_[0]) > 0xcf &&
             WrtTransform(event_buffer_[1]) > 0xcf) {
    expected_event_size_ = 3;
  }
  if (expected_event_size_ && event_size_ == expected_event_size_) {
    event_size_ = 0;
    expected_event_size_ = 0;
  }
}

std::uint64_t WrtPhaseResidual::StateBytes() const {
  std::uint64_t total = 0;
  for (const std::size_t size : kLevelSizes) total += size * 12;
  return total;
}
