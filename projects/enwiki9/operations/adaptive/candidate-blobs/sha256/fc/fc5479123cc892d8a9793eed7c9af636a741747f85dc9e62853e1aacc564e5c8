#include "midpoint_kernels.hpp"

#include <algorithm>
#include <bit>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>

namespace nncp = gamma_enwiki9::nncp;

namespace {

void Require(bool value, const char* message) {
  if (!value) throw std::runtime_error(message);
}

nncp::Bf16 Make(std::size_t index, float scale = 0.015625F) {
  const int centered = static_cast<int>((index * 37U + 11U) % 29U) - 14;
  return nncp::FloatToBf16(static_cast<float>(centered) * scale);
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
    TestBf16();
    TestStatewiseBias();
    TestStatewiseWeight();
    TestFlatReductions();
    TestPanelledInputAdjoint();
    TestElementwiseBackward();
    TestLossAndSoftmax();
    TestAttentionBridge();
    TestRmsNormSchedules();
    std::cout << "MIDPOINT_KERNEL_SELFTEST_OK\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
