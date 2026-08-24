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
#include <optional>
#include <string>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <vector>

namespace {

constexpr uint64_t kPopulationBytes = 587138826ULL;
constexpr uint64_t kRequiredCorrectBytes = 4079243ULL;
constexpr unsigned char kLessThan = 'L';
constexpr unsigned char kGreaterThan = 'N';
constexpr size_t kMaxName = 16;
constexpr size_t kMaxDepth = 16;
constexpr size_t kMaxEvent = 4096;
constexpr size_t kTableEntries = 1024;
constexpr size_t kMaxSignature = 19;
constexpr size_t kReadBlock = 1U << 20;
constexpr uint64_t kFnvOffset = 14695981039346656037ULL;
constexpr uint64_t kFnvPrime = 1099511628211ULL;

[[noreturn]] void Fail(const char* operation) {
  std::fprintf(stderr, "%s: errno=%d (%s)\n", operation, errno,
               std::strerror(errno));
  std::exit(1);
}

uint64_t FnvByte(uint64_t value, uint8_t byte) {
  return (value ^ byte) * kFnvPrime;
}

uint64_t FnvU64(uint64_t value, uint64_t input) {
  for (unsigned shift = 0; shift < 64; shift += 8) {
    value = FnvByte(value, static_cast<uint8_t>(input >> shift));
  }
  return value;
}

uint64_t SplitMix64(uint64_t value) {
  value += 0x9e3779b97f4a7c15ULL;
  value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ULL;
  value = (value ^ (value >> 27)) * 0x94d049bb133111ebULL;
  return value ^ (value >> 31);
}

struct Name {
  std::array<uint8_t, kMaxName> bytes{};
  uint8_t size = 0;

  bool operator==(const Name& other) const {
    return size == other.size &&
           std::equal(bytes.begin(), bytes.begin() + size,
                      other.bytes.begin());
  }

  uint64_t Hash() const {
    uint64_t value = kFnvOffset;
    for (size_t i = 0; i < size; ++i) value = FnvByte(value, bytes[i]);
    return value;
  }
};

struct Signature {
  std::array<uint8_t, kMaxSignature> bytes{};
  uint8_t size = 0;

  bool operator==(const Signature& other) const {
    return size == other.size &&
           std::equal(bytes.begin(), bytes.begin() + size,
                      other.bytes.begin());
  }
};

struct ParsedEvent {
  bool valid = false;
  bool closing = false;
  bool self_closing = false;
  Name name;
  Signature signature;
};

bool IsNameTerminator(uint8_t value) {
  return value == ' ' || value == '\t' || value == '\r' || value == '\n' ||
         value == '/' || value == kGreaterThan;
}

ParsedEvent ParseEvent(const std::vector<uint8_t>& event) {
  ParsedEvent parsed;
  if (event.size() < 3 || event.front() != kLessThan ||
      event.back() != kGreaterThan) {
    return parsed;
  }
  size_t position = 1;
  if (event[position] == '!' || event[position] == '?') return parsed;
  if (event[position] == '/') {
    parsed.closing = true;
    ++position;
  }
  const size_t name_start = position;
  while (position < event.size() && !IsNameTerminator(event[position])) {
    ++position;
  }
  const size_t name_size = position - name_start;
  if (name_size == 0 || name_size > kMaxName) return parsed;
  parsed.name.size = static_cast<uint8_t>(name_size);
  std::copy(event.begin() + static_cast<std::ptrdiff_t>(name_start),
            event.begin() + static_cast<std::ptrdiff_t>(position),
            parsed.name.bytes.begin());

  size_t last = event.size() - 1;
  while (last > position &&
         (event[last - 1] == ' ' || event[last - 1] == '\t' ||
          event[last - 1] == '\r' || event[last - 1] == '\n')) {
    --last;
  }
  parsed.self_closing =
      !parsed.closing && last > position && event[last - 1] == '/';

  parsed.signature.bytes[parsed.signature.size++] = kLessThan;
  if (parsed.closing) parsed.signature.bytes[parsed.signature.size++] = '/';
  for (size_t i = 0; i < name_size; ++i) {
    parsed.signature.bytes[parsed.signature.size++] = parsed.name.bytes[i];
  }
  if (position == event.size() - 1) {
    parsed.signature.bytes[parsed.signature.size++] = kGreaterThan;
  }
  parsed.valid = true;
  return parsed;
}

Signature NameClosure(const Name& name) {
  Signature result;
  for (size_t i = 0; i < name.size; ++i) {
    result.bytes[result.size++] = name.bytes[i];
  }
  result.bytes[result.size++] = kGreaterThan;
  return result;
}

struct TableEntry {
  uint64_t key = 0;
  uint8_t state = 0;  // 0 empty, 1 exact, 2 poisoned.
  Signature target;
};

class UnanimousTable {
 public:
  std::optional<Signature> Lookup(uint64_t key) const {
    const TableEntry& entry = entries_[key & (kTableEntries - 1)];
    if (entry.state == 1 && entry.key == key) return entry.target;
    return std::nullopt;
  }

  void Observe(uint64_t key, const Signature& target) {
    TableEntry& entry = entries_[key & (kTableEntries - 1)];
    if (entry.state == 0) {
      entry.key = key;
      entry.target = target;
      entry.state = 1;
      ++installs_;
      return;
    }
    if (entry.state == 2) {
      ++poisoned_observations_;
      return;
    }
    if (entry.key != key || !(entry.target == target)) {
      entry.state = 2;
      ++poisons_;
    } else {
      ++reinforcements_;
    }
  }

  uint64_t Digest() const {
    uint64_t value = kFnvOffset;
    for (const TableEntry& entry : entries_) {
      value = FnvU64(value, entry.key);
      value = FnvByte(value, entry.state);
      value = FnvByte(value, entry.target.size);
      for (size_t i = 0; i < entry.target.size; ++i) {
        value = FnvByte(value, entry.target.bytes[i]);
      }
    }
    return value;
  }

  uint64_t installs() const { return installs_; }
  uint64_t reinforcements() const { return reinforcements_; }
  uint64_t poisons() const { return poisons_; }
  uint64_t poisoned_observations() const { return poisoned_observations_; }

 private:
  std::array<TableEntry, kTableEntries> entries_{};
  uint64_t installs_ = 0;
  uint64_t reinforcements_ = 0;
  uint64_t poisons_ = 0;
  uint64_t poisoned_observations_ = 0;
};

struct Counts {
  uint64_t active = 0;
  uint64_t correct = 0;
};

struct ArmCounts {
  uint64_t active = 0;
  uint64_t correct = 0;
  std::array<Counts, 3> thirds{};
};

size_t Third(uint64_t position) {
  return static_cast<size_t>(
      std::min<uint64_t>(2, (position * 3ULL) / kPopulationBytes));
}

void Score(ArmCounts* counts, uint64_t position, uint8_t prediction,
           uint8_t truth) {
  ++counts->active;
  Counts& third = counts->thirds[Third(position)];
  ++third.active;
  if (prediction == truth) {
    ++counts->correct;
    ++third.correct;
  }
}

uint64_t ComposeState(uint64_t parent, uint64_t previous, size_t depth) {
  uint64_t value = SplitMix64(parent ^ 0x5752545044410001ULL);
  value ^= SplitMix64(previous ^ 0x5752545044410002ULL);
  value ^= SplitMix64(static_cast<uint64_t>(depth) ^
                      0x5752545044410003ULL);
  return SplitMix64(value);
}

uint64_t EventHash(const ParsedEvent& event) {
  return SplitMix64(
      event.name.Hash() ^
      (event.closing ? 0x434c4f53494e4701ULL : 0x4f50454e494e4701ULL));
}

struct SelectedPrediction {
  uint8_t treatment = 0;
  uint8_t shifted = 0;
  uint8_t source = 0;  // 1 transition, 2 closure.
};

class Scanner {
 public:
  Scanner() { event_.reserve(kMaxEvent + 1); }

  void Observe(uint8_t truth) {
    if (position_ >= kPopulationBytes) Fail("population exceeds contract");
    if (in_event_) ScoreBeforeTruth(truth);

    input_digest_ = FnvByte(input_digest_, truth);
    AdvanceTransitionDigests(truth, 0);
    if (!in_event_) {
      if (truth == kLessThan) BeginEvent();
      ++position_;
      return;
    }

    event_.push_back(truth);
    if (truth == '\'' && !double_quote_) single_quote_ = !single_quote_;
    if (truth == '"' && !single_quote_) double_quote_ = !double_quote_;
    const bool terminal =
        truth == kGreaterThan && !single_quote_ && !double_quote_;
    if (event_.size() > kMaxEvent) {
      ++malformed_events_;
      ResetEvent();
    } else if (terminal) {
      CompleteEvent();
      ResetEvent();
    }
    ++position_;
  }

  void Finish() {
    if (position_ != kPopulationBytes) Fail("population shorter than contract");
    unterminated_event_ = in_event_;
    causal_and_verification_pass_ = Verify();
  }

  void Write(FILE* output) const {
    const int64_t minimum_margin = MinimumThirdMargin();
    const bool target_pass = d_.correct >= kRequiredCorrectBytes;
    const bool third_pass = minimum_margin > 0;
    const bool absolute_pass = target_pass && third_pass &&
                               causal_and_verification_pass_;
    std::fprintf(output,
        "{\n"
        "  \"schema\": \"gamma.enwiki9.wiki-pda-ceiling-scan.v1\",\n"
        "  \"candidate_id\": \"wiki_pda_structural_replay_ceiling_q0_v2\",\n"
        "  \"claim_authority\": \"causal_shadow_opportunity_screen_only\",\n"
        "  \"population_bytes\": %" PRIu64 ",\n"
        "  \"required_correct_bytes\": %" PRIu64 ",\n"
        "  \"events_started\": %" PRIu64 ",\n"
        "  \"events_completed\": %" PRIu64 ",\n"
        "  \"valid_events\": %" PRIu64 ",\n"
        "  \"malformed_events\": %" PRIu64 ",\n"
        "  \"unterminated_event\": %s,\n"
        "  \"close_mismatches\": %" PRIu64 ",\n"
        "  \"stack_pushes\": %" PRIu64 ",\n"
        "  \"stack_pops\": %" PRIu64 ",\n"
        "  \"suppression_pushes\": %" PRIu64 ",\n"
        "  \"suppression_pops\": %" PRIu64 ",\n"
        "  \"table_lookups\": %" PRIu64 ",\n"
        "  \"table_installs\": %" PRIu64 ",\n"
        "  \"table_reinforcements\": %" PRIu64 ",\n"
        "  \"table_poisons\": %" PRIu64 ",\n"
        "  \"table_poisoned_observations\": %" PRIu64 ",\n"
        "  \"transition_offset_zero_predictions\": %" PRIu64 ",\n"
        "  \"closing_before_offset_two_predictions\": %" PRIu64 ",\n",
        position_, kRequiredCorrectBytes, events_started_, events_completed_,
        valid_events_, malformed_events_,
        unterminated_event_ ? "true" : "false", close_mismatches_,
        stack_pushes_, stack_pops_, suppression_pushes_, suppression_pops_,
        table_lookups_, table_.installs(), table_.reinforcements(),
        table_.poisons(), table_.poisoned_observations(),
        transition_offset_zero_predictions_,
        closing_before_offset_two_predictions_);
    std::fprintf(output, "  \"arms\": {\n");
    WriteArm(output, "C", c_, true);
    WriteArm(output, "T", t_, true);
    WriteArm(output, "D", d_, true);
    WriteArm(output, "R", r_, true);
    WriteArm(output, "S", s_, true);
    WriteArm(output, "N", n_, false);
    std::fprintf(output,
        "  },\n"
        "  \"minimum_third_treatment_minus_max_control_correct_bytes\": %" PRId64 ",\n"
        "  \"input_fnv1a64\": \"%016" PRIx64 "\",\n"
        "  \"opportunity_fnv1a64\": \"%016" PRIx64 "\",\n"
        "  \"table_fnv1a64\": \"%016" PRIx64 "\",\n"
        "  \"stack_fnv1a64\": \"%016" PRIx64 "\",\n"
        "  \"k_transition_fnv1a64\": \"%016" PRIx64 "\",\n"
        "  \"d_transition_fnv1a64\": \"%016" PRIx64 "\",\n"
        "  \"treatment_k_state_identity_pass\": %s,\n"
        "  \"control_outcomes_feed_state\": false,\n"
        "  \"causal_and_verification_pass\": %s,\n"
        "  \"target_scale_correct_ceiling_pass\": %s,\n"
        "  \"all_thirds_beat_controls_pass\": %s,\n"
        "  \"absolute_ceiling_pass\": %s,\n"
        "  \"promotion_authorized\": false,\n"
        "  \"gamma_compression_credit_bytes\": 0,\n"
        "  \"gamma_score_credit_bytes\": 0\n"
        "}\n",
        minimum_margin, input_digest_, opportunity_digest_, table_.Digest(),
        StackDigest(), k_transition_digest_, d_transition_digest_,
        k_transition_digest_ == d_transition_digest_ ? "true" : "false",
        causal_and_verification_pass_ ? "true" : "false",
        target_pass ? "true" : "false", third_pass ? "true" : "false",
        absolute_pass ? "true" : "false");
  }

 private:
  void BeginEvent() {
    in_event_ = true;
    single_quote_ = false;
    double_quote_ = false;
    event_.clear();
    event_.push_back(kLessThan);
    const uint64_t parent = stack_.empty() ? 0 : stack_.back().Hash();
    const size_t depth = stack_.size();
    event_key_ = ComposeState(parent, previous_at_depth_[depth], depth);
    transition_target_ =
        suppressed_depth_ == 0 ? table_.Lookup(event_key_) : std::nullopt;
    ++events_started_;
    ++table_lookups_;
    AdvanceTransitionDigests(kLessThan, 1);
  }

  void ResetEvent() {
    in_event_ = false;
    single_quote_ = false;
    double_quote_ = false;
    event_.clear();
    transition_target_.reset();
  }

  void ScoreBeforeTruth(uint8_t truth) {
    const size_t relative = event_.size();
    if (relative == 0) ++transition_offset_zero_predictions_;
    std::optional<uint8_t> transition;
    if (transition_target_.has_value() &&
        relative < transition_target_->size) {
      if (relative == 0) ++transition_offset_zero_predictions_;
      transition = transition_target_->bytes[relative];
      Score(&t_, position_, transition.value(), truth);
    }

    std::optional<Signature> closure_target;
    std::optional<uint8_t> closure;
    if (suppressed_depth_ == 0 && !stack_.empty() && relative >= 2 &&
        event_[0] == kLessThan && event_[1] == '/') {
      closure_target = NameClosure(stack_.back());
      const size_t closure_index = relative - 2;
      if (closure_index < closure_target->size) {
        closure = closure_target->bytes[closure_index];
        Score(&c_, position_, closure.value(), truth);
      }
    }

    std::optional<SelectedPrediction> selected;
    if (transition.has_value()) {
      const size_t index = relative;
      selected = SelectedPrediction{
          transition.value(),
          transition_target_->bytes[(index + 1) % transition_target_->size],
          1};
    } else if (closure.has_value()) {
      const size_t index = relative - 2;
      selected = SelectedPrediction{
          closure.value(),
          closure_target->bytes[(index + 1) % closure_target->size],
          2};
    }
    if (!selected.has_value()) return;
    if (selected->source == 2 && relative < 2) {
      ++closing_before_offset_two_predictions_;
    }

    const uint8_t random = static_cast<uint8_t>(
        SplitMix64(event_key_ ^ (position_ << 1) ^
                   (static_cast<uint64_t>(selected->source) << 61) ^
                   0xd1b54a32d192ed03ULL) >> 56);
    const uint8_t negated = static_cast<uint8_t>(selected->treatment ^ 0xffU);
    Score(&d_, position_, selected->treatment, truth);
    Score(&r_, position_, random, truth);
    Score(&s_, position_, selected->shifted, truth);
    Score(&n_, position_, negated, truth);
    opportunity_digest_ = FnvU64(opportunity_digest_, position_);
    opportunity_digest_ = FnvByte(opportunity_digest_, selected->source);
    opportunity_digest_ = FnvByte(opportunity_digest_, selected->treatment);
    opportunity_digest_ = FnvByte(opportunity_digest_, random);
    opportunity_digest_ = FnvByte(opportunity_digest_, selected->shifted);
    opportunity_digest_ = FnvByte(opportunity_digest_, negated);
    opportunity_digest_ = FnvByte(opportunity_digest_, truth);
  }

  void CompleteEvent() {
    ++events_completed_;
    const ParsedEvent parsed = ParseEvent(event_);
    if (!parsed.valid) return;
    ++valid_events_;
    if (suppressed_depth_ == 0) table_.Observe(event_key_, parsed.signature);
    const uint64_t hash = EventHash(parsed);
    if (parsed.closing) {
      if (suppressed_depth_ > 0) {
        --suppressed_depth_;
        ++suppression_pops_;
      } else if (!stack_.empty() && stack_.back() == parsed.name) {
        stack_.pop_back();
        ++stack_pops_;
        previous_at_depth_[stack_.size()] = hash;
      } else {
        ++close_mismatches_;
      }
    } else if (!parsed.self_closing) {
      previous_at_depth_[stack_.size()] = hash;
      if (suppressed_depth_ > 0 || stack_.size() >= kMaxDepth) {
        ++suppressed_depth_;
        ++suppression_pushes_;
      } else {
        stack_.push_back(parsed.name);
        ++stack_pushes_;
        previous_at_depth_[stack_.size()] = 0;
      }
    } else {
      previous_at_depth_[stack_.size()] = hash;
    }
    AdvanceTransitionDigests(hash, 2);
  }

  void AdvanceTransitionDigests(uint64_t value, uint8_t event) {
    const auto advance = [value, event, this](uint64_t digest) {
      digest = FnvU64(digest, position_);
      digest = FnvByte(digest, event);
      digest = FnvU64(digest, value);
      digest = FnvU64(digest, event_key_);
      digest = FnvU64(digest, stack_.size());
      digest = FnvU64(digest, suppressed_depth_);
      return digest;
    };
    k_transition_digest_ = advance(k_transition_digest_);
    d_transition_digest_ = advance(d_transition_digest_);
  }

  uint64_t StackDigest() const {
    uint64_t value = kFnvOffset;
    value = FnvU64(value, stack_.size());
    value = FnvU64(value, suppressed_depth_);
    for (const Name& name : stack_) {
      value = FnvByte(value, name.size);
      for (size_t i = 0; i < name.size; ++i) {
        value = FnvByte(value, name.bytes[i]);
      }
    }
    for (uint64_t prior : previous_at_depth_) value = FnvU64(value, prior);
    value = FnvByte(value, in_event_ ? 1 : 0);
    for (uint8_t byte : event_) value = FnvByte(value, byte);
    return value;
  }

  int64_t MinimumThirdMargin() const {
    int64_t result = std::numeric_limits<int64_t>::max();
    for (size_t i = 0; i < 3; ++i) {
      const uint64_t control = std::max(
          {r_.thirds[i].correct, s_.thirds[i].correct,
           n_.thirds[i].correct});
      const int64_t margin = static_cast<int64_t>(d_.thirds[i].correct) -
                             static_cast<int64_t>(control);
      result = std::min(result, margin);
    }
    return result;
  }

  bool Verify() const {
    const auto total_active = [](const ArmCounts& arm) {
      uint64_t value = 0;
      for (const Counts& row : arm.thirds) value += row.active;
      return value;
    };
    const auto total_correct = [](const ArmCounts& arm) {
      uint64_t value = 0;
      for (const Counts& row : arm.thirds) value += row.correct;
      return value;
    };
    return transition_offset_zero_predictions_ == 0 &&
           closing_before_offset_two_predictions_ == 0 &&
           d_.active == r_.active && d_.active == s_.active &&
           d_.active == n_.active && d_.active <= c_.active + t_.active &&
           total_active(c_) == c_.active && total_correct(c_) == c_.correct &&
           total_active(t_) == t_.active && total_correct(t_) == t_.correct &&
           total_active(d_) == d_.active && total_correct(d_) == d_.correct &&
           total_active(r_) == r_.active && total_correct(r_) == r_.correct &&
           total_active(s_) == s_.active && total_correct(s_) == s_.correct &&
           total_active(n_) == n_.active && total_correct(n_) == n_.correct &&
           c_.correct <= c_.active && t_.correct <= t_.active &&
           d_.correct <= d_.active && r_.correct <= r_.active &&
           s_.correct <= s_.active && n_.correct <= n_.active &&
           k_transition_digest_ == d_transition_digest_ &&
           table_.installs() + table_.reinforcements() + table_.poisons() +
                   table_.poisoned_observations() <=
               valid_events_ &&
           stack_.size() <= kMaxDepth;
  }

  static void WriteArm(FILE* output, const char* name, const ArmCounts& arm,
                       bool trailing) {
    std::fprintf(output,
                 "    \"%s\": {\"active\": %" PRIu64
                 ", \"correct\": %" PRIu64 ", \"thirds\": [",
                 name, arm.active, arm.correct);
    for (size_t i = 0; i < arm.thirds.size(); ++i) {
      if (i != 0) std::fputc(',', output);
      std::fprintf(output,
                   "{\"active\": %" PRIu64 ", \"correct\": %" PRIu64 "}",
                   arm.thirds[i].active, arm.thirds[i].correct);
    }
    std::fprintf(output, "]}%s\n", trailing ? "," : "");
  }

  UnanimousTable table_;
  std::vector<Name> stack_;
  std::array<uint64_t, kMaxDepth + 1> previous_at_depth_{};
  size_t suppressed_depth_ = 0;
  bool in_event_ = false;
  bool single_quote_ = false;
  bool double_quote_ = false;
  bool unterminated_event_ = false;
  bool causal_and_verification_pass_ = false;
  std::vector<uint8_t> event_;
  std::optional<Signature> transition_target_;
  uint64_t position_ = 0;
  uint64_t event_key_ = 0;
  uint64_t events_started_ = 0;
  uint64_t events_completed_ = 0;
  uint64_t valid_events_ = 0;
  uint64_t malformed_events_ = 0;
  uint64_t close_mismatches_ = 0;
  uint64_t stack_pushes_ = 0;
  uint64_t stack_pops_ = 0;
  uint64_t suppression_pushes_ = 0;
  uint64_t suppression_pops_ = 0;
  uint64_t table_lookups_ = 0;
  uint64_t transition_offset_zero_predictions_ = 0;
  uint64_t closing_before_offset_two_predictions_ = 0;
  uint64_t input_digest_ = kFnvOffset;
  uint64_t opportunity_digest_ = kFnvOffset;
  uint64_t k_transition_digest_ = kFnvOffset;
  uint64_t d_transition_digest_ = kFnvOffset;
  ArmCounts c_;
  ArmCounts t_;
  ArmCounts d_;
  ArmCounts r_;
  ArmCounts s_;
  ArmCounts n_;
};

}  // namespace

int main(int argc, char** argv) {
  if (argc != 3) {
    std::fprintf(stderr, "usage: %s INPUT OUTPUT\n", argv[0]);
    return 2;
  }
  const int input = open(argv[1], O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (input < 0) Fail("open input");
  struct stat metadata = {};
  if (fstat(input, &metadata) != 0 || !S_ISREG(metadata.st_mode) ||
      metadata.st_size != static_cast<off_t>(kPopulationBytes)) {
    Fail("validate input");
  }
  const int output = open(argv[2], O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC |
                                       O_NOFOLLOW,
                          0600);
  if (output < 0) Fail("open output");
  FILE* stream = fdopen(output, "w");
  if (stream == nullptr) Fail("fdopen output");

  Scanner scanner;
  std::array<uint8_t, kReadBlock> buffer{};
  off_t file_offset = 0;
  while (true) {
    ssize_t count = read(input, buffer.data(), buffer.size());
    if (count < 0 && errno == EINTR) continue;
    if (count < 0) Fail("read input");
    if (count == 0) break;
    for (ssize_t index = 0; index < count; ++index) {
      scanner.Observe(buffer[static_cast<size_t>(index)]);
    }
    const int advice = posix_fadvise(input, file_offset, count,
                                     POSIX_FADV_DONTNEED);
    if (advice != 0) {
      errno = advice;
      Fail("fadvise consumed input");
    }
    file_offset += count;
  }
  if (close(input) != 0) Fail("close input");
  scanner.Finish();
  scanner.Write(stream);
  if (std::fflush(stream) != 0 || fsync(fileno(stream)) != 0 ||
      std::fclose(stream) != 0) {
    Fail("close output");
  }
  return 0;
}
