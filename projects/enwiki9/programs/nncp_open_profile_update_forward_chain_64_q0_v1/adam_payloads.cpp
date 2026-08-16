#define main gamma_adam_replay_comparator_main
#include "../nncp_open_profile_adam_replay_64_q0_retry_v2/adam_replay.cpp"
#undef main

namespace {

void require_output(std::ofstream &output, const fs::path &path) {
    if (!output) {
        throw std::runtime_error("cannot write open parameter payload " + path.string());
    }
}

void write_bf16_payload(
    const std::string &name, const Record &parameter_initial,
    const Record &low_initial, const Record &variance_initial,
    const Mapping &gradient, float gradient_scale, float alpha,
    float epsilon_squared, const fs::path &path) {
    const std::uint64_t count = parameter_initial.count;
    if (count % 8 != 0) {
        throw std::runtime_error("BF16 tensor width is not divisible by eight: " + name);
    }
    const auto *parameter_in = reinterpret_cast<const std::uint16_t *>(
        parameter_initial.payload);
    const auto *low_in = reinterpret_cast<const std::uint16_t *>(low_initial.payload);
    const auto *variance_in = reinterpret_cast<const std::uint16_t *>(
        variance_initial.payload);
    const auto *gradient_in = reinterpret_cast<const std::uint16_t *>(gradient.data());
    const __m256 scale = _mm256_set1_ps(gradient_scale);
    const __m256 beta2 = _mm256_set1_ps(kBeta2);
    const __m256 one_minus_beta2 = _mm256_set1_ps(1.0F - kBeta2);
    const __m256 alpha_vector = _mm256_set1_ps(alpha);
    const __m256 epsilon_vector = _mm256_set1_ps(epsilon_squared);
    const __m256 decay = _mm256_set1_ps(1.0F);
    const __m256i bias = _mm256_set1_epi32(static_cast<int>(kBf16Bias));
    const __m256i inverse_bias = _mm256_set1_epi32(-static_cast<int>(kBf16Bias));
    alignas(32) std::array<std::uint32_t, 8> predicted_parameter {};
    alignas(16) std::array<std::uint16_t, 8> predicted_high {};
    std::ofstream output(path, std::ios::binary);
    require_output(output, path);

    for (std::uint64_t index = 0; index < count; index += 8) {
        const __m256 gradient_value = _mm256_mul_ps(load_bf16(gradient_in + index), scale);
        const __m256 old_variance = load_bf16(variance_in + index);
        const __m256 gradient_square = _mm256_mul_ps(gradient_value, gradient_value);
        const __m256 weighted_square = _mm256_mul_ps(gradient_square, one_minus_beta2);
        const __m256 new_variance = _mm256_fmadd_ps(old_variance, beta2, weighted_square);
        const __m256 scaled_update = _mm256_mul_ps(gradient_value, alpha_vector);
        const __m256 update = _mm256_mul_ps(
            fast_rsqrt(_mm256_add_ps(new_variance, epsilon_vector)), scaled_update);
        const __m256i parameter_high = _mm256_slli_epi32(
            _mm256_cvtepu16_epi32(_mm_loadu_si128(
                reinterpret_cast<const __m128i *>(parameter_in + index))),
            16);
        const __m256i parameter_low = _mm256_cvtepu16_epi32(_mm_loadu_si128(
            reinterpret_cast<const __m128i *>(low_in + index)));
        const __m256 parameter = _mm256_castsi256_ps(_mm256_add_epi32(
            _mm256_or_si256(parameter_high, parameter_low), inverse_bias));
        const __m256 new_parameter = _mm256_fmsub_ps(parameter, decay, update);
        const __m256i biased_parameter = _mm256_add_epi32(
            _mm256_castps_si256(new_parameter), bias);
        _mm256_store_si256(
            reinterpret_cast<__m256i *>(predicted_parameter.data()), biased_parameter);
        for (std::size_t lane = 0; lane < predicted_high.size(); ++lane) {
            predicted_high[lane] = static_cast<std::uint16_t>(
                predicted_parameter[lane] >> 16);
        }
        output.write(reinterpret_cast<const char *>(predicted_high.data()),
                     sizeof(predicted_high));
        require_output(output, path);
    }
}

void write_f32_payload(
    const std::string &name, const Record &parameter_initial,
    const Record &variance_initial, const Mapping &gradient,
    float gradient_scale, float alpha, float epsilon_squared,
    const fs::path &path) {
    const std::uint64_t count = parameter_initial.count;
    if (count % 8 != 0) {
        throw std::runtime_error("F32 tensor width is not divisible by eight: " + name);
    }
    const auto *parameter_in = reinterpret_cast<const float *>(parameter_initial.payload);
    const auto *variance_in = reinterpret_cast<const float *>(variance_initial.payload);
    const auto *gradient_in = reinterpret_cast<const float *>(gradient.data());
    const __m256 scale = _mm256_set1_ps(gradient_scale);
    const __m256 beta2 = _mm256_set1_ps(kBeta2);
    const __m256 one_minus_beta2 = _mm256_set1_ps(1.0F - kBeta2);
    const __m256 alpha_vector = _mm256_set1_ps(alpha);
    const __m256 epsilon_vector = _mm256_set1_ps(epsilon_squared);
    const __m256 decay = _mm256_set1_ps(1.0F);
    alignas(32) std::array<std::uint32_t, 8> predicted_parameter {};
    std::ofstream output(path, std::ios::binary);
    require_output(output, path);

    for (std::uint64_t index = 0; index < count; index += 8) {
        const __m256 gradient_value = _mm256_mul_ps(
            _mm256_loadu_ps(gradient_in + index), scale);
        const __m256 old_variance = _mm256_loadu_ps(variance_in + index);
        const __m256 weighted_square = _mm256_mul_ps(
            _mm256_mul_ps(gradient_value, gradient_value), one_minus_beta2);
        const __m256 new_variance = _mm256_fmadd_ps(old_variance, beta2, weighted_square);
        const __m256 scaled_update = _mm256_mul_ps(gradient_value, alpha_vector);
        const __m256 update = _mm256_mul_ps(
            fast_rsqrt(_mm256_add_ps(new_variance, epsilon_vector)), scaled_update);
        const __m256 new_parameter = _mm256_fmsub_ps(
            _mm256_loadu_ps(parameter_in + index), decay, update);
        _mm256_store_si256(reinterpret_cast<__m256i *>(predicted_parameter.data()),
                           _mm256_castps_si256(new_parameter));
        output.write(reinterpret_cast<const char *>(predicted_parameter.data()),
                     sizeof(predicted_parameter));
        require_output(output, path);
    }
}

void write_open_parameters(const fs::path &fixture, const fs::path &directory) {
    if (!fs::create_directory(directory) || !fs::is_empty(directory)) {
        throw std::runtime_error("open parameter output directory is not fresh");
    }
    Container parameters_initial(fixture / "parameters_initial.coefs");
    Container optimizer_initial(fixture / "optimizer_initial.params");
    const auto gradients = load_gradients(fixture / "gradients");
    if (parameters_initial.size() != kExpectedParameters ||
        gradients.size() != kExpectedParameters || optimizer_initial.size() != 491) {
        throw std::runtime_error("open update input population differs");
    }
    volatile float beta2_source = kBeta2;
    const float beta2_power = power_f32(beta2_source, kUpdateExponent);
    const float bias_correction = std::sqrt(1.0F - beta2_power);
    const float alpha = kLearningRate * bias_correction;
    float epsilon_squared = kEpsilon * bias_correction;
    epsilon_squared *= epsilon_squared;

    for (const std::string &name : parameters_initial.order()) {
        const Record &parameter_initial = parameters_initial.at(name);
        const auto gradient_iterator = gradients.find(name);
        if (gradient_iterator == gradients.end()) {
            throw std::runtime_error("missing gradient " + name);
        }
        const Gradient &gradient_metadata = gradient_iterator->second;
        if (gradient_metadata.type != parameter_initial.type ||
            gradient_metadata.dimensions != parameter_initial.dimensions) {
            throw std::runtime_error("gradient geometry differs for " + name);
        }
        Mapping gradient(gradient_metadata.payload);
        const float sum_squares = gradient_sum_squares(
            gradient, gradient_metadata.type, parameter_initial.count);
        const float norm = std::sqrt(sum_squares);
        const float scale = norm > kGradientClip ? kGradientClip / norm : 1.0F;
        const Record &variance_initial = optimizer_initial.at(name + ".grad_v");
        require_same_geometry(parameter_initial, variance_initial, name + ".grad_v");
        const fs::path output = directory / (name + ".bin");
        if (parameter_initial.type == kBf16) {
            const Record &low_initial = optimizer_initial.at(name + ".low");
            if (low_initial.type != 7 ||
                low_initial.dimensions != parameter_initial.dimensions) {
                throw std::runtime_error("BF16 low-word geometry differs for " + name);
            }
            write_bf16_payload(name, parameter_initial, low_initial,
                               variance_initial, gradient, scale, alpha,
                               epsilon_squared, output);
        } else if (parameter_initial.type == kF32) {
            write_f32_payload(name, parameter_initial, variance_initial,
                              gradient, scale, alpha, epsilon_squared, output);
        } else {
            throw std::runtime_error("parameter type is not F32 or BF16: " + name);
        }
    }
}

} // namespace

int main(int argc, char **argv) {
    try {
        if (argc != 4) {
            throw std::runtime_error(
                "usage: adam_payloads FIXTURE REPORT OUTPUT_DIRECTORY");
        }
        const fs::path fixture = fs::canonical(argv[1]);
        write_open_parameters(fixture, fs::absolute(argv[3]));
        char *comparator_argv[] = {argv[0], argv[1], argv[2], nullptr};
        return gamma_adam_replay_comparator_main(3, comparator_argv);
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
