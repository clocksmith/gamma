// Emit fixed post-warmup byte-context endpoints derived from causal WRT history.

#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr std::size_t kStoreHeaderBytes = 5;
constexpr std::size_t kTraceHeaderBytes = 16;
constexpr std::size_t kNodesPerContext = 255;

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  input.seekg(0, std::ios::end);
  const auto size = input.tellg();
  if (size < 0) throw std::runtime_error("cannot size " + path);
  input.seekg(0, std::ios::beg);
  std::vector<unsigned char> data(static_cast<std::size_t>(size));
  if (!data.empty()) input.read(reinterpret_cast<char*>(data.data()), size);
  if (!input) throw std::runtime_error("cannot read " + path);
  return data;
}

std::uint64_t ReadU64(const unsigned char* input) {
  std::uint64_t value = 0;
  for (unsigned int shift = 0; shift < 64; shift += 8) {
    value |= static_cast<std::uint64_t>(*input++) << shift;
  }
  return value;
}

std::uint16_t ReadU16(const unsigned char* input) {
  return static_cast<std::uint16_t>(input[0]) |
         static_cast<std::uint16_t>(input[1]) << 8;
}

void WriteU16(std::ofstream& output, std::uint16_t value) {
  const std::array<unsigned char, 2> bytes = {
      static_cast<unsigned char>(value & 255),
      static_cast<unsigned char>(value >> 8),
  };
  output.write(reinterpret_cast<const char*>(bytes.data()), bytes.size());
}

std::uint32_t Context(const unsigned char* stream, std::size_t position,
                      unsigned int order) {
  std::uint32_t value = 0;
  for (unsigned int index = order; index > 0; --index) {
    value = (value << 8) | stream[position - index];
  }
  return value;
}

std::size_t ContextCount(unsigned int order) {
  return std::size_t{1} << (8 * order);
}

std::vector<std::uint16_t> BuildTree(const std::vector<std::uint32_t>& counts,
                                     unsigned int order) {
  const std::size_t contexts = ContextCount(order);
  std::vector<std::uint16_t> tree(contexts * kNodesPerContext, 32768);
  std::array<std::uint64_t, 512> sums{};
  for (std::size_t context = 0; context < contexts; ++context) {
    sums.fill(0);
    const auto* row = counts.data() + context * 256;
    for (std::size_t symbol = 0; symbol < 256; ++symbol) {
      sums[256 + symbol] = row[symbol];
    }
    for (std::size_t node = 255; node > 0; --node) {
      sums[node] = sums[node * 2] + sums[node * 2 + 1];
    }
    for (std::size_t node = 1; node <= 255; ++node) {
      unsigned int depth = 0;
      for (std::size_t value = node; value > 1; value >>= 1) ++depth;
      const std::uint64_t symbols_per_child =
          std::uint64_t{1} << (7 - depth);
      const std::uint64_t numerator2 =
          2 * sums[node * 2 + 1] + symbols_per_child;
      const std::uint64_t denominator2 =
          2 * sums[node] + 2 * symbols_per_child;
      std::uint64_t probability =
          (numerator2 * 65536 + denominator2 / 2) / denominator2;
      probability = std::max<std::uint64_t>(
          1, std::min<std::uint64_t>(65535, probability));
      tree[context * kNodesPerContext + node - 1] =
          static_cast<std::uint16_t>(probability);
    }
  }
  return tree;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 6) {
      std::cerr << "usage: wrt_epoch_frozen_endpoint STORE BASE_P1 "
                   "WARMUP_WRT_BYTES OUTPUT_PREFIX MAX_ORDER\n";
      return 2;
    }
    const auto store = ReadFile(argv[1]);
    const auto base = ReadFile(argv[2]);
    const std::size_t warmup = std::stoull(argv[3]);
    const std::string output_prefix = argv[4];
    const unsigned int maximum_order = std::stoul(argv[5]);
    if (store.size() <= kStoreHeaderBytes || base.size() < kTraceHeaderBytes ||
        maximum_order > 2) {
      throw std::runtime_error("invalid input or order");
    }
    const unsigned char* stream = store.data() + kStoreHeaderBytes;
    const std::size_t stream_bytes = store.size() - kStoreHeaderBytes;
    const std::uint64_t rows = ReadU64(base.data() + 8);
    if (rows != stream_bytes * 8 ||
        base.size() != kTraceHeaderBytes + rows * 2 ||
        warmup > stream_bytes) {
      throw std::runtime_error("store/P1/warmup mismatch");
    }

    for (unsigned int order = 0; order <= maximum_order; ++order) {
      const std::size_t contexts = ContextCount(order);
      std::vector<std::uint32_t> counts(contexts * 256, 0);
      for (std::size_t position = order; position < warmup; ++position) {
        const auto context = Context(stream, position, order);
        auto& count = counts[static_cast<std::size_t>(context) * 256 +
                             stream[position]];
        if (count != UINT32_MAX) ++count;
      }
      const auto tree = BuildTree(counts, order);
      const std::string output_path =
          output_prefix + ".order" + std::to_string(order) + ".p1";
      std::ofstream output(output_path, std::ios::binary);
      if (!output) throw std::runtime_error("cannot open " + output_path);
      output.write(reinterpret_cast<const char*>(base.data()),
                   kTraceHeaderBytes);
      for (std::size_t position = 0; position < stream_bytes; ++position) {
        const std::uint32_t context =
            position >= order ? Context(stream, position, order) : 0;
        std::size_t node = 1;
        for (unsigned int bit_position = 0; bit_position < 8; ++bit_position) {
          const std::size_t row = position * 8 + bit_position;
          std::uint16_t probability = ReadU16(
              base.data() + kTraceHeaderBytes + row * 2);
          if (position >= warmup) {
            probability =
                tree[static_cast<std::size_t>(context) * kNodesPerContext +
                     node - 1];
          }
          WriteU16(output, probability);
          const unsigned int bit = (stream[position] >> (7 - bit_position)) & 1;
          node = node * 2 + bit;
        }
      }
      if (!output) throw std::runtime_error("cannot write " + output_path);
      std::cout << "{\"order\":" << order << ",\"warmup_wrt_bytes\":"
                << warmup << ",\"mature_wrt_bytes\":"
                << stream_bytes - warmup << ",\"contexts\":" << contexts
                << ",\"model_state_bytes\":" << counts.size() * 4 +
                                                    tree.size() * 2
                << ",\"output\":\"" << output_path << "\"}\n";
    }
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\n";
    return 1;
  }
  return 0;
}
