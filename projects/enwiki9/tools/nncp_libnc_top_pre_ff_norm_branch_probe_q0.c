#define GAMMA_PRE_FF_NORM_LAYER 19
#define GAMMA_PRE_FF_NORM_STATES 64

static unsigned char gamma_pre_ff_norm_markers[GAMMA_PRE_FF_NORM_STATES];
static int gamma_pre_ff_norm_target_active;

static int gamma_pre_ff_norm_write_axis(FILE *output,
                                        const NCTensorData *data,
                                        const uint8_t *base, int axis)
{
    size_t index;

    if (axis < 0)
        return fwrite(base, data->item_size, 1, output) == 1 ? 0 : -1;
    for (index = 0; index < data->dims[axis]; index++) {
        if (gamma_pre_ff_norm_write_axis(
                output, data, base + index * data->strides[axis], axis - 1))
            return -1;
    }
    return 0;
}

static void gamma_pre_ff_norm_dump(const char *kind, int state,
                                   NCTensor *tensor)
{
    NCTensor *cpu_tensor;
    NCTensorData data;
    char data_name[128], metadata_name[128];
    char data_path[4096], metadata_path[4096];
    FILE *output;
    int axis;

    snprintf(data_name, sizeof(data_name),
             "pre_ff_norm_%s_s%03d.bin", kind, state);
    snprintf(metadata_name, sizeof(metadata_name),
             "pre_ff_norm_%s_s%03d.meta", kind, state);
    gamma_fixture_path(data_path, sizeof(data_path), data_name);
    gamma_fixture_path(metadata_path, sizeof(metadata_path), metadata_name);
    if (access(data_path, F_OK) == 0 || access(metadata_path, F_OK) == 0) {
        fprintf(stderr, "duplicate pre-FF normalization probe state %d\n", state);
        abort();
    }
    cpu_tensor = nc_tensor_to_cpu_device(nc_dup_tensor(tensor));
    if (cpu_tensor == NULL ||
        nc_tensor_get_data(&data, cpu_tensor) == NULL ||
        data.item_type != NC_TYPE_BF16 || data.item_size != 2) {
        fprintf(stderr, "invalid pre-FF normalization %s tensor\n", kind);
        abort();
    }
    output = fopen(data_path, "wb");
    if (output == NULL ||
        gamma_pre_ff_norm_write_axis(
            output, &data, data.data, data.n_dims - 1) != 0 ||
        fclose(output) != 0) {
        fprintf(stderr, "cannot write pre-FF normalization %s state %d\n",
                kind, state);
        abort();
    }
    output = fopen(metadata_path, "w");
    if (output == NULL)
        abort();
    fprintf(output,
            "kind=%s\nstate=%d\nitem_type=%d\nitem_size=%zu\ndims=",
            kind, state, data.item_type, data.item_size);
    for (axis = 0; axis < data.n_dims; axis++)
        fprintf(output, "%s%zu", axis == 0 ? "" : ",", data.dims[axis]);
    if (fputs("\nbyte_order=little\n", output) < 0 || fclose(output) != 0)
        abort();
    nc_free_tensor(cpu_tensor);
}

static void gamma_pre_ff_norm_probe_set_block(int block_idx)
{
    gamma_pre_ff_norm_target_active = block_idx == 256;
}

static void gamma_pre_ff_norm_input_dump(NCTensor *value, int layer, int state)
{
    if (!gamma_pre_ff_norm_target_active || layer != GAMMA_PRE_FF_NORM_LAYER)
        return;
    if (state < 0 || state >= GAMMA_PRE_FF_NORM_STATES) {
        fprintf(stderr, "pre-FF normalization probe requires sequential states\n");
        abort();
    }
    gamma_pre_ff_norm_dump("input", state, value);
}

static NCTensor *gamma_pre_ff_norm_probe_attach(NCTensor *value, int layer,
                                                int state)
{
    NCTensor *zero;

    if (!gamma_pre_ff_norm_target_active || layer != GAMMA_PRE_FF_NORM_LAYER)
        return value;
    if (state < 0 || state >= GAMMA_PRE_FF_NORM_STATES) {
        fprintf(stderr, "pre-FF normalization probe received invalid state\n");
        abort();
    }
    zero = nc_new_tensor_from_tensor_nz(value);
    if (zero == NULL) {
        fprintf(stderr, "cannot allocate pre-FF normalization probe\n");
        abort();
    }
    nc_tensor_set_zero(zero);
    zero = nc_set_param(zero, &gamma_pre_ff_norm_markers[state]);
    return nc_add(value, zero);
}

static int gamma_pre_ff_norm_probe_capture(void *opaque, NCTensor *gradient,
                                           NCTensor *column_index)
{
    int state;

    for (state = 0; state < GAMMA_PRE_FF_NORM_STATES; state++) {
        if (opaque != &gamma_pre_ff_norm_markers[state])
            continue;
        if (!gamma_update_fixture_active || column_index != NULL) {
            fprintf(stderr, "invalid pre-FF normalization adjoint callback\n");
            abort();
        }
        gamma_pre_ff_norm_dump("adjoint", state, gradient);
        nc_free_tensor(gradient);
        return 1;
    }
    return 0;
}
