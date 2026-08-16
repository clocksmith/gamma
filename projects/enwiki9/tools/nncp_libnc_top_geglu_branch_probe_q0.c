#define GAMMA_TOP_GEGLU_LAYER 19
#define GAMMA_TOP_GEGLU_STATES 64
#define GAMMA_TOP_GEGLU_BRANCHES 2

static unsigned char gamma_top_geglu_markers
    [GAMMA_TOP_GEGLU_BRANCHES][GAMMA_TOP_GEGLU_STATES];
static int gamma_top_geglu_target_active;

static const char *gamma_top_geglu_branch_name(int branch)
{
    return branch == 0 ? "gate" : "value";
}

static int gamma_top_geglu_write_axis(FILE *output, const NCTensorData *data,
                                      const uint8_t *base, int axis)
{
    size_t index;

    if (axis < 0)
        return fwrite(base, data->item_size, 1, output) == 1 ? 0 : -1;
    for (index = 0; index < data->dims[axis]; index++) {
        if (gamma_top_geglu_write_axis(
                output, data, base + index * data->strides[axis], axis - 1))
            return -1;
    }
    return 0;
}

static void gamma_top_geglu_dump(const char *kind, int branch, int state,
                                 NCTensor *tensor)
{
    NCTensor *cpu_tensor;
    NCTensorData data;
    char data_name[128], metadata_name[128];
    char data_path[4096], metadata_path[4096];
    FILE *output;
    int axis;

    snprintf(data_name, sizeof(data_name), "top_geglu_%s_%s_s%03d.bin",
             gamma_top_geglu_branch_name(branch), kind, state);
    snprintf(metadata_name, sizeof(metadata_name), "top_geglu_%s_%s_s%03d.meta",
             gamma_top_geglu_branch_name(branch), kind, state);
    gamma_fixture_path(data_path, sizeof(data_path), data_name);
    gamma_fixture_path(metadata_path, sizeof(metadata_path), metadata_name);
    if (access(data_path, F_OK) == 0 || access(metadata_path, F_OK) == 0) {
        fprintf(stderr, "duplicate top GEGLU branch probe state %d\n", state);
        abort();
    }
    cpu_tensor = nc_tensor_to_cpu_device(nc_dup_tensor(tensor));
    if (cpu_tensor == NULL ||
        nc_tensor_get_data(&data, cpu_tensor) == NULL ||
        data.item_type != NC_TYPE_BF16 || data.item_size != 2) {
        fprintf(stderr, "invalid top GEGLU %s branch %s tensor\n",
                gamma_top_geglu_branch_name(branch), kind);
        abort();
    }
    output = fopen(data_path, "wb");
    if (output == NULL ||
        gamma_top_geglu_write_axis(
            output, &data, data.data, data.n_dims - 1) != 0 ||
        fclose(output) != 0) {
        fprintf(stderr, "cannot write top GEGLU %s branch %s state %d\n",
                gamma_top_geglu_branch_name(branch), kind, state);
        abort();
    }
    output = fopen(metadata_path, "w");
    if (output == NULL)
        abort();
    fprintf(output,
            "kind=%s\nbranch=%s\nstate=%d\nitem_type=%d\nitem_size=%zu\ndims=",
            kind, gamma_top_geglu_branch_name(branch), state,
            data.item_type, data.item_size);
    for (axis = 0; axis < data.n_dims; axis++)
        fprintf(output, "%s%zu", axis == 0 ? "" : ",", data.dims[axis]);
    if (fputs("\nbyte_order=little\n", output) < 0 || fclose(output) != 0)
        abort();
    nc_free_tensor(cpu_tensor);
}

static void gamma_top_geglu_probe_set_block(int block_idx)
{
    gamma_top_geglu_target_active = block_idx == 256;
}

static void gamma_top_geglu_input_dump(NCTensor *value, int layer, int state,
                                       int branch)
{
    if (!gamma_top_geglu_target_active || layer != GAMMA_TOP_GEGLU_LAYER)
        return;
    if (state < 0 || state >= GAMMA_TOP_GEGLU_STATES ||
        branch < 0 || branch >= GAMMA_TOP_GEGLU_BRANCHES) {
        fprintf(stderr, "top GEGLU probe requires valid sequential states\n");
        abort();
    }
    gamma_top_geglu_dump("input", branch, state, value);
}

static NCTensor *gamma_top_geglu_probe_attach(
    NCTensor *value, int layer, int state, int branch)
{
    NCTensor *zero;

    if (!gamma_top_geglu_target_active || layer != GAMMA_TOP_GEGLU_LAYER)
        return value;
    if (state < 0 || state >= GAMMA_TOP_GEGLU_STATES ||
        branch < 0 || branch >= GAMMA_TOP_GEGLU_BRANCHES) {
        fprintf(stderr, "top GEGLU probe received an invalid branch or state\n");
        abort();
    }
    zero = nc_new_tensor_from_tensor_nz(value);
    if (zero == NULL) {
        fprintf(stderr, "cannot allocate top GEGLU branch adjoint probe\n");
        abort();
    }
    nc_tensor_set_zero(zero);
    zero = nc_set_param(zero, &gamma_top_geglu_markers[branch][state]);
    return nc_add(value, zero);
}

static int gamma_top_geglu_probe_capture(
    void *opaque, NCTensor *gradient, NCTensor *column_index)
{
    int branch, state;

    for (branch = 0; branch < GAMMA_TOP_GEGLU_BRANCHES; branch++) {
        for (state = 0; state < GAMMA_TOP_GEGLU_STATES; state++) {
            if (opaque != &gamma_top_geglu_markers[branch][state])
                continue;
            if (!gamma_update_fixture_active || column_index != NULL) {
                fprintf(stderr, "invalid top GEGLU branch adjoint callback\n");
                abort();
            }
            gamma_top_geglu_dump("adjoint", branch, state, gradient);
            nc_free_tensor(gradient);
            return 1;
        }
    }
    return 0;
}
