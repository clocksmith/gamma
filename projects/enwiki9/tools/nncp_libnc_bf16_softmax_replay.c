#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libnc.h"

static uint16_t f32_to_bf16(float value)
{
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    bits += 0x7fffU + ((bits >> 16) & 1U);
    return (uint16_t)(bits >> 16);
}

static float bf16_to_f32(uint16_t value)
{
    uint32_t bits = (uint32_t)value << 16;
    float result;
    memcpy(&result, &bits, sizeof(result));
    return result;
}

static int parse_size(const char *text, size_t *value)
{
    char *end;
    unsigned long long parsed;
    errno = 0;
    parsed = strtoull(text, &end, 10);
    if (errno != 0 || *text == '\0' || *end != '\0' || parsed == 0)
        return -1;
    *value = (size_t)parsed;
    return (unsigned long long)*value == parsed ? 0 : -1;
}

int main(int argc, char **argv)
{
    FILE *input = NULL, *output = NULL;
    float *source = NULL;
    NCContext *context = NULL;
    NCDevice *device = NULL;
    NCTensor *tensor = NULL;
    NCTensorData data;
    size_t width, rows, count, row, column;
    int status = 1;

    if (argc != 5 || parse_size(argv[3], &width) != 0 ||
        parse_size(argv[4], &rows) != 0 || rows > SIZE_MAX / width) {
        fprintf(stderr, "usage: %s INPUT_F32 OUTPUT_F32 WIDTH ROWS\n", argv[0]);
        return 2;
    }
    count = width * rows;
    source = malloc(count * sizeof(*source));
    if (source == NULL) goto done;
    input = fopen(argv[1], "rb");
    if (input == NULL || fread(source, sizeof(*source), count, input) != count ||
        fgetc(input) != EOF)
        goto done;
    fclose(input);
    input = NULL;

    context = nc_context_init(4);
    if (context == NULL) goto done;
    device = nc_new_cpu_device(context);
    if (device == NULL) goto done;
    tensor = nc_new_tensor_2d(device, NC_TYPE_BF16, width, rows);
    if (tensor == NULL || nc_tensor_get_data(&data, tensor) == NULL ||
        data.item_type != NC_TYPE_BF16)
        goto done;
    for (row = 0; row < rows; row++) {
        for (column = 0; column < width; column++) {
            uint8_t *address = (uint8_t *)data.data +
                column * data.strides[0] + row * data.strides[1];
            *(uint16_t *)address = f32_to_bf16(source[row * width + column]);
        }
    }
    tensor = nc_soft_max(tensor);
    if (tensor == NULL || nc_tensor_get_data(&data, tensor) == NULL ||
        data.item_type != NC_TYPE_BF16)
        goto done;

    output = fopen(argv[2], "wb");
    if (output == NULL) goto done;
    for (row = 0; row < rows; row++) {
        for (column = 0; column < width; column++) {
            const uint8_t *address = (const uint8_t *)data.data +
                column * data.strides[0] + row * data.strides[1];
            float value = bf16_to_f32(*(const uint16_t *)address);
            if (fwrite(&value, sizeof(value), 1, output) != 1) goto done;
        }
    }
    if (fclose(output) != 0) {
        output = NULL;
        goto done;
    }
    output = NULL;
    status = 0;

done:
    if (output != NULL) fclose(output);
    if (input != NULL) fclose(input);
    if (tensor != NULL) nc_free_tensor(tensor);
    if (context != NULL) nc_context_end(context);
    free(source);
    return status;
}
