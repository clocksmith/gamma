#define _GNU_SOURCE

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include "libnc.h"

/*
 * Zero-credit oracle hook for the frozen enwik9 production-forward fixture.
 * The patched teacher creates NNCP_PRODUCTION_FIXTURE_MARKER immediately
 * before the selected evaluation.  Until that marker exists this interposer
 * is a no-op, so preceding training evaluations do not produce fixtures.
 */

static size_t tensor_index;

static int marker_exists(void)
{
    const char *marker = getenv("NNCP_PRODUCTION_FIXTURE_MARKER");
    struct stat status;

    return marker != NULL && marker[0] != '\0' && stat(marker, &status) == 0 &&
           S_ISREG(status.st_mode);
}

static void sanitize(char *destination, size_t size, const char *source)
{
    size_t index;

    for (index = 0; index + 1 < size && source[index] != '\0'; index++) {
        const unsigned char value = (unsigned char)source[index];
        destination[index] =
            ((value >= 'a' && value <= 'z') ||
             (value >= 'A' && value <= 'Z') ||
             (value >= '0' && value <= '9') || value == '_')
                ? (char)value
                : '_';
    }
    destination[index] = '\0';
}

static int write_element(FILE *output, const NCTensorData *data,
                         const size_t *indexes)
{
    const uint8_t *pointer = data->data;
    int axis;

    for (axis = 0; axis < data->n_dims; axis++)
        pointer += indexes[axis] * data->strides[axis];
    return fwrite(pointer, data->item_size, 1, output) == 1 ? 0 : -1;
}

static int write_selected_recursive(FILE *output, const NCTensorData *data,
                                    const size_t *selected_dims,
                                    size_t *indexes, int axis)
{
    size_t selected_index;

    if (axis < 0)
        return write_element(output, data, indexes);
    for (selected_index = 0; selected_index < selected_dims[axis];
         selected_index++) {
        size_t source_index = selected_index;

        /* Matrices flatten [feature, stream * position]. */
        if (data->n_dims == 2 && axis == 1 && data->dims[1] == 32 * 64)
            source_index = selected_index * 32;
        /* Probability tensors use [symbol, stream, position]. */
        if (data->n_dims == 3 && axis == 1 && data->dims[1] == 32 &&
            data->dims[2] == 64)
            source_index = 0;
        /* Split-head tensors use stream as the final logical axis. */
        if (data->n_dims == 4 && axis == 3 && data->dims[3] == 32)
            source_index = 0;
        indexes[axis] = source_index;
        if (write_selected_recursive(output, data, selected_dims, indexes,
                                     axis - 1) != 0)
            return -1;
    }
    return 0;
}

static void selected_shape(const NCTensorData *data, size_t *selected_dims)
{
    int axis;

    for (axis = 0; axis < data->n_dims; axis++)
        selected_dims[axis] = data->dims[axis];
    if (data->n_dims == 2 && data->dims[1] == 32 * 64)
        selected_dims[1] = 64;
    if (data->n_dims == 3 && data->dims[1] == 32 && data->dims[2] == 64)
        selected_dims[1] = 1;
    if (data->n_dims == 4 && data->dims[3] == 32)
        selected_dims[3] = 1;
}

void nc_dump_tensor_hash(const char *name, const NCTensor *tensor)
{
    const char *directory = getenv("NNCP_PRODUCTION_FIXTURE_INTERNAL_DIR");
    NCTensor *cpu_tensor;
    NCTensorData data;
    char safe_name[160];
    char data_path[4096];
    char metadata_path[4096];
    FILE *output;
    size_t indexes[NC_N_DIMS_MAX] = {0};
    size_t selected_dims[NC_N_DIMS_MAX] = {0};
    size_t current;
    int axis;

    if (directory == NULL || directory[0] == '\0' || !marker_exists())
        return;
    cpu_tensor = nc_tensor_to_cpu_device(
        nc_convert(nc_dup_tensor(tensor), NC_TYPE_F32));
    if (cpu_tensor == NULL || nc_tensor_get_data(&data, cpu_tensor) == NULL ||
        data.item_type != NC_TYPE_F32) {
        fprintf(stderr, "production fixture received a non-F32 tensor\n");
        abort();
    }
    selected_shape(&data, selected_dims);
    current = tensor_index++;
    sanitize(safe_name, sizeof(safe_name), name);
    snprintf(data_path, sizeof(data_path), "%s/%04zu_%s.f32", directory,
             current, safe_name);
    output = fopen(data_path, "wb");
    if (output == NULL ||
        write_selected_recursive(output, &data, selected_dims, indexes,
                                 data.n_dims - 1) != 0 ||
        fclose(output) != 0) {
        fprintf(stderr, "cannot write production tensor %s\n", data_path);
        abort();
    }

    snprintf(metadata_path, sizeof(metadata_path), "%s/%04zu_%s.meta",
             directory, current, safe_name);
    output = fopen(metadata_path, "w");
    if (output == NULL)
        abort();
    fprintf(output, "index=%zu\nlabel=%s\nitem_type=F32\nitem_size=%zu\n",
            current, name, data.item_size);
    fputs("source_dims=", output);
    for (axis = 0; axis < data.n_dims; axis++)
        fprintf(output, "%s%zu", axis == 0 ? "" : ",", data.dims[axis]);
    fputs("\nselected_dims=", output);
    for (axis = 0; axis < data.n_dims; axis++)
        fprintf(output, "%s%zu", axis == 0 ? "" : ",",
                selected_dims[axis]);
    fputs("\nsource_strides=", output);
    for (axis = 0; axis < data.n_dims; axis++)
        fprintf(output, "%s%zu", axis == 0 ? "" : ",", data.strides[axis]);
    fputs("\nbyte_order=little\nstream_selection=0\n", output);
    if (fclose(output) != 0)
        abort();
    nc_free_tensor(cpu_tensor);
}
