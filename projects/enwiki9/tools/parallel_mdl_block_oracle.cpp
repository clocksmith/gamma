// Zero-credit two-pass block MDL feasibility oracle for WRT bytes.

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

struct ContextSummary {
  std::uint64_t total = 0;
  std::uint32_t symbols = 0;
  double sum_log_factorial_counts = 0.0;
};

struct Cost {
  unsigned int order = 0;
  double free_bits = 0.0;
  double mdl_bits = 0.0;
  std::uint64_t contexts = 0;
  std::uint64_t transitions = 0;
};

Cost Measure(const std::vector<unsigned char>& data, std::size_t begin,
             std::size_t end, unsigned int order) {
  Cost result;
  result.order = order;
  if (begin == end) return result;
  const std::size_t first = std::min(end, begin + order);
  result.free_bits = static_cast<double>(first - begin) * 8.0;
  result.mdl_bits = result.free_bits;
  if (first == end) return result;

  std::unordered_map<std::uint64_t, std::uint32_t> pairs;
  pairs.reserve((end - first) * 2);
  for (std::size_t position = first; position < end; ++position) {
    const std::uint64_t context = Context(data, position, order);
    const std::uint64_t pair = (context << 8) | data[position];
    ++pairs[pair];
  }

  std::unordered_map<std::uint64_t, ContextSummary> contexts;
  contexts.reserve(pairs.size());
  for (const auto& [pair, count] : pairs) {
    const std::uint64_t context = pair >> 8;
    auto& summary = contexts[context];
    summary.total += count;
    ++summary.symbols;
    summary.sum_log_factorial_counts +=
        std::lgamma(static_cast<double>(count) + 1.0) / kLn2;
  }

  for (const auto& [context, summary] : contexts) {
    (void)context;
    const double total_log =
        std::lgamma(static_cast<double>(summary.total) + 1.0) / kLn2;
    const double sequence_bits =
        total_log - summary.sum_log_factorial_counts;
    result.free_bits +=
        static_cast<double>(summary.total) *
            std::log2(static_cast<double>(summary.total)) -
        [&]() {
          double value = 0.0;
          return value;
        }();
    const double symbol_set_bits = Log2Choose(256, summary.symbols);
    const double composition_bits =
        summary.symbols <= 1
            ? 0.0
            : Log2Choose(summary.total - 1, summary.symbols - 1);
    result.mdl_bits += sequence_bits + symbol_set_bits + composition_bits +
                       static_cast<double>(order) * 8.0;
  }

  // Recompute plug-in entropy directly from pair counts.
  result.free_bits = static_cast<double>(first - begin) * 8.0;
  for (const auto& [pair, count] : pairs) {
    const auto& summary = contexts.at(pair >> 8);
    result.free_bits += static_cast<double>(count) *
                        std::log2(static_cast<double>(summary.total) / count);
  }
  result.contexts = contexts.size();
  result.transitions = pairs.size();
  return result;
}

struct BlockChoice {
  Cost free;
  Cost mdl;
};

struct ScopeResult {
  std::size_t block_bytes = 0;
  std::size_t blocks = 0;
  double free_bits = 0.0;
  double mdl_bits = 0.0;
  std::vector<std::uint64_t> free_orders;
  std::vector<std::uint64_t> mdl_orders;
  std::uint64_t mdl_contexts = 0;
  std::uint64_t mdl_transitions = 0;
};

ScopeResult Screen(const std::vector<unsigned char>& data, std::size_t begin,
                   std::size_t block_bytes, unsigned int max_order) {
  ScopeResult result;
  result.block_bytes = block_bytes;
  result.free_orders.assign(max_order + 1, 0);
  result.mdl_orders.assign(max_order + 1, 0);
  for (std::size_t block_begin = begin; block_begin < data.size();
       block_begin += block_bytes) {
    const std::size_t block_end =
        std::min(data.size(), block_begin + block_bytes);
    BlockChoice choice;
    choice.free.free_bits = std::numeric_limits<double>::infinity();
    choice.mdl.mdl_bits = std::numeric_limits<double>::infinity();
    for (unsigned int order = 0; order <= max_order; ++order) {
      const Cost cost = Measure(data, block_begin, block_end, order);
      if (cost.free_bits < choice.free.free_bits) choice.free = cost;
      if (cost.mdl_bits < choice.mdl.mdl_bits) choice.mdl = cost;
    }
    result.free_bits += choice.free.free_bits + 8.0;
    result.mdl_bits += choice.mdl.mdl_bits + 8.0;
    ++result.free_orders[choice.free.order];
    ++result.mdl_orders[choice.mdl.order];
    result.mdl_contexts += choice.mdl.contexts;
    result.mdl_transitions += choice.mdl.transitions;
    ++result.blocks;
  }
  return result;
}

void PrintArray(const std::vector<std::uint64_t>& values) {
  std::cout << "[";
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index) std::cout << ",";
    std::cout << values[index];
  }
  std::cout << "]";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 6) {
      std::cerr << "usage: parallel_mdl_block_oracle STORE HEADER_BYTES "
                   "BASE_ARCHIVE_BYTES REQUIRED_SAVINGS_BYTES MAX_ORDER\n";
      return 2;
    }
    const std::string path = argv[1];
    const std::size_t header_bytes = std::stoull(argv[2]);
    const std::uint64_t base_archive_bytes = std::stoull(argv[3]);
    const std::int64_t required_savings_bytes = std::stoll(argv[4]);
    const unsigned int max_order = std::stoul(argv[5]);
    const auto data = ReadFile(path);
    if (header_bytes >= data.size()) throw std::runtime_error("invalid header");

    const std::vector<std::size_t> block_sizes = {65536, 262144, 1048576};
    std::vector<ScopeResult> results;
    for (const auto block_size : block_sizes) {
      results.push_back(Screen(data, header_bytes, block_size, max_order));
    }
    const auto free_best = std::min_element(
        results.begin(), results.end(),
        [](const ScopeResult& a, const ScopeResult& b) {
          return a.free_bits < b.free_bits;
        });
    const auto mdl_best = std::min_element(
        results.begin(), results.end(),
        [](const ScopeResult& a, const ScopeResult& b) {
          return a.mdl_bits < b.mdl_bits;
        });
    const auto free_bytes =
        static_cast<std::uint64_t>(std::ceil(free_best->free_bits / 8.0));
    const auto mdl_bytes =
        static_cast<std::uint64_t>(std::ceil(mdl_best->mdl_bits / 8.0));
    const std::int64_t free_savings =
        static_cast<std::int64_t>(base_archive_bytes) - free_bytes;
    const std::int64_t mdl_savings =
        static_cast<std::int64_t>(base_archive_bytes) - mdl_bytes;
    const bool pass = mdl_savings >= required_savings_bytes;

    std::cout << std::fixed << std::setprecision(3);
    std::cout << "{\"schema\":\"parallel_mdl_block_oracle_v1\","
              << "\"evidence_level\":\"zero_credit_two_pass_mdl_bound\","
              << "\"store_bytes\":" << data.size() << ","
              << "\"header_bytes\":" << header_bytes << ","
              << "\"base_archive_bytes\":" << base_archive_bytes << ","
              << "\"required_savings_bytes\":" << required_savings_bytes << ","
              << "\"free_best\":{\"block_bytes\":" << free_best->block_bytes
              << ",\"coded_bytes\":" << free_bytes
              << ",\"savings_bytes\":" << free_savings << "},"
              << "\"mdl_best\":{\"block_bytes\":" << mdl_best->block_bytes
              << ",\"coded_bytes\":" << mdl_bytes
              << ",\"savings_bytes\":" << mdl_savings
              << ",\"contexts\":" << mdl_best->mdl_contexts
              << ",\"transitions\":" << mdl_best->mdl_transitions
              << ",\"selected_orders\":";
    PrintArray(mdl_best->mdl_orders);
    std::cout << "},\"pass\":" << (pass ? "true" : "false")
              << ",\"decision\":\""
              << (pass ? "authorize_constructive_parallel_mdl"
                       : free_savings < required_savings_bytes
                             ? "retire_parallel_mdl_v1_information_bound"
                             : "retire_parallel_mdl_v1_model_cost")
              << "\"}\n";
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\n";
    return 1;
  }
  return 0;
}
