// Prospective lossless FX2TFWC2 model transcoder; not a measured codec result.
// Derived from astOwOlfo/fx2-cmix-transformer-v1, commit
// 83f2603f3f7751da5f429fd32669807eb8510494:
//   pysrc/weights_compress.py (binary range coder and tensor format)
//   cpp_infer/src/weights_io_compressed.cpp (model layout and decoder)
// Upstream repository notice: GNU General Public License, version 3.
// Preserve its LICENSE with any distribution of this derived implementation.
// Gamma change: tensor-local INT4 trees conditioned on the preceding symbol
// within the current last-dimension row; row starts use a distinct context.
// No training, float arithmetic, RoPE table generation, or corpus access.
// Build prospectively with an installed C++17 compiler; do not infer approval
// to compile or execute from the existence of this file.

#include <array>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
using Bytes = std::vector<uint8_t>;
constexpr uint64_t kFileLimit = 8ull << 20;
constexpr uint64_t kExpandedLimit = 128ull << 20;
constexpr uint32_t kTensorLimit = 4096;
constexpr char kParent[] = "FX2TFWC2";
constexpr char kTreatment[] = "GFWPACK1";

void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}

void require_identical(const Bytes& left, const Bytes& right, const char* message) {
  size_t offset = 0;
  while (offset < left.size() && offset < right.size() && left[offset] == right[offset]) ++offset;
  if (offset != left.size() || offset != right.size())
    throw std::runtime_error(std::string(message) + "; first differing byte " + std::to_string(offset)
                             + "; lengths " + std::to_string(left.size()) + "," + std::to_string(right.size()));
}

uint32_t u32(const Bytes& bytes, size_t offset) {
  require(offset + 4 <= bytes.size(), "truncated u32");
  uint32_t value = 0;
  for (unsigned k = 0; k < 4; ++k) value |= uint32_t(bytes[offset + k]) << (8 * k);
  return value;
}

void append_u32(Bytes& bytes, uint32_t value) {
  for (unsigned k = 0; k < 4; ++k) bytes.push_back(uint8_t(value >> (8 * k)));
}

bool treatment_format(const Bytes& bytes) {
  require(bytes.size() >= 17 && bytes.size() <= kFileLimit, "invalid model file length");
  const std::string magic(bytes.begin(), bytes.begin() + 8);
  require(magic == kParent || magic == kTreatment, "unsupported model magic");
  require(bytes[12] == 0, "noncanonical initial range cache");
  return magic == kTreatment;
}

class Decoder {
 public:
  explicit Decoder(const Bytes& bytes) : bytes_(bytes), position_(13) {
    for (int k = 0; k < 4; ++k) code_ = (code_ << 8) | byte();
  }
  uint32_t tree(uint16_t* probabilities, unsigned bits) {
    uint32_t node = 1;
    for (unsigned k = 0; k < bits; ++k) node = (node << 1) | bit(probabilities[node]);
    return node - (1u << bits);
  }
 private:
  uint8_t byte() {
    if (position_ < bytes_.size()) return bytes_[position_++];
    // The pinned upstream reader supplies zero after physical EOF. Match its
    // arithmetic semantics; tensor/payload bounds limit decoding work, and
    // exact reserialization in main rejects missing flush bytes, truncation,
    // and trailing bytes without inventing a different end-of-stream rule.
    return 0;
  }
  unsigned bit(uint16_t& probability) {
    const uint32_t bound = (range_ >> 11) * probability;
    unsigned value;
    if (code_ < bound) {
      range_ = bound;
      probability += (2048 - probability) >> 5;
      value = 0;
    } else {
      code_ -= bound;
      range_ -= bound;
      probability -= probability >> 5;
      value = 1;
    }
    while (range_ < (1u << 24)) {
      code_ = (code_ << 8) | byte();
      range_ <<= 8;
    }
    return value;
  }
  const Bytes& bytes_;
  size_t position_;
  uint32_t range_ = 0xffffffffu, code_ = 0;
};

class Encoder {
 public:
  void tree(uint16_t* probabilities, unsigned bits, uint32_t symbol) {
    require(symbol < (1u << bits), "symbol outside tree");
    uint32_t node = 1;
    for (unsigned k = bits; k; --k) {
      const unsigned value = (symbol >> (k - 1)) & 1;
      bit(probabilities[node], value);
      node = (node << 1) | value;
    }
  }
  Bytes finish() {
    for (int k = 0; k < 5; ++k) shift_low();
    return std::move(output_);
  }
 private:
  void emit(uint8_t value) {
    require(output_.size() < kFileLimit, "encoded stream exceeds bound");
    output_.push_back(value);
  }
  void shift_low() {
    if (low_ < 0xff000000ull || low_ > 0xffffffffull) {
      const uint32_t carry = uint32_t(low_ >> 32);
      emit(uint8_t(cache_ + carry));
      for (uint64_t k = 1; k < cache_size_; ++k) emit(uint8_t(0xffu + carry));
      cache_ = uint8_t(low_ >> 24);
      cache_size_ = 0;
    }
    ++cache_size_;
    low_ = uint32_t(low_ << 8);
  }
  void bit(uint16_t& probability, unsigned value) {
    const uint32_t bound = (range_ >> 11) * probability;
    if (!value) {
      range_ = bound;
      probability += (2048 - probability) >> 5;
    } else {
      low_ += bound;
      range_ -= bound;
      probability -= probability >> 5;
    }
    while (range_ < (1u << 24)) {
      range_ <<= 8;
      shift_low();
    }
  }
  uint64_t low_ = 0, cache_size_ = 1;
  uint32_t range_ = 0xffffffffu;
  uint8_t cache_ = 0;
  Bytes output_;
};

struct Models {
  std::vector<uint16_t> meta = std::vector<uint16_t>(256 * 256, 1024);
  std::vector<uint16_t> name = std::vector<uint16_t>(65536 * 256, 1024);
  std::vector<uint16_t> raw = std::vector<uint16_t>(256, 1024);
  std::vector<uint16_t> int4 = std::vector<uint16_t>(16, 1024);
  std::vector<uint16_t> bf16_hi = std::vector<uint16_t>(256, 1024);
  std::vector<uint16_t> bf16_lo = std::vector<uint16_t>(256 * 256, 1024);
  std::vector<uint16_t> plane = std::vector<uint16_t>(4 * 256, 1024);
};

struct TensorCount {
  std::string name;
  unsigned dtype, encoding;
  uint64_t elements, represented_bytes, stored_payload_bytes, row_width;
};

struct Result {
  Bytes bytes;
  std::vector<TensorCount> tensors;
  uint64_t stored_payload_bytes = 0, regenerated_rope_bytes = 0;
};

// Transcode decoded events directly. The special RoPE tags carry no payload;
// preserving their metadata reproduces the same tables in the upstream loader.
Result transcode(const Bytes& input, bool output_treatment) {
  const bool input_treatment = treatment_format(input);
  const uint32_t count = u32(input, 8);
  require(count <= kTensorLimit, "tensor count exceeds bound");
  Decoder decoder(input);
  Encoder encoder;
  Models from, to;
  uint8_t previous_meta = 0;
  auto symbol = [&](uint16_t* input_model, uint16_t* output_model, unsigned bits) {
    const uint32_t value = decoder.tree(input_model, bits);
    encoder.tree(output_model, bits, value);
    return value;
  };
  auto meta = [&]() {
    const uint8_t value = uint8_t(symbol(&from.meta[size_t(previous_meta) * 256],
                                        &to.meta[size_t(previous_meta) * 256], 8));
    previous_meta = value;
    return value;
  };
  Result result;
  std::set<std::string> names;
  uint64_t represented_total = 0, inv_frequency_elements = 0;
  for (uint32_t tensor = 0; tensor < count; ++tensor) {
    const unsigned length = meta();
    std::string name;
    uint32_t c2 = 0, c1 = 0;
    for (unsigned k = 0; k < length; ++k) {
      const size_t context = size_t((c2 << 8) | c1) * 256;
      const uint32_t value = symbol(&from.name[context], &to.name[context], 8);
      name.push_back(char(value));
      c2 = c1;
      c1 = value;
    }
    require(names.insert(name).second, "duplicate tensor name");
    const unsigned dtype = meta(), dimensions = meta();
    require(dtype <= 3 && dimensions <= 8, "unsupported tensor type or dimensions");
    std::vector<uint32_t> shape;
    uint64_t elements = 1;
    for (unsigned dim = 0; dim < dimensions; ++dim) {
      uint32_t extent = 0;
      for (unsigned k = 0; k < 4; ++k) extent |= uint32_t(meta()) << (8 * k);
      require(!extent || elements <= kExpandedLimit / extent, "tensor extent exceeds bound");
      elements *= extent;
      shape.push_back(extent);
    }
    const uint64_t element_bytes = dtype == 0 ? 1 : dtype == 1 ? 2 : 4;
    require(elements <= kExpandedLimit / element_bytes, "tensor storage exceeds bound");
    const uint64_t bytes = elements * element_bytes;
    require(represented_total <= kExpandedLimit - bytes, "total tensor storage exceeds bound");
    represented_total += bytes;
    const unsigned encoding = meta();
    const uint64_t row_width = dimensions ? shape.back() : 1;
    const bool generated_rope = encoding == 4 || encoding == 5;
    result.tensors.push_back({name, dtype, encoding, elements, bytes,
                              generated_rope ? 0 : bytes, row_width});
    if (generated_rope) result.regenerated_rope_bytes += bytes;
    else result.stored_payload_bytes += bytes;
    if (name == "rope.inv_freq") {
      // Public writer/Python reader use a vector; the native reader alone
      // accepts broader shapes with the same element count. Keep this stricter
      // public-format subset explicit instead of calling those shapes valid.
      require(dtype == 2 && dimensions == 1, "RoPE frequency must be an F32 vector");
      inv_frequency_elements = elements;
    }
    if (encoding == 1) {
      require(dtype == 0 && (!elements || row_width), "invalid INT4 tensor");
      std::array<uint16_t, 16 * 16> input_rows, output_rows;
      input_rows.fill(1024);
      output_rows.fill(1024);
      uint32_t previous = 15;
      for (uint64_t k = 0; k < elements; ++k) {
        if (k % row_width == 0) previous = 15;
        uint16_t* input_model = input_treatment ? &input_rows[previous * 16] : from.int4.data();
        uint16_t* output_model = output_treatment ? &output_rows[previous * 16] : to.int4.data();
        const uint32_t value = symbol(input_model, output_model, 4);
        require(value < 15, "invalid quantized weight symbol");
        previous = value;
      }
    } else if (encoding == 2) {
      require(dtype == 1, "BF16 encoding requires BF16 type");
      for (uint64_t k = 0; k < elements; ++k) {
        const size_t hi = symbol(from.bf16_hi.data(), to.bf16_hi.data(), 8);
        symbol(&from.bf16_lo[hi * 256], &to.bf16_lo[hi * 256], 8);
      }
    } else if (encoding == 3) {
      require(element_bytes == 4, "plane encoding requires four-byte type");
      for (uint64_t k = 0; k < bytes; ++k)
        symbol(&from.plane[(k & 3) * 256], &to.plane[(k & 3) * 256], 8);
    } else if (generated_rope) {
      require(dtype == 2 && dimensions == 2 && inv_frequency_elements == shape[1]
                  && names.count("rope.inv_freq") &&
                  name == (encoding == 4 ? "rope.sin" : "rope.cos"), "invalid generated RoPE tensor");
    } else {
      require(encoding == 0, "unknown tensor encoding");
      for (uint64_t k = 0; k < bytes; ++k) symbol(from.raw.data(), to.raw.data(), 8);
    }
  }
  const char* magic = output_treatment ? kTreatment : kParent;
  result.bytes.assign(magic, magic + 8);
  append_u32(result.bytes, count);
  const Bytes stream = encoder.finish();
  result.bytes.insert(result.bytes.end(), stream.begin(), stream.end());
  require(result.bytes.size() <= kFileLimit, "output exceeds file bound");
  return result;
}

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
  // C11 exclusive-create mode; publication uses a same-directory hard link,
  // which atomically fails if the destination already exists.
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
}  // namespace

int main(int argc, char** argv) {
  try {
    require(argc == 4, "usage: fx2_weight_pack_probe_v1 parent|pack|unpack INPUT OUTPUT");
    const std::string mode = argv[1];
    require(mode == "parent" || mode == "pack" || mode == "unpack", "unknown mode");
    const Bytes input = read_file(argv[2]);
    const bool input_treatment = treatment_format(input);
    require(input_treatment == (mode == "unpack"), "mode/input format mismatch");
    // Reject noncanonical trailing bytes and streams differing from this exact
    // range-coder implementation before making any output available.
    require_identical(transcode(input, input_treatment).bytes, input,
                      "input does not regenerate byte-identically with its own coder");
    Result output = transcode(input, mode == "pack");
    require_identical(transcode(output.bytes, input_treatment).bytes, input,
                      "inverse does not regenerate original packed bytes");
    require_identical(transcode(input, mode == "pack").bytes, output.bytes,
                      "repeat transcode differs");
    write_new_file(argv[3], output.bytes);
    std::cout << "{\"schema\":\"gamma.fx2-weight-pack-probe.v1\",\"mode\":" << quoted(mode)
              << ",\"input_bytes\":" << input.size() << ",\"output_bytes\":" << output.bytes.size()
              << ",\"original_stream_regeneration_ok\":true,\"inverse_ok\":true,\"repeat_ok\":true"
              << ",\"objective_credit_bytes\":0,\"tensor_payload_bytes\":" << output.stored_payload_bytes
              << ",\"regenerated_rope_bytes\":" << output.regenerated_rope_bytes << ",\"tensors\":[";
    bool first = true;
    for (const auto& tensor : output.tensors) {
      if (!first) std::cout << ',';
      first = false;
      std::cout << "{\"name\":" << quoted(tensor.name) << ",\"dtype\":" << tensor.dtype
                << ",\"encoding\":" << tensor.encoding << ",\"elements\":" << tensor.elements
                << ",\"represented_bytes\":" << tensor.represented_bytes
                << ",\"stored_payload_bytes\":" << tensor.stored_payload_bytes
                << ",\"row_width\":" << tensor.row_width << '}';
    }
    std::cout << "]}\n";
    std::cout.flush();
    require(bool(std::cout), "receipt stdout flush failed");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "fx2_weight_pack_probe_v1: " << error.what() << '\n';
    return 1;
  }
}
