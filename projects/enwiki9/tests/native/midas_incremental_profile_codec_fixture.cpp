#include "../../lib/midas_open_profile_fixture.hpp"
#include "../../lib/midas_open_profile_incremental_fixture.hpp"

#include <chrono>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sys/resource.h>

using namespace gamma_enwiki9::midas_codec;
using Reference = OpenProfileFixture;
using Incremental = OpenProfileIncrementalFixture;
constexpr std::size_t raw_bound = 129, archive_bound = 4096, joined_bound = 8 * 1024 * 1024;

namespace {
bool boundary(std::size_t byte) {
  return byte == 1 || byte % 32 == 0 || byte % 32 == 1 || byte % 32 == 31;
}
template<class Model> Bytes reference_state(const Model& model) {
  if constexpr (std::is_same_v<Model, Incremental>) return model.reference_state();
  else return model.serialize();
}
template<class Model> void checkpoint(MidpointBitPredictor<Model>& model) {
  const auto state = model.serialize();
  model = MidpointBitPredictor<Model>::restore(state, joined_bound);
  require(state == model.serialize(), "incremental joined checkpoint changed state");
}

struct Encoded {
  Bytes archive;
  std::vector<std::uint16_t> probabilities;
  std::vector<Bytes> coder_states;
  std::map<std::size_t, Bytes> reference_states, native_states, pending_states, shadows;
};

template<class Model> Encoded encode(const Bytes& raw, Arm arm, bool audit) {
  require(raw.size() <= raw_bound, "incremental fixture raw bound exceeded");
  MidpointBitPredictor<Model> model(Model{}, arm);
  Encoder coder;
  Encoded result;
  for (std::size_t byte = 0; byte < raw.size(); ++byte) {
    for (int shift = 7; shift >= 0; --shift) {
      const auto probability = model.predict();
      if (audit && shift == 7) {
        if constexpr (std::is_same_v<Model, Incremental>) model.schedule().model().verify_reference_row();
      }
      if (audit && boundary(byte + 1)) {
        checkpoint(model);  // Include pending predictions at every bit offset.
        result.pending_states.emplace(byte * 8 + 7 - shift, model.serialize());
      }
      const auto truth = (raw[byte] >> shift) & 1U;
      coder.encode(truth, probability); model.observe(truth);
      if (audit) {
        result.probabilities.push_back(probability);
        result.coder_states.push_back(coder.comparison_state());
      }
    }
    if (audit && boundary(byte + 1)) {
      checkpoint(model);
      result.reference_states.emplace(byte + 1, reference_state(model.schedule().model()));
      result.native_states.emplace(byte + 1, model.serialize());
      if (!model.schedule().last_shadow().empty())
        result.shadows.emplace(byte + 1, reference_state(Model::restore(model.schedule().last_shadow())));
    }
  }
  result.archive = frame(raw, coder.finish(), Model::model_tag,
                         arm == Arm::F ? 1 : arm == Arm::S ? 2 : 0);
  return result;
}

template<class Model> Bytes decode(const Bytes& archive, Arm arm, const Encoded* expected = nullptr) {
  const auto input = unframe(archive, Model::model_tag, raw_bound, archive_bound);
  require(input.arm == (arm == Arm::F ? 1 : arm == Arm::S ? 2 : 0), "incremental archive arm differs");
  MidpointBitPredictor<Model> model(Model{}, arm);
  Decoder coder(input.payload);
  Bytes raw;
  for (std::size_t byte = 0; byte < input.raw_bytes; ++byte) {
    unsigned value = 0;
    for (unsigned bit = 0; bit != 8; ++bit) {
      const auto probability = model.predict();
      if (expected) {
        require(probability == expected->probabilities[byte * 8 + bit], "incremental pre-truth divergence");
        if (boundary(byte + 1)) {
          checkpoint(model);
          require(model.serialize() == expected->pending_states.at(byte * 8 + bit),
                  "incremental pending state diverged");
        }
      }
      const auto truth = coder.decode(probability); model.observe(truth); value = (value << 1) | truth;
      if (expected)
        require(coder.comparison_state() == expected->coder_states[byte * 8 + bit],
                "incremental coder state diverged");
    }
    raw.push_back(static_cast<std::uint8_t>(value));
    if (expected && boundary(byte + 1)) {
      checkpoint(model);
      const auto difference = first_difference("incremental predictor",
          expected->native_states.at(byte + 1), model.serialize());
      if (!difference.equal) throw std::runtime_error("incremental byte " + std::to_string(byte + 1) +
          " checkpoint divergence at " + std::to_string(difference.offset));
    }
  }
  coder.finish(); verify_inverse(input, raw); return raw;
}

std::string hex(const Bytes& bytes) {
  std::string out;
  for (auto byte : bytes) { out += "0123456789abcdef"[byte >> 4]; out += "0123456789abcdef"[byte & 15]; }
  return out;
}
Bytes fixture(std::size_t size) {
  Bytes raw; for (std::size_t i = 0; i < size; ++i) raw.push_back((17 * i + 3) & 255); return raw;
}
void selftest(int selected_arm = -1, unsigned selected_size = 0) {
  for (const auto size : {65U, 129U}) {
    if (selected_size && size != selected_size) continue;
    const auto raw = fixture(size);
    Bytes parent;
    for (const auto arm : {Arm::P, Arm::K, Arm::F, Arm::S}) {
      if (selected_arm >= 0 && static_cast<int>(arm) != selected_arm) continue;
      const auto reference = encode<Reference>(raw, arm, true);
      const auto incremental = encode<Incremental>(raw, arm, true);
      require(reference.archive == incremental.archive && reference.probabilities == incremental.probabilities &&
              reference.reference_states == incremental.reference_states && reference.shadows == incremental.shadows,
              "incremental/reference probabilities, model, optimizer, memory, shadow or archive differs");
      require(decode<Incremental>(incremental.archive, arm, &incremental) == raw,
              "incremental inverse or synchronization differs");
      require(decode<Reference>(incremental.archive, arm) == raw, "reference cross-decoding differs");
      require(decode<Incremental>(reference.archive, arm) == raw, "incremental cross-decoding differs");
      require(encode<Incremental>(raw, arm, false).archive == incremental.archive, "incremental repeat differs");
      if (arm == Arm::P) parent = incremental.archive;
      if (arm == Arm::K && parent.empty()) parent = encode<Incremental>(raw, Arm::P, false).archive;
      if (arm == Arm::K) require(parent == incremental.archive, "incremental P/K identity differs");
      std::cout << "arm=" << "PKFS"[static_cast<unsigned>(arm)] << " raw_bytes=" << size
                << " archive_bytes=" << incremental.archive.size() << " archive_hex=" << hex(incremental.archive)
                << " inverse=exact cross_decode=exact repeat=exact f32_rows=exact\n";
    }
  }
  for (const auto size : {0U, 1U, 31U, 32U, 33U, 63U, 64U}) {
    const auto raw = fixture(size);
    const auto archive = encode<Incremental>(raw, Arm::F, false).archive;
    require(archive == encode<Reference>(raw, Arm::F, false).archive && decode<Incremental>(archive, Arm::F) == raw,
            "incremental partial-segment inverse differs");
  }
  const auto rejects = [](auto&& operation) {
    bool rejected = false;
    try { operation(); } catch (const std::exception&) { rejected = true; }
    require(rejected, "invalid incremental checkpoint accepted");
  };
  auto model = Incremental{}; model.predict_byte();
  const auto state = model.serialize();
  const auto engine_begin = model.reference_state().size() + 8;
  for (const auto offset : {engine_begin, engine_begin + 5, engine_begin + 6,
                            engine_begin + 7, engine_begin + 16, state.size() - 1}) {
    auto bad = state; bad[offset] ^= 0x80;
    rejects([&]() { Incremental::restore(bad); });
  }
  auto truncated = state; truncated.pop_back();
  rejects([&]() { Incremental::restore(truncated); });
  auto trailing = state; trailing.push_back(0);
  rejects([&]() { Incremental::restore(trailing); });
  // A real parameter mutation must invalidate the cache, even if its final
  // quantized distribution happens to remain unchanged on this symbol.
  auto stale = state; stale[1054] ^= 0x80;
  rejects([&]() { Incremental::restore(stale); });
  std::cout << "incremental profile: exact F32/Q16 rows, P/K/F/S archives, full states, "
               "midpoint invalidation, cross-decoding and checkpoint replay passed\n";
}

void kernel() {
  const auto raw = fixture(129);
  rusage usage{};
  for (const bool incremental : {false, true}) {
    const auto encode_cpu = std::clock(); const auto encode_wall = std::chrono::steady_clock::now();
    const auto result = incremental ? encode<Incremental>(raw, Arm::F, false) : encode<Reference>(raw, Arm::F, false);
    const auto encode_seconds = double(std::clock() - encode_cpu) / CLOCKS_PER_SEC;
    const auto encode_elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - encode_wall).count();
    const auto decode_cpu = std::clock(); const auto decode_wall = std::chrono::steady_clock::now();
    const auto inverse = incremental ? decode<Incremental>(result.archive, Arm::F) : decode<Reference>(result.archive, Arm::F);
    const auto decode_seconds = double(std::clock() - decode_cpu) / CLOCKS_PER_SEC;
    const auto decode_elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - decode_wall).count();
    require(inverse == raw, "incremental kernel inverse differs");
    require(getrusage(RUSAGE_SELF, &usage) == 0, "incremental resource observation failed");
    std::cout << std::setprecision(9) << "KERNEL_JSON={\"backend\":\"" << (incremental ? "incremental" : "reference")
              << "\",\"arm\":\"F\",\"raw_bytes\":129,\"archive_bytes\":" << result.archive.size()
              << ",\"encode_cpu_seconds\":" << encode_seconds << ",\"decode_cpu_seconds\":" << decode_seconds
              << ",\"encode_wall_seconds\":" << encode_elapsed << ",\"decode_wall_seconds\":" << decode_elapsed
              << ",\"process_peak_rss_kib\":" << usage.ru_maxrss << ",\"inverse_exact\":true,\"qualification\":false}\n";
  }
}

Bytes read_file(const char* path, std::size_t bound) {
  std::ifstream input(path, std::ios::binary); require(bool(input), "cannot open incremental fixture input");
  Bytes out; char byte;
  while (input.get(byte)) { require(out.size() < bound, "incremental input bound exceeded"); out.push_back(byte); }
  require(input.eof(), "incremental input read failed"); return out;
}
}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string(argv[1]) == "selftest") { selftest(); return 0; }
    if (argc == 4 && std::string(argv[1]) == "selftest") {
      const std::string arm_name = argv[2], size = argv[3];
      const auto arm = std::string("PKFS").find(arm_name);
      require(arm_name.size() == 1 && arm != std::string::npos && (size == "65" || size == "129"),
              "partitioned selftest requires P/K/F/S and 65/129");
      selftest(static_cast<int>(arm), size == "65" ? 65 : 129); return 0;
    }
    if (argc == 2 && std::string(argv[1]) == "kernel") { kernel(); return 0; }
    require(argc == 6, "usage: selftest | kernel | reference/incremental encode/decode P/K/F/S INPUT OUTPUT");
    const std::string backend = argv[1], operation = argv[2], arm_name = argv[3];
    require(backend == "reference" || backend == "incremental", "unknown incremental fixture backend");
    require(operation == "encode" || operation == "decode", "unknown incremental fixture operation");
    const auto index = std::string("PKFS").find(arm_name);
    require(arm_name.size() == 1 && index != std::string::npos, "unknown incremental fixture arm");
    const auto arm = static_cast<Arm>(index);
    const auto input = read_file(argv[4], operation == "encode" ? raw_bound : archive_bound);
    Bytes output;
    if (backend == "incremental") output = operation == "encode" ? encode<Incremental>(input, arm, false).archive : decode<Incremental>(input, arm);
    else output = operation == "encode" ? encode<Reference>(input, arm, false).archive : decode<Reference>(input, arm);
    std::ofstream file(argv[5], std::ios::binary); require(bool(file), "cannot create incremental fixture output");
    file.write(reinterpret_cast<const char*>(output.data()), output.size());
    require(bool(file), "incremental fixture output write failed");
    return 0;
  } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
