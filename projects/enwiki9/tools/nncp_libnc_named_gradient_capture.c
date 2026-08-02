#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

static NCParamList *active_parameters;
static size_t gradient_index;

void nncp_named_gradient_set_param_list(NCParamList *parameters)
{
    active_parameters = parameters;
}

static const char *parameter_name(void *parameter_opaque)
{
    struct list_head *element;

    if (active_parameters == NULL)
        return NULL;
    list_for_each(element, &active_parameters->param_list) {
        NCParam *parameter = list_entry(element, NCParam, link);
        if ((void *)parameter == parameter_opaque)
            return parameter->name;
    }
    return NULL;
}

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

static void sanitize(char *destination, size_t size, const char *source)
{
    size_t index;

    for (index = 0; index + 1 < size && source[index] != '\0'; index++) {
        unsigned char value = source[index];
        destination[index] =
            ((value >= 'a' && value <= 'z') ||
             (value >= 'A' && value <= 'Z') ||
             (value >= '0' && value <= '9') || value == '_')
                ? (char)value
                : '_';
    }
    destination[index] = '\0';
}

void nncp_named_gradient_dump(void *parameter_opaque, NCTensor *gradient)
{
    const char *directory = getenv("NNCP_NAMED_GRADIENT_DIR");
    const char *name = parameter_name(parameter_opaque);
    NCTensor *cpu_gradient;
    NCTensorData data;
    char safe_name[256];
    char data_path[4096];
    char metadata_path[4096];
    FILE *output;
    size_t current;
    int axis;

    if (directory == NULL || directory[0] == '\0')
        return;
    if (name == NULL)
        name = "UNMAPPED";
    sanitize(safe_name, sizeof(safe_name), name);
    current = gradient_index++;
    cpu_gradient = nc_tensor_to_cpu_device(nc_dup_tensor(gradient));
    if (cpu_gradient == NULL ||
        nc_tensor_get_data(&data, cpu_gradient) == NULL ||
        data.item_type != NC_TYPE_F32) {
        fprintf(stderr, "named-gradient capture received invalid tensor\n");
        abort();
    }

    snprintf(data_path, sizeof(data_path), "%s/%03zu_%s.bin", directory,
             current, safe_name);
    output = fopen(data_path, "wb");
    if (output == NULL ||
        write_axis(output, &data, data.data, data.n_dims - 1) != 0 ||
        fclose(output) != 0) {
        fprintf(stderr, "cannot write named gradient %s\n", data_path);
        abort();
    }

    snprintf(metadata_path, sizeof(metadata_path), "%s/%03zu_%s.meta",
             directory, current, safe_name);
    output = fopen(metadata_path, "w");
    if (output == NULL)
        abort();
    fprintf(output, "index=%zu\nname=%s\nitem_type=%d\nitem_size=%zu\n",
            current, name, data.item_type, data.item_size);
    fprintf(output, "dims=");
    for (axis = 0; axis < data.n_dims; axis++)
        fprintf(output, "%s%zu", axis == 0 ? "" : ",", data.dims[axis]);
    fprintf(output, "\n");
    if (fclose(output) != 0)
        abort();
    nc_free_tensor(cpu_gradient);
}
