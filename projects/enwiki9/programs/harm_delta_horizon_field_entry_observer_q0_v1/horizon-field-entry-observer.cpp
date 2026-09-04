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
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

namespace {

constexpr std::uint64_t kHashBase = UINT64_C(0x9e3779b185ebca87);
constexpr std::uint64_t kHashBasePower16 = UINT64_C(0x6fe6ef9fbd3b9581);
constexpr std::uint64_t kFnvOffset = UINT64_C(1469598103934665603);
constexpr std::uint64_t kFnvPrime = UINT64_C(1099511628211);
constexpr std::uint64_t kProductionWrtBytes = UINT64_C(647798592);
constexpr std::uint64_t kProductionMinimumAge = UINT64_C(100000000);
constexpr unsigned int kProductionTableBits = 24U;
constexpr std::uint64_t kProductionTableEntries = UINT64_C(1) << kProductionTableBits;
constexpr std::uint64_t kProductionDonorBytes = UINT64_C(512);
constexpr std::uint64_t kProductionKeyBytes = UINT64_C(16);
constexpr char kExpectedRollingHash[] = "01345eea197318a2";
constexpr char kExpectedAnchorHash[] = "199185a886ba1064";
constexpr char kExpectedTransitionHash[] = "46e3b81f2877dde1";

constexpr std::size_t kTapeHeaderBytes = 192U;
constexpr std::size_t kTapeRecordBytes = 88U;
constexpr std::size_t kRawHeaderBytes = 32U;
constexpr std::array<std::uint8_t, 8> kTapeMagic{{'G','S','R','T','2',0,0,0}};
constexpr std::array<std::uint8_t, 8> kRawMagic{{'H','G','S','R','1',0,0,0}};
constexpr std::uint8_t kFieldEntry = 2U;
constexpr std::uint8_t kPredictive = 3U;
constexpr std::uint8_t kDeferred = 4U;
constexpr std::array<std::uint8_t, 10> kExpectedFlags{{
    0U, 128U, 137U, 11U, 77U, 137U, 144U, 128U, 160U, 160U,
}};
constexpr std::array<std::uint8_t, 10> kExpectedKeys{{
    0U, 0U, 1U, 1U, 1U, 1U, 2U, 0U, 0U, 0U,
}};

[[noreturn]] void Fail(const char* message) {
  std::fprintf(stderr, "horizon-field-entry-observer failure=%s errno=%d\n",
               message, errno);
  std::exit(1);
}

std::uint32_t ReadLe32(const std::uint8_t* input) {
  std::uint32_t value = 0;
  for (unsigned int index = 0; index < 4U; ++index) {
    value |= static_cast<std::uint32_t>(input[index]) << (8U * index);
  }
  return value;
}

std::uint64_t ReadLe64(const std::uint8_t* input) {
  std::uint64_t value = 0;
  for (unsigned int index = 0; index < 8U; ++index) {
    value |= static_cast<std::uint64_t>(input[index]) << (8U * index);
  }
  return value;
}

void PutLe64(std::uint8_t* output, std::uint64_t value) {
  for (unsigned int index = 0; index < 8U; ++index) {
    output[index] = static_cast<std::uint8_t>(value >> (8U * index));
  }
}

std::uint64_t FnvByte(std::uint64_t hash, std::uint8_t value) {
  return (hash ^ value) * kFnvPrime;
}

std::uint64_t FnvU32(std::uint64_t hash, std::uint32_t value) {
  for (unsigned int shift = 0; shift < 32U; shift += 8U) {
    hash = FnvByte(hash, static_cast<std::uint8_t>(value >> shift));
  }
  return hash;
}

std::uint64_t FnvU64(std::uint64_t hash, std::uint64_t value) {
  for (unsigned int shift = 0; shift < 64U; shift += 8U) {
    hash = FnvByte(hash, static_cast<std::uint8_t>(value >> shift));
  }
  return hash;
}

std::uint64_t Power(std::uint64_t base, std::uint64_t exponent) {
  std::uint64_t result = 1;
  while (exponent != 0) {
    if ((exponent & 1U) != 0U) result *= base;
    base *= base;
    exponent >>= 1U;
  }
  return result;
}

class Mapping {
 public:
  Mapping(const char* path, const char* label) {
    struct stat lexical{};
    if (lstat(path, &lexical) != 0 || !S_ISREG(lexical.st_mode) ||
        S_ISLNK(lexical.st_mode) || lexical.st_size <= 0) {
      Fail(label);
    }
    fd_ = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd_ < 0) Fail(label);
    struct stat opened{};
    if (fstat(fd_, &opened) != 0 || !S_ISREG(opened.st_mode) ||
        opened.st_dev != lexical.st_dev || opened.st_ino != lexical.st_ino ||
        opened.st_size != lexical.st_size) {
      Fail(label);
    }
    bytes_ = static_cast<std::uint64_t>(opened.st_size);
    void* mapped = mmap(nullptr, static_cast<std::size_t>(bytes_), PROT_READ,
                        MAP_PRIVATE, fd_, 0);
    if (mapped == MAP_FAILED) Fail(label);
    data_ = static_cast<const std::uint8_t*>(mapped);
  }

  ~Mapping() {
    if (data_ != nullptr) {
      (void)munmap(const_cast<std::uint8_t*>(data_),
                   static_cast<std::size_t>(bytes_));
    }
    if (fd_ >= 0) (void)close(fd_);
  }

  Mapping(const Mapping&) = delete;
  Mapping& operator=(const Mapping&) = delete;

  const std::uint8_t* data() const { return data_; }
  std::uint64_t bytes() const { return bytes_; }

 private:
  int fd_ = -1;
  std::uint64_t bytes_ = 0;
  const std::uint8_t* data_ = nullptr;
};

struct Config {
  const char* mode = "fixture";
  std::uint64_t key_bytes = 16;
  std::uint64_t minimum_age = 32;
  std::uint64_t donor_bytes = 16;
  unsigned int table_bits = 8;

  std::uint64_t table_entries() const {
    return UINT64_C(1) << table_bits;
  }
  std::uint64_t table_mask() const { return table_entries() - 1U; }
  std::uint64_t hash_power() const { return Power(kHashBase, key_bytes); }
};

struct TapeRow {
  std::uint64_t source = 0;
  std::uint64_t availability = 0;
  std::uint64_t first_bit = 0;
  std::uint64_t raw_before = 0;
  std::uint64_t raw_after = 0;
  std::uint64_t route_lo = 0;
  std::uint64_t route_hi = 0;
  std::uint64_t witness_lo = 0;
  std::uint64_t witness_hi = 0;
  std::uint64_t virtual_ordinal = 0;
  std::uint32_t field_ordinal = 0;
  std::uint8_t event = 0;
  std::uint8_t flags = 0;
  std::uint8_t depth = 0;
  std::uint8_t key_identity = 0;
};

unsigned int Priority(std::uint8_t event) {
  if (event == kDeferred) return 0U;
  if (event == kPredictive) return 2U;
  return 1U;
}

class Tape {
 public:
  Tape(const Mapping& mapping, std::uint64_t wrt_bytes)
      : mapping_(mapping), wrt_bytes_(wrt_bytes) {
    if (mapping_.bytes() < kTapeHeaderBytes ||
        !std::equal(kTapeMagic.begin(), kTapeMagic.end(), mapping_.data())) {
      Fail("GSRT2 header");
    }
    const std::uint8_t* header = mapping_.data();
    if (ReadLe32(header + 8) != 2U ||
        ReadLe32(header + 12) != kTapeHeaderBytes ||
        ReadLe32(header + 16) != kTapeRecordBytes ||
        ReadLe32(header + 20) > 1U) {
      Fail("GSRT2 ABI");
    }
    if (ReadLe64(header + 32) != wrt_bytes_) Fail("GSRT2 WRT population");
    raw_bytes_ = ReadLe64(header + 40);
    record_count_ = ReadLe64(header + 56);
    for (std::size_t index = 0; index < counts_.size(); ++index) {
      counts_[index] = ReadLe64(header + 72 + 8U * index);
    }
    deferred_updates_ = ReadLe64(header + 144);
    if (ReadLe64(header + 152) != 0 || ReadLe64(header + 160) != 0) {
      Fail("GSRT2 causal header");
    }
    parser_digest_ = ReadLe64(header + 168);
    if (record_count_ >
        (std::numeric_limits<std::uint64_t>::max() - kTapeHeaderBytes) /
            kTapeRecordBytes ||
        mapping_.bytes() != kTapeHeaderBytes + record_count_ * kTapeRecordBytes) {
      Fail("GSRT2 length");
    }
    std::uint64_t count_sum = 0;
    for (std::uint64_t count : counts_) count_sum += count;
    if (count_sum != record_count_ || counts_[kDeferred - 1U] != deferred_updates_) {
      Fail("GSRT2 header counts");
    }
    Validate();
  }

  std::uint64_t record_count() const { return record_count_; }

  TapeRow row(std::uint64_t index) const {
    if (index >= record_count_) Fail("GSRT2 row index");
    const std::uint8_t* input = mapping_.data() + kTapeHeaderBytes +
        index * kTapeRecordBytes;
    TapeRow result{};
    result.source = ReadLe64(input);
    result.availability = ReadLe64(input + 8);
    result.first_bit = ReadLe64(input + 16);
    result.raw_before = ReadLe64(input + 24);
    result.raw_after = ReadLe64(input + 32);
    result.route_lo = ReadLe64(input + 40);
    result.route_hi = ReadLe64(input + 48);
    result.witness_lo = ReadLe64(input + 56);
    result.witness_hi = ReadLe64(input + 64);
    result.virtual_ordinal = ReadLe64(input + 72);
    result.field_ordinal = ReadLe32(input + 80);
    result.event = input[84];
    result.flags = input[85];
    result.depth = input[86];
    result.key_identity = input[87];
    return result;
  }

 private:
  void Validate() const {
    std::array<std::uint64_t, 9> observed{};
    std::uint64_t digest = kFnvOffset;
    bool has_order = false;
    std::array<std::uint64_t, 3> previous{};
    for (std::uint64_t index = 0; index < record_count_; ++index) {
      const TapeRow current = row(index);
      if (current.event == 0U || current.event >= kExpectedFlags.size() ||
          current.flags != kExpectedFlags[current.event] ||
          current.key_identity != kExpectedKeys[current.event]) {
        Fail("GSRT2 event identity");
      }
      if (current.source >= wrt_bytes_ || current.availability > wrt_bytes_ ||
          current.source > current.availability ||
          current.first_bit != current.availability * 8U ||
          current.raw_before > current.raw_after || current.raw_after > raw_bytes_) {
        Fail("GSRT2 coordinate geometry");
      }
      if (current.event == kPredictive) {
        if (current.availability != current.source) Fail("GSRT2 predictive timing");
      } else if (current.event == kDeferred) {
        const bool ordinary = current.availability == current.source + 2U;
        const bool terminal = current.availability == wrt_bytes_ &&
            current.availability == current.source + 1U;
        if (!ordinary && !terminal) Fail("GSRT2 deferred timing");
      } else if (current.availability != current.source + 1U) {
        Fail("GSRT2 structural timing");
      }
      if (current.depth > 16U) Fail("GSRT2 depth");
      const bool routed = (current.flags & 1U) != 0U;
      const bool route_zero = current.route_lo == 0U && current.route_hi == 0U;
      const bool witness_zero = current.witness_lo == 0U && current.witness_hi == 0U;
      if (routed) {
        if (route_zero || witness_zero || current.depth == 0U) {
          Fail("GSRT2 routed identity");
        }
      } else if (!route_zero || !witness_zero || current.virtual_ordinal != 0U) {
        Fail("GSRT2 plain identity");
      }
      const std::array<std::uint64_t, 3> order{{
          current.availability, Priority(current.event), current.source,
      }};
      if (has_order && order < previous) Fail("GSRT2 causal order");
      has_order = true;
      previous = order;
      ++observed[current.event - 1U];
      digest = FnvU64(digest, current.source);
      digest = FnvU64(digest, current.availability);
      digest = FnvU64(digest, current.route_lo);
      digest = FnvU64(digest, current.route_hi);
      digest = FnvU64(digest, current.virtual_ordinal);
      digest = FnvByte(digest, current.event);
      digest = FnvByte(digest, current.flags);
    }
    if (observed != counts_ || digest != parser_digest_) {
      Fail("GSRT2 body binding");
    }
  }

  const Mapping& mapping_;
  std::uint64_t wrt_bytes_ = 0;
  std::uint64_t raw_bytes_ = 0;
  std::uint64_t record_count_ = 0;
  std::array<std::uint64_t, 9> counts_{};
  std::uint64_t deferred_updates_ = 0;
  std::uint64_t parser_digest_ = 0;
};

struct Record {
  std::uint32_t tag = 0;
  std::uint32_t continuation_plus_one = 0;
};
static_assert(sizeof(Record) == 8U, "HORIZON record geometry");

struct Candidate {
  bool active = false;
  std::uint64_t source = 0;
};

struct Measurements {
  std::uint64_t field_entry_events = 0;
  std::uint64_t unique_field_entry_targets = 0;
  std::uint64_t emitted_seeds = 0;
  std::uint64_t empty = 0;
  std::uint64_t tag_mismatch = 0;
  std::uint64_t invalid = 0;
  std::uint64_t age_suppressed = 0;
  std::uint64_t donor_suppressed = 0;
  std::uint64_t context_verify_fail = 0;
  std::uint64_t active = 0;
  std::uint64_t transition = kFnvOffset;
};

class RawWriter {
 public:
  explicit RawWriter(const char* path) {
    fd_ = open(path, O_RDWR | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (fd_ < 0) Fail("create raw observer output");
    std::array<std::uint8_t, kRawHeaderBytes> header{};
    std::copy(kRawMagic.begin(), kRawMagic.end(), header.begin());
    WriteAll(header.data(), header.size());
  }

  ~RawWriter() {
    if (fd_ >= 0) (void)close(fd_);
  }

  void Row(std::uint64_t target, std::uint64_t source,
           std::uint64_t context_hash, std::uint64_t transition_hash) {
    std::array<std::uint8_t, 32> row{};
    PutLe64(row.data(), target);
    PutLe64(row.data() + 8, source);
    PutLe64(row.data() + 16, context_hash);
    PutLe64(row.data() + 24, transition_hash);
    WriteAll(row.data(), row.size());
    ++rows_;
  }

  void Finish(std::uint64_t wrt_bytes, std::uint64_t terminal_transition) {
    std::array<std::uint8_t, kRawHeaderBytes> header{};
    std::copy(kRawMagic.begin(), kRawMagic.end(), header.begin());
    PutLe64(header.data() + 8, wrt_bytes);
    PutLe64(header.data() + 16, rows_);
    PutLe64(header.data() + 24, terminal_transition);
    if (pwrite(fd_, header.data(), header.size(), 0) !=
        static_cast<ssize_t>(header.size()) || fsync(fd_) != 0 || close(fd_) != 0) {
      fd_ = -1;
      Fail("finalize raw observer output");
    }
    fd_ = -1;
  }

 private:
  void WriteAll(const std::uint8_t* data, std::size_t size) {
    std::size_t done = 0;
    while (done < size) {
      const ssize_t count = write(fd_, data + done, size - done);
      if (count < 0 && errno == EINTR) continue;
      if (count <= 0) Fail("write raw observer output");
      done += static_cast<std::size_t>(count);
    }
  }

  int fd_ = -1;
  std::uint64_t rows_ = 0;
};

class Observer {
 public:
  Observer(const Config& config, const Mapping& wrt, const Tape& tape,
           RawWriter* output)
      : config_(config), wrt_(wrt), tape_(tape), output_(output),
        anchor_(static_cast<std::size_t>(config.table_entries())),
        context_(static_cast<std::size_t>(config.key_bytes), 0U) {
    if (config_.key_bytes != 16U || config_.table_bits == 0U ||
        config_.table_bits > 24U || config_.hash_power() != kHashBasePower16) {
      Fail("observer configuration");
    }
  }

  void Run() {
    std::uint64_t tape_index = 0;
    for (std::uint64_t coordinate = 0; coordinate < wrt_.bytes(); ++coordinate) {
      bool field_entry = false;
      while (tape_index < tape_.record_count()) {
        const TapeRow current = tape_.row(tape_index);
        if (current.availability > coordinate) break;
        if (current.availability < coordinate) Fail("late GSRT2 callback");
        if (current.event == kFieldEntry) {
          field_entry = true;
          ++measurements_.field_entry_events;
        }
        ++tape_index;
      }
      if (field_entry) {
        ++measurements_.unique_field_entry_targets;
        const Candidate candidate = Evaluate(coordinate);
        if (candidate.active) {
          output_->Row(coordinate, candidate.source, rolling_hash_,
                       measurements_.transition);
          ++measurements_.emitted_seeds;
        }
      }
      ObserveTruth(coordinate, wrt_.data()[coordinate]);
    }
    while (tape_index < tape_.record_count()) {
      const TapeRow current = tape_.row(tape_index++);
      if (current.availability != wrt_.bytes()) Fail("GSRT2 callback beyond WRT");
    }
    std::uint64_t recomputed = 0;
    for (std::uint8_t byte : context_) recomputed = recomputed * kHashBase + byte;
    if (recomputed != rolling_hash_) Fail("terminal rolling hash recomputation");
    anchor_hash_ = kFnvOffset;
    for (const Record& record : anchor_) {
      anchor_hash_ = FnvU32(anchor_hash_, record.tag);
      anchor_hash_ = FnvU32(anchor_hash_, record.continuation_plus_one);
    }
    output_->Finish(wrt_.bytes(), measurements_.transition);
  }

  const Measurements& measurements() const { return measurements_; }
  std::uint64_t rolling_hash() const { return rolling_hash_; }
  std::uint64_t anchor_hash() const { return anchor_hash_; }

 private:
  Candidate Evaluate(std::uint64_t current) {
    if (current < config_.key_bytes) {
      ++measurements_.empty;
      return {};
    }
    const std::uint32_t index = static_cast<std::uint32_t>(
        rolling_hash_ & config_.table_mask());
    const std::uint32_t tag = static_cast<std::uint32_t>(rolling_hash_ >> 32U);
    const Record record = anchor_[index];
    if (record.continuation_plus_one == 0U) {
      ++measurements_.empty;
      return {};
    }
    if (record.tag != tag) {
      ++measurements_.tag_mismatch;
      return {};
    }
    const std::uint64_t source =
        static_cast<std::uint64_t>(record.continuation_plus_one) - 1U;
    if (source < config_.key_bytes || source >= current) {
      ++measurements_.invalid;
      return {};
    }
    if (current - source <= config_.minimum_age) {
      ++measurements_.age_suppressed;
      return {};
    }
    if (source + config_.donor_bytes > current) {
      ++measurements_.donor_suppressed;
      return {};
    }
    if (std::memcmp(wrt_.data() + source - config_.key_bytes,
                    context_.data(), static_cast<std::size_t>(config_.key_bytes)) != 0) {
      ++measurements_.context_verify_fail;
      return {};
    }
    ++measurements_.active;
    return Candidate{true, source};
  }

  void ObserveTruth(std::uint64_t coordinate, std::uint8_t truth) {
    if (coordinate < config_.key_bytes) {
      rolling_hash_ = rolling_hash_ * kHashBase + truth;
      context_[static_cast<std::size_t>(coordinate)] = truth;
      return;
    }
    const std::uint32_t index = static_cast<std::uint32_t>(
        rolling_hash_ & config_.table_mask());
    const std::uint32_t tag = static_cast<std::uint32_t>(rolling_hash_ >> 32U);
    const Record old = anchor_[index];
    Record next = old;
    if (old.continuation_plus_one == 0U || old.tag != tag) {
      if (coordinate >= std::numeric_limits<std::uint32_t>::max()) {
        Fail("continuation coordinate overflow");
      }
      next = Record{tag, static_cast<std::uint32_t>(coordinate + 1U)};
      anchor_[index] = next;
    }
    std::uint64_t transition = measurements_.transition;
    transition = FnvU64(transition, coordinate);
    transition = FnvU64(transition, rolling_hash_);
    transition = FnvU32(transition, index);
    transition = FnvU32(transition, old.tag);
    transition = FnvU32(transition, old.continuation_plus_one);
    transition = FnvU32(transition, next.tag);
    transition = FnvU32(transition, next.continuation_plus_one);
    measurements_.transition = FnvByte(transition, truth);

    const std::uint8_t outgoing = context_.front();
    std::move(context_.begin() + 1, context_.end(), context_.begin());
    context_.back() = truth;
    rolling_hash_ = rolling_hash_ * kHashBase -
        static_cast<std::uint64_t>(outgoing) * config_.hash_power() + truth;
  }

  const Config config_;
  const Mapping& wrt_;
  const Tape& tape_;
  RawWriter* output_;
  std::vector<Record> anchor_;
  std::vector<std::uint8_t> context_;
  Measurements measurements_{};
  std::uint64_t rolling_hash_ = 0;
  std::uint64_t anchor_hash_ = 0;
};

FILE* OpenJson(const char* path) {
  const int descriptor = open(
      path, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0600);
  if (descriptor < 0) Fail("create JSON output");
  FILE* output = fdopen(descriptor, "wb");
  if (output == nullptr) {
    (void)close(descriptor);
    Fail("fdopen JSON output");
  }
  return output;
}

void CloseJson(FILE* output) {
  const int descriptor = fileno(output);
  if (std::fflush(output) != 0 || fsync(descriptor) != 0 ||
      std::fclose(output) != 0) {
    Fail("close JSON output");
  }
}

void DescribeProduction(const char* path) {
  if (Power(kHashBase, kProductionKeyBytes) != kHashBasePower16) {
    Fail("production hash power");
  }
  FILE* output = OpenJson(path);
  std::fprintf(
      output,
      "{\n"
      "  \"schema\": \"gamma.enwiki9.harm-horizon-field-entry-production-config.v1\",\n"
      "  \"wrt_bytes\": %" PRIu64 ",\n"
      "  \"key_bytes\": %" PRIu64 ",\n"
      "  \"hash_base\": \"%016" PRIx64 "\",\n"
      "  \"hash_base_power_16\": \"%016" PRIx64 "\",\n"
      "  \"table_bits\": %u,\n"
      "  \"table_entries\": %" PRIu64 ",\n"
      "  \"record_bytes\": %zu,\n"
      "  \"minimum_age_bytes\": %" PRIu64 ",\n"
      "  \"donor_bytes\": %" PRIu64 ",\n"
      "  \"expected_terminal_rolling_hash\": \"%s\",\n"
      "  \"expected_terminal_anchor_table_hash\": \"%s\",\n"
      "  \"expected_terminal_anchor_transition_hash\": \"%s\",\n"
      "  \"archive_authority\": false,\n"
      "  \"corpus_execution_authority\": false,\n"
      "  \"score_credit_bytes\": 0\n"
      "}\n",
      kProductionWrtBytes, kProductionKeyBytes, kHashBase,
      kHashBasePower16, kProductionTableBits, kProductionTableEntries,
      sizeof(Record), kProductionMinimumAge, kProductionDonorBytes,
      kExpectedRollingHash, kExpectedAnchorHash, kExpectedTransitionHash);
  CloseJson(output);
}

void WriteSummary(const char* path, const Config& config,
                  const Observer& observer, std::uint64_t wrt_bytes) {
  const Measurements& values = observer.measurements();
  FILE* output = OpenJson(path);
  std::fprintf(
      output,
      "{\n"
      "  \"schema\": \"gamma.enwiki9.harm-horizon-field-entry-observer.v1\",\n"
      "  \"mode\": \"%s\",\n"
      "  \"wrt_bytes\": %" PRIu64 ",\n"
      "  \"key_bytes\": %" PRIu64 ",\n"
      "  \"hash_base\": \"%016" PRIx64 "\",\n"
      "  \"hash_power\": \"%016" PRIx64 "\",\n"
      "  \"table_bits\": %u,\n"
      "  \"table_entries\": %" PRIu64 ",\n"
      "  \"minimum_age_bytes\": %" PRIu64 ",\n"
      "  \"donor_bytes\": %" PRIu64 ",\n"
      "  \"field_entry_events\": %" PRIu64 ",\n"
      "  \"unique_field_entry_targets\": %" PRIu64 ",\n"
      "  \"emitted_seeds\": %" PRIu64 ",\n"
      "  \"empty_lookups\": %" PRIu64 ",\n"
      "  \"tag_mismatches\": %" PRIu64 ",\n"
      "  \"invalid_continuations\": %" PRIu64 ",\n"
      "  \"age_suppressed\": %" PRIu64 ",\n"
      "  \"donor_suppressed\": %" PRIu64 ",\n"
      "  \"context_verification_failures\": %" PRIu64 ",\n"
      "  \"active_lookups\": %" PRIu64 ",\n"
      "  \"terminal_rolling_hash\": \"%016" PRIx64 "\",\n"
      "  \"terminal_anchor_table_hash\": \"%016" PRIx64 "\",\n"
      "  \"terminal_anchor_transition_hash\": \"%016" PRIx64 "\",\n"
      "  \"lookup_before_truth\": true,\n"
      "  \"control_outcomes_feed_state\": false,\n"
      "  \"archive_authority\": false,\n"
      "  \"score_credit_bytes\": 0\n"
      "}\n",
      config.mode, wrt_bytes, config.key_bytes, kHashBase,
      config.hash_power(), config.table_bits, config.table_entries(),
      config.minimum_age, config.donor_bytes, values.field_entry_events,
      values.unique_field_entry_targets, values.emitted_seeds, values.empty,
      values.tag_mismatch, values.invalid, values.age_suppressed,
      values.donor_suppressed, values.context_verify_fail, values.active,
      observer.rolling_hash(), observer.anchor_hash(), values.transition);
  CloseJson(output);
}

}  // namespace

int main(int argc, char** argv) {
  if (argc == 3 && std::string(argv[1]) == "--describe-production") {
    DescribeProduction(argv[2]);
    return 0;
  }
  if (argc != 6 || std::string(argv[1]) != "--fixture") {
    std::fprintf(
        stderr,
        "usage: %s --fixture WRT GSRT2 RAW_OUTPUT SUMMARY_JSON\n"
        "       %s --describe-production OUTPUT_JSON\n",
        argv[0], argv[0]);
    return 64;
  }
  const Config config{};
  Mapping wrt(argv[2], "open fixture WRT");
  Mapping route(argv[3], "open fixture GSRT2");
  Tape tape(route, wrt.bytes());
  RawWriter output(argv[4]);
  Observer observer(config, wrt, tape, &output);
  observer.Run();
  WriteSummary(argv[5], config, observer, wrt.bytes());
  return 0;
}
