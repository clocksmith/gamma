#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

#define CLASSES 256
#define COLUMNS 4

static NCTensor *logit_gradient;

static float *element_3d(NCTensorData *data, size_t class_index,
                         size_t stream, size_t column)
{
    return (float *)((uint8_t *)data->data +
                     class_index * data->strides[0] +
                     stream * data->strides[1] +
                     column * data->strides[2]);
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
        logit_gradient != NULL) {
        fprintf(stderr, "unexpected loss-graph gradient\n");
        abort();
    }
    logit_gradient = gradient;
}

int main(int argc, char **argv)
{
    static const int targets[COLUMNS] = {60, 109, 101, 100};
    NCContext *context;
    NCDevice *device;
    NCTensor *logits, *expected, *probabilities, *loss;
    NCTensorData logits_data;
    char path[1024];
    size_t class_index, column;

    if (argc != 2) {
        fprintf(stderr, "usage: %s OUTPUT_DIRECTORY\n", argv[0]);
        return 2;
    }
    context = nc_context_init(1);
    if (context == NULL)
        return 1;
    nc_set_reproducible(context, TRUE);
    device = nc_new_cpu_device(context);
    logits = nc_new_tensor_3d(device, NC_TYPE_F32, CLASSES, 1, COLUMNS);
    expected = nc_new_tensor_2d(device, NC_TYPE_I32, 1, COLUMNS);
    if (logits == NULL || expected == NULL ||
        nc_tensor_get_data(&logits_data, logits) == NULL)
        return 1;
    for (column = 0; column < COLUMNS; column++) {
        for (class_index = 0; class_index < CLASSES; class_index++) {
            int value =
                (int)((class_index * 37 + column * 53) % 509) - 254;
            *element_3d(&logits_data, class_index, 0, column) =
                (float)value / 128.0f;
        }
        nc_set1_i32_2d(expected, 0, column, targets[column]);
    }

    logits = nc_set_param(logits, (void *)(uintptr_t)1);
    probabilities = nc_soft_max(nc_dup_tensor(logits));
    loss = nc_indexed_log(nc_dup_tensor(probabilities),
                          nc_dup_tensor(expected));
    loss = nc_sum(loss);
    loss = nc_mul(loss, nc_new_f32(device, -1.0f / COLUMNS));
    nc_backward(loss, nc_new_f32(device, 1.0f), capture_gradient, 0);
    if (logit_gradient == NULL)
        return 1;

    snprintf(path, sizeof(path), "%s/probabilities.bin", argv[1]);
    if (write_tensor(path, probabilities) != 0)
        return 1;
    snprintf(path, sizeof(path), "%s/logit_gradient.bin", argv[1]);
    if (write_tensor(path, logit_gradient) != 0)
        return 1;

    nc_free_tensor(logit_gradient);
    nc_free_tensor(loss);
    nc_free_tensor(probabilities);
    nc_free_tensor(expected);
    nc_free_tensor(logits);
    nc_context_end(context);
    return 0;
}
