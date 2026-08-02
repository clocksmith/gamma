#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

#define OUTPUTS 256
#define INPUTS 32
#define COLUMNS 4

static NCTensor *left_gradient;
static NCTensor *right_gradient;

static float *element_2d(NCTensorData *data, size_t row, size_t column)
{
    return (float *)((uint8_t *)data->data +
                     row * data->strides[0] +
                     column * data->strides[1]);
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
    if (column_index != NULL) {
        fprintf(stderr, "unexpected sparse matrix gradient\n");
        abort();
    }
    if (opaque == (void *)(uintptr_t)1) {
        if (left_gradient != NULL)
            abort();
        left_gradient = gradient;
    } else if (opaque == (void *)(uintptr_t)2) {
        if (right_gradient != NULL)
            abort();
        right_gradient = gradient;
    } else {
        fprintf(stderr, "unexpected matrix gradient identity\n");
        abort();
    }
}

int main(int argc, char **argv)
{
    NCContext *context;
    NCDevice *device;
    NCTensor *left, *right, *upstream, *output, *loss;
    NCTensorData left_data, right_data, upstream_data;
    char path[1024];
    size_t column, input, row;

    if (argc != 2) {
        fprintf(stderr, "usage: %s OUTPUT_DIRECTORY\n", argv[0]);
        return 2;
    }
    context = nc_context_init(1);
    if (context == NULL)
        return 1;
    nc_set_reproducible(context, TRUE);
    device = nc_new_cpu_device(context);
    left = nc_new_tensor_2d(device, NC_TYPE_F32, OUTPUTS, INPUTS);
    right = nc_new_tensor_2d(device, NC_TYPE_F32, INPUTS, COLUMNS);
    upstream = nc_new_tensor_2d(device, NC_TYPE_F32, OUTPUTS, COLUMNS);
    if (left == NULL || right == NULL || upstream == NULL ||
        nc_tensor_get_data(&left_data, left) == NULL ||
        nc_tensor_get_data(&right_data, right) == NULL ||
        nc_tensor_get_data(&upstream_data, upstream) == NULL)
        return 1;

    for (input = 0; input < INPUTS; input++) {
        for (row = 0; row < OUTPUTS; row++) {
            int value = (int)((row * 37 + input * 13) % 257) - 128;
            *element_2d(&left_data, row, input) = (float)value / 257.0f;
        }
    }
    for (column = 0; column < COLUMNS; column++) {
        for (input = 0; input < INPUTS; input++) {
            int value = (int)((input * 19 + column * 23) % 67) - 33;
            *element_2d(&right_data, input, column) = (float)value / 41.0f;
        }
    }
    for (column = 0; column < COLUMNS; column++) {
        float total = 0.0f;
        for (row = 0; row + 1 < OUTPUTS; row++) {
            int value = (int)((row * 29 + column * 17) % 251) - 125;
            float item = (float)value / 8192.0f;
            *element_2d(&upstream_data, row, column) = item;
            total += item;
        }
        *element_2d(&upstream_data, OUTPUTS - 1, column) = -total;
    }

    left = nc_set_param(left, (void *)(uintptr_t)1);
    right = nc_set_param(right, (void *)(uintptr_t)2);
    output = nc_matmul(nc_dup_tensor(left), nc_dup_tensor(right));
    loss = nc_sum(nc_mul(nc_dup_tensor(output), upstream));
    nc_backward(loss, nc_new_f32(device, 1.0f), capture_gradient, 0);
    if (left_gradient == NULL || right_gradient == NULL)
        return 1;

    snprintf(path, sizeof(path), "%s/output.bin", argv[1]);
    if (write_tensor(path, output) != 0)
        return 1;
    snprintf(path, sizeof(path), "%s/left_gradient.bin", argv[1]);
    if (write_tensor(path, left_gradient) != 0)
        return 1;
    snprintf(path, sizeof(path), "%s/right_gradient.bin", argv[1]);
    if (write_tensor(path, right_gradient) != 0)
        return 1;

    nc_free_tensor(left_gradient);
    nc_free_tensor(right_gradient);
    nc_free_tensor(loss);
    nc_free_tensor(output);
    nc_free_tensor(right);
    nc_free_tensor(left);
    nc_context_end(context);
    return 0;
}
