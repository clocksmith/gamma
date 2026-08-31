#include <algorithm>
#include <array>
#include <cerrno>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <optional>
#include <string>
#include <sys/stat.h>
#include <unordered_map>
#include <utility>
#include <vector>
#include <unistd.h>

namespace {

constexpr uint64_t kFullStoreBytes = 647798597ULL;
constexpr uint64_t kFullWrtBytes = 647798592ULL;
constexpr uint64_t kFullRawBytes = 1000000000ULL;
constexpr uint64_t kFullDictionaryBytes = 411996ULL;
constexpr uint64_t kStoreWrapperBytes = 5;
constexpr uint32_t kTapeHeaderBytes = 192;
constexpr uint32_t kTapeRecordBytes = 88;
constexpr uint32_t kSideHeaderBytes = 64;
constexpr uint32_t kSideRecordBytes = 232;
constexpr size_t kMaximumDepth = 16;
constexpr size_t kMaximumAtomBytes = 96;
constexpr uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr uint64_t kFnvPrime = 1099511628211ULL;
constexpr uint8_t kOpenByte = static_cast<uint8_t>('P');
constexpr uint8_t kFieldByte = static_cast<uint8_t>('Q');
constexpr uint8_t kEqualByte = static_cast<uint8_t>('M');
constexpr uint8_t kCloseByte = static_cast<uint8_t>('R');

enum EventType : uint8_t {
  kTemplateEnter = 1,
  kExplicitFieldEntry = 2,
  kFieldValueByte = 3,
  kDeferredValueUpdate = 4,
  kFieldExit = 5,
  kPositionalFieldExitAudit = 6,
  kTemplateExit = 7,
  kOverflowEnter = 8,
  kOverflowExit = 9,
};

enum RecordFlag : uint8_t {
  kValidRoute = 1,
  kPredictive = 2,
  kUpdateOnly = 4,
  kExplicitKey = 8,
  kPositionalAudit = 16,
  kOverflow = 32,
  kDeferred = 64,
  kPosttruth = 128,
};

[[noreturn]] void Fail(const char* operation) {
  std::fprintf(stderr, "endpoint428-semantic-route-tape failure operation=%s errno=%d\n",
               operation, errno);
  std::exit(1);
}

uint64_t FnvByte(uint64_t hash, uint8_t value) {
  return (hash ^ value) * kFnvPrime;
}

uint64_t FnvU64(uint64_t hash, uint64_t value) {
  for (unsigned i = 0; i < 8; ++i) {
    hash = FnvByte(hash, static_cast<uint8_t>(value >> (8 * i)));
  }
  return hash;
}

uint64_t Mix64(uint64_t value) {
  value ^= value >> 30;
  value *= 0xbf58476d1ce4e5b9ULL;
  value ^= value >> 27;
  value *= 0x94d049bb133111ebULL;
  value ^= value >> 31;
  return value;
}

void PutU16(std::array<uint8_t, kSideRecordBytes>* out, size_t offset,
            uint16_t value) {
  (*out)[offset] = static_cast<uint8_t>(value);
  (*out)[offset + 1] = static_cast<uint8_t>(value >> 8);
}

template <size_t N>
void PutU32(std::array<uint8_t, N>* out, size_t offset, uint32_t value) {
  for (unsigned i = 0; i < 4; ++i) {
    (*out)[offset + i] = static_cast<uint8_t>(value >> (8 * i));
  }
}

template <size_t N>
void PutU64(std::array<uint8_t, N>* out, size_t offset, uint64_t value) {
  for (unsigned i = 0; i < 8; ++i) {
    (*out)[offset + i] = static_cast<uint8_t>(value >> (8 * i));
  }
}

void WriteAll(int fd, const uint8_t* data, size_t size) {
  while (size != 0) {
    const ssize_t written = write(fd, data, size);
    if (written < 0 && errno == EINTR) continue;
    if (written <= 0) Fail("write");
    data += written;
    size -= static_cast<size_t>(written);
  }
}

class ExclusiveOutput {
 public:
  explicit ExclusiveOutput(const char* path) {
    fd_ = open(path, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW,
               0600);
    if (fd_ < 0) Fail("open output");
  }

  ~ExclusiveOutput() {
    if (fd_ >= 0) close(fd_);
  }

  void Write(const uint8_t* data, size_t size) { WriteAll(fd_, data, size); }

  template <size_t N>
  void Write(const std::array<uint8_t, N>& data) {
    Write(data.data(), data.size());
  }

  void Rewrite(const uint8_t* data, size_t size, off_t offset) {
    size_t remaining = size;
    while (remaining != 0) {
      const ssize_t written = pwrite(fd_, data + (size - remaining), remaining,
                                     offset + static_cast<off_t>(size - remaining));
      if (written < 0 && errno == EINTR) continue;
      if (written <= 0) Fail("pwrite");
      remaining -= static_cast<size_t>(written);
    }
  }

  void Finish() {
    if (fsync(fd_) != 0) Fail("fsync output");
    if (close(fd_) != 0) Fail("close output");
    fd_ = -1;
  }

 private:
  int fd_ = -1;
};

struct Atom {
  std::array<uint8_t, kMaximumAtomBytes> bytes{};
  uint16_t size = 0;
  bool valid = true;

  void Clear() {
    bytes.fill(0);
    size = 0;
    valid = true;
  }

  void Append(uint8_t value) {
    if (!valid) return;
    if (size >= bytes.size()) {
      valid = false;
      return;
    }
    bytes[size++] = value;
  }
};

struct RouteId {
  uint64_t lo = 0;
  uint64_t hi = 0;

  bool operator==(const RouteId& other) const {
    return lo == other.lo && hi == other.hi;
  }
};

struct RouteIdHash {
  size_t operator()(const RouteId& id) const {
    return static_cast<size_t>(Mix64(id.lo ^ Mix64(id.hi)));
  }
};

struct Descriptor {
  Atom name{};
  Atom key{};
  RouteId route{};
  RouteId witness{};
};

RouteId HashDescriptor(const Atom& name, const Atom& key, uint64_t seed_a,
                       uint64_t seed_b) {
  uint64_t a = FnvU64(kFnvOffset ^ seed_a, name.size);
  uint64_t b = FnvU64(kFnvOffset ^ seed_b, name.size);
  for (size_t i = 0; i < name.size; ++i) {
    a = FnvByte(a, name.bytes[i]);
    b = FnvByte(b, name.bytes[i]);
  }
  a = FnvByte(a, 1);
  b = FnvByte(b, 1);
  a = FnvU64(a, key.size);
  b = FnvU64(b, key.size);
  for (size_t i = 0; i < key.size; ++i) {
    a = FnvByte(a, key.bytes[i]);
    b = FnvByte(b, key.bytes[i]);
  }
  a = Mix64(a);
  b = Mix64(b);
  if ((a | b) == 0) a = 1;
  return {a, b};
}

bool SameAtom(const Atom& a, const Atom& b) {
  return a.size == b.size && a.valid == b.valid &&
         std::memcmp(a.bytes.data(), b.bytes.data(), a.size) == 0;
}

bool SameDescriptor(const Descriptor& a, const Descriptor& b) {
  return SameAtom(a.name, b.name) && SameAtom(a.key, b.key);
}

struct RouteState {
  Descriptor descriptor{};
  uint64_t virtual_ordinal = 0;
};

struct Observation {
  uint64_t source = 0;
  uint64_t raw_before = 0;
  uint64_t raw_after = 0;
  uint8_t byte = 0;
};

struct Record {
  uint64_t source = 0;
  uint64_t availability = 0;
  uint64_t raw_before = 0;
  uint64_t raw_after = 0;
  RouteId route{};
  RouteId witness{};
  uint64_t virtual_ordinal = 0;
  uint32_t field_ordinal = 0;
  uint8_t event_type = 0;
  uint8_t flags = 0;
  uint8_t depth = 0;
  uint8_t key_identity = 0;
};

class TapeWriter {
 public:
  TapeWriter(const char* tape_path, const char* side_path, bool fixture,
             uint64_t store_bytes, uint64_t wrt_bytes, uint64_t raw_bytes,
             uint64_t dictionary_bytes)
      : tape_(tape_path), side_(side_path), fixture_(fixture),
        store_bytes_(store_bytes), wrt_bytes_(wrt_bytes), raw_bytes_(raw_bytes),
        dictionary_bytes_(dictionary_bytes) {
    std::array<uint8_t, kTapeHeaderBytes> tape_header{};
    std::array<uint8_t, kSideHeaderBytes> side_header{};
    tape_.Write(tape_header);
    side_.Write(side_header);
  }

  void WriteRecord(const Record& record) {
    if (record.event_type < 1 || record.event_type > 9) Fail("event type");
    if (record.availability < record.source ||
        record.availability > wrt_bytes_ ||
        record.availability > UINT64_MAX / 8) {
      Fail("record coordinate");
    }
    std::array<uint8_t, kTapeRecordBytes> bytes{};
    PutU64(&bytes, 0, record.source);
    PutU64(&bytes, 8, record.availability);
    PutU64(&bytes, 16, record.availability * 8);
    PutU64(&bytes, 24, record.raw_before);
    PutU64(&bytes, 32, record.raw_after);
    PutU64(&bytes, 40, record.route.lo);
    PutU64(&bytes, 48, record.route.hi);
    PutU64(&bytes, 56, record.witness.lo);
    PutU64(&bytes, 64, record.witness.hi);
    PutU64(&bytes, 72, record.virtual_ordinal);
    PutU32(&bytes, 80, record.field_ordinal);
    bytes[84] = record.event_type;
    bytes[85] = record.flags;
    bytes[86] = record.depth;
    bytes[87] = record.key_identity;
    tape_.Write(bytes);
    ++record_count_;
    ++event_counts_[record.event_type - 1];
    if (record.event_type == kDeferredValueUpdate) ++deferred_updates_;
    if ((record.flags & kPredictive) != 0 && record.key_identity == 2) {
      ++positional_predictive_events_;
    }
    parser_digest_ = FnvU64(parser_digest_, record.source);
    parser_digest_ = FnvU64(parser_digest_, record.availability);
    parser_digest_ = FnvU64(parser_digest_, record.route.lo);
    parser_digest_ = FnvU64(parser_digest_, record.route.hi);
    parser_digest_ = FnvU64(parser_digest_, record.virtual_ordinal);
    parser_digest_ = FnvByte(parser_digest_, record.event_type);
    parser_digest_ = FnvByte(parser_digest_, record.flags);
  }

  void WriteDescriptor(const Descriptor& descriptor) {
    std::array<uint8_t, kSideRecordBytes> bytes{};
    PutU64(&bytes, 0, descriptor.route.lo);
    PutU64(&bytes, 8, descriptor.route.hi);
    PutU64(&bytes, 16, descriptor.witness.lo);
    PutU64(&bytes, 24, descriptor.witness.hi);
    PutU16(&bytes, 32, descriptor.name.size);
    PutU16(&bytes, 34, descriptor.key.size);
    bytes[36] = 1;
    std::memcpy(bytes.data() + 40, descriptor.name.bytes.data(),
                descriptor.name.size);
    std::memcpy(bytes.data() + 136, descriptor.key.bytes.data(),
                descriptor.key.size);
    side_.Write(bytes);
    ++descriptor_count_;
  }

  void SetDigests(uint64_t raw_digest, uint64_t wrt_digest) {
    raw_digest_ = raw_digest;
    wrt_digest_ = wrt_digest;
  }

  void Finish() {
    std::array<uint8_t, kTapeHeaderBytes> tape_header{};
    const std::array<uint8_t, 8> tape_magic = {'G', 'S', 'R', 'T', '2', 0, 0, 0};
    std::copy(tape_magic.begin(), tape_magic.end(), tape_header.begin());
    PutU32(&tape_header, 8, 2);
    PutU32(&tape_header, 12, kTapeHeaderBytes);
    PutU32(&tape_header, 16, kTapeRecordBytes);
    PutU32(&tape_header, 20, fixture_ ? 1U : 0U);
    PutU64(&tape_header, 24, store_bytes_);
    PutU64(&tape_header, 32, wrt_bytes_);
    PutU64(&tape_header, 40, raw_bytes_);
    PutU64(&tape_header, 48, dictionary_bytes_);
    PutU64(&tape_header, 56, record_count_);
    PutU64(&tape_header, 64, descriptor_count_);
    for (size_t i = 0; i < event_counts_.size(); ++i) {
      PutU64(&tape_header, 72 + 8 * i, event_counts_[i]);
    }
    PutU64(&tape_header, 144, deferred_updates_);
    PutU64(&tape_header, 152, positional_predictive_events_);
    PutU64(&tape_header, 160, pretruth_violations_);
    PutU64(&tape_header, 168, parser_digest_);
    PutU64(&tape_header, 176, raw_digest_);
    PutU64(&tape_header, 184, wrt_digest_);
    tape_.Rewrite(tape_header.data(), tape_header.size(), 0);

    std::array<uint8_t, kSideHeaderBytes> side_header{};
    const std::array<uint8_t, 8> side_magic = {'G', 'S', 'R', 'D', '2', 0, 0, 0};
    std::copy(side_magic.begin(), side_magic.end(), side_header.begin());
    PutU32(&side_header, 8, 2);
    PutU32(&side_header, 12, kSideHeaderBytes);
    PutU32(&side_header, 16, kSideRecordBytes);
    PutU32(&side_header, 20, fixture_ ? 1U : 0U);
    PutU64(&side_header, 24, descriptor_count_);
    PutU64(&side_header, 32, parser_digest_);
    side_.Rewrite(side_header.data(), side_header.size(), 0);
    tape_.Finish();
    side_.Finish();
  }

  uint64_t record_count() const { return record_count_; }
  uint64_t descriptor_count() const { return descriptor_count_; }
  uint64_t deferred_updates() const { return deferred_updates_; }
  uint64_t positional_predictive_events() const {
    return positional_predictive_events_;
  }
  uint64_t pretruth_violations() const { return pretruth_violations_; }
  uint64_t parser_digest() const { return parser_digest_; }
  const std::array<uint64_t, 9>& event_counts() const { return event_counts_; }

 private:
  ExclusiveOutput tape_;
  ExclusiveOutput side_;
  bool fixture_ = false;
  uint64_t store_bytes_ = 0;
  uint64_t wrt_bytes_ = 0;
  uint64_t raw_bytes_ = 0;
  uint64_t dictionary_bytes_ = 0;
  uint64_t record_count_ = 0;
  uint64_t descriptor_count_ = 0;
  std::array<uint64_t, 9> event_counts_{};
  uint64_t deferred_updates_ = 0;
  uint64_t positional_predictive_events_ = 0;
  uint64_t pretruth_violations_ = 0;
  uint64_t parser_digest_ = kFnvOffset;
  uint64_t raw_digest_ = kFnvOffset;
  uint64_t wrt_digest_ = kFnvOffset;
};

class CoordinateDecoder {
 public:
  CoordinateDecoder(FILE* dictionary, FILE* raw) : raw_(raw) {
    LoadDictionary(dictionary);
  }

  std::pair<uint64_t, uint64_t> Consume(uint8_t stored, uint64_t coordinate) {
    const uint64_t before = raw_position_;
    wrt_digest_ = FnvByte(wrt_digest_, stored);
    if (coordinate < 5) {
      if (coordinate == 0 && stored != 7) Fail("fixture WRT type");
      if (coordinate > 0) raw_length_header_ =
          (raw_length_header_ << 8) | static_cast<uint64_t>(stored);
    } else if (coordinate == 5) {
      if (stored != 7) Fail("WRT enabled marker");
    } else {
      DecodeStored(stored);
    }
    return {before, raw_position_};
  }

  void Finish(uint64_t expected_raw_bytes) {
    if (pending_escape_ || code_needed_ != 0) Fail("incomplete WRT code");
    if (raw_length_header_ != expected_raw_bytes ||
        raw_position_ != expected_raw_bytes) {
      errno = EINVAL;
      Fail("raw length identity");
    }
    if (getc(raw_) != EOF) Fail("raw trailing bytes");
  }

  uint64_t raw_position() const { return raw_position_; }
  uint64_t raw_digest() const { return raw_digest_; }
  uint64_t wrt_digest() const { return wrt_digest_; }

 private:
  static uint8_t UndoRemap(uint8_t c) {
    if (c >= static_cast<uint8_t>('{') && c < 127) {
      c = static_cast<uint8_t>(c + static_cast<int>('P') - static_cast<int>('{'));
    } else if (c >= static_cast<uint8_t>('P') && c < static_cast<uint8_t>('T')) {
      c = static_cast<uint8_t>(c - static_cast<int>('P') + static_cast<int>('{'));
    } else if ((c >= static_cast<uint8_t>(':') && c <= static_cast<uint8_t>('?')) ||
               (c >= static_cast<uint8_t>('J') && c <= static_cast<uint8_t>('O'))) {
      c ^= 0x70;
    }
    if (c == static_cast<uint8_t>('X') || c == static_cast<uint8_t>('`')) {
      c ^= static_cast<uint8_t>('X' ^ '`');
    }
    return c;
  }

  void LoadDictionary(FILE* dictionary) {
    std::string word;
    uint32_t line = 0;
    for (;;) {
      const int value = getc(dictionary);
      if (value == EOF) break;
      const uint8_t c = static_cast<uint8_t>(value);
      if (c >= 'a' && c <= 'z') {
        word.push_back(static_cast<char>(c));
        continue;
      }
      if (word.empty()) continue;
      uint32_t code = 0;
      if (line < 80) {
        code = 0x80U + line;
      } else if (line < 3920) {
        code = 0xD0U + ((line - 80) / 80);
        code += (0x80U + ((line - 80) % 80)) << 8;
      } else if (line < 44880) {
        code = 0xF0U + (((line - 3920) / 80) / 32);
        code += (0xD0U + (((line - 3920) / 80) % 32)) << 8;
        code += (0x80U + ((line - 3920) % 80)) << 16;
      } else {
        Fail("dictionary line bound");
      }
      reverse_[code] = word;
      ++line;
      word.clear();
    }
  }

  void Emit(uint8_t byte) {
    const int expected = getc(raw_);
    if (expected == EOF || static_cast<uint8_t>(expected) != byte) {
      std::fprintf(stderr,
                   "raw divergence raw=%" PRIu64 " expected=%d observed=%u\n",
                   raw_position_, expected, static_cast<unsigned>(byte));
      errno = EILSEQ;
      Fail("raw byte identity");
    }
    raw_digest_ = FnvByte(raw_digest_, byte);
    ++raw_position_;
  }

  void EmitWord(uint32_t code) {
    const auto found = reverse_.find(code);
    if (found == reverse_.end()) Fail("unknown dictionary code");
    std::string word = found->second;
    for (size_t i = 0; i < word.size(); ++i) {
      uint8_t c = static_cast<uint8_t>(word[i]);
      if (i == 0 && capitalized_) {
        c = static_cast<uint8_t>(c - 'a' + 'A');
        capitalized_ = false;
      }
      if (uppercase_) c = static_cast<uint8_t>(c - 'a' + 'A');
      Emit(c);
    }
  }

  void DecodeStored(uint8_t stored) {
    const uint8_t c = UndoRemap(stored);
    if (pending_escape_) {
      uppercase_ = false;
      pending_escape_ = false;
      Emit(c);
      return;
    }
    if (code_needed_ != 0) {
      code_ += static_cast<uint32_t>(c) << (8 * code_bytes_);
      ++code_bytes_;
      --code_needed_;
      if (code_bytes_ == 2 && c > 0xCF) ++code_needed_;
      if (code_needed_ == 0) {
        EmitWord(code_);
        code_ = 0;
        code_bytes_ = 0;
      }
      return;
    }
    if (c == 0x0C) {
      pending_escape_ = true;
    } else if (c == 0x07) {
      uppercase_ = true;
    } else if (c == 0x40) {
      capitalized_ = true;
    } else if (c == 0x06) {
      uppercase_ = false;
    } else if (c >= 0x80) {
      code_ = c;
      code_bytes_ = 1;
      code_needed_ = c > 0xCF ? 1 : 0;
      if (code_needed_ == 0) EmitWord(code_);
      if (code_needed_ == 0) {
        code_ = 0;
        code_bytes_ = 0;
      }
    } else {
      uint8_t literal = c;
      const bool alpha = (literal >= 'a' && literal <= 'z') ||
                         (literal >= 'A' && literal <= 'Z');
      if (!alpha) uppercase_ = false;
      if (capitalized_ || uppercase_) {
        literal = static_cast<uint8_t>(literal - 'a' + 'A');
      }
      if (capitalized_) capitalized_ = false;
      Emit(literal);
    }
  }

  FILE* raw_ = nullptr;
  std::unordered_map<uint32_t, std::string> reverse_{};
  uint64_t raw_length_header_ = 0;
  uint64_t raw_position_ = 0;
  uint64_t raw_digest_ = kFnvOffset;
  uint64_t wrt_digest_ = kFnvOffset;
  bool uppercase_ = false;
  bool capitalized_ = false;
  bool pending_escape_ = false;
  uint32_t code_ = 0;
  unsigned code_bytes_ = 0;
  unsigned code_needed_ = 0;
};

enum class Phase : uint8_t { kName, kFieldKey, kFieldValue };

struct Frame {
  Phase phase = Phase::kName;
  Atom name{};
  Atom token{};
  uint32_t field_ordinal = 0;
  bool usable = true;
  bool route_valid = false;
  RouteId route{};
  RouteId witness{};
};

struct Pending {
  bool valid = false;
  Observation observation{};
};

class RouteParser {
 public:
  explicit RouteParser(TapeWriter* writer) : writer_(writer) {}

  std::optional<Record> PreparePretruth(const Observation& observation) {
    if (depth_ == 0 || overflow_depth_ != 0) return std::nullopt;
    Frame& frame = frames_[depth_ - 1];
    if (frame.phase != Phase::kFieldValue || !frame.route_valid) {
      return std::nullopt;
    }
    RouteState& state = State(frame.route);
    Record record = RouteRecord(frame, observation, observation.source,
                                kFieldValueByte,
                                kValidRoute | kPredictive | kExplicitKey, 1);
    record.virtual_ordinal = state.virtual_ordinal;
    return record;
  }

  void Posttruth(const Observation& observation) {
    if (pending_.valid) {
      if (pending_.observation.byte == kOpenByte &&
          observation.byte == kOpenByte) {
        pending_.valid = false;
        OpenTemplate(observation);
        return;
      }
      if (pending_.observation.byte == kCloseByte &&
          observation.byte == kCloseByte) {
        pending_.valid = false;
        CloseTemplate(observation);
        return;
      }
      ConsumeLiteral(pending_.observation, observation.source + 1, true);
      pending_.valid = false;
    }
    if (observation.byte == kOpenByte || observation.byte == kCloseByte) {
      pending_.valid = true;
      pending_.observation = observation;
      return;
    }
    ConsumeLiteral(observation, observation.source + 1, false);
  }

  void Finish(uint64_t wrt_bytes) {
    if (pending_.valid) {
      ConsumeLiteral(pending_.observation, wrt_bytes, true);
      pending_.valid = false;
    }
  }

 private:
  RouteState& State(const RouteId& id) {
    const auto found = routes_.find(id);
    if (found == routes_.end()) Fail("missing route state");
    return found->second;
  }

  Record RouteRecord(const Frame& frame, const Observation& source,
                     uint64_t availability, uint8_t event_type, uint8_t flags,
                     uint8_t key_identity) const {
    Record record{};
    record.source = source.source;
    record.availability = availability;
    record.raw_before = source.raw_before;
    record.raw_after = source.raw_after;
    record.route = frame.route;
    record.witness = frame.witness;
    record.field_ordinal = frame.field_ordinal;
    record.event_type = event_type;
    record.flags = flags;
    record.depth = static_cast<uint8_t>(depth_);
    record.key_identity = key_identity;
    return record;
  }

  Record PlainRecord(const Observation& source, uint64_t availability,
                     uint8_t event_type, uint8_t flags) const {
    Record record{};
    record.source = source.source;
    record.availability = availability;
    record.raw_before = source.raw_before;
    record.raw_after = source.raw_after;
    record.event_type = event_type;
    record.flags = flags;
    record.depth = static_cast<uint8_t>(depth_);
    return record;
  }

  void OpenTemplate(const Observation& source) {
    if (overflow_depth_ != 0) {
      ++overflow_depth_;
      writer_->WriteRecord(PlainRecord(source, source.source + 1,
                                       kOverflowEnter,
                                       kOverflow | kPosttruth));
      return;
    }
    if (depth_ >= frames_.size()) {
      overflow_depth_ = 1;
      writer_->WriteRecord(PlainRecord(source, source.source + 1,
                                       kOverflowEnter,
                                       kOverflow | kPosttruth));
      return;
    }
    if (depth_ != 0) {
      Frame& parent = frames_[depth_ - 1];
      if (parent.phase == Phase::kName) {
        parent.name.valid = false;
        parent.usable = false;
      } else if (parent.phase == Phase::kFieldKey) {
        parent.token.valid = false;
      }
    }
    frames_[depth_] = Frame{};
    ++depth_;
    writer_->WriteRecord(PlainRecord(source, source.source + 1,
                                     kTemplateEnter, kPosttruth));
  }

  void EmitFieldExit(Frame& frame, const Observation& source,
                     uint64_t availability) {
    if (frame.phase == Phase::kFieldValue && frame.route_valid) {
      Record record = RouteRecord(frame, source, availability, kFieldExit,
                                  kValidRoute | kExplicitKey | kPosttruth, 1);
      record.virtual_ordinal = State(frame.route).virtual_ordinal;
      writer_->WriteRecord(record);
      frame.route_valid = false;
    } else if (frame.phase == Phase::kFieldKey && frame.token.size != 0) {
      Record record = PlainRecord(source, availability,
                                  kPositionalFieldExitAudit,
                                  kPositionalAudit | kPosttruth);
      record.field_ordinal = frame.field_ordinal;
      record.key_identity = 2;
      writer_->WriteRecord(record);
    }
  }

  void CloseTemplate(const Observation& source) {
    if (overflow_depth_ != 0) {
      --overflow_depth_;
      writer_->WriteRecord(PlainRecord(source, source.source + 1,
                                       kOverflowExit,
                                       kOverflow | kPosttruth));
      return;
    }
    if (depth_ == 0) return;
    Frame& frame = frames_[depth_ - 1];
    EmitFieldExit(frame, source, source.source + 1);
    writer_->WriteRecord(PlainRecord(source, source.source + 1,
                                     kTemplateExit, kPosttruth));
    --depth_;
  }

  void ActivateExplicitRoute(Frame& frame, const Observation& source,
                             uint64_t availability) {
    if (!frame.usable || !frame.name.valid || frame.name.size == 0 ||
        !frame.token.valid || frame.token.size == 0) {
      frame.route_valid = false;
      return;
    }
    Descriptor descriptor{};
    descriptor.name = frame.name;
    descriptor.key = frame.token;
    descriptor.route = HashDescriptor(descriptor.name, descriptor.key,
                                      0x5254554c455f3031ULL,
                                      0x5254554c455f3032ULL);
    descriptor.witness = HashDescriptor(descriptor.name, descriptor.key,
                                        0x5749544e45535331ULL,
                                        0x5749544e45535332ULL);
    auto inserted = routes_.emplace(descriptor.route,
                                    RouteState{descriptor, 0});
    if (!inserted.second &&
        !SameDescriptor(inserted.first->second.descriptor, descriptor)) {
      Fail("route fingerprint alias");
    }
    auto witness = witnesses_.emplace(descriptor.witness, descriptor.route);
    if (!witness.second && !(witness.first->second == descriptor.route)) {
      Fail("descriptor witness alias");
    }
    if (inserted.second) writer_->WriteDescriptor(descriptor);
    frame.route = descriptor.route;
    frame.witness = descriptor.witness;
    frame.route_valid = true;
    Record record = RouteRecord(frame, source, availability,
                                kExplicitFieldEntry,
                                kValidRoute | kExplicitKey | kPosttruth, 1);
    record.virtual_ordinal = inserted.first->second.virtual_ordinal;
    writer_->WriteRecord(record);
  }

  void AppendRoute(Frame& frame, const Observation& source,
                   uint64_t availability, bool deferred) {
    if (!frame.route_valid) return;
    RouteState& state = State(frame.route);
    if (deferred) {
      Record record = RouteRecord(frame, source, availability,
                                  kDeferredValueUpdate,
                                  kValidRoute | kUpdateOnly | kExplicitKey |
                                      kDeferred,
                                  1);
      record.virtual_ordinal = state.virtual_ordinal;
      writer_->WriteRecord(record);
    }
    ++state.virtual_ordinal;
  }

  void ConsumeLiteral(const Observation& source, uint64_t availability,
                      bool deferred) {
    if (overflow_depth_ != 0 || depth_ == 0) return;
    Frame& frame = frames_[depth_ - 1];
    if (frame.phase == Phase::kName) {
      if (source.byte == kFieldByte) {
        if (!frame.name.valid || frame.name.size == 0) frame.usable = false;
        frame.phase = Phase::kFieldKey;
        frame.token.Clear();
        frame.field_ordinal = 0;
      } else {
        frame.name.Append(source.byte);
      }
      return;
    }
    if (frame.phase == Phase::kFieldKey) {
      if (source.byte == kEqualByte) {
        ActivateExplicitRoute(frame, source, availability);
        frame.phase = Phase::kFieldValue;
      } else if (source.byte == kFieldByte) {
        EmitFieldExit(frame, source, availability);
        ++frame.field_ordinal;
        frame.token.Clear();
      } else {
        frame.token.Append(source.byte);
      }
      return;
    }
    if (source.byte == kFieldByte) {
      EmitFieldExit(frame, source, availability);
      ++frame.field_ordinal;
      frame.phase = Phase::kFieldKey;
      frame.token.Clear();
      return;
    }
    AppendRoute(frame, source, availability, deferred);
  }

  TapeWriter* writer_ = nullptr;
  std::array<Frame, kMaximumDepth> frames_{};
  size_t depth_ = 0;
  size_t overflow_depth_ = 0;
  Pending pending_{};
  std::unordered_map<RouteId, RouteState, RouteIdHash> routes_{};
  std::unordered_map<RouteId, RouteId, RouteIdHash> witnesses_{};
};

uint64_t FileSize(const char* path) {
  struct stat metadata = {};
  if (stat(path, &metadata) != 0 || !S_ISREG(metadata.st_mode) ||
      metadata.st_size < 0) {
    Fail("input geometry");
  }
  return static_cast<uint64_t>(metadata.st_size);
}

FILE* OpenInput(const char* path) {
  FILE* stream = fopen(path, "rb");
  if (stream == nullptr) Fail("open input");
  return stream;
}

void WriteSummary(const char* path, bool fixture, uint64_t store_bytes,
                  uint64_t wrt_bytes, uint64_t raw_bytes,
                  uint64_t dictionary_bytes, const TapeWriter& writer,
                  const CoordinateDecoder& decoder) {
  const int fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW,
                      0600);
  if (fd < 0) Fail("open summary");
  const auto& events = writer.event_counts();
  char buffer[4096];
  const int length = std::snprintf(
      buffer, sizeof(buffer),
      "{\n"
      "  \"schema\": \"gamma.enwiki9.endpoint428-semantic-route-tape-summary.v2\",\n"
      "  \"candidate_id\": \"endpoint428_semantic_route_tape_q0_v2\",\n"
      "  \"fixture\": %s,\n"
      "  \"store_bytes\": %" PRIu64 ",\n"
      "  \"wrt_stream_bytes\": %" PRIu64 ",\n"
      "  \"reconstructed_raw_bytes\": %" PRIu64 ",\n"
      "  \"dictionary_bytes\": %" PRIu64 ",\n"
      "  \"record_bytes\": %u,\n"
      "  \"record_count\": %" PRIu64 ",\n"
      "  \"descriptor_count\": %" PRIu64 ",\n"
      "  \"event_counts\": [%" PRIu64 ", %" PRIu64 ", %" PRIu64
      ", %" PRIu64 ", %" PRIu64 ", %" PRIu64 ", %" PRIu64
      ", %" PRIu64 ", %" PRIu64 "],\n"
      "  \"deferred_update_events\": %" PRIu64 ",\n"
      "  \"positional_predictive_events\": %" PRIu64 ",\n"
      "  \"pretruth_eligibility_violations\": %" PRIu64 ",\n"
      "  \"parser_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"raw_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"wrt_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"archive_authority\": false,\n"
      "  \"score_credit_bytes\": 0\n"
      "}\n",
      fixture ? "true" : "false", store_bytes, wrt_bytes, raw_bytes,
      dictionary_bytes, kTapeRecordBytes, writer.record_count(),
      writer.descriptor_count(), events[0], events[1], events[2], events[3],
      events[4], events[5], events[6], events[7], events[8],
      writer.deferred_updates(), writer.positional_predictive_events(),
      writer.pretruth_violations(), writer.parser_digest(), decoder.raw_digest(),
      decoder.wrt_digest());
  if (length < 0 || static_cast<size_t>(length) >= sizeof(buffer)) {
    close(fd);
    Fail("format summary");
  }
  WriteAll(fd, reinterpret_cast<const uint8_t*>(buffer),
           static_cast<size_t>(length));
  if (fsync(fd) != 0 || close(fd) != 0) Fail("close summary");
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 7 && argc != 8) {
    std::fprintf(stderr,
                 "usage: %s STORE RAW DICTIONARY TAPE SIDECAR SUMMARY [--fixture]\n",
                 argv[0]);
    return 64;
  }
  const bool fixture = argc == 8 && std::strcmp(argv[7], "--fixture") == 0;
  if (argc == 8 && !fixture) return 64;
  const uint64_t store_bytes = FileSize(argv[1]);
  const uint64_t raw_bytes = FileSize(argv[2]);
  const uint64_t dictionary_bytes = FileSize(argv[3]);
  if (store_bytes < kStoreWrapperBytes + 6) Fail("store too short");
  const uint64_t wrt_bytes = store_bytes - kStoreWrapperBytes;
  if (!fixture && (store_bytes != kFullStoreBytes || wrt_bytes != kFullWrtBytes ||
                   raw_bytes != kFullRawBytes ||
                   dictionary_bytes != kFullDictionaryBytes)) {
    errno = EINVAL;
    Fail("full input geometry");
  }

  FILE* store = OpenInput(argv[1]);
  FILE* raw = OpenInput(argv[2]);
  FILE* dictionary = OpenInput(argv[3]);
  const std::array<uint8_t, 5> expected_wrapper = {0x80, 0, 0, 0, 0};
  for (uint8_t expected : expected_wrapper) {
    const int actual = getc(store);
    if (actual == EOF || static_cast<uint8_t>(actual) != expected) {
      Fail("store wrapper");
    }
  }

  CoordinateDecoder decoder(dictionary, raw);
  TapeWriter writer(argv[4], argv[5], fixture, store_bytes, wrt_bytes,
                    raw_bytes, dictionary_bytes);
  RouteParser parser(&writer);
  for (uint64_t coordinate = 0; coordinate < wrt_bytes; ++coordinate) {
    Observation observation{};
    observation.source = coordinate;
    observation.raw_before = decoder.raw_position();
    std::optional<Record> predictive = parser.PreparePretruth(observation);
    const int value = getc(store);
    if (value == EOF) Fail("short store");
    observation.byte = static_cast<uint8_t>(value);
    const auto raw_span = decoder.Consume(observation.byte, coordinate);
    observation.raw_before = raw_span.first;
    observation.raw_after = raw_span.second;
    if (predictive.has_value()) {
      predictive->raw_before = raw_span.first;
      predictive->raw_after = raw_span.second;
      writer.WriteRecord(*predictive);
    }
    parser.Posttruth(observation);
  }
  if (getc(store) != EOF) Fail("trailing store");
  decoder.Finish(raw_bytes);
  parser.Finish(wrt_bytes);
  writer.SetDigests(decoder.raw_digest(), decoder.wrt_digest());
  writer.Finish();
  WriteSummary(argv[6], fixture, store_bytes, wrt_bytes, raw_bytes,
               dictionary_bytes, writer, decoder);
  if (fclose(dictionary) != 0 || fclose(raw) != 0 || fclose(store) != 0) {
    Fail("close input");
  }
  return 0;
}
