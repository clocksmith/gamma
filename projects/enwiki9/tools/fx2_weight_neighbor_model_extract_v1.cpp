// Laboratory-only adapter reusing the measured CLI's exact file operations.
// No changes to the substream codec or preserved public model reader.
#define main fx2_neighbor_existing_cli_main
#include "fx2_weight_neighbor_probe_v1.cpp"
#undef main
int main(int argc, char** argv) {
  try {
    require(argc == 3, "usage: extractor MODEL NEW_OUTPUT_DIRECTORY");
    const auto input = read(argv[1]);
    const auto document = decode(input);
    require_identical(encode(document, document.format), input, "noncanonical source model");
    const std::filesystem::path output = argv[2];
    require(std::filesystem::create_directory(output), "extraction directory already exists");
    size_t symbols = 0, count = 0;
    std::cout << "{\"tensors\":" << document.tensors.size() << ",\"rows\":[";
    for (size_t k = 0; k < document.tensors.size(); ++k) {
      const auto& tensor = document.tensors[k];
      if (tensor.encoding != 1) continue;
      require(tensor.payload.size() <= kSymbols && tensor.row_width > 0 &&
                  tensor.row_width <= kSymbols, "tensor exceeds substream bounds");
      write_new((output / (std::to_string(k) + ".raw")).string(), tensor.payload);
      if (count++) std::cout << ',';
      std::cout << "{\"index\":" << k << ",\"symbols\":" << tensor.payload.size()
                << ",\"width\":" << tensor.row_width << '}';
      symbols += tensor.payload.size();
    }
    std::cout << "],\"int4_tensors\":" << count << ",\"int4_symbols\":" << symbols
              << ",\"canonical_original_regeneration\":true}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "fx2_weight_neighbor_model_extract_v1: " << error.what() << '\n'; return 1;
  }
}
