#include "midpoint_kernels.hpp"
#include "profile_artifacts.hpp"
#include "profile_backward.hpp"
#include "profile_fixture.hpp"
#include "profile_forward.hpp"
#include "tensor_container.hpp"
#include "transformer_backward.hpp"

#include <algorithm>
#include <bit>
#include <cerrno>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <unistd.h>
#include <utility>
#include <vector>

namespace nncp = gamma_enwiki9::nncp;

namespace {

void Require(bool value, const char* message) {
  if (!value) throw std::runtime_error(message);
}

nncp::Bf16 Make(std::size_t index, float scale = 0.015625F) {
  const int centered = static_cast<int>((index * 37U + 11U) % 29U) - 14;
  return nncp::FloatToBf16(static_cast<float>(centered) * scale);
}

void PutU32(std::vector<std::uint8_t>& bytes, std::uint32_t value) {
  for (unsigned int shift = 0; shift < 32; shift += 8) {
    bytes.push_back(static_cast<std::uint8_t>(value >> shift));
  }
}

void AddTensor(
    std::vector<std::uint8_t>& bytes,
    std::uint32_t type,
    const std::string& name,
    const std::vector<std::uint32_t>& dimensions,
    const std::vector<std::uint8_t>& payload) {
  PutU32(bytes, UINT32_C(0x23f4aefa));
  PutU32(bytes, type);
  PutU32(bytes, static_cast<std::uint32_t>(dimensions.size()));
  PutU32(bytes, static_cast<std::uint32_t>(name.size()));
  for (std::uint32_t dimension : dimensions) PutU32(bytes, dimension);
  bytes.insert(bytes.end(), name.begin(), name.end());
  bytes.insert(bytes.end(), payload.begin(), payload.end());
}

std::vector<std::uint8_t> NewContainer(const std::string& configuration) {
  std::vector<std::uint8_t> bytes;
  PutU32(bytes, UINT32_C(0x23f4aefb));
  PutU32(bytes, static_cast<std::uint32_t>(configuration.size()));
  bytes.insert(bytes.end(), configuration.begin(), configuration.end());
  return bytes;
}

std::vector<std::uint8_t> Bf16Bytes(
    std::size_t count,
    nncp::Bf16 value = 0) {
  std::vector<std::uint8_t> bytes;
  bytes.reserve(count * 2);
  for (std::size_t index = 0; index < count; ++index) {
    bytes.push_back(static_cast<std::uint8_t>(value));
    bytes.push_back(static_cast<std::uint8_t>(value >> 8U));
  }
  return bytes;
}

std::vector<std::uint8_t> F32Bytes(
    std::size_t count,
    float value = 0.0F) {
  std::vector<std::uint8_t> bytes;
  bytes.reserve(count * 4);
  for (std::size_t index = 0; index < count; ++index) {
    PutU32(bytes, std::bit_cast<std::uint32_t>(value));
  }
  return bytes;
}

std::vector<std::uint8_t> U32Bytes(
    const std::vector<std::uint32_t>& values) {
  std::vector<std::uint8_t> bytes;
  bytes.reserve(values.size() * 4);
  for (std::uint32_t value : values) PutU32(bytes, value);
  return bytes;
}

class TemporaryFile {
 public:
  TemporaryFile() {
    char pattern[] = "/tmp/gamma-nncp-container-XXXXXX";
    fd_ = mkstemp(pattern);
    if (fd_ < 0) {
      throw std::runtime_error(std::string("mkstemp failed: ") + std::strerror(errno));
    }
    path_ = pattern;
  }

  ~TemporaryFile() {
    if (fd_ >= 0) close(fd_);
    if (!path_.empty()) unlink(path_.c_str());
  }

  void Write(const std::vector<std::uint8_t>& bytes) {
    std::size_t offset = 0;
    while (offset < bytes.size()) {
      const ssize_t count = write(fd_, bytes.data() + offset, bytes.size() - offset);
      if (count < 0) {
        if (errno == EINTR) continue;
        throw std::runtime_error(std::string("temporary write failed: ") +
                                 std::strerror(errno));
      }
      if (count == 0) throw std::runtime_error("temporary write made no progress");
      offset += static_cast<std::size_t>(count);
    }
    if (close(fd_) != 0) {
      fd_ = -1;
      throw std::runtime_error("temporary close failed");
    }
    fd_ = -1;
  }

  const std::string& path() const { return path_; }

 private:
  int fd_ = -1;
  std::string path_;
};

class TemporaryDirectory {
 public:
  TemporaryDirectory() {
    char pattern[] = "/tmp/gamma-nncp-artifacts-XXXXXX";
    const char* created = mkdtemp(pattern);
    if (created == nullptr) {
      throw std::runtime_error(std::string("mkdtemp failed: ") +
                               std::strerror(errno));
    }
    path_ = created;
  }

  ~TemporaryDirectory() {
    std::error_code error;
    std::filesystem::remove_all(path_, error);
  }

  const std::filesystem::path& path() const { return path_; }

 private:
  std::filesystem::path path_;
};

void TestTensorContainer() {
  std::vector<std::uint8_t> bytes = NewContainer("cfg");
  std::vector<std::uint8_t> bf16_payload;
  for (std::size_t index = 0; index < 8; ++index) {
    const nncp::Bf16 value = Make(index);
    bf16_payload.push_back(static_cast<std::uint8_t>(value));
    bf16_payload.push_back(static_cast<std::uint8_t>(value >> 8U));
  }
  AddTensor(bytes, 1, "bf", {8}, bf16_payload);
  std::vector<std::uint8_t> f32_payload;
  for (float value : {1.0F, -2.0F, 3.5F, 4.0F}) {
    PutU32(f32_payload, std::bit_cast<std::uint32_t>(value));
  }
  AddTensor(bytes, 0, "fp", {2, 2}, f32_payload);
  std::vector<std::uint8_t> u32_payload;
  PutU32(u32_payload, 17);
  PutU32(u32_payload, 29);
  AddTensor(bytes, 5, "ui", {2}, u32_payload);
  TemporaryFile file;
  file.Write(bytes);
  const nncp::TensorContainer container(file.path());
  Require(container.configuration() == "cfg", "container configuration differs");
  Require(container.tensors().size() == 3, "container tensor count differs");
  Require(container.contains("fp") && !container.contains("missing"),
          "container name index differs");
  const nncp::Bf16Buffer bf = container.CopyBf16("bf", {8});
  Require(bf.size() == 8 && bf[3] == Make(3), "container BF16 copy differs");
  const std::vector<float> fp = container.CopyF32("fp", {2, 2});
  Require(fp == std::vector<float>({1.0F, -2.0F, 3.5F, 4.0F}),
          "container F32 copy differs");
  const std::vector<std::uint32_t> ui = container.CopyU32("ui", {2});
  Require(ui == std::vector<std::uint32_t>({17, 29}),
          "container U32 copy differs");
  bool rejected = false;
  try {
    static_cast<void>(container.CopyBf16("bf", {4, 2}));
  } catch (const std::runtime_error&) {
    rejected = true;
  }
  Require(rejected, "container accepted a forged tensor shape");
}

void TestProfileFixtureLoader() {
  const nncp::ProfileGeometry geometry{
      .transformer = {2, 2, 1, 128, 126, 128},
      .layers = 1,
      .vocabulary = 8,
      .loss_start = 0,
      .loss_length = 1,
  };
  constexpr std::uint32_t model = 128;
  constexpr std::uint32_t positions = 128;
  constexpr std::uint32_t inner = 128;
  std::vector<std::uint8_t> parameters = NewContainer("p\n");
  const auto add_bf16 = [&parameters](
                              const std::string& name,
                              std::vector<std::uint32_t> dimensions,
                              std::size_t elements,
                              nncp::Bf16 value = 0) {
    AddTensor(
        parameters, 1, name, dimensions, Bf16Bytes(elements, value));
  };
  add_bf16("b_r_0", {positions, 1}, positions);
  add_bf16("w_r_0", {128, positions, 1}, positions * model);
  add_bf16("w_q_0", {model, model}, model * model);
  add_bf16("w_kv_0", {2 * model, model}, 2 * model * model);
  add_bf16("w_o_0", {model, model}, model * model);
  add_bf16("ff1_0", {2 * inner, model}, 2 * inner * model);
  add_bf16("ff_bias1_0", {2 * inner}, 2 * inner);
  add_bf16("ff2_0", {model, inner}, model * inner);
  add_bf16("ff_bias2_0", {model}, model);
  add_bf16("ln_g_0", {model}, model, nncp::FloatToBf16(1.0F));
  add_bf16("ln_b_0", {model}, model);
  add_bf16("ln_g_1", {model}, model, nncp::FloatToBf16(1.0F));
  add_bf16("ln_b_1", {model}, model);
  add_bf16("ln_g_2", {model}, model, nncp::FloatToBf16(1.0F));
  add_bf16("ln_b_2", {model}, model);
  AddTensor(
      parameters,
      0,
      "embed",
      {model, 8},
      F32Bytes(static_cast<std::size_t>(model) * 8));
  add_bf16("embed_out", {8, model}, static_cast<std::size_t>(model) * 8);
  add_bf16("out_bias", {8}, 8);

  std::vector<std::uint8_t> state = NewContainer("s\n");
  const std::vector<std::uint32_t> symbols{0, 1, 2, 3};
  AddTensor(state, 5, "input_all_streams", {2, 2}, U32Bytes(symbols));
  AddTensor(state, 5, "target_all_streams", {2, 2}, U32Bytes(symbols));
  AddTensor(
      state,
      1,
      "mem_h_0",
      {model, 2, 126},
      Bf16Bytes(static_cast<std::size_t>(model) * 2 * 126));
  AddTensor(
      state,
      1,
      "train_h_0",
      {model, 2, 2},
      Bf16Bytes(static_cast<std::size_t>(model) * 2 * 2));
  TemporaryFile parameter_file;
  TemporaryFile state_file;
  parameter_file.Write(parameters);
  state_file.Write(state);
  const nncp::ProfileFixtureInputs fixture = nncp::LoadProfileFixture(
      geometry,
      parameter_file.path(),
      state_file.path(),
      nncp::FutureInputPolicy::kPreserve);
  Require(fixture.weights.layers.size() == 1, "fixture layer count differs");
  Require(fixture.input_symbols == symbols, "fixture input symbols differ");
  Require(fixture.targets == symbols, "fixture targets differ");
  Require(fixture.memory_inputs.size() == 1, "fixture memory count differs");
  Require(
      fixture.memory_inputs[0].size() ==
          static_cast<std::size_t>(model) * 2 * 126,
      "fixture memory geometry differs");
}

void TestGradientArtifacts() {
  const nncp::ProfileGeometry geometry{
      .transformer = {2, 2, 1, 128, 126, 128},
      .layers = 1,
      .vocabulary = 8,
      .loss_start = 0,
      .loss_length = 1,
  };
  constexpr std::size_t model = 128;
  constexpr std::size_t positions = 128;
  constexpr std::size_t inner = 128;
  nncp::TransformerLayerGradients layer{
      .ff2 = nncp::Bf16Buffer(model * inner, 0),
      .ff1 = nncp::Bf16Buffer(2 * inner * model, 0),
      .ln_g2 = nncp::Bf16Buffer(model, 0),
      .ln_b2 = nncp::Bf16Buffer(model, 0),
      .ff_bias1 = nncp::Bf16Buffer(2 * inner, 0),
      .ff_bias2 = nncp::Bf16Buffer(model, 0),
      .w_o = nncp::Bf16Buffer(model * model, 0),
      .w_r = nncp::Bf16Buffer(positions * model, 0),
      .w_kv = nncp::Bf16Buffer(2 * model * model, 0),
      .w_q = nncp::Bf16Buffer(model * model, 0),
      .ln_g1 = nncp::Bf16Buffer(model, 0),
      .ln_b1 = nncp::Bf16Buffer(model, 0),
      .relative_bias_contribution = nncp::Bf16Buffer(positions, 0),
  };
  nncp::ProfileGradients gradients{
      .output_weight = nncp::Bf16Buffer(8 * model, 0),
      .layers = {std::move(layer)},
      .shared_relative_bias = nncp::Bf16Buffer(positions, 0),
      .embedding = nncp::F32Buffer(model * 8, 0.0F),
      .final_ln_gain = nncp::Bf16Buffer(model, 0),
      .final_ln_bias = nncp::Bf16Buffer(model, 0),
      .output_bias = nncp::Bf16Buffer(8, 0),
  };
  const std::vector<nncp::GradientArtifactView> artifacts =
      nncp::CanonicalGradientArtifacts(geometry, gradients);
  Require(artifacts.size() == 18, "synthetic artifact count differs");
  Require(artifacts.front().descriptor.name == "embed_out",
          "synthetic first artifact differs");
  Require(artifacts[9].descriptor.name == "b_r_0",
          "synthetic shared-bias position differs");
  Require(artifacts[14].descriptor.name == "embed" &&
              artifacts[14].f32_values == &gradients.embedding,
          "synthetic F32 artifact binding differs");
  Require(artifacts.back().descriptor.name == "out_bias",
          "synthetic last artifact differs");

  TemporaryDirectory temporary;
  const std::filesystem::path output = temporary.path() / "gradients";
  nncp::WriteCanonicalGradientArtifacts(output, geometry, gradients);
  std::size_t regular_files = 0;
  for (const auto& entry : std::filesystem::directory_iterator(output)) {
    Require(entry.is_regular_file(), "artifact output is not a regular file");
    Require(entry.path().extension() != ".partial",
            "artifact output retained a partial file");
    ++regular_files;
  }
  Require(regular_files == artifacts.size() * 2,
          "artifact file population differs");
  Require(std::filesystem::file_size(output / "0000_embed_out.bin") ==
              8 * model * sizeof(nncp::Bf16),
          "first artifact payload size differs");
  std::ifstream metadata(output / "0014_embed.meta", std::ios::binary);
  const std::string metadata_text{
      std::istreambuf_iterator<char>(metadata),
      std::istreambuf_iterator<char>()};
  Require(
      metadata_text ==
          "index=14\nname=embed\nitem_type=0\nitem_size=4\n"
          "dims=128,8\nbyte_order=little\ncolumn_index=none\n",
      "F32 artifact metadata differs");

  gradients.output_bias.pop_back();
  bool rejected = false;
  try {
    static_cast<void>(nncp::CanonicalGradientArtifacts(geometry, gradients));
  } catch (const std::invalid_argument&) {
    rejected = true;
  }
  Require(rejected, "artifact binder accepted a truncated gradient");
}

void TestBf16() {
  Require(nncp::FloatToBf16(1.0F) == UINT16_C(0x3f80), "BF16 one differs");
  Require(nncp::Bf16ToFloat(UINT16_C(0xbf80)) == -1.0F, "BF16 minus one differs");
  const float halfway_even = std::bit_cast<float>(UINT32_C(0x3f808000));
  Require(
      nncp::FloatToBf16(halfway_even) == UINT16_C(0x3f80),
      "BF16 ties-to-even differs");
}

void TestStatewiseBias() {
  constexpr std::size_t states = 3;
  constexpr std::size_t streams = 4;
  constexpr std::size_t features = 8;
  nncp::Bf16Buffer residuals(states * streams * features);
  for (std::size_t index = 0; index < residuals.size(); ++index) {
    residuals[index] = Make(index);
  }
  const nncp::Bf16Buffer observed =
      nncp::StatewiseBiasGradient(residuals, states, streams, features);
  nncp::Bf16Buffer expected(features, 0);
  for (std::size_t state = 0; state < states; ++state) {
    for (std::size_t feature = 0; feature < features; ++feature) {
      float total = nncp::Bf16ToFloat(expected[feature]);
      for (std::size_t stream = 0; stream < streams; ++stream) {
        total += nncp::Bf16ToFloat(
            residuals[(state * streams + stream) * features + feature]);
      }
      expected[feature] = nncp::FloatToBf16(total);
    }
  }
  Require(observed == expected, "statewise bias gradient differs");
}

void TestStatewiseWeight() {
  constexpr std::size_t states = 3;
  constexpr std::size_t streams = 4;
  constexpr std::size_t inputs_count = 5;
  constexpr std::size_t outputs_count = 16;
  nncp::Bf16Buffer inputs(states * streams * inputs_count);
  nncp::Bf16Buffer residuals(states * streams * outputs_count);
  for (std::size_t index = 0; index < inputs.size(); ++index) inputs[index] = Make(index);
  for (std::size_t index = 0; index < residuals.size(); ++index) {
    residuals[index] = Make(index + 101U, 0.0078125F);
  }
  const nncp::Bf16Buffer observed = nncp::StatewiseWeightGradient(
      inputs, residuals, states, streams, inputs_count, outputs_count);
  nncp::Bf16Buffer expected(inputs_count * outputs_count, 0);
  for (std::size_t state = 0; state < states; ++state) {
    for (std::size_t input = 0; input < inputs_count; ++input) {
      for (std::size_t output = 0; output < outputs_count; ++output) {
        float dot = 0.0F;
        for (std::size_t stream = 0; stream < streams; ++stream) {
          const std::size_t sample = state * streams + stream;
          dot = std::fma(
              nncp::Bf16ToFloat(inputs[sample * inputs_count + input]),
              nncp::Bf16ToFloat(residuals[sample * outputs_count + output]),
              dot);
        }
        const std::size_t target = input * outputs_count + output;
        expected[target] = nncp::FloatToBf16(
            dot + nncp::Bf16ToFloat(expected[target]));
      }
    }
  }
  Require(observed == expected, "statewise weight gradient differs");
}

void TestFlatReductions() {
  constexpr std::size_t samples = 131;
  constexpr std::size_t inputs_count = 3;
  constexpr std::size_t outputs_count = 8;
  nncp::Bf16Buffer inputs(samples * inputs_count);
  nncp::Bf16Buffer residuals(samples * outputs_count);
  for (std::size_t index = 0; index < inputs.size(); ++index) inputs[index] = Make(index);
  for (std::size_t index = 0; index < residuals.size(); ++index) {
    residuals[index] = Make(index + 809U, 0.00390625F);
  }
  const nncp::Bf16Buffer bias =
      nncp::FlatBiasGradient(residuals, samples, outputs_count);
  const nncp::Bf16Buffer weight = nncp::Flat128WeightGradient(
      inputs, residuals, samples, inputs_count, outputs_count);
  for (std::size_t output = 0; output < outputs_count; ++output) {
    float expected_bias = 0.0F;
    for (std::size_t sample = 0; sample < samples; ++sample) {
      expected_bias += nncp::Bf16ToFloat(residuals[sample * outputs_count + output]);
    }
    Require(bias[output] == nncp::FloatToBf16(expected_bias), "flat bias differs");
    for (std::size_t input = 0; input < inputs_count; ++input) {
      float total = 0.0F;
      for (std::size_t panel = 0; panel < samples; panel += 128) {
        float partial = 0.0F;
        const std::size_t end = std::min(samples, panel + 128);
        for (std::size_t sample = panel; sample < end; ++sample) {
          partial = std::fma(
              nncp::Bf16ToFloat(inputs[sample * inputs_count + input]),
              nncp::Bf16ToFloat(residuals[sample * outputs_count + output]),
              partial);
        }
        total += partial;
      }
      Require(
          weight[input * outputs_count + output] == nncp::FloatToBf16(total),
          "flat weight gradient differs");
    }
  }
}

void TestElementwiseBackward() {
  constexpr std::size_t samples = 3;
  constexpr std::size_t inner = 8;
  nncp::Bf16Buffer ff1(samples * 2 * inner);
  nncp::Bf16Buffer incoming(samples * inner);
  for (std::size_t index = 0; index < ff1.size(); ++index) ff1[index] = Make(index);
  for (std::size_t index = 0; index < incoming.size(); ++index) {
    incoming[index] = Make(index + 907U, 0.0078125F);
  }
  const nncp::GegluBackwardResult result =
      nncp::GegluBackward(ff1, incoming, samples, inner);
  Require(result.ff2_input_adjoint == incoming, "GEGLU input boundary differs");
  Require(result.ff1_output_adjoint.size() == ff1.size(), "GEGLU output size differs");
  const nncp::Bf16Buffer doubled = nncp::AddBf16(incoming, incoming);
  for (std::size_t index = 0; index < doubled.size(); ++index) {
    Require(
        doubled[index] == nncp::FloatToBf16(
            2.0F * nncp::Bf16ToFloat(incoming[index])),
        "BF16 residual add differs");
  }
}

void TestLossAndSoftmax() {
  constexpr std::size_t states = 4;
  constexpr std::size_t streams = 2;
  constexpr std::size_t vocabulary = 8;
  std::vector<float> probabilities(states * streams * vocabulary, 0.125F);
  std::vector<std::uint32_t> targets(states * streams);
  for (std::size_t index = 0; index < targets.size(); ++index) {
    targets[index] = static_cast<std::uint32_t>(index % vocabulary);
  }
  const nncp::Bf16Buffer residual = nncp::CrossEntropyLogitResidual(
      probabilities, targets, states, streams, vocabulary, 1, 2);
  for (std::size_t state = 0; state < states; ++state) {
    for (std::size_t stream = 0; stream < streams; ++stream) {
      const std::size_t sample = state * streams + stream;
      for (std::size_t symbol = 0; symbol < vocabulary; ++symbol) {
        const std::size_t index = sample * vocabulary + symbol;
        if (state == 0 || state == 3) {
          Require(residual[index] == 0, "loss escaped its frozen window");
        } else {
          float expected = 0.125F / 4.0F;
          if (symbol == targets[sample]) expected -= 0.25F;
          Require(
              residual[index] == nncp::FloatToBf16(expected),
              "cross-entropy residual differs");
        }
      }
    }
  }

  nncp::Bf16Buffer softmax_probability(16, nncp::FloatToBf16(0.125F));
  nncp::Bf16Buffer softmax_incoming(16);
  for (std::size_t index = 0; index < softmax_incoming.size(); ++index) {
    softmax_incoming[index] = Make(index + 1009U, 0.0078125F);
  }
  const nncp::Bf16Buffer score =
      nncp::SoftmaxBackward(softmax_probability, softmax_incoming, 2, 8);
  for (std::size_t row = 0; row < 2; ++row) {
    float dot = 0.0F;
    for (std::size_t key = 0; key < 8; ++key) {
      dot += nncp::Bf16ToFloat(softmax_probability[row * 8 + key]) *
          nncp::Bf16ToFloat(softmax_incoming[row * 8 + key]);
    }
    for (std::size_t key = 0; key < 8; ++key) {
      const float expected =
          nncp::Bf16ToFloat(softmax_probability[row * 8 + key]) *
          (nncp::Bf16ToFloat(softmax_incoming[row * 8 + key]) - dot);
      Require(
          score[row * 8 + key] == nncp::FloatToBf16(expected),
          "softmax backward differs");
    }
  }
}

void TestAttentionReverseProducts() {
  const nncp::AttentionGeometry geometry{3, 2, 2, 8, 8};
  nncp::Bf16Buffer probability(
      geometry.states * geometry.streams * geometry.heads * geometry.keys);
  nncp::Bf16Buffer incoming(
      geometry.states * geometry.streams * geometry.heads * geometry.width);
  nncp::Bf16Buffer key(
      geometry.streams * geometry.heads * geometry.keys * geometry.width);
  nncp::Bf16Buffer query(incoming.size());
  nncp::Bf16Buffer score(probability.size());
  for (std::size_t index = 0; index < probability.size(); ++index) {
    probability[index] = Make(index + 1201U, 0.00390625F);
    score[index] = Make(index + 1301U, 0.00390625F);
  }
  for (std::size_t index = 0; index < incoming.size(); ++index) {
    incoming[index] = Make(index + 1409U, 0.0078125F);
    query[index] = Make(index + 1601U, 0.0078125F);
  }
  for (std::size_t index = 0; index < key.size(); ++index) {
    key[index] = Make(index + 1801U, 0.0078125F);
  }
  const nncp::Bf16Buffer value_gradient =
      nncp::AttentionValueGradient(probability, incoming, geometry);
  const nncp::AttentionDotBackwardResult dot =
      nncp::AttentionDotBackward(key, query, score, geometry);
  Require(value_gradient.size() == key.size(), "attention value gradient size differs");
  Require(dot.key_adjoint.size() == key.size(), "attention key adjoint size differs");
  Require(dot.query_adjoint.size() == query.size(), "attention query adjoint size differs");

  const std::size_t stream = 1;
  const std::size_t head = 0;
  const std::size_t key_index = 3;
  const std::size_t feature = 5;
  float expected_value = 0.0F;
  float expected_key = 0.0F;
  for (std::size_t state = 0; state < geometry.states; ++state) {
    const std::size_t score_index =
        (((state * geometry.streams + stream) * geometry.heads + head) *
         geometry.keys + key_index);
    const std::size_t vector_index =
        (((state * geometry.streams + stream) * geometry.heads + head) *
         geometry.width + feature);
    expected_value = nncp::RoundToBf16(std::fma(
        nncp::Bf16ToFloat(probability[score_index]),
        nncp::Bf16ToFloat(incoming[vector_index]),
        expected_value));
    expected_key = nncp::RoundToBf16(
        expected_key +
        nncp::Bf16ToFloat(score[score_index]) *
            nncp::Bf16ToFloat(query[vector_index]));
  }
  const std::size_t key_vector_index =
      (((stream * geometry.heads + head) * geometry.keys + key_index) *
       geometry.width + feature);
  Require(
      value_gradient[key_vector_index] == nncp::FloatToBf16(expected_value),
      "attention value gradient arithmetic differs");
  Require(
      dot.key_adjoint[key_vector_index] == nncp::FloatToBf16(expected_key),
      "attention key adjoint arithmetic differs");
}

void TestRelativeShiftBackward() {
  constexpr std::size_t states = 4;
  constexpr std::size_t streams = 2;
  constexpr std::size_t heads = 2;
  constexpr std::size_t positions = 8;
  nncp::Bf16Buffer shifted(states * streams * heads * positions);
  for (std::size_t index = 0; index < shifted.size(); ++index) {
    shifted[index] = static_cast<nncp::Bf16>(index + 1);
  }
  const nncp::Bf16Buffer raw = nncp::RelativeShiftBackward(
      shifted, states, streams, heads, positions);
  std::size_t assigned = 0;
  for (std::size_t state = 0; state < states; ++state) {
    for (std::size_t stream = 0; stream < streams; ++stream) {
      for (std::size_t head = 0; head < heads; ++head) {
        for (std::size_t position = 0; position < positions; ++position) {
          const std::size_t flat = states + state * positions + position;
          const std::size_t raw_state = flat / (positions + 1);
          const std::size_t padded_position = flat % (positions + 1);
          if (raw_state >= states || padded_position == 0) continue;
          const std::size_t shifted_index =
              (((state * streams + stream) * heads + head) * positions + position);
          const std::size_t raw_index =
              (((raw_state * streams + stream) * heads + head) * positions +
               padded_position - 1);
          Require(raw[raw_index] == shifted[shifted_index], "relative shift differs");
          ++assigned;
        }
      }
    }
  }
  Require(assigned > 0 && assigned < raw.size(), "relative shift control is dead");
}

void TestRelativeProjectionAndKvMerge() {
  const nncp::AttentionGeometry geometry{2, 2, 2, 8, 8};
  nncp::Bf16Buffer query(
      geometry.states * geometry.streams * geometry.heads * geometry.width);
  nncp::Bf16Buffer weight(
      geometry.heads * geometry.keys * geometry.width);
  nncp::Bf16Buffer raw(
      geometry.states * geometry.streams * geometry.heads * geometry.keys);
  for (std::size_t index = 0; index < query.size(); ++index) query[index] = Make(index);
  for (std::size_t index = 0; index < weight.size(); ++index) {
    weight[index] = Make(index + 1901U, 0.0078125F);
  }
  for (std::size_t index = 0; index < raw.size(); ++index) {
    raw[index] = Make(index + 2003U, 0.00390625F);
  }
  const nncp::RelativeProjectionBackwardResult relative =
      nncp::RelativeProjectionBackward(query, weight, raw, geometry, 4.0F);
  Require(relative.weight_gradient.size() == weight.size(), "relative weight size differs");
  Require(
      relative.bias_gradient.size() == geometry.heads * geometry.keys,
      "relative bias size differs");
  Require(relative.query_adjoint.size() == query.size(), "relative query size differs");

  constexpr std::size_t positions = 4;
  nncp::Bf16Buffer key(
      geometry.streams * geometry.heads * positions * geometry.width);
  nncp::Bf16Buffer value(key.size());
  for (std::size_t index = 0; index < key.size(); ++index) {
    key[index] = static_cast<nncp::Bf16>(index + 1);
    value[index] = static_cast<nncp::Bf16>(index + 1001);
  }
  const nncp::Bf16Buffer merged = nncp::MergeKeyValueAdjoints(
      key, value, geometry.streams, geometry.heads, positions, geometry.width);
  const nncp::Bf16Buffer current = nncp::SlicePositionRange(
      merged,
      positions,
      geometry.streams,
      2 * geometry.heads * geometry.width,
      1,
      2);
  Require(
      current.size() == 2 * geometry.streams * 2 * geometry.heads * geometry.width,
      "K/V current slice size differs");
  const std::size_t head = 1;
  const std::size_t feature = 3;
  const std::size_t stream = 1;
  const std::size_t position = 2;
  const std::size_t model_width = geometry.heads * geometry.width;
  const std::size_t source =
      (((stream * geometry.heads + head) * positions + position) * geometry.width +
       feature);
  const std::size_t target =
      (position * geometry.streams + stream) * 2 * model_width +
      head * geometry.width + feature;
  Require(merged[target] == key[source], "merged key coordinate differs");
  Require(merged[target + model_width] == value[source], "merged value coordinate differs");
}

void TestTransformerLayerZeroAdjoint() {
  const nncp::TransformerGeometry geometry{2, 2, 1, 128, 126, 128};
  constexpr std::size_t model = 128;
  constexpr std::size_t positions = 128;
  constexpr std::size_t samples = 4;
  nncp::TransformerLayerWeights weights{
      .ln_g1 = nncp::Bf16Buffer(model, nncp::FloatToBf16(1.0F)),
      .ln_b1 = nncp::Bf16Buffer(model, 0),
      .w_q = nncp::Bf16Buffer(model * model, 0),
      .w_kv = nncp::Bf16Buffer(model * 2 * model, 0),
      .relative_weight = nncp::Bf16Buffer(positions * model, 0),
      .w_o = nncp::Bf16Buffer(model * model, 0),
      .ln_g2 = nncp::Bf16Buffer(model, nncp::FloatToBf16(1.0F)),
      .ln_b2 = nncp::Bf16Buffer(model, 0),
      .ff1 = nncp::Bf16Buffer(model * 2 * geometry.inner, 0),
      .ff_bias1 = nncp::Bf16Buffer(2 * geometry.inner, 0),
      .ff2 = nncp::Bf16Buffer(geometry.inner * model, 0),
      .ff_bias2 = nncp::Bf16Buffer(model, 0),
  };
  nncp::TransformerLayerCache cache{
      .hidden_input = nncp::Bf16Buffer(samples * model, 0),
      .attention_input = nncp::Bf16Buffer(samples * model, 0),
      .attention_residual = nncp::Bf16Buffer(samples * model, 0),
      .feedforward_input = nncp::Bf16Buffer(samples * model, 0),
      .merged_attention = nncp::Bf16Buffer(samples * model, 0),
      .ff1_output = nncp::Bf16Buffer(samples * 2 * geometry.inner, 0),
      .geglu = nncp::Bf16Buffer(samples * geometry.inner, 0),
      .memory_attention_input =
          nncp::Bf16Buffer(geometry.memory * geometry.streams * model, 0),
      .query = nncp::Bf16Buffer(samples * model, 0),
      .key = nncp::Bf16Buffer(geometry.streams * positions * model, 0),
      .value = nncp::Bf16Buffer(geometry.streams * positions * model, 0),
      .attention_probability =
          nncp::Bf16Buffer(samples * positions, nncp::FloatToBf16(1.0F / 128.0F)),
  };
  const nncp::Bf16Buffer incoming(samples * model, 0);
  const nncp::TransformerLayerBackwardResult result =
      nncp::TransformerLayerBackward(geometry, weights, cache, incoming);
  Require(result.hidden_input_adjoint == incoming, "zero layer adjoint became nonzero");
  const auto all_zero = [](const nncp::Bf16Buffer& values) {
    return std::all_of(values.begin(), values.end(), [](nncp::Bf16 value) {
      return value == 0;
    });
  };
  Require(all_zero(result.gradients.ff2), "zero FF2 gradient became nonzero");
  Require(all_zero(result.gradients.ff1), "zero FF1 gradient became nonzero");
  Require(all_zero(result.gradients.w_o), "zero w_o gradient became nonzero");
  Require(all_zero(result.gradients.w_r), "zero w_r gradient became nonzero");
  Require(all_zero(result.gradients.w_kv), "zero w_kv gradient became nonzero");
  Require(all_zero(result.gradients.w_q), "zero w_q gradient became nonzero");
}

void TestProfileBackwardTopology() {
  const nncp::ProfileGeometry production{
      .transformer = {64, 32, 8, 128, 256, 3072},
      .layers = 20,
      .vocabulary = 16392,
      .loss_start = 0,
      .loss_length = 32,
  };
  const std::vector<nncp::GradientDescriptor> descriptors =
      nncp::CanonicalGradientDescriptors(production);
  Require(descriptors.size() == 246, "production gradient count differs");
  Require(descriptors[0].name == "embed_out", "first gradient differs");
  Require(descriptors[1].name == "ff2_19", "top FF2 gradient differs");
  Require(descriptors[236].name == "w_r_0", "bottom relative weight differs");
  Require(descriptors[237].name == "b_r_0", "shared relative bias differs");
  Require(descriptors[242].name == "embed", "embedding gradient differs");
  Require(
      descriptors[242].element_type == nncp::GradientElementType::kF32,
      "embedding gradient type differs");
  Require(descriptors[245].name == "out_bias", "last gradient differs");

  const nncp::ProfileGeometry geometry{
      .transformer = {2, 2, 1, 128, 126, 128},
      .layers = 1,
      .vocabulary = 8,
      .loss_start = 0,
      .loss_length = 1,
  };
  constexpr std::size_t model = 128;
  constexpr std::size_t positions = 128;
  constexpr std::size_t samples = 4;
  nncp::TransformerLayerWeights layer_weights{
      .ln_g1 = nncp::Bf16Buffer(model, nncp::FloatToBf16(1.0F)),
      .ln_b1 = nncp::Bf16Buffer(model, 0),
      .w_q = nncp::Bf16Buffer(model * model, 0),
      .w_kv = nncp::Bf16Buffer(model * 2 * model, 0),
      .relative_weight = nncp::Bf16Buffer(positions * model, 0),
      .w_o = nncp::Bf16Buffer(model * model, 0),
      .ln_g2 = nncp::Bf16Buffer(model, nncp::FloatToBf16(1.0F)),
      .ln_b2 = nncp::Bf16Buffer(model, 0),
      .ff1 = nncp::Bf16Buffer(model * 2 * geometry.transformer.inner, 0),
      .ff_bias1 = nncp::Bf16Buffer(2 * geometry.transformer.inner, 0),
      .ff2 = nncp::Bf16Buffer(geometry.transformer.inner * model, 0),
      .ff_bias2 = nncp::Bf16Buffer(model, 0),
  };
  nncp::TransformerLayerCache layer_cache{
      .hidden_input = nncp::Bf16Buffer(samples * model, 0),
      .attention_input = nncp::Bf16Buffer(samples * model, 0),
      .attention_residual = nncp::Bf16Buffer(samples * model, 0),
      .feedforward_input = nncp::Bf16Buffer(samples * model, 0),
      .merged_attention = nncp::Bf16Buffer(samples * model, 0),
      .ff1_output =
          nncp::Bf16Buffer(samples * 2 * geometry.transformer.inner, 0),
      .geglu = nncp::Bf16Buffer(samples * geometry.transformer.inner, 0),
      .memory_attention_input = nncp::Bf16Buffer(
          geometry.transformer.memory * geometry.transformer.streams * model, 0),
      .query = nncp::Bf16Buffer(samples * model, 0),
      .key = nncp::Bf16Buffer(
          geometry.transformer.streams * positions * model, 0),
      .value = nncp::Bf16Buffer(
          geometry.transformer.streams * positions * model, 0),
      .attention_probability = nncp::Bf16Buffer(samples * positions, 0),
  };
  nncp::F32Buffer probabilities(samples * geometry.vocabulary, 0.0F);
  std::vector<std::uint32_t> targets(samples);
  for (std::size_t sample = 0; sample < samples; ++sample) {
    targets[sample] = static_cast<std::uint32_t>(sample % geometry.vocabulary);
    probabilities[sample * geometry.vocabulary + targets[sample]] = 1.0F;
  }
  const nncp::ProfileWeights weights{
      .output_weight = nncp::Bf16Buffer(model * geometry.vocabulary, 0),
      .final_ln_gain = nncp::Bf16Buffer(model, nncp::FloatToBf16(1.0F)),
      .layers = {layer_weights},
      .embedding = nncp::F32Buffer(model * geometry.vocabulary, 0.0F),
      .shared_relative_bias = nncp::Bf16Buffer(positions, 0),
      .final_ln_bias = nncp::Bf16Buffer(model, 0),
      .output_bias = nncp::Bf16Buffer(geometry.vocabulary, 0),
  };
  const nncp::ProfileCache cache{
      .pre_final_hidden = nncp::Bf16Buffer(samples * model, 0),
      .final_hidden = nncp::Bf16Buffer(samples * model, 0),
      .layers = {layer_cache},
      .probabilities = probabilities,
      .targets = targets,
      .input_symbols = targets,
  };
  const nncp::ProfileBackwardResult result =
      nncp::ProfileBackward(geometry, weights, cache);
  const auto all_zero_bf16 = [](const nncp::Bf16Buffer& values) {
    return std::all_of(values.begin(), values.end(), [](nncp::Bf16 value) {
      return value == 0;
    });
  };
  Require(all_zero_bf16(result.gradients.output_weight),
          "zero profile output gradient became nonzero");
  Require(all_zero_bf16(result.gradients.shared_relative_bias),
          "zero profile relative bias became nonzero");
  Require(
      std::all_of(
          result.gradients.embedding.begin(),
          result.gradients.embedding.end(),
          [](float value) { return value == 0.0F; }),
      "zero profile embedding gradient became nonzero");
  Require(all_zero_bf16(result.checkpoints.embedding_input_adjoint),
          "zero profile input adjoint became nonzero");
}

void TestProfileForwardBackwardComposition() {
  const nncp::ProfileGeometry geometry{
      .transformer = {2, 2, 1, 128, 126, 128},
      .layers = 1,
      .vocabulary = 8,
      .loss_start = 0,
      .loss_length = 1,
  };
  constexpr std::size_t model = 128;
  constexpr std::size_t positions = 128;
  constexpr std::size_t samples = 4;
  nncp::TransformerLayerWeights layer{
      .ln_g1 = nncp::Bf16Buffer(model, nncp::FloatToBf16(1.0F)),
      .ln_b1 = nncp::Bf16Buffer(model, 0),
      .w_q = nncp::Bf16Buffer(model * model, 0),
      .w_kv = nncp::Bf16Buffer(model * 2 * model, 0),
      .relative_weight = nncp::Bf16Buffer(positions * model, 0),
      .w_o = nncp::Bf16Buffer(model * model, 0),
      .ln_g2 = nncp::Bf16Buffer(model, nncp::FloatToBf16(1.0F)),
      .ln_b2 = nncp::Bf16Buffer(model, 0),
      .ff1 = nncp::Bf16Buffer(model * 2 * geometry.transformer.inner, 0),
      .ff_bias1 = nncp::Bf16Buffer(2 * geometry.transformer.inner, 0),
      .ff2 = nncp::Bf16Buffer(geometry.transformer.inner * model, 0),
      .ff_bias2 = nncp::Bf16Buffer(model, 0),
  };
  const nncp::ProfileWeights weights{
      .output_weight = nncp::Bf16Buffer(model * geometry.vocabulary, 0),
      .final_ln_gain = nncp::Bf16Buffer(model, nncp::FloatToBf16(1.0F)),
      .layers = {std::move(layer)},
      .embedding = nncp::F32Buffer(model * geometry.vocabulary, 0.0F),
      .shared_relative_bias = nncp::Bf16Buffer(positions, 0),
      .final_ln_bias = nncp::Bf16Buffer(model, 0),
      .output_bias = nncp::Bf16Buffer(geometry.vocabulary, 0),
  };
  const std::vector<std::uint32_t> symbols{0, 1, 2, 3};
  const nncp::ProfileCache cache = nncp::ProfileForward(
      geometry,
      weights,
      symbols,
      symbols,
      {nncp::Bf16Buffer(
          geometry.transformer.memory * geometry.transformer.streams * model, 0)});
  Require(cache.layers.size() == 1, "forward layer cache count differs");
  Require(cache.final_hidden.size() == samples * model,
          "forward final hidden size differs");
  Require(cache.probabilities.size() == samples * geometry.vocabulary,
          "forward probability size differs");
  for (float probability : cache.probabilities) {
    Require(probability == 0.125F, "zero-logit probability differs");
  }
  const nncp::ProfileBackwardResult backward =
      nncp::ProfileBackward(geometry, weights, cache);
  Require(
      std::any_of(
          backward.gradients.output_bias.begin(),
          backward.gradients.output_bias.end(),
          [](nncp::Bf16 value) { return value != 0; }),
      "live causal loss produced no output-bias gradient");
  Require(
      std::all_of(
          backward.gradients.embedding.begin(),
          backward.gradients.embedding.end(),
          [](float value) { return value == 0.0F; }),
      "zero output matrix leaked a gradient into embedding");
}

void TestPanelledInputAdjoint() {
  constexpr std::size_t samples = 2;
  constexpr std::size_t reduction = 256;
  constexpr std::size_t destination = 16;
  nncp::Bf16Buffer weights(destination * reduction);
  nncp::Bf16Buffer incoming(samples * reduction);
  for (std::size_t index = 0; index < weights.size(); ++index) {
    weights[index] = Make(index, 0.00390625F);
  }
  for (std::size_t index = 0; index < incoming.size(); ++index) {
    incoming[index] = Make(index + 211U, 0.0078125F);
  }
  const nncp::Bf16Buffer observed = nncp::Panel128InputAdjoint(
      weights, incoming, samples, reduction, destination);
  nncp::Bf16Buffer expected(samples * destination);
  for (std::size_t sample = 0; sample < samples; ++sample) {
    for (std::size_t feature = 0; feature < destination; ++feature) {
      float total = 0.0F;
      for (std::size_t panel = 0; panel < reduction; panel += 128) {
        float partial = 0.0F;
        for (std::size_t reduce = panel; reduce < panel + 128; ++reduce) {
          partial = std::fma(
              nncp::Bf16ToFloat(incoming[sample * reduction + reduce]),
              nncp::Bf16ToFloat(weights[feature * reduction + reduce]),
              partial);
        }
        total += partial;
      }
      expected[sample * destination + feature] = nncp::FloatToBf16(total);
    }
  }
  Require(observed == expected, "panelled input adjoint differs");
}

void TestAttentionBridge() {
  const nncp::AttentionGeometry geometry{2, 3, 2, 8, 4};
  nncp::Bf16Buffer value(
      geometry.streams * geometry.heads * geometry.keys * geometry.width);
  nncp::Bf16Buffer incoming(
      geometry.states * geometry.streams * geometry.heads * geometry.width);
  for (std::size_t index = 0; index < value.size(); ++index) value[index] = Make(index);
  for (std::size_t index = 0; index < incoming.size(); ++index) {
    incoming[index] = Make(index + 307U, 0.0078125F);
  }
  const nncp::Bf16Buffer source =
      nncp::AttentionProbabilityAdjoint(value, incoming, geometry);
  const nncp::Bf16Buffer stream_major =
      nncp::AttentionSourceToStreamMajor(source, geometry);
  for (std::size_t state = 0; state < geometry.states; ++state) {
    for (std::size_t head = 0; head < geometry.heads; ++head) {
      for (std::size_t stream = 0; stream < geometry.streams; ++stream) {
        for (std::size_t key = 0; key < geometry.keys; ++key) {
          float expected = 0.0F;
          for (std::size_t feature = 0; feature < geometry.width; ++feature) {
            const std::size_t value_index =
                (((stream * geometry.heads + head) * geometry.keys + key) *
                 geometry.width + feature);
            const std::size_t incoming_index =
                (((state * geometry.streams + stream) * geometry.heads + head) *
                 geometry.width + feature);
            expected = std::fma(
                nncp::Bf16ToFloat(incoming[incoming_index]),
                nncp::Bf16ToFloat(value[value_index]),
                expected);
          }
          const std::size_t source_index =
              (((state * geometry.heads + head) * geometry.streams + stream) *
               geometry.keys + key);
          const std::size_t stream_index =
              (((state * geometry.streams + stream) * geometry.heads + head) *
               geometry.keys + key);
          Require(
              source[source_index] == nncp::FloatToBf16(expected),
              "attention probability adjoint differs");
          Require(
              stream_major[stream_index] == source[source_index],
              "attention layout bridge differs");
        }
      }
    }
  }
}

void TestRmsNormSchedules() {
  constexpr std::size_t states = 2;
  constexpr std::size_t streams = 3;
  constexpr std::size_t width = 128;
  nncp::Bf16Buffer input(states * streams * width);
  nncp::Bf16Buffer incoming(states * streams * width);
  nncp::Bf16Buffer gain(width, nncp::FloatToBf16(1.0F));
  for (std::size_t index = 0; index < input.size(); ++index) {
    input[index] = Make(index + 401U, 0.03125F);
    incoming[index] = Make(index + 701U, 0.0078125F);
  }
  const nncp::RmsNormBackwardResult final_result = nncp::RmsNormBackward(
      input,
      incoming,
      gain,
      states,
      streams,
      width,
      nncp::RmsNormSchedule::kFinalRoot);
  const nncp::RmsNormBackwardResult state_result = nncp::RmsNormBackward(
      input,
      incoming,
      gain,
      states,
      streams,
      width,
      nncp::RmsNormSchedule::kSequentialStates);
  Require(final_result.input_adjoint.size() == input.size(), "final RMSNorm size differs");
  Require(state_result.input_adjoint.size() == input.size(), "state RMSNorm size differs");
  Require(
      state_result.bias_gradient ==
          nncp::StatewiseBiasGradient(incoming, states, streams, width),
      "state RMSNorm bias schedule differs");
  nncp::Bf16Buffer zeros(input.size(), 0);
  const nncp::RmsNormBackwardResult zero_result = nncp::RmsNormBackward(
      input,
      zeros,
      gain,
      states,
      streams,
      width,
      nncp::RmsNormSchedule::kSequentialStates);
  Require(
      zero_result.input_adjoint == zeros,
      "zero RMSNorm incoming produced an input adjoint");
  Require(
      zero_result.gain_gradient == nncp::Bf16Buffer(width, 0),
      "zero RMSNorm incoming produced a gain gradient");
}

}  // namespace

int main() {
  try {
    nncp::ValidateArithmeticEnvironment();
    TestTensorContainer();
    TestProfileFixtureLoader();
    TestGradientArtifacts();
    TestBf16();
    TestStatewiseBias();
    TestStatewiseWeight();
    TestFlatReductions();
    TestPanelledInputAdjoint();
    TestElementwiseBackward();
    TestLossAndSoftmax();
    TestAttentionReverseProducts();
    TestRelativeShiftBackward();
    TestRelativeProjectionAndKvMerge();
    TestTransformerLayerZeroAdjoint();
    TestProfileBackwardTopology();
    TestProfileForwardBackwardComposition();
    TestAttentionBridge();
    TestRmsNormSchedules();
    std::cout << "MIDPOINT_KERNEL_SELFTEST_OK\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
