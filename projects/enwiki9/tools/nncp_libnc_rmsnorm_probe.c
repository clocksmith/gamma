#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

#define FEATURES 8
#define COLUMNS 5

static const float input_values[COLUMNS][FEATURES] = {
    {-3.0f, -1.0f, 0.0f, 1.0f, 2.0f, 4.0f, -2.0f, 0.5f},
    {0.001f, -0.002f, 0.003f, -0.004f, 0.0005f, -0.0015f, 0.0025f, -0.0035f},
    {12.0f, -9.0f, 7.0f, -5.0f, 3.0f, -1.0f, 0.25f, 15.0f},
    {-0.125f, 0.25f, -0.5f, 0.75f, -1.0f, 1.25f, -1.5f, 1.75f},
    {2.5f, 2.0f, 1.5f, 1.0f, -1.0f, -1.5f, -2.0f, -2.5f},
};

static const float upstream_values[COLUMNS][FEATURES] = {
    {0.5f, -0.75f, 1.0f, -1.25f, 1.5f, -1.75f, 2.0f, -2.25f},
    {-3.0f, 2.5f, -2.0f, 1.5f, -1.0f, 0.5f, 0.25f, -0.125f},
    {1.0f, 0.875f, 0.75f, 0.625f, 0.5f, 0.375f, 0.25f, 0.125f},
    {-0.25f, 0.5f, -0.75f, 1.0f, -1.25f, 1.5f, -1.75f, 2.0f},
    {2.25f, -2.0f, 1.75f, -1.5f, 1.25f, -1.0f, 0.75f, -0.5f},
};

static float captured_gradient[COLUMNS][FEATURES];

static float *element(NCTensorData *data, size_t feature, size_t column)
{
    uint8_t *base = data->data;
    return (float *)(base + feature * data->strides[0] +
                     column * data->strides[1]);
}

static void copy_gradient(void *opaque, NCTensor *gradient,
                          NCTensor *column_index)
{
    NCTensorData data;
    size_t column, feature;

    if (opaque != (void *)(uintptr_t)1 || column_index != NULL ||
        nc_tensor_get_data(&data, gradient) == NULL ||
        data.item_type != NC_TYPE_F32 || data.n_dims != 2 ||
        data.dims[0] != FEATURES || data.dims[1] != COLUMNS) {
        fprintf(stderr, "unexpected RMSNorm gradient tensor\n");
        abort();
    }
    for (column = 0; column < COLUMNS; column++) {
        for (feature = 0; feature < FEATURES; feature++) {
            captured_gradient[column][feature] =
                *element(&data, feature, column);
        }
    }
    nc_free_tensor(gradient);
}

int main(void)
{
    NCContext *context;
    NCDevice *device;
    NCTensor *input, *upstream, *output, *loss;
    NCTensorData input_data, upstream_data, output_data;
    float output_values[COLUMNS][FEATURES];
    size_t column, feature;

    context = nc_context_init(1);
    if (context == NULL)
        return 1;
    nc_set_reproducible(context, TRUE);
    device = nc_new_cpu_device(context);
    input = nc_new_tensor_2d(device, NC_TYPE_F32, FEATURES, COLUMNS);
    upstream = nc_new_tensor_2d(device, NC_TYPE_F32, FEATURES, COLUMNS);
    if (input == NULL || upstream == NULL ||
        nc_tensor_get_data(&input_data, input) == NULL ||
        nc_tensor_get_data(&upstream_data, upstream) == NULL) {
        fprintf(stderr, "cannot create RMSNorm probe tensors\n");
        return 1;
    }
    for (column = 0; column < COLUMNS; column++) {
        for (feature = 0; feature < FEATURES; feature++) {
            *element(&input_data, feature, column) =
                input_values[column][feature];
            *element(&upstream_data, feature, column) =
                upstream_values[column][feature];
        }
    }

    input = nc_set_param(input, (void *)(uintptr_t)1);
    output = nc_rms_norm(nc_dup_tensor(input), 1e-5f);
    if (output == NULL || nc_tensor_get_data(&output_data, output) == NULL) {
        fprintf(stderr, "nc_rms_norm failed\n");
        return 1;
    }
    for (column = 0; column < COLUMNS; column++) {
        for (feature = 0; feature < FEATURES; feature++) {
            output_values[column][feature] =
                *element(&output_data, feature, column);
        }
    }
    loss = nc_sum(nc_mul(nc_dup_tensor(output), nc_dup_tensor(upstream)));
    nc_backward(loss, nc_new_f32(device, 1.0f), copy_gradient, 0);

    fputs("{\"rows\":[", stdout);
    for (column = 0; column < COLUMNS; column++) {
        for (feature = 0; feature < FEATURES; feature++) {
            if (column != 0 || feature != 0)
                fputc(',', stdout);
            printf("{\"column\":%zu,\"feature\":%zu,\"x\":%.9g,"
                   "\"upstream\":%.9g,\"y\":%.9g,\"dx\":%.9g}",
                   column, feature, input_values[column][feature],
                   upstream_values[column][feature],
                   output_values[column][feature],
                   captured_gradient[column][feature]);
        }
    }
    fputs("]}\n", stdout);

    nc_free_tensor(loss);
    nc_free_tensor(output);
    nc_free_tensor(upstream);
    nc_free_tensor(input);
    nc_context_end(context);
    return 0;
}
