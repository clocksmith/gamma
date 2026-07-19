#ifndef WRT_PHASE_RESIDUAL_NATIVE_H
#define WRT_PHASE_RESIDUAL_NATIVE_H

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

class WrtPhaseResidual {
 public:
  WrtPhaseResidual();
  std::uint16_t Predict(std::uint16_t base);
  void Perceive(int bit);
  std::uint64_t StateBytes() const;

 private:
  static constexpr std::uint32_t kTotal = 65536;
  static constexpr std::uint32_t kPrior = 256;
  static constexpr std::uint32_t kStrengthPpm = 250000;
  static constexpr std::array<std::size_t, 4> kLevelSizes = {
      4096, 16384, 65536, 1048576};

  static unsigned char WrtTransform(unsigned char value);
  static std::uint32_t Bucket(std::uint16_t base);
  void ObserveByte(unsigned char value);

  std::array<std::vector<std::uint32_t>, 4> counts_;
  std::array<std::vector<std::int64_t>, 4> sums_;
  std::array<std::size_t, 4> indices_{};
  std::array<unsigned char, 3> event_buffer_{};
  std::uint64_t row_ = 0;
  std::uint16_t base_ = 32768;
  unsigned char current_byte_ = 0;
  unsigned int event_size_ = 0;
  unsigned int expected_event_size_ = 0;
};

#endif
