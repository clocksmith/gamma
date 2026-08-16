#define GAMMA_FINAL_RMS_STATES 64

static int gamma_final_rms_target_active;

static int gamma_final_rms_write_axis(FILE *output, const NCTensorData *data,
                                      const uint8_t *base, int axis)
{
    size_t index;

    if (axis < 0)
        return fwrite(base, data->item_size, 1, output) == 1 ? 0 : -1;
    for (index = 0; index < data->dims[axis]; index++) {
        if (gamma_final_rms_write_axis(
                output, data, base + index * data->strides[axis], axis - 1))
            return -1;
    }
    return 0;
}

static void gamma_final_rms_set_block(int block_idx)
{
    gamma_final_rms_target_active = block_idx == 256;
}

static void gamma_final_rms_dump(const char *kind, int state,
                                 NCTensor *tensor)
{
    NCTensor *cpu_tensor;
    NCTensorData data;
    char data_name[128], metadata_name[128];
    char data_path[4096], metadata_path[4096];
    FILE *output;
    int axis;

    if (!gamma_final_rms_target_active)
        return;
    if (state < 0 || state >= GAMMA_FINAL_RMS_STATES) {
        fprintf(stderr, "final RMSNorm probe requires sequential states\n");
        abort();
    }
    snprintf(data_name, sizeof(data_name), "final_rms_%s_s%03d.bin",
             kind, state);
    snprintf(metadata_name, sizeof(metadata_name), "final_rms_%s_s%03d.meta",
             kind, state);
    gamma_fixture_path(data_path, sizeof(data_path), data_name);
    gamma_fixture_path(metadata_path, sizeof(metadata_path), metadata_name);
    if (access(data_path, F_OK) == 0 || access(metadata_path, F_OK) == 0) {
        fprintf(stderr, "duplicate final RMSNorm probe state %d\n", state);
        abort();
    }
    cpu_tensor = nc_tensor_to_cpu_device(nc_dup_tensor(tensor));
    if (cpu_tensor == NULL ||
        nc_tensor_get_data(&data, cpu_tensor) == NULL ||
        data.item_type != NC_TYPE_BF16 || data.item_size != 2 ||
        data.n_dims != 2 || data.dims[0] != 1024 || data.dims[1] != 32) {
        fprintf(stderr, "invalid final RMSNorm %s tensor\n", kind);
        abort();
    }
    output = fopen(data_path, "wb");
    if (output == NULL ||
        gamma_final_rms_write_axis(
            output, &data, data.data, data.n_dims - 1) != 0 ||
        fclose(output) != 0) {
        fprintf(stderr, "cannot write final RMSNorm %s state %d\n",
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
