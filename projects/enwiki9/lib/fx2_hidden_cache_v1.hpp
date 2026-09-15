#ifndef GAMMA_FX2_HIDDEN_CACHE_V1_HPP
#define GAMMA_FX2_HIDDEN_CACHE_V1_HPP

#include <array>
#include <cstddef>
#include <cstdint>

namespace gamma_hidden_cache_v1 {
constexpr unsigned CAPACITY = 4096, NEIGHBORS = 32, RADIUS = 8;
constexpr uint64_t Q = 65536, MASS = uint64_t(1) << 32;
constexpr std::size_t STATE_BYTES = 38102;

inline unsigned distance(uint64_t a, uint64_t b) {
  const uint64_t x = a ^ b;
  return unsigned(__builtin_popcountll((x | (x >> 1)) & 0x5555555555555555ULL));
}

inline bool valid_signature(uint64_t s) {
  return (s & (s >> 1) & 0x5555555555555555ULL) == 0;
}

struct Cache {
  explicit Cache(char mode) : arm(mode) {
    for (auto& row : weights) row = {{MASS / 2, MASS / 2}};
  }
  const char arm;
  uint64_t clock = 0;
  unsigned head = 0, used = 0;
  uint8_t previous = 0, prefix = 0;
  bool has_previous = false, pending = false;
  uint64_t current_signature = 0;
  bool current_valid = false, pending_active = false;
  uint16_t pending_parent = 0, pending_expert = 0;
  std::array<std::array<uint64_t, 2>, 8> weights{};
  std::array<uint64_t, CAPACITY> signatures{};
  std::array<uint8_t, CAPACITY> labels{};
  std::array<uint32_t, 257> cdf{};
  // Hypothetical D counters are also collected by K, preserving K/D identity.
  std::array<uint64_t, 6> stats{};

  void query() {
    cdf.fill(0);
    if (!current_valid || !current_signature) return;
    ++stats[0];
    std::array<std::array<uint16_t, NEIGHBORS>, RADIUS + 1> buckets{};
    std::array<unsigned, RADIUS + 1> sizes{};
    // Newest first supplies the specified tie-break within each distance.
    for (unsigned age = 0; age < used; ++age) {
      const unsigned slot = (head + CAPACITY - 1 - age) % CAPACITY;
      const unsigned d = distance(current_signature, signatures[slot]);
      if (d <= RADIUS && sizes[d] < NEIGHBORS) buckets[d][sizes[d]++] = uint16_t(slot);
      if (sizes[0] == NEIGHBORS) break;
    }
    unsigned selected = 0;
    for (unsigned d = 0; d <= RADIUS && selected < NEIGHBORS; ++d) {
      for (unsigned i = 0; i < sizes[d] && selected < NEIGHBORS; ++i, ++selected) {
        cdf[unsigned(labels[buckets[d][i]]) + 1] += RADIUS + 1 - d;
      }
    }
    stats[1] += selected != 0;
    stats[2] += selected;
    for (unsigned i = 1; i <= 256; ++i) cdf[i] += cdf[i - 1];
  }

  int predict(unsigned parent, uint64_t signature, bool valid) {
    if (pending || parent == 0 || parent >= Q || !valid_signature(signature)
        || (!valid && signature) || (arm != 'K' && arm != 'D' && arm != 'S')) return -1;
    const unsigned row = unsigned(clock & 7);
    if (!row) {
      current_signature = signature;
      current_valid = valid;
      query();
    } else if (signature != current_signature || valid != current_valid) return -1;
    const unsigned start = unsigned(prefix) << (8 - row);
    const unsigned mid = start + (1u << (7 - row));
    const unsigned end = start + (1u << (8 - row));
    const unsigned total = cdf[end] - cdf[start];
    unsigned expert = parent;
    if (total) {
      const uint64_t ones = cdf[end] - cdf[mid];
      const unsigned cache = unsigned((Q * ones + total / 2) / total);
      expert = (3 * parent + cache + 2) / 4;
    }
    const auto& w = weights[row];
    const unsigned corrected = unsigned((w[0] * parent + w[1] * expert + MASS / 2) / MASS);
    if (!corrected || corrected >= Q) return -1;
    pending_parent = uint16_t(parent);
    pending_expert = uint16_t(expert);
    pending_active = total != 0 && expert != parent;
    pending = true;
    stats[3] += pending_active;
    stats[4] += corrected != parent;
    return arm == 'K' ? int(parent) : int(corrected);
  }

  bool observe(unsigned bit) {
    if (!pending || bit > 1) return false;
    const unsigned row = unsigned(clock & 7);
    if (pending_active) {
      auto& w = weights[row];
      const uint64_t m0 = w[0] * (bit ? pending_parent : Q - pending_parent);
      const uint64_t m1 = w[1] * (bit ? pending_expert : Q - pending_expert);
      const uint64_t den = m0 + m1;
      const unsigned __int128 z0 = static_cast<unsigned __int128>(MASS - 2) * m0;
      const unsigned __int128 z1 = static_cast<unsigned __int128>(MASS - 2) * m1;
      w[0] = 1 + uint64_t(z0 / den);
      w[1] = 1 + uint64_t(z1 / den);
      if (w[0] + w[1] < MASS) ++w[z1 % den > z0 % den ? 1 : 0];
      if (w[0] + w[1] != MASS || !w[0] || !w[1]) return false;
    }
    prefix = uint8_t((unsigned(prefix) << 1) | bit);
    ++clock;
    if (!(clock & 7)) {
      if (current_valid && current_signature) {
        signatures[head] = current_signature;
        labels[head] = arm == 'S' && has_previous ? previous : prefix;
        head = (head + 1) % CAPACITY;
        if (used < CAPACITY) ++used;
        ++stats[5];
      }
      previous = prefix;
      has_previous = true;
      prefix = 0;
    }
    pending = false;
    return true;
  }

  std::size_t state(uint8_t* out, std::size_t capacity) const {
    if (!out || capacity < STATE_BYTES) return 0;
    std::size_t n = 0;
    auto put = [&](uint64_t x, unsigned bytes) {
      for (unsigned j = 0; j < bytes; ++j) out[n++] = uint8_t(x >> (8 * j));
    };
    put(clock, 8); put(head, 4); put(used, 4);
    put(previous, 1); put(has_previous, 1); put(prefix, 1); put(pending, 1);
    put(current_signature, 8); put(current_valid, 1);
    put(pending_parent, 2); put(pending_expert, 2); put(pending_active, 1);
    for (const auto& row : weights) for (auto v : row) put(v, 8);
    for (auto v : signatures) put(v, 8);
    for (auto v : labels) put(v, 1);
    for (auto v : cdf) put(v, 4);
    for (auto v : stats) put(v, 8);
    return n == STATE_BYTES ? n : 0;
  }
};
}  // namespace gamma_hidden_cache_v1
#endif
