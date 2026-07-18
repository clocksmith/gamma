// Emit causal P1 endpoints from compact hashed mixers over FX2-lite FXCM.
//
// Build this file against the dependency-closed fx2lite endpoint source.  The
// FXCM object already computes 431 probabilities to expose slot 428.  These
// probes reuse that live vector, project it through a deterministic signed
// feature hash, and train small logistic mixers from decoded truth.  No
// offline weights or trace data enter the emitted endpoint.

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <utility>
#include <valarray>
#include <vector>

#include "mixer/byte-mixer.h"
#include "mixer/lstm.h"
#include "models/fxcmv1.h"
#include "models/ppmd.h"


int lstmpr = 0;
int lstmex = 0;

extern const unsigned char wrt_2b[256];
extern const unsigned char wrt_3b[256];

namespace {

constexpr unsigned int kEndpointIndex = 428;
constexpr unsigned int kSeed = 923;
constexpr int kDiscardedIndirectModelCount = 16;
constexpr int kPpmdOrder = 25;
constexpr int kPpmdMemoryMb = 20;
constexpr unsigned int kFxcmOutputs = 431;
constexpr unsigned int kMaxHashDimensions = 64;
constexpr unsigned int kFullFeatureCount = kFxcmOutputs + 3;
constexpr unsigned int kMxxContexts = 512;
constexpr std::uint64_t kDecayT0 = 1000000;
constexpr std::uint64_t kDecayT1 = 5000000;

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    std::cerr << "cannot open " << path << "\n";
    std::exit(2);
  }
  input.seekg(0, std::ios::end);
  const std::streamoff size = input.tellg();
  input.seekg(0, std::ios::beg);
  std::vector<unsigned char> data(static_cast<std::size_t>(size));
  input.read(reinterpret_cast<char*>(data.data()), size);
  if (!input) {
    std::cerr << "cannot read " << path << "\n";
    std::exit(2);
  }
  return data;
}

std::uint16_t Discretize(float probability) {
  if (probability <= 0.0f) return 1;
  if (probability >= 1.0f) return 65535;
  return static_cast<std::uint16_t>(1 + 65534 * probability);
}

float Logit(float probability) {
  probability = std::max(0.0001f, std::min(0.9999f, probability));
  return std::log(probability / (1.0f - probability));
}

struct MxxState {
  unsigned int bit_context = 1;
  unsigned long long long_bit_context = 1;
  unsigned int bpos = 0;
  unsigned long long b2stream = 0;
  unsigned long long b3stream = 0;
  unsigned long long stream2b_r = 0;
  unsigned int old_2b_state = 0;
  unsigned int old_3b_state = 0;
  unsigned long long stream3b_r = 0;
  unsigned int mxx = 0;

  void Observe(int bit) {
    bit_context += bit_context + static_cast<unsigned int>(bit);
    long_bit_context = bit_context;
    if (bit_context >= 256) {
      bit_context -= 256;
      long_bit_context = 1;
      const unsigned char value = static_cast<unsigned char>(bit_context);
      if (value == 'R' || value == 'P' || value == ']') {
        b3stream = (b3stream & ~7ULL) + 3;
      } else if (value == 'M') {
        b3stream = (b3stream & ~7ULL) + 4;
      }
      const unsigned int next_2b = wrt_2b[value];
      b2stream = b2stream * 4 + next_2b;
      const unsigned int next_3b = wrt_3b[value];
      b3stream = b3stream * 8 + next_3b;
      if (old_3b_state != next_3b) {
        stream3b_r = stream3b_r * 8 + next_3b;
        old_3b_state = next_3b;
      }
      if (value == 10 || value == ')') b3stream <<= 6;
      if (value == 'Q') b3stream = b3stream * 8 + wrt_3b[value];
      if (old_2b_state != next_2b) {
        stream2b_r = stream2b_r * 4 + next_2b;
        old_2b_state = next_2b;
      }
    }

    bpos = (bpos + 1) & 7;
    if (bpos == 0) {
      mxx = (stream2b_r & 63) * 8 + (b3stream & 7);
    } else if (bpos > 3) {
      const unsigned int partial =
          static_cast<unsigned int>((long_bit_context << (8 - bpos)) & 255);
      mxx = static_cast<unsigned int>(((b2stream << 2) & 63) +
          wrt_2b[partial] * 8 + (b3stream & 7));
    } else {
      mxx = static_cast<unsigned int>((stream2b_r & 63) * 8 +
          (b3stream & 7));
    }
    if (mxx >= kMxxContexts) std::abort();
  }
};

class Endpoint428Features {
 public:
  explicit Endpoint428Features(const std::vector<bool>& vocab)
      : bit_context_(1), fxcm_(), ppmd_prediction_(0.5f),
        byte_prediction_(0.0f) {
    ppmd_.reset(new PPMD::PPMD(
        kPpmdOrder, kPpmdMemoryMb, bit_context_, vocab));
    for (int index = 0; index < kDiscardedIndirectModelCount; ++index) {
      static_cast<void>(std::rand());
    }
    unsigned int vocab_size = 0;
    for (bool present : vocab) {
      if (present) ++vocab_size;
    }
    byte_mixer_.reset(new ByteMixer(
        1, bit_context_, vocab, vocab_size,
        new Lstm(vocab_size, vocab_size, 200, 1, 128, 0.03f, 10.0f)));
  }

  const std::valarray<float>& Predict() {
    const std::valarray<float>& probabilities = fxcm_.Predict();
    if (probabilities.size() != kFxcmOutputs) std::abort();
    ppmd_prediction_ = ppmd_->Predict()[0];
    return probabilities;
  }

  float ppmd_prediction() const { return ppmd_prediction_; }
  float byte_prediction() const { return byte_prediction_; }

  void Perceive(int bit) {
    ppmd_->Perceive(bit);
    byte_mixer_->Perceive(bit);
    const bool byte_update = bit_context_ >= 128;
    bit_context_ += bit_context_ + static_cast<unsigned int>(bit);
    if (bit_context_ >= 256) bit_context_ -= 256;
    if (byte_update) {
      ppmd_->ByteUpdate();
      const std::valarray<float>& probabilities = ppmd_->BytePredict();
      for (unsigned int value = 0; value < 256; ++value) {
        byte_mixer_->SetInput(value, probabilities[value]);
      }
      byte_mixer_->ByteUpdate();
    }
    byte_prediction_ = byte_mixer_->Predict()[0];
    lstmpr = 1 + 4094 * byte_prediction_;
    lstmex = byte_mixer_->ex;
    fxcm_.Perceive(bit);
    if (byte_update) bit_context_ = 1;
  }

  void Pretrain(int bit) {
    fxcm_.Predict();
    fxcm_.Perceive(bit);
    const bool byte_update = bit_context_ >= 128;
    bit_context_ += bit_context_ + static_cast<unsigned int>(bit);
    if (bit_context_ >= 256) bit_context_ -= 256;
    if (byte_update) bit_context_ = 1;
  }

 private:
  unsigned int bit_context_;
  FXCM fxcm_;
  std::unique_ptr<PPMD::PPMD> ppmd_;
  std::unique_ptr<ByteMixer> byte_mixer_;
  float ppmd_prediction_;
  float byte_prediction_;
};

std::array<float, kMaxHashDimensions> HashFxcm(
    const std::valarray<float>& probabilities) {
  std::array<float, kMaxHashDimensions> projection{};
  for (unsigned int index = 0; index < kFxcmOutputs; ++index) {
    std::uint32_t hash = index * 0x9e3779b1U + 0x85ebca6bU;
    hash ^= hash >> 16;
    const unsigned int bucket = hash & (kMaxHashDimensions - 1);
    const float sign = (hash & 0x10000U) ? 1.0f : -1.0f;
    projection[bucket] += sign * Logit(probabilities[index]);
  }
  return projection;
}

std::array<float, kFullFeatureCount> BuildFullFeatures(
    const std::valarray<float>& probabilities, float ppmd, float byte_mixer) {
  std::array<float, kFullFeatureCount> features{};
  for (unsigned int index = 0; index < kFxcmOutputs; ++index) {
    features[index] = Logit(probabilities[index]);
  }
  features[kFxcmOutputs] = Logit(ppmd);
  // Full FX2 clips this layer-0 input even when the final byte-mixer override
  // later treats an exact zero or one specially.
  features[kFxcmOutputs + 1] = Logit(byte_mixer);
  features[kFxcmOutputs + 2] = 1.0f;
  return features;
}

struct MixerConfig {
  std::string name;
  unsigned int dimensions;
  float learning_rate;
  bool contextual;
};

class HashedMixer {
 public:
  explicit HashedMixer(MixerConfig config)
      : config_(std::move(config)),
        weights_((config_.contextual ? kMxxContexts : 1) *
            (config_.dimensions + 2), 0.0f),
        last_features_(config_.dimensions + 2, 0.0f) {}

  const MixerConfig& config() const { return config_; }

  float Predict(const std::array<float, kMaxHashDimensions>& projection,
      float endpoint428, unsigned int mxx) {
    last_context_ = config_.contextual ? mxx : 0;
    std::fill(last_features_.begin(), last_features_.end(), 0.0f);
    for (unsigned int bucket = 0; bucket < kMaxHashDimensions; ++bucket) {
      last_features_[bucket & (config_.dimensions - 1)] += projection[bucket];
    }
    last_features_[config_.dimensions] = Logit(endpoint428);
    last_features_[config_.dimensions + 1] = 1.0f;
    const std::size_t offset = static_cast<std::size_t>(last_context_) *
        last_features_.size();
    float score = 0.0f;
    for (std::size_t index = 0; index < last_features_.size(); ++index) {
      score += weights_[offset + index] * last_features_[index];
    }
    last_probability_ = 1.0f / (1.0f + std::exp(-score));
    return last_probability_;
  }

  void Perceive(int bit) {
    float decay = 0.3f;
    if (steps_ < kDecayT1) {
      decay = steps_ < kDecayT0 ? 1.0f : 0.7f;
    }
    ++steps_;
    const float update = config_.learning_rate * decay *
        (last_probability_ - static_cast<float>(bit));
    const std::size_t offset = static_cast<std::size_t>(last_context_) *
        last_features_.size();
    for (std::size_t index = 0; index < last_features_.size(); ++index) {
      weights_[offset + index] -= update * last_features_[index];
    }
  }

 private:
  MixerConfig config_;
  std::vector<float> weights_;
  std::vector<float> last_features_;
  unsigned int last_context_ = 0;
  float last_probability_ = 0.5f;
  std::uint64_t steps_ = 0;
};

class FullFxcmMixer {
 public:
  FullFxcmMixer(std::string name, float learning_rate, bool contextual)
      : name_(std::move(name)), learning_rate_(learning_rate),
        contextual_(contextual),
        weights_((contextual_ ? kMxxContexts : 1) * kFullFeatureCount, 0.0f),
        last_features_(kFullFeatureCount, 0.0f) {}

  const std::string& name() const { return name_; }
  float learning_rate() const { return learning_rate_; }
  bool contextual() const { return contextual_; }

  float Predict(const std::array<float, kFullFeatureCount>& features,
      unsigned int mxx) {
    last_context_ = contextual_ ? mxx : 0;
    std::copy(features.begin(), features.end(), last_features_.begin());
    const std::size_t offset = static_cast<std::size_t>(last_context_) *
        last_features_.size();
    float score = 0.0f;
    for (std::size_t index = 0; index < last_features_.size(); ++index) {
      score += weights_[offset + index] * last_features_[index];
    }
    last_probability_ = 1.0f / (1.0f + std::exp(-score));
    return last_probability_;
  }

  void Perceive(int bit) {
    float decay = 0.3f;
    if (steps_ < kDecayT1) decay = steps_ < kDecayT0 ? 1.0f : 0.7f;
    ++steps_;
    const float update = learning_rate_ * decay *
        (last_probability_ - static_cast<float>(bit));
    const std::size_t offset = static_cast<std::size_t>(last_context_) *
        last_features_.size();
    for (std::size_t index = 0; index < last_features_.size(); ++index) {
      weights_[offset + index] -= update * last_features_[index];
    }
  }

 private:
  std::string name_;
  float learning_rate_;
  bool contextual_;
  std::vector<float> weights_;
  std::vector<float> last_features_;
  unsigned int last_context_ = 0;
  float last_probability_ = 0.5f;
  std::uint64_t steps_ = 0;
};

void ObserveByte(unsigned char value, Endpoint428Features* endpoint,
    MxxState* mxx) {
  for (int shift = 7; shift >= 0; --shift) {
    const int bit = (value >> shift) & 1;
    endpoint->Pretrain(bit);
    mxx->Observe(bit);
  }
}

struct Output {
  explicit Output(const std::string& path, std::uint64_t rows)
      : stream(path, std::ios::binary) {
    if (!stream) {
      std::cerr << "cannot open output " << path << "\n";
      std::exit(2);
    }
    const std::array<char, 8> magic = {'F', 'X', '2', 'L', '4', '2', '8', 0};
    stream.write(magic.data(), magic.size());
    stream.write(reinterpret_cast<const char*>(&rows), sizeof(rows));
  }
  std::ofstream stream;
};

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4 && argc != 5) {
    std::cerr << "usage: fx2lite_fxcm_hash_mixer_trace DICTIONARY WRT_STORE "
                 "OUTPUT_PREFIX [hash|full|all]\n";
    return 2;
  }
  const std::string mode = argc == 5 ? argv[4] : "all";
  if (mode != "hash" && mode != "full" && mode != "all") {
    std::cerr << "mode must be hash, full, or all\n";
    return 2;
  }
  const std::vector<unsigned char> dictionary = ReadFile(argv[1]);
  const std::vector<unsigned char> store = ReadFile(argv[2]);
  if (store.size() < 5 || store[0] != 0x80 || store[1] != 0 ||
      store[2] != 0 || store[3] != 0 || store[4] != 0) {
    std::cerr << "WRT store must have the canonical five-byte dictionary header\n";
    return 2;
  }
  std::vector<bool> vocab(256, false);
  for (std::size_t index = 5; index < store.size(); ++index) {
    vocab[store[index]] = true;
  }

  std::srand(kSeed);
  Endpoint428Features endpoint(vocab);
  MxxState mxx;
  const std::uint32_t dictionary_size =
      static_cast<std::uint32_t>(dictionary.size());
  const std::array<unsigned char, 5> dictionary_header = {
      0,
      static_cast<unsigned char>(dictionary_size >> 24),
      static_cast<unsigned char>(dictionary_size >> 16),
      static_cast<unsigned char>(dictionary_size >> 8),
      static_cast<unsigned char>(dictionary_size)};
  for (unsigned char value : dictionary_header) {
    ObserveByte(value, &endpoint, &mxx);
  }
  for (unsigned char value : dictionary) {
    ObserveByte(value == '\n' ? ' ' : value, &endpoint, &mxx);
  }

  const std::vector<MixerConfig> configs = {
      {"mxx_h16_lr1000", 16, 0.001f, true},
      {"mxx_h32_lr0500", 32, 0.0005f, true},
      {"mxx_h32_lr1000", 32, 0.001f, true},
      {"mxx_h32_lr2000", 32, 0.002f, true},
      {"mxx_h64_lr0500", 64, 0.0005f, true},
      {"mxx_h64_lr1000", 64, 0.001f, true},
      {"control_global_h32_lr1000", 32, 0.001f, false},
  };
  std::vector<HashedMixer> mixers;
  if (mode != "full") {
    for (const MixerConfig& config : configs) mixers.emplace_back(config);
  }
  std::vector<FullFxcmMixer> full_mixers;
  if (mode != "hash") {
    full_mixers.emplace_back("mxx_full433_lr0250", 0.00025f, true);
    full_mixers.emplace_back("mxx_full433_lr0500", 0.0005f, true);
    full_mixers.emplace_back("mxx_full433_lr1000", 0.001f, true);
    full_mixers.emplace_back("mxx_full433_lr2000", 0.002f, true);
    full_mixers.emplace_back("control_global_full433_lr1000", 0.001f, false);
  }
  const std::uint64_t rows = static_cast<std::uint64_t>(store.size() - 5) * 8;
  std::vector<std::unique_ptr<Output>> outputs;
  Output raw428_output(std::string(argv[3]) + ".raw428.p1", rows);
  for (const HashedMixer& mixer : mixers) {
    outputs.emplace_back(new Output(std::string(argv[3]) + "." +
        mixer.config().name + ".p1", rows));
  }
  std::vector<std::unique_ptr<Output>> full_outputs;
  for (const FullFxcmMixer& mixer : full_mixers) {
    full_outputs.emplace_back(new Output(
        std::string(argv[3]) + "." + mixer.name() + ".p1", rows));
  }

  std::uint64_t row = 0;
  for (std::size_t byte_index = 5; byte_index < store.size(); ++byte_index) {
    const unsigned char value = store[byte_index];
    for (int shift = 7; shift >= 0; --shift) {
      const int bit = (value >> shift) & 1;
      const std::valarray<float>& probabilities = endpoint.Predict();
      std::array<float, kMaxHashDimensions> projection{};
      if (!mixers.empty()) projection = HashFxcm(probabilities);
      std::array<float, kFullFeatureCount> full_features{};
      if (!full_mixers.empty()) {
        full_features = BuildFullFeatures(probabilities,
            endpoint.ppmd_prediction(), endpoint.byte_prediction());
      }
      const std::uint16_t raw428 = Discretize(probabilities[kEndpointIndex]);
      raw428_output.stream.write(
          reinterpret_cast<const char*>(&raw428), sizeof(raw428));
      for (std::size_t index = 0; index < mixers.size(); ++index) {
        const float prediction = mixers[index].Predict(
            projection, probabilities[kEndpointIndex], mxx.mxx);
        const std::uint16_t p1 = Discretize(prediction);
        outputs[index]->stream.write(
            reinterpret_cast<const char*>(&p1), sizeof(p1));
      }
      for (std::size_t index = 0; index < full_mixers.size(); ++index) {
        const float prediction = full_mixers[index].Predict(
            full_features, mxx.mxx);
        const std::uint16_t p1 = Discretize(prediction);
        full_outputs[index]->stream.write(
            reinterpret_cast<const char*>(&p1), sizeof(p1));
      }
      endpoint.Perceive(bit);
      for (HashedMixer& mixer : mixers) mixer.Perceive(bit);
      for (FullFxcmMixer& mixer : full_mixers) mixer.Perceive(bit);
      mxx.Observe(bit);
      ++row;
    }
    if (((byte_index - 4) & 0xffff) == 0) {
      std::cerr << "\rrows=" << row << '/' << rows;
    }
  }
  std::cerr << "\rrows=" << row << '/' << rows << "\n";
  for (const auto& output : outputs) {
    if (!output->stream) return 2;
  }
  for (const auto& output : full_outputs) {
    if (!output->stream) return 2;
  }
  if (!raw428_output.stream) return 2;
  for (const HashedMixer& mixer : mixers) {
    const MixerConfig& config = mixer.config();
    std::cout << config.name << " dimensions=" << config.dimensions
              << " learning_rate=" << config.learning_rate
              << " contextual=" << (config.contextual ? "true" : "false")
              << "\n";
  }
  for (const FullFxcmMixer& mixer : full_mixers) {
    std::cout << mixer.name() << " dimensions=433 learning_rate="
              << mixer.learning_rate() << " contextual="
              << (mixer.contextual() ? "true" : "false") << "\n";
  }
  return row == rows ? 0 : 2;
}
