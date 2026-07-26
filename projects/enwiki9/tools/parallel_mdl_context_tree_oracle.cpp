// Sparse two-pass context-tree MDL bound with bottom-up paid splitting.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

constexpr double kLn2 = 0.693147180559945309417232121458176568;

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

double Log2Choose(std::uint64_t n, std::uint64_t k) {
  if (k > n) return std::numeric_limits<double>::infinity();
  if (k == 0 || k == n) return 0.0;
  return (std::lgamma(static_cast<double>(n) + 1.0) -
          std::lgamma(static_cast<double>(k) + 1.0) -
          std::lgamma(static_cast<double>(n - k) + 1.0)) /
         kLn2;
}

std::uint64_t Context(const std::vector<unsigned char>& data,
                      std::size_t position, unsigned int order) {
  std::uint64_t value = 0;
  for (unsigned int index = order; index > 0; --index) {
    value = (value << 8) | data[position - index];
  }
  return value;
}

struct Node {
  std::uint64_t total = 0;
  std::uint32_t symbols = 0;
  double sum_log_factorial_counts = 0.0;
  double leaf_bits = 0.0;
};

using Nodes = std::unordered_map<std::uint64_t, Node>;

Nodes BuildNodes(const std::vector<unsigned char>& data, std::size_t begin,
                 std::size_t end, unsigned int order,
                 unsigned int maximum_order) {
  std::unordered_map<std::uint64_t, std::uint32_t> pairs;
  const std::size_t first = std::min(end, begin + maximum_order);
  pairs.reserve((end - first) * 2);
  for (std::size_t position = first; position < end; ++position) {
    const std::uint64_t context = Context(data, position, order);
    ++pairs[(context << 8) | data[position]];
  }
  Nodes nodes;
  nodes.reserve(pairs.size());
  for (const auto& [pair, count] : pairs) {
    auto& node = nodes[pair >> 8];
    node.total += count;
    ++node.symbols;
    node.sum_log_factorial_counts +=
        std::lgamma(static_cast<double>(count) + 1.0) / kLn2;
  }
  for (auto& [context, node] : nodes) {
    (void)context;
    const double sequence =
        std::lgamma(static_cast<double>(node.total) + 1.0) / kLn2 -
        node.sum_log_factorial_counts;
    const double symbol_set = Log2Choose(256, node.symbols);
    const double composition =
        node.symbols <= 1 ? 0.0
                          : Log2Choose(node.total - 1, node.symbols - 1);
    node.leaf_bits = sequence + symbol_set + composition;
  }
  return nodes;
}

struct Choice {
  double bits = 0.0;
  std::uint64_t leaves = 0;
  std::uint64_t splits = 0;
};

Choice Prune(const std::vector<Nodes>& levels, unsigned int maximum_order) {
  std::unordered_map<std::uint64_t, Choice> child_choices;
  child_choices.reserve(levels[maximum_order].size());
  for (const auto& [context, node] : levels[maximum_order]) {
    child_choices[context] = Choice{node.leaf_bits + 1.0, 1, 0};
  }

  for (unsigned int depth = maximum_order; depth > 0; --depth) {
    const unsigned int parent_depth = depth - 1;
    const std::uint64_t parent_mask =
        parent_depth == 0 ? 0 : ((std::uint64_t{1} << (8 * parent_depth)) - 1);
    struct Split {
      double bits = 0.0;
      std::uint32_t children = 0;
      std::uint64_t leaves = 0;
      std::uint64_t splits = 0;
    };
    std::unordered_map<std::uint64_t, Split> split_costs;
    split_costs.reserve(levels[parent_depth].size());
    for (const auto& [context, choice] : child_choices) {
      const std::uint64_t parent = parent_depth == 0 ? 0 : context & parent_mask;
      auto& split = split_costs[parent];
      split.bits += choice.bits;
      ++split.children;
      split.leaves += choice.leaves;
      split.splits += choice.splits;
    }

    std::unordered_map<std::uint64_t, Choice> parent_choices;
    parent_choices.reserve(levels[parent_depth].size());
    for (const auto& [context, node] : levels[parent_depth]) {
      const Choice leaf{node.leaf_bits + 1.0, 1, 0};
      const auto found = split_costs.find(context);
      if (found == split_costs.end()) {
        parent_choices[context] = leaf;
        continue;
      }
      const Split& children = found->second;
      const Choice split{
          1.0 + Log2Choose(256, children.children) + children.bits,
          children.leaves,
          children.splits + 1,
      };
      parent_choices[context] = split.bits < leaf.bits ? split : leaf;
    }
    child_choices = std::move(parent_choices);
  }
  const auto root = child_choices.find(0);
  if (root == child_choices.end()) return {};
  return root->second;
}

struct Result {
  std::size_t block_bytes = 0;
  std::uint64_t blocks = 0;
  double bits = 0.0;
  std::uint64_t leaves = 0;
  std::uint64_t splits = 0;
};

Result Screen(const std::vector<unsigned char>& data, std::size_t begin,
              std::size_t block_bytes, unsigned int maximum_order) {
  Result result;
  result.block_bytes = block_bytes;
  for (std::size_t block_begin = begin; block_begin < data.size();
       block_begin += block_bytes) {
    const std::size_t block_end =
        std::min(data.size(), block_begin + block_bytes);
    std::vector<Nodes> levels;
    levels.reserve(maximum_order + 1);
    for (unsigned int order = 0; order <= maximum_order; ++order) {
      levels.push_back(
          BuildNodes(data, block_begin, block_end, order, maximum_order));
    }
    const Choice choice = Prune(levels, maximum_order);
    const std::size_t literal_prefix =
        std::min<std::size_t>(maximum_order, block_end - block_begin);
    result.bits += choice.bits + literal_prefix * 8.0 + 8.0;
    result.leaves += choice.leaves;
    result.splits += choice.splits;
    ++result.blocks;
  }
  return result;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 6) {
      std::cerr << "usage: parallel_mdl_context_tree_oracle STORE HEADER_BYTES "
                   "BASE_ARCHIVE_BYTES REQUIRED_SAVINGS_BYTES MAX_ORDER\n";
      return 2;
    }
    const auto data = ReadFile(argv[1]);
    const std::size_t header_bytes = std::stoull(argv[2]);
    const std::uint64_t base_archive_bytes = std::stoull(argv[3]);
    const std::int64_t required_savings_bytes = std::stoll(argv[4]);
    const unsigned int maximum_order = std::stoul(argv[5]);
    if (header_bytes >= data.size() || maximum_order > 7) {
      throw std::runtime_error("invalid header or order");
    }
    const std::vector<std::size_t> block_sizes = {65536, 262144, 1048576};
    std::vector<Result> results;
    for (const auto size : block_sizes) {
      results.push_back(
          Screen(data, header_bytes, size, maximum_order));
    }
    const auto best = std::min_element(
        results.begin(), results.end(),
        [](const Result& left, const Result& right) {
          return left.bits < right.bits;
        });
    const auto coded_bytes =
        static_cast<std::uint64_t>(std::ceil(best->bits / 8.0));
    const std::int64_t savings =
        static_cast<std::int64_t>(base_archive_bytes) - coded_bytes;
    const bool pass = savings >= required_savings_bytes;
    std::cout << std::fixed << std::setprecision(3)
              << "{\"schema\":\"parallel_mdl_context_tree_oracle_v1\","
              << "\"evidence_level\":\"zero_credit_pruned_two_pass_mdl_bound\","
              << "\"store_bytes\":" << data.size() << ","
              << "\"header_bytes\":" << header_bytes << ","
              << "\"base_archive_bytes\":" << base_archive_bytes << ","
              << "\"required_savings_bytes\":" << required_savings_bytes << ","
              << "\"maximum_order\":" << maximum_order << ","
              << "\"best\":{\"block_bytes\":" << best->block_bytes
              << ",\"blocks\":" << best->blocks
              << ",\"coded_bytes\":" << coded_bytes
              << ",\"savings_bytes\":" << savings
              << ",\"leaves\":" << best->leaves
              << ",\"splits\":" << best->splits << "},"
              << "\"pass\":" << (pass ? "true" : "false")
              << ",\"decision\":\""
              << (pass ? "authorize_constructive_parallel_mdl"
                       : "retire_pruned_parallel_mdl_v1")
              << "\"}\n";
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\n";
    return 1;
  }
  return 0;
}
