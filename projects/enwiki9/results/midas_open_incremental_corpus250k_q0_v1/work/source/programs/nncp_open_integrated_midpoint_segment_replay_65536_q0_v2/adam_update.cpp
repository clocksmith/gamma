#include "adam_update.hpp"

#include "profile_artifacts.hpp"
#include "tensor_container.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <immintrin.h>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace gamma_enwiki9::nncp {
namespace {

constexpr float kBeta2 = 0.9999F;
constexpr float kEpsilon = 1.0e-8F;
constexpr float kGradientClip = 0.05F;
constexpr std::uint32_t kBf16Bias = UINT32_C(0x8000);
constexpr char kOptimizerConfiguration[] =
    "gamma.nncp.production.update.optimizer.v1";

bool SameDescriptor(
    const GradientDescriptor& left,
    const GradientDescriptor& right) {
  return left.name == right.name && left.element_type == right.element_type &&
      left.dimensions == right.dimensions;
}

__m256 LoadBf16(const std::uint16_t* source) {
  const __m128i packed =
      _mm_loadu_si128(reinterpret_cast<const __m128i*>(source));
  return _mm256_castsi256_ps(
      _mm256_slli_epi32(_mm256_cvtepu16_epi32(packed), 16));
}

float LibncSum64(const __m256 (&values)[8]) {
  const __m256 u23 = _mm256_unpacklo_ps(values[2], values[3]);
  const __m256 u67 = _mm256_unpacklo_ps(values[6], values[7]);
  const __m256 u01 = _mm256_unpacklo_ps(values[0], values[1]);
  const __m256 h23 = _mm256_unpackhi_ps(values[2], values[3]);
  const __m256 h01 = _mm256_unpackhi_ps(values[0], values[1]);
  const __m256 u45 = _mm256_unpacklo_ps(values[4], values[5]);
  const __m256 h45 = _mm256_unpackhi_ps(values[4], values[5]);
  const __m256 h67 = _mm256_unpackhi_ps(values[6], values[7]);
  const __m256 a = _mm256_shuffle_ps(u01, u23, 0x44);
  const __m256 b = _mm256_shuffle_ps(h01, h23, 0x44);
  const __m256 c = _mm256_shuffle_ps(u01, u23, 0xee);
  const __m256 d = _mm256_shuffle_ps(h01, h23, 0xee);
  const __m256 e = _mm256_shuffle_ps(u45, u67, 0x44);
  const __m256 f = _mm256_shuffle_ps(h45, h67, 0x44);
  const __m256 g = _mm256_shuffle_ps(u45, u67, 0xee);
  const __m256 h = _mm256_shuffle_ps(h45, h67, 0xee);
  const __m256 left_low =
      _mm256_insertf128_ps(a, _mm256_castps256_ps128(e), 1);
  __m256 left_high =
      _mm256_insertf128_ps(c, _mm256_castps256_ps128(g), 1);
  const __m256 right_low =
      _mm256_insertf128_ps(b, _mm256_castps256_ps128(f), 1);
  __m256 right_high =
      _mm256_insertf128_ps(d, _mm256_castps256_ps128(h), 1);
  const __m256 left_low_high = _mm256_permute2f128_ps(a, e, 0x31);
  left_high = _mm256_add_ps(left_high, left_low);
  const __m256 left_high_high = _mm256_permute2f128_ps(c, g, 0x31);
  const __m256 right_low_high = _mm256_permute2f128_ps(b, f, 0x31);
  const __m256 right_high_high = _mm256_permute2f128_ps(d, h, 0x31);
  const __m256 left_tail = _mm256_add_ps(left_low_high, left_high_high);
  right_high = _mm256_add_ps(right_high, right_low);
  const __m256 right_tail = _mm256_add_ps(right_low_high, right_high_high);
  right_high = _mm256_add_ps(left_high, right_high);
  __m256 total = _mm256_add_ps(left_tail, right_tail);
  total = _mm256_add_ps(right_high, total);
  total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0xb1));
  total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0x4e));
  total =
      _mm256_add_ps(total, _mm256_permute2f128_ps(total, total, 0x01));
  return _mm_cvtss_f32(_mm256_castps256_ps128(total));
}

template <typename Load>
float GradientNorm(std::size_t count, Load load) {
  if (count == 0 || count % 8 != 0) {
    throw std::invalid_argument(
        "Adam gradient population must be a nonzero multiple of eight");
  }
  std::array<float, 64> tail{};
  std::array<float, 8 * sizeof(std::size_t)> partials{};
  std::size_t blocks = 0;
  std::size_t index = 0;
  while (index < count) {
    const std::size_t available = std::min<std::size_t>(64, count - index);
    __m256 squares[8]{};
    if (available == 64) {
      for (std::size_t lane = 0; lane < 8; ++lane) {
        const __m256 value = load(index + lane * 8);
        squares[lane] = _mm256_mul_ps(value, value);
      }
    } else {
      std::fill(tail.begin(), tail.end(), 0.0F);
      for (std::size_t item = 0; item < available; item += 8) {
        _mm256_storeu_ps(tail.data() + item, load(index + item));
      }
      for (std::size_t lane = 0; lane < 8; ++lane) {
        const __m256 value = _mm256_loadu_ps(tail.data() + lane * 8);
        squares[lane] = _mm256_mul_ps(value, value);
      }
    }
    float block_sum = LibncSum64(squares);
    std::size_t slot = 0;
    while ((blocks & (std::size_t{1} << slot)) != 0) {
      block_sum += partials[slot];
      partials[slot] = 0.0F;
      ++slot;
    }
    partials[slot] = block_sum;
    ++blocks;
    index += available;
  }
  float total = 0.0F;
  std::size_t slots = 0;
  for (std::size_t remaining = blocks; remaining != 0; remaining >>= 1) {
    ++slots;
  }
  for (std::size_t slot = 0; slot < slots; ++slot) total += partials[slot];
  const float norm = std::sqrt(total);
  if (!std::isfinite(norm)) {
    throw std::runtime_error("Adam gradient norm is not finite");
  }
  return norm;
}

float GradientNorm(const Bf16Buffer& gradient) {
  for (const Bf16 value : gradient) {
    if (!std::isfinite(Bf16ToFloat(value))) {
      throw std::runtime_error("Adam BF16 gradient is not finite");
    }
  }
  return GradientNorm(gradient.size(), [&gradient](std::size_t index) {
    return LoadBf16(gradient.data() + index);
  });
}

float GradientNorm(const F32Buffer& gradient) {
  if (!std::all_of(gradient.begin(), gradient.end(), [](float value) {
        return std::isfinite(value);
      })) {
    throw std::runtime_error("Adam F32 gradient is not finite");
  }
  return GradientNorm(gradient.size(), [&gradient](std::size_t index) {
    return _mm256_loadu_ps(gradient.data() + index);
  });
}

__m256 FastReciprocalSquareRoot(__m256 value) {
  const __m256 half = _mm256_mul_ps(value, _mm256_set1_ps(0.5F));
  const __m256i shifted =
      _mm256_srli_epi32(_mm256_castps_si256(value), 1);
  const __m256 estimate = _mm256_castsi256_ps(
      _mm256_sub_epi32(_mm256_set1_epi32(0x5f3759df), shifted));
  const __m256 half_estimate = _mm256_mul_ps(half, estimate);
  const __m256 correction = _mm256_fnmadd_ps(
      estimate, half_estimate, _mm256_set1_ps(1.5F));
  return _mm256_mul_ps(correction, estimate);
}

float PowerF32(float base, std::uint64_t exponent) {
  if (exponent == 0) return 1.0F;
  std::uint32_t highest =
      63U - static_cast<std::uint32_t>(__builtin_clzll(exponent));
  float result = base;
  while (highest-- != 0) {
    result *= result;
    if ((exponent & (std::uint64_t{1} << highest)) != 0) result *= base;
  }
  return result;
}

void ValidateFinite(const Bf16Buffer& values, const char* label) {
  for (const Bf16 value : values) {
    if (!std::isfinite(Bf16ToFloat(value))) {
      throw std::runtime_error(std::string(label) + " contains a non-finite value");
    }
  }
}

void ValidateFinite(const F32Buffer& values, const char* label) {
  if (!std::all_of(values.begin(), values.end(), [](float value) {
        return std::isfinite(value);
      })) {
    throw std::runtime_error(std::string(label) + " contains a non-finite value");
  }
}

void UpdateBf16(
    Bf16Buffer& parameter,
    std::vector<std::uint16_t>& low,
    Bf16Buffer& variance,
    const Bf16Buffer& gradient,
    float gradient_scale,
    float alpha,
    float epsilon_squared) {
  const __m256 scale = _mm256_set1_ps(gradient_scale);
  const __m256 beta2 = _mm256_set1_ps(kBeta2);
  const __m256 one_minus_beta2 = _mm256_set1_ps(1.0F - kBeta2);
  const __m256 alpha_vector = _mm256_set1_ps(alpha);
  const __m256 epsilon_vector = _mm256_set1_ps(epsilon_squared);
  const __m256 decay = _mm256_set1_ps(1.0F);
  const __m256i bias = _mm256_set1_epi32(static_cast<int>(kBf16Bias));
  const __m256i inverse_bias =
      _mm256_set1_epi32(-static_cast<int>(kBf16Bias));
  const __m256i round_bias = _mm256_set1_epi32(0x7fff);
  const __m256i one = _mm256_set1_epi32(1);
  alignas(32) std::array<std::uint32_t, 8> parameter_words{};
  alignas(32) std::array<std::uint32_t, 8> variance_words{};
  for (std::size_t index = 0; index < parameter.size(); index += 8) {
    const __m256 gradient_value =
        _mm256_mul_ps(LoadBf16(gradient.data() + index), scale);
    const __m256 old_variance = LoadBf16(variance.data() + index);
    const __m256 gradient_square =
        _mm256_mul_ps(gradient_value, gradient_value);
    const __m256 weighted_square =
        _mm256_mul_ps(gradient_square, one_minus_beta2);
    const __m256 new_variance =
        _mm256_fmadd_ps(old_variance, beta2, weighted_square);

    __m256i variance_bits = _mm256_castps_si256(new_variance);
    const __m256i variance_lsb = _mm256_and_si256(
        _mm256_srli_epi32(variance_bits, 16), one);
    variance_bits = _mm256_add_epi32(
        _mm256_add_epi32(variance_bits, round_bias), variance_lsb);
    _mm256_store_si256(
        reinterpret_cast<__m256i*>(variance_words.data()),
        _mm256_srli_epi32(variance_bits, 16));

    const __m256 scaled_update =
        _mm256_mul_ps(gradient_value, alpha_vector);
    const __m256 update = _mm256_mul_ps(
        FastReciprocalSquareRoot(
            _mm256_add_ps(new_variance, epsilon_vector)),
        scaled_update);
    const __m256i parameter_high = _mm256_slli_epi32(
        _mm256_cvtepu16_epi32(_mm_loadu_si128(
            reinterpret_cast<const __m128i*>(parameter.data() + index))),
        16);
    const __m256i parameter_low = _mm256_cvtepu16_epi32(
        _mm_loadu_si128(reinterpret_cast<const __m128i*>(low.data() + index)));
    const __m256 decoded_parameter = _mm256_castsi256_ps(_mm256_add_epi32(
        _mm256_or_si256(parameter_high, parameter_low), inverse_bias));
    const __m256 new_parameter =
        _mm256_fmsub_ps(decoded_parameter, decay, update);
    _mm256_store_si256(
        reinterpret_cast<__m256i*>(parameter_words.data()),
        _mm256_add_epi32(_mm256_castps_si256(new_parameter), bias));
    for (std::size_t lane = 0; lane < 8; ++lane) {
      parameter[index + lane] =
          static_cast<Bf16>(parameter_words[lane] >> 16U);
      low[index + lane] =
          static_cast<std::uint16_t>(parameter_words[lane]);
      variance[index + lane] =
          static_cast<Bf16>(variance_words[lane]);
    }
  }
}

void UpdateF32(
    F32Buffer& parameter,
    F32Buffer& variance,
    const F32Buffer& gradient,
    float gradient_scale,
    float alpha,
    float epsilon_squared) {
  const __m256 scale = _mm256_set1_ps(gradient_scale);
  const __m256 beta2 = _mm256_set1_ps(kBeta2);
  const __m256 one_minus_beta2 = _mm256_set1_ps(1.0F - kBeta2);
  const __m256 alpha_vector = _mm256_set1_ps(alpha);
  const __m256 epsilon_vector = _mm256_set1_ps(epsilon_squared);
  const __m256 decay = _mm256_set1_ps(1.0F);
  for (std::size_t index = 0; index < parameter.size(); index += 8) {
    const __m256 gradient_value = _mm256_mul_ps(
        _mm256_loadu_ps(gradient.data() + index), scale);
    const __m256 old_variance = _mm256_loadu_ps(variance.data() + index);
    const __m256 weighted_square = _mm256_mul_ps(
        _mm256_mul_ps(gradient_value, gradient_value), one_minus_beta2);
    const __m256 new_variance =
        _mm256_fmadd_ps(old_variance, beta2, weighted_square);
    const __m256 scaled_update =
        _mm256_mul_ps(gradient_value, alpha_vector);
    const __m256 update = _mm256_mul_ps(
        FastReciprocalSquareRoot(
            _mm256_add_ps(new_variance, epsilon_vector)),
        scaled_update);
    const __m256 new_parameter = _mm256_fmsub_ps(
        _mm256_loadu_ps(parameter.data() + index), decay, update);
    _mm256_storeu_ps(parameter.data() + index, new_parameter);
    _mm256_storeu_ps(variance.data() + index, new_variance);
  }
}

}  // namespace

ProfileAdamState LoadProfileAdamState(
    const ProfileGeometry& geometry,
    const std::filesystem::path& optimizer_container,
    std::uint64_t next_update_exponent) {
  if (next_update_exponent == 0) {
    throw std::invalid_argument("Adam next update exponent is zero");
  }
  const TensorContainer container(optimizer_container);
  if (container.configuration() != kOptimizerConfiguration) {
    throw std::runtime_error("optimizer configuration differs");
  }
  const std::vector<GradientDescriptor> descriptors =
      CanonicalGradientDescriptors(geometry);
  std::size_t expected_tensors = descriptors.size();
  for (const GradientDescriptor& descriptor : descriptors) {
    if (descriptor.element_type == GradientElementType::kBf16) {
      if (expected_tensors == std::numeric_limits<std::size_t>::max()) {
        throw std::invalid_argument("optimizer tensor population overflows");
      }
      ++expected_tensors;
    }
  }
  if (container.tensors().size() != expected_tensors) {
    throw std::runtime_error("optimizer tensor population differs");
  }
  ProfileAdamState state{
      .next_update_exponent = next_update_exponent,
      .tensors = {},
  };
  state.tensors.reserve(descriptors.size());
  for (const GradientDescriptor& descriptor : descriptors) {
    AdamTensorState tensor{
        .descriptor = descriptor,
        .low_words = {},
        .variance_bf16 = {},
        .variance_f32 = {},
    };
    if (descriptor.element_type == GradientElementType::kBf16) {
      tensor.variance_bf16 = container.CopyBf16(
          descriptor.name + ".grad_v", descriptor.dimensions);
      tensor.low_words = container.CopyU16Type7(
          descriptor.name + ".low", descriptor.dimensions);
    } else {
      tensor.variance_f32 = container.CopyF32(
          descriptor.name + ".grad_v", descriptor.dimensions);
    }
    state.tensors.push_back(std::move(tensor));
  }
  return state;
}

namespace {

struct IndexedGradientArtifact {
  std::size_t parameter_index;
  GradientArtifactView gradient;
};

ProfileAdamUpdateResult ApplySelectedProfileAdamUpdate(
    std::vector<ParameterArtifactView>& parameters,
    const std::vector<IndexedGradientArtifact>& selected,
    ProfileAdamState& state,
    float learning_rate) {
  if (!std::isfinite(learning_rate) || learning_rate <= 0.0F) {
    throw std::invalid_argument("Adam learning rate is invalid");
  }
  if (state.next_update_exponent == 0 ||
      state.next_update_exponent ==
          std::numeric_limits<std::uint64_t>::max()) {
    throw std::invalid_argument("Adam update exponent is invalid");
  }
  if (parameters.size() != state.tensors.size() || selected.empty()) {
    throw std::invalid_argument("Adam tensor population differs");
  }
  for (std::size_t index = 0; index < parameters.size(); ++index) {
    if (!SameDescriptor(parameters[index].descriptor, state.tensors[index].descriptor)) {
      throw std::invalid_argument("Adam state descriptor differs at index " +
                                  std::to_string(index));
    }
  }

  volatile float beta2_source = kBeta2;
  const float beta2_power =
      PowerF32(beta2_source, state.next_update_exponent);
  const float bias_correction = std::sqrt(1.0F - beta2_power);
  const float alpha = learning_rate * bias_correction;
  float epsilon_squared = kEpsilon * bias_correction;
  epsilon_squared *= epsilon_squared;
  if (!std::isfinite(beta2_power) || !std::isfinite(bias_correction) ||
      !std::isfinite(alpha) || !std::isfinite(epsilon_squared) ||
      bias_correction <= 0.0F) {
    throw std::runtime_error("Adam scalar schedule is invalid");
  }

  ProfileAdamUpdateResult result{
      .update_exponent = state.next_update_exponent,
      .beta2_power = beta2_power,
      .bias_correction = bias_correction,
      .alpha = alpha,
      .epsilon_squared = epsilon_squared,
      .clipped_tensors = 0,
      .tensors = {},
  };
  result.tensors.reserve(selected.size());
  std::size_t previous_index = 0;
  bool has_previous = false;
  for (const IndexedGradientArtifact& item : selected) {
    const std::size_t index = item.parameter_index;
    if (index >= parameters.size() ||
        (has_previous && index <= previous_index)) {
      throw std::invalid_argument(
          "selected Adam indexes must be unique canonical order");
    }
    previous_index = index;
    has_previous = true;
    const ParameterArtifactView& parameter = parameters[index];
    const GradientArtifactView& gradient = item.gradient;
    const AdamTensorState& tensor = state.tensors[index];
    if (!SameDescriptor(parameter.descriptor, gradient.descriptor)) {
      throw std::invalid_argument("Adam tensor descriptor differs at index " +
                                  std::to_string(index));
    }
    float norm;
    if (parameter.descriptor.element_type == GradientElementType::kBf16) {
      if (parameter.bf16_values == nullptr || gradient.bf16_values == nullptr ||
          parameter.f32_values != nullptr || gradient.f32_values != nullptr ||
          gradient.bf16_values->size() != parameter.bf16_values->size() ||
          tensor.low_words.size() != parameter.bf16_values->size() ||
          tensor.variance_bf16.size() != parameter.bf16_values->size() ||
          !tensor.variance_f32.empty()) {
        throw std::invalid_argument("Adam BF16 state geometry differs for " +
                                    parameter.descriptor.name);
      }
      ValidateFinite(*parameter.bf16_values, "Adam BF16 parameter");
      ValidateFinite(tensor.variance_bf16, "Adam BF16 variance");
      norm = GradientNorm(*gradient.bf16_values);
    } else {
      if (parameter.f32_values == nullptr || gradient.f32_values == nullptr ||
          parameter.bf16_values != nullptr || gradient.bf16_values != nullptr ||
          gradient.f32_values->size() != parameter.f32_values->size() ||
          tensor.variance_f32.size() != parameter.f32_values->size() ||
          !tensor.low_words.empty() || !tensor.variance_bf16.empty()) {
        throw std::invalid_argument("Adam F32 state geometry differs for " +
                                    parameter.descriptor.name);
      }
      ValidateFinite(*parameter.f32_values, "Adam F32 parameter");
      ValidateFinite(tensor.variance_f32, "Adam F32 variance");
      norm = GradientNorm(*gradient.f32_values);
    }
    const float scale = norm > kGradientClip ? kGradientClip / norm : 1.0F;
    if (!std::isfinite(scale) || scale <= 0.0F) {
      throw std::runtime_error("Adam gradient scale is invalid");
    }
    if (scale != 1.0F) ++result.clipped_tensors;
    result.tensors.push_back({parameter.descriptor.name, norm, scale});
  }

  for (std::size_t selected_index = 0;
       selected_index < selected.size();
       ++selected_index) {
    const std::size_t index = selected[selected_index].parameter_index;
    ParameterArtifactView& parameter = parameters[index];
    const GradientArtifactView& gradient = selected[selected_index].gradient;
    AdamTensorState& tensor = state.tensors[index];
    const float scale = result.tensors[selected_index].gradient_scale;
    if (parameter.descriptor.element_type == GradientElementType::kBf16) {
      UpdateBf16(
          *parameter.bf16_values,
          tensor.low_words,
          tensor.variance_bf16,
          *gradient.bf16_values,
          scale,
          alpha,
          epsilon_squared);
    } else {
      UpdateF32(
          *parameter.f32_values,
          tensor.variance_f32,
          *gradient.f32_values,
          scale,
          alpha,
          epsilon_squared);
    }
  }
  ++state.next_update_exponent;
  return result;
}

}  // namespace

ProfileAdamUpdateResult ApplyProfileAdamUpdate(
    const ProfileGeometry& geometry,
    ProfileWeights& weights,
    const ProfileGradients& gradients,
    ProfileAdamState& state,
    float learning_rate) {
  std::vector<ParameterArtifactView> parameters =
      CanonicalParameterArtifacts(geometry, weights);
  const std::vector<GradientArtifactView> gradient_artifacts =
      CanonicalGradientArtifacts(geometry, gradients);
  if (parameters.size() != gradient_artifacts.size()) {
    throw std::invalid_argument("Adam gradient population differs");
  }
  std::vector<IndexedGradientArtifact> selected;
  selected.reserve(gradient_artifacts.size());
  for (std::size_t index = 0; index < gradient_artifacts.size(); ++index) {
    selected.push_back({index, gradient_artifacts[index]});
  }
  return ApplySelectedProfileAdamUpdate(
      parameters, selected, state, learning_rate);
}

ProfileAdamUpdateResult ApplyProfileAdamOutputHeadUpdate(
    const ProfileGeometry& geometry,
    ProfileWeights& weights,
    const Bf16Buffer& output_weight_gradient,
    const Bf16Buffer& output_bias_gradient,
    ProfileAdamState& state,
    float learning_rate) {
  std::vector<ParameterArtifactView> parameters =
      CanonicalParameterArtifacts(geometry, weights);
  std::vector<IndexedGradientArtifact> selected;
  selected.reserve(2);
  for (std::size_t index = 0; index < parameters.size(); ++index) {
    const GradientDescriptor& descriptor = parameters[index].descriptor;
    if (descriptor.name == "embed_out") {
      selected.push_back({
          index,
          GradientArtifactView{descriptor, &output_weight_gradient, nullptr},
      });
    } else if (descriptor.name == "out_bias") {
      selected.push_back({
          index,
          GradientArtifactView{descriptor, &output_bias_gradient, nullptr},
      });
    }
  }
  if (selected.size() != 2) {
    throw std::logic_error("output-head Adam topology differs");
  }
  return ApplySelectedProfileAdamUpdate(
      parameters, selected, state, learning_rate);
}

}  // namespace gamma_enwiki9::nncp
