// Exact container probe. Preserve the inherited FX2 GPLv3 source notices.
#define main fx2_preserved_marginal_cli_main
#include "fx2_weight_marginal_probe_v1.cpp"
#undef main
#include "../lib/fx2_weight_adaptive_marginal_v1.hpp"
#include "fx2_width_carry_generated.hpp"
namespace {
Bytes count_trace;
void witness(uint32_t width, const Histogram& counts, uint8_t value) {
  require(count_trace.size() <= 32 * 1024 * 1024 - 65, "count trace exceeds bound");
  append_u32(count_trace, width);
  for (auto count : counts) append_u32(count_trace, count);
  count_trace.push_back(value);
}
}
int main(int argc, char** argv) {
  try {
    require(argc == 4 || argc == 5, "usage: probe P|K|D|restore INPUT NEW_OUTPUT [NEW_TRACE]");
    const std::string mode = argv[1];
    require(mode == "P" || mode == "K" || mode == "D" || mode == "restore", "invalid mode");
    const Bytes input = read_file(argv[2]);
    Document document;
    if (input.size() >= 8 && std::equal(input.begin(), input.begin()+8, kWidthCarry)) {
      document = decode_width_carry(input, argc == 5 ? witness : nullptr);
      require_identical(encode_width_carry(document), input, "noncanonical width-carry input");
    } else if (input.size() >= 8 && std::equal(input.begin(), input.begin()+8, kAdaptive)) {
      document = decode_adaptive(input);
      require_identical(encode_adaptive(document), input, "noncanonical adaptive input");
    } else {
      document = decode(input);
      require_identical(encode(document, document.format), input, "noncanonical original input");
    }
    Bytes output;
    if (mode == "restore") output = encode(document, Format::Parent);
    else if (mode == "D") output = encode_width_carry(document, argc == 5 ? witness : nullptr);
    else {
      if (mode == "K") {
        std::map<uint32_t, WidthCounts> bank;
        for (const auto& tensor : document.tensors) if (tensor.encoding == 1) {
          auto& counts = bank[tensor.shape.empty() ? 1 : tensor.shape.back()];
          for (auto value : tensor.payload) counts.observe(value);
        }
      }
      output = encode_adaptive(document);
    }
    write_new_file(argv[3], output);
    if (argc == 5) write_new_file(argv[4], count_trace);
    std::cout << "{\"mode\":" << quoted(mode) << ",\"archive_bytes\":" << output.size()
              << ",\"count_trace_bytes\":" << count_trace.size() << ",\"objective_credit_bytes\":0}\n";
  } catch (const std::exception& error) {
    std::cerr << "fx2_weight_width_carry_probe_v1: " << error.what() << '\n'; return 1;
  }
}
