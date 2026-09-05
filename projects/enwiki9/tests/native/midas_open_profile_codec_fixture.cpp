#include "../../lib/midas_open_profile_fixture.hpp"

#include <fstream>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <map>
#include <sys/resource.h>

using namespace gamma_enwiki9::midas_codec;
using Predictor = MidpointBitPredictor<OpenProfileFixture>;

namespace {
constexpr std::size_t raw_bound = 65;
constexpr std::size_t joined_bound = 8 * 1024 * 1024;
constexpr std::size_t archive_bound = 2048;

std::string hex(const Bytes& bytes) {
  constexpr char alphabet[] = "0123456789abcdef";
  std::string out; out.reserve(bytes.size() * 2);
  for (auto byte : bytes) { out += alphabet[byte >> 4]; out += alphabet[byte & 15]; }
  return out;
}

bool boundary(std::size_t byte) {
  return byte == 1 || byte == 31 || byte == 32 || byte == 33 ||
         byte == 63 || byte == 64 || byte == 65;
}
void checkpoint(Predictor& model) {
  const auto before = model.serialize();
  model = Predictor::restore(before, joined_bound);
  require(before == model.serialize(), "real profile checkpoint did not repeat exactly");
}

struct Encoded {
  Bytes archive;
  std::vector<std::uint16_t> probabilities;
  std::vector<Bytes> coder_states;
  std::map<std::size_t, Bytes> states, identities;
  std::vector<std::pair<std::string, Bytes>> midpoint_parameters;
  Bytes midpoint_backend, midpoint_shadow;
};

Encoded encode(const Bytes& raw, Arm arm, bool audit) {
  require(raw.size() <= raw_bound, "raw population exceeds synthetic integration bound");
  Predictor model(OpenProfileFixture{}, arm);
  Encoder coder;
  Encoded result;
  for (std::size_t byte = 0; byte != raw.size(); ++byte) {
    for (int shift = 7; shift >= 0; --shift) {
      const auto p = model.predict();
      if (audit && shift == 7 && boundary(byte + 1)) checkpoint(model);
      const auto bit = (raw[byte] >> shift) & 1U;
      coder.encode(bit, p); model.observe(bit);
      if (audit) {
        result.probabilities.push_back(p); result.coder_states.push_back(coder.comparison_state());
      }
    }
    if (audit && boundary(byte + 1)) {
      checkpoint(model);
      result.states.emplace(byte + 1, model.serialize());
      result.identities.emplace(byte + 1, model.parent_identity_state());
    }
    if (audit && byte + 1 == 32) {
      result.midpoint_parameters = model.schedule().model().parameter_states();
      result.midpoint_backend = model.schedule().model().serialize();
      result.midpoint_shadow = model.schedule().last_shadow();
    }
  }
  const std::uint8_t archive_arm = arm == Arm::F ? 1 : arm == Arm::S ? 2 : 0;
  result.archive = frame(raw, coder.finish(), OpenProfileFixture::model_tag, archive_arm);
  require(result.archive.size() <= archive_bound, "synthetic archive bound exceeded");
  return result;
}

Bytes decode(const Bytes& archive, Arm arm, const Encoded* expected = nullptr) {
  const auto input = unframe(archive, OpenProfileFixture::model_tag, raw_bound, archive_bound);
  const auto archive_arm = arm == Arm::F ? 1 : arm == Arm::S ? 2 : 0;
  require(input.arm == archive_arm, "archive and decoder learning law differ");
  Predictor model(OpenProfileFixture{}, arm);
  Decoder coder(input.payload);
  Bytes raw;
  std::size_t position = 0;
  for (std::size_t byte = 0; byte != input.raw_bytes; ++byte) {
    unsigned value = 0;
    for (unsigned shift = 0; shift != 8; ++shift, ++position) {
      const auto p = model.predict();
      if (expected) require(p == expected->probabilities[position], "real pre-truth probability diverged");
      if (expected && shift == 0 && boundary(byte + 1)) checkpoint(model);
      const auto bit = coder.decode(p); model.observe(bit); value = (value << 1) | bit;
      if (expected)
        require(coder.comparison_state() == expected->coder_states[position],
                "real normalized arithmetic state diverged");
    }
    raw.push_back(static_cast<std::uint8_t>(value));
    if (expected && boundary(byte + 1)) {
      checkpoint(model);
      const auto difference = first_difference("full predictor", expected->states.at(byte + 1), model.serialize());
      if (!difference.equal)
        throw std::runtime_error("real predictor state diverged at byte " + std::to_string(byte + 1) +
                                 ", serialized offset " + std::to_string(difference.offset));
    }
  }
  coder.finish(); verify_inverse(input, raw); return raw;
}

void selftest() {
  Bytes raw;
  for (unsigned i = 0; i != raw_bound; ++i) raw.push_back(static_cast<std::uint8_t>(17 * i + 3));
  const auto initial_parameters = OpenProfileFixture{}.parameter_states();
  const auto parent = encode(raw, Arm::P, true);
  unsigned changed_full_tensors = 0;
  Bytes shadow_midpoint, full_midpoint;
  for (const auto arm : {Arm::P, Arm::K, Arm::F, Arm::S}) {
    const auto encoded = arm == Arm::P ? parent : encode(raw, arm, true);
    const auto inverse = decode(encoded.archive, arm, &encoded);
    require(inverse == raw, "real open profile inverse differs");
    require(encode(inverse, arm, false).archive == encoded.archive, "real open profile re-encode differs");
    require(std::equal(parent.probabilities.begin(), parent.probabilities.begin() + 32 * 8,
                       encoded.probabilities.begin()), "an arm changed pre-midpoint probabilities");
    if (arm == Arm::P || arm == Arm::K) {
      require(encoded.midpoint_parameters == initial_parameters,
              "P/K changed authoritative parameters at the midpoint");
      require(encoded.archive == parent.archive && encoded.probabilities == parent.probabilities &&
              encoded.identities == parent.identities, "real P/K archive or state identity failed");
      if (arm == Arm::K) {
        require(!encoded.midpoint_shadow.empty() &&
                OpenProfileFixture::restore(encoded.midpoint_shadow).updates() == 1 &&
                OpenProfileFixture::restore(encoded.midpoint_backend).updates() == 0,
                "K failed to isolate its real full update");
        shadow_midpoint = encoded.midpoint_shadow;
      }
    } else {
      std::map<std::string, bool> changed;
      for (std::size_t i = 0; i != initial_parameters.size(); ++i) {
        require(initial_parameters[i].first == encoded.midpoint_parameters[i].first,
                "real full-update parameter order differs");
        changed.emplace(initial_parameters[i].first,
                        initial_parameters[i].second != encoded.midpoint_parameters[i].second);
      }
      require(changed.at("embed") && changed.at("w_q_0") && changed.at("w_kv_0") &&
              changed.at("ff1_0") && changed.at("ff2_0") && changed.at("embed_out"),
              "real midpoint update did not reach embedding, attention, feedforward and output");
      if (arm == Arm::F) {
        require(encoded.midpoint_backend == shadow_midpoint,
                "K shadow did not execute the same full update and rebuild as F");
        full_midpoint = encoded.midpoint_backend;
        for (const auto& [name, value] : changed) { (void)name; changed_full_tensors += value; }
      } else {
        require(encoded.midpoint_backend != full_midpoint,
                "S did not change the full-model midpoint association");
      }
    }
    std::cout << "arm=" << static_cast<unsigned>(arm) << " raw_bytes=" << raw.size()
              << " archive_bytes=" << encoded.archive.size() << " inverse=exact repeat=exact"
              << " archive_hex=" << hex(encoded.archive) << '\n';
  }
  const auto empty = encode({}, Arm::P, false);
  require(decode(empty.archive, Arm::P).empty(), "real empty archive inverse differs");
  const auto rejects = [](auto&& operation) {
    bool rejected = false;
    try { operation(); } catch (const std::runtime_error&) { rejected = true; }
    require(rejected, "invalid real model checkpoint was accepted");
  };
  const auto initial = OpenProfileFixture{}.serialize();
  for (const auto offset : {5, 18, 19, 20, 21, 22, 1046}) {
    auto corrupted = initial; corrupted[offset] ^= 0x80;
    rejects([&]() { OpenProfileFixture::restore(corrupted); });
  }
  auto nonfinite = initial; nonfinite[1054] = 0x80; nonfinite[1055] = 0x7f;
  rejects([&]() { OpenProfileFixture::restore(nonfinite); });
  Reader moment_reader(initial); moment_reader.take(22 + 1024);
  const auto memory_elements = moment_reader.get(8); moment_reader.take(memory_elements * 2);
  for (const auto& item : initial_parameters) moment_reader.take(item.second.size());
  moment_reader.get(8);  // optimizer exponent
  const auto low_words = moment_reader.get(8); moment_reader.take(low_words * 2);
  require(moment_reader.get(8) > 0, "negative-moment fixture lacks a second moment");
  const auto moment_offset = initial.size() - moment_reader.remaining();
  auto negative_moment = initial;
  negative_moment[moment_offset] = 0x80; negative_moment[moment_offset + 1] = 0xbf;
  rejects([&]() { OpenProfileFixture::restore(negative_moment); });
  auto truncated = initial; truncated.pop_back();
  rejects([&]() { OpenProfileFixture::restore(truncated); });
  auto trailing = initial; trailing.push_back(0);
  rejects([&]() { OpenProfileFixture::restore(trailing); });
  auto active_model = OpenProfileFixture{}; active_model.predict_byte();
  auto mismatched_cache = active_model.serialize();
  // Preserve Q16 unity but make the cached byte distribution disagree with the
  // reconstructed neural model. Counts begin at byte 22 of the empty prefix.
  Reader cache_reader(mismatched_cache); cache_reader.take(22);
  const auto count0 = cache_reader.get(4), count1 = cache_reader.get(4);
  require(count1 > 1, "cached corruption fixture has no movable count");
  Bytes replacement; put(replacement, count0 + 1, 4); put(replacement, count1 - 1, 4);
  std::copy(replacement.begin(), replacement.end(), mismatched_cache.begin() + 22);
  rejects([&]() { OpenProfileFixture::restore(mismatched_cache); });
  std::cout << "real open profile parent: P/K identity, full F/S updates, exact inverse, "
               "replay and checkpoint synchronization passed; midpoint_changed_tensors="
            << changed_full_tensors << " of " << initial_parameters.size() << '\n';
}

void kernel_diagnostic() {
  Bytes raw;
  for (unsigned i = 0; i != raw_bound; ++i) raw.push_back(static_cast<std::uint8_t>(17 * i + 3));
  const auto encode_wall = std::chrono::steady_clock::now();
  const auto encode_cpu = std::clock();
  const auto encoded = encode(raw, Arm::P, false);
  const double encode_cpu_seconds = double(std::clock() - encode_cpu) / CLOCKS_PER_SEC;
  const double encode_wall_seconds = std::chrono::duration<double>(
      std::chrono::steady_clock::now() - encode_wall).count();
  const auto decode_wall = std::chrono::steady_clock::now();
  const auto decode_cpu = std::clock();
  const auto inverse = decode(encoded.archive, Arm::P);
  const double decode_cpu_seconds = double(std::clock() - decode_cpu) / CLOCKS_PER_SEC;
  const double decode_wall_seconds = std::chrono::duration<double>(
      std::chrono::steady_clock::now() - decode_wall).count();
  require(inverse == raw, "kernel diagnostic inverse differs");
  rusage usage{}; require(getrusage(RUSAGE_SELF, &usage) == 0, "kernel resource observation failed");
  std::cout << std::setprecision(9)
            << "KERNEL_JSON={\"raw_bytes\":" << raw.size()
            << ",\"archive_bytes\":" << encoded.archive.size()
            << ",\"encode_cpu_seconds\":" << encode_cpu_seconds
            << ",\"decode_cpu_seconds\":" << decode_cpu_seconds
            << ",\"encode_wall_seconds\":" << encode_wall_seconds
            << ",\"decode_wall_seconds\":" << decode_wall_seconds
            << ",\"process_peak_rss_kib\":" << usage.ru_maxrss
            << ",\"inverse_exact\":true,\"qualification\":false}\n";
}

Bytes read_file(const char* path, std::size_t bound) {
  std::ifstream input(path, std::ios::binary); require(bool(input), "cannot open bounded fixture input");
  Bytes bytes;
  char byte;
  while (input.get(byte)) {
    require(bytes.size() < bound, "fixture input exceeds its bound");
    bytes.push_back(static_cast<std::uint8_t>(byte));
  }
  require(input.eof(), "fixture input read failed"); return bytes;
}
void write_file(const char* path, const Bytes& bytes) {
  std::ofstream output(path, std::ios::binary); require(bool(output), "cannot create fixture output");
  if (!bytes.empty()) output.write(reinterpret_cast<const char*>(bytes.data()), bytes.size());
  require(bool(output), "fixture output write failed");
}
Arm parse_arm(const std::string& name) {
  if (name == "P") return Arm::P;
  if (name == "K") return Arm::K;
  if (name == "F") return Arm::F;
  require(name == "S", "unknown fixture arm"); return Arm::S;
}
}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string(argv[1]) == "selftest") { selftest(); return 0; }
    if (argc == 2 && std::string(argv[1]) == "kernel") { kernel_diagnostic(); return 0; }
    require(argc == 5, "usage: selftest | kernel | encode/decode P/K/F/S INPUT OUTPUT");
    const std::string operation = argv[1]; const auto arm = parse_arm(argv[2]);
    require(operation == "encode" || operation == "decode", "unknown fixture operation");
    const auto input = read_file(argv[3], operation == "encode" ? raw_bound : archive_bound);
    write_file(argv[4], operation == "encode" ? encode(input, arm, false).archive : decode(input, arm));
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
