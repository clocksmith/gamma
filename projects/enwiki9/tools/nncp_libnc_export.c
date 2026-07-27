#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include "libnc.h"

static void fail(const char *message)
{
    perror(message);
    exit(1);
}

static void json_string(FILE *output, const char *text)
{
    const unsigned char *p = (const unsigned char *)text;
    fputc('"', output);
    while (*p) {
        if (*p == '"' || *p == '\\')
            fputc('\\', output);
        if (*p >= 0x20)
            fputc(*p, output);
        p++;
    }
    fputc('"', output);
}

int main(int argc, char **argv)
{
    NCContext *context;
    NCTensor *tensor, *cpu, *contiguous;
    FILE *input, *manifest, *payload;
    char name[1024], filename[4096];
    char *config;
    size_t dims[NC_N_DIMS_MAX], stride;
    int index, n_dims, axis;
    int64_t bytes;
    void *pointer;

    if (argc != 3) {
        fprintf(stderr, "usage: %s COEFS OUTPUT_DIR\n", argv[0]);
        return 2;
    }
    if (mkdir(argv[2], 0777) < 0 && errno != EEXIST)
        fail("mkdir");
    snprintf(filename, sizeof(filename), "%s/manifest.json", argv[2]);
    manifest = fopen(filename, "wb");
    if (!manifest)
        fail("manifest");
    input = fopen(argv[1], "rb");
    if (!input)
        fail("coefs");

    context = nc_context_init(1);
    if (!context)
        fail("nc_context_init");
    config = nc_load_param_header(input);
    if (!config) {
        fprintf(stderr, "invalid LibNC coefficient header\n");
        return 1;
    }

    fprintf(manifest, "{\n  \"schema\": \"gamma.libnc_tensor_export.v1\",\n");
    fprintf(manifest, "  \"config\": ");
    json_string(manifest, config);
    fprintf(manifest, ",\n  \"tensors\": [\n");
    nc_free(config);

    index = 0;
    while ((tensor = nc_load_param(context, input, name, sizeof(name)))) {
        cpu = nc_tensor_to_cpu_device(tensor);
        contiguous = nc_make_contiguous(cpu);
        n_dims = nc_tensor_get_dims(contiguous, dims);
        bytes = nc_tensor_get_buffer_size(contiguous);
        pointer = nc_tensor_get_ptr(contiguous, &stride);
        if (!pointer || bytes < 0) {
            fprintf(stderr, "cannot access tensor %s\n", name);
            return 1;
        }
        snprintf(filename, sizeof(filename), "%s/%05d.bin", argv[2], index);
        payload = fopen(filename, "wb");
        if (!payload)
            fail("payload");
        if (fwrite(pointer, 1, (size_t)bytes, payload) != (size_t)bytes)
            fail("write payload");
        if (fclose(payload))
            fail("close payload");

        if (index)
            fprintf(manifest, ",\n");
        fprintf(manifest, "    {\"index\": %d, \"name\": ", index);
        json_string(manifest, name);
        fprintf(manifest, ", \"type\": ");
        json_string(manifest, nc_type_name_table[nc_tensor_get_item_type(contiguous)]);
        fprintf(manifest, ", \"bytes\": %" PRId64 ", \"dims\": [", bytes);
        for (axis = 0; axis < n_dims; axis++) {
            if (axis)
                fputs(", ", manifest);
            fprintf(manifest, "%zu", dims[axis]);
        }
        fprintf(manifest, "], \"payload\": \"%05d.bin\"}", index);
        index++;
        nc_free_tensor(contiguous);
        if (cpu != contiguous)
            nc_free_tensor(cpu);
        if (tensor != cpu)
            nc_free_tensor(tensor);
    }
    fprintf(manifest, "\n  ],\n  \"tensor_count\": %d\n}\n", index);
    if (fclose(input) || fclose(manifest))
        fail("close");
    nc_context_end(context);
    return 0;
}
