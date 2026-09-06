#include "../lib/midas_observer_sha256_x86_v1.hpp"
#include <iostream>
#include <vector>

int main() {
  using namespace gamma_enwiki9::observer_sha_v1;
  if (!accelerated_available()) {
    std::cerr << "accelerated branch is unavailable; parity cannot be certified here\n";
    return 1;
  }
  std::vector<std::size_t> sizes;
  for (std::size_t n = 0; n <= 130; ++n) sizes.push_back(n);
  for (auto n : {511, 512, 513, 1000, 4096, 32768, 1048576}) sizes.push_back(n);
  for (auto n : sizes) {
    std::vector<std::uint8_t> backing(n + 1);
    for (std::size_t i = 0; i < backing.size(); ++i) backing[i] = std::uint8_t(i * 17 + (i >> 7) + 3);
    const std::span<const std::uint8_t> data(backing.data() + 1, n);
    const auto accelerated = hex(data), scalar = hex(data, true);
    if (accelerated != scalar) return 2;
    std::cout << n << ' ' << accelerated << '\n';
  }
  // A real allocated over-bound input avoids constructing an invalid span.
  std::vector<std::uint8_t> over(32 * 1024 * 1024 + 1);
  try { (void)hex(over); return 3; } catch (const std::length_error&) {}
}
