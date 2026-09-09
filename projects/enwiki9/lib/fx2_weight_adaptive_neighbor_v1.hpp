// Exact INT4 representation probe; no inference arithmetic changes.
// Reuses the GPLv3 FX2 range primitive; retain its provenance and LICENSE.
#pragma once
#include <functional>
#include "fx2_weight_neighbor_v1.hpp"

namespace fx2_weight_adaptive_neighbor_v1 {
using namespace fx2_weights_v1;
constexpr uint32_t kSymbols = fx2_weight_neighbor_v1::kSymbols;
constexpr char kMagic[] = "GFX2ADN1";
struct State {
  std::array<Histogram, 16> rows{};
  std::array<uint32_t, 16> totals{};
  State() { for (auto& row : rows) row.fill(1); totals.fill(15); }
  void observe(size_t context, uint8_t symbol) {
    require(context < 16 && symbol < 15, "invalid adaptive update");
    ++rows[context][symbol];
    if (++totals[context] >= 65536) {
      totals[context] = 0;
      for (auto& count : rows[context]) {
        count = (count + 1) / 2;
        totals[context] += count;
      }
    }
  }
};
// Diagnostic callback observes complete future-affecting count state before
// each truth, and once after the final update. Not stored in the archive.
using Witness = std::function<void(size_t, size_t, const State&)>;
inline size_t context(const Bytes& values, size_t k, uint32_t width, char arm) {
  return arm == 'A' ? 0 : k % width == 0 ? 15 : values[k - 1];
}
inline Bytes pack(const Bytes& values, uint32_t width, char arm,
                  const Witness& witness = {}) {
  require(arm == 'P' || arm == 'K' || arm == 'A' || arm == 'D', "unknown adaptive arm");
  require(values.size() <= kSymbols && width > 0 && width <= kSymbols, "invalid adaptive bounds");
  for (auto value : values) require(value < 15, "invalid INT4 symbol");
  if (arm == 'P') return fx2_weight_neighbor_v1::pack(values, width, 'P');
  State state;
  Encoder encoder;
  for (size_t k = 0; k < values.size(); ++k) {
    const auto c = context(values, k, width, arm);
    if (witness) witness(k, c, state);
    if (arm == 'A' || arm == 'D') {
      auto tree = fixed_tree(state.rows[c]);
      encoder.tree(tree.data(), 4, values[k], false);
    }
    state.observe(c, values[k]);
  }
  if (witness) witness(values.size(), 16, state);
  // P is the unchanged fixed marginal archive. K exercises the same adaptive
  // bookkeeping as D while emitting exactly P, including its original header.
  if (arm == 'P' || arm == 'K') return fx2_weight_neighbor_v1::pack(values, width, 'P');
  Bytes output(kMagic, kMagic + 8);
  output.push_back(arm == 'D');
  append_u32(output, uint32_t(values.size()));
  append_u32(output, width);
  const auto stream = encoder.finish();
  output.insert(output.end(), stream.begin(), stream.end());
  return output;
}
struct Restored { Bytes values; uint32_t width; char arm; };
inline Restored unpack(const Bytes& input, const Witness& witness = {}) {
  require(input.size() >= 17 && input.size() <= kFileLimit, "invalid adaptive file length");
  if (std::equal(input.begin(), input.begin() + 8, fx2_weight_neighbor_v1::kMagic)) {
    auto old = fx2_weight_neighbor_v1::unpack(input);
    require(!old.neighbor, "fixed neighbor is not an adaptive parent");
    if (witness) (void)pack(old.values, old.width, 'K', witness);
    return {std::move(old.values), old.width, 'P'};
  }
  require(std::equal(input.begin(), input.begin() + 8, kMagic) && input[8] <= 1,
          "invalid adaptive header");
  const char arm = input[8] ? 'D' : 'A';
  const uint32_t length = u32(input, 9), width = u32(input, 13);
  require(length <= kSymbols && width > 0 && width <= kSymbols, "invalid adaptive decoded bounds");
  State state;
  Decoder decoder(input, 17);
  Bytes values;
  values.reserve(length);
  for (size_t k = 0; k < length; ++k) {
    const auto c = context(values, k, width, arm);
    if (witness) witness(k, c, state);
    auto tree = fixed_tree(state.rows[c]);
    auto symbol = uint8_t(decoder.tree(tree.data(), 4, false));
    require(symbol < 15, "invalid adaptive decoded symbol");
    values.push_back(symbol);
    state.observe(c, symbol);
  }
  if (witness) witness(length, 16, state);
  require_identical(pack(values, width, arm), input, "noncanonical or truncated adaptive stream");
  return {std::move(values), width, arm};
}
}  // namespace fx2_weight_adaptive_neighbor_v1
