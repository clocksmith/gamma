#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

#define FEATURES 32
#define CLASSES 256
#define STATES 4

static NCTensor *tail_gradient;

static int read_axis(FILE *input, const NCTensorData *data,
                     uint8_t *base, int axis)
{
    size_t index;

    if (axis < 0)
        return fread(base, data->item_size, 1, input) == 1 ? 0 : -1;
    for (index = 0; index < data->dims[axis]; index++) {
        if (read_axis(input, data, base + index * data->strides[axis],
                      axis - 1) != 0)
            return -1;
    }
    return 0;
}

static int load_tensor(NCTensor *tensor, const char *path)
{
    NCTensorData data;
    FILE *input;
    int status;

    if (nc_tensor_get_data(&data, tensor) == NULL ||
        data.item_type != NC_TYPE_F32)
        return -1;
    input = fopen(path, "rb");
    if (input == NULL)
        return -1;
    status = read_axis(input, &data, data.data, data.n_dims - 1);
    if (status == 0 && fgetc(input) != EOF)
        status = -1;
    if (fclose(input) != 0)
        status = -1;
    return status;
}

static int write_axis(FILE *output, const NCTensorData *data,
                      const uint8_t *base, int axis)
{
    size_t index;

    if (axis < 0)
        return fwrite(base, data->item_size, 1, output) == 1 ? 0 : -1;
    for (index = 0; index < data->dims[axis]; index++) {
        if (write_axis(output, data, base + index * data->strides[axis],
                       axis - 1) != 0)
            return -1;
    }
    return 0;
}

static int write_tensor(const char *path, NCTensor *tensor)
{
    NCTensorData data;
    FILE *output;
    int status;

    if (nc_tensor_get_data(&data, tensor) == NULL ||
        data.item_type != NC_TYPE_F32)
        return -1;
    output = fopen(path, "wb");
    if (output == NULL)
        return -1;
    status = write_axis(output, &data, data.data, data.n_dims - 1);
    if (fclose(output) != 0)
        status = -1;
    return status;
}

static void capture_gradient(void *opaque, NCTensor *gradient,
                             NCTensor *column_index)
{
    if (opaque != (void *)(uintptr_t)1 || column_index != NULL ||
        tail_gradient != NULL) {
        fprintf(stderr, "unexpected tail gradient callback\n");
        abort();
    }
    tail_gradient = gradient;
}

static NCTensor *tail_forward(NCTensor *pre_final, NCTensor *delta,
                              NCTensor *gain, NCTensor *bias,
                              NCTensor *embed_out, NCTensor *out_bias)
{
    NCTensor *value;

    value = nc_add(pre_final, nc_dup_tensor(delta));
    value = nc_rms_norm(value, 1e-5f);
    value = nc_add(nc_mul(value, nc_dup_tensor(gain)),
                   nc_dup_tensor(bias));
    value = nc_matmul(nc_dup_tensor(embed_out), value);
    value = nc_add(value, nc_dup_tensor(out_bias));
    value = nc_convert(value, NC_TYPE_F32);
    value = nc_reshape_3d(value, CLASSES, 1, 1);
    return nc_soft_max(value);
}

int main(int argc, char **argv)
{
    static const int targets[STATES] = {60, 109, 101, 100};
    NCContext *context;
    NCDevice *device;
    NCTensor *delta, *gain, *bias, *embed_out, *out_bias;
    NCTensor *outputs[STATES], *output, *expected, *loss;
    NCNode *output_node;
    char path[4096];
    size_t state;

    if (argc != 10) {
        fprintf(stderr,
                "usage: %s PRE0 PRE1 PRE2 PRE3 GAIN BIAS EMBED_OUT "
                "OUT_BIAS OUTPUT_DIRECTORY\n",
                argv[0]);
        return 2;
    }
    context = nc_context_init(1);
    if (context == NULL)
        return 1;
    nc_set_reproducible(context, TRUE);
    device = nc_new_cpu_device(context);

    delta = nc_new_tensor_1d(device, NC_TYPE_F32, FEATURES);
    gain = nc_new_tensor_1d(device, NC_TYPE_F32, FEATURES);
    bias = nc_new_tensor_1d(device, NC_TYPE_F32, FEATURES);
    embed_out = nc_new_tensor_2d(device, NC_TYPE_F32, CLASSES, FEATURES);
    out_bias = nc_new_tensor_1d(device, NC_TYPE_F32, CLASSES);
    expected = nc_new_tensor_2d(device, NC_TYPE_I32, 1, STATES);
    if (delta == NULL || gain == NULL || bias == NULL ||
        embed_out == NULL || out_bias == NULL || expected == NULL)
        return 1;
    nc_tensor_set_f32(delta, 0.0f);
    if (load_tensor(gain, argv[5]) != 0 ||
        load_tensor(bias, argv[6]) != 0 ||
        load_tensor(embed_out, argv[7]) != 0 ||
        load_tensor(out_bias, argv[8]) != 0) {
        fprintf(stderr, "cannot load tail weights\n");
        return 1;
    }
    for (state = 0; state < STATES; state++)
        nc_set1_i32_2d(expected, 0, state, targets[state]);

    delta = nc_set_param(delta, (void *)(uintptr_t)1);
    for (state = 0; state < STATES; state++) {
        NCTensor *pre_final =
            nc_new_tensor_2d(device, NC_TYPE_F32, FEATURES, 1);
        if (pre_final == NULL || load_tensor(pre_final, argv[1 + state]) != 0) {
            fprintf(stderr, "cannot load pre-final state %zu\n", state);
            return 1;
        }
        outputs[state] = tail_forward(pre_final, delta, gain, bias,
                                      embed_out, out_bias);
        if (outputs[state] == NULL)
            return 1;
    }
    output = nc_concat(outputs, STATES, 2);
    if (output == NULL)
        return 1;
    output_node = nc_get_node(output);
    nc_concat_optimization(context, &output_node, 1);

    loss = nc_indexed_log(nc_dup_tensor(output), nc_dup_tensor(expected));
    loss = nc_sum(loss);
    loss = nc_mul(loss, nc_new_f32(device, -1.0f / STATES));
    nc_backward(loss, nc_new_f32(device, 1.0f), capture_gradient, 0);
    if (tail_gradient == NULL)
        return 1;

    snprintf(path, sizeof(path), "%s/probabilities.bin", argv[9]);
    if (write_tensor(path, output) != 0)
        return 1;
    snprintf(path, sizeof(path), "%s/tail_gradient.bin", argv[9]);
    if (write_tensor(path, tail_gradient) != 0)
        return 1;

    nc_free_tensor(tail_gradient);
    nc_free_tensor(loss);
    nc_free_tensor(output);
    nc_free_tensor(expected);
    nc_free_tensor(out_bias);
    nc_free_tensor(embed_out);
    nc_free_tensor(bias);
    nc_free_tensor(gain);
    nc_free_tensor(delta);
    nc_context_end(context);
    return 0;
}
