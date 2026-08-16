#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libnc.h"

#define GAMMA_ELEMENTS ((size_t)2097152)

static const char *gamma_output_path;

static NCTensor *gamma_read_tensor(NCDevice *device, const char *path,
                                   int negate)
{
    FILE *input;
    uint16_t *words;
    NCTensor *tensor;
    NCTensorData data;
    size_t index;

    input = fopen(path, "rb");
    words = malloc(GAMMA_ELEMENTS * sizeof(*words));
    if (input == NULL || words == NULL) {
        if (input != NULL)
            fclose(input);
        free(words);
        return NULL;
    }
    if (fread(words, sizeof(*words), GAMMA_ELEMENTS, input) != GAMMA_ELEMENTS ||
        fgetc(input) != EOF) {
        fclose(input);
        free(words);
        return NULL;
    }
    if (fclose(input) != 0) {
        free(words);
        return NULL;
    }
    tensor = nc_new_tensor_1d(device, NC_TYPE_BF16, GAMMA_ELEMENTS);
    if (tensor == NULL || nc_tensor_get_data(&data, tensor) == NULL ||
        data.item_type != NC_TYPE_BF16 || data.item_size != 2 ||
        data.n_dims != 1 || data.dims[0] != GAMMA_ELEMENTS) {
        if (tensor != NULL)
            nc_free_tensor(tensor);
        free(words);
        return NULL;
    }
    for (index = 0; index < GAMMA_ELEMENTS; index++) {
        uint16_t word = words[index];
        uint8_t *destination =
            (uint8_t *)data.data + index * data.strides[0];
        if (negate)
            word ^= UINT16_C(0x8000);
        memcpy(destination, &word, sizeof(word));
    }
    free(words);
    return tensor;
}

static void gamma_capture(void *opaque, NCTensor *gradient,
                          NCTensor *column_index)
{
    NCTensorData data;
    FILE *output;
    size_t index;

    if (opaque != (void *)(uintptr_t)1 || column_index != NULL ||
        nc_tensor_get_data(&data, gradient) == NULL ||
        data.item_type != NC_TYPE_BF16 || data.item_size != 2 ||
        data.n_dims != 1 || data.dims[0] != GAMMA_ELEMENTS) {
        fprintf(stderr, "unexpected LibNC gradient-merge tensor\n");
        abort();
    }
    output = fopen(gamma_output_path, "wb");
    if (output == NULL)
        abort();
    for (index = 0; index < GAMMA_ELEMENTS; index++) {
        const uint8_t *source =
            (const uint8_t *)data.data + index * data.strides[0];
        if (fwrite(source, sizeof(uint16_t), 1, output) != 1)
            abort();
    }
    if (fclose(output) != 0)
        abort();
    nc_free_tensor(gradient);
}

static NCTensor *gamma_path(NCTensor *parameter, NCTensor *coefficient)
{
    return nc_sum(nc_mul(nc_dup_tensor(parameter), coefficient));
}

int main(int argc, char **argv)
{
    NCContext *context;
    NCDevice *device;
    NCTensor *parameter, *branch, *direct, *loss;
    const char *mode;
    int negate_branch;

    if (argc != 5) {
        fprintf(stderr,
                "usage: gradient_merge BRANCH DIRECT OUTPUT MODE\n");
        return 1;
    }
    mode = argv[4];
    if (strcmp(mode, "branch") != 0 && strcmp(mode, "direct") != 0 &&
        strcmp(mode, "branch-left") != 0 &&
        strcmp(mode, "direct-left") != 0 &&
        strcmp(mode, "negated-branch-left") != 0) {
        fprintf(stderr, "unknown gradient-merge mode: %s\n", mode);
        return 1;
    }
    negate_branch = strcmp(mode, "negated-branch-left") == 0;
    gamma_output_path = argv[3];
    context = nc_context_init(1);
    if (context == NULL)
        return 1;
    nc_set_reproducible(context, TRUE);
    device = nc_new_cpu_device(context);
    if (device == NULL) {
        nc_context_end(context);
        return 1;
    }
    parameter = nc_new_tensor_1d(device, NC_TYPE_BF16, GAMMA_ELEMENTS);
    branch = gamma_read_tensor(device, argv[1], negate_branch);
    direct = gamma_read_tensor(device, argv[2], 0);
    if (parameter == NULL || branch == NULL || direct == NULL) {
        fprintf(stderr, "cannot allocate LibNC gradient-merge tensors\n");
        return 1;
    }
    nc_tensor_set_zero(parameter);
    parameter = nc_set_param(parameter, (void *)(uintptr_t)1);
    if (strcmp(mode, "branch") == 0) {
        loss = gamma_path(parameter, branch);
        nc_free_tensor(direct);
    } else if (strcmp(mode, "direct") == 0) {
        loss = gamma_path(parameter, direct);
        nc_free_tensor(branch);
    } else if (strcmp(mode, "direct-left") == 0) {
        NCTensor *left = gamma_path(parameter, direct);
        NCTensor *right = gamma_path(parameter, branch);
        loss = nc_add(left, right);
    } else {
        NCTensor *left = gamma_path(parameter, branch);
        NCTensor *right = gamma_path(parameter, direct);
        loss = nc_add(left, right);
    }
    if (loss == NULL) {
        fprintf(stderr, "cannot construct LibNC gradient-merge graph\n");
        return 1;
    }
    nc_backward(loss, nc_new_f32(device, 1.0f), gamma_capture, 0);
    nc_free_tensor(loss);
    nc_free_tensor(parameter);
    nc_context_end(context);
    return 0;
}
