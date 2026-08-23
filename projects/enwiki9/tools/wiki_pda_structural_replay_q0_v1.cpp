#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr unsigned char kLessThan = 'L';
constexpr unsigned char kGreaterThan = 'N';
constexpr std::size_t kMaxName = 16;
constexpr std::size_t kMaxDepth = 16;
constexpr std::size_t kMaxEvent = 4096;
constexpr std::size_t kTableEntries = 1024;
constexpr std::size_t kMaxSignature = 19;

uint64_t Fnv1a(const unsigned char* data, std::size_t size) {
  uint64_t value = 1469598103934665603ULL;
  for (std::size_t i = 0; i < size; ++i) {
    value ^= data[i];
    value *= 1099511628211ULL;
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
  std::array<unsigned char, kMaxName> bytes{};
  uint8_t size = 0;

  bool operator==(const Name& other) const {
    return size == other.size &&
        std::equal(bytes.begin(), bytes.begin() + size, other.bytes.begin());
  }

  uint64_t Hash() const { return Fnv1a(bytes.data(), size); }
};

struct Signature {
  std::array<unsigned char, kMaxSignature> bytes{};
  uint8_t size = 0;

  bool operator==(const Signature& other) const {
    return size == other.size &&
        std::equal(bytes.begin(), bytes.begin() + size, other.bytes.begin());
  }
};

struct ParsedEvent {
  bool valid = false;
  bool closing = false;
  bool self_closing = false;
  Name name;
  Signature signature;
};

bool IsNameTerminator(unsigned char value) {
  return value == ' ' || value == '\t' || value == '\r' || value == '\n' ||
      value == '/' || value == kGreaterThan;
}

ParsedEvent ParseEvent(const std::vector<unsigned char>& event) {
  ParsedEvent parsed;
  if (event.size() < 3 || event.front() != kLessThan ||
      event.back() != kGreaterThan) {
    return parsed;
  }
  std::size_t position = 1;
  if (event[position] == '!' || event[position] == '?') return parsed;
  if (event[position] == '/') {
    parsed.closing = true;
    ++position;
  }
  const std::size_t name_start = position;
  while (position < event.size() && !IsNameTerminator(event[position])) {
    ++position;
  }
  const std::size_t name_size = position - name_start;
  if (name_size == 0 || name_size > kMaxName) return parsed;
  parsed.name.size = static_cast<uint8_t>(name_size);
  std::copy(event.begin() + name_start, event.begin() + position,
            parsed.name.bytes.begin());

  std::size_t last = event.size() - 1;
  while (last > position &&
         (event[last - 1] == ' ' || event[last - 1] == '\t' ||
          event[last - 1] == '\r' || event[last - 1] == '\n')) {
    --last;
  }
  parsed.self_closing = !parsed.closing && last > position && event[last - 1] == '/';

  parsed.signature.bytes[parsed.signature.size++] = kLessThan;
  if (parsed.closing) parsed.signature.bytes[parsed.signature.size++] = '/';
  for (std::size_t i = 0; i < name_size; ++i) {
    parsed.signature.bytes[parsed.signature.size++] = parsed.name.bytes[i];
  }
  if (position == event.size() - 1) {
    parsed.signature.bytes[parsed.signature.size++] = kGreaterThan;
  }
  parsed.valid = true;
  return parsed;
}

struct TableEntry {
  uint64_t key = 0;
  uint8_t state = 0;  // 0 empty, 1 exact, 2 poisoned
  Signature target;
};

class UnanimousTable {
 public:
  const Signature* Lookup(uint64_t key) const {
    const TableEntry& entry = entries_[key & (kTableEntries - 1)];
    return entry.state == 1 && entry.key == key ? &entry.target : nullptr;
  }

  void Observe(uint64_t key, const Signature& target) {
    TableEntry& entry = entries_[key & (kTableEntries - 1)];
    if (entry.state == 0) {
      entry.key = key;
      entry.target = target;
      entry.state = 1;
      return;
    }
    if (entry.state == 2) return;
    if (entry.key != key || !(entry.target == target)) entry.state = 2;
  }

 private:
  std::array<TableEntry, kTableEntries> entries_{};
};

struct Counters {
  uint64_t opportunities = 0;
  uint64_t correct = 0;
  uint64_t incorrect = 0;
  uint64_t predicted_events = 0;
  uint64_t exact_events = 0;
  std::array<uint64_t, 3> correct_by_third{};
};

using Prediction = std::vector<std::optional<unsigned char>>;

void ApplySignature(Prediction& prediction, std::size_t offset,
                    const Signature& signature, bool preserve_existing) {
  if (prediction.size() < offset + signature.size) {
    prediction.resize(offset + signature.size);
  }
  for (std::size_t i = 0; i < signature.size; ++i) {
    if (!preserve_existing || !prediction[offset + i].has_value()) {
      prediction[offset + i] = signature.bytes[i];
    }
  }
}

Signature RandomSignature(uint64_t key, std::size_t size) {
  Signature result;
  result.size = static_cast<uint8_t>(std::min(size, kMaxSignature));
  uint64_t state = key;
  for (std::size_t i = 0; i < result.size; ++i) {
    if ((i & 7U) == 0) state = SplitMix64(state + i);
    result.bytes[i] = static_cast<unsigned char>(state >> (8 * (i & 7U)));
  }
  return result;
}

Signature NameClosure(const Name& name) {
  Signature result;
  for (std::size_t i = 0; i < name.size; ++i) {
    result.bytes[result.size++] = name.bytes[i];
  }
  result.bytes[result.size++] = kGreaterThan;
  return result;
}

void Score(const Prediction& prediction, const std::vector<unsigned char>& actual,
           uint64_t event_position, uint64_t score_start, uint64_t score_end,
           Counters& counters) {
  bool predicted = false;
  bool exact = true;
  for (std::size_t i = 0; i < prediction.size(); ++i) {
    if (!prediction[i].has_value()) continue;
    const uint64_t position = event_position + i;
    if (position < score_start || position >= score_end) continue;
    predicted = true;
    ++counters.opportunities;
    if (i < actual.size() && prediction[i].value() == actual[i]) {
      ++counters.correct;
      const uint64_t span = score_end - score_start;
      const std::size_t third = span == 0 ? 0 : std::min<uint64_t>(
          2, ((position - score_start) * 3) / span);
      ++counters.correct_by_third[third];
    } else {
      ++counters.incorrect;
      exact = false;
    }
  }
  if (predicted) {
    ++counters.predicted_events;
    if (exact) ++counters.exact_events;
  }
}

uint64_t ComposeState(uint64_t parent, uint64_t previous, std::size_t depth) {
  uint64_t value = SplitMix64(parent ^ 0x5752545044410001ULL);
  value ^= SplitMix64(previous ^ 0x5752545044410002ULL);
  value ^= SplitMix64(static_cast<uint64_t>(depth) ^ 0x5752545044410003ULL);
  return SplitMix64(value);
}

uint64_t EventHash(const ParsedEvent& event) {
  return SplitMix64(event.name.Hash() ^
                    (event.closing ? 0x434c4f53494e4701ULL : 0x4f50454e494e4701ULL));
}

void PrintCounters(const char* name, const Counters& value, bool trailing) {
  std::cout << "    \"" << name << "\": {\n"
            << "      \"opportunities\": " << value.opportunities << ",\n"
            << "      \"correct\": " << value.correct << ",\n"
            << "      \"incorrect\": " << value.incorrect << ",\n"
            << "      \"predicted_events\": " << value.predicted_events << ",\n"
            << "      \"exact_events\": " << value.exact_events << ",\n"
            << "      \"correct_by_third\": [" << value.correct_by_third[0]
            << ", " << value.correct_by_third[1] << ", "
            << value.correct_by_third[2] << "]\n"
            << "    }" << (trailing ? "," : "") << "\n";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    std::string input_path;
    uint64_t score_start = 0;
    uint64_t score_end = std::numeric_limits<uint64_t>::max();
    uint64_t required_gross = 4079243;
    for (int i = 1; i < argc; ++i) {
      const std::string argument = argv[i];
      if (argument == "--input" && i + 1 < argc) input_path = argv[++i];
      else if (argument == "--score-start" && i + 1 < argc)
        score_start = std::stoull(argv[++i]);
      else if (argument == "--score-end" && i + 1 < argc)
        score_end = std::stoull(argv[++i]);
      else if (argument == "--required-gross" && i + 1 < argc)
        required_gross = std::stoull(argv[++i]);
      else throw std::runtime_error("invalid arguments");
    }
    if (input_path.empty() || score_end <= score_start) {
      throw std::runtime_error("--input and a nonempty score range are required");
    }
    std::ifstream input(input_path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot open input");

    UnanimousTable correct_table;
    UnanimousTable shifted_table;
    std::vector<Name> stack;
    std::array<uint64_t, kMaxDepth + 1> previous_at_depth{};
    std::optional<Signature> previous_event;
    std::optional<Name> previous_closed;
    std::size_t suppressed_depth = 0;
    uint64_t position = 0;
    uint64_t events = 0;
    uint64_t valid_events = 0;
    uint64_t malformed_events = 0;
    uint64_t close_mismatches = 0;
    Counters closure_d;
    Counters transition_d;
    Counters d;
    Counters r;
    Counters s;

    bool in_event = false;
    bool single_quote = false;
    bool double_quote = false;
    uint64_t event_position = 0;
    uint64_t event_key = 0;
    const Signature* transition_prediction = nullptr;
    const Signature* shifted_prediction = nullptr;
    std::vector<unsigned char> event;
    event.reserve(128);

    char raw = 0;
    while (position < score_end && input.get(raw)) {
      const unsigned char value = static_cast<unsigned char>(raw);
      if (!in_event) {
        if (value == kLessThan) {
          in_event = true;
          single_quote = false;
          double_quote = false;
          event.clear();
          event.push_back(value);
          event_position = position;
          const uint64_t parent = stack.empty() ? 0 : stack.back().Hash();
          const std::size_t depth = stack.size();
          event_key = ComposeState(parent, previous_at_depth[depth], depth);
          transition_prediction = suppressed_depth == 0 ? correct_table.Lookup(event_key) : nullptr;
          shifted_prediction = suppressed_depth == 0 ? shifted_table.Lookup(event_key) : nullptr;
        }
        ++position;
        continue;
      }

      event.push_back(value);
      if (value == '\'' && !double_quote) single_quote = !single_quote;
      if (value == '"' && !single_quote) double_quote = !double_quote;
      const bool terminal = value == kGreaterThan && !single_quote && !double_quote;
      if (event.size() > kMaxEvent) {
        ++malformed_events;
        in_event = false;
        event.clear();
      } else if (terminal) {
        ++events;
        const ParsedEvent parsed = ParseEvent(event);
        if (parsed.valid) {
          ++valid_events;
          Prediction pred_d;
          Prediction pred_r;
          Prediction pred_s;
          Prediction pred_transition;
          Prediction pred_closure;

          if (transition_prediction != nullptr) {
            ApplySignature(pred_d, 0, *transition_prediction, false);
            ApplySignature(pred_transition, 0, *transition_prediction, false);
            const Signature random = RandomSignature(event_key, transition_prediction->size);
            ApplySignature(pred_r, 0, random, false);
          }
          if (shifted_prediction != nullptr) {
            ApplySignature(pred_s, 0, *shifted_prediction, false);
          }

          if (parsed.closing && suppressed_depth == 0 && !stack.empty()) {
            const Signature closure = NameClosure(stack.back());
            ApplySignature(pred_d, 2, closure, true);
            ApplySignature(pred_closure, 2, closure, false);
            const Signature random = RandomSignature(event_key ^ 0x434c4f5355524501ULL,
                                                      closure.size);
            ApplySignature(pred_r, 2, random, true);
            if (previous_closed.has_value()) {
              const Signature shifted = NameClosure(previous_closed.value());
              ApplySignature(pred_s, 2, shifted, true);
            }
          }

          Score(pred_closure, event, event_position, score_start, score_end, closure_d);
          Score(pred_transition, event, event_position, score_start, score_end, transition_d);
          Score(pred_d, event, event_position, score_start, score_end, d);
          Score(pred_r, event, event_position, score_start, score_end, r);
          Score(pred_s, event, event_position, score_start, score_end, s);

          if (suppressed_depth == 0) {
            correct_table.Observe(event_key, parsed.signature);
            if (previous_event.has_value()) {
              shifted_table.Observe(event_key, previous_event.value());
            }
          }
          previous_event = parsed.signature;
          const uint64_t hash = EventHash(parsed);

          if (parsed.closing) {
            if (suppressed_depth > 0) {
              --suppressed_depth;
            } else if (!stack.empty() && stack.back() == parsed.name) {
              previous_closed = parsed.name;
              stack.pop_back();
              previous_at_depth[stack.size()] = hash;
            } else {
              ++close_mismatches;
            }
          } else if (!parsed.self_closing) {
            previous_at_depth[stack.size()] = hash;
            if (suppressed_depth > 0 || stack.size() >= kMaxDepth) {
              ++suppressed_depth;
            } else {
              stack.push_back(parsed.name);
              previous_at_depth[stack.size()] = 0;
            }
          } else {
            previous_at_depth[stack.size()] = hash;
          }
        }
        in_event = false;
        event.clear();
      }
      ++position;
    }

    const bool thirds_pass = std::all_of(d.correct_by_third.begin(),
                                         d.correct_by_third.end(),
                                         [](uint64_t value) { return value > 0; });
    const bool absolute_pass = d.correct >= required_gross && thirds_pass &&
                               d.correct > r.correct && d.correct > s.correct;
    std::cout << "{\n"
              << "  \"schema\": \"gamma.enwiki9.wiki_pda_structural_replay_scan.v1\",\n"
              << "  \"claim_authority\": \"none\",\n"
              << "  \"input_path\": \"" << input_path << "\",\n"
              << "  \"bytes_processed\": " << position << ",\n"
              << "  \"score_start\": " << score_start << ",\n"
              << "  \"score_end\": " << score_end << ",\n"
              << "  \"events\": " << events << ",\n"
              << "  \"valid_events\": " << valid_events << ",\n"
              << "  \"malformed_events\": " << malformed_events << ",\n"
              << "  \"close_mismatches\": " << close_mismatches << ",\n"
              << "  \"required_gross_savings_bytes\": " << required_gross << ",\n"
              << "  \"arms\": {\n";
    PrintCounters("C", closure_d, true);
    PrintCounters("T", transition_d, true);
    PrintCounters("D", d, true);
    PrintCounters("R", r, true);
    PrintCounters("S", s, false);
    std::cout << "  },\n"
              << "  \"absolute_eight_bit_ceiling_bytes\": " << d.correct << ",\n"
              << "  \"all_thirds_positive\": " << (thirds_pass ? "true" : "false") << ",\n"
              << "  \"absolute_ceiling_pass\": " << (absolute_pass ? "true" : "false") << ",\n"
              << "  \"promotion_authorized\": false,\n"
              << "  \"next_authority\": \"donor-surprise tracing only if two exact scans pass\"\n"
              << "}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
