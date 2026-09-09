// Reuse immutable file IO; preserve the upstream FX2 GPLv3 provenance.
#define main fx2_neighbor_preserved_cli_main
#include "fx2_weight_neighbor_probe_v1.cpp"
#undef main
#include "../lib/fx2_weight_adaptive_neighbor_v1.hpp"
int main(int argc, char** argv) {
  try {
    require(argc == 4 || argc == 5, "usage: probe P|K|A|D INPUT OUTPUT WIDTH; probe restore INPUT OUTPUT");
    const std::string mode = argv[1];
    const Bytes input = read(argv[2]);
    Bytes output;
    if (mode == "restore") {
      require(argc == 4, "restore requires no width");
      output = fx2_weight_adaptive_neighbor_v1::unpack(input).values;
    } else {
      require(argc == 5 && mode.size() == 1 && mode.find_first_not_of("PKAD") == std::string::npos,
              "invalid encode arguments");
      const std::string number = argv[4];
      require(!number.empty() && number.find_first_not_of("0123456789") == std::string::npos,
              "width must be unsigned decimal");
      const auto width = std::stoull(number);
      require(width > 0 && width <= kSymbols, "invalid row width");
      output = fx2_weight_adaptive_neighbor_v1::pack(input, uint32_t(width), mode[0]);
    }
    write_new(argv[3], output);
    std::cout << "{\"input_bytes\":" << input.size() << ",\"output_bytes\":" << output.size()
              << ",\"objective_credit_bytes\":0}\n";
  } catch (const std::exception& error) {
    std::cerr << "fx2_weight_adaptive_neighbor_probe_v1: " << error.what() << '\n'; return 1;
  }
}
