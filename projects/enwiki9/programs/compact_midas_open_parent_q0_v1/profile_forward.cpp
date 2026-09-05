#include "profile_forward.hpp"

#include <algorithm>
#include <array>
#include <cmath>
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

std::size_t Product(
    std::initializer_list<std::size_t> factors,
    const char* label) {
  std::size_t result = 1;
  for (const std::size_t factor : factors) {
    if (factor == 0 || result > std::numeric_limits<std::size_t>::max() / factor) {
      throw std::invalid_argument(std::string(label) + " geometry is invalid");
    }
    result *= factor;
  }
  return result;
}

std::size_t Sum(std::size_t left, std::size_t right, const char* label) {
  if (left == 0 || right == 0 ||
      left > std::numeric_limits<std::size_t>::max() - right) {
    throw std::invalid_argument(std::string(label) + " geometry is invalid");
  }
  return left + right;
}

void Require(const Bf16Buffer& values, std::size_t expected, const char* label) {
  if (values.size() != expected) {
    throw std::invalid_argument(
        std::string(label) + " size differs: " + std::to_string(values.size()) +
        " != " + std::to_string(expected));
  }
}

void Require(const F32Buffer& values, std::size_t expected, const char* label) {
  if (values.size() != expected) {
    throw std::invalid_argument(
        std::string(label) + " size differs: " + std::to_string(values.size()) +
        " != " + std::to_string(expected));
  }
}

__m256 LoadBf16x8(const Bf16* source) {
  const __m128i words =
      _mm_loadu_si128(reinterpret_cast<const __m128i*>(source));
  return _mm256_castsi256_ps(
      _mm256_slli_epi32(_mm256_cvtepu16_epi32(words), 16));
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

float SumSquares64(const float* source) {
  __m256 x[8];
  for (std::size_t index = 0; index < 8; ++index) {
    x[index] = _mm256_loadu_ps(source + index * 8);
    x[index] = _mm256_mul_ps(x[index], x[index]);
  }
  const __m256 u01 = _mm256_unpacklo_ps(x[0], x[1]);
  const __m256 u23 = _mm256_unpacklo_ps(x[2], x[3]);
  const __m256 h01 = _mm256_unpackhi_ps(x[0], x[1]);
  const __m256 h23 = _mm256_unpackhi_ps(x[2], x[3]);
  const __m256 u45 = _mm256_unpacklo_ps(x[4], x[5]);
  const __m256 u67 = _mm256_unpacklo_ps(x[6], x[7]);
  const __m256 h45 = _mm256_unpackhi_ps(x[4], x[5]);
  const __m256 h67 = _mm256_unpackhi_ps(x[6], x[7]);
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

float SumSquares(const float* source, std::size_t width) {
  if (width == 0 || width % 64 != 0) {
    throw std::invalid_argument("forward RMSNorm width must be a multiple of 64");
  }
  std::array<float, 64> partials{};
  std::size_t blocks = 0;
  for (std::size_t index = 0; index < width; index += 64, ++blocks) {
    float block_sum = SumSquares64(source + index);
    std::size_t slot = 0;
    while ((blocks & (std::size_t{1} << slot)) != 0) {
      block_sum += partials[slot];
      partials[slot++] = 0.0F;
    }
    if (slot >= partials.size()) {
      throw std::invalid_argument("forward RMSNorm width is unsupported");
    }
    partials[slot] = block_sum;
  }
  float total = 0.0F;
  std::size_t slots = 0;
  for (std::size_t count = blocks; count != 0; count >>= 1U) ++slots;
  for (std::size_t slot = 0; slot < slots; ++slot) total += partials[slot];
  return total;
}

Bf16Buffer RmsNormForward(
    const Bf16Buffer& input,
    const Bf16Buffer& gain,
    const Bf16Buffer& bias,
    std::size_t samples,
    std::size_t width) {
  Require(input, Product({samples, width}, "forward RMSNorm input"),
          "forward RMSNorm input");
  Require(gain, width, "forward RMSNorm gain");
  Require(bias, width, "forward RMSNorm bias");
  Bf16Buffer output(input.size());
  std::vector<float> source(width);
  for (std::size_t sample = 0; sample < samples; ++sample) {
    for (std::size_t feature = 0; feature < width; ++feature) {
      source[feature] = Bf16ToFloat(input[sample * width + feature]);
    }
    const float inverse = 1.0F / std::sqrt(
        SumSquares(source.data(), width) / static_cast<float>(width) + 1.0e-5F);
    for (std::size_t feature = 0; feature < width; ++feature) {
      const float normalized = RoundToBf16(source[feature] * inverse);
      output[sample * width + feature] = FloatToBf16(
          normalized * Bf16ToFloat(gain[feature]) +
          Bf16ToFloat(bias[feature]));
    }
  }
  return output;
}

Bf16Buffer LinearForward(
    const Bf16Buffer& weights,
    const Bf16Buffer& input,
    const Bf16Buffer* bias,
    std::size_t samples,
    std::size_t inputs,
    std::size_t outputs) {
  if (outputs == 0 || outputs % kLanes != 0) {
    throw std::invalid_argument("forward linear outputs must be a multiple of eight");
  }
  Require(weights, Product({inputs, outputs}, "forward linear weights"),
          "forward linear weights");
  Require(input, Product({samples, inputs}, "forward linear input"),
          "forward linear input");
  if (bias != nullptr) Require(*bias, outputs, "forward linear bias");
  Bf16Buffer output(Product({samples, outputs}, "forward linear output"));
  for (std::size_t sample = 0; sample < samples; ++sample) {
    for (std::size_t destination = 0; destination < outputs;
         destination += kLanes) {
      __m256 accumulated = _mm256_setzero_ps();
      for (std::size_t panel = 0; panel < inputs; panel += kReductionPanel) {
        __m256 partial = _mm256_setzero_ps();
        const std::size_t end = std::min(inputs, panel + kReductionPanel);
        for (std::size_t source = panel; source < end; ++source) {
          partial = _mm256_fmadd_ps(
              _mm256_set1_ps(Bf16ToFloat(input[sample * inputs + source])),
              LoadBf16x8(weights.data() + source * outputs + destination),
              partial);
        }
        accumulated = _mm256_add_ps(accumulated, partial);
      }
      StoreBf16x8(
          output.data() + sample * outputs + destination,
          accumulated,
          "forward linear output");
    }
  }
  if (bias != nullptr) {
    for (std::size_t sample = 0; sample < samples; ++sample) {
      for (std::size_t destination = 0; destination < outputs; ++destination) {
        output[sample * outputs + destination] = FloatToBf16(
            Bf16ToFloat(output[sample * outputs + destination]) +
            Bf16ToFloat((*bias)[destination]));
      }
    }
  }
  return output;
}

float Gelu(float value) {
  constexpr float kCubic = 0.044715F;
  const float scale = std::sqrt(
      2.0F / static_cast<float>(3.14159265358979323846264338327950288));
  const float argument = scale * (value + kCubic * value * value * value);
  const float tanh_value = argument >= 8.0F ? 1.0F : std::tanh(argument);
  return 0.5F * value * (1.0F + tanh_value);
}

Bf16Buffer GegluForward(
    const Bf16Buffer& input,
    std::size_t samples,
    std::size_t inner) {
  Require(input, Product({samples, 2, inner}, "forward GEGLU input"),
          "forward GEGLU input");
  Bf16Buffer output(Product({samples, inner}, "forward GEGLU output"));
  for (std::size_t sample = 0; sample < samples; ++sample) {
    for (std::size_t feature = 0; feature < inner; ++feature) {
      const float gate = Bf16ToFloat(input[(sample * 2) * inner + feature]);
      const float value =
          Bf16ToFloat(input[(sample * 2 + 1) * inner + feature]);
      output[sample * inner + feature] =
          FloatToBf16(RoundToBf16(Gelu(gate)) * value);
    }
  }
  return output;
}

__m256 Exp8(__m256 value, __m256 maximum) {
  const __m256 upper = _mm256_set1_ps(87.0F);
  const __m256 lower = _mm256_set1_ps(-88.0F);
  const __m256 log2e = _mm256_set1_ps(1.4426950216293335F);
  const __m256 minus_ln2_high = _mm256_set1_ps(-0.693359375F);
  const __m256 ln2_low = _mm256_set1_ps(0.00021219444170128554F);
  __m256 reduced = _mm256_sub_ps(value, maximum);
  reduced = _mm256_min_ps(reduced, upper);
  reduced = _mm256_max_ps(reduced, lower);
  const __m256i exponent =
      _mm256_cvtps_epi32(_mm256_mul_ps(log2e, reduced));
  const __m256 exponent_float = _mm256_cvtepi32_ps(exponent);
  reduced = _mm256_fmadd_ps(minus_ln2_high, exponent_float, reduced);
  reduced = _mm256_fmadd_ps(ln2_low, exponent_float, reduced);
  __m256 polynomial = _mm256_set1_ps(0.00019841270113829523F);
  polynomial = _mm256_fmadd_ps(
      polynomial, reduced, _mm256_set1_ps(0.0013888889225199819F));
  polynomial = _mm256_fmadd_ps(
      polynomial, reduced, _mm256_set1_ps(0.008333333767950535F));
  polynomial = _mm256_fmadd_ps(
      polynomial, reduced, _mm256_set1_ps(0.0416666679084301F));
  polynomial = _mm256_fmadd_ps(
      polynomial, reduced, _mm256_set1_ps(0.1666666716337204F));
  polynomial =
      _mm256_fmadd_ps(polynomial, reduced, _mm256_set1_ps(0.5F));
  polynomial = _mm256_fmadd_ps(
      polynomial, _mm256_mul_ps(reduced, reduced), reduced);
  polynomial = _mm256_add_ps(polynomial, _mm256_set1_ps(1.0F));
  return _mm256_castsi256_ps(_mm256_add_epi32(
      _mm256_castps_si256(polynomial), _mm256_slli_epi32(exponent, 23)));
}

float Sum8(__m256 value) {
  value = _mm256_add_ps(value, _mm256_shuffle_ps(value, value, 0xb1));
  value = _mm256_add_ps(value, _mm256_shuffle_ps(value, value, 0x4e));
  value = _mm256_add_ps(
      value, _mm256_permute2f128_ps(value, value, 0x01));
  return _mm_cvtss_f32(_mm256_castps256_ps128(value));
}

float Sum64(const __m256 (&x)[8]) {
  const __m256 u23 = _mm256_unpacklo_ps(x[2], x[3]);
  const __m256 u67 = _mm256_unpacklo_ps(x[6], x[7]);
  const __m256 u01 = _mm256_unpacklo_ps(x[0], x[1]);
  const __m256 h23 = _mm256_unpackhi_ps(x[2], x[3]);
  const __m256 h01 = _mm256_unpackhi_ps(x[0], x[1]);
  const __m256 u45 = _mm256_unpacklo_ps(x[4], x[5]);
  const __m256 h45 = _mm256_unpackhi_ps(x[4], x[5]);
  const __m256 h67 = _mm256_unpackhi_ps(x[6], x[7]);
  const __m256 a = _mm256_shuffle_ps(u01, u23, 0x44);
  const __m256 b = _mm256_shuffle_ps(h01, h23, 0x44);
  const __m256 c = _mm256_shuffle_ps(u01, u23, 0xee);
  const __m256 d = _mm256_shuffle_ps(h01, h23, 0xee);
  const __m256 e = _mm256_shuffle_ps(u45, u67, 0x44);
  const __m256 f = _mm256_shuffle_ps(h45, h67, 0x44);
  const __m256 g = _mm256_shuffle_ps(h45, h67, 0xee);
  const __m256 h = _mm256_shuffle_ps(u45, u67, 0xee);
  __m256 left_low =
      _mm256_insertf128_ps(a, _mm256_castps256_ps128(e), 1);
  __m256 left_high =
      _mm256_insertf128_ps(c, _mm256_castps256_ps128(h), 1);
  __m256 right_low =
      _mm256_insertf128_ps(b, _mm256_castps256_ps128(f), 1);
  __m256 right_high =
      _mm256_insertf128_ps(d, _mm256_castps256_ps128(g), 1);
  const __m256 left_low_high = _mm256_permute2f128_ps(a, e, 0x31);
  left_high = _mm256_add_ps(left_high, left_low);
  const __m256 left_high_high = _mm256_permute2f128_ps(c, h, 0x31);
  const __m256 right_low_high = _mm256_permute2f128_ps(b, f, 0x31);
  const __m256 right_high_high = _mm256_permute2f128_ps(d, g, 0x31);
  const __m256 left_tail = _mm256_add_ps(left_low_high, left_high_high);
  right_high = _mm256_add_ps(right_high, right_low);
  const __m256 right_tail = _mm256_add_ps(right_low_high, right_high_high);
  right_high = _mm256_add_ps(left_high, right_high);
  __m256 total = _mm256_add_ps(left_tail, right_tail);
  total = _mm256_add_ps(right_high, total);
  total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0xb1));
  total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0x4e));
  total = _mm256_add_ps(
      total, _mm256_permute2f128_ps(total, total, 0x01));
  return _mm_cvtss_f32(_mm256_castps256_ps128(total));
}

F32Buffer SoftmaxForward(F32Buffer values, std::size_t row_width) {
  if (row_width == 0 || values.size() % row_width != 0) {
    throw std::invalid_argument("forward softmax geometry differs");
  }
  for (std::size_t base = 0; base < values.size(); base += row_width) {
    float maximum = -std::numeric_limits<float>::infinity();
    for (std::size_t index = 0; index < row_width; ++index) {
      maximum = std::max(maximum, values[base + index]);
    }
    if (!std::isfinite(maximum)) {
      throw std::invalid_argument("forward softmax row has no finite maximum");
    }
    const __m256 maximum8 = _mm256_set1_ps(maximum);
    std::array<float, 64> partials{};
    std::size_t blocks = 0;
    std::size_t index = 0;
    for (; index + 64 <= row_width; index += 64, ++blocks) {
      __m256 exponentials[8];
      for (std::size_t lane = 0; lane < 8; ++lane) {
        exponentials[lane] = Exp8(
            _mm256_loadu_ps(values.data() + base + index + lane * 8),
            maximum8);
        _mm256_storeu_ps(
            values.data() + base + index + lane * 8, exponentials[lane]);
      }
      float block_sum = Sum64(exponentials);
      std::size_t slot = 0;
      while ((blocks & (std::size_t{1} << slot)) != 0) {
        block_sum += partials[slot];
        partials[slot++] = 0.0F;
      }
      if (slot >= partials.size()) {
        throw std::invalid_argument("forward softmax width is unsupported");
      }
      partials[slot] = block_sum;
    }
    if (index < row_width) {
      if (row_width - index != 8) {
        throw std::invalid_argument("unsupported forward softmax tail");
      }
      const __m256 exponential = Exp8(
          _mm256_loadu_ps(values.data() + base + index), maximum8);
      _mm256_storeu_ps(values.data() + base + index, exponential);
      float block_sum = Sum8(exponential);
      std::size_t slot = 0;
      while ((blocks & (std::size_t{1} << slot)) != 0) {
        block_sum += partials[slot];
        partials[slot++] = 0.0F;
      }
      if (slot >= partials.size()) {
        throw std::invalid_argument("forward softmax tail is unsupported");
      }
      partials[slot] = block_sum;
      ++blocks;
    }
    float total = 0.0F;
    std::size_t slots = 0;
    for (std::size_t count = blocks; count != 0; count >>= 1U) ++slots;
    for (std::size_t slot = 0; slot < slots; ++slot) total += partials[slot];
    const float inverse = 1.0F / total;
    for (std::size_t column = 0; column < row_width; ++column) {
      values[base + column] *= inverse;
    }
  }
  return values;
}

Bf16Buffer SplitQuery(
    const Bf16Buffer& merged,
    std::size_t states,
    std::size_t streams,
    std::size_t heads,
    std::size_t width) {
  const std::size_t model = Product({heads, width}, "query model");
  Require(merged, Product({states, streams, model}, "merged query"),
          "merged query");
  return merged;
}

void SplitKeyValue(
    const Bf16Buffer& merged,
    std::size_t positions,
    std::size_t streams,
    std::size_t heads,
    std::size_t width,
    Bf16Buffer& key,
    Bf16Buffer& value) {
  const std::size_t model = Product({heads, width}, "K/V model");
  Require(merged, Product({positions, streams, 2, model}, "merged K/V"),
          "merged K/V");
  const std::size_t split = Product({streams, heads, positions, width}, "split K/V");
  key.assign(split, 0);
  value.assign(split, 0);
  for (std::size_t position = 0; position < positions; ++position) {
    for (std::size_t stream = 0; stream < streams; ++stream) {
      for (std::size_t head = 0; head < heads; ++head) {
        for (std::size_t feature = 0; feature < width; ++feature) {
          const std::size_t source =
              (position * streams + stream) * 2 * model + head * width + feature;
          const std::size_t destination =
              (((stream * heads + head) * positions + position) * width + feature);
          key[destination] = merged[source];
          value[destination] = merged[source + model];
        }
      }
    }
  }
}

Bf16Buffer DotKeyQuery(
    const Bf16Buffer& key,
    const Bf16Buffer& query,
    std::size_t states,
    std::size_t streams,
    std::size_t heads,
    std::size_t positions,
    std::size_t width) {
  if (positions % kLanes != 0) {
    throw std::invalid_argument("attention position count must be a multiple of eight");
  }
  Require(key, Product({streams, heads, positions, width}, "attention key"),
          "attention key");
  Require(query, Product({states, streams, heads, width}, "attention query"),
          "attention query");
  Bf16Buffer output(Product(
      {states, streams, heads, positions}, "content attention score"));
  alignas(32) std::array<float, kLanes> lanes{};
  for (std::size_t state = 0; state < states; ++state) {
    for (std::size_t stream = 0; stream < streams; ++stream) {
      for (std::size_t head = 0; head < heads; ++head) {
        for (std::size_t position = 0; position < positions;
             position += kLanes) {
          __m256 total = _mm256_setzero_ps();
          for (std::size_t feature = 0; feature < width; ++feature) {
            for (std::size_t lane = 0; lane < kLanes; ++lane) {
              const std::size_t source =
                  (((stream * heads + head) * positions + position + lane) *
                   width + feature);
              lanes[lane] = Bf16ToFloat(key[source]);
            }
            const std::size_t query_index =
                (((state * streams + stream) * heads + head) * width + feature);
            total = _mm256_fmadd_ps(
                _mm256_set1_ps(Bf16ToFloat(query[query_index])),
                _mm256_load_ps(lanes.data()),
                total);
          }
          const std::size_t destination =
              (((state * streams + stream) * heads + head) * positions + position);
          StoreBf16x8(output.data() + destination, total, "content attention score");
        }
      }
    }
  }
  return output;
}

Bf16Buffer DotRelativeQuery(
    const Bf16Buffer& relative_weight,
    const Bf16Buffer& query,
    std::size_t states,
    std::size_t streams,
    std::size_t heads,
    std::size_t positions,
    std::size_t width) {
  Require(relative_weight,
          Product({heads, positions, width}, "relative weight"),
          "relative weight");
  Bf16Buffer expanded(Product({streams, heads, positions, width}, "relative expanded"));
  for (std::size_t stream = 0; stream < streams; ++stream) {
    for (std::size_t head = 0; head < heads; ++head) {
      std::copy_n(
          relative_weight.begin() + head * positions * width,
          positions * width,
          expanded.begin() + (stream * heads + head) * positions * width);
    }
  }
  return DotKeyQuery(expanded, query, states, streams, heads, positions, width);
}

Bf16Buffer AttentionProbability(
    const Bf16Buffer& content,
    const Bf16Buffer& raw_relative,
    const Bf16Buffer& shared_bias,
    std::size_t states,
    std::size_t streams,
    std::size_t heads,
    std::size_t memory,
    std::size_t positions,
    std::size_t width,
    std::size_t model) {
  const std::size_t elements = Product(
      {states, streams, heads, positions}, "attention score elements");
  Require(content, elements, "content attention score");
  Require(raw_relative, elements, "relative attention score");
  Require(shared_bias, Product({heads, positions}, "shared relative bias"),
          "shared relative bias");
  const float bias_scale = RoundToBf16(std::sqrt(
      static_cast<float>(Product({width, model}, "relative bias scale"))));
  const float score_scale =
      RoundToBf16(1.0F / std::sqrt(static_cast<float>(width)));
  Bf16Buffer repeated_bias(Product({heads, positions}, "relative repeated bias"));
  for (std::size_t index = 0; index < repeated_bias.size(); ++index) {
    repeated_bias[index] = FloatToBf16(
        Bf16ToFloat(shared_bias[index]) * bias_scale);
  }
  F32Buffer scores(elements);
  const std::size_t padded_width = positions + 1;
  for (std::size_t state = 0; state < states; ++state) {
    for (std::size_t stream = 0; stream < streams; ++stream) {
      for (std::size_t head = 0; head < heads; ++head) {
        for (std::size_t position = 0; position < positions; ++position) {
          const std::size_t destination =
              (((state * streams + stream) * heads + head) * positions + position);
          const std::size_t flat = states + state * positions + position;
          const std::size_t raw_state = flat / padded_width;
          const std::size_t padded_position = flat % padded_width;
          float shifted = 0.0F;
          if (raw_state < states && padded_position != 0) {
            const std::size_t raw_position = padded_position - 1;
            const std::size_t raw_index =
                (((raw_state * streams + stream) * heads + head) * positions +
                 raw_position);
            shifted = RoundToBf16(
                Bf16ToFloat(raw_relative[raw_index]) +
                Bf16ToFloat(repeated_bias[head * positions + raw_position]));
          }
          float score = RoundToBf16(
              RoundToBf16(Bf16ToFloat(content[destination]) + shifted) *
              score_scale);
          if (position > memory + state) {
            score = -std::numeric_limits<float>::infinity();
          }
          scores[destination] = score;
        }
      }
    }
  }
  const F32Buffer probabilities = SoftmaxForward(std::move(scores), positions);
  Bf16Buffer output(probabilities.size());
  std::transform(
      probabilities.begin(), probabilities.end(), output.begin(), FloatToBf16);
  return output;
}

Bf16Buffer AttendValues(
    const Bf16Buffer& value,
    const Bf16Buffer& probability,
    std::size_t states,
    std::size_t streams,
    std::size_t heads,
    std::size_t positions,
    std::size_t width) {
  Require(value, Product({streams, heads, positions, width}, "attention value"),
          "attention value");
  Require(probability,
          Product({states, streams, heads, positions}, "attention probability"),
          "attention probability");
  Bf16Buffer output(Product(
      {states, streams, heads, width}, "attended output"));
  for (std::size_t state = 0; state < states; ++state) {
    for (std::size_t stream = 0; stream < streams; ++stream) {
      for (std::size_t head = 0; head < heads; ++head) {
        for (std::size_t feature = 0; feature < width; feature += kLanes) {
          __m256 accumulated = _mm256_setzero_ps();
          for (std::size_t panel = 0; panel < positions;
               panel += kReductionPanel) {
            __m256 partial = _mm256_setzero_ps();
            const std::size_t end = std::min(positions, panel + kReductionPanel);
            for (std::size_t position = panel; position < end; ++position) {
              const std::size_t probability_index =
                  (((state * streams + stream) * heads + head) * positions +
                   position);
              const std::size_t value_index =
                  (((stream * heads + head) * positions + position) * width +
                   feature);
              partial = _mm256_fmadd_ps(
                  _mm256_set1_ps(Bf16ToFloat(probability[probability_index])),
                  LoadBf16x8(value.data() + value_index),
                  partial);
            }
            accumulated = _mm256_add_ps(accumulated, partial);
          }
          const std::size_t destination =
              (((state * streams + stream) * heads + head) * width + feature);
          StoreBf16x8(
              output.data() + destination, accumulated, "attended output");
        }
      }
    }
  }
  return output;
}

Bf16Buffer JoinMemory(
    const Bf16Buffer& memory,
    const Bf16Buffer& current) {
  Bf16Buffer output;
  output.reserve(memory.size() + current.size());
  output.insert(output.end(), memory.begin(), memory.end());
  output.insert(output.end(), current.begin(), current.end());
  return output;
}

}  // namespace

ProfileCache ProfileForward(
    const ProfileGeometry& geometry,
    const ProfileWeights& weights,
    const std::vector<std::uint32_t>& input_symbols,
    const std::vector<std::uint32_t>& targets,
    const std::vector<Bf16Buffer>& memory_inputs) {
  const std::size_t states = geometry.transformer.states;
  const std::size_t streams = geometry.transformer.streams;
  const std::size_t heads = geometry.transformer.heads;
  const std::size_t head_width = geometry.transformer.head_width;
  const std::size_t memory = geometry.transformer.memory;
  const std::size_t inner = geometry.transformer.inner;
  const std::size_t model = Product({heads, head_width}, "forward model");
  const std::size_t samples = Product({states, streams}, "forward samples");
  const std::size_t positions = Sum(memory, states, "forward positions");
  if (geometry.layers == 0 || weights.layers.size() != geometry.layers ||
      memory_inputs.size() != geometry.layers) {
    throw std::invalid_argument("forward layer population differs");
  }
  if (input_symbols.size() != samples || targets.size() != samples) {
    throw std::invalid_argument("forward symbol population differs");
  }
  Require(weights.embedding, Product({geometry.vocabulary, model}, "embedding"),
          "embedding");
  Require(weights.shared_relative_bias,
          Product({heads, positions}, "shared relative bias"),
          "shared relative bias");
  Require(weights.final_ln_gain, model, "final layer-norm gain");
  Require(weights.final_ln_bias, model, "final layer-norm bias");
  Require(weights.output_weight,
          Product({model, geometry.vocabulary}, "output weight"),
          "output weight");
  Require(weights.output_bias, geometry.vocabulary, "output bias");

  const float embedding_scale =
      RoundToBf16(std::sqrt(static_cast<float>(model)));
  Bf16Buffer hidden(Product({samples, model}, "embedding output"));
  for (std::size_t sample = 0; sample < samples; ++sample) {
    const std::uint32_t symbol = input_symbols[sample];
    if (symbol >= geometry.vocabulary) {
      throw std::invalid_argument("forward input symbol is outside vocabulary");
    }
    for (std::size_t feature = 0; feature < model; ++feature) {
      const float source = weights.embedding[
          static_cast<std::size_t>(symbol) * model + feature];
      if (!std::isfinite(source)) {
        throw std::invalid_argument("embedding contains a non-finite value");
      }
      hidden[sample * model + feature] =
          FloatToBf16(RoundToBf16(source) * embedding_scale);
    }
  }

  std::vector<TransformerLayerCache> layer_caches;
  layer_caches.reserve(geometry.layers);
  for (std::size_t layer = 0; layer < geometry.layers; ++layer) {
    const TransformerLayerWeights& current_weights = weights.layers[layer];
    Require(current_weights.ln_g1, model, "layer ln_g1");
    Require(current_weights.ln_b1, model, "layer ln_b1");
    Require(current_weights.w_q, Product({model, model}, "layer w_q"),
            "layer w_q");
    Require(current_weights.w_kv, Product({model, 2, model}, "layer w_kv"),
            "layer w_kv");
    Require(current_weights.relative_weight,
            Product({heads, positions, head_width}, "layer w_r"),
            "layer w_r");
    Require(current_weights.w_o, Product({model, model}, "layer w_o"),
            "layer w_o");
    Require(current_weights.ln_g2, model, "layer ln_g2");
    Require(current_weights.ln_b2, model, "layer ln_b2");
    Require(current_weights.ff1, Product({model, 2, inner}, "layer ff1"),
            "layer ff1");
    Require(current_weights.ff_bias1, Product({2, inner}, "layer ff_bias1"),
            "layer ff_bias1");
    Require(current_weights.ff2, Product({inner, model}, "layer ff2"),
            "layer ff2");
    Require(current_weights.ff_bias2, model, "layer ff_bias2");
    Require(memory_inputs[layer],
            Product({memory, streams, model}, "layer memory"),
            "layer memory");

    TransformerLayerCache cache;
    cache.hidden_input = hidden;
    cache.attention_input = RmsNormForward(
        hidden,
        current_weights.ln_g1,
        current_weights.ln_b1,
        samples,
        model);
    const Bf16Buffer merged_query = LinearForward(
        current_weights.w_q,
        cache.attention_input,
        nullptr,
        samples,
        model,
        model);
    cache.query = SplitQuery(merged_query, states, streams, heads, head_width);
    cache.memory_attention_input = memory_inputs[layer];
    const Bf16Buffer all_attention_input = JoinMemory(
        cache.memory_attention_input, cache.attention_input);
    const Bf16Buffer merged_key_value = LinearForward(
        current_weights.w_kv,
        all_attention_input,
        nullptr,
        Product({positions, streams}, "K/V samples"),
        model,
        Product({2, model}, "K/V outputs"));
    SplitKeyValue(
        merged_key_value,
        positions,
        streams,
        heads,
        head_width,
        cache.key,
        cache.value);
    const Bf16Buffer content = DotKeyQuery(
        cache.key,
        cache.query,
        states,
        streams,
        heads,
        positions,
        head_width);
    const Bf16Buffer relative = DotRelativeQuery(
        current_weights.relative_weight,
        cache.query,
        states,
        streams,
        heads,
        positions,
        head_width);
    cache.attention_probability = AttentionProbability(
        content,
        relative,
        weights.shared_relative_bias,
        states,
        streams,
        heads,
        memory,
        positions,
        head_width,
        model);
    cache.merged_attention = AttendValues(
        cache.value,
        cache.attention_probability,
        states,
        streams,
        heads,
        positions,
        head_width);
    const Bf16Buffer attention_output = LinearForward(
        current_weights.w_o,
        cache.merged_attention,
        nullptr,
        samples,
        model,
        model);
    cache.attention_residual = AddBf16(hidden, attention_output);
    cache.feedforward_input = RmsNormForward(
        cache.attention_residual,
        current_weights.ln_g2,
        current_weights.ln_b2,
        samples,
        model);
    cache.ff1_output = LinearForward(
        current_weights.ff1,
        cache.feedforward_input,
        &current_weights.ff_bias1,
        samples,
        model,
        Product({2, inner}, "FF1 outputs"));
    cache.geglu = GegluForward(cache.ff1_output, samples, inner);
    const Bf16Buffer feedforward = LinearForward(
        current_weights.ff2,
        cache.geglu,
        &current_weights.ff_bias2,
        samples,
        inner,
        model);
    hidden = AddBf16(cache.attention_residual, feedforward);
    layer_caches.push_back(std::move(cache));
  }

  Bf16Buffer pre_final_hidden = hidden;
  Bf16Buffer final_hidden = RmsNormForward(
      pre_final_hidden,
      weights.final_ln_gain,
      weights.final_ln_bias,
      samples,
      model);
  const Bf16Buffer logits = LinearForward(
      weights.output_weight,
      final_hidden,
      &weights.output_bias,
      samples,
      model,
      geometry.vocabulary);
  F32Buffer logits_f32(logits.size());
  std::transform(logits.begin(), logits.end(), logits_f32.begin(), Bf16ToFloat);
  F32Buffer probabilities =
      SoftmaxForward(std::move(logits_f32), geometry.vocabulary);
  return {
      .pre_final_hidden = std::move(pre_final_hidden),
      .final_hidden = std::move(final_hidden),
      .layers = std::move(layer_caches),
      .probabilities = std::move(probabilities),
      .targets = targets,
      .input_symbols = input_symbols,
  };
}

}  // namespace gamma_enwiki9::nncp
