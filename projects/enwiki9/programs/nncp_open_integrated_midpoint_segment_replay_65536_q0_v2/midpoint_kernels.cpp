#include "midpoint_kernels.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cfenv>
#include <cmath>
#include <cstring>
#include <immintrin.h>
#include <initializer_list>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>

namespace gamma_enwiki9::nncp {
namespace {

constexpr std::size_t kLanes = 8;
constexpr std::size_t kReductionPanel = 128;

std::size_t CheckedProduct(
    std::initializer_list<std::size_t> factors,
    const char* label) {
  std::size_t result = 1;
  for (const std::size_t factor : factors) {
    if (factor == 0 || result > std::numeric_limits<std::size_t>::max() / factor) {
      throw std::invalid_argument(std::string(label) + " geometry overflows or is zero");
    }
    result *= factor;
  }
  return result;
}

void RequireSize(
    const Bf16Buffer& values,
    std::size_t expected,
    const char* label) {
  if (values.size() != expected) {
    throw std::invalid_argument(
        std::string(label) + " size differs: " + std::to_string(values.size()) +
        " != " + std::to_string(expected));
  }
}

__m256 LoadBf16x8(const Bf16* source) {
  const __m128i words =
      _mm_loadu_si128(reinterpret_cast<const __m128i*>(source));
  const __m256i expanded =
      _mm256_slli_epi32(_mm256_cvtepu16_epi32(words), 16);
  return _mm256_castsi256_ps(expanded);
}

void StoreBf16x8(Bf16* destination, __m256 values, const char* label) {
  alignas(32) std::array<float, kLanes> lanes{};
  _mm256_store_ps(lanes.data(), values);
  for (std::size_t lane = 0; lane < kLanes; ++lane) {
    if (!std::isfinite(lanes[lane])) {
      throw std::runtime_error(std::string("non-finite ") + label);
    }
    destination[lane] = FloatToBf16(lanes[lane]);
  }
}

std::size_t ValueIndex(
    const AttentionGeometry& g,
    std::size_t stream,
    std::size_t head,
    std::size_t key,
    std::size_t feature) {
  return (((stream * g.heads + head) * g.keys + key) * g.width + feature);
}

std::size_t IncomingIndex(
    const AttentionGeometry& g,
    std::size_t state,
    std::size_t stream,
    std::size_t head,
    std::size_t feature) {
  return (((state * g.streams + stream) * g.heads + head) * g.width + feature);
}

std::size_t SourceIndex(
    const AttentionGeometry& g,
    std::size_t state,
    std::size_t head,
    std::size_t stream,
    std::size_t key) {
  return (((state * g.heads + head) * g.streams + stream) * g.keys + key);
}

std::size_t StreamMajorIndex(
    const AttentionGeometry& g,
    std::size_t state,
    std::size_t stream,
    std::size_t head,
    std::size_t key) {
  return (((state * g.streams + stream) * g.heads + head) * g.keys + key);
}

float ReduceProducts64(const float* left, const float* right) {
  __m256 products[8];
  for (std::size_t index = 0; index < 8; ++index) {
    products[index] = _mm256_mul_ps(
        _mm256_loadu_ps(left + index * 8),
        _mm256_loadu_ps(right + index * 8));
  }
  const __m256 u01 = _mm256_unpacklo_ps(products[0], products[1]);
  const __m256 u23 = _mm256_unpacklo_ps(products[2], products[3]);
  const __m256 h01 = _mm256_unpackhi_ps(products[0], products[1]);
  const __m256 h23 = _mm256_unpackhi_ps(products[2], products[3]);
  const __m256 u45 = _mm256_unpacklo_ps(products[4], products[5]);
  const __m256 u67 = _mm256_unpacklo_ps(products[6], products[7]);
  const __m256 h45 = _mm256_unpackhi_ps(products[4], products[5]);
  const __m256 h67 = _mm256_unpackhi_ps(products[6], products[7]);
  const __m256 a = _mm256_shuffle_ps(u01, u23, 0xee);
  const __m256 b = _mm256_shuffle_ps(u45, u67, 0x44);
  const __m256 c = _mm256_shuffle_ps(u01, u23, 0x44);
  const __m256 d = _mm256_shuffle_ps(u45, u67, 0xee);
  const __m256 e = _mm256_shuffle_ps(h01, h23, 0x44);
  const __m256 f = _mm256_shuffle_ps(h45, h67, 0x44);
  const __m256 g = _mm256_shuffle_ps(h01, h23, 0xee);
  const __m256 h = _mm256_shuffle_ps(h45, h67, 0xee);
  const __m256 low_a =
      _mm256_insertf128_ps(a, _mm256_castps256_ps128(d), 1);
  const __m256 low_c =
      _mm256_insertf128_ps(c, _mm256_castps256_ps128(b), 1);
  const __m256 low_g =
      _mm256_insertf128_ps(g, _mm256_castps256_ps128(h), 1);
  const __m256 low_e =
      _mm256_insertf128_ps(e, _mm256_castps256_ps128(f), 1);
  const __m256 high_g = _mm256_permute2f128_ps(g, h, 0x31);
  const __m256 first = _mm256_add_ps(low_a, low_c);
  const __m256 second = _mm256_add_ps(low_g, low_e);
  const __m256 high_a = _mm256_permute2f128_ps(a, d, 0x31);
  const __m256 high_c = _mm256_permute2f128_ps(c, b, 0x31);
  const __m256 high_e = _mm256_permute2f128_ps(e, f, 0x31);
  const __m256 third = _mm256_add_ps(high_a, high_c);
  const __m256 fourth = _mm256_add_ps(high_g, high_e);
  __m256 total = _mm256_add_ps(third, fourth);
  total = _mm256_add_ps(_mm256_add_ps(first, second), total);
  total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0xb1));
  total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0x4e));
  total = _mm256_add_ps(
      total, _mm256_permute2f128_ps(total, total, 0x01));
  return _mm_cvtss_f32(_mm256_castps256_ps128(total));
}

float ReduceProducts(const float* left, const float* right, std::size_t width) {
  if (width == 0 || width % 64 != 0) {
    throw std::invalid_argument("RMSNorm reduction width must be a multiple of 64");
  }
  std::array<float, 64> partials{};
  std::size_t blocks = 0;
  for (std::size_t index = 0; index < width; index += 64, ++blocks) {
    float block_sum = ReduceProducts64(left + index, right + index);
    std::size_t slot = 0;
    while ((blocks & (std::size_t{1} << slot)) != 0) {
      block_sum += partials[slot];
      partials[slot++] = 0.0F;
    }
    if (slot >= partials.size()) {
      throw std::invalid_argument("RMSNorm reduction width is unsupported");
    }
    partials[slot] = block_sum;
  }
  float total = 0.0F;
  std::size_t slots = 0;
  for (std::size_t count = blocks; count != 0; count >>= 1U) ++slots;
  for (std::size_t slot = 0; slot < slots; ++slot) total += partials[slot];
  return total;
}

float ReduceStreamingProducts(
    const float* left,
    const float* right,
    std::size_t width) {
  if (width == 0 || width % kLanes != 0) {
    throw std::invalid_argument("streaming reduction width must be a multiple of eight");
  }
  __m256 total = _mm256_setzero_ps();
  for (std::size_t index = 0; index < width; index += kLanes) {
    total = _mm256_fmadd_ps(
        _mm256_loadu_ps(left + index),
        _mm256_loadu_ps(right + index),
        total);
  }
  total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0xb1));
  total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0x4e));
  total = _mm256_add_ps(
      total, _mm256_permute2f128_ps(total, total, 0x01));
  return _mm_cvtss_f32(_mm256_castps256_ps128(total));
}

}  // namespace

void ValidateArithmeticEnvironment() {
  if constexpr (std::endian::native != std::endian::little) {
    throw std::runtime_error("little-endian arithmetic host required");
  }
  if (std::fegetround() != FE_TONEAREST) {
    throw std::runtime_error("FE_TONEAREST arithmetic required");
  }
#if !defined(__AVX2__) || !defined(__FMA__)
  throw std::runtime_error("AVX2 and FMA compilation required");
#endif
  const unsigned int mxcsr = _mm_getcsr();
  constexpr unsigned int kFlushToZero = 1U << 15U;
  constexpr unsigned int kDenormalsAreZero = 1U << 6U;
  if ((mxcsr & (kFlushToZero | kDenormalsAreZero)) != 0) {
    throw std::runtime_error("FTZ and DAZ must be disabled");
  }
}

float Bf16ToFloat(Bf16 value) {
  const std::uint32_t bits = static_cast<std::uint32_t>(value) << 16U;
  return std::bit_cast<float>(bits);
}

Bf16 FloatToBf16(float value) {
  const std::uint32_t bits = std::bit_cast<std::uint32_t>(value);
  if ((bits & UINT32_C(0x7f800000)) == UINT32_C(0x7f800000) &&
      (bits & UINT32_C(0x007fffff)) != 0) {
    return static_cast<Bf16>((bits >> 16U) | UINT32_C(0x0040));
  }
  const std::uint32_t rounding = UINT32_C(0x00007fff) + ((bits >> 16U) & 1U);
  return static_cast<Bf16>((bits + rounding) >> 16U);
}

float RoundToBf16(float value) {
  return Bf16ToFloat(FloatToBf16(value));
}

Bf16Buffer StatewiseBiasGradient(
    const Bf16Buffer& residuals,
    std::size_t states,
    std::size_t streams,
    std::size_t features) {
  RequireSize(
      residuals,
      CheckedProduct({states, streams, features}, "bias residual"),
      "bias residual");
  Bf16Buffer result(features, 0);
  for (std::size_t state = 0; state < states; ++state) {
    for (std::size_t feature = 0; feature < features; ++feature) {
      float total = Bf16ToFloat(result[feature]);
      for (std::size_t stream = 0; stream < streams; ++stream) {
        const std::size_t index =
            (state * streams + stream) * features + feature;
        total += Bf16ToFloat(residuals[index]);
      }
      if (!std::isfinite(total)) {
        throw std::runtime_error("non-finite statewise bias gradient");
      }
      result[feature] = FloatToBf16(total);
    }
  }
  return result;
}

Bf16Buffer FlatBiasGradient(
    const Bf16Buffer& residuals,
    std::size_t samples,
    std::size_t features) {
  RequireSize(
      residuals,
      CheckedProduct({samples, features}, "flat bias residual"),
      "flat bias residual");
  Bf16Buffer result(features);
  for (std::size_t feature = 0; feature < features; ++feature) {
    float total = 0.0F;
    for (std::size_t sample = 0; sample < samples; ++sample) {
      total += Bf16ToFloat(residuals[sample * features + feature]);
    }
    if (!std::isfinite(total)) {
      throw std::runtime_error("non-finite flat bias gradient");
    }
    result[feature] = FloatToBf16(total);
  }
  return result;
}

Bf16Buffer StatewiseWeightGradient(
    const Bf16Buffer& inputs,
    const Bf16Buffer& residuals,
    std::size_t states,
    std::size_t streams,
    std::size_t inputs_count,
    std::size_t outputs_count) {
  if (outputs_count == 0 || outputs_count % kLanes != 0) {
    throw std::invalid_argument("weight-gradient outputs must be a multiple of eight");
  }
  RequireSize(
      inputs,
      CheckedProduct({states, streams, inputs_count}, "weight input"),
      "weight input");
  RequireSize(
      residuals,
      CheckedProduct({states, streams, outputs_count}, "weight residual"),
      "weight residual");
  Bf16Buffer result(
      CheckedProduct({inputs_count, outputs_count}, "weight gradient"), 0);
  for (std::size_t state = 0; state < states; ++state) {
    for (std::size_t input = 0; input < inputs_count; ++input) {
      for (std::size_t output = 0; output < outputs_count; output += kLanes) {
        Bf16* prior_words = result.data() + input * outputs_count + output;
        const __m256 prior = LoadBf16x8(prior_words);
        __m256 dot = _mm256_setzero_ps();
        for (std::size_t stream = 0; stream < streams; ++stream) {
          const std::size_t sample = state * streams + stream;
          const float activation =
              Bf16ToFloat(inputs[sample * inputs_count + input]);
          const __m256 residual =
              LoadBf16x8(residuals.data() + sample * outputs_count + output);
          dot = _mm256_fmadd_ps(_mm256_set1_ps(activation), residual, dot);
        }
        StoreBf16x8(
            prior_words, _mm256_add_ps(dot, prior), "statewise weight gradient");
      }
    }
  }
  return result;
}

Bf16Buffer Flat128WeightGradient(
    const Bf16Buffer& inputs,
    const Bf16Buffer& residuals,
    std::size_t samples,
    std::size_t inputs_count,
    std::size_t outputs_count) {
  if (outputs_count == 0 || outputs_count % kLanes != 0) {
    throw std::invalid_argument("flat weight-gradient outputs must be a multiple of eight");
  }
  RequireSize(
      inputs,
      CheckedProduct({samples, inputs_count}, "flat weight input"),
      "flat weight input");
  RequireSize(
      residuals,
      CheckedProduct({samples, outputs_count}, "flat weight residual"),
      "flat weight residual");
  Bf16Buffer result(
      CheckedProduct({inputs_count, outputs_count}, "flat weight gradient"));
  for (std::size_t input = 0; input < inputs_count; ++input) {
    for (std::size_t output = 0; output < outputs_count; output += kLanes) {
      __m256 accumulated = _mm256_setzero_ps();
      for (std::size_t panel = 0; panel < samples; panel += kReductionPanel) {
        __m256 partial = _mm256_setzero_ps();
        const std::size_t end = std::min(samples, panel + kReductionPanel);
        for (std::size_t sample = panel; sample < end; ++sample) {
          const float activation = Bf16ToFloat(inputs[sample * inputs_count + input]);
          const __m256 residual =
              LoadBf16x8(residuals.data() + sample * outputs_count + output);
          partial = _mm256_fmadd_ps(_mm256_set1_ps(activation), residual, partial);
        }
        accumulated = _mm256_add_ps(accumulated, partial);
      }
      StoreBf16x8(
          result.data() + input * outputs_count + output,
          accumulated,
          "flat weight gradient");
    }
  }
  return result;
}

Bf16Buffer Panel128InputAdjoint(
    const Bf16Buffer& weights,
    const Bf16Buffer& incoming,
    std::size_t samples,
    std::size_t reduction,
    std::size_t destination) {
  if (reduction == 0) {
    throw std::invalid_argument("input-adjoint reduction must be nonzero");
  }
  if (destination == 0 || destination % kLanes != 0) {
    throw std::invalid_argument("input-adjoint destination must be a multiple of eight");
  }
  RequireSize(
      weights,
      CheckedProduct({destination, reduction}, "input-adjoint weights"),
      "input-adjoint weights");
  RequireSize(
      incoming,
      CheckedProduct({samples, reduction}, "input-adjoint incoming"),
      "input-adjoint incoming");

  Bf16Buffer packed(weights.size());
  for (std::size_t reduce = 0; reduce < reduction; ++reduce) {
    for (std::size_t feature = 0; feature < destination; ++feature) {
      packed[reduce * destination + feature] =
          weights[feature * reduction + reduce];
    }
  }

  Bf16Buffer result(
      CheckedProduct({samples, destination}, "input-adjoint result"));
  for (std::size_t sample = 0; sample < samples; ++sample) {
    for (std::size_t feature = 0; feature < destination; feature += kLanes) {
      __m256 total = _mm256_setzero_ps();
      for (std::size_t panel = 0; panel < reduction; panel += kReductionPanel) {
        __m256 partial = _mm256_setzero_ps();
        const std::size_t end = std::min(reduction, panel + kReductionPanel);
        for (std::size_t reduce = panel; reduce < end; ++reduce) {
          const float gradient =
              Bf16ToFloat(incoming[sample * reduction + reduce]);
          const __m256 weight =
              LoadBf16x8(packed.data() + reduce * destination + feature);
          partial = _mm256_fmadd_ps(_mm256_set1_ps(gradient), weight, partial);
        }
        total = _mm256_add_ps(total, partial);
      }
      StoreBf16x8(
          result.data() + sample * destination + feature,
          total,
          "panelled input adjoint");
    }
  }
  return result;
}

GegluBackwardResult GegluBackward(
    const Bf16Buffer& ff1_output,
    const Bf16Buffer& incoming,
    std::size_t samples,
    std::size_t inner) {
  const std::size_t ff1_width = CheckedProduct({2, inner}, "GEGLU width");
  RequireSize(
      ff1_output,
      CheckedProduct({samples, ff1_width}, "GEGLU input"),
      "GEGLU input");
  RequireSize(
      incoming,
      CheckedProduct({samples, inner}, "GEGLU incoming"),
      "GEGLU incoming");
  Bf16Buffer ff2_input(incoming.size());
  Bf16Buffer ff1_adjoint(ff1_output.size());
  constexpr float kGeluCubic = 0.044715F;
  constexpr float kGeluScale = 0.7978845608028654F;
  const auto gelu = [](float value) {
    const float argument = kGeluScale *
        (value + kGeluCubic * value * value * value);
    const float tanh_value = argument >= 8.0F ? 1.0F : std::tanh(argument);
    return 0.5F * value * (1.0F + tanh_value);
  };
  const auto gelu_derivative = [](float value) {
    const float square = value * value;
    const float argument =
        kGeluScale * (value + kGeluCubic * value * square);
    const float tanh_value = argument >= 8.0F ? 1.0F : std::tanh(argument);
    const float argument_derivative =
        kGeluScale * (1.0F + 3.0F * kGeluCubic * square);
    return 0.5F * (1.0F + tanh_value) +
        0.5F * value * (1.0F - tanh_value * tanh_value) *
            argument_derivative;
  };
  for (std::size_t sample = 0; sample < samples; ++sample) {
    for (std::size_t feature = 0; feature < inner; ++feature) {
      const float upstream = Bf16ToFloat(incoming[sample * inner + feature]);
      ff2_input[sample * inner + feature] = FloatToBf16(upstream);
      const float gate =
          Bf16ToFloat(ff1_output[sample * ff1_width + feature]);
      const float value =
          Bf16ToFloat(ff1_output[sample * ff1_width + inner + feature]);
      const float gate_upstream = RoundToBf16(upstream * value);
      ff1_adjoint[sample * ff1_width + feature] =
          FloatToBf16(gate_upstream * gelu_derivative(gate));
      ff1_adjoint[sample * ff1_width + inner + feature] =
          FloatToBf16(upstream * RoundToBf16(gelu(gate)));
    }
  }
  return {std::move(ff2_input), std::move(ff1_adjoint)};
}

Bf16Buffer AddBf16(
    const Bf16Buffer& left,
    const Bf16Buffer& right) {
  if (left.size() != right.size()) {
    throw std::invalid_argument("BF16 add geometry differs");
  }
  Bf16Buffer result(left.size());
  for (std::size_t index = 0; index < left.size(); ++index) {
    const float value = Bf16ToFloat(left[index]) + Bf16ToFloat(right[index]);
    if (!std::isfinite(value)) {
      throw std::runtime_error("non-finite BF16 add result");
    }
    result[index] = FloatToBf16(value);
  }
  return result;
}

Bf16Buffer CrossEntropyLogitResidual(
    const std::vector<float>& probabilities,
    const std::vector<std::uint32_t>& targets,
    std::size_t states,
    std::size_t streams,
    std::size_t vocabulary,
    std::size_t loss_start,
    std::size_t loss_length) {
  if (loss_length == 0 || loss_start > states || loss_length > states - loss_start) {
    throw std::invalid_argument("cross-entropy loss window is invalid");
  }
  const std::size_t samples = CheckedProduct({states, streams}, "loss samples");
  if (probabilities.size() != CheckedProduct({samples, vocabulary}, "probabilities")) {
    throw std::invalid_argument("probability size differs");
  }
  if (targets.size() != samples) {
    throw std::invalid_argument("target size differs");
  }
  const float scale =
      1.0F / static_cast<float>(CheckedProduct({loss_length, streams}, "loss scale"));
  Bf16Buffer result(probabilities.size(), 0);
  for (std::size_t state = loss_start; state < loss_start + loss_length; ++state) {
    for (std::size_t stream = 0; stream < streams; ++stream) {
      const std::size_t sample = state * streams + stream;
      const std::uint32_t target = targets[sample];
      if (target >= vocabulary) {
        throw std::invalid_argument("cross-entropy target is outside vocabulary");
      }
      for (std::size_t symbol = 0; symbol < vocabulary; ++symbol) {
        const std::size_t index = sample * vocabulary + symbol;
        const float probability = probabilities[index];
        if (!std::isfinite(probability) || probability < 0.0F) {
          throw std::invalid_argument("cross-entropy probability is invalid");
        }
        float value = probability * scale;
        if (symbol == target) value -= scale;
        result[index] = FloatToBf16(value);
      }
    }
  }
  return result;
}

Bf16Buffer SoftmaxBackward(
    const Bf16Buffer& probability,
    const Bf16Buffer& incoming,
    std::size_t rows,
    std::size_t keys) {
  const std::size_t elements = CheckedProduct({rows, keys}, "softmax backward");
  RequireSize(probability, elements, "softmax probability");
  RequireSize(incoming, elements, "softmax incoming");
  Bf16Buffer output(elements);
  for (std::size_t row = 0; row < rows; ++row) {
    const std::size_t base = row * keys;
    volatile float dot = 0.0F;
    for (std::size_t key = 0; key < keys; ++key) {
      const float p = Bf16ToFloat(probability[base + key]);
      const float dp = Bf16ToFloat(incoming[base + key]);
      if (!std::isfinite(p) || !std::isfinite(dp)) {
        throw std::invalid_argument("softmax backward input is non-finite");
      }
      volatile float product = p * dp;
      dot = dot + product;
    }
    if (!std::isfinite(dot)) {
      throw std::runtime_error("softmax backward reduction is non-finite");
    }
    for (std::size_t key = 0; key < keys; ++key) {
      const float p = Bf16ToFloat(probability[base + key]);
      const float dp = Bf16ToFloat(incoming[base + key]);
      volatile float centered = dp - dot;
      volatile float value = p * centered;
      if (!std::isfinite(value)) {
        throw std::runtime_error("softmax backward output is non-finite");
      }
      output[base + key] = FloatToBf16(value);
    }
  }
  return output;
}

RmsNormBackwardResult RmsNormBackward(
    const Bf16Buffer& input,
    const Bf16Buffer& incoming,
    const Bf16Buffer& gain,
    std::size_t states,
    std::size_t streams,
    std::size_t width,
    RmsNormSchedule schedule,
    float epsilon) {
  if (!(epsilon > 0.0F) || !std::isfinite(epsilon)) {
    throw std::invalid_argument("RMSNorm epsilon must be positive and finite");
  }
  const std::size_t samples = CheckedProduct({states, streams}, "RMSNorm samples");
  const std::size_t elements = CheckedProduct({samples, width}, "RMSNorm elements");
  RequireSize(input, elements, "RMSNorm input");
  RequireSize(incoming, elements, "RMSNorm incoming");
  RequireSize(gain, width, "RMSNorm gain");
  if (width % 64 != 0) {
    throw std::invalid_argument("RMSNorm width must be a multiple of 64");
  }

  Bf16Buffer normalized(elements);
  Bf16Buffer input_adjoint(elements);
  std::vector<float> source(width);
  std::vector<float> gradient(width);
  std::vector<float> gain_values(width);
  std::vector<float> unit(width);
  std::vector<float> upstream(width);
  std::vector<float> ones(width, 1.0F);
  for (std::size_t feature = 0; feature < width; ++feature) {
    gain_values[feature] = Bf16ToFloat(gain[feature]);
  }
  for (std::size_t sample = 0; sample < samples; ++sample) {
    for (std::size_t feature = 0; feature < width; ++feature) {
      source[feature] = Bf16ToFloat(input[sample * width + feature]);
      gradient[feature] = Bf16ToFloat(incoming[sample * width + feature]);
    }
    const float sum_squares = ReduceProducts(source.data(), source.data(), width);
    const float inverse =
        1.0F / std::sqrt(sum_squares / static_cast<float>(width) + epsilon);
    for (std::size_t feature = 0; feature < width; ++feature) {
      unit[feature] = RoundToBf16(source[feature] * inverse);
      normalized[sample * width + feature] = FloatToBf16(unit[feature]);
      upstream[feature] =
          RoundToBf16(gradient[feature] * gain_values[feature]);
    }
    const float upstream_sum =
        ReduceProducts(upstream.data(), ones.data(), width);
    const float product_sum =
        ReduceStreamingProducts(upstream.data(), unit.data(), width);
    for (std::size_t feature = 0; feature < width; feature += kLanes) {
      const __m256 current = _mm256_loadu_ps(upstream.data() + feature);
      const __m256 norm = _mm256_loadu_ps(unit.data() + feature);
      __m256 values;
      if (schedule == RmsNormSchedule::kFinalRoot) {
        const __m256 mean_centered = _mm256_sub_ps(
            current,
            _mm256_set1_ps(upstream_sum / static_cast<float>(width)));
        const __m256 centered = _mm256_fnmadd_ps(
            norm,
            _mm256_set1_ps(product_sum / static_cast<float>(width)),
            mean_centered);
        values = _mm256_mul_ps(_mm256_set1_ps(inverse), centered);
      } else {
        __m256 centered = _mm256_fmsub_ps(
            current,
            _mm256_set1_ps(static_cast<float>(width)),
            _mm256_set1_ps(upstream_sum));
        centered = _mm256_fnmadd_ps(
            norm, _mm256_set1_ps(product_sum), centered);
        values = _mm256_mul_ps(
            _mm256_set1_ps(inverse / static_cast<float>(width)), centered);
      }
      StoreBf16x8(
          input_adjoint.data() + sample * width + feature,
          values,
          "RMSNorm input adjoint");
    }
  }

  Bf16Buffer gain_terms(elements);
  for (std::size_t index = 0; index < elements; ++index) {
    gain_terms[index] = FloatToBf16(
        Bf16ToFloat(incoming[index]) * Bf16ToFloat(normalized[index]));
  }
  Bf16Buffer gain_gradient(width);
  Bf16Buffer bias_gradient(width);
  if (schedule == RmsNormSchedule::kSequentialStates) {
    gain_gradient = StatewiseBiasGradient(gain_terms, states, streams, width);
    bias_gradient = StatewiseBiasGradient(incoming, states, streams, width);
  } else {
    for (std::size_t feature = 0; feature < width; ++feature) {
      float gain_accumulated = 0.0F;
      float bias_accumulated = 0.0F;
      for (std::size_t chunk = 0; chunk < samples; chunk += kReductionPanel) {
        const std::size_t end = std::min(samples, chunk + kReductionPanel);
        float gain_partial = 0.0F;
        for (std::size_t sample = chunk; sample < end; ++sample) {
          gain_partial += Bf16ToFloat(gain_terms[sample * width + feature]);
        }
        gain_accumulated += gain_partial;
      }
      for (std::size_t sample = 0; sample < samples; ++sample) {
        bias_accumulated += Bf16ToFloat(incoming[sample * width + feature]);
      }
      gain_gradient[feature] = FloatToBf16(gain_accumulated);
      bias_gradient[feature] = FloatToBf16(bias_accumulated);
    }
  }
  return {std::move(gain_gradient), std::move(bias_gradient), std::move(input_adjoint)};
}

Bf16Buffer AttentionProbabilityAdjoint(
    const Bf16Buffer& value,
    const Bf16Buffer& incoming,
    const AttentionGeometry& geometry) {
  if (geometry.keys == 0 || geometry.keys % kLanes != 0) {
    throw std::invalid_argument("attention key count must be a multiple of eight");
  }
  RequireSize(
      value,
      CheckedProduct(
          {geometry.streams, geometry.heads, geometry.keys, geometry.width},
          "attention value"),
      "attention value");
  RequireSize(
      incoming,
      CheckedProduct(
          {geometry.states, geometry.streams, geometry.heads, geometry.width},
          "attention incoming"),
      "attention incoming");
  Bf16Buffer output(CheckedProduct(
      {geometry.states, geometry.heads, geometry.streams, geometry.keys},
      "attention probability adjoint"));
  alignas(32) std::array<float, kLanes> lanes{};
  for (std::size_t state = 0; state < geometry.states; ++state) {
    for (std::size_t head = 0; head < geometry.heads; ++head) {
      for (std::size_t stream = 0; stream < geometry.streams; ++stream) {
        for (std::size_t key = 0; key < geometry.keys; key += kLanes) {
          __m256 accumulator = _mm256_setzero_ps();
          for (std::size_t feature = 0; feature < geometry.width; ++feature) {
            const float gradient = Bf16ToFloat(
                incoming[IncomingIndex(geometry, state, stream, head, feature)]);
            const __m256 values = _mm256_set_ps(
                Bf16ToFloat(value[ValueIndex(geometry, stream, head, key + 7, feature)]),
                Bf16ToFloat(value[ValueIndex(geometry, stream, head, key + 6, feature)]),
                Bf16ToFloat(value[ValueIndex(geometry, stream, head, key + 5, feature)]),
                Bf16ToFloat(value[ValueIndex(geometry, stream, head, key + 4, feature)]),
                Bf16ToFloat(value[ValueIndex(geometry, stream, head, key + 3, feature)]),
                Bf16ToFloat(value[ValueIndex(geometry, stream, head, key + 2, feature)]),
                Bf16ToFloat(value[ValueIndex(geometry, stream, head, key + 1, feature)]),
                Bf16ToFloat(value[ValueIndex(geometry, stream, head, key + 0, feature)]));
            accumulator =
                _mm256_fmadd_ps(_mm256_set1_ps(gradient), values, accumulator);
          }
          _mm256_store_ps(lanes.data(), accumulator);
          for (std::size_t lane = 0; lane < kLanes; ++lane) {
            if (!std::isfinite(lanes[lane])) {
              throw std::runtime_error("non-finite attention probability adjoint");
            }
            output[SourceIndex(geometry, state, head, stream, key + lane)] =
                FloatToBf16(lanes[lane]);
          }
        }
      }
    }
  }
  return output;
}

Bf16Buffer AttentionSourceToStreamMajor(
    const Bf16Buffer& source_order,
    const AttentionGeometry& geometry) {
  const std::size_t count = CheckedProduct(
      {geometry.states, geometry.heads, geometry.streams, geometry.keys},
      "attention layout bridge");
  RequireSize(source_order, count, "attention layout bridge source");
  Bf16Buffer output(count);
  for (std::size_t state = 0; state < geometry.states; ++state) {
    for (std::size_t head = 0; head < geometry.heads; ++head) {
      for (std::size_t stream = 0; stream < geometry.streams; ++stream) {
        for (std::size_t key = 0; key < geometry.keys; ++key) {
          output[StreamMajorIndex(geometry, state, stream, head, key)] =
              source_order[SourceIndex(geometry, state, head, stream, key)];
        }
      }
    }
  }
  return output;
}

}  // namespace gamma_enwiki9::nncp
