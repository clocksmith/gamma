#include <array>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <sys/mman.h>
#include <unistd.h>

namespace {

constexpr std::size_t kWays = 14;
constexpr std::size_t kBaseWays = 10;
constexpr std::size_t kOverflowWays = 4;
constexpr std::size_t kHistoryBytes = 7;
constexpr std::size_t kBuckets = 257;
constexpr std::size_t kRandomOperationsPerEpoch = 250000;

struct ParentCell {
  std::uint16_t chk[kWays];
  std::uint8_t last;
  std::uint8_t bh[kWays][kHistoryBytes];
  std::uint8_t pad;
};

struct SparseBase {
  std::uint16_t chk[kBaseWays];
  std::uint32_t overflow_index_plus_one;
  std::uint8_t last;
  std::uint8_t reserved;
  std::uint8_t bh[kBaseWays][kHistoryBytes];
};

struct SparseOverflow {
  std::uint16_t chk[kOverflowWays];
  std::uint8_t bh[kOverflowWays][kHistoryBytes];
};

static_assert(sizeof(ParentCell) == 128, "parent width");
static_assert(offsetof(ParentCell, chk) == 0, "parent checksum offset");
static_assert(offsetof(ParentCell, last) == 28, "parent recent offset");
static_assert(offsetof(ParentCell, bh) == 29, "parent history offset");
static_assert(sizeof(SparseBase) == 96, "base width");
static_assert(alignof(SparseBase) == 4, "base alignment");
static_assert(offsetof(SparseBase, chk) == 0, "base checksum offset");
static_assert(offsetof(SparseBase, overflow_index_plus_one) == 20,
              "base handle offset");
static_assert(offsetof(SparseBase, last) == 24, "base recent offset");
static_assert(offsetof(SparseBase, bh) == 26, "base history offset");
static_assert(sizeof(SparseOverflow) == 36, "overflow width");
static_assert(offsetof(SparseOverflow, chk) == 0,
              "overflow checksum offset");
static_assert(offsetof(SparseOverflow, bh) == 8,
              "overflow history offset");

enum class AccessKind : std::uint8_t { kRecent = 0, kScan = 1, kMiss = 2 };

struct Access {
  std::size_t slot;
  std::uint8_t* history;
  AccessKind kind;
};

struct ParentTable {
  std::array<ParentCell, kBuckets> cells{};

  Access Get(std::size_t bucket, std::uint16_t checksum, int keep) {
    ParentCell& cell = cells.at(bucket);
    const int recent0 = cell.last & 15;
    const int recent1 = cell.last >> 4;
    if (recent0 < static_cast<int>(kWays) &&
        cell.chk[recent0] == checksum) {
      return {static_cast<std::size_t>(recent0), cell.bh[recent0],
              AccessKind::kRecent};
    }
    for (std::size_t slot = 0; slot < kWays; ++slot) {
      if (cell.chk[slot] == checksum) {
        cell.last = static_cast<std::uint8_t>((cell.last << 4) | slot);
        return {slot, cell.bh[slot], AccessKind::kScan};
      }
    }
    int priority = 0xffff;
    std::size_t victim = 0;
    for (std::size_t slot = 0; slot < kWays; ++slot) {
      if (static_cast<int>(slot) != recent0 &&
          static_cast<int>(slot) != recent1 &&
          cell.bh[slot][0] < priority) {
        priority = cell.bh[slot][0];
        victim = slot;
      }
    }
    cell.last =
        static_cast<std::uint8_t>((cell.last << 4) | victim | keep);
    cell.chk[victim] = checksum;
    std::memset(cell.bh[victim], 0, kHistoryBytes);
    return {victim, cell.bh[victim], AccessKind::kMiss};
  }

  void Reset() { std::memset(cells.data(), 0, sizeof(cells)); }
};

class SparseTable {
 public:
  SparseTable() {
    const long page = sysconf(_SC_PAGESIZE);
    if (page <= 0) throw std::runtime_error("sysconf(_SC_PAGESIZE)");
    page_bytes_ = static_cast<std::size_t>(page);
    const std::size_t needed = kBuckets * sizeof(SparseOverflow);
    mapping_bytes_ = ((needed + page_bytes_ - 1) / page_bytes_) * page_bytes_;
    void* mapping = mmap(nullptr, mapping_bytes_, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);
    if (mapping == MAP_FAILED) {
      throw std::runtime_error(std::string("mmap: ") + std::strerror(errno));
    }
    arena_ = static_cast<SparseOverflow*>(mapping);
  }

  SparseTable(const SparseTable&) = delete;
  SparseTable& operator=(const SparseTable&) = delete;

  ~SparseTable() {
    if (arena_ != nullptr) munmap(arena_, mapping_bytes_);
  }

  Access Get(std::size_t bucket, std::uint16_t checksum, int keep) {
    SparseBase& cell = cells_.at(bucket);
    const int recent0 = cell.last & 15;
    const int recent1 = cell.last >> 4;
    if (recent0 < static_cast<int>(kWays) &&
        Checksum(cell, static_cast<std::size_t>(recent0)) == checksum) {
      return {static_cast<std::size_t>(recent0),
              MutableHistory(cell, static_cast<std::size_t>(recent0)),
              AccessKind::kRecent};
    }
    for (std::size_t slot = 0; slot < kWays; ++slot) {
      if (Checksum(cell, slot) == checksum) {
        cell.last = static_cast<std::uint8_t>((cell.last << 4) | slot);
        return {slot, MutableHistory(cell, slot), AccessKind::kScan};
      }
    }
    int priority = 0xffff;
    std::size_t victim = 0;
    for (std::size_t slot = 0; slot < kWays; ++slot) {
      if (static_cast<int>(slot) != recent0 &&
          static_cast<int>(slot) != recent1 &&
          History(cell, slot)[0] < priority) {
        priority = History(cell, slot)[0];
        victim = slot;
      }
    }
    cell.last =
        static_cast<std::uint8_t>((cell.last << 4) | victim | keep);
    MutableChecksum(cell, victim) = checksum;
    std::uint8_t* const history = MutableHistory(cell, victim);
    std::memset(history, 0, kHistoryBytes);
    return {victim, history, AccessKind::kMiss};
  }

  void SetSyntheticBaseFullNoOverflow(std::size_t bucket) {
    SparseBase& cell = cells_.at(bucket);
    std::memset(&cell, 0, sizeof(cell));
    for (std::size_t slot = 0; slot < kBaseWays; ++slot) {
      cell.chk[slot] = static_cast<std::uint16_t>(slot + 1);
      cell.bh[slot][0] = static_cast<std::uint8_t>(slot + 1);
    }
    cell.last = 0;
  }

  void Reset() {
    std::memset(cells_.data(), 0, sizeof(cells_));
    if (used_ != 0) {
      const std::size_t touched = used_ * sizeof(SparseOverflow);
      const std::size_t decommit =
          ((touched + page_bytes_ - 1) / page_bytes_) * page_bytes_;
      if (madvise(arena_, decommit, MADV_DONTNEED) != 0) {
        throw std::runtime_error(std::string("madvise: ") +
                                 std::strerror(errno));
      }
    }
    used_ = 0;
  }

  std::uint16_t ChecksumAt(std::size_t bucket, std::size_t slot) const {
    return Checksum(cells_.at(bucket), slot);
  }

  const std::uint8_t* HistoryAt(std::size_t bucket,
                                std::size_t slot) const {
    return History(cells_.at(bucket), slot);
  }

  std::uint8_t LastAt(std::size_t bucket) const {
    return cells_.at(bucket).last;
  }

  std::size_t overflow_allocations() const { return used_; }
  std::size_t mapping_bytes() const { return mapping_bytes_; }
  std::size_t page_bytes() const { return page_bytes_; }
  std::size_t cross_page_records() const { return cross_page_records_; }

 private:
  SparseOverflow* Overflow(const SparseBase& cell) const {
    if (cell.overflow_index_plus_one == 0) return nullptr;
    return &arena_[cell.overflow_index_plus_one - 1];
  }

  SparseOverflow* EnsureOverflow(SparseBase& cell) {
    if (SparseOverflow* const present = Overflow(cell)) return present;
    if (used_ >= kBuckets || used_ >= std::numeric_limits<std::uint32_t>::max()) {
      throw std::runtime_error("overflow arena exhausted");
    }
    const std::size_t begin = used_ * sizeof(SparseOverflow);
    const std::size_t end = begin + sizeof(SparseOverflow) - 1;
    if (begin / page_bytes_ != end / page_bytes_) ++cross_page_records_;
    std::memset(&arena_[used_], 0, sizeof(SparseOverflow));
    ++used_;
    cell.overflow_index_plus_one = static_cast<std::uint32_t>(used_);
    return &arena_[used_ - 1];
  }

  std::uint16_t Checksum(const SparseBase& cell, std::size_t slot) const {
    if (slot < kBaseWays) return cell.chk[slot];
    const SparseOverflow* const overflow = Overflow(cell);
    return overflow == nullptr ? 0 : overflow->chk[slot - kBaseWays];
  }

  std::uint16_t& MutableChecksum(SparseBase& cell, std::size_t slot) {
    if (slot < kBaseWays) return cell.chk[slot];
    return EnsureOverflow(cell)->chk[slot - kBaseWays];
  }

  const std::uint8_t* History(const SparseBase& cell,
                              std::size_t slot) const {
    static constexpr std::uint8_t zeros[kHistoryBytes] = {};
    if (slot < kBaseWays) return cell.bh[slot];
    const SparseOverflow* const overflow = Overflow(cell);
    return overflow == nullptr ? zeros : overflow->bh[slot - kBaseWays];
  }

  std::uint8_t* MutableHistory(SparseBase& cell, std::size_t slot) {
    if (slot < kBaseWays) return cell.bh[slot];
    return EnsureOverflow(cell)->bh[slot - kBaseWays];
  }

  std::array<SparseBase, kBuckets> cells_{};
  SparseOverflow* arena_ = nullptr;
  std::size_t used_ = 0;
  std::size_t mapping_bytes_ = 0;
  std::size_t page_bytes_ = 0;
  std::size_t cross_page_records_ = 0;
};

struct Counters {
  std::uint64_t operations = 0;
  std::uint64_t recent_hits = 0;
  std::uint64_t scan_hits = 0;
  std::uint64_t misses = 0;
  std::uint64_t persistent_pointer_writes = 0;
  std::uint32_t returned_slot_mask = 0;
  std::uint32_t miss_victim_mask = 0;
};

std::uint64_t Next(std::uint64_t& state) {
  state ^= state >> 12;
  state ^= state << 25;
  state ^= state >> 27;
  return state * 2685821657736338717ULL;
}

void Mutate(std::uint8_t* bytes, std::uint64_t operation,
            std::uint16_t checksum) {
  for (std::size_t i = 0; i < kHistoryBytes; ++i) {
    bytes[i] = static_cast<std::uint8_t>(
        bytes[i] * 33U + static_cast<unsigned>(operation) + checksum +
        static_cast<unsigned>(i * 29U) + 1U);
  }
  if (bytes[0] == 0) bytes[0] = 1;
}

bool EqualBucket(const ParentTable& parent, const SparseTable& sparse,
                 std::size_t bucket) {
  const ParentCell& p = parent.cells.at(bucket);
  if (p.last != sparse.LastAt(bucket)) return false;
  for (std::size_t slot = 0; slot < kWays; ++slot) {
    if (p.chk[slot] != sparse.ChecksumAt(bucket, slot)) return false;
    if (std::memcmp(p.bh[slot], sparse.HistoryAt(bucket, slot),
                    kHistoryBytes) != 0) {
      return false;
    }
  }
  return true;
}

void Apply(ParentTable& parent, SparseTable& sparse, std::size_t bucket,
           std::uint16_t checksum, int keep, Counters& counters,
           std::array<std::uint8_t*, kBuckets>& parent_saved,
           std::array<std::uint8_t*, kBuckets>& sparse_saved) {
  const Access p = parent.Get(bucket, checksum, keep);
  const Access d = sparse.Get(bucket, checksum, keep);
  if (p.slot != d.slot || p.kind != d.kind) {
    throw std::runtime_error("access decision divergence");
  }
  ++counters.operations;
  counters.returned_slot_mask |= 1U << p.slot;
  if (p.kind == AccessKind::kRecent) ++counters.recent_hits;
  if (p.kind == AccessKind::kScan) ++counters.scan_hits;
  if (p.kind == AccessKind::kMiss) {
    ++counters.misses;
    counters.miss_victim_mask |= 1U << p.slot;
  }
  Mutate(p.history, counters.operations, checksum);
  Mutate(d.history, counters.operations, checksum);
  if (parent_saved[bucket] != nullptr && (counters.operations % 19U) == 0) {
    const std::size_t index = counters.operations % kHistoryBytes;
    parent_saved[bucket][index] ^= static_cast<std::uint8_t>(checksum | 1U);
    sparse_saved[bucket][index] ^= static_cast<std::uint8_t>(checksum | 1U);
    ++counters.persistent_pointer_writes;
  }
  parent_saved[bucket] = p.history;
  sparse_saved[bucket] = d.history;
  if (!EqualBucket(parent, sparse, bucket)) {
    throw std::runtime_error("normalized bucket divergence");
  }
}

void SeedSyntheticZeroOverflowCase(ParentTable& parent, SparseTable& sparse,
                                   std::size_t bucket) {
  ParentCell& cell = parent.cells.at(bucket);
  std::memset(&cell, 0, sizeof(cell));
  for (std::size_t slot = 0; slot < kBaseWays; ++slot) {
    cell.chk[slot] = static_cast<std::uint16_t>(slot + 1);
    cell.bh[slot][0] = static_cast<std::uint8_t>(slot + 1);
  }
  cell.last = 0;
  sparse.SetSyntheticBaseFullNoOverflow(bucket);
  if (!EqualBucket(parent, sparse, bucket)) {
    throw std::runtime_error("synthetic precondition divergence");
  }
}

void RunRandomEpoch(ParentTable& parent, SparseTable& sparse,
                    std::uint64_t& random_state, Counters& counters,
                    std::array<std::uint8_t*, kBuckets>& parent_saved,
                    std::array<std::uint8_t*, kBuckets>& sparse_saved) {
  for (std::size_t n = 0; n < kRandomOperationsPerEpoch; ++n) {
    const std::uint64_t r0 = Next(random_state);
    const std::size_t bucket = r0 % kBuckets;
    const std::size_t mode = (r0 >> 16) & 3U;
    std::uint16_t checksum;
    if (mode == 0) {
      checksum = 0;
    } else if (mode == 1) {
      checksum = parent.cells[bucket].chk[(r0 >> 24) % kWays];
    } else {
      checksum = static_cast<std::uint16_t>(Next(random_state));
    }
    const int keep = ((r0 >> 40) & 7U) == 0 ? 0xf0 : 0;
    Apply(parent, sparse, bucket, checksum, keep, counters, parent_saved,
          sparse_saved);
  }
}

std::uint64_t LogicalHash(const ParentTable& table) {
  std::uint64_t hash = 1469598103934665603ULL;
  for (const ParentCell& cell : table.cells) {
    hash = (hash ^ cell.last) * 1099511628211ULL;
    for (std::size_t slot = 0; slot < kWays; ++slot) {
      hash = (hash ^ cell.chk[slot]) * 1099511628211ULL;
      for (std::size_t j = 0; j < kHistoryBytes; ++j) {
        hash = (hash ^ cell.bh[slot][j]) * 1099511628211ULL;
      }
    }
  }
  return hash;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 3 || std::string(argv[1]) != "--output") {
      throw std::runtime_error("usage: verifier --output PATH");
    }
    std::ofstream output(argv[2], std::ios::binary | std::ios::trunc);
    if (!output) throw std::runtime_error("open output");

    ParentTable parent;
    SparseTable sparse;
    Counters counters;
    std::array<std::uint8_t*, kBuckets> parent_saved{};
    std::array<std::uint8_t*, kBuckets> sparse_saved{};

    for (std::uint16_t checksum = 1; checksum <= 64; ++checksum) {
      Apply(parent, sparse, 0, checksum, checksum & 1U ? 0 : 0xf0,
            counters, parent_saved, sparse_saved);
    }

    SeedSyntheticZeroOverflowCase(parent, sparse, kBuckets - 1);
    Apply(parent, sparse, kBuckets - 1, 0, 0, counters, parent_saved,
          sparse_saved);

    std::uint64_t random_state = 0x6a09e667f3bcc909ULL;
    RunRandomEpoch(parent, sparse, random_state, counters, parent_saved,
                   sparse_saved);

    parent.Reset();
    sparse.Reset();
    parent_saved.fill(nullptr);
    sparse_saved.fill(nullptr);
    for (std::size_t bucket = 0; bucket < kBuckets; ++bucket) {
      if (!EqualBucket(parent, sparse, bucket)) {
        throw std::runtime_error("reset divergence");
      }
    }

    RunRandomEpoch(parent, sparse, random_state, counters, parent_saved,
                   sparse_saved);

    for (std::size_t bucket = 0; bucket < kBuckets; ++bucket) {
      if (!EqualBucket(parent, sparse, bucket)) {
        throw std::runtime_error("terminal divergence");
      }
    }

    constexpr std::uint32_t kAllSlotsMask = (1U << kWays) - 1U;
    const bool coverage = counters.returned_slot_mask == kAllSlotsMask &&
                          counters.miss_victim_mask == kAllSlotsMask &&
                          counters.recent_hits != 0 &&
                          counters.scan_hits != 0 && counters.misses != 0 &&
                          counters.persistent_pointer_writes != 0 &&
                          sparse.overflow_allocations() != 0 &&
                          sparse.cross_page_records() != 0;
    if (!coverage) throw std::runtime_error("coverage contract not met");

    output << "{\n"
              << "  \"schema\": \"gamma.enwiki9.cmix-sparse-exact-assoc-transition-verification.v1\",\n"
              << "  \"parent_record_bytes\": " << sizeof(ParentCell) << ",\n"
              << "  \"base_record_bytes\": " << sizeof(SparseBase) << ",\n"
              << "  \"overflow_record_bytes\": " << sizeof(SparseOverflow)
              << ",\n"
              << "  \"base_handle_offset\": "
              << offsetof(SparseBase, overflow_index_plus_one) << ",\n"
              << "  \"base_recent_offset\": " << offsetof(SparseBase, last)
              << ",\n"
              << "  \"base_history_offset\": " << offsetof(SparseBase, bh)
              << ",\n"
              << "  \"buckets_checked\": " << kBuckets << ",\n"
              << "  \"operations_checked\": " << counters.operations << ",\n"
              << "  \"recent_hits\": " << counters.recent_hits << ",\n"
              << "  \"scan_hits\": " << counters.scan_hits << ",\n"
              << "  \"misses\": " << counters.misses << ",\n"
              << "  \"persistent_pointer_writes\": "
              << counters.persistent_pointer_writes << ",\n"
              << "  \"returned_slot_mask\": " << counters.returned_slot_mask
              << ",\n"
              << "  \"miss_victim_mask\": " << counters.miss_victim_mask
              << ",\n"
              << "  \"overflow_allocations_after_reset\": "
              << sparse.overflow_allocations() << ",\n"
              << "  \"cross_page_overflow_records\": "
              << sparse.cross_page_records() << ",\n"
              << "  \"page_bytes\": " << sparse.page_bytes() << ",\n"
              << "  \"overflow_mapping_bytes\": " << sparse.mapping_bytes()
              << ",\n"
              << "  \"synthetic_zero_checksum_overflow_selection_checked\": true,\n"
              << "  \"reset_decommit_checked\": true,\n"
              << "  \"normalized_state_identity\": true,\n"
              << "  \"logical_state_hash\": " << LogicalHash(parent) << ",\n"
              << "  \"determinism_requires_external_repeat\": true,\n"
              << "  \"verdict\": \"pass\",\n"
              << "  \"score_credit_bytes\": 0\n"
              << "}\n";
    output.flush();
    if (!output) throw std::runtime_error("write output");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
