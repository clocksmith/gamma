#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>

#include "libnc.h"

static float *captured_gradient;
static size_t captured_count;

static void copy_gradient(void *opaque, NCTensor *gradient,
                          NCTensor *column_index)
{
    NCTensorData data;
    size_t i;

    (void)column_index;
    if (opaque != (void *)(uintptr_t)1) {
        fprintf(stderr, "unexpected gradient opaque pointer\n");
        abort();
    }
    if (nc_tensor_get_data(&data, gradient) == NULL ||
        data.item_type != NC_TYPE_F32 || data.n_dims != 1 ||
        data.dims[0] != captured_count) {
        fprintf(stderr, "unexpected gradient tensor\n");
        abort();
    }
    for (i = 0; i < captured_count; i++) {
        const uint8_t *address =
            (const uint8_t *)data.data + i * data.strides[0];
        captured_gradient[i] = *(const float *)address;
    }
    nc_free_tensor(gradient);
    if (column_index != NULL)
        nc_free_tensor(column_index);
}

int main(void)
{
    static const float input_values[] = {
        -8.0f, -6.0f, -5.0f, -4.0f, -3.0f, -2.5f, -2.0f, -1.75f,
        -1.5f, -1.25f, -1.0f, -0.875f, -0.75f, -0.625f, -0.5f,
        -0.375f, -0.25f, -0.125f, -0.0625f, -0.03125f, 0.0f,
        0.03125f, 0.0625f, 0.125f, 0.25f, 0.375f, 0.5f, 0.625f,
        0.75f, 0.875f, 1.0f, 1.25f, 1.5f, 1.75f, 2.0f, 2.5f,
        3.0f, 4.0f, 5.0f, 6.0f, 8.0f,
    };
    const size_t count = sizeof(input_values) / sizeof(input_values[0]);
    NCContext *context;
    NCDevice *device;
    NCTensor *input;
    NCTensor *output;
    NCTensor *loss;
    NCTensorData input_data;
    NCTensorData output_data;
    float *output_values;
    size_t i;

    context = nc_context_init(1);
    if (context == NULL) {
        fprintf(stderr, "nc_context_init failed\n");
        return 1;
    }
    nc_set_reproducible(context, TRUE);
    device = nc_new_cpu_device(context);
    input = nc_new_tensor_1d(device, NC_TYPE_F32, count);
    if (input == NULL || nc_tensor_get_data(&input_data, input) == NULL) {
        fprintf(stderr, "cannot create input tensor\n");
        return 1;
    }
    for (i = 0; i < count; i++) {
        uint8_t *address =
            (uint8_t *)input_data.data + i * input_data.strides[0];
        *(float *)address = input_values[i];
    }

    input = nc_set_param(input, (void *)(uintptr_t)1);
    output = nc_gelu(nc_dup_tensor(input));
    if (output == NULL || nc_tensor_get_data(&output_data, output) == NULL) {
        fprintf(stderr, "nc_gelu failed\n");
        return 1;
    }
    output_values = calloc(count, sizeof(*output_values));
    captured_gradient = calloc(count, sizeof(*captured_gradient));
    captured_count = count;
    if (output_values == NULL || captured_gradient == NULL)
        return 1;
    for (i = 0; i < count; i++) {
        const uint8_t *address =
            (const uint8_t *)output_data.data + i * output_data.strides[0];
        output_values[i] = *(const float *)address;
    }

    loss = nc_sum(nc_dup_tensor(output));
    nc_backward(loss, nc_new_f32(device, 1.0f), copy_gradient, 0);

    fputs("{\"rows\":[", stdout);
    for (i = 0; i < count; i++) {
        if (i != 0)
            fputc(',', stdout);
        printf("{\"x\":%.9g,\"y\":%.9g,\"dy\":%.9g}",
               input_values[i], output_values[i], captured_gradient[i]);
    }
    fputs("]}\n", stdout);

    free(captured_gradient);
    free(output_values);
    nc_free_tensor(loss);
    nc_free_tensor(output);
    nc_free_tensor(input);
    nc_context_end(context);
    return 0;
}
