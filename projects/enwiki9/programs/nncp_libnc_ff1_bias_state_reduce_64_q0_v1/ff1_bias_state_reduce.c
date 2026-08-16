#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libnc.h"

#define GAMMA_FEATURES 6144
#define GAMMA_STREAMS 32
#define GAMMA_STATES 64
#define GAMMA_ELEMENTS ((size_t)GAMMA_FEATURES * GAMMA_STREAMS * GAMMA_STATES)

static uint16_t *read_payload(const char *path)
{
    FILE *input;
    uint16_t *payload;

    input = fopen(path, "rb");
    if (input == NULL)
        return NULL;
    payload = malloc(GAMMA_ELEMENTS * sizeof(*payload));
    if (payload == NULL ||
        fread(payload, sizeof(*payload), GAMMA_ELEMENTS, input) !=
            GAMMA_ELEMENTS ||
        fgetc(input) != EOF || fclose(input) != 0) {
        free(payload);
        return NULL;
    }
    return payload;
}

static int write_gradient(const char *path, NCTensor *gradient)
{
    NCTensorData data;
    FILE *output;
    size_t feature;

    if (nc_tensor_get_data(&data, gradient) == NULL ||
        data.item_type != NC_TYPE_BF16 || data.item_size != 2 ||
        data.n_dims != 1 || data.dims[0] != GAMMA_FEATURES)
        return -1;
    output = fopen(path, "wb");
    if (output == NULL)
        return -1;
    for (feature = 0; feature < GAMMA_FEATURES; feature++) {
        const uint8_t *address =
            (const uint8_t *)data.data + feature * data.strides[0];
        if (fwrite(address, sizeof(uint16_t), 1, output) != 1) {
            fclose(output);
            return -1;
        }
    }
    return fclose(output) == 0 ? 0 : -1;
}

static int reduce_payload(const uint16_t *payload, const char *path,
                          int reverse_states, int negate)
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
        NCTensor *panel = nc_new_tensor_2d(
            device, NC_TYPE_BF16, GAMMA_FEATURES, GAMMA_STREAMS);
        NCTensorData data;
        size_t stream, feature;

        if (panel == NULL || nc_tensor_get_data(&data, panel) == NULL ||
            data.item_type != NC_TYPE_BF16 || data.item_size != 2 ||
            data.n_dims != 2 || data.dims[0] != GAMMA_FEATURES ||
            data.dims[1] != GAMMA_STREAMS) {
            if (panel != NULL)
                nc_free_tensor(panel);
            if (gradient != NULL)
                nc_free_tensor(gradient);
            nc_context_end(context);
            return -1;
        }
        for (stream = 0; stream < GAMMA_STREAMS; stream++) {
            for (feature = 0; feature < GAMMA_FEATURES; feature++) {
                const size_t source_index =
                    ((state * GAMMA_STREAMS + stream) * GAMMA_FEATURES) +
                    feature;
                uint16_t word = payload[source_index];
                uint8_t *address = (uint8_t *)data.data +
                    feature * data.strides[0] + stream * data.strides[1];
                if (negate)
                    word ^= UINT16_C(0x8000);
                memcpy(address, &word, sizeof(word));
            }
        }
        gradient = nc_reduce_sum(gradient, panel, 1);
        if (gradient == NULL) {
            nc_context_end(context);
            return -1;
        }
    }
    if (write_gradient(path, gradient) != 0) {
        nc_free_tensor(gradient);
        nc_context_end(context);
        return -1;
    }
    nc_free_tensor(gradient);
    nc_context_end(context);
    return 0;
}

int main(int argc, char **argv)
{
    uint16_t *payload;
    int status;

    if (argc != 5) {
        fprintf(stderr,
                "usage: ff1_bias_state_reduce INPUT TREATMENT REVERSE NEGATED\n");
        return 1;
    }
    payload = read_payload(argv[1]);
    if (payload == NULL) {
        fprintf(stderr, "cannot read exact FF1-output residual\n");
        return 1;
    }
    status = reduce_payload(payload, argv[2], 0, 0) != 0 ||
        reduce_payload(payload, argv[3], 1, 0) != 0 ||
        reduce_payload(payload, argv[4], 0, 1) != 0;
    free(payload);
    if (status) {
        fprintf(stderr, "LibNC FF1 bias state reduction failed\n");
        return 1;
    }
    return 0;
}
