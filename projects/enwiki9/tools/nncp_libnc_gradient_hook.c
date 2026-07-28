#define _GNU_SOURCE

#include <dlfcn.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "libnc.h"

typedef void (*sgd_opt_set_fn)(NCParam *, NCSGDOptState *);
typedef void (*sgd_opt_set_all_fn)(NCParamList *, NCSGDOptState *);
typedef void (*sgd_opt_update_var_fn)(void *, NCTensor *, NCTensor *);

typedef struct {
    void *optimizer_variable;
    char *name;
} GradientName;

static GradientName gradient_names[4096];
static size_t gradient_name_count;
static size_t unknown_gradient_count;

static const char *find_gradient_name(void *optimizer_variable)
{
    size_t i;

    for (i = 0; i < gradient_name_count; i++) {
        if (gradient_names[i].optimizer_variable == optimizer_variable)
            return gradient_names[i].name;
    }
    return NULL;
}

static void remember_gradient_name(NCParam *parameter)
{
    const char *known;

    if (parameter == NULL || parameter->sgd_opt == NULL ||
        parameter->name == NULL)
        return;
    known = find_gradient_name(parameter->sgd_opt);
    if (known != NULL || gradient_name_count >=
        sizeof(gradient_names) / sizeof(gradient_names[0]))
        return;
    gradient_names[gradient_name_count].optimizer_variable =
        parameter->sgd_opt;
    gradient_names[gradient_name_count].name = strdup(parameter->name);
    gradient_name_count++;
}

void nc_sgd_opt_set(NCParam *parameter, NCSGDOptState *optimizer)
{
    static sgd_opt_set_fn real_function;

    if (real_function == NULL) {
        real_function = (sgd_opt_set_fn)dlsym(RTLD_NEXT, "nc_sgd_opt_set");
        if (real_function == NULL) {
            fprintf(stderr, "gradient hook: nc_sgd_opt_set unavailable\n");
            abort();
        }
    }
    real_function(parameter, optimizer);
    remember_gradient_name(parameter);
}

void nc_sgd_opt_set_all(NCParamList *parameters, NCSGDOptState *optimizer)
{
    static sgd_opt_set_all_fn real_function;
    struct list_head *element;

    if (real_function == NULL) {
        real_function = (sgd_opt_set_all_fn)dlsym(
            RTLD_NEXT, "nc_sgd_opt_set_all");
        if (real_function == NULL) {
            fprintf(stderr,
                    "gradient hook: nc_sgd_opt_set_all unavailable\n");
            abort();
        }
    }
    real_function(parameters, optimizer);
    list_for_each(element, &parameters->param_list) {
        NCParam *parameter = list_entry(element, NCParam, link);
        remember_gradient_name(parameter);
    }
}

static void sanitize_name(char *destination, size_t destination_size,
                          const char *source)
{
    size_t i;

    if (source == NULL)
        source = "unknown";
    for (i = 0; i + 1 < destination_size && source[i] != '\0'; i++) {
        unsigned char value = source[i];
        destination[i] =
            ((value >= 'a' && value <= 'z') ||
             (value >= 'A' && value <= 'Z') ||
             (value >= '0' && value <= '9') ||
             value == '_' || value == '-') ? value : '_';
    }
    destination[i] = '\0';
}

static int write_tensor_axis(FILE *output, const NCTensorData *data,
                             const uint8_t *base, int axis)
{
    size_t i;

    if (axis < 0)
        return fwrite(base, data->item_size, 1, output) == 1 ? 0 : -1;
    for (i = 0; i < data->dims[axis]; i++) {
        if (write_tensor_axis(output, data,
                              base + i * data->strides[axis],
                              axis - 1) != 0)
            return -1;
    }
    return 0;
}

static void dump_gradient(void *optimizer_variable, NCTensor *gradient)
{
    const char *directory = getenv("NNCP_GRADIENT_DIR");
    const char *name = find_gradient_name(optimizer_variable);
    char safe_name[256];
    char data_path[1024];
    char metadata_path[1024];
    NCTensor *cpu_gradient;
    NCTensorData data;
    FILE *output;
    int i;

    if (directory == NULL || directory[0] == '\0')
        return;
    if (name != NULL) {
        sanitize_name(safe_name, sizeof(safe_name), name);
    } else {
        snprintf(safe_name, sizeof(safe_name), "unknown_%04zu",
                 unknown_gradient_count++);
    }
    snprintf(data_path, sizeof(data_path), "%s/%s.bin", directory,
             safe_name);
    if (access(data_path, F_OK) == 0)
        return;
    if (mkdir(directory, 0700) != 0 && errno != EEXIST)
        return;

    cpu_gradient = nc_tensor_to_cpu_device(nc_dup_tensor(gradient));
    if (cpu_gradient == NULL)
        return;
    if (nc_tensor_get_data(&data, cpu_gradient) == NULL) {
        nc_free_tensor(cpu_gradient);
        return;
    }

    output = fopen(data_path, "wb");
    if (output != NULL) {
        if (write_tensor_axis(output, &data, data.data,
                              data.n_dims - 1) != 0)
            fprintf(stderr, "gradient hook: write failed for %s\n",
                    data_path);
        fclose(output);
    }

    snprintf(metadata_path, sizeof(metadata_path), "%s/%s.meta",
             directory, safe_name);
    output = fopen(metadata_path, "w");
    if (output != NULL) {
        fprintf(output, "name=%s\n", name != NULL ? name : "unknown");
        fprintf(output, "item_type=%d\n", data.item_type);
        fprintf(output, "item_size=%zu\n", data.item_size);
        fprintf(output, "n_dims=%d\n", data.n_dims);
        fprintf(output, "dims=");
        for (i = 0; i < data.n_dims; i++)
            fprintf(output, "%s%zu", i == 0 ? "" : ",", data.dims[i]);
        fprintf(output, "\n");
        fclose(output);
    }
    nc_free_tensor(cpu_gradient);
}

void sgd_opt_update_var(void *optimizer_variable, NCTensor *gradient,
                        NCTensor *column_index)
{
    static sgd_opt_update_var_fn real_function;

    if (real_function == NULL) {
        real_function = (sgd_opt_update_var_fn)dlsym(
            RTLD_NEXT, "sgd_opt_update_var");
        if (real_function == NULL) {
            fprintf(stderr,
                    "gradient hook: sgd_opt_update_var unavailable\n");
            abort();
        }
    }
    dump_gradient(optimizer_variable, gradient);
    real_function(optimizer_variable, gradient, column_index);
}
