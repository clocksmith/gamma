#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

static uint16_t float_to_bf16(float value)
{
    union {
        float f;
        uint32_t u;
    } bits = { value };
    uint32_t lsb = (bits.u >> 16) & 1u;
    return (uint16_t)((bits.u + 0x7fffu + lsb) >> 16);
}

int main(int argc, char **argv)
{
    NCContext *context;
    NCDevice *device;
    NCTensor *input, *converted;
    NCTensorData input_data, converted_data;
    NCTypeEnum output_type;
    size_t rows, columns, length, index, raw_size;
    uint16_t *values;
    uint8_t *raw;

    if (argc != 5) {
        fprintf(stderr, "usage: %s TYPE ROWS COLUMNS OUTPUT\n", argv[0]);
        return 2;
    }
    output_type = (NCTypeEnum)strtol(argv[1], NULL, 0);
    rows = (size_t)strtoull(argv[2], NULL, 0);
    columns = (size_t)strtoull(argv[3], NULL, 0);
    length = rows * columns;
    context = nc_context_init(1);
    if (context == NULL)
        return 1;
    nc_set_reproducible(context, TRUE);
    device = nc_new_cpu_device(context);
    input = nc_new_tensor_2d(device, NC_TYPE_BF16, rows, columns);
    if (input == NULL || nc_tensor_get_data(&input_data, input) == NULL)
        return 1;
    values = input_data.data;
    for (index = 0; index < length; index++) {
        int numerator = (int)((index * 37 + 11) % 509) - 254;
        values[index] = float_to_bf16((float)numerator / 127.0f);
    }
    converted = nc_convert(nc_dup_tensor(input), output_type);
    if (converted == NULL ||
        nc_tensor_get_data(&converted_data, converted) == NULL)
        return 1;
    raw_size = (size_t)nc_tensor_get_buffer_size(converted);
    raw = converted_data.data;
    fprintf(stderr,
            "type=%d item_type=%d item_size=%zu buffer=%zu dims=%d dim0=%zu stride0=%zu tensor_stride=%zu n_strides=%zu\n",
            (int)output_type, (int)converted_data.item_type,
            converted_data.item_size, raw_size, converted_data.n_dims,
            converted_data.dims[0], converted_data.strides[0],
            converted_data.stride, converted_data.n_strides);
    FILE *output = fopen(argv[4], "wb");
    if (output == NULL || fwrite(raw, 1, raw_size, output) != raw_size ||
        fclose(output) != 0)
        return 1;
    nc_free_tensor(converted);
    nc_free_tensor(input);
    nc_context_end(context);
    return 0;
}
