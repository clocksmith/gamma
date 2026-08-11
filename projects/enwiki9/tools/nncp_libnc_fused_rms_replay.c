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

static int read_exact(const char *path, void *data, size_t bytes)
{
    FILE *input = fopen(path, "rb");
    int status;
    if (input == NULL) return -1;
    status = fread(data, 1, bytes, input) == bytes && fgetc(input) == EOF ? 0 : -1;
    if (fclose(input) != 0) status = -1;
    return status;
}

int main(int argc, char **argv)
{
    enum { WIDTH = 1024, ROWS = 64 };
    float *source = NULL;
    uint16_t *gain = NULL, *bias = NULL;
    NCContext *context = NULL;
    NCDevice *device = NULL;
    NCTensor *x = NULL, *w = NULL, *b = NULL, *y = NULL;
    NCTensorData xd, wd, bd, yd;
    FILE *output = NULL;
    size_t row, column;
    int status = 1;

    if (argc != 5) {
        fprintf(stderr, "usage: %s INPUT_F32 GAIN_BF16 BIAS_BF16 OUTPUT_F32\n", argv[0]);
        return 2;
    }
    source = malloc(sizeof(*source) * WIDTH * ROWS);
    gain = malloc(sizeof(*gain) * WIDTH);
    bias = malloc(sizeof(*bias) * WIDTH);
    if (source == NULL || gain == NULL || bias == NULL ||
        read_exact(argv[1], source, sizeof(*source) * WIDTH * ROWS) != 0 ||
        read_exact(argv[2], gain, sizeof(*gain) * WIDTH) != 0 ||
        read_exact(argv[3], bias, sizeof(*bias) * WIDTH) != 0)
        goto done;
    context = nc_context_init(4);
    if (context == NULL || (device = nc_new_cpu_device(context)) == NULL)
        goto done;
    x = nc_new_tensor_2d(device, NC_TYPE_BF16, WIDTH, ROWS);
    w = nc_new_tensor_1d(device, NC_TYPE_BF16, WIDTH);
    b = nc_new_tensor_1d(device, NC_TYPE_BF16, WIDTH);
    if (x == NULL || w == NULL || b == NULL ||
        nc_tensor_get_data(&xd, x) == NULL ||
        nc_tensor_get_data(&wd, w) == NULL ||
        nc_tensor_get_data(&bd, b) == NULL)
        goto done;
    for (column = 0; column < WIDTH; column++) {
        *(uint16_t *)((uint8_t *)wd.data + column * wd.strides[0]) = gain[column];
        *(uint16_t *)((uint8_t *)bd.data + column * bd.strides[0]) = bias[column];
        for (row = 0; row < ROWS; row++)
            *(uint16_t *)((uint8_t *)xd.data + column * xd.strides[0] +
                          row * xd.strides[1]) =
                f32_to_bf16(source[row * WIDTH + column]);
    }
    y = nc_fused_layer_norm(x, w, b, 1.0e-5f, FALSE);
    x = w = b = NULL;
    if (y == NULL || nc_tensor_get_data(&yd, y) == NULL ||
        yd.item_type != NC_TYPE_BF16)
        goto done;
    output = fopen(argv[4], "wb");
    if (output == NULL) goto done;
    for (row = 0; row < ROWS; row++)
        for (column = 0; column < WIDTH; column++) {
            const uint16_t raw = *(const uint16_t *)((const uint8_t *)yd.data +
                column * yd.strides[0] + row * yd.strides[1]);
            const float value = bf16_to_f32(raw);
            if (fwrite(&value, sizeof(value), 1, output) != 1) goto done;
        }
    if (fclose(output) != 0) {
        output = NULL;
        goto done;
    }
    output = NULL;
    status = 0;

done:
    if (output != NULL) fclose(output);
    if (y != NULL) nc_free_tensor(y);
    if (x != NULL) nc_free_tensor(x);
    if (w != NULL) nc_free_tensor(w);
    if (b != NULL) nc_free_tensor(b);
    if (context != NULL) nc_context_end(context);
    free(source);
    free(gain);
    free(bias);
    return status;
}
