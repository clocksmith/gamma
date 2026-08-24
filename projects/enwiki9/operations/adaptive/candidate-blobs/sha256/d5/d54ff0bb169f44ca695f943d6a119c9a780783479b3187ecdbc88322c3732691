#include <algorithm>
#include <array>
#include <cerrno>
#include <cinttypes>
#include <cstdlib>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <sys/stat.h>
#include <unistd.h>

namespace {

constexpr uint64_t kExpectedInputBytes = 587138826ULL;
constexpr uint8_t kOpenByte = static_cast<uint8_t>('P');
constexpr uint8_t kFieldByte = static_cast<uint8_t>('Q');
constexpr uint8_t kEqualByte = static_cast<uint8_t>('M');
constexpr uint8_t kCloseByte = static_cast<uint8_t>('R');
constexpr size_t kMaximumDepth = 32;
constexpr size_t kMaximumAtomBytes = 48;
constexpr size_t kMaximumTargetBytes = kMaximumAtomBytes + 1;
constexpr size_t kMaximumStagedProgramsPerTemplate = 64;
constexpr size_t kTableSets = 32768;
constexpr size_t kTableWays = 4;
constexpr uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr uint64_t kFnvPrime = 1099511628211ULL;
constexpr uint64_t kFirstFieldHash = 0xf17e5eed93a42711ULL;
constexpr uint64_t kPositionalFieldHash = 0x705051710fa1d31bULL;
constexpr uint64_t kRandomSeed = 0x57534d564d5f5231ULL;

[[noreturn]] void Fail(const char* operation) {
  std::fprintf(stderr, "wiki-schema-vm failure operation=%s errno=%d\n",
               operation, errno);
  std::exit(1);
}

uint64_t FnvByte(uint64_t hash, uint8_t value) {
  return (hash ^ value) * kFnvPrime;
}

uint64_t FnvU64(uint64_t hash, uint64_t value) {
  for (unsigned int i = 0; i < 8; ++i) {
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

uint64_t HashAtom(const uint8_t* data, size_t size) {
  uint64_t hash = FnvU64(kFnvOffset, static_cast<uint64_t>(size));
  for (size_t i = 0; i < size; ++i) hash = FnvByte(hash, data[i]);
  return Mix64(hash);
}

uint64_t StateKey(uint64_t name_hash, uint64_t previous_key_hash,
                  uint32_t field_index) {
  uint64_t hash = FnvU64(kFnvOffset, name_hash);
  hash = FnvU64(hash, previous_key_hash);
  hash = FnvU64(hash, field_index);
  hash = Mix64(hash);
  return hash == 0 ? 1 : hash;
}

struct Atom {
  std::array<uint8_t, kMaximumAtomBytes> bytes{};
  uint8_t size = 0;
  bool valid = true;

  void Clear() {
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

struct Candidate {
  std::array<uint8_t, kMaximumTargetBytes> bytes{};
  uint8_t size = 0;
  uint64_t count = 0;
  uint64_t error = 0;

  bool Empty() const { return size == 0; }

  bool Equals(const uint8_t* other, size_t other_size) const {
    return size == other_size &&
           std::memcmp(bytes.data(), other, other_size) == 0;
  }

  uint64_t LowerBound() const { return count - error; }

  void Assign(const uint8_t* source, size_t source_size, uint64_t new_count,
              uint64_t new_error) {
    std::fill(bytes.begin(), bytes.end(), 0);
    std::memcpy(bytes.data(), source, source_size);
    size = static_cast<uint8_t>(source_size);
    count = new_count;
    error = new_error;
  }
};

struct StateSlot {
  uint64_t key = 0;
  uint64_t observations = 0;
  std::array<Candidate, 2> candidates{};

  void Reset(uint64_t new_key) {
    key = new_key;
    observations = 0;
    candidates = {};
  }
};

struct TableStats {
  uint64_t lookups = 0;
  uint64_t hits = 0;
  uint64_t inserts = 0;
  uint64_t set_replacements = 0;
  uint64_t candidate_replacements = 0;
  uint64_t updates = 0;
};

class ProgramTable {
 public:
  bool Select(uint64_t key, std::array<uint8_t, kMaximumTargetBytes>* output,
              uint8_t* output_size) {
    ++stats_.lookups;
    const StateSlot* slot = Find(key);
    if (slot == nullptr) return false;
    ++stats_.hits;
    const Candidate* first = &slot->candidates[0];
    const Candidate* second = &slot->candidates[1];
    if (Better(*second, *first)) std::swap(first, second);
    if (first->Empty() || first->LowerBound() < 2 ||
        first->LowerBound() * 2 <= slot->observations) {
      return false;
    }
    *output = first->bytes;
    *output_size = first->size;
    return true;
  }

  void Update(uint64_t key, const uint8_t* target, size_t target_size) {
    if (target_size == 0 || target_size > kMaximumTargetBytes) Fail("target size");
    StateSlot* slot = Ensure(key);
    ++slot->observations;
    ++stats_.updates;
    for (Candidate& candidate : slot->candidates) {
      if (candidate.Equals(target, target_size)) {
        ++candidate.count;
        return;
      }
    }
    for (Candidate& candidate : slot->candidates) {
      if (candidate.Empty()) {
        candidate.Assign(target, target_size, 1, 0);
        return;
      }
    }
    Candidate* victim = &slot->candidates[0];
    if (slot->candidates[1].count < victim->count) victim = &slot->candidates[1];
    const uint64_t inherited = victim->count;
    victim->Assign(target, target_size, inherited + 1, inherited);
    ++stats_.candidate_replacements;
  }

  uint64_t Digest() const {
    uint64_t hash = kFnvOffset;
    for (size_t set = 0; set < kTableSets; ++set) {
      for (size_t way = 0; way < kTableWays; ++way) {
        const StateSlot& slot = slots_[set][way];
        hash = FnvU64(hash, set);
        hash = FnvU64(hash, way);
        hash = FnvU64(hash, slot.key);
        hash = FnvU64(hash, slot.observations);
        for (const Candidate& candidate : slot.candidates) {
          hash = FnvU64(hash, candidate.size);
          hash = FnvU64(hash, candidate.count);
          hash = FnvU64(hash, candidate.error);
          for (size_t i = 0; i < candidate.size; ++i) {
            hash = FnvByte(hash, candidate.bytes[i]);
          }
        }
      }
    }
    return hash;
  }

  const TableStats& stats() const { return stats_; }

 private:
  static bool Better(const Candidate& left, const Candidate& right) {
    if (left.Empty()) return false;
    if (right.Empty()) return true;
    if (left.LowerBound() != right.LowerBound()) {
      return left.LowerBound() > right.LowerBound();
    }
    if (left.count != right.count) return left.count > right.count;
    const size_t common = std::min<size_t>(left.size, right.size);
    const int ordering = std::memcmp(left.bytes.data(), right.bytes.data(), common);
    return ordering < 0 || (ordering == 0 && left.size < right.size);
  }

  const StateSlot* Find(uint64_t key) const {
    const auto& set = slots_[key & (kTableSets - 1)];
    for (const StateSlot& slot : set) {
      if (slot.key == key) return &slot;
    }
    return nullptr;
  }

  StateSlot* Ensure(uint64_t key) {
    auto& set = slots_[key & (kTableSets - 1)];
    for (StateSlot& slot : set) {
      if (slot.key == key) return &slot;
    }
    for (StateSlot& slot : set) {
      if (slot.key == 0) {
        slot.Reset(key);
        ++stats_.inserts;
        return &slot;
      }
    }
    StateSlot* victim = &set[0];
    for (size_t way = 1; way < kTableWays; ++way) {
      if (set[way].observations < victim->observations) victim = &set[way];
    }
    victim->Reset(key);
    ++stats_.set_replacements;
    return victim;
  }

  std::array<std::array<StateSlot, kTableWays>, kTableSets> slots_{};
  TableStats stats_{};
};

enum class Phase : uint8_t { name, field_key, field_value };

struct StagedProgram {
  uint64_t state_key = 0;
  std::array<uint8_t, kMaximumTargetBytes> target{};
  uint8_t target_size = 0;
};

struct Frame {
  Phase phase = Phase::name;
  Atom name{};
  Atom token{};
  uint64_t name_hash = 0;
  uint64_t previous_key_hash = kFirstFieldHash;
  uint64_t pending_state_key = 0;
  uint32_t field_index = 0;
  bool usable = true;
  bool staging_valid = true;
  uint8_t staged_programs = 0;
  std::array<StagedProgram, kMaximumStagedProgramsPerTemplate> staged{};
};

struct ActivePrediction {
  std::array<uint8_t, kMaximumTargetBytes> treatment{};
  std::array<uint8_t, kMaximumTargetBytes> random{};
  std::array<uint8_t, kMaximumTargetBytes> shifted{};
  uint64_t state_key = 0;
  uint8_t size = 0;
  uint8_t position = 0;
  bool live = false;

  void Stop() {
    live = false;
    size = 0;
    position = 0;
  }
};

struct Measurements {
  uint64_t input_bytes = 0;
  uint64_t templates_opened = 0;
  uint64_t templates_completed = 0;
  uint64_t depth_overflows = 0;
  uint64_t atom_overflows = 0;
  uint64_t staging_overflows = 0;
  uint64_t named_keys_completed = 0;
  uint64_t completed_template_updates = 0;
  uint64_t programs_activated = 0;
  uint64_t opportunity_bytes = 0;
  uint64_t treatment_correct_bytes = 0;
  uint64_t random_correct_bytes = 0;
  uint64_t shifted_correct_bytes = 0;
  std::array<uint64_t, 3> treatment_correct_by_third{};
  uint64_t opportunity_hash = kFnvOffset;
  uint64_t parser_hash = kFnvOffset;
};

class SchemaVm {
 public:
  void Observe(uint8_t byte, uint64_t offset) {
    Score(byte, offset);
    measurements_.input_bytes = offset + 1;
    if (pending_ != 0) {
      if (pending_ == kOpenByte && byte == kOpenByte) {
        pending_ = 0;
        OpenTemplate();
        return;
      }
      if (pending_ == kCloseByte && byte == kCloseByte) {
        pending_ = 0;
        CloseTemplate();
        return;
      }
      ConsumeLiteral(pending_);
      pending_ = 0;
    }
    if (byte == kOpenByte || byte == kCloseByte) {
      pending_ = byte;
      return;
    }
    ConsumeLiteral(byte);
  }

  void Finish() {
    if (pending_ != 0) ConsumeLiteral(pending_);
    pending_ = 0;
    prediction_.Stop();
    HashParserState();
  }

  const Measurements& measurements() const { return measurements_; }
  const ProgramTable& table() const { return table_; }

 private:
  void Score(uint8_t actual, uint64_t offset) {
    if (!prediction_.live) return;
    const size_t position = prediction_.position;
    const uint8_t expected = prediction_.treatment[position];
    ++measurements_.opportunity_bytes;
    measurements_.opportunity_hash = FnvU64(measurements_.opportunity_hash, offset);
    measurements_.opportunity_hash =
        FnvU64(measurements_.opportunity_hash, prediction_.state_key);
    measurements_.opportunity_hash =
        FnvByte(measurements_.opportunity_hash, static_cast<uint8_t>(position));
    measurements_.opportunity_hash = FnvByte(measurements_.opportunity_hash, actual);
    measurements_.opportunity_hash = FnvByte(measurements_.opportunity_hash, expected);
    measurements_.opportunity_hash =
        FnvByte(measurements_.opportunity_hash, prediction_.random[position]);
    measurements_.opportunity_hash =
        FnvByte(measurements_.opportunity_hash, prediction_.shifted[position]);
    if (actual == expected) {
      ++measurements_.treatment_correct_bytes;
      size_t third = static_cast<size_t>((offset * 3) / kExpectedInputBytes);
      if (third > 2) third = 2;
      ++measurements_.treatment_correct_by_third[third];
    }
    if (actual == prediction_.random[position]) ++measurements_.random_correct_bytes;
    if (actual == prediction_.shifted[position]) ++measurements_.shifted_correct_bytes;
    if (actual != expected || position + 1 >= prediction_.size) {
      prediction_.Stop();
    } else {
      ++prediction_.position;
    }
  }

  void OpenTemplate() {
    prediction_.Stop();
    ++measurements_.templates_opened;
    if (overflow_depth_ > 0) {
      ++overflow_depth_;
      return;
    }
    if (depth_ >= frames_.size()) {
      overflow_depth_ = 1;
      ++measurements_.depth_overflows;
      return;
    }
    if (depth_ > 0) {
      Frame& parent = frames_[depth_ - 1];
      if (parent.phase == Phase::name) {
        parent.name.valid = false;
        parent.usable = false;
      } else if (parent.phase == Phase::field_key) {
        parent.token.valid = false;
      }
    }
    frames_[depth_] = Frame{};
    ++depth_;
  }

  void CloseTemplate() {
    prediction_.Stop();
    if (overflow_depth_ > 0) {
      --overflow_depth_;
      return;
    }
    if (depth_ == 0) return;
    Frame& frame = frames_[depth_ - 1];
    if (frame.usable && frame.staging_valid) {
      for (size_t index = 0; index < frame.staged_programs; ++index) {
        const StagedProgram& staged = frame.staged[index];
        table_.Update(staged.state_key, staged.target.data(), staged.target_size);
        ++measurements_.completed_template_updates;
      }
    }
    if (frame.name_hash != 0) last_completed_name_hash_ = frame.name_hash;
    HashFrame(frame);
    --depth_;
    ++measurements_.templates_completed;
  }

  void ConsumeLiteral(uint8_t byte) {
    if (overflow_depth_ > 0 || depth_ == 0) return;
    Frame& frame = frames_[depth_ - 1];
    if (frame.phase == Phase::name) {
      if (byte == kFieldByte) {
        if (!frame.name.valid || frame.name.size == 0) {
          frame.usable = false;
        } else {
          frame.name_hash = HashAtom(frame.name.bytes.data(), frame.name.size);
          frame.previous_key_hash = kFirstFieldHash;
          frame.field_index = 0;
          frame.pending_state_key =
              StateKey(frame.name_hash, frame.previous_key_hash, frame.field_index);
          Schedule(frame);
        }
        frame.phase = Phase::field_key;
        frame.token.Clear();
      } else {
        const bool was_valid = frame.name.valid;
        frame.name.Append(byte);
        if (was_valid && !frame.name.valid) ++measurements_.atom_overflows;
      }
      return;
    }
    if (frame.phase == Phase::field_key) {
      if (byte == kEqualByte) {
        if (frame.usable && frame.token.valid && frame.token.size > 0) {
          std::array<uint8_t, kMaximumTargetBytes> target{};
          std::memcpy(target.data(), frame.token.bytes.data(), frame.token.size);
          target[frame.token.size] = kEqualByte;
          StageProgram(frame, target.data(), frame.token.size + 1);
          frame.previous_key_hash =
              HashAtom(frame.token.bytes.data(), frame.token.size);
          ++measurements_.named_keys_completed;
        } else {
          frame.previous_key_hash = kPositionalFieldHash ^ frame.field_index;
        }
        frame.phase = Phase::field_value;
        frame.token.Clear();
      } else if (byte == kFieldByte) {
        frame.previous_key_hash = kPositionalFieldHash ^ frame.field_index;
        ++frame.field_index;
        frame.pending_state_key =
            StateKey(frame.name_hash, frame.previous_key_hash, frame.field_index);
        frame.token.Clear();
        Schedule(frame);
      } else {
        const bool was_valid = frame.token.valid;
        frame.token.Append(byte);
        if (was_valid && !frame.token.valid) ++measurements_.atom_overflows;
      }
      return;
    }
    if (byte == kFieldByte) {
      ++frame.field_index;
      frame.phase = Phase::field_key;
      frame.token.Clear();
      frame.pending_state_key =
          StateKey(frame.name_hash, frame.previous_key_hash, frame.field_index);
      Schedule(frame);
    }
  }

  void StageProgram(Frame& frame, const uint8_t* target, size_t target_size) {
    if (!frame.staging_valid) return;
    if (frame.staged_programs >= frame.staged.size()) {
      frame.staging_valid = false;
      ++measurements_.staging_overflows;
      return;
    }
    StagedProgram& staged = frame.staged[frame.staged_programs++];
    staged.state_key = frame.pending_state_key;
    std::copy(target, target + target_size, staged.target.begin());
    staged.target_size = static_cast<uint8_t>(target_size);
  }

  void Schedule(const Frame& frame) {
    prediction_.Stop();
    if (!frame.usable || frame.name_hash == 0) return;
    uint8_t treatment_size = 0;
    if (!table_.Select(frame.pending_state_key, &prediction_.treatment,
                       &treatment_size)) {
      return;
    }
    prediction_.state_key = frame.pending_state_key;
    prediction_.size = treatment_size;
    prediction_.position = 0;
    prediction_.live = true;
    ++measurements_.programs_activated;

    uint64_t random_state = Mix64(frame.pending_state_key ^ kRandomSeed);
    for (size_t i = 0; i < treatment_size; ++i) {
      random_state = Mix64(random_state + 0x9e3779b97f4a7c15ULL + i);
      prediction_.random[i] = static_cast<uint8_t>(random_state >> 56);
    }

    std::array<uint8_t, kMaximumTargetBytes> shifted_program{};
    uint8_t shifted_size = 0;
    const uint64_t shifted_key =
        StateKey(last_completed_name_hash_, frame.previous_key_hash,
                 frame.field_index);
    const bool shifted_available = last_completed_name_hash_ != 0 &&
        table_.Select(shifted_key, &shifted_program, &shifted_size) &&
        shifted_size > 0;
    for (size_t i = 0; i < treatment_size; ++i) {
      prediction_.shifted[i] = shifted_available
          ? shifted_program[i % shifted_size]
          : prediction_.treatment[(i + 1) % treatment_size];
    }
  }

  void HashFrame(const Frame& frame) {
    measurements_.parser_hash = FnvU64(measurements_.parser_hash, frame.name_hash);
    measurements_.parser_hash =
        FnvU64(measurements_.parser_hash, frame.previous_key_hash);
    measurements_.parser_hash = FnvU64(measurements_.parser_hash, frame.field_index);
    measurements_.parser_hash =
        FnvByte(measurements_.parser_hash, static_cast<uint8_t>(frame.phase));
    measurements_.parser_hash = FnvByte(measurements_.parser_hash, frame.usable);
    measurements_.parser_hash =
        FnvByte(measurements_.parser_hash, frame.staging_valid);
    measurements_.parser_hash =
        FnvByte(measurements_.parser_hash, frame.staged_programs);
  }

  void HashParserState() {
    measurements_.parser_hash = FnvU64(measurements_.parser_hash, depth_);
    measurements_.parser_hash = FnvU64(measurements_.parser_hash, overflow_depth_);
    measurements_.parser_hash = FnvU64(measurements_.parser_hash,
                                       last_completed_name_hash_);
    measurements_.parser_hash = FnvU64(measurements_.parser_hash,
                                       measurements_.templates_opened);
    measurements_.parser_hash = FnvU64(measurements_.parser_hash,
                                       measurements_.templates_completed);
  }

  ProgramTable table_{};
  std::array<Frame, kMaximumDepth> frames_{};
  size_t depth_ = 0;
  size_t overflow_depth_ = 0;
  uint8_t pending_ = 0;
  uint64_t last_completed_name_hash_ = 0;
  ActivePrediction prediction_{};
  Measurements measurements_{};
};

void WriteAll(int descriptor, const char* data, size_t size) {
  while (size > 0) {
    const ssize_t written = write(descriptor, data, size);
    if (written < 0 && errno == EINTR) continue;
    if (written <= 0) Fail("write output");
    data += written;
    size -= static_cast<size_t>(written);
  }
}

void WriteReceipt(const char* path, const SchemaVm& vm) {
  const int descriptor = open(path, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC |
      O_NOFOLLOW, 0600);
  if (descriptor < 0) Fail("create output");
  const Measurements& m = vm.measurements();
  const TableStats& t = vm.table().stats();
  const uint64_t minimum_third = *std::min_element(
      m.treatment_correct_by_third.begin(), m.treatment_correct_by_third.end());
  char buffer[8192];
  const int length = std::snprintf(buffer, sizeof(buffer),
      "{\n"
      "  \"schema\": \"gamma.enwiki9.wiki-schema-vm-scan.v1\",\n"
      "  \"candidate_id\": \"wiki_schema_vm_ceiling_q0_v1\",\n"
      "  \"population_bytes\": %" PRIu64 ",\n"
      "  \"population_sha256_expected\": \"7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce\",\n"
      "  \"templates_opened\": %" PRIu64 ",\n"
      "  \"templates_completed\": %" PRIu64 ",\n"
      "  \"depth_overflows\": %" PRIu64 ",\n"
      "  \"atom_overflows\": %" PRIu64 ",\n"
      "  \"staging_overflows\": %" PRIu64 ",\n"
      "  \"named_keys_completed\": %" PRIu64 ",\n"
      "  \"completed_template_updates\": %" PRIu64 ",\n"
      "  \"programs_activated\": %" PRIu64 ",\n"
      "  \"opportunity_bytes\": %" PRIu64 ",\n"
      "  \"treatment_correct_bytes\": %" PRIu64 ",\n"
      "  \"random_correct_bytes\": %" PRIu64 ",\n"
      "  \"shifted_correct_bytes\": %" PRIu64 ",\n"
      "  \"treatment_minus_random_correct_bytes\": %" PRId64 ",\n"
      "  \"treatment_minus_shifted_correct_bytes\": %" PRId64 ",\n"
      "  \"treatment_correct_by_third\": [%" PRIu64 ", %" PRIu64 ", %" PRIu64 "],\n"
      "  \"minimum_third_treatment_correct_bytes\": %" PRIu64 ",\n"
      "  \"table_lookups\": %" PRIu64 ",\n"
      "  \"table_hits\": %" PRIu64 ",\n"
      "  \"table_inserts\": %" PRIu64 ",\n"
      "  \"table_set_replacements\": %" PRIu64 ",\n"
      "  \"table_candidate_replacements\": %" PRIu64 ",\n"
      "  \"table_updates\": %" PRIu64 ",\n"
      "  \"opportunity_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"parser_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"table_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"bounded_state_pass\": true,\n"
      "  \"archive_authority\": false,\n"
      "  \"score_credit_bytes\": 0\n"
      "}\n",
      m.input_bytes, m.templates_opened, m.templates_completed,
      m.depth_overflows, m.atom_overflows, m.staging_overflows,
      m.named_keys_completed, m.completed_template_updates,
      m.programs_activated, m.opportunity_bytes, m.treatment_correct_bytes,
      m.random_correct_bytes, m.shifted_correct_bytes,
      static_cast<int64_t>(m.treatment_correct_bytes) -
          static_cast<int64_t>(m.random_correct_bytes),
      static_cast<int64_t>(m.treatment_correct_bytes) -
          static_cast<int64_t>(m.shifted_correct_bytes),
      m.treatment_correct_by_third[0], m.treatment_correct_by_third[1],
      m.treatment_correct_by_third[2], minimum_third, t.lookups, t.hits,
      t.inserts, t.set_replacements, t.candidate_replacements, t.updates,
      m.opportunity_hash, m.parser_hash, vm.table().Digest());
  if (length < 0 || static_cast<size_t>(length) >= sizeof(buffer)) {
    close(descriptor);
    Fail("format output");
  }
  WriteAll(descriptor, buffer, static_cast<size_t>(length));
  if (fsync(descriptor) != 0) {
    close(descriptor);
    Fail("fsync output");
  }
  if (close(descriptor) != 0) Fail("close output");
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 3) {
    std::fprintf(stderr, "usage: %s TRANSFORMED_READY OUTPUT_JSON\n", argv[0]);
    return 64;
  }
  struct stat metadata = {};
  if (lstat(argv[1], &metadata) != 0 || !S_ISREG(metadata.st_mode) ||
      metadata.st_nlink != 1 || static_cast<uint64_t>(metadata.st_size) !=
          kExpectedInputBytes) {
    errno = EINVAL;
    Fail("input identity geometry");
  }
  const int input = open(argv[1], O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (input < 0) Fail("open input");
  // These objects deliberately have static storage. ProgramTable is roughly
  // 20 MiB and the read buffer is 8 MiB; placing either on the process stack
  // would make the bounded-state scanner depend on the host stack limit.
  static SchemaVm vm;
  static std::array<uint8_t, 8 * 1024 * 1024> buffer{};
  uint64_t offset = 0;
  for (;;) {
    const ssize_t count = read(input, buffer.data(), buffer.size());
    if (count < 0 && errno == EINTR) continue;
    if (count < 0) Fail("read input");
    if (count == 0) break;
    for (ssize_t i = 0; i < count; ++i) vm.Observe(buffer[i], offset++);
  }
  if (close(input) != 0) Fail("close input");
  if (offset != kExpectedInputBytes) {
    errno = EIO;
    Fail("short input");
  }
  vm.Finish();
  WriteReceipt(argv[2], vm);
  return 0;
}
