#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

static uint16_t float_to_bf16(float value)
{
    union { float f; uint32_t u; } bits = { value };
    uint32_t lsb = (bits.u >> 16) & 1u;
    return (uint16_t)((bits.u + 0x7fffu + lsb) >> 16);
}

int main(int argc, char **argv)
{
    NCContext *context;
    NCDevice *device;
    NCTensor *left, *right, *output;
    NCTensorData left_data, right_data, output_data;
    size_t outputs, inner, columns, index;

    if (argc != 5 && argc != 6) {
        fprintf(stderr,
                "usage: %s OUTPUTS INNER COLUMNS THREADS [REPRODUCIBLE]\n",
                argv[0]);
        return 2;
    }
    outputs = strtoull(argv[1], NULL, 0);
    inner = strtoull(argv[2], NULL, 0);
    columns = strtoull(argv[3], NULL, 0);
    context = nc_context_init(atoi(argv[4]));
    if (argc == 6)
        nc_set_reproducible(context, atoi(argv[5]) != 0);
    device = nc_new_cpu_device(context);
    left = nc_new_tensor_2d(device, NC_TYPE_BF16, outputs, inner);
    right = nc_new_tensor_2d(device, NC_TYPE_BF16, inner, columns);
    if (left == NULL || right == NULL ||
        nc_tensor_get_data(&left_data, left) == NULL ||
        nc_tensor_get_data(&right_data, right) == NULL)
        return 1;
    for (index = 0; index < outputs * inner; index++)
        ((uint16_t *)left_data.data)[index] =
            float_to_bf16((float)((int)(index % 251) - 125) / 127.0f);
    for (index = 0; index < inner * columns; index++)
        ((uint16_t *)right_data.data)[index] =
            float_to_bf16((float)((int)(index % 127) - 63) / 64.0f);
    output = nc_matmul(nc_dup_tensor(left), nc_dup_tensor(right));
    if (output == NULL || nc_tensor_get_data(&output_data, output) == NULL)
        return 1;
    fprintf(stderr, "output type=%d dims=%zu,%zu first=%a\n",
            output_data.item_type, output_data.dims[0], output_data.dims[1],
            ((float *)output_data.data)[0]);
    nc_free_tensor(output);
    nc_free_tensor(right);
    nc_free_tensor(left);
    nc_context_end(context);
    return 0;
}
