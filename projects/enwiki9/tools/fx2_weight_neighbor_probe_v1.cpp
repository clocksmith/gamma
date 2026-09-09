// GPLv3 derived representation probe; preserve fx2_weight_format_v1.hpp provenance.
// Input symbols are offset INT4 values 0..14, not corpus bytes or float weights.
#include "../lib/fx2_weight_neighbor_v1.hpp"
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
using namespace fx2_weight_neighbor_v1;
Bytes read(const std::string& path) {
  std::ifstream file(path, std::ios::binary | std::ios::ate);
  require(bool(file), "cannot open input");
  const auto length = file.tellg();
  require(length >= 0 && uint64_t(length) <= kFileLimit, "input exceeds bound");
  Bytes result(static_cast<size_t>(length));
  file.seekg(0); file.read(reinterpret_cast<char*>(result.data()), result.size());
  require(bool(file), "input read failed");
  return result;
}
void write_new(const std::string& path, const Bytes& bytes) {
  // Same exclusive publication law as the preserved marginal probe.
  const std::string temporary = path + ".partial";
  FILE* file = std::fopen(temporary.c_str(), "wbx");
  require(file != nullptr, "temporary output exists or cannot be created");
  const bool written = std::fwrite(bytes.data(), 1, bytes.size(), file) == bytes.size();
  const bool closed = std::fclose(file) == 0;
  std::error_code publish_error, cleanup_error;
  if (written && closed) std::filesystem::create_hard_link(temporary, path, publish_error);
  std::filesystem::remove(temporary, cleanup_error);
  require(!cleanup_error && written && closed && !publish_error, "exclusive output publication failed");
}
int main(int argc, char** argv) {
  try {
    require(argc == 4 || argc == 5, "usage: probe P|K|D INPUT OUTPUT WIDTH; probe restore INPUT OUTPUT");
    const std::string mode = argv[1];
    const Bytes input = read(argv[2]);
    Bytes output;
    if (mode == "restore") {
      require(argc == 4, "restore requires no width");
      output = unpack(input).values;
    } else {
      require(argc == 5 && mode.size() == 1 &&
                  (mode == "P" || mode == "K" || mode == "D"), "invalid encode arguments");
      const std::string width_text = argv[4];
      require(!width_text.empty() && width_text.find_first_not_of("0123456789") == std::string::npos,
              "width must be unsigned decimal");
      size_t consumed = 0;
      const auto width = std::stoull(width_text, &consumed);
      require(consumed == width_text.size() && width > 0 && width <= kSymbols, "width exceeds bound");
      output = pack(input, uint32_t(width), mode[0]);
    }
    write_new(argv[3], output);
    std::cout << "{\"input_bytes\":" << input.size() << ",\"output_bytes\":" << output.size()
              << ",\"objective_credit_bytes\":0}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "fx2_weight_neighbor_probe_v1: " << error.what() << '\n'; return 1;
  }
}
