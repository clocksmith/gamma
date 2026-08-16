#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libnc.h"

#define GAMMA_SLICE_OUTPUTS 128
#define GAMMA_FULL_OUTPUTS 6144
#define GAMMA_INPUTS 1024
#define GAMMA_STREAMS 32
#define GAMMA_STATES 64
#define GAMMA_SAMPLES (GAMMA_STREAMS * GAMMA_STATES)
#define GAMMA_INPUT_ELEMENTS ((size_t)GAMMA_INPUTS * GAMMA_SAMPLES)
#define GAMMA_RESIDUAL_ELEMENTS ((size_t)GAMMA_FULL_OUTPUTS * GAMMA_SAMPLES)

static uint16_t *read_words(const char *path, size_t count)
{
    FILE *input;
    uint16_t *payload;

    input = fopen(path, "rb");
    if (input == NULL)
        return NULL;
    payload = malloc(count * sizeof(*payload));
    if (payload == NULL ||
        fread(payload, sizeof(*payload), count, input) != count ||
        fgetc(input) != EOF || fclose(input) != 0) {
        free(payload);
        return NULL;
    }
    return payload;
}

static int store_word(NCTensorData *data, size_t row, size_t column,
                      uint16_t word)
{
    uint8_t *address;

    if (data->item_type != NC_TYPE_BF16 || data->item_size != 2 ||
        data->n_dims != 2 || row >= data->dims[0] ||
        column >= data->dims[1])
        return -1;
    address = (uint8_t *)data->data + row * data->strides[0] +
        column * data->strides[1];
    memcpy(address, &word, sizeof(word));
    return 0;
}

static int write_gradient(const char *path, NCTensor *gradient)
{
    NCTensorData data;
    FILE *output;
    size_t input, feature;

    if (nc_tensor_get_data(&data, gradient) == NULL ||
        data.item_type != NC_TYPE_BF16 || data.item_size != 2 ||
        data.n_dims != 2 || data.dims[0] != GAMMA_SLICE_OUTPUTS ||
        data.dims[1] != GAMMA_INPUTS)
        return -1;
    output = fopen(path, "wb");
    if (output == NULL)
        return -1;
    for (input = 0; input < GAMMA_INPUTS; input++) {
        for (feature = 0; feature < GAMMA_SLICE_OUTPUTS; feature++) {
            const uint8_t *address = (const uint8_t *)data.data +
                feature * data.strides[0] + input * data.strides[1];
            if (fwrite(address, sizeof(uint16_t), 1, output) != 1) {
                fclose(output);
                return -1;
            }
        }
    }
    return fclose(output) == 0 ? 0 : -1;
}

static int state_schedule(const uint16_t *inputs, const uint16_t *residuals,
                          const char *path, int reverse_states, int negate)
{
    NCContext *context;
    NCDevice *device;
    NCTensor *gradient = NULL;
    size_t step;

    context = nc_context_init(1);
    if (context == NULL)
        return -1;
    nc_set_reproducible(context, TRUE);
    device = nc_new_cpu_device(context);
    if (device == NULL) {
        nc_context_end(context);
        return -1;
    }
    for (step = 0; step < GAMMA_STATES; step++) {
        const size_t state = reverse_states ? GAMMA_STATES - 1 - step : step;
        NCTensor *residual = nc_new_tensor_2d(
            device, NC_TYPE_BF16, GAMMA_SLICE_OUTPUTS, GAMMA_STREAMS);
        NCTensor *input = nc_new_tensor_2d(
            device, NC_TYPE_BF16, GAMMA_INPUTS, GAMMA_STREAMS);
        NCTensorData residual_data, input_data;
        size_t stream, feature;

        if (residual == NULL || input == NULL ||
            nc_tensor_get_data(&residual_data, residual) == NULL ||
            nc_tensor_get_data(&input_data, input) == NULL) {
            nc_context_end(context);
            return -1;
        }
        for (stream = 0; stream < GAMMA_STREAMS; stream++) {
            const size_t sample = state * GAMMA_STREAMS + stream;
            for (feature = 0; feature < GAMMA_SLICE_OUTPUTS; feature++) {
                uint16_t word = residuals[
                    sample * GAMMA_FULL_OUTPUTS + feature];
                if (negate)
                    word ^= UINT16_C(0x8000);
                if (store_word(&residual_data, feature, stream, word) != 0) {
                    nc_context_end(context);
                    return -1;
                }
            }
            for (feature = 0; feature < GAMMA_INPUTS; feature++) {
                const uint16_t word = inputs[sample * GAMMA_INPUTS + feature];
                if (store_word(&input_data, feature, stream, word) != 0) {
                    nc_context_end(context);
                    return -1;
                }
            }
        }
        gradient = nc_matmul_add2(
            residual, input, gradient, FALSE, TRUE, 1.0f, 0);
        if (gradient == NULL) {
            nc_context_end(context);
            return -1;
        }
    }
    if (write_gradient(path, gradient) != 0) {
        nc_context_end(context);
        return -1;
    }
    nc_free_tensor(gradient);
    nc_context_end(context);
    return 0;
}

static int flat_schedule(const uint16_t *inputs, const uint16_t *residuals,
                         const char *path)
{
    NCContext *context;
    NCDevice *device;
    NCTensor *residual, *input, *gradient;
    NCTensorData residual_data, input_data;
    size_t sample, feature;

    context = nc_context_init(1);
    if (context == NULL)
        return -1;
    nc_set_reproducible(context, TRUE);
    device = nc_new_cpu_device(context);
    if (device == NULL) {
        nc_context_end(context);
        return -1;
    }
    residual = nc_new_tensor_2d(
        device, NC_TYPE_BF16, GAMMA_SLICE_OUTPUTS, GAMMA_SAMPLES);
    input = nc_new_tensor_2d(
        device, NC_TYPE_BF16, GAMMA_INPUTS, GAMMA_SAMPLES);
    if (residual == NULL || input == NULL ||
        nc_tensor_get_data(&residual_data, residual) == NULL ||
        nc_tensor_get_data(&input_data, input) == NULL) {
        nc_context_end(context);
        return -1;
    }
    for (sample = 0; sample < GAMMA_SAMPLES; sample++) {
        for (feature = 0; feature < GAMMA_SLICE_OUTPUTS; feature++) {
            if (store_word(
                    &residual_data, feature, sample,
                    residuals[sample * GAMMA_FULL_OUTPUTS + feature]) != 0) {
                nc_context_end(context);
                return -1;
            }
        }
        for (feature = 0; feature < GAMMA_INPUTS; feature++) {
            if (store_word(&input_data, feature, sample,
                           inputs[sample * GAMMA_INPUTS + feature]) != 0) {
                nc_context_end(context);
                return -1;
            }
        }
    }
    gradient = nc_matmul_add2(
        residual, input, NULL, FALSE, TRUE, 1.0f, 0);
    if (gradient == NULL || write_gradient(path, gradient) != 0) {
        nc_context_end(context);
        return -1;
    }
    nc_free_tensor(gradient);
    nc_context_end(context);
    return 0;
}

int main(int argc, char **argv)
{
    uint16_t *inputs, *residuals;
    int failed;

    if (argc != 7) {
        fprintf(stderr,
                "usage: ff1_weight_slice_schedule INPUT RESIDUAL "
                "TREATMENT FLAT REVERSE NEGATED\n");
        return 1;
    }
    inputs = read_words(argv[1], GAMMA_INPUT_ELEMENTS);
    residuals = read_words(argv[2], GAMMA_RESIDUAL_ELEMENTS);
    if (inputs == NULL || residuals == NULL) {
        free(inputs);
        free(residuals);
        fprintf(stderr, "cannot read exact FF1 matrix-gradient inputs\n");
        return 1;
    }
    failed = state_schedule(inputs, residuals, argv[3], 0, 0) != 0 ||
        flat_schedule(inputs, residuals, argv[4]) != 0 ||
        state_schedule(inputs, residuals, argv[5], 1, 0) != 0 ||
        state_schedule(inputs, residuals, argv[6], 0, 1) != 0;
    free(inputs);
    free(residuals);
    if (failed) {
        fprintf(stderr, "LibNC FF1 weight-slice schedule failed\n");
        return 1;
    }
    return 0;
}
