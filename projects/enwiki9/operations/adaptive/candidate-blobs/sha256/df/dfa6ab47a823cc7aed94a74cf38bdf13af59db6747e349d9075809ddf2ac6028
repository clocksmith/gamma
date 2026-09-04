#include "profile_backward.hpp"
#include "profile_artifacts.hpp"
#include "profile_fixture.hpp"
#include "profile_forward.hpp"

#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace fs = std::filesystem;
namespace nncp = gamma_enwiki9::nncp;

namespace {

template <typename Value>
void WritePayload(const fs::path& path, const std::vector<Value>& values) {
  if (values.size() > std::numeric_limits<std::size_t>::max() / sizeof(Value)) {
    throw std::runtime_error("checkpoint byte count overflows");
  }
  const std::size_t bytes = values.size() * sizeof(Value);
  if (bytes > static_cast<std::size_t>(
                  std::numeric_limits<std::streamsize>::max())) {
    throw std::runtime_error("checkpoint exceeds stream size");
  }
  if (fs::exists(path)) {
    throw std::runtime_error("refusing to replace " + path.string());
  }
  const fs::path partial = path.string() + ".partial";
  if (fs::exists(partial)) {
    throw std::runtime_error("checkpoint partial already exists");
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
  fs::rename(partial, path);
}

void WriteText(const fs::path& path, const std::string& text) {
  if (fs::exists(path)) {
    throw std::runtime_error("refusing to replace " + path.string());
  }
  const fs::path partial = path.string() + ".partial";
  if (fs::exists(partial)) {
    throw std::runtime_error("text partial already exists");
  }
  std::ofstream output(partial, std::ios::binary | std::ios::trunc);
  output << text;
  output.flush();
  if (!output) throw std::runtime_error("cannot write " + partial.string());
  output.close();
  fs::rename(partial, path);
}

void ValidateClaimLabel(std::string_view value) {
  if (value.empty() || value.size() > 128) {
    throw std::runtime_error("claim label length is invalid");
  }
  for (const unsigned char byte : value) {
    const bool ascii_alphanumeric =
        (byte >= '0' && byte <= '9') ||
        (byte >= 'A' && byte <= 'Z') ||
        (byte >= 'a' && byte <= 'z');
    if (!(ascii_alphanumeric || byte == '.' || byte == '_' || byte == '-')) {
      throw std::runtime_error("claim label contains a forbidden byte");
    }
  }
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 6) {
      std::cerr << "usage: " << argv[0]
                << " PARAMETERS STATE midpoint-first|full-comparator OUTPUT_DIR"
                   " CLAIM_LABEL\n";
      return 2;
    }
    nncp::ValidateArithmeticEnvironment();
    const std::string mode = argv[3];
    nncp::FutureInputPolicy policy;
    std::size_t loss_length;
    if (mode == "midpoint-first") {
      policy = nncp::FutureInputPolicy::kZeroSecondHalf;
      loss_length = 32;
    } else if (mode == "full-comparator") {
      policy = nncp::FutureInputPolicy::kPreserve;
      loss_length = 64;
    } else {
      throw std::runtime_error("unknown treatment mode");
    }
    const std::string claim_label = argv[5];
    ValidateClaimLabel(claim_label);
    const nncp::ProfileGeometry geometry{
        .transformer = {64, 32, 8, 128, 256, 3072},
        .layers = 20,
        .vocabulary = 16392,
        .loss_start = 0,
        .loss_length = loss_length,
    };
    const fs::path output = argv[4];
    if (fs::exists(output) || !fs::create_directory(output)) {
      throw std::runtime_error("treatment output directory must not exist");
    }
    const nncp::ProfileFixtureInputs fixture = nncp::LoadProfileFixture(
        geometry, argv[1], argv[2], policy);
    const nncp::ProfileCache cache = nncp::ProfileForward(
        geometry,
        fixture.weights,
        fixture.input_symbols,
        fixture.targets,
        fixture.memory_inputs);
    nncp::ProfileBackwardResult backward =
        nncp::ProfileBackward(geometry, fixture.weights, cache);
    nncp::WriteCanonicalGradientArtifacts(
        output / "gradients", geometry, backward.gradients);
    const fs::path checkpoints = output / "checkpoints";
    if (!fs::create_directory(checkpoints)) {
      throw std::runtime_error("cannot create checkpoint directory");
    }
    WritePayload(checkpoints / "output_probabilities.f32", cache.probabilities);
    WritePayload(
        checkpoints / "top_attention_dp_source.bf16",
        backward.checkpoints.top_attention_probability_adjoint_source_order);
    WritePayload(
        checkpoints / "top_attention_dp_stream_major.bf16",
        backward.checkpoints.top_attention_probability_adjoint_stream_major);
    WritePayload(
        checkpoints / "embedding_input_adjoint.bf16",
        backward.checkpoints.embedding_input_adjoint);
    for (std::size_t layer = 0; layer < geometry.layers; ++layer) {
      WritePayload(
          checkpoints / ("train_h_" + std::to_string(layer) + ".bf16"),
          cache.layers[layer].attention_input);
    }
    std::ostringstream receipt;
    receipt << "schema=gamma.enwiki9.nncp-open-midpoint-treatment.v2\n"
            << "mode=" << mode << '\n'
            << "claim_label=" << claim_label << '\n'
            << "gradient_count=246\n"
            << "teacher_gradient_inputs=0\n"
            << "objective_credit_bytes=0\n";
    WriteText(output / "treatment.txt", receipt.str());
    WriteText(output / "complete.marker", "COMPLETE\n");
    std::cout << "MIDPOINT_PROFILE_TREATMENT_COMPLETE\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "profile treatment failed: " << error.what() << '\n';
    return 1;
  }
}
