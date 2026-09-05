#include "../../lib/midas_bit_predictor.hpp"

#include <iostream>

using namespace gamma_enwiki9::midas_codec;

namespace {
// A causal sentinel, NOT a neural predictor or a compression experiment. Its
// visibly invalidated recurrent state makes omission of rebuild fail immediately.
struct Sentinel {
  struct Update {
    Bytes origin, inputs, targets;
  };
  std::uint64_t parameter = 7, moment = 0, recurrent = 3, position = 0;
  bool invalidated = false;
  std::vector<Update> updates;

  static void blob(Bytes& out, const Bytes& value) {
    put(out, value.size(), 8); out.insert(out.end(), value.begin(), value.end());
  }
  static Bytes blob(Reader& in) {
    const auto size = in.get(8);
    require(size <= in.remaining(), "sentinel blob exceeds checkpoint");
    return in.take(static_cast<std::size_t>(size));
  }
  BytePrefix::Counts predict_byte() const {
    require(!invalidated, "prediction used invalidated recurrent state");
    BytePrefix::Counts counts; counts.fill(128);
    counts[(parameter ^ recurrent ^ position) & 255U] += 32768;
    return counts;
  }
  void observe_byte(std::uint8_t byte) {
    require(!invalidated, "observation used invalidated recurrent state");
    recurrent = recurrent * 257 + parameter + byte;
    ++position;
  }
  Bytes sequence_origin() const {
    require(!invalidated, "origin captured stale state");
    Bytes out; put(out, recurrent, 8); put(out, position, 8); return out;
  }
  void full_update(const Bytes& origin, const Bytes& inputs, const Bytes& targets) {
    require(!invalidated && inputs.size() == targets.size(), "bad sentinel update");
    Reader in(origin); in.get(8); const auto start = in.get(8); in.end();
    require(start + inputs.size() == position, "training included future inputs");
    for (std::size_t i = 0; i != inputs.size(); ++i) {
      moment = moment * 17 + targets[i] + 1;
      parameter = parameter * 31 + moment + inputs[i];
    }
    updates.push_back({origin, inputs, targets});
    invalidated = true;
  }
  void rebuild(const Bytes& origin, const Bytes& inputs) {
    require(invalidated && !updates.empty() && updates.back().origin == origin &&
            updates.back().inputs == inputs, "wrong prefix rebuilt");
    Reader in(origin); recurrent = in.get(8); position = in.get(8); in.end();
    invalidated = false;
    for (auto byte : inputs) observe_byte(byte);
  }
  Bytes serialize() const {
    Bytes out{'S', 'E', 'N', 'T', 1};
    for (auto value : {parameter, moment, recurrent, position}) put(out, value, 8);
    put(out, invalidated, 1); put(out, updates.size(), 8);
    for (const auto& update : updates) {
      blob(out, update.origin); blob(out, update.inputs); blob(out, update.targets);
    }
    return out;
  }
  static Sentinel restore(const Bytes& bytes) {
    Reader in(bytes); in.magic("SENT\1", 5);
    Sentinel out;
    out.parameter = in.get(8); out.moment = in.get(8);
    out.recurrent = in.get(8); out.position = in.get(8);
    const auto invalidated = in.get(1), size = in.get(8);
    require(invalidated <= 1 && size <= in.remaining() / 24, "bad sentinel state");
    out.invalidated = invalidated != 0;
    for (std::uint64_t i = 0; i != size; ++i)
      out.updates.push_back({blob(in), blob(in), blob(in)});
    in.end(); return out;
  }
};

using Schedule = MidpointSchedule<Sentinel>;
using BitPredictor = MidpointBitPredictor<Sentinel>;
constexpr std::uint64_t component_bound = 1024 * 1024;

template<class Function> void rejects(Function&& function) {
  bool rejected = false;
  try { function(); } catch (const std::runtime_error&) { rejected = true; }
  require(rejected, "invalid scheduler input accepted");
}

void checkpoint(Schedule& schedule) {
  const auto bytes = schedule.serialize();
  schedule = Schedule::restore(bytes, component_bound);
  require(schedule.serialize() == bytes, "scheduler checkpoint changed state");
}

void check_update_law() {
  std::array<Schedule, 4> schedules{
      Schedule(Sentinel{}, Arm::P), Schedule(Sentinel{}, Arm::K),
      Schedule(Sentinel{}, Arm::F), Schedule(Sentinel{}, Arm::S)};
  for (unsigned position = 0; position != 129; ++position) {
    std::array<BytePrefix::Counts, 4> predictions;
    for (unsigned arm = 0; arm != 4; ++arm) {
      auto& schedule = schedules[arm];
      predictions[arm] = schedule.predict_byte();
      checkpoint(schedule);
      rejects([&]() { schedule.predict_byte(); });
    }
    require(predictions[0] == predictions[1], "P/K distributions diverged");
    if (position < 32)
      require(predictions[0] == predictions[2] && predictions[0] == predictions[3],
              "midpoint arm changed predictions before 32 decoded bytes");
    require(schedules[0].parent_identity_state() == schedules[1].parent_identity_state(),
            "pending P/K predictive states diverged");

    const auto byte = static_cast<std::uint8_t>(position);
    for (unsigned arm = 0; arm != 4; ++arm) {
      auto& schedule = schedules[arm];
      schedule.observe_byte(byte); checkpoint(schedule);
      rejects([&]() { schedule.observe_byte(byte); });
      require(schedule.position() == position + 1 &&
              schedule.model().position == position + 1, "byte clocks disagree");
      const auto parent_updates = (position + 1) / 64;
      const auto opportunities = parent_updates + ((position + 1) % 64 >= 32 ? 1 : 0);
      require(schedule.parent_updates() == parent_updates &&
              schedule.midpoint_updates() == (arm >= 2 ? opportunities : 0) &&
              schedule.shadow_updates() == (arm == 1 ? opportunities : 0),
              "incorrect update boundary");
    }
    require(schedules[0].parent_identity_state() == schedules[1].parent_identity_state(),
            "observed P/K predictive states diverged");
    require(schedules[0].model().serialize() == schedules[1].model().serialize(),
            "K shadow changed authoritative model or optimizer");

    if ((position + 1) % 64 == 32) {
      const auto& full = schedules[2].model().updates.back();
      const auto& shifted = schedules[3].model().updates.back();
      Bytes prefix;
      for (unsigned i = position - 31; i <= position; ++i)
        prefix.push_back(static_cast<std::uint8_t>(i));
      require(full.inputs == prefix && full.targets == prefix && shifted.inputs == prefix,
              "midpoint training population is not precisely the decoded prefix");
      std::rotate(prefix.begin(), prefix.begin() + 1, prefix.end());
      require(shifted.targets == prefix, "S did not shift only causal target association");
      const auto shadow = Sentinel::restore(schedules[1].last_shadow());
      require(!shadow.invalidated && shadow.updates.back().inputs == full.inputs &&
              shadow.updates.back().targets == full.targets,
              "K did not execute full update and rebuild on its shadow");
      require(schedules[0].model().serialize() != schedules[2].model().serialize() &&
              schedules[2].model().serialize() != schedules[3].model().serialize(),
              "F/S controls failed to exercise distinct updates");
    }
    if ((position + 1) % 64 == 0) {
      for (const auto& schedule : schedules) {
        const auto& update = schedule.model().updates.back();
        require(update.inputs.size() == 64 && update.targets == update.inputs,
                "common parent update used wrong population");
      }
    }
  }
}

struct Encoded {
  Bytes payload;
  std::vector<Bytes> model_states, identity_states, coder_states;
  std::vector<std::uint16_t> probabilities;
};

Encoded encode(const Bytes& raw, Arm arm) {
  Encoded result;
  BitPredictor model(Sentinel{}, arm);
  Encoder coder;
  for (auto byte : raw) {
    for (int shift = 7; shift >= 0; --shift) {
      const auto p = model.predict(); result.probabilities.push_back(p);
      const auto pending = model.serialize();
      model = BitPredictor::restore(pending, component_bound);
      require(pending == model.serialize(), "pending joined checkpoint changed state");
      rejects([&]() { model.predict(); });
      const auto bit = (byte >> shift) & 1U;
      coder.encode(bit, p);
      model.observe(bit);
      result.model_states.push_back(model.serialize());
      result.identity_states.push_back(model.parent_identity_state());
      result.coder_states.push_back(coder.comparison_state());
    }
  }
  result.payload = coder.finish(); return result;
}

void check_inverse(const Bytes& raw, Arm arm, const Encoded& encoded) {
  BitPredictor model(Sentinel{}, arm);
  Decoder coder(encoded.payload);
  Bytes restored;
  std::size_t position = 0;
  for (std::size_t byte = 0; byte != raw.size(); ++byte) {
    unsigned decoded_byte = 0;
    for (unsigned bit = 0; bit != 8; ++bit, ++position) {
      const auto p = model.predict();
      require(p == encoded.probabilities[position], "decoder pre-truth probability differs");
      model = BitPredictor::restore(model.serialize(), component_bound);
      const auto truth = coder.decode(p); model.observe(truth);
      decoded_byte = (decoded_byte << 1) | truth;
      require(model.serialize() == encoded.model_states[position],
              "decoder parameter, optimizer, recurrent or schedule state differs");
      require(coder.comparison_state() == encoded.coder_states[position],
              "decoder coder state differs");
      require(model.bit_position() == position + 1, "joined predictor bit clock differs");
      model = BitPredictor::restore(model.serialize(), component_bound);
      coder = Decoder::restore(coder.serialize());
    }
    restored.push_back(static_cast<std::uint8_t>(decoded_byte));
  }
  coder.finish();
  require(restored == raw, "scheduled arithmetic inverse failed");
  require(encode(restored, arm).payload == encoded.payload, "scheduled repeat failed");
}

void malformed_joined_checkpoints() {
  // Each component can be valid in isolation and still be invalid as a pair.
  const auto joined = [](const Schedule& schedule, const BytePrefix& prefix) {
    Bytes out{'M', 'B', 'I', 'T', 1};
    Sentinel::blob(out, schedule.serialize()); Sentinel::blob(out, prefix.serialize());
    return out;
  };
  Schedule schedule(Sentinel{}, Arm::P);
  BytePrefix prefix;
  const auto initial = joined(schedule, prefix);
  require(BitPredictor::restore(initial, component_bound).serialize() == initial,
          "joined initial checkpoint changed state");
  rejects([&]() { BitPredictor::restore(initial, initial.size() - 1); });
  const auto counts = schedule.predict_byte();
  rejects([&]() { BitPredictor::restore(joined(schedule, prefix), component_bound); });
  BytePrefix::Counts wrong; wrong.fill(256); prefix.begin_byte(wrong);
  rejects([&]() { BitPredictor::restore(joined(schedule, prefix), component_bound); });
  prefix = BytePrefix{}; prefix.begin_byte(counts);
  const auto pending_byte = joined(schedule, prefix);
  require(BitPredictor::restore(pending_byte, component_bound).serialize() == pending_byte,
          "joined pre-bit checkpoint changed state");
  for (unsigned bit = 0; bit != 8; ++bit) { prefix.predict(); prefix.observe(0); }
  rejects([&]() { BitPredictor::restore(joined(schedule, prefix), component_bound); });
  schedule.observe_byte(0);
  require(BitPredictor::restore(joined(schedule, prefix), component_bound).bit_position() == 8,
          "joined completed byte checkpoint changed clock");
  prefix = BytePrefix{};
  rejects([&]() { BitPredictor::restore(joined(schedule, prefix), component_bound); });
  auto truncated = initial; truncated.pop_back();
  rejects([&]() { BitPredictor::restore(truncated, component_bound); });
  auto trailing = initial; trailing.push_back(0);
  rejects([&]() { BitPredictor::restore(trailing, component_bound); });
}

void malformed_checkpoints() {
  Schedule model(Sentinel{}, Arm::P);
  const auto initial = model.serialize();
  rejects([&]() { Schedule(Sentinel{}, static_cast<Arm>(4)); });
  rejects([&]() { Schedule::restore(initial, 0); });
  for (const auto offset : {5, 6, 14, 22, 23}) {
    auto corrupt = initial; corrupt[offset] ^= 0x80;
    rejects([&]() { Schedule::restore(corrupt, component_bound); });
  }
  auto trailing = initial; trailing.push_back(0);
  rejects([&]() { Schedule::restore(trailing, component_bound); });
  auto truncated = initial; truncated.pop_back();
  rejects([&]() { Schedule::restore(truncated, component_bound); });
  model.predict_byte();
  auto pending = model.serialize(); pending[23] ^= 1;
  rejects([&]() { Schedule::restore(pending, component_bound); });
}
}  // namespace

int main() {
  try {
    check_update_law(); malformed_checkpoints(); malformed_joined_checkpoints();
    for (unsigned length : {0, 1, 31, 32, 33, 63, 64, 65, 128, 129}) {
      Bytes raw;
      for (unsigned i = 0; i != length; ++i)
        raw.push_back(static_cast<std::uint8_t>(i * 37));
      const auto parent = encode(raw, Arm::P);
      for (const auto arm : {Arm::P, Arm::K, Arm::F, Arm::S}) {
        const auto encoded = encode(raw, arm);
        if (arm == Arm::K)
          require(parent.payload == encoded.payload &&
                  parent.probabilities == encoded.probabilities &&
                  parent.identity_states == encoded.identity_states,
                  "P/K probability, finite payload or predictive state identity failed");
        check_inverse(raw, arm, encoded);
      }
    }
    std::cout << "sentinel-only midpoint scheduler: causal P/K/F/S, rebuild, "
                 "exact state synchronization, joined checkpoints and inverse passed\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
