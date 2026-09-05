#include "../../lib/midas_native_codec.hpp"

#include <array>
#include <fstream>
#include <iostream>
#include <iterator>
#include <random>

using namespace gamma_enwiki9::midas_codec;

namespace {
constexpr std::uint32_t model_tag = 0x514d4401U;

struct CountingFixture {
  std::array<std::array<unsigned, 2>, 256> counts{};
  unsigned context = 0;
  CountingFixture() { for (auto& row : counts) row = {1, 1}; }
  std::uint16_t predict() const {
    const auto& row = counts[context];
    return static_cast<std::uint16_t>(std::clamp(
        65536U * row[1] / (row[0] + row[1]), 1U, 65535U));
  }
  void observe(unsigned bit) {
    auto& row = counts[context];
    ++row[bit];
    if (row[0] + row[1] >= 32768)
      for (auto& count : row) count = std::max(1U, (count + 1) / 2);
    context = ((context << 1) | bit) & 255U;
  }
  Bytes serialize() const {
    Bytes out; put(out, context, 4);
    for (const auto& row : counts) for (auto value : row) put(out, value, 4);
    return out;
  }
};

Bytes read_file(const char* path) {
  std::ifstream in(path, std::ios::binary);
  require(bool(in), "cannot read fixture input");
  return Bytes(std::istreambuf_iterator<char>(in), {});
}
void write_file(const char* path, const Bytes& bytes) {
  std::ofstream out(path, std::ios::binary);
  require(bool(out), "cannot create fixture output");
  if (!bytes.empty())
    out.write(reinterpret_cast<const char*>(bytes.data()), bytes.size());
  require(bool(out), "fixture output write failed");
}

Bytes encode(const Bytes& raw) {
  Encoder coder;
  CountingFixture model;
  for (auto byte : raw) for (int shift = 7; shift >= 0; --shift) {
    const unsigned bit = (byte >> shift) & 1U;
    coder.encode(bit, model.predict()); model.observe(bit);
  }
  return frame(raw, coder.finish(), model_tag, 0);
}

Bytes decode(const Bytes& archive) {
  const auto input = unframe(archive, model_tag, 1000000, 4000000);
  require(input.arm == 0, "counting fixture supports parent only");
  Decoder coder(input.payload);
  CountingFixture model;
  Bytes raw;
  for (std::uint64_t i = 0; i != input.raw_bytes; ++i) {
    unsigned byte = 0;
    for (unsigned j = 0; j != 8; ++j) {
      const auto bit = coder.decode(model.predict()); model.observe(bit);
      byte = (byte << 1) | bit;
    }
    raw.push_back(static_cast<std::uint8_t>(byte));
  }
  coder.finish(); verify_inverse(input, raw);
  return raw;
}

template<class Function> void rejects(Function&& function) {
  bool rejected = false;
  try { function(); } catch (const std::runtime_error&) { rejected = true; }
  require(rejected, "malformed input was accepted");
}

void check_stream(const Bytes& raw, unsigned probability_mode) {
  Encoder encoder;
  CountingFixture parent;
  std::vector<Bytes> states;
  std::vector<std::uint16_t> probabilities;
  std::vector<Bytes> model_states;
  std::size_t position = 0;
  for (auto byte : raw) for (int shift = 7; shift >= 0; --shift) {
    const auto probability = probability_mode == 0 ? parent.predict() :
        static_cast<std::uint16_t>(probability_mode == 1 ? 1 :
                                   probability_mode == 2 ? 65535 : 32768);
    const unsigned bit = (byte >> shift) & 1U;
    probabilities.push_back(probability);
    encoder.encode(bit, probability); parent.observe(bit);
    states.push_back(encoder.comparison_state());
    if (position % 64 == 0) model_states.push_back(parent.serialize());
    if (position % 73 == 0) {
      const auto saved = encoder.serialize();
      encoder = Encoder::restore(saved);
      require(saved == encoder.serialize(), "encoder checkpoint changed");
    }
    ++position;
  }
  const auto payload = encoder.finish();
  const auto final_state = encoder.comparison_state();
  require(Encoder::restore(encoder.serialize()).serialize() == encoder.serialize(),
          "final encoder checkpoint changed");
  rejects([&]() { encoder.finish(); });

  Decoder decoder(payload);
  CountingFixture inverse;
  position = 0;
  std::size_t model_position = 0;
  for (auto byte : raw) for (int shift = 7; shift >= 0; --shift) {
    const auto probability = probability_mode == 0 ? inverse.predict() :
        static_cast<std::uint16_t>(probability_mode == 1 ? 1 :
                                   probability_mode == 2 ? 65535 : 32768);
    require(probability == probabilities[position], "pre-truth probability diverged");
    const auto bit = decoder.decode(probability); inverse.observe(bit);
    require(bit == ((byte >> shift) & 1U), "arithmetic inverse diverged");
    const auto difference = first_difference("coder", states[position],
                                             decoder.comparison_state());
    require(difference.equal, "normalized encoder/decoder state diverged");
    if (position % 64 == 0)
      require(model_states[model_position++] == inverse.serialize(),
              "predictor state diverged");
    if (position % 71 == 0) {
      const auto saved = decoder.serialize();
      decoder = Decoder::restore(saved);
      require(saved == decoder.serialize(), "decoder checkpoint changed");
    }
    ++position;
  }
  decoder.finish();
  require(final_state == decoder.comparison_state(), "final coder state diverged");
  require(Decoder::restore(decoder.serialize()).serialize() == decoder.serialize(),
          "final decoder checkpoint changed");
  rejects([&]() { decoder.finish(); });
  rejects([&]() { decoder.decode(32768); });

  auto junk = payload; junk.push_back(0);
  rejects([&]() {
    Decoder invalid(junk);
    for (auto p : probabilities) invalid.decode(p);
    invalid.finish();
  });
  junk = payload; junk.back() = 1;
  rejects([&]() {
    Decoder invalid(junk);
    for (auto p : probabilities) invalid.decode(p);
    invalid.finish();
  });
}

void check_byte_adapter() {
  for (unsigned mode = 0; mode != 3; ++mode) {
    BytePrefix::Counts counts;
    counts.fill(mode == 0 ? 256 : 1);
    if (mode) counts[mode == 1 ? 0 : 255] = 65536 - 255;
    BytePrefix prefix;
    Encoder encoder;
    std::vector<std::uint16_t> probabilities;
    std::vector<Bytes> states;
    for (unsigned byte = 0; byte != 256; ++byte) {
      prefix.begin_byte(counts);
      for (int shift = 7; shift >= 0; --shift) {
        const auto p = prefix.predict();
        const auto saved = prefix.serialize();
        prefix = BytePrefix::restore(saved);
        require(saved == prefix.serialize(), "pending byte-predictor state changed");
        rejects([&]() { prefix.predict(); });
        const unsigned bit = (byte >> shift) & 1U;
        probabilities.push_back(p);
        encoder.encode(bit, p);
        const auto complete = prefix.observe(bit);
        require(bool(complete) == (shift == 0), "wrong completed-byte boundary");
        if (complete) require(*complete == byte, "completed byte differs");
        states.push_back(prefix.serialize());
        prefix = BytePrefix::restore(prefix.serialize());
      }
    }
    require(!prefix.active() && prefix.position() == 2048, "wrong byte clock");
    const auto payload = encoder.finish();
    Decoder decoder(payload);
    BytePrefix inverse;
    std::size_t index = 0;
    for (unsigned byte = 0; byte != 256; ++byte) {
      inverse.begin_byte(counts);
      for (int shift = 7; shift >= 0; --shift) {
        const auto p = inverse.predict();
        require(p == probabilities[index], "byte adapter probability differs");
        const auto completed = inverse.observe(decoder.decode(p));
        require(states[index++] == inverse.serialize(), "byte adapter state differs");
        if (completed) require(*completed == byte, "byte adapter inverse differs");
      }
    }
    decoder.finish();
    require(encoder.comparison_state() == decoder.comparison_state(),
            "byte adapter final coder state differs");
  }
  BytePrefix empty;
  rejects([&]() { empty.predict(); });
  rejects([&]() { empty.observe(0); });
  BytePrefix::Counts counts{};
  rejects([&]() { empty.begin_byte(counts); });
  counts.fill(256); counts[0] = 255;
  rejects([&]() { empty.begin_byte(counts); });
  counts[0] = 256; empty.begin_byte(counts);
  rejects([&]() { empty.begin_byte(counts); });
  empty.predict();
  auto corrupted = empty.serialize(); corrupted[17] ^= 1;
  rejects([&]() { BytePrefix::restore(corrupted); });
  corrupted = empty.serialize(); corrupted[14] = 8;
  rejects([&]() { BytePrefix::restore(corrupted); });
}

void selftest() {
  check_byte_adapter();
  std::mt19937 random(123);
  for (std::size_t length : {0, 1, 2, 31, 32, 33, 63, 64, 65, 256, 1024}) {
    Bytes raw(length);
    for (auto& byte : raw) byte = static_cast<std::uint8_t>(random());
    for (unsigned mode = 0; mode != 4; ++mode) check_stream(raw, mode);
    const auto archive = encode(raw);
    require(decode(archive) == raw && encode(raw) == archive,
            "framed exact roundtrip/repeat failed");
  }
  check_stream(Bytes(1024, 0), 0);
  check_stream(Bytes(1024, 255), 0);
  auto archive = encode(Bytes{0, 1, 2, 255});
  rejects([&]() { unframe(archive, model_tag + 1, 4, 1000); });
  rejects([&]() { unframe(archive, model_tag, 3, 1000); });
  rejects([&]() { unframe(archive, model_tag, 4, 0); });
  for (std::size_t i = 0; i != archive.size(); ++i) {
    auto corrupted = archive; corrupted[i] ^= 0x80;
    rejects([&]() { decode(corrupted); });
  }
  for (std::size_t i = 0; i != archive.size(); ++i) {
    Bytes truncated(archive.begin(), archive.begin() + i);
    rejects([&]() { decode(truncated); });
  }
  auto extra = archive; extra.push_back(0);
  rejects([&]() { decode(extra); });
  Encoder e;
  rejects([&]() { e.encode(0, 0); });
  rejects([&]() { e.encode(2, 32768); });
  auto state = e.state().serialize();
  state[5] = 255; state[6] = 255; state[7] = 255; state[8] = 255;
  rejects([&]() { CoderState::restore(state); });
  const auto d = first_difference("parameters", Bytes{1, 2}, Bytes{1, 3});
  require(!d.equal && d.component == "parameters" && d.offset == 1 &&
          d.expected == 2 && d.actual == 3, "first-divergence position wrong");
  const auto short_state = first_difference("optimizer", Bytes{1}, Bytes{});
  require(!short_state.equal && short_state.expected == 1 && short_state.actual == -1,
          "first-divergence length handling wrong");
  require(crc32(Bytes{'1','2','3','4','5','6','7','8','9'}) == 0xcbf43926U,
          "CRC32 known-answer mismatch");
  std::cout << "native codec fixture: exact inverses, coder states, checkpoints, "
               "probabilities, corruption rejection and replay passed\n";
}
}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string(argv[1]) == "selftest") { selftest(); return 0; }
    require(argc == 4, "usage: fixture selftest | encode/decode INPUT OUTPUT");
    const std::string operation = argv[1];
    require(operation == "encode" || operation == "decode", "unknown operation");
    const auto input = read_file(argv[2]);
    write_file(argv[3], operation == "encode" ? encode(input) : decode(input));
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
