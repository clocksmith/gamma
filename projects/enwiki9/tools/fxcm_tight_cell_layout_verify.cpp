#include <cstddef>
#include <cstdint>
#include <iostream>

template <int A, int B>
union Cell {
  struct {
    std::uint16_t chk[A];
    std::uint8_t last;
    std::uint8_t bh[A][7];
  };
  std::uint8_t pad[B];
};

using Cell96 = Cell<10, 96>;
using Cell92 = Cell<10, 92>;
using Cell128 = Cell<14, 128>;

static_assert(sizeof(std::uint8_t) == 1, "U8 size");
static_assert(alignof(std::uint8_t) == 1, "U8 alignment");
static_assert(sizeof(std::uint16_t) == 2, "U16 size");
static_assert(alignof(std::uint16_t) == 2, "U16 alignment");
static_assert(offsetof(Cell96, chk) == 0, "A10 chk offset");
static_assert(offsetof(Cell96, last) == 20, "A10 last offset");
static_assert(offsetof(Cell96, bh) == 21, "A10 bh offset");
static_assert(offsetof(Cell92, chk) == 0, "tight A10 chk offset");
static_assert(offsetof(Cell92, last) == 20, "tight A10 last offset");
static_assert(offsetof(Cell92, bh) == 21, "tight A10 bh offset");
static_assert(sizeof(Cell96) == 96, "padded A10 width");
static_assert(sizeof(Cell92) == 92, "tight A10 width");
static_assert(sizeof(Cell128) == 128, "A14 width");

template <typename T>
std::uint64_t FillAndHash(T* cells, std::size_t count) {
  std::uint64_t hash = 1469598103934665603ULL;
  for (std::size_t n = 0; n < count; ++n) {
    cells[n].last = static_cast<std::uint8_t>(n * 17U);
    for (int i = 0; i < 10; ++i) {
      cells[n].chk[i] = static_cast<std::uint16_t>(n * 257U + i * 13U);
      for (int j = 0; j < 7; ++j) {
        cells[n].bh[i][j] =
            static_cast<std::uint8_t>(n + i * 11U + j * 29U);
      }
    }
  }
  for (std::size_t n = 0; n < count; ++n) {
    hash = (hash ^ cells[n].last) * 1099511628211ULL;
    for (int i = 0; i < 10; ++i) {
      hash = (hash ^ cells[n].chk[i]) * 1099511628211ULL;
      for (int j = 0; j < 7; ++j) {
        hash = (hash ^ cells[n].bh[i][j]) * 1099511628211ULL;
      }
    }
  }
  return hash;
}

int main() {
  constexpr std::size_t kCount = 257;
  alignas(128) Cell96 wide[kCount] = {};
  alignas(128) Cell92 tight[kCount] = {};

  bool checksum_alignment_ok = true;
  for (std::size_t n = 0; n < kCount; ++n) {
    for (int i = 0; i < 10; ++i) {
      const auto address =
          reinterpret_cast<std::uintptr_t>(&tight[n].chk[i]);
      checksum_alignment_ok = checksum_alignment_ok && address % 2 == 0;
    }
  }

  const std::uint64_t wide_hash = FillAndHash(wide, kCount);
  const std::uint64_t tight_hash = FillAndHash(tight, kCount);
  const bool logical_identity_ok = wide_hash == tight_hash;

  std::cout
      << "{\n"
      << "  \"schema\": \"fxcm_tight_cell_layout_verifier_v1\",\n"
      << "  \"cell_count\": " << kCount << ",\n"
      << "  \"cell96_bytes\": " << sizeof(Cell96) << ",\n"
      << "  \"cell92_bytes\": " << sizeof(Cell92) << ",\n"
      << "  \"cell128_bytes\": " << sizeof(Cell128) << ",\n"
      << "  \"chk_offset\": " << offsetof(Cell92, chk) << ",\n"
      << "  \"last_offset\": " << offsetof(Cell92, last) << ",\n"
      << "  \"bh_offset\": " << offsetof(Cell92, bh) << ",\n"
      << "  \"checksum_alignment_ok\": "
      << (checksum_alignment_ok ? "true" : "false") << ",\n"
      << "  \"logical_identity_ok\": "
      << (logical_identity_ok ? "true" : "false") << ",\n"
      << "  \"logical_hash\": " << tight_hash << "\n"
      << "}\n";
  return checksum_alignment_ok && logical_identity_ok ? 0 : 1;
}

