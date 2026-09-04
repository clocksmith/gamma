#include "profile_artifacts.hpp"

#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>

namespace gamma_enwiki9::nncp {
namespace {

namespace fs = std::filesystem;

struct UntypedGradientView {
  GradientElementType element_type;
  const Bf16Buffer* bf16_values;
  const F32Buffer* f32_values;
};

struct UntypedParameterView {
  GradientElementType element_type;
  Bf16Buffer* bf16_values;
  F32Buffer* f32_values;
};

std::size_t Product(
    const std::vector<std::size_t>& dimensions,
    const char* label) {
  std::size_t result = 1;
  for (const std::size_t dimension : dimensions) {
    if (dimension == 0 ||
        result > std::numeric_limits<std::size_t>::max() / dimension) {
      throw std::invalid_argument(std::string(label) + " geometry is invalid");
    }
    result *= dimension;
  }
  return result;
}

std::size_t ByteCount(
    std::size_t elements,
    std::size_t item_size,
    const char* label) {
  if (item_size == 0 ||
      elements > std::numeric_limits<std::size_t>::max() / item_size) {
    throw std::invalid_argument(std::string(label) + " byte count overflows");
  }
  const std::size_t bytes = elements * item_size;
  if (bytes > static_cast<std::size_t>(
                  std::numeric_limits<std::streamsize>::max())) {
    throw std::invalid_argument(std::string(label) + " exceeds stream size");
  }
  return bytes;
}

std::string IndexName(std::size_t index, std::string_view name) {
  std::ostringstream output;
  output << std::setfill('0') << std::setw(4) << index << '_' << name;
  return output.str();
}

template <typename Value>
void WritePayload(const fs::path& path, const std::vector<Value>& values) {
  if (fs::exists(path)) {
    throw std::runtime_error("refusing to replace " + path.string());
  }
  const std::size_t bytes = ByteCount(values.size(), sizeof(Value), "payload");
  const fs::path partial = path.string() + ".partial";
  if (fs::exists(partial)) {
    throw std::runtime_error("partial payload already exists: " + partial.string());
  }
  std::ofstream output(partial, std::ios::binary | std::ios::trunc);
  if (!output) throw std::runtime_error("cannot create " + partial.string());
  if (bytes != 0) {
    output.write(
        reinterpret_cast<const char*>(values.data()),
        static_cast<std::streamsize>(bytes));
  }
  output.flush();
  if (!output) throw std::runtime_error("cannot write " + partial.string());
  output.close();
  if (!output) throw std::runtime_error("cannot close " + partial.string());
  fs::rename(partial, path);
}

void WriteText(const fs::path& path, const std::string& text) {
  if (fs::exists(path)) {
    throw std::runtime_error("refusing to replace " + path.string());
  }
  const fs::path partial = path.string() + ".partial";
  if (fs::exists(partial)) {
    throw std::runtime_error("partial text already exists: " + partial.string());
  }
  if (text.size() > static_cast<std::size_t>(
                        std::numeric_limits<std::streamsize>::max())) {
    throw std::invalid_argument("text exceeds stream size");
  }
  std::ofstream output(partial, std::ios::binary | std::ios::trunc);
  if (!output) throw std::runtime_error("cannot create " + partial.string());
  output.write(text.data(), static_cast<std::streamsize>(text.size()));
  output.flush();
  if (!output) throw std::runtime_error("cannot write " + partial.string());
  output.close();
  if (!output) throw std::runtime_error("cannot close " + partial.string());
  fs::rename(partial, path);
}

void Insert(
    std::unordered_map<std::string, UntypedGradientView>& bindings,
    std::string name,
    const Bf16Buffer& values) {
  const auto [unused, inserted] = bindings.emplace(
      std::move(name),
      UntypedGradientView{GradientElementType::kBf16, &values, nullptr});
  static_cast<void>(unused);
  if (!inserted) throw std::logic_error("duplicate BF16 gradient binding");
}

void Insert(
    std::unordered_map<std::string, UntypedParameterView>& bindings,
    std::string name,
    Bf16Buffer& values) {
  const auto [unused, inserted] = bindings.emplace(
      std::move(name),
      UntypedParameterView{GradientElementType::kBf16, &values, nullptr});
  static_cast<void>(unused);
  if (!inserted) throw std::logic_error("duplicate BF16 parameter binding");
}

void Insert(
    std::unordered_map<std::string, UntypedParameterView>& bindings,
    std::string name,
    F32Buffer& values) {
  const auto [unused, inserted] = bindings.emplace(
      std::move(name),
      UntypedParameterView{GradientElementType::kF32, nullptr, &values});
  static_cast<void>(unused);
  if (!inserted) throw std::logic_error("duplicate F32 parameter binding");
}

void Insert(
    std::unordered_map<std::string, UntypedGradientView>& bindings,
    std::string name,
    const F32Buffer& values) {
  const auto [unused, inserted] = bindings.emplace(
      std::move(name),
      UntypedGradientView{GradientElementType::kF32, nullptr, &values});
  static_cast<void>(unused);
  if (!inserted) throw std::logic_error("duplicate F32 gradient binding");
}

}  // namespace

std::vector<GradientArtifactView> CanonicalGradientArtifacts(
    const ProfileGeometry& geometry,
    const ProfileGradients& gradients) {
  if (gradients.layers.size() != geometry.layers) {
    throw std::invalid_argument("gradient layer population differs");
  }
  std::vector<GradientDescriptor> descriptors =
      CanonicalGradientDescriptors(geometry);
  std::unordered_map<std::string, UntypedGradientView> bindings;
  bindings.reserve(descriptors.size());
  Insert(bindings, "embed_out", gradients.output_weight);
  for (std::size_t layer = 0; layer < geometry.layers; ++layer) {
    const std::string suffix = "_" + std::to_string(layer);
    const TransformerLayerGradients& current = gradients.layers[layer];
    Insert(bindings, "ff2" + suffix, current.ff2);
    Insert(bindings, "ff1" + suffix, current.ff1);
    Insert(bindings, "ln_g_" + std::to_string(2 * layer + 1), current.ln_g2);
    Insert(bindings, "ln_b_" + std::to_string(2 * layer + 1), current.ln_b2);
    Insert(bindings, "ff_bias1" + suffix, current.ff_bias1);
    Insert(bindings, "ff_bias2" + suffix, current.ff_bias2);
    Insert(bindings, "w_o" + suffix, current.w_o);
    Insert(bindings, "w_r" + suffix, current.w_r);
    Insert(bindings, "w_kv" + suffix, current.w_kv);
    Insert(bindings, "w_q" + suffix, current.w_q);
    Insert(bindings, "ln_g_" + std::to_string(2 * layer), current.ln_g1);
    Insert(bindings, "ln_b_" + std::to_string(2 * layer), current.ln_b1);
  }
  Insert(bindings, "b_r_0", gradients.shared_relative_bias);
  Insert(bindings, "embed", gradients.embedding);
  Insert(
      bindings,
      "ln_g_" + std::to_string(2 * geometry.layers),
      gradients.final_ln_gain);
  Insert(
      bindings,
      "ln_b_" + std::to_string(2 * geometry.layers),
      gradients.final_ln_bias);
  Insert(bindings, "out_bias", gradients.output_bias);

  if (bindings.size() != descriptors.size()) {
    throw std::logic_error("gradient binding population differs from topology");
  }
  std::vector<GradientArtifactView> artifacts;
  artifacts.reserve(descriptors.size());
  for (GradientDescriptor& descriptor : descriptors) {
    const auto found = bindings.find(descriptor.name);
    if (found == bindings.end() ||
        found->second.element_type != descriptor.element_type) {
      throw std::logic_error("gradient binding differs for " + descriptor.name);
    }
    const std::size_t expected = Product(descriptor.dimensions, "gradient");
    const std::size_t observed =
        descriptor.element_type == GradientElementType::kBf16
            ? found->second.bf16_values->size()
            : found->second.f32_values->size();
    if (observed != expected) {
      throw std::invalid_argument(
          "gradient buffer size differs for " + descriptor.name);
    }
    artifacts.push_back(
        {std::move(descriptor),
         found->second.bf16_values,
         found->second.f32_values});
  }
  return artifacts;
}

std::vector<ParameterArtifactView> CanonicalParameterArtifacts(
    const ProfileGeometry& geometry,
    ProfileWeights& weights) {
  if (weights.layers.size() != geometry.layers) {
    throw std::invalid_argument("parameter layer population differs");
  }
  std::vector<GradientDescriptor> descriptors =
      CanonicalGradientDescriptors(geometry);
  std::unordered_map<std::string, UntypedParameterView> bindings;
  bindings.reserve(descriptors.size());
  Insert(bindings, "embed_out", weights.output_weight);
  for (std::size_t layer = 0; layer < geometry.layers; ++layer) {
    const std::string suffix = "_" + std::to_string(layer);
    TransformerLayerWeights& current = weights.layers[layer];
    Insert(bindings, "ff2" + suffix, current.ff2);
    Insert(bindings, "ff1" + suffix, current.ff1);
    Insert(bindings, "ln_g_" + std::to_string(2 * layer + 1), current.ln_g2);
    Insert(bindings, "ln_b_" + std::to_string(2 * layer + 1), current.ln_b2);
    Insert(bindings, "ff_bias1" + suffix, current.ff_bias1);
    Insert(bindings, "ff_bias2" + suffix, current.ff_bias2);
    Insert(bindings, "w_o" + suffix, current.w_o);
    Insert(bindings, "w_r" + suffix, current.relative_weight);
    Insert(bindings, "w_kv" + suffix, current.w_kv);
    Insert(bindings, "w_q" + suffix, current.w_q);
    Insert(bindings, "ln_g_" + std::to_string(2 * layer), current.ln_g1);
    Insert(bindings, "ln_b_" + std::to_string(2 * layer), current.ln_b1);
  }
  Insert(bindings, "b_r_0", weights.shared_relative_bias);
  Insert(bindings, "embed", weights.embedding);
  Insert(
      bindings,
      "ln_g_" + std::to_string(2 * geometry.layers),
      weights.final_ln_gain);
  Insert(
      bindings,
      "ln_b_" + std::to_string(2 * geometry.layers),
      weights.final_ln_bias);
  Insert(bindings, "out_bias", weights.output_bias);
  if (bindings.size() != descriptors.size()) {
    throw std::logic_error("parameter binding population differs from topology");
  }
  std::vector<ParameterArtifactView> artifacts;
  artifacts.reserve(descriptors.size());
  for (GradientDescriptor& descriptor : descriptors) {
    const auto found = bindings.find(descriptor.name);
    if (found == bindings.end() ||
        found->second.element_type != descriptor.element_type) {
      throw std::logic_error("parameter binding differs for " + descriptor.name);
    }
    const std::size_t expected = Product(descriptor.dimensions, "parameter");
    const std::size_t observed =
        descriptor.element_type == GradientElementType::kBf16
            ? found->second.bf16_values->size()
            : found->second.f32_values->size();
    if (observed != expected) {
      throw std::invalid_argument(
          "parameter buffer size differs for " + descriptor.name);
    }
    artifacts.push_back(
        {std::move(descriptor),
         found->second.bf16_values,
         found->second.f32_values});
  }
  return artifacts;
}

void WriteCanonicalGradientArtifacts(
    const std::filesystem::path& directory,
    const ProfileGeometry& geometry,
    const ProfileGradients& gradients) {
  const std::vector<GradientArtifactView> artifacts =
      CanonicalGradientArtifacts(geometry, gradients);
  if (!fs::create_directory(directory)) {
    throw std::runtime_error("gradient output directory already exists");
  }
  for (std::size_t index = 0; index < artifacts.size(); ++index) {
    const GradientArtifactView& artifact = artifacts[index];
    const std::string stem = IndexName(index, artifact.descriptor.name);
    unsigned int item_type;
    unsigned int item_size;
    if (artifact.descriptor.element_type == GradientElementType::kBf16) {
      if (artifact.bf16_values == nullptr || artifact.f32_values != nullptr) {
        throw std::logic_error("invalid BF16 artifact binding");
      }
      WritePayload(directory / (stem + ".bin"), *artifact.bf16_values);
      item_type = 1;
      item_size = 2;
    } else {
      if (artifact.f32_values == nullptr || artifact.bf16_values != nullptr) {
        throw std::logic_error("invalid F32 artifact binding");
      }
      WritePayload(directory / (stem + ".bin"), *artifact.f32_values);
      item_type = 0;
      item_size = 4;
    }
    std::ostringstream metadata;
    metadata << "index=" << index << '\n'
             << "name=" << artifact.descriptor.name << '\n'
             << "item_type=" << item_type << '\n'
             << "item_size=" << item_size << '\n'
             << "dims=";
    for (std::size_t axis = 0;
         axis < artifact.descriptor.dimensions.size();
         ++axis) {
      if (axis != 0) metadata << ',';
      metadata << artifact.descriptor.dimensions[axis];
    }
    metadata << "\nbyte_order=little\ncolumn_index=none\n";
    WriteText(directory / (stem + ".meta"), metadata.str());
  }
}

}  // namespace gamma_enwiki9::nncp
