#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

#define MAX_LAYERS 32
#define MAX_STATES 256

static unsigned char probe_markers[MAX_LAYERS][MAX_STATES];

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

static void dump_tensor(const char *kind, int layer, int state,
                        NCTensor *tensor)
{
    const char *directory = getenv("NNCP_FF2_ADJOINT_DIR");
    NCTensor *cpu_tensor;
    NCTensorData data;
    char data_path[4096];
    char metadata_path[4096];
    FILE *output;
    int axis;

    if (directory == NULL || directory[0] == '\0')
        return;
    cpu_tensor = nc_tensor_to_cpu_device(nc_dup_tensor(tensor));
    if (cpu_tensor == NULL ||
        nc_tensor_get_data(&data, cpu_tensor) == NULL ||
        data.item_type != NC_TYPE_F32) {
        fprintf(stderr, "FF2 adjoint capture received invalid tensor\n");
        abort();
    }
    snprintf(data_path, sizeof(data_path), "%s/%s_l%02d_s%03d.bin",
             directory, kind, layer, state);
    output = fopen(data_path, "wb");
    if (output == NULL ||
        write_axis(output, &data, data.data, data.n_dims - 1) != 0 ||
        fclose(output) != 0) {
        fprintf(stderr, "cannot write FF2 capture %s\n", data_path);
        abort();
    }
    snprintf(metadata_path, sizeof(metadata_path), "%s/%s_l%02d_s%03d.meta",
             directory, kind, layer, state);
    output = fopen(metadata_path, "w");
    if (output == NULL)
        abort();
    fprintf(output, "kind=%s\nlayer=%d\nstate=%d\nitem_type=%d\nitem_size=%zu\n",
            kind, layer, state, data.item_type, data.item_size);
    fprintf(output, "dims=");
    for (axis = 0; axis < data.n_dims; axis++)
        fprintf(output, "%s%zu", axis == 0 ? "" : ",", data.dims[axis]);
    fprintf(output, "\n");
    if (fclose(output) != 0)
        abort();
    nc_free_tensor(cpu_tensor);
}

void nncp_ff2_input_dump(NCTensor *value, int layer, int state)
{
    if (layer < 0 || layer >= MAX_LAYERS || state < 0 || state >= MAX_STATES)
        return;
    dump_tensor("input", layer, state, value);
}

NCTensor *nncp_ff2_probe_attach(NCTensor *value, int layer, int state)
{
    NCTensor *zero;

    if (layer < 0 || layer >= MAX_LAYERS || state < 0 || state >= MAX_STATES)
        return value;
    zero = nc_new_tensor_from_tensor_nz(value);
    if (zero == NULL) {
        fprintf(stderr, "cannot allocate FF2 adjoint probe\n");
        abort();
    }
    nc_tensor_set_zero(zero);
    zero = nc_set_param(zero, &probe_markers[layer][state]);
    return nc_add(value, zero);
}

int nncp_ff2_probe_capture(void *opaque, NCTensor *gradient,
                           NCTensor *column_index)
{
    int layer;
    int state;

    for (layer = 0; layer < MAX_LAYERS; layer++) {
        for (state = 0; state < MAX_STATES; state++) {
            if (opaque == &probe_markers[layer][state]) {
                if (column_index != NULL) {
                    fprintf(stderr, "FF2 adjoint probe received sparse gradient\n");
                    abort();
                }
                dump_tensor("adjoint", layer, state, gradient);
                nc_free_tensor(gradient);
                return 1;
            }
        }
    }
    return 0;
}
