// Prospective fixed-marginal FX2 weight comparison; no codec or prize credit.
// Uses Gamma's derived GPLv3 tensor primitive; preserve the pinned upstream
// LICENSE and provenance recorded in ../lib/fx2_weight_format_v1.hpp.
// P: original coding. K: histogram bookkeeping, original coding unchanged.
// D/G: identical explicit histograms, fixed local/global INT4 probabilities.
#include "../lib/fx2_weight_format_v1.hpp"

#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace {
using namespace fx2_weights_v1;
Bytes read_file(const std::string& path) {
  std::ifstream input(path, std::ios::binary | std::ios::ate);
  require(bool(input), "cannot open input");
  const auto length = input.tellg();
  require(length >= 0 && uint64_t(length) <= kFileLimit, "input exceeds file bound");
  Bytes bytes(static_cast<size_t>(length));
  input.seekg(0);
  input.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
  require(bool(input), "cannot read complete input");
  return bytes;
}
void write_new_file(const std::string& path, const Bytes& bytes) {
  const std::string temporary = path + ".partial";
  FILE* file = std::fopen(temporary.c_str(), "wbx");
  require(file != nullptr, "temporary output exists or cannot be created exclusively");
  const bool written = std::fwrite(bytes.data(), 1, bytes.size(), file) == bytes.size();
  const bool closed = std::fclose(file) == 0;
  std::error_code publication_error, cleanup_error;
  if (written && closed) std::filesystem::create_hard_link(temporary, path, publication_error);
  std::filesystem::remove(temporary, cleanup_error);
  if (cleanup_error) throw std::runtime_error("temporary cleanup failed: " + cleanup_error.message());
  require(written && closed, "output write/close failed");
  if (publication_error) throw std::runtime_error("output publication failed: " + publication_error.message());
}
std::string quoted(const std::string& value) {
  std::string result = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (unsigned char ch : value) {
    if (ch == '\\' || ch == '"') { result.push_back('\\'); result.push_back(char(ch)); }
    else if (ch < 32 || ch >= 127) {
      result += "\\u00";
      result.push_back(hex[ch >> 4]); result.push_back(hex[ch & 15]);
    } else result.push_back(char(ch));
  }
  return result + '"';
}
const char* format_name(Format format) {
  return format == Format::Parent ? kParent : format == Format::Local ? "GFX2MAR1-D" : "GFX2MAR1-G";
}
}  // namespace

int main(int argc, char** argv) {
  try {
    require(argc == 4, "usage: fx2_weight_marginal_probe_v1 P|K|D|G|restore INPUT OUTPUT");
    const std::string mode = argv[1];
    require(mode == "P" || mode == "K" || mode == "D" || mode == "G" || mode == "restore", "unknown mode");
    const Bytes input = read_file(argv[2]);
    const Document document = decode(input);
    require_identical(encode(document, document.format), input, "input does not regenerate byte-identically with its own coder");
    const Format output_format = mode == "D" ? Format::Local : mode == "G" ? Format::Global : Format::Parent;
    // K deliberately runs the same encoder as P; its extra work is observable
    // histogram bookkeeping only. D/G transmit their independently checked counts.
    Histograms bookkeeping;
    if (mode == "K" || output_format != Format::Parent) bookkeeping = histograms(document);
    const Bytes output = encode(document, output_format);
    const Bytes parent = encode(document, Format::Parent);
    {
      const Document inverse = decode(output);
      require_identical(encode(inverse, document.format), input, "inverse does not regenerate original input bytes");
      require_identical(encode(inverse, Format::Parent), parent, "inverse does not regenerate original parent bytes");
    }
    {
      const Document repeat = decode(input);
      require_identical(encode(repeat, output_format), output, "repeat transcode differs");
    }
    write_new_file(argv[3], output);
    const size_t header_bytes = read_header(output).stream_offset;
    std::cout << "{\"schema\":\"gamma.fx2-weight-marginal-probe.v1\",\"mode\":" << quoted(mode)
              << ",\"input_format\":" << quoted(format_name(document.format))
              << ",\"output_format\":" << quoted(format_name(output_format))
              << ",\"input_bytes\":" << input.size() << ",\"output_bytes\":" << output.size()
              << ",\"original_stream_regeneration_ok\":true,\"inverse_ok\":true,\"repeat_ok\":true"
              << ",\"objective_credit_bytes\":0,\"tensor_payload_bytes\":" << document.stored_payload_bytes
              << ",\"regenerated_rope_bytes\":" << document.regenerated_rope_bytes
              << ",\"header_bytes\":" << header_bytes << ",\"side_information_bytes\":" << header_bytes - 12
              << ",\"bookkeeping_int4_tensors\":" << bookkeeping.local.size() << ",\"tensors\":[";
    bool first = true;
    for (const auto& tensor : document.tensors) {
      if (!first) std::cout << ',';
      first = false;
      std::cout << "{\"name\":" << quoted(tensor.name) << ",\"dtype\":" << tensor.dtype
                << ",\"encoding\":" << tensor.encoding << ",\"elements\":" << tensor.elements
                << ",\"represented_bytes\":" << tensor.represented_bytes
                << ",\"stored_payload_bytes\":" << tensor.payload.size()
                << ",\"row_width\":" << tensor.row_width << ",\"shape\":[";
      for (size_t k = 0; k < tensor.shape.size(); ++k) {
        if (k) std::cout << ',';
        std::cout << tensor.shape[k];
      }
      std::cout << "]}";
    }
    std::cout << "]}\n";
    std::cout.flush();
    require(bool(std::cout), "receipt stdout flush failed");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "fx2_weight_marginal_probe_v1: " << error.what() << '\n';
    return 1;
  }
}
