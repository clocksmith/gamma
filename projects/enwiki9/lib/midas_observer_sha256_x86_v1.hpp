// Observation-only SHA-256 acceleration. Predictor and codec law are unchanged.
// The block routine retains its upstream public-domain declaration and credits.
#pragma once
#include "../programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/profile_population.hpp"
#include <array>
#include <cstring>
#include <span>
#include <stdexcept>
#include <string>
#include <x86intrin.h>

namespace gamma_enwiki9::observer_sha_v1 {
namespace blocks {
#pragma GCC push_options
#pragma GCC target("sha,ssse3,sse4.1")
#include "../operations/provenance/sources/2026-09-06/sha256-x86-d03795497f3e.c"
#pragma GCC pop_options
}  // namespace blocks

inline bool accelerated_available() {
  return __builtin_cpu_supports("sha") && __builtin_cpu_supports("ssse3") &&
         __builtin_cpu_supports("sse4.1");
}

inline std::string hex(std::span<const std::uint8_t> input, bool force_scalar = false) {
  // Same maximum as the observer's bounded serialized-state files.
  if (input.size() > 32 * 1024 * 1024) throw std::length_error("observer SHA input exceeds32MiB");
  if (force_scalar || !accelerated_available()) return nncp::Sha256Hex(input);
  std::array<std::uint32_t, 8> state{
      0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
  const auto full = input.size() & ~std::size_t(63);
  if (full) blocks::sha256_process_x86(state.data(), input.data(), std::uint32_t(full));
  std::array<std::uint8_t, 128> tail{};
  const auto remaining = input.size() - full;
  if (remaining) std::memcpy(tail.data(), input.data() + full, remaining);
  tail[remaining] = 0x80;
  const std::size_t padded = remaining < 56 ? 64 : 128;
  const auto bit_length = std::uint64_t(input.size()) * 8;
  for (unsigned i = 0; i < 8; ++i) tail[padded - 1 - i] = std::uint8_t(bit_length >> (8 * i));
  blocks::sha256_process_x86(state.data(), tail.data(), std::uint32_t(padded));
  constexpr char digits[] = "0123456789abcdef";
  std::string output(64, '0');
  for (std::size_t i = 0; i < 32; ++i) {
    const auto byte = std::uint8_t(state[i / 4] >> (24 - 8 * (i % 4)));
    output[2 * i] = digits[byte >> 4]; output[2 * i + 1] = digits[byte & 15];
  }
  return output;
}
}  // namespace gamma_enwiki9::observer_sha_v1

namespace gamma_enwiki9::nncp {
inline std::string ObserverSha256Hex(std::span<const std::uint8_t> input) {
  return observer_sha_v1::hex(input);
}
}  // namespace gamma_enwiki9::nncp
