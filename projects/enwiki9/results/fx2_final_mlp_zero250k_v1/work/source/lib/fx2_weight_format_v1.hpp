// Lossless FX2 tensor-event reader/writer and fixed marginal experiment format.
// Derived from astOwOlfo/fx2-cmix-transformer-v1 at commit
// 83f2603f3f7751da5f429fd32669807eb8510494, pysrc/weights_compress.py and
// cpp_infer/src/weights_io_compressed.cpp, through Gamma's sealed
// tools/fx2_weight_pack_probe_v1.cpp. Upstream license: GNU GPL version 3;
// retain the upstream LICENSE with distributions of this derived source.
// Gamma changes: buffered tensor events and explicit fixed marginal histograms.
// No inference, training, corpus access, float arithmetic or RoPE generation.
#pragma once

#include <algorithm>
#include <array>
#include <cstdint>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace fx2_weights_v1 {
using Bytes = std::vector<uint8_t>;
using Histogram = std::array<uint32_t, 15>;
constexpr uint64_t kFileLimit = 8ull << 20;
constexpr uint64_t kExpandedLimit = 128ull << 20;
constexpr uint32_t kTensorLimit = 4096;
constexpr char kParent[] = "FX2TFWC2";
constexpr char kMarginal[] = "GFX2MAR1";
enum class Format : uint8_t { Parent = 0, Local = 1, Global = 2 };

inline void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}
inline void require_identical(const Bytes& a, const Bytes& b, const char* message) {
  size_t offset = 0;
  while (offset < a.size() && offset < b.size() && a[offset] == b[offset]) ++offset;
  if (offset != a.size() || offset != b.size())
    throw std::runtime_error(std::string(message) + "; first differing byte " +
                             std::to_string(offset) + "; lengths " +
                             std::to_string(a.size()) + "," + std::to_string(b.size()));
}
inline uint32_t u32(const Bytes& bytes, size_t offset) {
  require(offset <= bytes.size() && bytes.size() - offset >= 4, "truncated u32");
  uint32_t value = 0;
  for (unsigned k = 0; k < 4; ++k) value |= uint32_t(bytes[offset + k]) << (8 * k);
  return value;
}
inline void append_u32(Bytes& bytes, uint32_t value) {
  for (unsigned k = 0; k < 4; ++k) bytes.push_back(uint8_t(value >> (8 * k)));
}

class Decoder {
 public:
  Decoder(const Bytes& bytes, size_t offset) : bytes_(bytes), position_(offset + 1) {
    require(offset < bytes.size() && bytes.size() - offset >= 5 && bytes[offset] == 0,
            "truncated stream or noncanonical initial range cache");
    for (unsigned k = 0; k < 4; ++k) code_ = (code_ << 8) | byte();
  }
  uint32_t tree(uint16_t* probabilities, unsigned bits, bool adaptive = true) {
    uint32_t node = 1;
    for (unsigned k = 0; k < bits; ++k)
      node = (node << 1) | bit(probabilities[node], adaptive);
    return node - (1u << bits);
  }
 private:
  uint8_t byte() {
    // Match the pinned reader's zero extension. Canonical reserialization is
    // mandatory before publication and rejects absent flush/trailing bytes.
    return position_ < bytes_.size() ? bytes_[position_++] : 0;
  }
  unsigned bit(uint16_t& probability, bool adaptive) {
    const uint32_t bound = (range_ >> 11) * probability;
    unsigned value;
    if (code_ < bound) {
      range_ = bound;
      if (adaptive) probability += (2048 - probability) >> 5;
      value = 0;
    } else {
      code_ -= bound;
      range_ -= bound;
      if (adaptive) probability -= probability >> 5;
      value = 1;
    }
    while (range_ < (1u << 24)) { code_ = (code_ << 8) | byte(); range_ <<= 8; }
    return value;
  }
  const Bytes& bytes_;
  size_t position_;
  uint32_t range_ = 0xffffffffu, code_ = 0;
};

class Encoder {
 public:
  void tree(uint16_t* probabilities, unsigned bits, uint32_t symbol, bool adaptive = true) {
    require(symbol < (1u << bits), "symbol outside tree");
    uint32_t node = 1;
    for (unsigned k = bits; k; --k) {
      const unsigned value = (symbol >> (k - 1)) & 1;
      bit(probabilities[node], value, adaptive);
      node = (node << 1) | value;
    }
  }
  Bytes finish() {
    for (unsigned k = 0; k < 5; ++k) shift_low();
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
  void bit(uint16_t& probability, unsigned value, bool adaptive) {
    const uint32_t bound = (range_ >> 11) * probability;
    if (!value) {
      range_ = bound;
      if (adaptive) probability += (2048 - probability) >> 5;
    } else {
      low_ += bound;
      range_ -= bound;
      if (adaptive) probability -= probability >> 5;
    }
    while (range_ < (1u << 24)) { range_ <<= 8; shift_low(); }
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
struct Tensor {
  std::string name;
  unsigned dtype = 0, encoding = 0;
  std::vector<uint32_t> shape;
  uint64_t elements = 0, represented_bytes = 0, row_width = 0;
  Bytes payload;  // Exact decoded events; INT4 stores offset symbols 0..14.
};
struct IndexedHistogram { uint32_t index; Histogram counts; };
struct Histograms {
  Histogram global{};
  std::vector<IndexedHistogram> local;
};
struct Document {
  Format format = Format::Parent;
  std::vector<Tensor> tensors;
  uint64_t stored_payload_bytes = 0, regenerated_rope_bytes = 0;
};
inline bool generated(const Tensor& tensor) { return tensor.encoding == 4 || tensor.encoding == 5; }
inline Histogram histogram(const Tensor& tensor) {
  Histogram counts{};
  for (uint8_t value : tensor.payload) {
    require(value < 15, "invalid quantized weight symbol");
    ++counts[value];
  }
  return counts;
}
inline Histograms histograms(const Document& document) {
  Histograms result;
  for (size_t k = 0; k < document.tensors.size(); ++k) {
    const auto& tensor = document.tensors[k];
    if (tensor.encoding != 1) continue;
    const auto local = histogram(tensor);
    result.local.push_back({uint32_t(k), local});
    for (unsigned s = 0; s < 15; ++s) {
      require(uint64_t(result.global[s]) + local[s] <= kExpandedLimit, "histogram exceeds bound");
      result.global[s] += local[s];
    }
  }
  return result;
}
inline std::array<uint16_t, 16> fixed_tree(const Histogram& counts) {
  std::array<uint64_t, 32> totals{};
  for (unsigned s = 0; s < 15; ++s) totals[16 + s] = counts[s];
  std::array<uint16_t, 16> tree{};
  tree.fill(1024);
  for (unsigned node = 15; node; --node) {
    const uint64_t left = totals[2 * node], total = left + totals[2 * node + 1];
    totals[node] = total;
    // No smoothing. Round p0 to nearest Q11 integer; symbol15 has zero count.
    if (total) tree[node] = uint16_t(std::clamp<uint64_t>((2048 * left + total / 2) / total, 1, 2047));
  }
  return tree;
}

// Marginal header: "GFX2MAR1", u32le tensor_count, u8 mode (1=D,2=G),
// u32le INT4_count, 15 u32le global counts, then sorted records containing
// u32le original tensor_index and 15 u32le local counts. Stream offset is
// 77+64*INT4_count. D/G side information differs only in mode, not counts.
// Empty INT4 tensors have records. All counts must match decoded events.
struct Header {
  Format format = Format::Parent;
  uint32_t count = 0;
  size_t stream_offset = 12;
  Histograms counts;
};
inline Header read_header(const Bytes& input) {
  require(input.size() >= 17 && input.size() <= kFileLimit, "invalid model file length");
  Header header;
  const std::string magic(input.begin(), input.begin() + 8);
  require(magic == kParent || magic == kMarginal, "unsupported model magic");
  header.count = u32(input, 8);
  require(header.count <= kTensorLimit, "tensor count exceeds bound");
  if (magic == kParent) return header;
  require(input[12] == 1 || input[12] == 2, "invalid marginal mode");
  header.format = Format(input[12]);
  const uint32_t count = u32(input, 13);
  require(count <= header.count, "histogram record count exceeds tensor count");
  header.stream_offset = 77 + size_t(count) * 64;
  require(header.stream_offset <= input.size() && input.size() - header.stream_offset >= 5,
          "truncated histogram header or range stream");
  for (unsigned s = 0; s < 15; ++s) header.counts.global[s] = u32(input, 17 + 4 * s);
  std::array<uint64_t, 15> sums{};
  uint64_t total = 0;
  for (uint32_t k = 0; k < count; ++k) {
    const size_t offset = 77 + size_t(k) * 64;
    IndexedHistogram record{u32(input, offset), {}};
    require(record.index < header.count && (!k || record.index > header.counts.local.back().index),
            "histogram indices must be unique, increasing and in range");
    for (unsigned s = 0; s < 15; ++s) {
      record.counts[s] = u32(input, offset + 4 + 4 * s);
      total += record.counts[s];
      sums[s] += record.counts[s];
      require(total <= kExpandedLimit, "histogram count exceeds expanded bound");
    }
    header.counts.local.push_back(record);
  }
  for (unsigned s = 0; s < 15; ++s)
    require(sums[s] == header.counts.global[s], "global histogram differs from local sum");
  return header;
}

inline Document decode(const Bytes& input) {
  const Header header = read_header(input);
  Decoder decoder(input, header.stream_offset);
  Models models;
  uint8_t previous_meta = 0;
  auto meta = [&]() {
    previous_meta = uint8_t(decoder.tree(&models.meta[size_t(previous_meta) * 256], 8));
    return previous_meta;
  };
  Document result;
  result.format = header.format;
  std::set<std::string> names;
  uint64_t represented_total = 0, inv_frequency_elements = 0;
  size_t histogram_index = 0;
  for (uint32_t index = 0; index < header.count; ++index) {
    Tensor tensor;
    const unsigned length = meta();
    uint32_t c2 = 0, c1 = 0;
    for (unsigned k = 0; k < length; ++k) {
      const uint32_t value = decoder.tree(&models.name[size_t((c2 << 8) | c1) * 256], 8);
      tensor.name.push_back(char(value));
      c2 = c1; c1 = value;
    }
    require(names.insert(tensor.name).second, "duplicate tensor name");
    tensor.dtype = meta();
    const unsigned dimensions = meta();
    require(tensor.dtype <= 3 && dimensions <= 8, "unsupported tensor type or dimensions");
    tensor.elements = 1;
    for (unsigned dim = 0; dim < dimensions; ++dim) {
      uint32_t extent = 0;
      for (unsigned k = 0; k < 4; ++k) extent |= uint32_t(meta()) << (8 * k);
      require(!extent || tensor.elements <= kExpandedLimit / extent, "tensor extent exceeds bound");
      tensor.elements *= extent;
      tensor.shape.push_back(extent);
    }
    const uint64_t element_bytes = tensor.dtype == 0 ? 1 : tensor.dtype == 1 ? 2 : 4;
    require(tensor.elements <= kExpandedLimit / element_bytes, "tensor storage exceeds bound");
    tensor.represented_bytes = tensor.elements * element_bytes;
    require(represented_total <= kExpandedLimit - tensor.represented_bytes, "total tensor storage exceeds bound");
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
      auto byte = [&](uint16_t* model) { const auto v = uint8_t(decoder.tree(model, 8)); tensor.payload.push_back(v); return v; };
      if (tensor.encoding == 1) {
        require(tensor.dtype == 0 && (!tensor.elements || tensor.row_width), "invalid INT4 tensor");
        std::array<uint16_t, 16> fixed{};
        const Histogram* local = nullptr;
        if (header.format != Format::Parent) {
          require(histogram_index < header.counts.local.size() &&
                      header.counts.local[histogram_index].index == index, "missing INT4 histogram record");
          local = &header.counts.local[histogram_index++].counts;
          uint64_t sum = 0;
          for (uint32_t count : *local) sum += count;
          require(sum == tensor.elements, "local histogram total differs from tensor elements");
          fixed = fixed_tree(header.format == Format::Local ? *local : header.counts.global);
        }
        for (uint64_t k = 0; k < tensor.elements; ++k) {
          const auto value = uint8_t(decoder.tree(local ? fixed.data() : models.int4.data(), 4, local == nullptr));
          require(value < 15, "invalid quantized weight symbol");
          tensor.payload.push_back(value);
        }
        if (local) require(histogram(tensor) == *local, "decoded tensor histogram differs from header");
      } else if (tensor.encoding == 2) {
        require(tensor.dtype == 1, "BF16 encoding requires BF16 type");
        for (uint64_t k = 0; k < tensor.elements; ++k) {
          const size_t hi = byte(models.bf16_hi.data());
          byte(&models.bf16_lo[hi * 256]);
        }
      } else if (tensor.encoding == 3) {
        require(element_bytes == 4, "plane encoding requires four-byte type");
        for (uint64_t k = 0; k < tensor.represented_bytes; ++k) byte(&models.plane[(k & 3) * 256]);
      } else {
        for (uint64_t k = 0; k < tensor.represented_bytes; ++k) byte(models.raw.data());
      }
    }
    result.tensors.push_back(std::move(tensor));
  }
  require(histogram_index == header.counts.local.size(), "histogram record does not identify an INT4 tensor");
  return result;
}

inline void validate_document(const Document& document) {
  require(document.tensors.size() <= kTensorLimit, "tensor count exceeds bound");
  std::set<std::string> names;
  uint64_t total = 0, stored = 0, regenerated = 0, inv_frequency_elements = 0;
  for (const auto& tensor : document.tensors) {
    require(tensor.name.size() <= 255 && names.insert(tensor.name).second, "invalid or duplicate tensor name");
    require(tensor.dtype <= 3 && tensor.shape.size() <= 8 && tensor.encoding <= 5,
            "unsupported tensor type, dimensions or encoding");
    uint64_t elements = 1;
    for (uint32_t extent : tensor.shape) {
      require(!extent || elements <= kExpandedLimit / extent, "tensor extent exceeds bound");
      elements *= extent;
    }
    const uint64_t element_bytes = tensor.dtype == 0 ? 1 : tensor.dtype == 1 ? 2 : 4;
    require(elements <= kExpandedLimit / element_bytes, "tensor storage exceeds bound");
    const uint64_t bytes = elements * element_bytes;
    require(total <= kExpandedLimit - bytes, "total tensor storage exceeds bound");
    total += bytes;
    require(tensor.elements == elements && tensor.represented_bytes == bytes &&
                tensor.row_width == (tensor.shape.empty() ? 1 : tensor.shape.back()), "tensor metadata is inconsistent");
    require(tensor.payload.size() == (generated(tensor) ? 0 : bytes), "tensor payload size differs from metadata");
    if (tensor.name == "rope.inv_freq") {
      require(tensor.dtype == 2 && tensor.shape.size() == 1, "RoPE frequency must be an F32 vector");
      inv_frequency_elements = elements;
    }
    if (tensor.encoding == 1) {
      require(tensor.dtype == 0 && (!elements || tensor.row_width), "invalid INT4 tensor");
      for (uint8_t value : tensor.payload) require(value < 15, "invalid quantized weight symbol");
    } else if (tensor.encoding == 2) require(tensor.dtype == 1, "BF16 encoding requires BF16 type");
    else if (tensor.encoding == 3) require(element_bytes == 4, "plane encoding requires four-byte type");
    else if (generated(tensor))
      require(tensor.dtype == 2 && tensor.shape.size() == 2 && inv_frequency_elements == tensor.shape[1] &&
                  names.count("rope.inv_freq") && tensor.name == (tensor.encoding == 4 ? "rope.sin" : "rope.cos"),
              "invalid generated RoPE tensor");
    if (generated(tensor)) regenerated += bytes;
    else stored += bytes;
  }
  require(stored == document.stored_payload_bytes && regenerated == document.regenerated_rope_bytes,
          "document payload counts are inconsistent");
}

inline Bytes encode(const Document& document, Format format) {
  validate_document(document);
  require(format == Format::Parent || format == Format::Local || format == Format::Global, "invalid output format");
  Histograms counts;
  if (format != Format::Parent) counts = histograms(document);
  const char* magic = format == Format::Parent ? kParent : kMarginal;
  Bytes output(magic, magic + 8);
  append_u32(output, uint32_t(document.tensors.size()));
  if (format != Format::Parent) {
    output.push_back(uint8_t(format));
    append_u32(output, uint32_t(counts.local.size()));
    for (uint32_t value : counts.global) append_u32(output, value);
    for (const auto& record : counts.local) {
      append_u32(output, record.index);
      for (uint32_t value : record.counts) append_u32(output, value);
    }
  }
  Encoder encoder;
  Models models;
  uint8_t previous_meta = 0;
  auto meta = [&](uint8_t value) {
    encoder.tree(&models.meta[size_t(previous_meta) * 256], 8, value);
    previous_meta = value;
  };
  size_t histogram_index = 0;
  for (const auto& tensor : document.tensors) {
    require(tensor.name.size() <= 255 && tensor.shape.size() <= 8, "invalid tensor metadata");
    meta(uint8_t(tensor.name.size()));
    uint32_t c2 = 0, c1 = 0;
    for (unsigned char value : tensor.name) {
      encoder.tree(&models.name[size_t((c2 << 8) | c1) * 256], 8, value);
      c2 = c1; c1 = value;
    }
    meta(uint8_t(tensor.dtype)); meta(uint8_t(tensor.shape.size()));
    for (uint32_t extent : tensor.shape)
      for (unsigned k = 0; k < 4; ++k) meta(uint8_t(extent >> (8 * k)));
    meta(uint8_t(tensor.encoding));
    require(tensor.payload.size() == (generated(tensor) ? 0 : tensor.represented_bytes), "tensor payload size differs from metadata");
    if (generated(tensor)) continue;
    if (tensor.encoding == 1) {
      std::array<uint16_t, 16> fixed{};
      if (format != Format::Parent)
        fixed = fixed_tree(format == Format::Local ? counts.local[histogram_index].counts : counts.global);
      ++histogram_index;
      for (uint8_t value : tensor.payload) {
        require(value < 15, "invalid quantized weight symbol");
        encoder.tree(format == Format::Parent ? models.int4.data() : fixed.data(), 4, value, format == Format::Parent);
      }
    } else if (tensor.encoding == 2) {
      for (size_t k = 0; k < tensor.payload.size(); k += 2) {
        const size_t hi = tensor.payload[k];
        encoder.tree(models.bf16_hi.data(), 8, uint32_t(hi));
        encoder.tree(&models.bf16_lo[hi * 256], 8, tensor.payload[k + 1]);
      }
    } else {
      for (size_t k = 0; k < tensor.payload.size(); ++k)
        encoder.tree(tensor.encoding == 3 ? &models.plane[(k & 3) * 256] : models.raw.data(), 8, tensor.payload[k]);
    }
  }
  Bytes stream = encoder.finish();
  require(output.size() + stream.size() <= kFileLimit, "output exceeds file bound");
  output.insert(output.end(), stream.begin(), stream.end());
  return output;
}
}  // namespace fx2_weights_v1
