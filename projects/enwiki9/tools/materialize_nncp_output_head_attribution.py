#!/usr/bin/env python3
"""Materialize the frozen native P/K/O/OK/F/S attribution implementation."""

from __future__ import annotations

from pathlib import Path


ARMS = """
enum {
    ATTR_P = 0,
    ATTR_F = 1,
    ATTR_K = 2,
    ATTR_O = 3,
    ATTR_OK = 4,
    ATTR_S = 5,
};
"""


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected one match, found {count}")
    return source.replace(old, new, 1)


def materialize(source_root: Path) -> None:
    path = source_root / "nncp.c"
    source = path.read_text()
    if source.count("midsegment32") < 10:
        raise ValueError("midpoint parent patch is not present")
    source = source.replace("midsegment32", "midpoint_arm")

    source = replace_once(
        source,
        "#define N_LAYER_MAX 32\n",
        "#define N_LAYER_MAX 32\n" + ARMS,
        "arm enum",
    )
    source = source.replace("BOOL midpoint_arm;", "uint8_t midpoint_arm;")

    source = replace_once(
        source,
        "    int gradient_graph_len;\n} TransformerModel;",
        """    int gradient_graph_len;
    NCTensor *head_hidden[32];
    NCTensor *head_probability[32];
    void *head_weight_opt;
    void *head_bias_opt;
    BOOL head_only_backward;
} TransformerModel;""",
        "transformer attribution state",
    )

    source = replace_once(
        source,
        """    s->gradient_graph_len = s->train_len;
    
    nc_param_list_init(m, &s->param_list);""",
        """    s->gradient_graph_len = s->train_len;
    s->head_only_backward = FALSE;
    
    nc_param_list_init(m, &s->param_list);""",
        "initialize attribution state",
    )

    source = replace_once(
        source,
        """    /* apply the SGD optimizer to all the parameters */
    nc_sgd_opt_set_all(&s->param_list, s->sgd_opt);

    s->dropout_prob =""",
        """    /* apply the SGD optimizer to all the parameters */
    nc_sgd_opt_set_all(&s->param_list, s->sgd_opt);
    {
        NCParam *head_weight = nc_find_param(&s->param_list, "embed_out");
        NCParam *head_bias = nc_find_param(&s->param_list, "out_bias");
        if (!head_weight)
            fatal_error("output-head attribution requires untied embed_out\\n");
        s->head_weight_opt = head_weight;
        s->head_bias_opt = head_bias;
    }

    s->dropout_prob =""",
        "bind existing optimizer variables",
    )

    source = replace_once(
        source,
        """#endif
    sgd_opt_update_var(opaque, yg, get_col_index);
}

/* evaluate the gradient""",
        """#endif
    if (!attribution_backward_model ||
        !attribution_backward_model->head_only_backward ||
        opaque == attribution_backward_model->head_weight_opt ||
        opaque == attribution_backward_model->head_bias_opt) {
        if (attribution_backward_model &&
            attribution_backward_model->head_only_backward &&
            (opaque == attribution_backward_model->head_weight_opt ||
             opaque == attribution_backward_model->head_bias_opt))
            fprintf(stderr, "ATTR_GRAD arm=%d kind=%s hash=%08x\\n",
                    attribution_backward_model->common.midpoint_arm,
                    opaque == attribution_backward_model->head_weight_opt ?
                        "weight" : "bias",
                    nc_tensor_get_hash(yg));
        if (attribution_backward_model &&
            attribution_backward_model->head_only_backward &&
            getenv("NNCP_ATTRIBUTION_DUMP_GRAD") &&
            (opaque == attribution_backward_model->head_weight_opt ||
             opaque == attribution_backward_model->head_bias_opt))
            nc_dump_tensor(opaque == attribution_backward_model->head_weight_opt ?
                               "ATTR_WEIGHT_GRAD" : "ATTR_BIAS_GRAD",
                           yg, 32);
        sgd_opt_update_var(opaque, yg, get_col_index);
    } else {
        nc_free_tensor(yg);
        nc_free_tensor(get_col_index);
    }
}

static float trf_eval_head_gradient(NNCPModelState *s1,
                                    const NCTensor *expected_output1,
                                    BOOL shifted)
{
    TransformerModel *s = (TransformerModel *)s1;
    NCTensor *tab[32], *logits, *gradient;
    int state, stream, symbol;
    float *gradient_data;

    for(state = 0; state < 32; state++) {
        NCTensor *value = s->head_hidden[state];
        assert(value != NULL);
        s->head_hidden[state] = NULL;
        value = nc_matmul(nc_dup_tensor(s->embed_out), value);
        if (s->out_bias)
            value = nc_add(value, nc_dup_tensor(s->out_bias));
        value = nc_convert(value, NC_TYPE_F32);
        tab[state] = nc_reshape_3d(value, s->n_symbols, s->n_streams, 1);
    }
    logits = nc_concat(tab, 32, 2);
    {
        NCNode *head_node = nc_get_node(logits);
        nc_concat_optimization(s->common.model, &head_node, 1);
    }
    gradient = nc_new_tensor_3d(s->common.cpu_device, NC_TYPE_F32,
                                s->n_symbols, s->n_streams, 32);
    gradient_data = nc_tensor_get_ptr(gradient, NULL);
    for(state = 0; state < 32; state++) {
        NCTensor *probability = s->head_probability[state];
        float *probability_data;
        size_t probability_stride;
        int truth_state = shifted ? ((state + 1) & 31) : state;
        assert(probability != NULL);
        s->head_probability[state] = NULL;
        probability = nc_tensor_to_cpu_device(probability);
        probability_data = nc_tensor_get_ptr(probability, &probability_stride);
        for(stream = 0; stream < s->n_streams; stream++) {
            size_t indexes[2] = { (size_t)stream, (size_t)truth_state };
            int truth = nc_get1_i32(expected_output1, 2, indexes);
            for(symbol = 0; symbol < s->n_symbols; symbol++) {
                float value = probability_data[stream * probability_stride + symbol];
                if (symbol == truth)
                    value -= 1.0f;
                gradient_data[((state * s->n_streams + stream) *
                               s->n_symbols) + symbol] =
                    value * (1.0f / (32 * s->n_streams));
            }
        }
        nc_free_tensor(probability);
    }
    gradient = nc_tensor_to_device(gradient, s->common.device);
    s->head_only_backward = TRUE;
    attribution_backward_model = s;
    nc_backward(logits, gradient, backward_cb,
                s->use_sparse_grad ? NC_BW_SPARSE_GRAD : 0);
    attribution_backward_model = NULL;
    s->head_only_backward = FALSE;
    nc_free_tensor(logits);
    return 0;
}

/* evaluate the gradient""",
        "head-only backward helper",
    )

    source = replace_once(
        source,
        """#ifdef DUMP_GRAD_NORM
static double grad_sum;
static int grad_count;
#endif

static void backward_cb""",
        """#ifdef DUMP_GRAD_NORM
static double grad_sum;
static int grad_count;
#endif

static TransformerModel *attribution_backward_model;

static void backward_cb""",
        "backward filter state",
    )

    source = replace_once(
        source,
        """/* update with coefficients */
static void trf_param_update(NNCPModelState *s1)""",
        """static uint32_t attribution_hash_mix(uint32_t state, uint32_t value)
{
    return (state ^ value) * 16777619U;
}

static void trf_dump_attribution_state(TransformerModel *s, int block_idx)
{
    struct list_head *el;
    uint32_t parameter_hash = 2166136261U;
    uint32_t memory_hash = 2166136261U;
    int layer;

    list_for_each(el, &s->param_list.param_list) {
        NCParam *parameter = list_entry(el, NCParam, link);
        parameter_hash = attribution_hash_mix(
            parameter_hash, nc_tensor_get_hash(*parameter->pval));
    }
    for(layer = 0; layer < s->n_layer; layer++)
        memory_hash = attribution_hash_mix(
            memory_hash, nc_tensor_get_hash(s->mem_h[layer]));
    fprintf(stderr,
            "ATTR_STATE arm=%d block=%d step=%lld params=%08x memory=%08x\\n",
            s->common.midpoint_arm, block_idx,
            (long long)s->common.train_step, parameter_hash, memory_hash);
}

/* update with coefficients */
static void trf_param_update(NNCPModelState *s1)""",
        "trajectory witness",
    )

    block_start = source.index("        if (s->midpoint_arm) {\n", source.index("static void process_block"))
    block_end = source.index("        } else if (!use_encode_only) {\n", block_start)
    replacement = """        if (s->midpoint_arm != ATTR_P) {
            BOOL needs_replay;
            assert(n_states == 64);

            for(cur_state = 0; cur_state < 32; cur_state++) {
                for(stream_idx = 0; stream_idx < n_streams; stream_idx++) {
                    nc_set1_i32_2d(input, stream_idx, cur_state,
                                   get_symb(block_buf, block_stride, block_rem,
                                            stream_idx,
                                            block_idx + cur_state - 1));
                }
                output_host = s->model_class->model_eval(s, cur_state, input);
                output_host = nc_tensor_to_cpu_device(output_host);
                output = nc_tensor_get_ptr(output_host, &stride);
                for(stream_idx = 0; stream_idx < n_streams; stream_idx++) {
                    prof_start(PROF_WRITE_SYM);
                    if (!is_decode) {
                        c = get_symb(block_buf, block_stride, block_rem,
                                     stream_idx, block_idx + cur_state);
                        write_sym(pb, output + stream_idx * stride,
                                  s->n_symbols, c);
                    } else {
                        c = read_sym(gb, output + stream_idx * stride,
                                     s->n_symbols);
                        put_symb(block_buf, block_stride, block_rem,
                                 stream_idx, block_idx + cur_state, c);
                    }
                    prof_end(PROF_WRITE_SYM);
                    nc_set1_i32_2d(expected_output, stream_idx, cur_state, c);
                }
                nc_free_tensor(output_host);
            }

            needs_replay = TRUE;
            if (FALSE) {
                lr = get_interp_param(&s->lr, s->train_step / 2);
                st->last_lr = lr;
                s->model_class->model_set_lr(s, lr);
                trf_eval_head_gradient(s, expected_output,
                                       s->midpoint_arm == ATTR_S);
                trf_param_update(s);
                fprintf(stderr, "ATTR_HEAD arm=%d block=%d weight=%08x bias=%08x\\n",
                        s->midpoint_arm, block_idx,
                        nc_tensor_get_hash(((TransformerModel *)s)->embed_out),
                        nc_tensor_get_hash(((TransformerModel *)s)->out_bias));
                s->train_step++;
            } else if (s->midpoint_arm == ATTR_F ||
                       s->midpoint_arm == ATTR_O ||
                       s->midpoint_arm == ATTR_OK ||
                       s->midpoint_arm == ATTR_S) {
                NCTensor *midpoint_expected = expected_output;
                if (s->midpoint_arm == ATTR_S) {
                    midpoint_expected = nc_new_tensor_2d(s->cpu_device,
                                                         NC_TYPE_I32,
                                                         n_streams, n_states);
                    nc_tensor_set_zero(midpoint_expected);
                    for(cur_state = 0; cur_state < 32; cur_state++) {
                        int shifted_state = (cur_state + 1) & 31;
                        for(stream_idx = 0; stream_idx < n_streams; stream_idx++) {
                            size_t indexes[2] = {
                                (size_t)stream_idx, (size_t)shifted_state
                            };
                            nc_set1_i32_2d(
                                midpoint_expected, stream_idx, cur_state,
                                nc_get1_i32(expected_output, 2, indexes));
                        }
                    }
                }
                for(cur_state = 32; cur_state < n_states; cur_state++) {
                    for(stream_idx = 0; stream_idx < n_streams; stream_idx++)
                        nc_set1_i32_2d(input, stream_idx, cur_state, 0);
                    output_host = s->model_class->model_eval(s, cur_state, input);
                    nc_free_tensor(output_host);
                }
                lr = get_interp_param(&s->lr, s->train_step / 2);
                st->last_lr = lr;
                s->model_class->model_set_lr(s, lr);
                trf_set_gradient_range(s, 0, 32, 64);
                if (s->midpoint_arm == ATTR_O ||
                    s->midpoint_arm == ATTR_OK ||
                    s->midpoint_arm == ATTR_S) {
                    ((TransformerModel *)s)->head_only_backward = TRUE;
                    attribution_backward_model = (TransformerModel *)s;
                }
                s->model_class->model_eval_gradient(s, midpoint_expected);
                attribution_backward_model = NULL;
                ((TransformerModel *)s)->head_only_backward = FALSE;
                if (midpoint_expected != expected_output)
                    nc_free_tensor(midpoint_expected);
                trf_param_update(s);
                fprintf(stderr, "ATTR_HEAD arm=%d block=%d weight=%08x bias=%08x\\n",
                        s->midpoint_arm, block_idx,
                        nc_tensor_get_hash(((TransformerModel *)s)->embed_out),
                        nc_tensor_get_hash(((TransformerModel *)s)->out_bias));
                s->train_step++;
            } else {
                assert(s->midpoint_arm == ATTR_K);
                s->model_class->model_eval_end(s);
            }

            if (needs_replay) {
                for(cur_state = 0; cur_state < 32; cur_state++) {
                    for(stream_idx = 0; stream_idx < n_streams; stream_idx++) {
                        nc_set1_i32_2d(input, stream_idx, cur_state,
                                       get_symb(block_buf, block_stride, block_rem,
                                                stream_idx,
                                                block_idx + cur_state - 1));
                    }
                    output_host = s->model_class->model_eval(s, cur_state, input);
                    nc_free_tensor(output_host);
                }
            }
            if (s->midpoint_arm == ATTR_OK) {
                s->model_class->model_eval_end(s);
                for(cur_state = 0; cur_state < 32; cur_state++) {
                    for(stream_idx = 0; stream_idx < n_streams; stream_idx++) {
                        nc_set1_i32_2d(input, stream_idx, cur_state,
                                       get_symb(block_buf, block_stride, block_rem,
                                                stream_idx,
                                                block_idx + cur_state - 1));
                    }
                    output_host = s->model_class->model_eval(s, cur_state, input);
                    nc_free_tensor(output_host);
                }
            }

            for(cur_state = 32; cur_state < n_states; cur_state++) {
                for(stream_idx = 0; stream_idx < n_streams; stream_idx++) {
                    nc_set1_i32_2d(input, stream_idx, cur_state,
                                   get_symb(block_buf, block_stride, block_rem,
                                            stream_idx,
                                            block_idx + cur_state - 1));
                }
                output_host = s->model_class->model_eval(s, cur_state, input);
                output_host = nc_tensor_to_cpu_device(output_host);
                output = nc_tensor_get_ptr(output_host, &stride);
                for(stream_idx = 0; stream_idx < n_streams; stream_idx++) {
                    prof_start(PROF_WRITE_SYM);
                    if (!is_decode) {
                        c = get_symb(block_buf, block_stride, block_rem,
                                     stream_idx, block_idx + cur_state);
                        write_sym(pb, output + stream_idx * stride,
                                  s->n_symbols, c);
                    } else {
                        c = read_sym(gb, output + stream_idx * stride,
                                     s->n_symbols);
                        put_symb(block_buf, block_stride, block_rem,
                                 stream_idx, block_idx + cur_state, c);
                    }
                    prof_end(PROF_WRITE_SYM);
                    nc_set1_i32_2d(expected_output, stream_idx, cur_state, c);
                }
                nc_free_tensor(output_host);
            }
            if (s->midpoint_arm == ATTR_F || s->midpoint_arm == ATTR_O ||
                s->midpoint_arm == ATTR_OK || s->midpoint_arm == ATTR_S)
                trf_set_gradient_range(s, 32, 32, 64);
"""
    source = source[:block_start] + replacement + source[block_end:]

    source = replace_once(
        source,
        """        s->train_step++;
        block_idx += n_states;""",
        """        s->train_step++;
        trf_dump_attribution_state((TransformerModel *)s, block_idx);
        block_idx += n_states;""",
        "per-segment trajectory witness",
    )

    source = replace_once(
        source,
        """        if (s->midpoint_arm)
            lr = get_interp_param(&s->lr, s->train_step / 2);
        else
            lr = get_interp_param(&s->lr, s->train_step);""",
        """        if (s->midpoint_arm == ATTR_F || s->midpoint_arm == ATTR_O ||
            s->midpoint_arm == ATTR_OK || s->midpoint_arm == ATTR_S)
            lr = get_interp_param(&s->lr, s->train_step / 2);
        else
            lr = get_interp_param(&s->lr, s->train_step);""",
        "final learning-rate coordinate",
    )

    source = source.replace(
        '{ "midpoint_arm", 0, "update after each half of a 64-symbol transformer segment" },',
        '{ "midpoint_arm", CMD_HAS_ARG, "attribution schedule: 0=P,1=F,2=K,3=O,4=OK,5=S", "n" },',
    )
    source = replace_once(
        source,
        'p->midpoint_arm = cmdopt_has(co, "midpoint_arm");',
        'p->midpoint_arm = cmdopt_get_int(co, "midpoint_arm", ATTR_P);',
        "parse arm",
    )
    source = source.replace(
        'if (p->midpoint_arm && use_encode_only)',
        'if (p->midpoint_arm != ATTR_P && use_encode_only)',
    )
    source = source.replace(
        'if (p->midpoint_arm &&\n',
        'if (p->midpoint_arm != ATTR_P &&\n',
    )
    source = replace_once(
        source,
        """        if (p->midpoint_arm != ATTR_P &&
            (p->model_class != &trf_model || p->seg_len != 64))
            cmd_error("midpoint_arm requires the transformer and train_len=64");""",
        """        if (p->midpoint_arm < ATTR_P || p->midpoint_arm > ATTR_S)
            cmd_error("midpoint_arm must be in 0..5");
        if (p->midpoint_arm != ATTR_P &&
            (p->model_class != &trf_model || p->seg_len != 64))
            cmd_error("midpoint_arm requires the transformer and train_len=64");""",
        "validate arm",
    )
    path.write_text(source)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    args = parser.parse_args()
    materialize(args.source_root)
