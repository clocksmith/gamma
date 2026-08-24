#include <algorithm>
#include <array>
#include <cerrno>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <sys/stat.h>
#include <unistd.h>

namespace {

constexpr uint64_t kExpectedInputBytes = 587138826ULL;
constexpr uint64_t kKeyBytes = 16ULL;
constexpr uint64_t kRingBytes = 16777216ULL;
constexpr uint64_t kRingMask = 0x00ffffffULL;
constexpr uint64_t kTableEntries = 16777216ULL;
constexpr uint64_t kHashBase = 0x9e3779b185ebca87ULL;
constexpr uint64_t kHashBasePower16 = 0x6fe6ef9fbd3b9581ULL;
constexpr uint64_t kRandomSeed = 0xd1b54a32d192ed03ULL;
constexpr uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr uint64_t kFnvPrime = 1099511628211ULL;
constexpr size_t kReadBufferBytes = 8ULL * 1024ULL * 1024ULL;
constexpr uint64_t kSemanticStateBytes =
    kTableEntries * 8ULL + kRingBytes;

constexpr std::array<std::array<uint64_t, 2>, 6> kDistanceBuckets{{
    {{16777217ULL, 33554432ULL}},
    {{33554433ULL, 67108864ULL}},
    {{67108865ULL, 134217728ULL}},
    {{134217729ULL, 268435456ULL}},
    {{268435457ULL, 536870912ULL}},
    {{536870913ULL, 587138825ULL}},
}};

[[noreturn]] void Fail(const char* operation) {
  std::fprintf(stderr, "fossil-match failure operation=%s errno=%d\n",
               operation, errno);
  std::exit(1);
}

uint64_t FnvByte(uint64_t hash, uint8_t value) {
  return (hash ^ value) * kFnvPrime;
}

uint64_t FnvU32(uint64_t hash, uint32_t value) {
  for (unsigned int shift = 0; shift < 32; shift += 8) {
    hash = FnvByte(hash, static_cast<uint8_t>(value >> shift));
  }
  return hash;
}

uint64_t FnvU64(uint64_t hash, uint64_t value) {
  for (unsigned int shift = 0; shift < 64; shift += 8) {
    hash = FnvByte(hash, static_cast<uint8_t>(value >> shift));
  }
  return hash;
}

uint64_t SplitMix64(uint64_t value) {
  value += 0x9e3779b97f4a7c15ULL;
  value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ULL;
  value = (value ^ (value >> 27)) * 0x94d049bb133111ebULL;
  return value ^ (value >> 31);
}

struct Record {
  uint32_t tag = 0;
  uint32_t continuation_plus_one = 0;
};

static_assert(sizeof(Record) == 8, "FOSSIL-MATCH record must be eight bytes");

struct ControlCounts {
  uint64_t active = 0;
  uint64_t d = 0;
  uint64_t s = 0;
  uint64_t r = 0;
  uint64_t n = 0;
};

struct Measurements {
  uint64_t population_bytes = 0;
  uint64_t positions_scored = 0;
  uint64_t table_lookups = 0;
  uint64_t table_empty = 0;
  uint64_t table_tag_mismatches = 0;
  uint64_t invalid_continuations = 0;
  uint64_t context_verification_failures = 0;
  uint64_t distance_suppressed = 0;
  uint64_t active_bytes = 0;
  uint64_t treatment_correct_bytes = 0;
  uint64_t alias_correct_bytes = 0;
  uint64_t random_correct_bytes = 0;
  uint64_t negated_correct_bytes = 0;
  std::array<ControlCounts, 3> thirds{};
  std::array<ControlCounts, 6> buckets{};
  uint64_t table_replacements = 0;
  uint64_t ring_writes = 0;
  uint64_t hash_rolls = 0;
  uint64_t past_reads = 0;
  uint64_t past_bytes_read = 0;
  uint64_t past_read_advice_failures = 0;
  uint64_t opportunity_hash = kFnvOffset;
  uint64_t treatment_transition_hash = kFnvOffset;
  uint64_t k_transition_hash = kFnvOffset;
};

class FossilMatch {
 public:
  explicit FossilMatch(int input) : input_(input) {}

  void Observe(uint8_t truth, uint64_t i) {
    if (i != measurements_.population_bytes) Fail("nonsequential truth");
    if (i < kKeyBytes) {
      rolling_hash_ = rolling_hash_ * kHashBase + truth;
      terminal_context_[i] = truth;
      ring_[i & kRingMask] = truth;
      ++measurements_.ring_writes;
      ++measurements_.population_bytes;
      return;
    }

    ++measurements_.positions_scored;
    ++measurements_.table_lookups;
    const uint32_t index = static_cast<uint32_t>(rolling_hash_ & kRingMask);
    const uint32_t tag = static_cast<uint32_t>(rolling_hash_ >> 32);
    const Record previous = table_[index];
    bool active = false;
    uint64_t candidate = 0;
    uint8_t history_block[17] = {};

    if (previous.continuation_plus_one == 0) {
      ++measurements_.table_empty;
    } else if (previous.tag != tag) {
      ++measurements_.table_tag_mismatches;
    } else {
      candidate = static_cast<uint64_t>(previous.continuation_plus_one) - 1ULL;
      if (candidate < kKeyBytes || candidate >= i) {
        ++measurements_.invalid_continuations;
      } else {
        PastBytes(candidate - kKeyBytes, sizeof(history_block), i, history_block);
        bool equal = true;
        for (size_t j = 0; j < kKeyBytes; ++j) {
          if (history_block[j] != terminal_context_[j]) {
            equal = false;
            break;
          }
        }
        if (!equal) {
          ++measurements_.context_verification_failures;
        } else if (i - candidate <= kRingBytes) {
          ++measurements_.distance_suppressed;
        } else {
          active = true;
        }
      }
    }

    if (active) Score(i, candidate, history_block[16], truth);

    const uint8_t outgoing = terminal_context_[0];
    for (size_t j = 1; j < terminal_context_.size(); ++j) {
      terminal_context_[j - 1] = terminal_context_[j];
    }
    terminal_context_.back() = truth;

    table_[index] = Record{tag, static_cast<uint32_t>(i + 1ULL)};
    ++measurements_.table_replacements;
    AdvanceTransitionDigests(i, rolling_hash_, index, previous, tag, truth);
    ring_[i & kRingMask] = truth;
    ++measurements_.ring_writes;
    rolling_hash_ = rolling_hash_ * kHashBase -
        static_cast<uint64_t>(outgoing) * kHashBasePower16 + truth;
    ++measurements_.hash_rolls;
    ++measurements_.population_bytes;
  }

  void Finish() {
    if (measurements_.population_bytes != kExpectedInputBytes) {
      errno = EIO;
      Fail("short input");
    }
    uint64_t recomputed = 0;
    for (uint8_t value : terminal_context_) {
      recomputed = recomputed * kHashBase + value;
    }
    terminal_hash_recompute_pass_ = recomputed == rolling_hash_;
    table_hash_ = kFnvOffset;
    for (const Record& record : table_) {
      table_hash_ = FnvU32(table_hash_, record.tag);
      table_hash_ = FnvU32(table_hash_, record.continuation_plus_one);
    }
    ring_hash_ = kFnvOffset;
    for (uint8_t value : ring_) ring_hash_ = FnvByte(ring_hash_, value);
  }

  const Measurements& measurements() const { return measurements_; }
  uint64_t rolling_hash() const { return rolling_hash_; }
  uint64_t table_hash() const { return table_hash_; }
  uint64_t ring_hash() const { return ring_hash_; }
  bool terminal_hash_recompute_pass() const {
    return terminal_hash_recompute_pass_;
  }

 private:
  void PastBytes(uint64_t begin, size_t size, uint64_t current,
                 uint8_t* output) {
    if (size == 0 || begin >= current || begin > current - size) {
      errno = ERANGE;
      Fail("PastBytes causal bound");
    }
    size_t completed = 0;
    while (completed < size) {
      const ssize_t count = pread(
          input_, output + completed, size - completed,
          static_cast<off_t>(begin + completed));
      if (count < 0 && errno == EINTR) continue;
      if (count <= 0) Fail("PastBytes pread");
      completed += static_cast<size_t>(count);
    }
    ++measurements_.past_reads;
    measurements_.past_bytes_read += size;
    const long page_size_signed = sysconf(_SC_PAGESIZE);
    if (page_size_signed > 0) {
      const uint64_t page_size = static_cast<uint64_t>(page_size_signed);
      const uint64_t advice_begin = begin - (begin % page_size);
      const uint64_t end = begin + size;
      const uint64_t advice_end =
          ((end + page_size - 1ULL) / page_size) * page_size;
      const int advice = posix_fadvise(
          input_, static_cast<off_t>(advice_begin),
          static_cast<off_t>(advice_end - advice_begin), POSIX_FADV_DONTNEED);
      if (advice != 0) ++measurements_.past_read_advice_failures;
    } else {
      ++measurements_.past_read_advice_failures;
    }
  }

  static size_t Third(uint64_t position) {
    return std::min<size_t>(2, static_cast<size_t>(
        (position * 3ULL) / kExpectedInputBytes));
  }

  static size_t DistanceBucket(uint64_t distance) {
    for (size_t bucket = 0; bucket < kDistanceBuckets.size(); ++bucket) {
      if (distance >= kDistanceBuckets[bucket][0] &&
          distance <= kDistanceBuckets[bucket][1]) {
        return bucket;
      }
    }
    errno = ERANGE;
    Fail("distance bucket");
  }

  static void Count(ControlCounts* counts, bool d, bool s, bool r, bool n) {
    ++counts->active;
    counts->d += d ? 1ULL : 0ULL;
    counts->s += s ? 1ULL : 0ULL;
    counts->r += r ? 1ULL : 0ULL;
    counts->n += n ? 1ULL : 0ULL;
  }

  void Score(uint64_t i, uint64_t candidate, uint8_t d, uint8_t truth) {
    const uint8_t s = ring_[candidate & kRingMask];
    const uint8_t r = static_cast<uint8_t>(SplitMix64(
        rolling_hash_ ^ (i << 1) ^ kRandomSeed) >> 56);
    const uint8_t n = static_cast<uint8_t>(d ^ 0xffU);
    const bool d_correct = d == truth;
    const bool s_correct = s == truth;
    const bool r_correct = r == truth;
    const bool n_correct = n == truth;
    ++measurements_.active_bytes;
    measurements_.treatment_correct_bytes += d_correct ? 1ULL : 0ULL;
    measurements_.alias_correct_bytes += s_correct ? 1ULL : 0ULL;
    measurements_.random_correct_bytes += r_correct ? 1ULL : 0ULL;
    measurements_.negated_correct_bytes += n_correct ? 1ULL : 0ULL;
    Count(&measurements_.thirds[Third(i)], d_correct, s_correct, r_correct,
          n_correct);
    Count(&measurements_.buckets[DistanceBucket(i - candidate)], d_correct,
          s_correct, r_correct, n_correct);
    uint64_t& digest = measurements_.opportunity_hash;
    digest = FnvU64(digest, i);
    digest = FnvU64(digest, rolling_hash_);
    digest = FnvU64(digest, candidate);
    digest = FnvByte(digest, d);
    digest = FnvByte(digest, s);
    digest = FnvByte(digest, r);
    digest = FnvByte(digest, n);
    digest = FnvByte(digest, truth);
  }

  void AdvanceTransitionDigests(uint64_t i, uint64_t hash, uint32_t index,
                                const Record& previous, uint32_t tag,
                                uint8_t truth) {
    auto advance = [&](uint64_t value) {
      value = FnvU64(value, i);
      value = FnvU64(value, hash);
      value = FnvU32(value, index);
      value = FnvU32(value, previous.tag);
      value = FnvU32(value, previous.continuation_plus_one);
      value = FnvU32(value, tag);
      value = FnvByte(value, truth);
      return value;
    };
    measurements_.treatment_transition_hash =
        advance(measurements_.treatment_transition_hash);
    measurements_.k_transition_hash = advance(measurements_.k_transition_hash);
  }

  int input_;
  std::array<Record, kTableEntries> table_{};
  std::array<uint8_t, kRingBytes> ring_{};
  std::array<uint8_t, kKeyBytes> terminal_context_{};
  Measurements measurements_{};
  uint64_t rolling_hash_ = 0;
  uint64_t table_hash_ = 0;
  uint64_t ring_hash_ = 0;
  bool terminal_hash_recompute_pass_ = false;
};

int64_t Margin(const ControlCounts& counts) {
  const uint64_t control = std::max({counts.s, counts.r, counts.n});
  return static_cast<int64_t>(counts.d) - static_cast<int64_t>(control);
}

bool CountsBounded(const ControlCounts& counts) {
  return counts.d <= counts.active && counts.s <= counts.active &&
      counts.r <= counts.active && counts.n <= counts.active;
}

void WriteCounts(FILE* output, const ControlCounts& counts) {
  std::fprintf(output,
      "{\"active\":%" PRIu64 ",\"D\":%" PRIu64
      ",\"S\":%" PRIu64 ",\"R\":%" PRIu64 ",\"N\":%" PRIu64 "}",
      counts.active, counts.d, counts.s, counts.r, counts.n);
}

void WriteReceipt(const char* path, const FossilMatch& scanner) {
  const int descriptor = open(path, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC |
      O_NOFOLLOW, 0600);
  if (descriptor < 0) Fail("create output");
  FILE* output = fdopen(descriptor, "wb");
  if (output == nullptr) {
    close(descriptor);
    Fail("fdopen output");
  }
  const Measurements& m = scanner.measurements();
  int64_t minimum_third_margin = std::numeric_limits<int64_t>::max();
  for (const ControlCounts& counts : m.thirds) {
    minimum_third_margin = std::min(minimum_third_margin, Margin(counts));
  }
  uint64_t positive_buckets = 0;
  for (const ControlCounts& counts : m.buckets) {
    if (Margin(counts) > 0) ++positive_buckets;
  }
  const bool transition_identity =
      m.treatment_transition_hash == m.k_transition_hash;
  uint64_t third_active = 0;
  uint64_t third_d = 0;
  uint64_t third_s = 0;
  uint64_t third_r = 0;
  uint64_t third_n = 0;
  bool partition_counts_bounded = true;
  for (const ControlCounts& counts : m.thirds) {
    third_active += counts.active;
    third_d += counts.d;
    third_s += counts.s;
    third_r += counts.r;
    third_n += counts.n;
    partition_counts_bounded = partition_counts_bounded && CountsBounded(counts);
  }
  uint64_t bucket_active = 0;
  uint64_t bucket_d = 0;
  uint64_t bucket_s = 0;
  uint64_t bucket_r = 0;
  uint64_t bucket_n = 0;
  for (const ControlCounts& counts : m.buckets) {
    bucket_active += counts.active;
    bucket_d += counts.d;
    bucket_s += counts.s;
    bucket_r += counts.r;
    bucket_n += counts.n;
    partition_counts_bounded = partition_counts_bounded && CountsBounded(counts);
  }
  const uint64_t lookup_partition = m.table_empty + m.table_tag_mismatches +
      m.invalid_continuations + m.context_verification_failures +
      m.distance_suppressed + m.active_bytes;
  const bool causal_pass =
      scanner.terminal_hash_recompute_pass() && transition_identity &&
      m.population_bytes == kExpectedInputBytes &&
      m.positions_scored == kExpectedInputBytes - kKeyBytes &&
      m.table_lookups == m.positions_scored &&
      m.table_replacements == m.positions_scored &&
      m.ring_writes == kExpectedInputBytes &&
      m.hash_rolls == m.positions_scored &&
      lookup_partition == m.table_lookups &&
      m.past_reads == m.context_verification_failures +
          m.distance_suppressed + m.active_bytes &&
      m.past_bytes_read == m.past_reads * 17ULL &&
      m.treatment_correct_bytes <= m.active_bytes &&
      m.alias_correct_bytes <= m.active_bytes &&
      m.random_correct_bytes <= m.active_bytes &&
      m.negated_correct_bytes <= m.active_bytes &&
      partition_counts_bounded && third_active == m.active_bytes &&
      bucket_active == m.active_bytes &&
      third_d == m.treatment_correct_bytes &&
      third_s == m.alias_correct_bytes && third_r == m.random_correct_bytes &&
      third_n == m.negated_correct_bytes &&
      bucket_d == m.treatment_correct_bytes &&
      bucket_s == m.alias_correct_bytes && bucket_r == m.random_correct_bytes &&
      bucket_n == m.negated_correct_bytes;

  std::fprintf(output,
      "{\n"
      "  \"schema\": \"gamma.enwiki9.fxcm-fossil-match-scan.v1\",\n"
      "  \"candidate_id\": \"fxcm_fossil_match_q0_v3\",\n"
      "  \"population_bytes\": %" PRIu64 ",\n"
      "  \"population_sha256_expected\": \"7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce\",\n"
      "  \"positions_scored\": %" PRIu64 ",\n"
      "  \"table_lookups\": %" PRIu64 ",\n"
      "  \"table_empty\": %" PRIu64 ",\n"
      "  \"table_tag_mismatches\": %" PRIu64 ",\n"
      "  \"invalid_continuations\": %" PRIu64 ",\n"
      "  \"context_verification_failures\": %" PRIu64 ",\n"
      "  \"distance_suppressed\": %" PRIu64 ",\n"
      "  \"active_bytes\": %" PRIu64 ",\n"
      "  \"treatment_correct_bytes\": %" PRIu64 ",\n"
      "  \"alias_correct_bytes\": %" PRIu64 ",\n"
      "  \"random_correct_bytes\": %" PRIu64 ",\n"
      "  \"negated_correct_bytes\": %" PRIu64 ",\n",
      m.population_bytes, m.positions_scored, m.table_lookups, m.table_empty,
      m.table_tag_mismatches, m.invalid_continuations,
      m.context_verification_failures, m.distance_suppressed, m.active_bytes,
      m.treatment_correct_bytes, m.alias_correct_bytes, m.random_correct_bytes,
      m.negated_correct_bytes);

  std::fprintf(output, "  \"correct_by_third\": [");
  for (size_t index = 0; index < m.thirds.size(); ++index) {
    if (index != 0) std::fputc(',', output);
    WriteCounts(output, m.thirds[index]);
  }
  std::fprintf(output, "],\n  \"correct_by_distance_bucket\": [");
  for (size_t index = 0; index < m.buckets.size(); ++index) {
    if (index != 0) std::fputc(',', output);
    WriteCounts(output, m.buckets[index]);
  }
  std::fprintf(output,
      "],\n"
      "  \"minimum_third_treatment_minus_max_control_correct_bytes\": %" PRId64 ",\n"
      "  \"positive_distance_bucket_count\": %" PRIu64 ",\n"
      "  \"table_replacements\": %" PRIu64 ",\n"
      "  \"ring_writes\": %" PRIu64 ",\n"
      "  \"hash_rolls\": %" PRIu64 ",\n"
      "  \"past_reads\": %" PRIu64 ",\n"
      "  \"past_bytes_read\": %" PRIu64 ",\n"
      "  \"past_read_advice_failures\": %" PRIu64 ",\n"
      "  \"final_rolling_hash\": \"%016" PRIx64 "\",\n"
      "  \"terminal_hash_recompute_pass\": %s,\n"
      "  \"table_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"ring_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"opportunity_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"treatment_transition_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"k_transition_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"treatment_k_state_identity_pass\": %s,\n"
      "  \"control_outcomes_feed_state\": false,\n"
      "  \"causal_and_verification_pass\": %s,\n"
      "  \"semantic_state_bytes\": %" PRIu64 ",\n"
      "  \"archive_authority\": false,\n"
      "  \"score_credit_bytes\": 0\n"
      "}\n",
      minimum_third_margin, positive_buckets, m.table_replacements,
      m.ring_writes, m.hash_rolls, m.past_reads, m.past_bytes_read,
      m.past_read_advice_failures, scanner.rolling_hash(),
      scanner.terminal_hash_recompute_pass() ? "true" : "false",
      scanner.table_hash(), scanner.ring_hash(), m.opportunity_hash,
      m.treatment_transition_hash, m.k_transition_hash,
      transition_identity ? "true" : "false", causal_pass ? "true" : "false",
      kSemanticStateBytes);
  if (std::fflush(output) != 0 || fsync(descriptor) != 0) {
    std::fclose(output);
    Fail("flush output");
  }
  if (std::fclose(output) != 0) Fail("close output");
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 3) {
    std::fprintf(stderr, "usage: %s TRANSFORMED_READY OUTPUT_JSON\n", argv[0]);
    return 64;
  }
  struct stat metadata = {};
  if (lstat(argv[1], &metadata) != 0 || !S_ISREG(metadata.st_mode) ||
      metadata.st_nlink != 1 ||
      static_cast<uint64_t>(metadata.st_size) != kExpectedInputBytes) {
    errno = EINVAL;
    Fail("input identity geometry");
  }
  const int input = open(argv[1], O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (input < 0) Fail("open input");
  const int sequential_advice = posix_fadvise(input, 0, 0, POSIX_FADV_SEQUENTIAL);
  if (sequential_advice != 0) {
    errno = sequential_advice;
    Fail("sequential fadvise");
  }

  static FossilMatch scanner(input);
  static std::array<uint8_t, kReadBufferBytes> buffer{};
  uint64_t offset = 0;
  for (;;) {
    const ssize_t count = read(input, buffer.data(), buffer.size());
    if (count < 0 && errno == EINTR) continue;
    if (count < 0) Fail("read input");
    if (count == 0) break;
    for (ssize_t index = 0; index < count; ++index) {
      scanner.Observe(buffer[static_cast<size_t>(index)], offset++);
    }
    const uint64_t chunk_begin = offset - static_cast<uint64_t>(count);
    (void)posix_fadvise(input, static_cast<off_t>(chunk_begin), count,
                        POSIX_FADV_DONTNEED);
  }
  scanner.Finish();
  if (close(input) != 0) Fail("close input");
  WriteReceipt(argv[2], scanner);
  return 0;
}
