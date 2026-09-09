// Exact bounded INT4 substreams using the existing GPLv3 FX2 range primitive.
// Preserve the provenance and upstream LICENSE of fx2_weight_format_v1.hpp.
// This is a representation probe, not a native inference format.
#pragma once
#include "fx2_weight_format_v1.hpp"

namespace fx2_weight_neighbor_v1 {
using namespace fx2_weights_v1;
constexpr uint32_t kSymbols = 1u << 20;
constexpr char kMagic[] = "GFX2NBR1";
using Counts = std::vector<Histogram>;
inline size_t context(const Bytes& values, size_t k, uint32_t width, bool neighbor) {
  return !neighbor ? 0 : k % width == 0 ? 15 : values[k - 1];
}
inline Counts counts(const Bytes& values, uint32_t width, bool neighbor) {
  require(values.size() <= kSymbols && width > 0 && width <= kSymbols,
          "invalid symbol count or row width");
  Counts result(neighbor ? 16 : 1);
  for (size_t k = 0; k < values.size(); ++k) {
    require(values[k] < 15, "symbol outside INT4 alphabet");
    ++result[context(values, k, width, neighbor)][values[k]];
  }
  return result;
}
inline Bytes pack(const Bytes& values, uint32_t width, char arm) {
  require(arm == 'P' || arm == 'K' || arm == 'D', "unknown neighbor arm");
  if (arm == 'K') (void)counts(values, width, true);
  const bool neighbor = arm == 'D';
  const auto table = counts(values, width, neighbor);
  Bytes output(kMagic, kMagic + 8);
  output.push_back(neighbor);
  append_u32(output, uint32_t(values.size()));
  append_u32(output, width);
  std::vector<std::array<uint16_t, 16>> trees;
  for (const auto& row : table) {
    for (uint32_t count : row) append_u32(output, count);
    trees.push_back(fixed_tree(row));
  }
  Encoder encoder;
  for (size_t k = 0; k < values.size(); ++k)
    encoder.tree(trees[context(values, k, width, neighbor)].data(), 4, values[k], false);
  const auto stream = encoder.finish();
  output.insert(output.end(), stream.begin(), stream.end());
  return output;
}
struct Restored { Bytes values; uint32_t width; bool neighbor; };
inline Restored unpack(const Bytes& input) {
  require(input.size() >= 17 && input.size() <= kFileLimit &&
              std::equal(input.begin(), input.begin() + 8, kMagic), "invalid neighbor header");
  require(input[8] <= 1, "unknown neighbor mode");
  const bool neighbor = input[8];
  const uint32_t length = u32(input, 9), width = u32(input, 13);
  require(length <= kSymbols && width > 0 && width <= kSymbols, "invalid decoded bounds");
  Counts table(neighbor ? 16 : 1);
  size_t offset = 17;
  uint64_t total = 0;
  std::vector<std::array<uint16_t, 16>> trees;
  for (auto& row : table) {
    for (auto& value : row) {
      value = u32(input, offset); offset += 4;
      require(value <= length, "count exceeds decoded length");
      total += value;
    }
    trees.push_back(fixed_tree(row));
  }
  require(total == length, "counts differ from decoded length");
  Decoder decoder(input, offset);
  Bytes values;
  values.reserve(length);
  for (size_t k = 0; k < length; ++k) {
    auto& tree = trees[context(values, k, width, neighbor)];
    const auto value = uint8_t(decoder.tree(tree.data(), 4, false));
    require(value < 15, "decoded symbol outside INT4 alphabet");
    values.push_back(value);
  }
  require(counts(values, width, neighbor) == table, "decoded counts differ");
  require_identical(pack(values, width, neighbor ? 'D' : 'P'), input,
                    "noncanonical or truncated neighbor stream");
  return {std::move(values), width, neighbor};
}
}  // namespace fx2_weight_neighbor_v1
