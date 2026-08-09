#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-cpu.h"
#include "ggml-opt.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

constexpr int64_t FEATURES = 32;
constexpr int64_t CLASSES = 256;
constexpr int64_t STATES = 4;

static std::vector<float> read_f32(const fs::path & path, size_t count) {
    std::vector<float> values(count);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(values.data()), values.size() * sizeof(float));
    if (!input || input.peek() != std::ifstream::traits_type::eof()) {
        throw std::runtime_error("invalid fixture file: " + path.string());
    }
    return values;
}

static void write_f32(const fs::path & path, const std::vector<float> & values) {
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(values.data()), values.size() * sizeof(float));
    if (!output) {
        throw std::runtime_error("failed writing output: " + path.string());
    }
}

static void clipped_first_adam(std::vector<float> & parameter, const std::vector<float> & gradient) {
    constexpr float learning_rate = 0.00016f;
    constexpr float beta2 = 0.9999f;
    constexpr float epsilon = 1.0e-8f;
    constexpr float clip_limit = 0.05f;
    double sum_squares = 0.0;
    for (float value : gradient) {
        sum_squares += static_cast<double>(value) * value;
    }
    const float norm = static_cast<float>(std::sqrt(sum_squares));
    const float clip_scale = norm > clip_limit ? clip_limit / norm : 1.0f;
    const float beta2_correction = 1.0f - beta2;
    const float root_correction = std::sqrt(beta2_correction);
    const float epsilon_squared = epsilon * root_correction * epsilon * root_correction;
    const float step_size = learning_rate * root_correction;
    for (size_t index = 0; index < parameter.size(); ++index) {
        const float gradient_clipped = gradient[index] * clip_scale;
        const float second_moment = beta2_correction * gradient_clipped * gradient_clipped;
        parameter[index] -= step_size * gradient_clipped / std::sqrt(second_moment + epsilon_squared);
    }
}

int main(int argc, char ** argv) {
    if (argc != 3) {
        std::fprintf(stderr, "usage: %s FIXTURE_DIR OUTPUT_DIR\n", argv[0]);
        return 2;
    }
    const fs::path fixture = argv[1];
    const fs::path output = argv[2];
    fs::create_directories(output);

    std::vector<float> hidden = read_f32(fixture / "hidden.bin", FEATURES * STATES);
    std::vector<float> weights = read_f32(fixture / "weights.bin", FEATURES * CLASSES);
    std::vector<float> bias = read_f32(fixture / "bias.bin", CLASSES);
    std::vector<float> labels = read_f32(fixture / "labels.bin", CLASSES * STATES);

    ggml_log_set(nullptr, nullptr);
    ggml_backend_t backend = ggml_backend_cpu_init();
    if (!backend) {
        return 10;
    }
    ggml_backend_t backends[] = {backend};
    ggml_backend_sched_t sched = ggml_backend_sched_new(
        backends, nullptr, 1, GGML_DEFAULT_GRAPH_SIZE, false, true);

    ggml_init_params static_params = {
        16 * ggml_tensor_overhead(), nullptr, true,
    };
    ggml_context * ctx_static = ggml_init(static_params);
    ggml_init_params compute_params = {
        GGML_DEFAULT_GRAPH_SIZE * ggml_tensor_overhead() + 4 * ggml_graph_overhead(),
        nullptr,
        true,
    };
    ggml_context * ctx_compute = ggml_init(compute_params);

    ggml_tensor * input = ggml_new_tensor_2d(
        ctx_static, GGML_TYPE_F32, FEATURES, STATES);
    ggml_set_input(input);
    ggml_set_name(input, "hidden");
    ggml_tensor * matrix = ggml_new_tensor_2d(
        ctx_static, GGML_TYPE_F32, FEATURES, CLASSES);
    ggml_set_param(matrix);
    ggml_set_name(matrix, "output_matrix");
    ggml_tensor * offset = ggml_new_tensor_1d(ctx_static, GGML_TYPE_F32, CLASSES);
    ggml_set_param(offset);
    ggml_set_name(offset, "output_bias");

    ggml_tensor * logits = ggml_mul_mat(ctx_compute, matrix, input);
    ggml_tensor * repeated_bias = ggml_repeat(ctx_compute, offset, logits);
    ggml_tensor * outputs = ggml_add(ctx_compute, logits, repeated_bias);
    ggml_set_name(outputs, "head_logits");

    ggml_backend_buffer_t static_buffer = ggml_backend_alloc_ctx_tensors(ctx_static, backend);
    if (!static_buffer) {
        return 11;
    }
    ggml_backend_tensor_set(input, hidden.data(), 0, ggml_nbytes(input));
    ggml_backend_tensor_set(matrix, weights.data(), 0, ggml_nbytes(matrix));
    ggml_backend_tensor_set(offset, bias.data(), 0, ggml_nbytes(offset));

    ggml_opt_params opt_params = ggml_opt_default_params(
        sched, GGML_OPT_LOSS_TYPE_CROSS_ENTROPY);
    opt_params.ctx_compute = ctx_compute;
    opt_params.inputs = input;
    opt_params.outputs = outputs;
    opt_params.opt_period = 1;
    opt_params.optimizer = GGML_OPT_OPTIMIZER_TYPE_ADAMW;
    ggml_opt_context_t opt = ggml_opt_init(opt_params);
    ggml_opt_result_t result = ggml_opt_result_init();

    ggml_opt_alloc(opt, true);
    ggml_backend_tensor_set(
        ggml_opt_labels(opt), labels.data(), 0, ggml_nbytes(ggml_opt_labels(opt)));
    ggml_opt_eval(opt, result);

    ggml_tensor * matrix_gradient = ggml_opt_grad_acc(opt, matrix);
    ggml_tensor * bias_gradient = ggml_opt_grad_acc(opt, offset);
    if (!matrix_gradient || !bias_gradient) {
        return 12;
    }
    std::vector<float> gradient_weights(weights.size());
    std::vector<float> gradient_bias(bias.size());
    ggml_backend_tensor_get(
        matrix_gradient, gradient_weights.data(), 0, ggml_nbytes(matrix_gradient));
    ggml_backend_tensor_get(
        bias_gradient, gradient_bias.data(), 0, ggml_nbytes(bias_gradient));

    clipped_first_adam(weights, gradient_weights);
    clipped_first_adam(bias, gradient_bias);
    for (float value : gradient_weights) {
        if (!std::isfinite(value)) return 13;
    }
    for (float value : gradient_bias) {
        if (!std::isfinite(value)) return 14;
    }
    for (float value : weights) {
        if (!std::isfinite(value)) return 15;
    }
    for (float value : bias) {
        if (!std::isfinite(value)) return 16;
    }

    write_f32(output / "gradient_weights.bin", gradient_weights);
    write_f32(output / "gradient_bias.bin", gradient_bias);
    write_f32(output / "updated_weights.bin", weights);
    write_f32(output / "updated_bias.bin", bias);
    double loss = 0.0;
    ggml_opt_result_loss(result, &loss, nullptr);
    std::ofstream(output / "loss.txt") << std::hexfloat << loss << "\n";

    ggml_opt_result_free(result);
    ggml_opt_free(opt);
    ggml_backend_buffer_free(static_buffer);
    ggml_free(ctx_static);
    ggml_free(ctx_compute);
    ggml_backend_sched_free(sched);
    ggml_backend_free(backend);
    return 0;
}
