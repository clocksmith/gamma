// Complete adaptive marginal FX2 model representation. GPLv3 derived source.
// Preserve upstream provenance and LICENSE from fx2_weight_format_v1.hpp.
// Metadata, names, non-INT4 payloads and range arithmetic retain the original
// procedures. Only INT4 prediction changes; counts reset at each tensor.
// Separate identity: measured parent source is included and never overwritten.
#pragma once
#include "fx2_weight_format_v1.hpp"
namespace fx2_weights_v1 {
constexpr char kAdaptive[] = "GFX2ADM1";
struct AdaptiveCounts {
  Histogram row{};
  uint32_t total = 15;
  AdaptiveCounts() { row.fill(1); }
  void observe(uint8_t value) {
    require(value < 15, "invalid adaptive count symbol");
    ++row[value];
    if (++total >= 65536) {
      total = 0;
      for (auto& count : row) { count = (count + 1) / 2; total += count; }
    }
  }
};

inline Document decode_adaptive(const Bytes& input) {
  require(input.size() >= 17 && input.size() <= kFileLimit &&
              std::equal(input.begin(), input.begin() + 8, kAdaptive),
          "invalid adaptive model header");
  Header header;
  header.count = u32(input, 8);
  require(header.count <= kTensorLimit, "adaptive tensor count exceeds bound");
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
        AdaptiveCounts counts;
        for (uint64_t k = 0; k < tensor.elements; ++k) {
          auto tree = fixed_tree(counts.row);
          const auto value = uint8_t(decoder.tree(tree.data(), 4, false));
          require(value < 15, "invalid adaptive quantized symbol");
          tensor.payload.push_back(value);
          counts.observe(value);
        }
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
  return result;
}

inline Bytes encode_adaptive(const Document& document) {
  validate_document(document);
  Bytes output(kAdaptive, kAdaptive + 8);
  append_u32(output, uint32_t(document.tensors.size()));
  Encoder encoder;
  Models models;
  uint8_t previous_meta = 0;
  auto meta = [&](uint8_t value) {
    encoder.tree(&models.meta[size_t(previous_meta) * 256], 8, value);
    previous_meta = value;
  };
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
      AdaptiveCounts counts;
      for (uint8_t value : tensor.payload) {
        require(value < 15, "invalid adaptive quantized symbol");
        auto tree = fixed_tree(counts.row);
        encoder.tree(tree.data(), 4, value, false);
        counts.observe(value);
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
