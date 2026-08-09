#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-cpu.h"
#include "ggml-opt.h"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

static ggml_opt_optimizer_params frozen_adamw(void *) {
    ggml_opt_optimizer_params p = ggml_opt_get_default_optimizer_params(nullptr);
    p.adamw.alpha = 0.0025f;
    p.adamw.beta1 = 0.9f;
    p.adamw.beta2 = 0.999f;
    p.adamw.eps = 1.0e-8f;
    p.adamw.wd = 0.0f;
    return p;
}

static void print_hex(const std::vector<float> & values) {
    for (float value : values) {
        std::uint32_t bits = 0;
        std::memcpy(&bits, &value, sizeof(bits));
        std::printf("%08x", bits);
    }
    std::printf("\n");
}

int main() {
    ggml_log_set(nullptr, nullptr);
    constexpr int64_t d_model = 4;
    constexpr int64_t n_class = 3;
    constexpr int64_t n_batch = 2;

    ggml_backend_t backend = ggml_backend_cpu_init();
    if (!backend) {
        return 10;
    }
    ggml_backend_t backends[] = {backend};
    ggml_backend_sched_t sched = ggml_backend_sched_new(
        backends, nullptr, 1, GGML_DEFAULT_GRAPH_SIZE, false, true);

    ggml_init_params static_params = {
        8 * ggml_tensor_overhead(), nullptr, true,
    };
    ggml_context * ctx_static = ggml_init(static_params);
    ggml_init_params compute_params = {
        GGML_DEFAULT_GRAPH_SIZE * ggml_tensor_overhead() + 4 * ggml_graph_overhead(),
        nullptr,
        true,
    };
    ggml_context * ctx_compute = ggml_init(compute_params);

    ggml_tensor * input = ggml_new_tensor_2d(
        ctx_static, GGML_TYPE_F32, d_model, n_batch);
    ggml_set_name(input, "input");
    ggml_set_input(input);
    ggml_tensor * weights = ggml_new_tensor_2d(
        ctx_static, GGML_TYPE_F32, d_model, n_class);
    ggml_set_name(weights, "weights");
    ggml_set_param(weights);

    ggml_tensor * normalized = ggml_rms_norm(ctx_compute, input, 1.0e-5f);
    ggml_tensor * activated = ggml_gelu(ctx_compute, normalized);
    ggml_tensor * logits = ggml_mul_mat(ctx_compute, weights, activated);
    ggml_set_name(logits, "logits");

    ggml_backend_buffer_t static_buf = ggml_backend_alloc_ctx_tensors(ctx_static, backend);
    if (!static_buf) {
        return 11;
    }
    std::vector<float> initial_weights(d_model * n_class);
    for (size_t i = 0; i < initial_weights.size(); ++i) {
        initial_weights[i] = (static_cast<int>(i) - 5) * 0.03125f;
    }
    ggml_backend_tensor_set(weights, initial_weights.data(), 0, ggml_nbytes(weights));

    ggml_opt_params opt_params = ggml_opt_default_params(
        sched, GGML_OPT_LOSS_TYPE_CROSS_ENTROPY);
    opt_params.ctx_compute = ctx_compute;
    opt_params.inputs = input;
    opt_params.outputs = logits;
    opt_params.opt_period = 1;
    opt_params.optimizer = GGML_OPT_OPTIMIZER_TYPE_ADAMW;
    opt_params.get_opt_pars = frozen_adamw;
    opt_params.get_opt_pars_ud = nullptr;

    ggml_opt_context_t opt = ggml_opt_init(opt_params);
    ggml_opt_result_t result = ggml_opt_result_init();
    const std::vector<std::vector<float>> batches = {
        {0.25f, -0.50f, 0.75f, 1.00f, -0.25f, 0.50f, 1.25f, -1.00f},
        {-1.00f, 0.50f, 0.25f, 0.75f, 1.00f, -0.75f, 0.50f, 0.25f},
        {0.60f, 0.20f, -0.40f, 0.80f, -0.10f, 0.90f, -0.70f, 0.30f},
    };
    const std::vector<std::vector<float>> labels = {
        {1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f},
        {0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f},
        {0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 0.0f},
    };

    for (size_t step = 0; step < batches.size(); ++step) {
        ggml_opt_alloc(opt, true);
        ggml_backend_tensor_set(input, batches[step].data(), 0, ggml_nbytes(input));
        ggml_backend_tensor_set(
            ggml_opt_labels(opt), labels[step].data(), 0,
            ggml_nbytes(ggml_opt_labels(opt)));
        ggml_opt_eval(opt, result);
    }

    std::vector<float> final_weights(initial_weights.size());
    ggml_backend_tensor_get(weights, final_weights.data(), 0, ggml_nbytes(weights));
    for (float value : final_weights) {
        if (!std::isfinite(value)) {
            return 12;
        }
    }
    double loss = 0.0;
    ggml_opt_result_loss(result, &loss, nullptr);
    if (!std::isfinite(loss)) {
        return 13;
    }

    std::printf("weights=");
    print_hex(final_weights);
    std::uint64_t loss_bits = 0;
    std::memcpy(&loss_bits, &loss, sizeof(loss_bits));
    std::printf("loss=%016llx\n", static_cast<unsigned long long>(loss_bits));

    ggml_opt_result_free(result);
    ggml_opt_free(opt);
    ggml_backend_buffer_free(static_buf);
    ggml_free(ctx_static);
    ggml_free(ctx_compute);
    ggml_backend_sched_free(sched);
    ggml_backend_free(backend);
    return 0;
}
