// Exact even7 approximation/XOR-residual representation of public FX2 weights.
// Derived metadata/coder traversal from Gamma's GPLv3 fx2_weight_format_v1.hpp,
// itself derived from astOwOlfo/fx2-cmix-transformer-v1 commit
// 83f2603f3f7751da5f429fd32669807eb8510494. Preserve the upstream GPLv3 LICENSE.
//
// GFX2XOR1: same paid histogram header as GFX2MAR1-D (mode must be 1), then
// one range stream. Each INT4 signed byte b is represented by hat_b and
// e=b XOR hat_b. hat_q is clamp(2*round_ties_even(q/2),-6,6). First code
// (hat_q+6)/2 in a fixed 8-leaf tree; then code e in the fixed alphabet
// {0,1,3,7,255} using an 8-leaf tree conditioned on that approximation.
// All probabilities derive solely from the paid original 15-bin histogram.
// For a nonempty two-sided branch p0=clamp(round_half_up(2048*L/N),1,2047).
// One-sided branches emit no bit; absent/unused leaves reject. No adaptation.
// BF16, raw, metadata, tensor order and generated RoPE records are unchanged.
// H(hat_b,e)=H(b): mere exact factorization has no ideal entropy advantage.
// This tool measures representation bytes; it neither qualifies a package nor
// executes inference. The runner must count this restore code and dependencies.
#include "../lib/fx2_weight_format_v1.hpp"

#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace {
using namespace fx2_weights_v1;
constexpr char kExact[] = "GFX2XOR1";
constexpr std::array<uint8_t, 5> kResidual{{0, 1, 3, 7, 255}};

int approximation(int q) {
  require(q >= -7 && q <= 7, "signed weight outside INT4 domain");
  const int magnitude = q < 0 ? -q : q;
  const int half = magnitude / 2;
  const int rounded = std::min(6, 2 * (half + ((magnitude & 1) && (half & 1))));
  return q < 0 ? -rounded : rounded;
}
std::pair<unsigned, unsigned> split(uint8_t symbol) {
  require(symbol < 15, "invalid original INT4 symbol");
  const int q = int(symbol) - 7, hat = approximation(q);
  const uint8_t residual = uint8_t(q) ^ uint8_t(hat);
  const auto found = std::find(kResidual.begin(), kResidual.end(), residual);
  require(found != kResidual.end(), "unrepresentable XOR residual");
  return {unsigned((hat + 6) / 2), unsigned(found - kResidual.begin())};
}
uint8_t join(unsigned a, unsigned e) {
  require(a < 7 && e < kResidual.size(), "unused approximation/residual leaf");
  const int hat = int(a) * 2 - 6;
  const unsigned original = uint8_t(hat) ^ kResidual[e];
  const int q = original < 128 ? int(original) : int(original) - 256;
  require(q >= -7 && q <= 7, "XOR reconstruction outside INT4 domain");
  const auto pair = split(uint8_t(q + 7));
  require(pair.first == a && pair.second == e, "noncanonical approximation/residual pair");
  return uint8_t(q + 7);
}

struct Tree {
  std::array<uint64_t, 16> counts{};
  void finish() { for (unsigned n = 7; n; --n) counts[n] = counts[2*n] + counts[2*n+1]; }
  uint16_t probability(unsigned node) const {
    require(node && node < 8 && counts[node], "empty probability branch");
    return uint16_t(std::clamp<uint64_t>((2048 * counts[2*node] + counts[node]/2) / counts[node], 1, 2047));
  }
  void put(Encoder& coder, unsigned symbol) const {
    require(symbol < 8 && counts[8+symbol], "encoding an absent leaf");
    unsigned node = 1;
    for (unsigned shift = 3; shift; --shift) {
      const unsigned bit = (symbol >> (shift-1)) & 1;
      if (counts[2*node] && counts[2*node+1]) {
        uint16_t probabilities[2]{0, probability(node)};
        coder.tree(probabilities, 1, bit, false);
      }
      node = 2*node + bit;
    }
  }
  unsigned get(Decoder& coder) const {
    unsigned node = 1;
    for (unsigned depth = 0; depth < 3; ++depth) {
      require(counts[node], "decoding an empty branch");
      unsigned bit = counts[2*node] ? 0 : 1;
      if (counts[2*node] && counts[2*node+1]) {
        uint16_t probabilities[2]{0, probability(node)};
        bit = coder.tree(probabilities, 1, false);
      }
      node = 2*node + bit;
    }
    require(counts[node], "decoded an absent leaf");
    return node - 8;
  }
};
struct Joint {
  Tree approximate;
  std::array<Tree, 7> residual;
  explicit Joint(const Histogram& histogram) {
    for (unsigned symbol = 0; symbol < 15; ++symbol) {
      const auto pair = split(uint8_t(symbol));
      approximate.counts[8+pair.first] += histogram[symbol];
      residual[pair.first].counts[8+pair.second] += histogram[symbol];
    }
    approximate.finish();
    for (auto& tree : residual) tree.finish();
  }
  void put(Encoder& coder, uint8_t symbol) const {
    const auto pair = split(symbol);
    approximate.put(coder, pair.first);
    residual[pair.first].put(coder, pair.second);
  }
  uint8_t get(Decoder& coder) const {
    const unsigned a = approximate.get(coder);
    require(a < residual.size(), "unused approximation leaf");
    return join(a, residual[a].get(coder));
  }
};

bool is_exact(const Bytes& bytes) {
  return bytes.size() >= 8 && std::equal(bytes.begin(), bytes.begin()+8, kExact);
}
Header exact_header(const Bytes& input) {
  require(is_exact(input), "expected exact-residual magic");
  // Reuse all existing histogram bounds, counts, indices and trailer checks.
  Bytes routed = input;
  std::copy(kMarginal, kMarginal+8, routed.begin());
  Header header = read_header(routed);
  require(header.format == Format::Local, "exact-residual mode must be 1");
  return header;
}

Bytes encode_exact(const Document& document) {
  validate_document(document);
  const Histograms counts = histograms(document);
  Bytes output(kExact, kExact+8);
  append_u32(output, uint32_t(document.tensors.size()));
  output.push_back(1);
  append_u32(output, uint32_t(counts.local.size()));
  for (uint32_t value : counts.global) append_u32(output, value);
  for (const auto& record : counts.local) {
    append_u32(output, record.index);
    for (uint32_t value : record.counts) append_u32(output, value);
  }
  Encoder coder;
  Models models;
  uint8_t previous_meta = 0;
  auto meta = [&](uint8_t value) {
    coder.tree(&models.meta[size_t(previous_meta)*256], 8, value);
    previous_meta = value;
  };
  size_t histogram_index = 0;
  for (const auto& tensor : document.tensors) {
    meta(uint8_t(tensor.name.size()));
    uint32_t c2 = 0, c1 = 0;
    for (unsigned char value : tensor.name) {
      coder.tree(&models.name[size_t((c2<<8)|c1)*256], 8, value);
      c2 = c1; c1 = value;
    }
    meta(uint8_t(tensor.dtype)); meta(uint8_t(tensor.shape.size()));
    for (uint32_t extent : tensor.shape)
      for (unsigned k = 0; k < 4; ++k) meta(uint8_t(extent >> (8*k)));
    meta(uint8_t(tensor.encoding));
    if (generated(tensor)) continue;
    if (tensor.encoding == 1) {
      const Joint joint(counts.local[histogram_index++].counts);
      for (uint8_t symbol : tensor.payload) joint.put(coder, symbol);
    } else if (tensor.encoding == 2) {
      for (size_t k = 0; k < tensor.payload.size(); k += 2) {
        const uint8_t hi = tensor.payload[k];
        coder.tree(models.bf16_hi.data(), 8, hi);
        coder.tree(&models.bf16_lo[size_t(hi)*256], 8, tensor.payload[k+1]);
      }
    } else {
      for (size_t k = 0; k < tensor.payload.size(); ++k)
        coder.tree(tensor.encoding == 3 ? &models.plane[(k&3)*256] : models.raw.data(), 8, tensor.payload[k]);
    }
  }
  const Bytes stream = coder.finish();
  require(output.size() + stream.size() <= kFileLimit, "output exceeds file bound");
  output.insert(output.end(), stream.begin(), stream.end());
  return output;
}

Document decode_exact(const Bytes& input) {
  const Header header = exact_header(input);
  Decoder coder(input, header.stream_offset);
  Models models;
  uint8_t previous_meta = 0;
  auto meta = [&]() {
    previous_meta = uint8_t(coder.tree(&models.meta[size_t(previous_meta)*256], 8));
    return previous_meta;
  };
  Document result;
  result.format = Format::Local;
  std::set<std::string> names;
  uint64_t represented_total = 0, inv_frequency_elements = 0;
  size_t histogram_index = 0;
  for (uint32_t index = 0; index < header.count; ++index) {
    Tensor tensor;
    const unsigned length = meta();
    uint32_t c2 = 0, c1 = 0;
    for (unsigned k = 0; k < length; ++k) {
      const uint32_t value = coder.tree(&models.name[size_t((c2<<8)|c1)*256], 8);
      tensor.name.push_back(char(value)); c2 = c1; c1 = value;
    }
    require(names.insert(tensor.name).second, "duplicate tensor name");
    tensor.dtype = meta();
    const unsigned dimensions = meta();
    require(tensor.dtype <= 3 && dimensions <= 8, "unsupported tensor type or dimensions");
    tensor.elements = 1;
    for (unsigned dim = 0; dim < dimensions; ++dim) {
      uint32_t extent = 0;
      for (unsigned k = 0; k < 4; ++k) extent |= uint32_t(meta()) << (8*k);
      require(!extent || tensor.elements <= kExpandedLimit/extent, "tensor extent exceeds bound");
      tensor.elements *= extent; tensor.shape.push_back(extent);
    }
    const uint64_t width = tensor.dtype == 0 ? 1 : tensor.dtype == 1 ? 2 : 4;
    require(tensor.elements <= kExpandedLimit/width, "tensor storage exceeds bound");
    tensor.represented_bytes = tensor.elements*width;
    require(represented_total <= kExpandedLimit-tensor.represented_bytes, "total tensor storage exceeds bound");
    represented_total += tensor.represented_bytes;
    tensor.encoding = meta();
    tensor.row_width = dimensions ? tensor.shape.back() : 1;
    if (tensor.name == "rope.inv_freq") {
      require(tensor.dtype == 2 && dimensions == 1, "RoPE frequency must be an F32 vector");
      inv_frequency_elements = tensor.elements;
    }
    if (generated(tensor)) {
      require(tensor.dtype == 2 && dimensions == 2 && inv_frequency_elements == tensor.shape[1] &&
                  names.count("rope.inv_freq") && tensor.name == (tensor.encoding == 4 ? "rope.sin" : "rope.cos"),
              "invalid generated RoPE tensor");
      result.regenerated_rope_bytes += tensor.represented_bytes;
    } else {
      require(tensor.encoding <= 3, "unknown tensor encoding");
      result.stored_payload_bytes += tensor.represented_bytes;
      tensor.payload.reserve(size_t(tensor.represented_bytes));
      auto byte = [&](uint16_t* model) { const auto value = uint8_t(coder.tree(model, 8)); tensor.payload.push_back(value); return value; };
      if (tensor.encoding == 1) {
        require(tensor.dtype == 0 && (!tensor.elements || tensor.row_width), "invalid INT4 tensor");
        require(histogram_index < header.counts.local.size() && header.counts.local[histogram_index].index == index,
                "missing INT4 histogram record");
        const auto& local = header.counts.local[histogram_index++].counts;
        uint64_t sum = 0;
        for (uint32_t value : local) sum += value;
        require(sum == tensor.elements, "local histogram differs from tensor size");
        const Joint joint(local);
        for (uint64_t k = 0; k < tensor.elements; ++k) tensor.payload.push_back(joint.get(coder));
        require(histogram(tensor) == local, "decoded histogram differs from header");
      } else if (tensor.encoding == 2) {
        require(tensor.dtype == 1, "BF16 encoding requires BF16 type");
        for (uint64_t k = 0; k < tensor.elements; ++k) {
          const size_t hi = byte(models.bf16_hi.data()); byte(&models.bf16_lo[hi*256]);
        }
      } else if (tensor.encoding == 3) {
        require(width == 4, "plane encoding requires four-byte type");
        for (uint64_t k = 0; k < tensor.represented_bytes; ++k) byte(&models.plane[(k&3)*256]);
      } else for (uint64_t k = 0; k < tensor.represented_bytes; ++k) byte(models.raw.data());
    }
    result.tensors.push_back(std::move(tensor));
  }
  require(histogram_index == header.counts.local.size(), "histogram record is not an INT4 tensor");
  validate_document(result);
  return result;
}

Bytes read_file(const std::string& path) {
  std::ifstream file(path, std::ios::binary | std::ios::ate);
  require(bool(file), "cannot open input");
  const auto size = file.tellg();
  require(size >= 0 && uint64_t(size) <= kFileLimit, "input exceeds file bound");
  Bytes bytes(static_cast<size_t>(size)); file.seekg(0);
  file.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
  require(bool(file), "cannot read complete input"); return bytes;
}
void publish(const std::string& path, const Bytes& bytes) {
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
    else if (ch < 32 || ch >= 127) { result += "\\u00"; result.push_back(hex[ch>>4]); result.push_back(hex[ch&15]); }
    else result.push_back(char(ch));
  }
  return result + '"';
}
void self_test() {
  constexpr std::array<int, 15> expected{{-6,-6,-4,-4,-4,-2,0,0,0,2,4,4,4,6,6}};
  for (unsigned symbol = 0; symbol < 15; ++symbol) {
    require(approximation(int(symbol)-7) == expected[symbol], "approximation self-test failed");
    const auto pair = split(uint8_t(symbol));
    require(join(pair.first, pair.second) == symbol, "XOR mapping self-test failed");
  }
  std::cout << "{\"schema\":\"gamma.fx2-weight-exact-residual-selftest.v1\",\"all_15_signed_values_exact\":true}\n";
}
}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string(argv[1]) == "--self-test") self_test();
    else {
      require(argc == 4, "usage: probe P|K|D|restore INPUT OUTPUT; or --self-test");
      const std::string mode = argv[1];
      require(mode == "P" || mode == "K" || mode == "D" || mode == "restore", "unknown mode");
      const Bytes input = read_file(argv[2]);
      const bool exact_input = is_exact(input);
      const Document document = exact_input ? decode_exact(input) : decode(input);
      require_identical(exact_input ? encode_exact(document) : encode(document, document.format), input,
                        "input is not a canonical complete stream");
      uint64_t changed = 0;
      if (mode == "K" || mode == "D") for (const auto& tensor : document.tensors) if (tensor.encoding == 1)
        for (uint8_t symbol : tensor.payload) {
          const auto pair = split(symbol);
          require(join(pair.first, pair.second) == symbol, "bookkeeping reconstruction differs");
          changed += kResidual[pair.second] != 0;
        }
      const Bytes original = encode(document, Format::Parent);
      const Bytes parent = encode(document, Format::Local);
      const Bytes output = mode == "D" ? encode_exact(document) : mode == "restore" ? original : parent;
      const Document inverse = mode == "D" ? decode_exact(output) : decode(output);
      require_identical(encode(inverse, Format::Parent), original, "canonical original reconstruction differs");
      require_identical(encode(inverse, Format::Local), parent, "selected marginal reconstruction differs");
      require_identical(exact_input ? encode_exact(inverse) : encode(inverse, document.format), input, "input reconstruction differs");
      const Document fresh = exact_input ? decode_exact(input) : decode(input);
      require_identical(mode == "D" ? encode_exact(fresh) : encode(fresh, mode == "restore" ? Format::Parent : Format::Local), output,
                        "fresh re-encoding differs");
      publish(argv[3], output);
      const auto counts = histograms(document);
      const size_t header_bytes = mode == "restore" ? 12 : 77 + 64*counts.local.size();
      std::cout << "{\"schema\":\"gamma.fx2-weight-exact-residual-probe.v1\",\"mode\":" << quoted(mode)
                << ",\"input_bytes\":" << input.size() << ",\"output_bytes\":" << output.size()
                << ",\"original_stream_bytes\":" << original.size() << ",\"selected_marginal_bytes\":" << parent.size()
                << ",\"delta_vs_selected_marginal_bytes\":" << int64_t(output.size())-int64_t(parent.size())
                << ",\"original_stream_regeneration_ok\":true,\"inverse_ok\":true,\"repeat_ok\":true"
                << ",\"original_parameter_bits_exact\":true,\"BF16_and_raw_bits_unchanged\":true"
                << ",\"inference_executed\":false,\"complete_package_bytes\":null,\"full_corpus_score_bytes\":null,\"objective_credit_bytes\":0"
                << ",\"header_bytes\":" << header_bytes << ",\"side_information_bytes\":" << header_bytes-12
                << ",\"bookkeeping_nonzero_residuals\":" << changed << ",\"int4_tensor_count\":" << counts.local.size()
                << ",\"tensor_payload_bytes\":" << document.stored_payload_bytes
                << ",\"regenerated_rope_bytes\":" << document.regenerated_rope_bytes << ",\"tensors\":[";
      bool first = true;
      for (const auto& tensor : document.tensors) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << "{\"name\":" << quoted(tensor.name) << ",\"dtype\":" << tensor.dtype << ",\"encoding\":" << tensor.encoding
                  << ",\"elements\":" << tensor.elements << ",\"represented_bytes\":" << tensor.represented_bytes
                  << ",\"stored_payload_bytes\":" << tensor.payload.size() << ",\"row_width\":" << tensor.row_width << ",\"shape\":[";
        for (size_t k = 0; k < tensor.shape.size(); ++k) { if (k) std::cout << ','; std::cout << tensor.shape[k]; }
        std::cout << "]}";
      }
      std::cout << "]}\n";
    }
    std::cout.flush(); require(bool(std::cout), "receipt stdout flush failed");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "fx2_weight_exact_residual_probe_v1: " << error.what() << '\n'; return 1;
  }
}
