// Exact full-container comparison; preserve the included GPLv3 provenance.
#define main fx2_preserved_marginal_cli_main
#include "fx2_weight_marginal_probe_v1.cpp"
#undef main
#ifndef FX2_FIXED_ONLY
#include "../lib/fx2_weight_adaptive_marginal_v1.hpp"
#endif
int main(int argc, char** argv) {
  try {
    require(argc == 4, "usage: probe P|K|D|restore INPUT NEW_OUTPUT");
    const std::string mode = argv[1];
    require(mode == "P" || mode == "K" || mode == "D" || mode == "restore", "unknown mode");
    const Bytes input = read_file(argv[2]);
    Document document;
    bool adaptive_input = false;
#ifndef FX2_FIXED_ONLY
    adaptive_input = input.size() >= 8 && std::equal(input.begin(), input.begin()+8, kAdaptive);
    if (adaptive_input) {
      document = decode_adaptive(input);
      require_identical(encode_adaptive(document), input, "noncanonical adaptive input");
    } else
#endif
    {
      document = decode(input);
      require_identical(encode(document, document.format), input, "noncanonical original input");
    }
    Bytes output;
    if (mode == "restore") output = encode(document, Format::Parent);
    else if (mode == "D") {
#ifdef FX2_FIXED_ONLY
      throw std::runtime_error("adaptive encoding absent from fixed-only build");
#else
      output = encode_adaptive(document);
#endif
    } else {
#ifndef FX2_FIXED_ONLY
      if (mode == "K") {
        uint64_t witnessed = 0;
        for (const auto& tensor : document.tensors) if (tensor.encoding == 1) {
          AdaptiveCounts counts;
          for (uint8_t value : tensor.payload) counts.observe(value);
          witnessed += counts.total;
        }
        require(witnessed <= kExpandedLimit, "bookkeeping count bound");
      }
#endif
      output = encode(document, Format::Local);
    }
    write_new_file(argv[3], output);
    std::cout << "{\"mode\":" << quoted(mode) << ",\"input_bytes\":" << input.size()
              << ",\"output_bytes\":" << output.size() << ",\"adaptive_input\":"
              << (adaptive_input ? "true" : "false") << ",\"tensors\":" << document.tensors.size()
              << ",\"objective_credit_bytes\":0}\n";
    std::cout.flush();
    require(bool(std::cout), "receipt flush failed");
  } catch (const std::exception& error) {
    std::cerr << "fx2_weight_adaptive_marginal_probe_v1: " << error.what() << '\n'; return 1;
  }
}
