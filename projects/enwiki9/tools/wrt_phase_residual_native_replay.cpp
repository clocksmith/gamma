#include "wrt_phase_residual_native.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  input.seekg(0, std::ios::end);
  const auto size = input.tellg();
  input.seekg(0, std::ios::beg);
  std::vector<unsigned char> data(static_cast<std::size_t>(size));
  if (!data.empty()) input.read(reinterpret_cast<char*>(data.data()), size);
  if (!input) throw std::runtime_error("cannot read " + path);
  return data;
}

std::uint64_t ReadU64(const unsigned char* input) {
  std::uint64_t value = 0;
  for (unsigned int shift = 0; shift < 64; shift += 8) value |= std::uint64_t{*input++} << shift;
  return value;
}

class RangeCounter {
 public:
  void Encode(int bit, std::uint16_t p1) {
    const std::uint32_t delta = high_ - low_;
    const std::uint32_t midpoint = low_ + (delta >> 16) * p1 +
        static_cast<std::uint32_t>((static_cast<std::uint64_t>(delta & 0xffffu) * p1) >> 16);
    if (bit) high_ = midpoint;
    else low_ = midpoint + 1;
    while (((low_ ^ high_) & 0xff000000u) == 0) {
      ++bytes_;
      low_ <<= 8;
      high_ = (high_ << 8) + 255;
    }
  }
  void Finish() {
    while (((low_ ^ high_) & 0xff000000u) == 0) {
      ++bytes_;
      low_ <<= 8;
      high_ = (high_ << 8) + 255;
    }
    ++bytes_;
  }
  std::uint64_t bytes() const { return bytes_; }

 private:
  std::uint32_t low_ = 0;
  std::uint32_t high_ = 0xffffffffu;
  std::uint64_t bytes_ = 0;
};

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 3) throw std::runtime_error("usage: replay P1 WRT_STORE");
    const auto p1 = ReadFile(argv[1]);
    const auto store = ReadFile(argv[2]);
    const std::array<unsigned char, 8> magic = {'C', 'M', 'X', '2', '1', 'P', '1', 0};
    if (p1.size() < 16 || !std::equal(magic.begin(), magic.end(), p1.begin())) {
      throw std::runtime_error("invalid P1 stream");
    }
    const std::uint64_t rows = ReadU64(p1.data() + 8);
    if (p1.size() != 16 + rows * 2 || (rows & 7) != 0 || store.size() != 5 + rows / 8) {
      throw std::runtime_error("P1/store dimensions differ");
    }
    WrtPhaseResidual model;
    RangeCounter baseline;
    RangeCounter candidate;
    for (std::uint64_t row = 0; row < rows; ++row) {
      const unsigned char* record = p1.data() + 16 + row * 2;
      const std::uint16_t base = record[0] | (std::uint16_t{record[1]} << 8);
      const int bit = (store[5 + row / 8] >> (7 - (row & 7))) & 1;
      const std::uint16_t prediction = model.Predict(base);
      baseline.Encode(bit, base);
      candidate.Encode(bit, prediction);
      model.Perceive(bit);
    }
    baseline.Finish();
    candidate.Finish();
    std::cout << "rows=" << rows << " baseline_payload_bytes=" << baseline.bytes()
              << " candidate_payload_bytes=" << candidate.bytes()
              << " exact_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(candidate.bytes())
              << " state_bytes=" << model.StateBytes() << '\n';
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
