#include <array>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <limits>

namespace {
constexpr std::size_t A = 10;
constexpr std::array<std::uint32_t, A + 1> fact = {
    1u, 1u, 2u, 6u, 24u, 120u, 720u, 5040u, 40320u, 362880u,
    3628800u};
using Perm = std::array<std::uint8_t, A>;

std::uint32_t rank_perm(const Perm& p) {
  Perm available{};
  for (std::size_t i = 0; i < A; ++i) available[i] = static_cast<std::uint8_t>(i);
  std::size_t n = A;
  std::uint32_t rank = 0;
  for (std::size_t i = 0; i < A; ++i) {
    std::size_t d = 0;
    while (d < n && available[d] != p[i]) ++d;
    if (d == n) return std::numeric_limits<std::uint32_t>::max();
    rank += static_cast<std::uint32_t>(d) * fact[A - 1 - i];
    for (std::size_t j = d + 1; j < n; ++j) available[j - 1] = available[j];
    --n;
  }
  return rank;
}

Perm unrank_perm(std::uint32_t rank) {
  Perm available{};
  Perm p{};
  for (std::size_t i = 0; i < A; ++i) available[i] = static_cast<std::uint8_t>(i);
  std::size_t n = A;
  for (std::size_t i = 0; i < A; ++i) {
    const auto f = fact[A - 1 - i];
    const std::size_t d = rank / f;
    rank %= f;
    p[i] = available[d];
    for (std::size_t j = d + 1; j < n; ++j) available[j - 1] = available[j];
    --n;
  }
  return p;
}

Perm move_front(Perm p, std::uint8_t way) {
  std::size_t pos = 0;
  while (p[pos] != way) ++pos;
  for (std::size_t i = pos; i > 0; --i) p[i] = p[i - 1];
  p[0] = way;
  return p;
}

std::uint8_t lru_in_mask(const Perm& p, std::uint16_t mask) {
  for (std::size_t i = A; i-- > 0;) {
    if ((mask >> p[i]) & 1u) return p[i];
  }
  return 255;
}

struct Logical10Rank {
  std::uint16_t chk[A];
  std::uint8_t last;
  std::uint8_t bh[A][7];
  std::uint32_t recency_rank;
};

static_assert(offsetof(Logical10Rank, chk) == 0, "checksum offset");
static_assert(offsetof(Logical10Rank, last) == 20, "last offset");
static_assert(offsetof(Logical10Rank, bh) == 21, "state offset");
static_assert(offsetof(Logical10Rank, recency_rank) == 92, "rank offset");
static_assert(sizeof(Logical10Rank) == 96, "record size");
static_assert(alignof(Logical10Rank) == 4, "record alignment");
}  // namespace

int main() {
  std::uint64_t digest = 1469598103934665603ull;
  for (std::uint32_t r = 0; r < fact[A]; ++r) {
    const Perm p = unrank_perm(r);
    if (rank_perm(p) != r) return 1;

    const auto way = static_cast<std::uint8_t>((r * 2654435761u) % A);
    const Perm moved = move_front(p, way);
    const auto moved_rank = rank_perm(moved);
    if (moved_rank >= fact[A] || unrank_perm(moved_rank) != moved) return 2;

    const std::uint16_t mask = static_cast<std::uint16_t>(((r * 40503u) & 1023u) | 1u);
    const auto chosen = lru_in_mask(p, mask);
    if (chosen >= A || ((mask >> chosen) & 1u) == 0) return 3;
    bool found = false;
    for (std::size_t i = A; i-- > 0;) {
      if ((mask >> p[i]) & 1u) {
        if (p[i] != chosen) return 4;
        found = true;
        break;
      }
    }
    if (!found) return 5;

    digest ^= static_cast<std::uint64_t>(moved_rank) |
              (static_cast<std::uint64_t>(chosen) << 32);
    digest *= 1099511628211ull;
  }

  std::cout
      << "{\n"
      << "  \"schema\": \"fxcm_factoradic_recency_theorem_verifier_v1\",\n"
      << "  \"associativity\": 10,\n"
      << "  \"permutations_checked\": 3628800,\n"
      << "  \"transitions_checked\": 3628800,\n"
      << "  \"lru_masks_checked\": 3628800,\n"
      << "  \"minimum_rank_bits\": 22,\n"
      << "  \"rank_offset_bytes\": 92,\n"
      << "  \"record_size_bytes\": 96,\n"
      << "  \"record_alignment_bytes\": 4,\n"
      << "  \"digest\": " << digest << ",\n"
      << "  \"verdict\": \"pass\",\n"
      << "  \"score_credit_bytes\": 0\n"
      << "}\n";
}
