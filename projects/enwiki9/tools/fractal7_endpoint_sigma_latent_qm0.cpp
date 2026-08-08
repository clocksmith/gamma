#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

constexpr uint64_t kP1HeaderBytes = 16;
constexpr uint32_t kIndexBits = 21;
constexpr uint32_t kIndexSize = 1u << kIndexBits;
constexpr uint32_t kIndexMask = kIndexSize - 1;
constexpr int kPositions = 8;
constexpr int kStateCap = 128;
constexpr double kNewMass = 1.0 / 16.0;
constexpr double kMixerShare = 1.0 / 65536.0;
constexpr std::array<int, 3> kSuffixLengths{2, 4, 8};

uint64_t mix64(uint64_t value) {
  value ^= value >> 30;
  value *= 0xbf58476d1ce4e5b9ULL;
  value ^= value >> 27;
  value *= 0x94d049bb133111ebULL;
  return value ^ (value >> 31);
}

std::vector<uint8_t> read_bytes(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  input.seekg(0, std::ios::end);
  const auto size = input.tellg();
  if (size < 0) throw std::runtime_error("cannot size " + path);
  input.seekg(0, std::ios::beg);
  std::vector<uint8_t> output(static_cast<size_t>(size));
  input.read(reinterpret_cast<char*>(output.data()), size);
  if (!input) throw std::runtime_error("cannot read " + path);
  return output;
}

uint64_t little_u64(const uint8_t* data) {
  uint64_t value = 0;
  for (int i = 7; i >= 0; --i) value = (value << 8) | data[i];
  return value;
}

uint8_t wrt_byte(uint8_t value) {
  if (value >= static_cast<uint8_t>('{') && value < 127) {
    value = static_cast<uint8_t>(value + ('P' - '{'));
  } else if (value >= static_cast<uint8_t>('P') && value < static_cast<uint8_t>('T')) {
    value = static_cast<uint8_t>(value - ('P' - '{'));
  } else if ((value >= ':' && value <= '?') || (value >= 'J' && value <= 'O')) {
    value ^= 0x70;
  }
  if (value == 'X' || value == '`') value ^= static_cast<uint8_t>('X' ^ '`');
  return value;
}

struct Event {
  uint32_t start;
  uint32_t end;
  uint64_t symbol;
};

uint64_t bytes_hash(const uint8_t* data, size_t size) {
  uint64_t value = 0xcbf29ce484222325ULL ^ size;
  for (size_t i = 0; i < size; ++i) {
    value ^= data[i];
    value *= 0x100000001b3ULL;
  }
  return mix64(value);
}

std::vector<Event> parse_events(const std::vector<uint8_t>& stream) {
  if (stream.size() < 6 || stream[0] != 7 || stream[5] != 7) {
    throw std::runtime_error("invalid WRT stream header");
  }
  std::vector<Event> events;
  events.reserve(stream.size());
  uint32_t position = 6;
  while (position < stream.size()) {
    const uint32_t start = position;
    const uint8_t first = wrt_byte(stream[position++]);
    if (first == 0x0c) {
      if (position >= stream.size()) throw std::runtime_error("truncated escape");
      ++position;
    } else if (first >= 0x80 && first > 0xcf) {
      if (position >= stream.size()) throw std::runtime_error("truncated token");
      const uint8_t second = wrt_byte(stream[position++]);
      if (second > 0xcf) {
        if (position >= stream.size()) throw std::runtime_error("truncated token");
        ++position;
      }
    }
    events.push_back(Event{start, position, bytes_hash(stream.data() + start, position - start)});
  }
  return events;
}

class DirectIndex {
 public:
  DirectIndex() : keys_(kIndexSize), positions_(static_cast<size_t>(kIndexSize) * kPositions), counts_(kIndexSize), heads_(kIndexSize) {}

  void add(uint64_t key, uint32_t position) {
    key = key ? key : 1;
    const uint32_t slot = static_cast<uint32_t>(mix64(key)) & kIndexMask;
    if (keys_[slot] != key) {
      keys_[slot] = key;
      counts_[slot] = 0;
      heads_[slot] = 0;
    }
    const uint8_t head = heads_[slot];
    positions_[static_cast<size_t>(slot) * kPositions + head] = position;
    heads_[slot] = static_cast<uint8_t>((head + 1) % kPositions);
    counts_[slot] = std::min<uint8_t>(kPositions, static_cast<uint8_t>(counts_[slot] + 1));
  }

  std::vector<uint32_t> get(uint64_t key) const {
    key = key ? key : 1;
    const uint32_t slot = static_cast<uint32_t>(mix64(key)) & kIndexMask;
    if (keys_[slot] != key) return {};
    std::vector<uint32_t> output;
    const int count = counts_[slot];
    output.reserve(count);
    for (int offset = 0; offset < count; ++offset) {
      const int index = (heads_[slot] + kPositions - 1 - offset) % kPositions;
      output.push_back(positions_[static_cast<size_t>(slot) * kPositions + index]);
    }
    return output;
  }

 private:
  std::vector<uint64_t> keys_;
  std::vector<uint32_t> positions_;
  std::vector<uint8_t> counts_;
  std::vector<uint8_t> heads_;
};

uint64_t event_key(const std::vector<Event>& events, uint32_t target, int length) {
  uint64_t value = 0x243f6a8885a308d3ULL ^ static_cast<uint64_t>(length);
  for (uint32_t i = target - length; i < target; ++i) {
    value = mix64(value ^ events[i].symbol ^ (static_cast<uint64_t>(events[i].end - events[i].start) << 56));
  }
  return value ? value : 1;
}

bool exact_event_suffix(const std::vector<Event>& events, uint32_t a, uint32_t b, int length, const std::vector<uint8_t>& stream) {
  if (a < static_cast<uint32_t>(length) || b < static_cast<uint32_t>(length)) return false;
  for (int offset = 1; offset <= length; ++offset) {
    const Event& left = events[a - offset];
    const Event& right = events[b - offset];
    const size_t left_size = left.end - left.start;
    if (left_size != right.end - right.start || std::memcmp(stream.data() + left.start, stream.data() + right.start, left_size) != 0) return false;
  }
  return true;
}

struct State {
  uint64_t pointer_bit;
  double weight;
};

class SourcePopulation {
 public:
  void inject(const std::vector<uint64_t>& pointers) {
    if (pointers.empty()) return;
    const double old_mass = states_.empty() ? 0.0 : 1.0 - kNewMass;
    for (auto& state : states_) state.weight *= old_mass;
    const double each = (states_.empty() ? 1.0 : kNewMass) / pointers.size();
    for (uint64_t pointer : pointers) states_.push_back(State{pointer, each});
    merge_and_cap();
  }

  bool active(uint64_t current_bit) {
    states_.erase(std::remove_if(states_.begin(), states_.end(), [current_bit](const State& state) { return state.pointer_bit >= current_bit; }), states_.end());
    normalize();
    return !states_.empty();
  }

  double probability_one(const std::vector<uint8_t>& stream) const {
    double one = 0.0;
    for (const auto& state : states_) {
      const uint8_t byte = stream[state.pointer_bit >> 3];
      const int bit = (byte >> (7 - (state.pointer_bit & 7))) & 1;
      if (bit) one += state.weight;
    }
    return std::clamp(one, 0.0, 1.0);
  }

  void observe(int truth, const std::vector<uint8_t>& stream) {
    states_.erase(std::remove_if(states_.begin(), states_.end(), [&](const State& state) {
      const uint8_t byte = stream[state.pointer_bit >> 3];
      return ((byte >> (7 - (state.pointer_bit & 7))) & 1) != truth;
    }), states_.end());
    for (auto& state : states_) ++state.pointer_bit;
    merge_and_cap();
  }

  int support_bucket() const {
    const size_t count = states_.size();
    if (count <= 1) return 0;
    return std::min(5, static_cast<int>(std::log2(static_cast<double>(count))));
  }

  int concentration_bucket() const {
    double maximum = 0.0;
    for (const auto& state : states_) maximum = std::max(maximum, state.weight);
    if (maximum < 0.5) return 0;
    if (maximum < 0.75) return 1;
    if (maximum < 0.9375) return 2;
    return 3;
  }

 private:
  void normalize() {
    double sum = 0.0;
    for (const auto& state : states_) sum += state.weight;
    if (!(sum > 0.0)) {
      states_.clear();
      return;
    }
    for (auto& state : states_) state.weight /= sum;
  }

  void merge_and_cap() {
    std::sort(states_.begin(), states_.end(), [](const State& a, const State& b) { return a.pointer_bit < b.pointer_bit; });
    std::vector<State> merged;
    for (const auto& state : states_) {
      if (!merged.empty() && merged.back().pointer_bit == state.pointer_bit) merged.back().weight += state.weight;
      else merged.push_back(state);
    }
    if (merged.size() > kStateCap) {
      std::nth_element(merged.begin(), merged.begin() + kStateCap, merged.end(), [](const State& a, const State& b) { return a.weight > b.weight; });
      merged.resize(kStateCap);
    }
    states_.swap(merged);
    normalize();
  }

  std::vector<State> states_;
};

struct Mixer {
  double base = 0.999;
  double echo = 0.001;

  double predict(double base_p1, double echo_p1) const {
    return std::clamp(base * base_p1 + echo * echo_p1, 1e-15, 1.0 - 1e-15);
  }

  void observe(double base_truth, double echo_truth) {
    base *= base_truth;
    echo *= echo_truth;
    const double sum = base + echo;
    if (!(sum > 0.0) || !std::isfinite(sum)) {
      base = 0.999;
      echo = 0.001;
      return;
    }
    base /= sum;
    echo /= sum;
    base = (1.0 - 2.0 * kMixerShare) * base + kMixerShare;
    echo = 1.0 - base;
  }
};

struct Arm {
  std::string name;
  SourcePopulation population;
  std::array<Mixer, 6 * 4 * 8> mixers{};
  double candidate_bits = 0.0;
  double oracle_bits = 0.0;
  std::array<double, 3> candidate_thirds{};
  uint64_t active_bits = 0;
  uint64_t opportunities = 0;

  void inject(const std::vector<uint64_t>& pointers) {
    if (!pointers.empty()) ++opportunities;
    population.inject(pointers);
  }

  void bit(uint64_t current_bit, int truth, uint16_t p1, const std::vector<uint8_t>& stream, double base_cost, int third) {
    const double base_p1 = static_cast<double>(p1) / 65536.0;
    const double base_truth = truth ? base_p1 : 1.0 - base_p1;
    if (!population.active(current_bit)) {
      candidate_bits += base_cost;
      oracle_bits += base_cost;
      candidate_thirds[third] += base_cost;
      return;
    }
    ++active_bits;
    const double echo_p1 = population.probability_one(stream);
    const double echo_truth = truth ? echo_p1 : 1.0 - echo_p1;
    const int bucket = (population.support_bucket() * 4 + population.concentration_bucket()) * 8 + static_cast<int>(current_bit & 7);
    Mixer& mixer = mixers[bucket];
    const double prediction = mixer.predict(base_p1, echo_p1);
    const double truth_probability = truth ? prediction : 1.0 - prediction;
    const double cost = -std::log2(truth_probability);
    candidate_bits += cost;
    candidate_thirds[third] += cost;
    const double echo_cost = echo_truth > 0.0 ? -std::log2(echo_truth) : std::numeric_limits<double>::infinity();
    oracle_bits += std::min(base_cost, echo_cost);
    mixer.observe(base_truth, echo_truth);
    population.observe(truth, stream);
  }
};

std::vector<uint64_t> event_sources(const std::vector<Event>& events, const std::vector<uint8_t>& stream, uint32_t target, const std::array<DirectIndex, 3>& indexes) {
  std::vector<uint64_t> output;
  for (int lane = 2; lane >= 0; --lane) {
    const int length = kSuffixLengths[lane];
    if (target < static_cast<uint32_t>(length)) continue;
    for (uint32_t source : indexes[lane].get(event_key(events, target, length))) {
      if (source >= target || !exact_event_suffix(events, target, source, length, stream)) continue;
      const uint64_t pointer = static_cast<uint64_t>(events[source].start) * 8;
      if (std::find(output.begin(), output.end(), pointer) == output.end()) output.push_back(pointer);
    }
  }
  return output;
}

std::vector<uint16_t> load_p1(const std::string& path, uint64_t expected_rows) {
  const auto bytes = read_bytes(path);
  if (bytes.size() < kP1HeaderBytes || std::memcmp(bytes.data(), "CMX21P1\0", 8) != 0) throw std::runtime_error("invalid P1 header");
  const uint64_t rows = little_u64(bytes.data() + 8);
  if (rows != expected_rows || bytes.size() != kP1HeaderBytes + rows * 2) throw std::runtime_error("P1 length mismatch");
  std::vector<uint16_t> output(rows);
  for (uint64_t i = 0; i < rows; ++i) output[i] = static_cast<uint16_t>(bytes[16 + 2 * i] | (static_cast<uint16_t>(bytes[17 + 2 * i]) << 8));
  return output;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 3) {
      std::cerr << "usage: " << argv[0] << " STORE P1\n";
      return 2;
    }
    const auto stored = read_bytes(argv[1]);
    if (stored.size() < 11 || stored[1] != 0 || stored[2] != 0 || stored[3] != 0 || stored[4] != 0) throw std::runtime_error("expected full WRT store");
    const std::vector<uint8_t> stream(stored.begin() + 5, stored.end());
    const auto events = parse_events(stream);
    const auto p1 = load_p1(argv[2], static_cast<uint64_t>(stream.size()) * 8);

    std::array<DirectIndex, 3> event_indexes;
    DirectIndex byte_index;
    Arm sigma{"SIGMA"}, recency{"RECENCY"}, shuffled{"SHUFFLED"}, byte8{"BYTE8"};
    std::array<Arm*, 4> arms{&sigma, &recency, &shuffled, &byte8};
    double base_bits = 0.0;
    std::array<double, 3> base_thirds{};

    auto process_plain_bit = [&](uint64_t bit_index) {
      const int truth = (stream[bit_index >> 3] >> (7 - (bit_index & 7))) & 1;
      const double probability = truth ? static_cast<double>(p1[bit_index]) / 65536.0 : 1.0 - static_cast<double>(p1[bit_index]) / 65536.0;
      const double cost = -std::log2(probability);
      base_bits += cost;
      const int third = std::min(2, static_cast<int>((bit_index >> 3) * 3 / stream.size()));
      base_thirds[third] += cost;
      for (Arm* arm : arms) {
        arm->candidate_bits += cost;
        arm->oracle_bits += cost;
        arm->candidate_thirds[third] += cost;
      }
    };
    for (uint64_t bit = 0; bit < 48; ++bit) process_plain_bit(bit);

    for (uint32_t target = 0; target < events.size(); ++target) {
      const Event& event = events[target];
      const auto sources = event_sources(events, stream, target, event_indexes);
      sigma.inject(sources);
      if (!sources.empty()) recency.inject({sources.front()});
      std::vector<uint64_t> shuffled_sources;
      shuffled_sources.reserve(sources.size());
      for (size_t i = 0; i < sources.size(); ++i) {
        if (target == 0) break;
        const uint32_t mapped = static_cast<uint32_t>(mix64((static_cast<uint64_t>(target) << 32) ^ sources[i] ^ i) % target);
        shuffled_sources.push_back(static_cast<uint64_t>(events[mapped].start) * 8);
      }
      shuffled.inject(shuffled_sources);
      std::vector<uint64_t> byte_sources;
      if (event.start >= 8) {
        const uint64_t key = bytes_hash(stream.data() + event.start - 8, 8);
        for (uint32_t source : byte_index.get(key)) {
          if (source >= event.start || std::memcmp(stream.data() + source - 8, stream.data() + event.start - 8, 8) != 0) continue;
          byte_sources.push_back(static_cast<uint64_t>(source) * 8);
        }
      }
      byte8.inject(byte_sources);

      for (uint64_t bit = static_cast<uint64_t>(event.start) * 8; bit < static_cast<uint64_t>(event.end) * 8; ++bit) {
        const int truth = (stream[bit >> 3] >> (7 - (bit & 7))) & 1;
        const double probability = truth ? static_cast<double>(p1[bit]) / 65536.0 : 1.0 - static_cast<double>(p1[bit]) / 65536.0;
        const double base_cost = -std::log2(probability);
        base_bits += base_cost;
        const int third = std::min(2, static_cast<int>((bit >> 3) * 3 / stream.size()));
        base_thirds[third] += base_cost;
        for (Arm* arm : arms) arm->bit(bit, truth, p1[bit], stream, base_cost, third);
      }

      for (int lane = 0; lane < 3; ++lane) {
        const int length = kSuffixLengths[lane];
        if (target >= static_cast<uint32_t>(length)) event_indexes[lane].add(event_key(events, target, length), target);
      }
      for (uint32_t position = event.start; position < event.end; ++position) {
        if (position >= 8) byte_index.add(bytes_hash(stream.data() + position - 8, 8), position);
      }
    }

    auto gain = [&](const Arm& arm) { return (base_bits - arm.candidate_bits) / 8.0; };
    auto ceiling = [&](const Arm& arm) { return (base_bits - arm.oracle_bits) / 8.0; };
    const double sigma_gain = gain(sigma);
    const double sigma_ceiling = ceiling(sigma);
    bool thirds_positive = true;
    for (int i = 0; i < 3; ++i) thirds_positive = thirds_positive && (base_thirds[i] - sigma.candidate_thirds[i] > 0.0);
    double minimum_gain_margin = std::numeric_limits<double>::infinity();
    double minimum_ceiling_margin = std::numeric_limits<double>::infinity();
    for (Arm* control : std::array<Arm*, 3>{&recency, &shuffled, &byte8}) {
      minimum_gain_margin = std::min(minimum_gain_margin, sigma_gain - gain(*control));
      minimum_ceiling_margin = std::min(minimum_ceiling_margin, sigma_ceiling - ceiling(*control));
    }
    const bool passed = sigma_ceiling >= 100000.0 && minimum_ceiling_margin >= 20000.0 && sigma_gain >= 75000.0 && minimum_gain_margin >= 10000.0 && thirds_positive;

    std::cout << std::fixed << std::setprecision(6);
    std::cout << "{\n  \"schema\": \"fractal7_endpoint_sigma_latent_qm0_v1\",\n";
    std::cout << "  \"evidence_level\": \"zero_credit_exact_parent_codelength_screen\",\n";
    std::cout << "  \"scope\": {\"wrt_stream_bytes\": " << stream.size() << ", \"wrt_events\": " << events.size() << ", \"p1_rows\": " << p1.size() << "},\n";
    std::cout << "  \"base_ideal_bytes\": " << base_bits / 8.0 << ",\n  \"arms\": {\n";
    for (size_t index = 0; index < arms.size(); ++index) {
      const Arm& arm = *arms[index];
      std::cout << "    \"" << arm.name << "\": {\"causal_gain_bytes\": " << gain(arm) << ", \"free_selector_ceiling_bytes\": " << ceiling(arm) << ", \"active_bits\": " << arm.active_bits << ", \"opportunities\": " << arm.opportunities << ", \"chronological_gain_bytes\": [";
      for (int i = 0; i < 3; ++i) {
        if (i) std::cout << ", ";
        std::cout << (base_thirds[i] - arm.candidate_thirds[i]) / 8.0;
      }
      std::cout << "]}" << (index + 1 == arms.size() ? "\n" : ",\n");
    }
    std::cout << "  },\n  \"gates\": {\"sigma_ceiling_at_least_100000\": " << (sigma_ceiling >= 100000.0 ? "true" : "false") << ", \"minimum_ceiling_control_margin_bytes\": " << minimum_ceiling_margin << ", \"sigma_causal_gain_at_least_75000\": " << (sigma_gain >= 75000.0 ? "true" : "false") << ", \"minimum_causal_control_margin_bytes\": " << minimum_gain_margin << ", \"all_chronological_thirds_positive\": " << (thirds_positive ? "true" : "false") << ", \"passed\": " << (passed ? "true" : "false") << "},\n";
    std::cout << "  \"verdict\": \"" << (passed ? "authorize_exact_paid_codec" : "retire_frozen_endpoint_sigma_realization") << "\",\n";
    std::cout << "  \"score_credit_bytes\": 0,\n  \"claim_boundary\": \"Ideal finite codelength screen only; no arithmetic archive, decoder, package, raw roundtrip, transfer, or full-corpus score.\"\n}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
