#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-cpu.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>
#include <map>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace profile {
constexpr int layers = 20;
constexpr int width = 1024;
constexpr int heads = 8;
constexpr int key = 128;
constexpr int inner = 3072;
constexpr int memory = 256;
constexpr int segment = 64;
constexpr int position = 320;
constexpr int vocabulary = 16392;
constexpr float epsilon = 1.0e-5f;
constexpr int probability_unit = 32768;
}

struct TensorRecord {
    std::string category;
    int index = -1;
    std::string name;
    std::string type;
    std::vector<int64_t> dims;
    std::string payload;
    uint64_t bytes = 0;
};

static std::vector<std::string> split(const std::string & value, char delimiter) {
    std::vector<std::string> output;
    std::istringstream source(value);
    std::string part;
    while (std::getline(source, part, delimiter)) output.push_back(part);
    return output;
}

static std::vector<int64_t> parse_dims(const std::string & value) {
    std::vector<int64_t> output;
    for (const std::string & part : split(value, ',')) output.push_back(std::stoll(part));
    return output;
}

static uint64_t product(const std::vector<int64_t> & dims) {
    uint64_t value = 1;
    for (int64_t dim : dims) value *= static_cast<uint64_t>(dim);
    return value;
}

class Fixture {
public:
    explicit Fixture(fs::path root) : root_(std::move(root)) {
        std::ifstream input(root_ / "tensor_index.tsv");
        if (!input) throw std::runtime_error("missing tensor_index.tsv");
        std::string line;
        if (!std::getline(input, line) ||
            line != "category\tindex\tname\ttype\tdims\tstrides\tbytes\tsha256\tpayload") {
            throw std::runtime_error("invalid tensor index header");
        }
        std::map<std::string, int> next_index;
        while (std::getline(input, line)) {
            const auto fields = split(line, '\t');
            if (fields.size() != 9) throw std::runtime_error("invalid tensor index row");
            TensorRecord record;
            record.category = fields[0];
            record.index = std::stoi(fields[1]);
            record.name = fields[2];
            record.type = fields[3];
            record.dims = parse_dims(fields[4]);
            record.bytes = std::stoull(fields[6]);
            record.payload = fields[8];
            if (record.index != next_index[record.category]++)
                throw std::runtime_error("reordered tensor index: " + record.category);
            const fs::path payload = root_ / record.payload;
            if (!fs::is_regular_file(payload) || fs::file_size(payload) != record.bytes)
                throw std::runtime_error("missing or size-inconsistent payload: " + payload.string());
            // The sequential oracle records the same semantic checkpoint once
            // per decoded position.  Those internal records are comparison
            // evidence, not runtime inputs.  Parameters and initial state must
            // remain uniquely addressable; repeated internal labels are bound
            // by their ordered tensor-index rows and validated by the driver.
            if (record.category != "internal") {
                const std::string key = record.category + "\x1f" + record.name;
                if (!records_.emplace(key, record).second)
                    throw std::runtime_error("duplicate tensor name: " + record.name);
            }
        }
    }

    const TensorRecord & get(const std::string & category, const std::string & name,
                             const std::vector<int64_t> & expected_dims) const {
        const auto found = records_.find(category + "\x1f" + name);
        if (found == records_.end()) throw std::runtime_error("missing tensor: " + name);
        if (found->second.dims != expected_dims)
            throw std::runtime_error("shape mismatch for tensor: " + name);
        return found->second;
    }

    std::vector<float> floats(const TensorRecord & record) const {
        std::ifstream input(root_ / record.payload, std::ios::binary);
        if (!input) throw std::runtime_error("cannot open tensor: " + record.payload);
        const uint64_t count = product(record.dims);
        std::vector<float> output(count);
        if (record.type == "F32") {
            input.read(reinterpret_cast<char *>(output.data()), count * sizeof(float));
        } else if (record.type == "BF16") {
            std::vector<ggml_bf16_t> values(count);
            input.read(reinterpret_cast<char *>(values.data()), count * sizeof(ggml_bf16_t));
            for (uint64_t index = 0; index < count; index++)
                output[index] = ggml_bf16_to_fp32(values[index]);
        } else if (record.type == "I32") {
            std::vector<int32_t> values(count);
            input.read(reinterpret_cast<char *>(values.data()), count * sizeof(int32_t));
            for (uint64_t index = 0; index < count; index++) output[index] = values[index];
        } else if (record.type == "I8") {
            std::vector<int8_t> values(count);
            input.read(reinterpret_cast<char *>(values.data()), count * sizeof(int8_t));
            for (uint64_t index = 0; index < count; index++) output[index] = values[index];
        } else {
            throw std::runtime_error("unsupported tensor type: " + record.type);
        }
        if (!input || input.peek() != std::ifstream::traits_type::eof())
            throw std::runtime_error("truncated or trailing tensor payload: " + record.payload);
        return output;
    }

    std::vector<float> parameter(const std::string & name,
                                 const std::vector<int64_t> & dims) const {
        return floats(get("parameter", name, dims));
    }

    std::vector<float> state(const std::string & name,
                             const std::vector<int64_t> & dims) const {
        return floats(get("state", name, dims));
    }

    const fs::path & root() const { return root_; }

private:
    fs::path root_;
    std::map<std::string, TensorRecord> records_;
};

static void ensure_finite(const std::vector<float> & values, const std::string & label) {
    if (!std::all_of(values.begin(), values.end(), [](float value) { return std::isfinite(value); }))
        throw std::runtime_error("nonfinite tensor: " + label);
}

static float bf16(float value) {
    return ggml_bf16_to_fp32(ggml_fp32_to_bf16(value));
}

static void round_bf16(std::vector<float> & values) {
    for (float & value : values) value = bf16(value);
}

class GGMLMatrixEngine {
public:
    GGMLMatrixEngine() {
        ggml_log_set(nullptr, nullptr);
        backend_ = ggml_backend_cpu_init();
        if (!backend_) throw std::runtime_error("cannot initialize GGML CPU backend");
        ggml_backend_cpu_set_n_threads(backend_, 4);
        ggml_backend_t backends[] = {backend_};
        scheduler_ = ggml_backend_sched_new(
            backends, nullptr, 1, GGML_DEFAULT_GRAPH_SIZE, false, true);
        if (!scheduler_) throw std::runtime_error("cannot initialize GGML scheduler");
    }

    ~GGMLMatrixEngine() {
        ggml_backend_sched_free(scheduler_);
        ggml_backend_free(backend_);
    }

    std::vector<float> multiply(const std::vector<float> & matrix,
                                const std::vector<float> & input,
                                int64_t k, int64_t outputs, int64_t columns,
                                int64_t batches = 1) {
        if (matrix.size() != static_cast<size_t>(k * outputs * batches) ||
            input.size() != static_cast<size_t>(k * columns * batches))
            throw std::runtime_error("GGML matrix geometry mismatch");
        ggml_backend_sched_reset(scheduler_);
        const size_t tensors = 8;
        ggml_init_params params = {
            tensors * ggml_tensor_overhead() + ggml_graph_overhead_custom(16, false),
            nullptr,
            true,
        };
        ggml_context * context = ggml_init(params);
        if (!context) throw std::runtime_error("cannot create GGML context");
        ggml_tensor * weight = batches == 1
            ? ggml_new_tensor_2d(context, GGML_TYPE_BF16, k, outputs)
            : ggml_new_tensor_3d(context, GGML_TYPE_BF16, k, outputs, batches);
        ggml_tensor * source = batches == 1
            ? ggml_new_tensor_2d(context, GGML_TYPE_BF16, k, columns)
            : ggml_new_tensor_3d(context, GGML_TYPE_BF16, k, columns, batches);
        ggml_set_input(weight);
        ggml_set_input(source);
        ggml_tensor * result = ggml_mul_mat(context, weight, source);
        ggml_set_output(result);
        ggml_cgraph * graph = ggml_new_graph_custom(context, 16, false);
        ggml_build_forward_expand(graph, result);
        if (!ggml_backend_sched_alloc_graph(scheduler_, graph)) {
            ggml_free(context);
            throw std::runtime_error("cannot allocate GGML graph");
        }
        std::vector<ggml_bf16_t> matrix_bf16(matrix.size());
        std::vector<ggml_bf16_t> input_bf16(input.size());
        ggml_fp32_to_bf16_row(matrix.data(), matrix_bf16.data(), matrix.size());
        ggml_fp32_to_bf16_row(input.data(), input_bf16.data(), input.size());
        ggml_backend_tensor_set(weight, matrix_bf16.data(), 0,
                                matrix_bf16.size() * sizeof(ggml_bf16_t));
        ggml_backend_tensor_set(source, input_bf16.data(), 0,
                                input_bf16.size() * sizeof(ggml_bf16_t));
        if (ggml_backend_sched_graph_compute(scheduler_, graph) != GGML_STATUS_SUCCESS) {
            ggml_backend_sched_reset(scheduler_);
            ggml_free(context);
            throw std::runtime_error("GGML graph computation failed");
        }
        std::vector<float> output(outputs * columns * batches);
        ggml_backend_tensor_get(result, output.data(), 0, output.size() * sizeof(float));
        ggml_backend_sched_reset(scheduler_);
        ggml_free(context);
        return output;
    }

    std::vector<float> multiply_libnc(const std::vector<float> & matrix,
                                      const std::vector<float> & input,
                                      int64_t outputs, int64_t k,
                                      int64_t columns) {
        if (matrix.size() != static_cast<size_t>(outputs * k))
            throw std::runtime_error("LibNC matrix geometry mismatch");
        // LibNC exports [output,input] with output as the contiguous axis.
        // GGML mul_mat consumes [input,output] with input contiguous.
        std::vector<float> ggml_matrix(matrix.size());
        for (int64_t input_index = 0; input_index < k; input_index++)
            for (int64_t output_index = 0; output_index < outputs; output_index++)
                ggml_matrix[output_index * k + input_index] =
                    matrix[input_index * outputs + output_index];
        return multiply(ggml_matrix, input, k, outputs, columns);
    }

private:
    ggml_backend_t backend_ = nullptr;
    ggml_backend_sched_t scheduler_ = nullptr;
};

static void write_f32(const fs::path & path, const std::vector<float> & values) {
    ensure_finite(values, path.filename().string());
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(values.data()), values.size() * sizeof(float));
    if (!output) throw std::runtime_error("cannot write tensor: " + path.string());
}

static void add_bias_round(std::vector<float> & values, const std::vector<float> & bias,
                           int width, bool round) {
    if (bias.size() != static_cast<size_t>(width) || values.size() % width != 0)
        throw std::runtime_error("bias geometry mismatch");
    for (size_t index = 0; index < values.size(); index++) {
        values[index] += bias[index % width];
        if (round) values[index] = bf16(values[index]);
    }
}

static std::vector<float> rms_norm(const std::vector<float> & input,
                                   const std::vector<float> & gain,
                                   const std::vector<float> & bias) {
    if (input.size() % profile::width || gain.size() != profile::width ||
        bias.size() != profile::width)
        throw std::runtime_error("RMSNorm geometry mismatch");
    std::vector<float> output(input.size());
    const size_t rows = input.size() / profile::width;
    for (size_t row = 0; row < rows; row++) {
        float sum = 0.0f;
        const float * source = input.data() + row * profile::width;
        for (int feature = 0; feature < profile::width; feature++)
            sum += source[feature] * source[feature];
        const float inverse = 1.0f / std::sqrt(sum / profile::width + profile::epsilon);
        for (int feature = 0; feature < profile::width; feature++)
            output[row * profile::width + feature] =
                bf16(bf16(source[feature] * bf16(inverse)) * gain[feature] + bias[feature]);
    }
    return output;
}

static float libnc_gelu(float value) {
    const float argument = std::sqrt(2.0f / static_cast<float>(M_PI)) *
        (value + 0.044715f * value * value * value);
    const float tanh_value = argument >= 8.0f ? 1.0f : std::tanh(argument);
    return 0.5f * value * (1.0f + tanh_value);
}

static std::vector<float> softmax_rows(std::vector<float> values, int row_width) {
    if (values.size() % row_width) throw std::runtime_error("softmax geometry mismatch");
    for (size_t base = 0; base < values.size(); base += row_width) {
        float maximum = -std::numeric_limits<float>::infinity();
        for (int index = 0; index < row_width; index++)
            maximum = std::max(maximum, values[base + index]);
        float total = 0.0f;
        for (int index = 0; index < row_width; index++) {
            values[base + index] = std::exp(values[base + index] - maximum);
            total += values[base + index];
        }
        for (int index = 0; index < row_width; index++)
            values[base + index] /= total;
    }
    return values;
}

static std::vector<uint16_t> read_targets(const fs::path & path) {
    std::ifstream input(path, std::ios::binary);
    std::vector<uint16_t> values(profile::segment);
    for (uint16_t & value : values) {
        const int low = input.get();
        const int high = input.get();
        if (low < 0 || high < 0) throw std::runtime_error("truncated target symbols");
        value = static_cast<uint16_t>(low | (high << 8));
        if (value >= profile::vocabulary) throw std::runtime_error("target out of vocabulary");
    }
    if (input.get() != EOF) throw std::runtime_error("trailing target symbols");
    return values;
}

static void put_u32(std::ofstream & output, uint32_t value) {
    std::array<char, 4> bytes{};
    for (int index = 0; index < 4; index++) bytes[index] = (value >> (8 * index)) & 255;
    output.write(bytes.data(), bytes.size());
}

static void write_tree_path(const fs::path & path,
                            const std::vector<float> & probabilities,
                            const std::vector<uint16_t> & targets) {
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write("NNPTREE1", 8);
    put_u32(output, profile::segment);
    put_u32(output, profile::vocabulary);
    for (int position = 0; position < profile::segment; position++) {
        const float * table = probabilities.data() + position * profile::vocabulary;
        int start = 0;
        int range = profile::vocabulary;
        float total = 1.0f;
        int depth = 0;
        while (range > 1) {
            const int range0 = range >> 1;
            float total0 = 0.0f;
            for (int index = 0; index < range0; index++) total0 += table[start + index];
            int probability0 = std::lrint(total0 * profile::probability_unit / total);
            probability0 = std::max(1, std::min(profile::probability_unit - 1, probability0));
            const int bit = targets[position] >= start + range0;
            for (uint32_t value : {
                     static_cast<uint32_t>(position), static_cast<uint32_t>(targets[position]),
                     static_cast<uint32_t>(depth), static_cast<uint32_t>(start),
                     static_cast<uint32_t>(range), static_cast<uint32_t>(range0),
                     static_cast<uint32_t>(probability0), static_cast<uint32_t>(bit)})
                put_u32(output, value);
            if (bit) {
                start += range0;
                range -= range0;
                total -= total0;
            } else {
                range = range0;
                total = total0;
            }
            depth++;
        }
    }
    if (!output) throw std::runtime_error("cannot write branch path");
}

static std::string layer_name(const char * prefix, int layer) {
    return std::string(prefix) + "_" + std::to_string(layer);
}

int main(int argc, char ** argv) {
    try {
        if (argc != 3) {
            std::fprintf(stderr, "usage: %s FIXTURE_DIR OUTPUT_DIR\n", argv[0]);
            return 2;
        }
        Fixture fixture(argv[1]);
        const fs::path output_dir = argv[2];
        fs::create_directories(output_dir);
        GGMLMatrixEngine engine;

        std::vector<float> input_values = fixture.state(
            "input_stream_0", {1, profile::segment});
        const std::vector<uint16_t> targets = read_targets(
            fixture.root() / "target_symbols.u16le");
        std::vector<int> input_symbols(profile::segment);
        input_symbols[0] = static_cast<int>(input_values[0]);
        for (int position = 1; position < profile::segment; position++) {
            input_symbols[position] = targets[position - 1];
        }
        for (int position = 0; position < profile::segment; position++) {
            if (input_symbols[position] < 0 || input_symbols[position] >= profile::vocabulary)
                throw std::runtime_error("input symbol out of vocabulary");
        }
        const std::vector<float> embed = fixture.parameter(
            "embed", {profile::width, profile::vocabulary});
        std::vector<float> hidden(profile::segment * profile::width);
        for (int position = 0; position < profile::segment; position++)
            for (int feature = 0; feature < profile::width; feature++)
                hidden[position * profile::width + feature] = bf16(
                    bf16(embed[input_symbols[position] * profile::width + feature]) * 32.0f);
        write_f32(output_dir / "embedding_input.f32", hidden);

        const std::vector<float> shared_relative_bias = fixture.parameter(
            "b_r_0", {profile::position, profile::heads});
        const std::vector<float> attention_mask = fixture.state(
            "attention_mask", {profile::position, profile::segment});
        for (int query = 0; query < profile::segment; query++)
            for (int key = 0; key < profile::position; key++) {
                const int expected = key > profile::memory + query;
                if (static_cast<int>(attention_mask[query * profile::position + key]) != expected)
                    throw std::runtime_error("fixture causal attention mask mismatch");
            }
        for (int layer = 0; layer < profile::layers; layer++) {
            const std::vector<float> ln_g1 = fixture.parameter(
                layer_name("ln_g", layer * 2), {profile::width});
            const std::vector<float> ln_b1 = fixture.parameter(
                layer_name("ln_b", layer * 2), {profile::width});
            const std::vector<float> attention_input = rms_norm(hidden, ln_g1, ln_b1);
            write_f32(output_dir / ("layer_" + (layer < 10 ? std::string("0") : "") +
                                    std::to_string(layer) + "_attention_input.f32"), attention_input);

            const std::vector<float> wq = fixture.parameter(
                layer_name("w_q", layer), {profile::width, profile::width});
            std::vector<float> query = engine.multiply_libnc(
                wq, attention_input, profile::width, profile::width, profile::segment);
            round_bf16(query);

            const std::vector<float> memory_hidden = fixture.state(
                layer_name("mem_h", layer) + "_stream_0",
                {profile::width, 1, profile::memory});
            std::vector<float> all_hidden;
            all_hidden.reserve(profile::position * profile::width);
            all_hidden.insert(all_hidden.end(), memory_hidden.begin(), memory_hidden.end());
            all_hidden.insert(all_hidden.end(), attention_input.begin(), attention_input.end());
            const std::vector<float> wkv = fixture.parameter(
                layer_name("w_kv", layer), {2 * profile::width, profile::width});
            std::vector<float> key_value = engine.multiply_libnc(
                wkv, all_hidden, 2 * profile::width, profile::width, profile::position);
            round_bf16(key_value);

            std::vector<float> keys(profile::heads * profile::position * profile::key);
            std::vector<float> values(keys.size());
            std::vector<float> queries(profile::heads * profile::segment * profile::key);
            for (int head = 0; head < profile::heads; head++) {
                for (int position = 0; position < profile::position; position++) {
                    for (int dimension = 0; dimension < profile::key; dimension++) {
                        const size_t destination =
                            (head * profile::position + position) * profile::key + dimension;
                        keys[destination] = key_value[position * 2 * profile::width +
                            head * profile::key + dimension];
                        values[destination] = key_value[position * 2 * profile::width +
                            profile::width + head * profile::key + dimension];
                    }
                }
                for (int position = 0; position < profile::segment; position++)
                    for (int dimension = 0; dimension < profile::key; dimension++)
                        queries[(head * profile::segment + position) * profile::key + dimension] =
                            query[position * profile::width + head * profile::key + dimension];
            }
            write_f32(output_dir / ("layer_" + (layer < 10 ? std::string("0") : "") +
                                    std::to_string(layer) + "_key_state.f32"), keys);
            write_f32(output_dir / ("layer_" + (layer < 10 ? std::string("0") : "") +
                                    std::to_string(layer) + "_value_state.f32"), values);

            const std::vector<float> relative_weight = fixture.parameter(
                layer_name("w_r", layer),
                {profile::key, profile::position, profile::heads});
            write_f32(output_dir / ("layer_" + (layer < 10 ? std::string("0") : "") +
                                    std::to_string(layer) + "_relative_weight.f32"), relative_weight);
            std::vector<float> relative_bias(
                profile::heads * profile::segment * profile::position);
            const float relative_bias_scale = bf16(std::sqrt(
                static_cast<float>(profile::key * profile::width)));
            for (int head = 0; head < profile::heads; head++)
                for (int q = 0; q < profile::segment; q++)
                    for (int key = 0; key < profile::position; key++)
                        relative_bias[(head * profile::segment + q) * profile::position + key] =
                            bf16(shared_relative_bias[head * profile::position + key] *
                                 relative_bias_scale);
            write_f32(output_dir / ("layer_" + (layer < 10 ? std::string("0") : "") +
                                    std::to_string(layer) + "_relative_bias.f32"), relative_bias);

            const std::vector<float> content = engine.multiply(
                keys, queries, profile::key, profile::position,
                profile::segment, profile::heads);
            const std::vector<float> raw_relative = engine.multiply(
                relative_weight, queries, profile::key, profile::position,
                profile::segment, profile::heads);
            std::vector<float> scores(content.size());
            const float inverse_key_scale = bf16(1.0f / std::sqrt(static_cast<float>(profile::key)));
            for (int head = 0; head < profile::heads; head++) {
                std::vector<float> padded(profile::segment * (profile::position + 1));
                for (int q = 0; q < profile::segment; q++)
                    for (int key = 0; key < profile::position; key++)
                        padded[q * (profile::position + 1) + key + 1] = bf16(
                            raw_relative[(head * profile::segment + q) * profile::position + key] +
                            relative_bias[(head * profile::segment + q) * profile::position + key]);
                for (int q = 0; q < profile::segment; q++) {
                    for (int key = 0; key < profile::position; key++) {
                        const size_t flat = profile::segment + q * profile::position + key;
                        const float shifted = padded[flat];
                        const size_t destination =
                            (head * profile::segment + q) * profile::position + key;
                        float score = bf16(bf16(content[destination] + shifted) * inverse_key_scale);
                        if (key > profile::memory + q)
                            score = -std::numeric_limits<float>::infinity();
                        scores[destination] = score;
                    }
                }
            }
            std::vector<float> attention = softmax_rows(std::move(scores), profile::position);
            write_f32(output_dir / ("layer_" + (layer < 10 ? std::string("0") : "") +
                                    std::to_string(layer) + "_attention_probability.f32"), attention);

            std::vector<float> value_matrix(profile::heads * profile::key * profile::position);
            for (int head = 0; head < profile::heads; head++)
                for (int dimension = 0; dimension < profile::key; dimension++)
                    for (int key = 0; key < profile::position; key++)
                        value_matrix[(head * profile::key + dimension) * profile::position + key] =
                            values[(head * profile::position + key) * profile::key + dimension];
            std::vector<float> attended = engine.multiply(
                value_matrix, attention, profile::position, profile::key,
                profile::segment, profile::heads);
            round_bf16(attended);
            std::vector<float> merged_attention(hidden.size());
            for (int position = 0; position < profile::segment; position++)
                for (int head = 0; head < profile::heads; head++)
                    for (int dimension = 0; dimension < profile::key; dimension++) {
                        const size_t destination = position * profile::width +
                            head * profile::key + dimension;
                        const size_t source = (head * profile::segment + position) *
                            profile::key + dimension;
                        merged_attention[destination] = attended[source];
                    }
            std::vector<float> attention_output = engine.multiply_libnc(
                fixture.parameter(layer_name("w_o", layer),
                                  {profile::width, profile::width}),
                merged_attention, profile::width, profile::width, profile::segment);
            round_bf16(attention_output);
            std::vector<float> attention_residual(hidden.size());
            for (size_t index = 0; index < hidden.size(); index++)
                attention_residual[index] = bf16(hidden[index] + attention_output[index]);
            const std::string layer_prefix = "layer_" +
                (layer < 10 ? std::string("0") : "") + std::to_string(layer);
            write_f32(output_dir / (layer_prefix + "_attention_residual.f32"), attention_residual);
            write_f32(output_dir / (layer_prefix + "_attention_output.f32"), attention_residual);

            const std::vector<float> ln_g2 = fixture.parameter(
                layer_name("ln_g", layer * 2 + 1), {profile::width});
            const std::vector<float> ln_b2 = fixture.parameter(
                layer_name("ln_b", layer * 2 + 1), {profile::width});
            const std::vector<float> feedforward_input = rms_norm(
                attention_residual, ln_g2, ln_b2);
            const std::vector<float> ff1 = fixture.parameter(
                layer_name("ff1", layer), {2 * profile::inner, profile::width});
            std::vector<float> ff1_output = engine.multiply_libnc(
                ff1, feedforward_input, 2 * profile::inner, profile::width,
                profile::segment);
            add_bias_round(
                ff1_output,
                fixture.parameter(layer_name("ff_bias1", layer), {2 * profile::inner}),
                2 * profile::inner, true);
            write_f32(output_dir / (layer_prefix + "_ff1_output.f32"), ff1_output);
            std::vector<float> geglu(profile::segment * profile::inner);
            for (int position = 0; position < profile::segment; position++)
                for (int index = 0; index < profile::inner; index++)
                    geglu[position * profile::inner + index] = bf16(
                        libnc_gelu(ff1_output[position * 2 * profile::inner + index]) *
                        ff1_output[position * 2 * profile::inner + profile::inner + index]);
            write_f32(output_dir / (layer_prefix + "_geglu_output.f32"), geglu);
            const std::vector<float> ff2 = fixture.parameter(
                layer_name("ff2", layer), {profile::width, profile::inner});
            std::vector<float> feedforward = engine.multiply_libnc(
                ff2, geglu, profile::width, profile::inner, profile::segment);
            add_bias_round(
                feedforward,
                fixture.parameter(layer_name("ff_bias2", layer), {profile::width}),
                profile::width, true);
            std::vector<float> feedforward_residual(hidden.size());
            for (size_t index = 0; index < hidden.size(); index++)
                feedforward_residual[index] = bf16(attention_residual[index] + feedforward[index]);
            write_f32(output_dir / (layer_prefix + "_feedforward_residual.f32"),
                      feedforward_residual);
            write_f32(output_dir / (layer_prefix + "_layer_hidden.f32"),
                      feedforward_residual);
            hidden = std::move(feedforward_residual);
        }

        const std::vector<float> final_hidden = rms_norm(
            hidden,
            fixture.parameter("ln_g_40", {profile::width}),
            fixture.parameter("ln_b_40", {profile::width}));
        write_f32(output_dir / "final_hidden.f32", final_hidden);
        std::vector<float> logits = engine.multiply_libnc(
            fixture.parameter("embed_out", {profile::vocabulary, profile::width}),
            final_hidden, profile::vocabulary, profile::width, profile::segment);
        add_bias_round(logits, fixture.parameter("out_bias", {profile::vocabulary}),
                       profile::vocabulary, true);
        write_f32(output_dir / "logits.f32", logits);
        const std::vector<float> probabilities = softmax_rows(logits, profile::vocabulary);
        write_f32(output_dir / "output.f32", probabilities);
        write_tree_path(output_dir / "tree_path.u32le", probabilities, targets);
        std::ofstream(output_dir / "complete.marker") << "COMPLETE\n";
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "profile forward parity failed: %s\n", error.what());
        return 1;
    }
}
