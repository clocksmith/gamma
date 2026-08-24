#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <limits>

#include "gamma-full-identity-observer.h"

int main(int argc, char** argv) {
  if (argc != 2 || argv[1] == nullptr || argv[1][0] != '/') return 64;
  if (::setenv("GAMMA_FULL_IDENTITY_DIR", argv[1], 1) != 0) return 65;

  alignas(64) std::array<unsigned char, 4096> baseline{};
  alignas(64) std::array<unsigned char, 4096> state{};
  for (size_t index = 0; index < baseline.size(); ++index) {
    baseline[index] = static_cast<unsigned char>((index * 131U + 17U) & 255U);
  }
  state = baseline;

  gamma_full_identity::RegisterSemanticRange(state.data(), state.size(), 64);
  gamma_full_identity::Begin(
      0U, std::numeric_limits<uint32_t>::max(), 0U);
  state[2047] ^= 0x80U;
  gamma_full_identity::SnapshotState(1U, "mutation");
  gamma_full_identity::Finish(
      0U, std::numeric_limits<uint32_t>::max(), 0U);
  return 0;
}
