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
typedef void (*save_param_opt_fn)(FILE *, const NCParam *);

typedef struct {
    void *optimizer_variable;
    char *name;
} GradientName;

static GradientName gradient_names[4096];
static size_t gradient_name_count;
static size_t gradient_dump_count;

static const char *fixture_directory(void)
{
    const char *directory = getenv("NNCP_PROFILE_UPDATE_FIXTURE_DIR");
    return directory != NULL && directory[0] != '\0' ? directory : NULL;
}

static int capture_active(void)
{
    const char *directory = fixture_directory();
    char path[4096];
    struct stat status;

    if (directory == NULL)
        return 0;
    snprintf(path, sizeof(path), "%s/active.marker", directory);
    return stat(path, &status) == 0 && S_ISREG(status.st_mode);
}

static const char *find_gradient_name(void *optimizer_variable)
{
    size_t index;

    for (index = 0; index < gradient_name_count; index++) {
        if (gradient_names[index].optimizer_variable == optimizer_variable)
            return gradient_names[index].name;
    }
    return NULL;
}

static void remember_gradient_name(NCParam *parameter)
{
    if (parameter == NULL || parameter->sgd_opt == NULL ||
        parameter->name == NULL ||
        find_gradient_name(parameter) != NULL)
        return;
    if (gradient_name_count >=
        sizeof(gradient_names) / sizeof(gradient_names[0])) {
        fprintf(stderr, "profile update fixture gradient-name capacity exceeded\n");
        abort();
    }
    gradient_names[gradient_name_count].optimizer_variable =
        parameter;
    gradient_names[gradient_name_count].name = strdup(parameter->name);
    if (gradient_names[gradient_name_count].name == NULL)
        abort();
    gradient_name_count++;
}

void nc_save_param_opt(FILE *file, const NCParam *parameter)
{
    static save_param_opt_fn real_function;

    if (real_function == NULL) {
        real_function = (save_param_opt_fn)dlsym(
            RTLD_NEXT, "nc_save_param_opt");
        if (real_function == NULL)
            abort();
    }
    remember_gradient_name((NCParam *)parameter);
    real_function(file, parameter);
}

void nc_sgd_opt_set(NCParam *parameter, NCSGDOptState *optimizer)
{
    static sgd_opt_set_fn real_function;

    if (real_function == NULL) {
        real_function = (sgd_opt_set_fn)dlsym(RTLD_NEXT, "nc_sgd_opt_set");
        if (real_function == NULL)
            abort();
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
        if (real_function == NULL)
            abort();
    }
    real_function(parameters, optimizer);
    list_for_each(element, &parameters->param_list) {
        NCParam *parameter = list_entry(element, NCParam, link);
        remember_gradient_name(parameter);
    }
}

static void sanitize(char *destination, size_t size, const char *source)
{
    size_t index;

    for (index = 0; index + 1 < size && source[index] != '\0'; index++) {
        const unsigned char value = (unsigned char)source[index];
        destination[index] =
            ((value >= 'a' && value <= 'z') ||
             (value >= 'A' && value <= 'Z') ||
             (value >= '0' && value <= '9') || value == '_' || value == '-')
                ? (char)value
                : '_';
    }
    destination[index] = '\0';
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

static void dump_gradient(void *optimizer_variable, NCTensor *gradient,
                          NCTensor *column_index)
{
    const char *directory = fixture_directory();
    const char *name = find_gradient_name(optimizer_variable);
    char safe_name[256];
    char gradient_directory[4096];
    char data_path[4608];
    char metadata_path[4608];
    NCTensor *cpu_gradient;
    NCTensorData data;
    FILE *output;
    int axis;

    if (!capture_active())
        return;
    if (name == NULL || column_index != NULL) {
        fprintf(stderr, "profile update fixture requires named dense gradients\n");
        abort();
    }
    sanitize(safe_name, sizeof(safe_name), name);
    snprintf(gradient_directory, sizeof(gradient_directory), "%s/gradients",
             directory);
    if (mkdir(gradient_directory, 0700) != 0 && errno != EEXIST)
        abort();
    snprintf(data_path, sizeof(data_path), "%s/%04zu_%s.bin",
             gradient_directory, gradient_dump_count, safe_name);
    snprintf(metadata_path, sizeof(metadata_path), "%s/%04zu_%s.meta",
             gradient_directory, gradient_dump_count, safe_name);
    if (access(data_path, F_OK) == 0) {
        fprintf(stderr, "duplicate profile update gradient path\n");
        abort();
    }

    cpu_gradient = nc_tensor_to_cpu_device(nc_dup_tensor(gradient));
    if (cpu_gradient == NULL ||
        nc_tensor_get_data(&data, cpu_gradient) == NULL)
        abort();
    output = fopen(data_path, "wb");
    if (output == NULL ||
        write_axis(output, &data, data.data, data.n_dims - 1) != 0 ||
        fclose(output) != 0)
        abort();
    output = fopen(metadata_path, "w");
    if (output == NULL)
        abort();
    fprintf(output, "index=%zu\nname=%s\nitem_type=%d\nitem_size=%zu\n",
            gradient_dump_count, name, data.item_type, data.item_size);
    fputs("dims=", output);
    for (axis = 0; axis < data.n_dims; axis++)
        fprintf(output, "%s%zu", axis == 0 ? "" : ",", data.dims[axis]);
    fputs("\nbyte_order=little\ncolumn_index=none\n", output);
    if (fclose(output) != 0)
        abort();
    gradient_dump_count++;
    nc_free_tensor(cpu_gradient);
}

void sgd_opt_update_var(void *optimizer_variable, NCTensor *gradient,
                        NCTensor *column_index)
{
    static sgd_opt_update_var_fn real_function;

    if (real_function == NULL) {
        real_function = (sgd_opt_update_var_fn)dlsym(
            RTLD_NEXT, "sgd_opt_update_var");
        if (real_function == NULL)
            abort();
    }
    dump_gradient(optimizer_variable, gradient, column_index);
    real_function(optimizer_variable, gradient, column_index);
}
