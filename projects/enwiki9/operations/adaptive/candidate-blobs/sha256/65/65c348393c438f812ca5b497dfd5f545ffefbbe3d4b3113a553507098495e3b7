#include <algorithm>
#include <array>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <optional>
#include <string>
#include <sys/stat.h>
#include <unordered_map>

namespace {

constexpr uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr uint64_t kFnvPrime = 1099511628211ULL;
constexpr size_t kTapeHeaderBytes = 192;
constexpr size_t kTapeRecordBytes = 88;
constexpr size_t kSideHeaderBytes = 64;
constexpr size_t kSideRecordBytes = 232;
constexpr size_t kMaximumDepth = 16;
constexpr size_t kMaximumAtomBytes = 96;
constexpr uint8_t kOpen = 'P';
constexpr uint8_t kField = 'Q';
constexpr uint8_t kEqual = 'M';
constexpr uint8_t kClose = 'R';

enum Event : uint8_t {
  kTemplateEnter = 1,
  kExplicitEntry = 2,
  kValuePrediction = 3,
  kDeferredUpdate = 4,
  kFieldExit = 5,
  kPositionalExit = 6,
  kTemplateExit = 7,
  kOverflowEnter = 8,
  kOverflowExit = 9,
};

enum Flag : uint8_t {
  kValid = 1,
  kPredictive = 2,
  kUpdateOnly = 4,
  kExplicit = 8,
  kPositional = 16,
  kOverflow = 32,
  kDeferred = 64,
  kPosttruth = 128,
};

[[noreturn]] void Die(const std::string& message) {
  std::fprintf(stderr, "semantic replay failure: %s\n", message.c_str());
  std::exit(1);
}

uint64_t U64(const uint8_t* bytes) {
  uint64_t value = 0;
  for (unsigned i = 0; i < 8; ++i) value |= uint64_t(bytes[i]) << (8 * i);
  return value;
}

uint32_t U32(const uint8_t* bytes) {
  uint32_t value = 0;
  for (unsigned i = 0; i < 4; ++i) value |= uint32_t(bytes[i]) << (8 * i);
  return value;
}

template <size_t N>
void PutU64(std::array<uint8_t, N>* bytes, size_t offset, uint64_t value) {
  for (unsigned i = 0; i < 8; ++i) (*bytes)[offset + i] = uint8_t(value >> (8 * i));
}

template <size_t N>
void PutU32(std::array<uint8_t, N>* bytes, size_t offset, uint32_t value) {
  for (unsigned i = 0; i < 4; ++i) (*bytes)[offset + i] = uint8_t(value >> (8 * i));
}

void PutU16(std::array<uint8_t, kSideRecordBytes>* bytes, size_t offset,
            uint16_t value) {
  (*bytes)[offset] = uint8_t(value);
  (*bytes)[offset + 1] = uint8_t(value >> 8);
}

uint64_t FileSize(const char* path) {
  struct stat metadata = {};
  if (stat(path, &metadata) != 0 || !S_ISREG(metadata.st_mode) || metadata.st_size < 0) {
    Die(std::string("bad input geometry: ") + path);
  }
  return uint64_t(metadata.st_size);
}

FILE* Open(const char* path) {
  FILE* stream = std::fopen(path, "rb");
  if (stream == nullptr) Die(std::string("cannot open: ") + path);
  return stream;
}

void ReadExact(FILE* stream, uint8_t* bytes, size_t count, const char* label) {
  if (std::fread(bytes, 1, count, stream) != count) Die(std::string("short ") + label);
}

uint64_t FnvByte(uint64_t value, uint8_t byte) {
  return (value ^ byte) * kFnvPrime;
}

uint64_t FnvU64(uint64_t value, uint64_t item) {
  for (unsigned i = 0; i < 8; ++i) value = FnvByte(value, uint8_t(item >> (8 * i)));
  return value;
}

uint64_t Mix(uint64_t value) {
  value ^= value >> 30;
  value *= 0xbf58476d1ce4e5b9ULL;
  value ^= value >> 27;
  value *= 0x94d049bb133111ebULL;
  value ^= value >> 31;
  return value;
}

struct Id {
  uint64_t lo = 0;
  uint64_t hi = 0;
  bool operator==(const Id& other) const { return lo == other.lo && hi == other.hi; }
};

struct IdHash {
  size_t operator()(const Id& id) const { return size_t(Mix(id.lo ^ Mix(id.hi))); }
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
  void Add(uint8_t byte) {
    if (!valid) return;
    if (size == bytes.size()) {
      valid = false;
      return;
    }
    bytes[size++] = byte;
  }
};

bool Same(const Atom& left, const Atom& right) {
  return left.valid == right.valid && left.size == right.size &&
         std::memcmp(left.bytes.data(), right.bytes.data(), left.size) == 0;
}

Id DescriptorHash(const Atom& name, const Atom& key, uint64_t seed0, uint64_t seed1) {
  uint64_t lo = FnvU64(kFnvOffset ^ seed0, name.size);
  uint64_t hi = FnvU64(kFnvOffset ^ seed1, name.size);
  for (size_t i = 0; i < name.size; ++i) {
    lo = FnvByte(lo, name.bytes[i]);
    hi = FnvByte(hi, name.bytes[i]);
  }
  lo = FnvByte(lo, 1);
  hi = FnvByte(hi, 1);
  lo = FnvU64(lo, key.size);
  hi = FnvU64(hi, key.size);
  for (size_t i = 0; i < key.size; ++i) {
    lo = FnvByte(lo, key.bytes[i]);
    hi = FnvByte(hi, key.bytes[i]);
  }
  lo = Mix(lo);
  hi = Mix(hi);
  if ((lo | hi) == 0) lo = 1;
  return {lo, hi};
}

struct Descriptor {
  Atom name{};
  Atom key{};
  Id route{};
  Id witness{};
};

struct Record {
  uint64_t source = 0;
  uint64_t availability = 0;
  uint64_t raw_before = 0;
  uint64_t raw_after = 0;
  Id route{};
  Id witness{};
  uint64_t ordinal = 0;
  uint32_t field = 0;
  uint8_t event = 0;
  uint8_t flags = 0;
  uint8_t depth = 0;
  uint8_t key_identity = 0;
};

class ArtifactReader {
 public:
  ArtifactReader(const char* tape_path, const char* side_path, uint64_t store_bytes,
                 uint64_t wrt_bytes, uint64_t raw_bytes, uint64_t dictionary_bytes)
      : tape_(Open(tape_path)), side_(Open(side_path)) {
    std::array<uint8_t, kTapeHeaderBytes> tape_header{};
    ReadExact(tape_, tape_header.data(), tape_header.size(), "tape header");
    if (std::memcmp(tape_header.data(), "GSRT2\0\0\0", 8) != 0 ||
        U32(tape_header.data() + 8) != 2 || U32(tape_header.data() + 12) != 192 ||
        U32(tape_header.data() + 16) != 88 ||
        (U32(tape_header.data() + 20) & ~1U) != 0) {
      Die("tape header ABI");
    }
    fixture_ = (U32(tape_header.data() + 20) & 1U) != 0;
    if (U64(tape_header.data() + 24) != store_bytes ||
        U64(tape_header.data() + 32) != wrt_bytes ||
        U64(tape_header.data() + 40) != raw_bytes ||
        U64(tape_header.data() + 48) != dictionary_bytes) {
      Die("tape input geometry");
    }
    record_limit_ = U64(tape_header.data() + 56);
    descriptor_limit_ = U64(tape_header.data() + 64);
    for (size_t i = 0; i < 9; ++i) expected_events_[i] = U64(tape_header.data() + 72 + i * 8);
    expected_deferred_ = U64(tape_header.data() + 144);
    if (U64(tape_header.data() + 152) != 0 || U64(tape_header.data() + 160) != 0) {
      Die("tape forbidden violation counters");
    }
    expected_parser_digest_ = U64(tape_header.data() + 168);
    expected_raw_digest_ = U64(tape_header.data() + 176);
    expected_wrt_digest_ = U64(tape_header.data() + 184);
    if (FileSize(tape_path) != kTapeHeaderBytes + kTapeRecordBytes * record_limit_) {
      Die("tape file size");
    }

    std::array<uint8_t, kSideHeaderBytes> side_header{};
    ReadExact(side_, side_header.data(), side_header.size(), "side header");
    if (std::memcmp(side_header.data(), "GSRD2\0\0\0", 8) != 0 ||
        U32(side_header.data() + 8) != 2 || U32(side_header.data() + 12) != 64 ||
        U32(side_header.data() + 16) != 232 ||
        U32(side_header.data() + 20) != (fixture_ ? 1U : 0U) ||
        U64(side_header.data() + 24) != descriptor_limit_ ||
        U64(side_header.data() + 32) != expected_parser_digest_) {
      Die("side header ABI");
    }
    for (size_t i = 40; i < side_header.size(); ++i) {
      if (side_header[i] != 0) Die("side header reserved bytes");
    }
    if (FileSize(side_path) != kSideHeaderBytes + kSideRecordBytes * descriptor_limit_) {
      Die("side file size");
    }
  }

  ~ArtifactReader() {
    if (tape_ != nullptr) std::fclose(tape_);
    if (side_ != nullptr) std::fclose(side_);
  }

  void Expect(const Record& record) {
    if (record_count_ == record_limit_) Die("unexpected extra semantic record");
    std::array<uint8_t, kTapeRecordBytes> expected{};
    PutU64(&expected, 0, record.source);
    PutU64(&expected, 8, record.availability);
    PutU64(&expected, 16, record.availability * 8);
    PutU64(&expected, 24, record.raw_before);
    PutU64(&expected, 32, record.raw_after);
    PutU64(&expected, 40, record.route.lo);
    PutU64(&expected, 48, record.route.hi);
    PutU64(&expected, 56, record.witness.lo);
    PutU64(&expected, 64, record.witness.hi);
    PutU64(&expected, 72, record.ordinal);
    PutU32(&expected, 80, record.field);
    expected[84] = record.event;
    expected[85] = record.flags;
    expected[86] = record.depth;
    expected[87] = record.key_identity;
    std::array<uint8_t, kTapeRecordBytes> actual{};
    ReadExact(tape_, actual.data(), actual.size(), "tape record");
    if (actual != expected) {
      size_t byte = 0;
      while (byte < actual.size() && actual[byte] == expected[byte]) ++byte;
      Die("record " + std::to_string(record_count_) + " differs at ABI byte " +
          std::to_string(byte));
    }
    ++record_count_;
    ++events_[record.event - 1];
    if (record.event == kDeferredUpdate) ++deferred_;
    parser_digest_ = FnvU64(parser_digest_, record.source);
    parser_digest_ = FnvU64(parser_digest_, record.availability);
    parser_digest_ = FnvU64(parser_digest_, record.route.lo);
    parser_digest_ = FnvU64(parser_digest_, record.route.hi);
    parser_digest_ = FnvU64(parser_digest_, record.ordinal);
    parser_digest_ = FnvByte(parser_digest_, record.event);
    parser_digest_ = FnvByte(parser_digest_, record.flags);
  }

  void ExpectDescriptor(const Descriptor& descriptor) {
    if (descriptor_count_ == descriptor_limit_) Die("unexpected extra descriptor");
    std::array<uint8_t, kSideRecordBytes> expected{};
    PutU64(&expected, 0, descriptor.route.lo);
    PutU64(&expected, 8, descriptor.route.hi);
    PutU64(&expected, 16, descriptor.witness.lo);
    PutU64(&expected, 24, descriptor.witness.hi);
    PutU16(&expected, 32, descriptor.name.size);
    PutU16(&expected, 34, descriptor.key.size);
    expected[36] = 1;
    std::copy_n(descriptor.name.bytes.begin(), descriptor.name.size, expected.begin() + 40);
    std::copy_n(descriptor.key.bytes.begin(), descriptor.key.size, expected.begin() + 136);
    std::array<uint8_t, kSideRecordBytes> actual{};
    ReadExact(side_, actual.data(), actual.size(), "side record");
    if (actual != expected) Die("descriptor " + std::to_string(descriptor_count_) + " differs");
    ++descriptor_count_;
  }

  void Finish(uint64_t raw_digest, uint64_t wrt_digest) {
    if (record_count_ != record_limit_ || descriptor_count_ != descriptor_limit_) {
      Die("artifact count mismatch");
    }
    if (events_ != expected_events_ || deferred_ != expected_deferred_ ||
        parser_digest_ != expected_parser_digest_ || raw_digest != expected_raw_digest_ ||
        wrt_digest != expected_wrt_digest_) {
      Die("header aggregate mismatch");
    }
    if (std::getc(tape_) != EOF || std::getc(side_) != EOF) Die("artifact trailing byte");
  }

  uint64_t record_count() const { return record_count_; }
  uint64_t descriptor_count() const { return descriptor_count_; }
  bool fixture() const { return fixture_; }

 private:
  FILE* tape_ = nullptr;
  FILE* side_ = nullptr;
  bool fixture_ = false;
  uint64_t record_limit_ = 0;
  uint64_t descriptor_limit_ = 0;
  uint64_t record_count_ = 0;
  uint64_t descriptor_count_ = 0;
  std::array<uint64_t, 9> expected_events_{};
  std::array<uint64_t, 9> events_{};
  uint64_t expected_deferred_ = 0;
  uint64_t deferred_ = 0;
  uint64_t expected_parser_digest_ = 0;
  uint64_t expected_raw_digest_ = 0;
  uint64_t expected_wrt_digest_ = 0;
  uint64_t parser_digest_ = kFnvOffset;
};

class RawReplay {
 public:
  RawReplay(FILE* dictionary, FILE* raw) : raw_(raw) { Load(dictionary); }

  std::pair<uint64_t, uint64_t> Push(uint8_t stored, uint64_t coordinate) {
    const uint64_t before = raw_position_;
    wrt_digest_ = FnvByte(wrt_digest_, stored);
    if (coordinate < 5) {
      if (coordinate == 0 && stored != 7) Die("WRT type");
      if (coordinate != 0) raw_header_ = (raw_header_ << 8) | stored;
    } else if (coordinate == 5) {
      if (stored != 7) Die("WRT marker");
    } else {
      Decode(stored);
    }
    return {before, raw_position_};
  }

  void Finish(uint64_t expected) {
    if (escaped_ || need_ != 0 || raw_header_ != expected || raw_position_ != expected ||
        std::getc(raw_) != EOF) {
      Die("raw reconstruction terminal identity");
    }
  }

  uint64_t position() const { return raw_position_; }
  uint64_t raw_digest() const { return raw_digest_; }
  uint64_t wrt_digest() const { return wrt_digest_; }

 private:
  static uint8_t Unmap(uint8_t byte) {
    if (byte >= '{' && byte < 127) byte = uint8_t(byte + int('P') - int('{'));
    else if (byte >= 'P' && byte < 'T') byte = uint8_t(byte - int('P') + int('{'));
    else if ((byte >= ':' && byte <= '?') || (byte >= 'J' && byte <= 'O')) byte ^= 0x70;
    if (byte == 'X' || byte == '`') byte ^= uint8_t('X' ^ '`');
    return byte;
  }

  void Load(FILE* dictionary) {
    std::string word;
    uint32_t line = 0;
    for (;;) {
      const int item = std::getc(dictionary);
      if (item == EOF) break;
      const uint8_t byte = uint8_t(item);
      if (byte >= 'a' && byte <= 'z') {
        word.push_back(char(byte));
        continue;
      }
      if (word.empty()) continue;
      uint32_t code = 0;
      if (line < 80) code = 0x80U + line;
      else if (line < 3920) {
        code = 0xD0U + ((line - 80) / 80);
        code += (0x80U + ((line - 80) % 80)) << 8;
      } else if (line < 44880) {
        code = 0xF0U + (((line - 3920) / 80) / 32);
        code += (0xD0U + (((line - 3920) / 80) % 32)) << 8;
        code += (0x80U + ((line - 3920) % 80)) << 16;
      } else {
        Die("dictionary line bound");
      }
      if (!words_.emplace(code, word).second) Die("duplicate dictionary code");
      ++line;
      word.clear();
    }
  }

  void Emit(uint8_t byte) {
    const int expected = std::getc(raw_);
    if (expected == EOF || uint8_t(expected) != byte) {
      Die("raw divergence at " + std::to_string(raw_position_));
    }
    raw_digest_ = FnvByte(raw_digest_, byte);
    ++raw_position_;
  }

  void Word(uint32_t code) {
    const auto found = words_.find(code);
    if (found == words_.end()) Die("unknown dictionary code");
    for (size_t index = 0; index < found->second.size(); ++index) {
      uint8_t byte = uint8_t(found->second[index]);
      if (index == 0 && capital_) {
        byte = uint8_t(byte - 'a' + 'A');
        capital_ = false;
      }
      if (upper_) byte = uint8_t(byte - 'a' + 'A');
      Emit(byte);
    }
  }

  void Decode(uint8_t stored) {
    const uint8_t byte = Unmap(stored);
    if (escaped_) {
      upper_ = false;
      escaped_ = false;
      Emit(byte);
      return;
    }
    if (need_ != 0) {
      code_ += uint32_t(byte) << (8 * code_bytes_);
      ++code_bytes_;
      --need_;
      if (code_bytes_ == 2 && byte > 0xCF) ++need_;
      if (need_ == 0) {
        Word(code_);
        code_ = 0;
        code_bytes_ = 0;
      }
      return;
    }
    if (byte == 0x0C) escaped_ = true;
    else if (byte == 0x07) upper_ = true;
    else if (byte == 0x40) capital_ = true;
    else if (byte == 0x06) upper_ = false;
    else if (byte >= 0x80) {
      code_ = byte;
      code_bytes_ = 1;
      need_ = byte > 0xCF ? 1 : 0;
      if (need_ == 0) {
        Word(code_);
        code_ = 0;
        code_bytes_ = 0;
      }
    } else {
      uint8_t literal = byte;
      const bool alpha = (literal >= 'a' && literal <= 'z') ||
                         (literal >= 'A' && literal <= 'Z');
      if (!alpha) upper_ = false;
      if (capital_ || upper_) literal = uint8_t(literal - 'a' + 'A');
      if (capital_) capital_ = false;
      Emit(literal);
    }
  }

  FILE* raw_ = nullptr;
  std::unordered_map<uint32_t, std::string> words_{};
  uint64_t raw_header_ = 0;
  uint64_t raw_position_ = 0;
  uint64_t raw_digest_ = kFnvOffset;
  uint64_t wrt_digest_ = kFnvOffset;
  bool upper_ = false;
  bool capital_ = false;
  bool escaped_ = false;
  uint32_t code_ = 0;
  unsigned code_bytes_ = 0;
  unsigned need_ = 0;
};

enum class Phase : uint8_t { kName, kKey, kValue };

struct Frame {
  Phase phase = Phase::kName;
  Atom name{};
  Atom token{};
  uint32_t field = 0;
  bool usable = true;
  bool route_valid = false;
  Id route{};
  Id witness{};
};

struct SeenRoute {
  Descriptor descriptor{};
  uint64_t ordinal = 0;
};

struct Observation {
  uint64_t source = 0;
  uint64_t raw_before = 0;
  uint64_t raw_after = 0;
  uint8_t byte = 0;
};

class SemanticReplay {
 public:
  explicit SemanticReplay(ArtifactReader* artifacts) : artifacts_(artifacts) {}

  std::optional<Record> Prediction(const Observation& source) {
    if (depth_ == 0 || overflow_ != 0) return std::nullopt;
    Frame& frame = frames_[depth_ - 1];
    if (frame.phase != Phase::kValue || !frame.route_valid) return std::nullopt;
    Record result = Routed(frame, source, source.source, kValuePrediction,
                           kValid | kPredictive | kExplicit, 1);
    result.ordinal = Route(frame.route).ordinal;
    return result;
  }

  void Truth(const Observation& source) {
    if (pending_.has_value()) {
      if (pending_->byte == kOpen && source.byte == kOpen) {
        pending_.reset();
        OpenTemplate(source);
        return;
      }
      if (pending_->byte == kClose && source.byte == kClose) {
        pending_.reset();
        CloseTemplate(source);
        return;
      }
      Literal(*pending_, source.source + 1, true);
      pending_.reset();
    }
    if (source.byte == kOpen || source.byte == kClose) {
      pending_ = source;
      return;
    }
    Literal(source, source.source + 1, false);
  }

  void Finish(uint64_t wrt_bytes) {
    if (pending_.has_value()) {
      Literal(*pending_, wrt_bytes, true);
      pending_.reset();
    }
  }

 private:
  SeenRoute& Route(const Id& route) {
    const auto found = routes_.find(route);
    if (found == routes_.end()) Die("replay route missing");
    return found->second;
  }

  Record Plain(const Observation& source, uint64_t availability, uint8_t event,
               uint8_t flags) const {
    Record result{};
    result.source = source.source;
    result.availability = availability;
    result.raw_before = source.raw_before;
    result.raw_after = source.raw_after;
    result.event = event;
    result.flags = flags;
    result.depth = uint8_t(depth_);
    return result;
  }

  Record Routed(const Frame& frame, const Observation& source, uint64_t availability,
                uint8_t event, uint8_t flags, uint8_t key) const {
    Record result = Plain(source, availability, event, flags);
    result.route = frame.route;
    result.witness = frame.witness;
    result.field = frame.field;
    result.key_identity = key;
    return result;
  }

  void OpenTemplate(const Observation& source) {
    if (overflow_ != 0) {
      ++overflow_;
      artifacts_->Expect(Plain(source, source.source + 1, kOverflowEnter,
                               kOverflow | kPosttruth));
      return;
    }
    if (depth_ == frames_.size()) {
      overflow_ = 1;
      artifacts_->Expect(Plain(source, source.source + 1, kOverflowEnter,
                               kOverflow | kPosttruth));
      return;
    }
    if (depth_ != 0) {
      Frame& parent = frames_[depth_ - 1];
      if (parent.phase == Phase::kName) {
        parent.name.valid = false;
        parent.usable = false;
      } else if (parent.phase == Phase::kKey) {
        parent.token.valid = false;
      }
    }
    frames_[depth_] = Frame{};
    ++depth_;
    artifacts_->Expect(Plain(source, source.source + 1, kTemplateEnter, kPosttruth));
  }

  void FieldExit(Frame& frame, const Observation& source, uint64_t availability) {
    if (frame.phase == Phase::kValue && frame.route_valid) {
      Record result = Routed(frame, source, availability, kFieldExit,
                             kValid | kExplicit | kPosttruth, 1);
      result.ordinal = Route(frame.route).ordinal;
      artifacts_->Expect(result);
      frame.route_valid = false;
    } else if (frame.phase == Phase::kKey && frame.token.size != 0) {
      Record result = Plain(source, availability, kPositionalExit,
                            kPositional | kPosttruth);
      result.field = frame.field;
      result.key_identity = 2;
      artifacts_->Expect(result);
    }
  }

  void CloseTemplate(const Observation& source) {
    if (overflow_ != 0) {
      --overflow_;
      artifacts_->Expect(Plain(source, source.source + 1, kOverflowExit,
                               kOverflow | kPosttruth));
      return;
    }
    if (depth_ == 0) return;
    Frame& frame = frames_[depth_ - 1];
    FieldExit(frame, source, source.source + 1);
    artifacts_->Expect(Plain(source, source.source + 1, kTemplateExit, kPosttruth));
    --depth_;
  }

  void Activate(Frame& frame, const Observation& source, uint64_t availability) {
    if (!frame.usable || !frame.name.valid || frame.name.size == 0 ||
        !frame.token.valid || frame.token.size == 0) {
      frame.route_valid = false;
      return;
    }
    Descriptor descriptor{};
    descriptor.name = frame.name;
    descriptor.key = frame.token;
    descriptor.route = DescriptorHash(descriptor.name, descriptor.key,
                                      0x5254554c455f3031ULL, 0x5254554c455f3032ULL);
    descriptor.witness = DescriptorHash(descriptor.name, descriptor.key,
                                        0x5749544e45535331ULL, 0x5749544e45535332ULL);
    const auto inserted = routes_.emplace(descriptor.route, SeenRoute{descriptor, 0});
    if (!inserted.second &&
        (!Same(inserted.first->second.descriptor.name, descriptor.name) ||
         !Same(inserted.first->second.descriptor.key, descriptor.key))) {
      Die("route collision in independent replay");
    }
    const auto witness = witnesses_.emplace(descriptor.witness, descriptor.route);
    if (!witness.second && !(witness.first->second == descriptor.route)) {
      Die("witness collision in independent replay");
    }
    if (inserted.second) artifacts_->ExpectDescriptor(descriptor);
    frame.route = descriptor.route;
    frame.witness = descriptor.witness;
    frame.route_valid = true;
    Record result = Routed(frame, source, availability, kExplicitEntry,
                           kValid | kExplicit | kPosttruth, 1);
    result.ordinal = inserted.first->second.ordinal;
    artifacts_->Expect(result);
  }

  void Append(Frame& frame, const Observation& source, uint64_t availability,
              bool deferred) {
    if (!frame.route_valid) return;
    SeenRoute& route = Route(frame.route);
    if (deferred) {
      Record result = Routed(frame, source, availability, kDeferredUpdate,
                             kValid | kUpdateOnly | kExplicit | kDeferred, 1);
      result.ordinal = route.ordinal;
      artifacts_->Expect(result);
    }
    ++route.ordinal;
  }

  void Literal(const Observation& source, uint64_t availability, bool deferred) {
    if (overflow_ != 0 || depth_ == 0) return;
    Frame& frame = frames_[depth_ - 1];
    if (frame.phase == Phase::kName) {
      if (source.byte == kField) {
        if (!frame.name.valid || frame.name.size == 0) frame.usable = false;
        frame.phase = Phase::kKey;
        frame.token.Clear();
        frame.field = 0;
      } else {
        frame.name.Add(source.byte);
      }
      return;
    }
    if (frame.phase == Phase::kKey) {
      if (source.byte == kEqual) {
        Activate(frame, source, availability);
        frame.phase = Phase::kValue;
      } else if (source.byte == kField) {
        FieldExit(frame, source, availability);
        ++frame.field;
        frame.token.Clear();
      } else {
        frame.token.Add(source.byte);
      }
      return;
    }
    if (source.byte == kField) {
      FieldExit(frame, source, availability);
      ++frame.field;
      frame.phase = Phase::kKey;
      frame.token.Clear();
      return;
    }
    Append(frame, source, availability, deferred);
  }

  ArtifactReader* artifacts_ = nullptr;
  std::array<Frame, kMaximumDepth> frames_{};
  size_t depth_ = 0;
  size_t overflow_ = 0;
  std::optional<Observation> pending_{};
  std::unordered_map<Id, SeenRoute, IdHash> routes_{};
  std::unordered_map<Id, Id, IdHash> witnesses_{};
};

}  // namespace

int main(int argc, char** argv) {
  if (argc != 6) {
    std::fprintf(stderr, "usage: %s STORE RAW DICTIONARY TAPE SIDECAR\n", argv[0]);
    return 64;
  }
  const uint64_t store_bytes = FileSize(argv[1]);
  const uint64_t raw_bytes = FileSize(argv[2]);
  const uint64_t dictionary_bytes = FileSize(argv[3]);
  if (store_bytes < 11) Die("store too short");
  const uint64_t wrt_bytes = store_bytes - 5;
  FILE* store = Open(argv[1]);
  FILE* raw = Open(argv[2]);
  FILE* dictionary = Open(argv[3]);
  const std::array<uint8_t, 5> wrapper = {0x80, 0, 0, 0, 0};
  for (const uint8_t expected : wrapper) {
    if (std::getc(store) != expected) Die("store wrapper");
  }
  ArtifactReader artifacts(argv[4], argv[5], store_bytes, wrt_bytes, raw_bytes,
                           dictionary_bytes);
  RawReplay inverse(dictionary, raw);
  SemanticReplay semantics(&artifacts);
  for (uint64_t coordinate = 0; coordinate < wrt_bytes; ++coordinate) {
    Observation observation{};
    observation.source = coordinate;
    observation.raw_before = inverse.position();
    std::optional<Record> prediction = semantics.Prediction(observation);
    const int item = std::getc(store);
    if (item == EOF) Die("short store");
    observation.byte = uint8_t(item);
    const auto span = inverse.Push(observation.byte, coordinate);
    observation.raw_before = span.first;
    observation.raw_after = span.second;
    if (prediction.has_value()) {
      prediction->raw_before = span.first;
      prediction->raw_after = span.second;
      artifacts.Expect(*prediction);
    }
    semantics.Truth(observation);
  }
  if (std::getc(store) != EOF) Die("store trailing byte");
  inverse.Finish(raw_bytes);
  semantics.Finish(wrt_bytes);
  artifacts.Finish(inverse.raw_digest(), inverse.wrt_digest());
  std::printf(
      "{\"schema\":\"gamma.enwiki9.endpoint428-semantic-native-replay.v3\","
      "\"semantic_replay_pass\":true,\"fixture\":%s,\"wrt_bytes\":%" PRIu64
      ",\"raw_bytes\":%" PRIu64 ",\"record_count\":%" PRIu64
      ",\"descriptor_count\":%" PRIu64
      ",\"archive_authority\":false,\"score_credit_bytes\":0}\n",
      artifacts.fixture() ? "true" : "false", wrt_bytes, raw_bytes,
      artifacts.record_count(), artifacts.descriptor_count());
  if (std::fclose(dictionary) != 0 || std::fclose(raw) != 0 ||
      std::fclose(store) != 0) {
    Die("input close");
  }
  return 0;
}
