#!/usr/bin/env python3
"""Add deterministic named-gradient witnesses to the production F arm."""

from __future__ import annotations

import argparse
from pathlib import Path

from materialize_nncp_output_head_attribution import materialize as materialize_parent
from materialize_nncp_output_head_attribution import replace_once


def materialize(source_root: Path) -> None:
    materialize_parent(source_root)
    path = source_root / "nncp.c"
    source = path.read_text()
    source = replace_once(
        source,
        """    BOOL head_only_backward;
} TransformerModel;""",
        """    BOOL head_only_backward;
    BOOL named_gradient_capture;
    int named_gradient_block;
} TransformerModel;""",
        "named-gradient state",
    )
    source = replace_once(
        source,
        """    s->head_only_backward = FALSE;
    
    nc_param_list_init(m, &s->param_list);""",
        """    s->head_only_backward = FALSE;
    s->named_gradient_capture = FALSE;
    s->named_gradient_block = -1;
    
    nc_param_list_init(m, &s->param_list);""",
        "named-gradient initialization",
    )
    source = replace_once(
        source,
        """static TransformerModel *attribution_backward_model;

static void backward_cb""",
        r'''static TransformerModel *attribution_backward_model;

static size_t attribution_tensor_element_count(const NCTensor *tensor)
{
    size_t dims[NC_N_DIMS_MAX];
    size_t count = 1;
    int dimension_count, index;

    dimension_count = nc_tensor_get_dims(tensor, dims);
    for(index = 0; index < dimension_count; index++)
        count *= dims[index];
    return count;
}

static void attribution_dump_named_gradient(TransformerModel *model,
                                            NCParam *parameter,
                                            NCTensor *gradient)
{
    NCTensor *sum;
    float energy;
    BOOL finite;

    finite = nc_tensor_isfinite(gradient);
    sum = nc_sum(nc_mul(nc_dup_tensor(gradient), nc_dup_tensor(gradient)));
    energy = nc_get_scalar_f32(sum);
    nc_free_tensor(sum);
    fprintf(stderr,
            "ATTR_NAMED_GRAD block=%d name=%s grad=%08x grad_elems=%zu "
            "param_elems=%zu energy=%a finite=%d\n",
            model->named_gradient_block, parameter->name,
            nc_tensor_get_hash(gradient),
            attribution_tensor_element_count(gradient),
            attribution_tensor_element_count(*parameter->pval),
            energy, finite);
}

static void backward_cb''',
        "named-gradient helper",
    )
    source = replace_once(
        source,
        """static void backward_cb(void *opaque, NCTensor *yg, NCTensor *get_col_index)
{
#ifdef DUMP_GRAD_NORM""",
        """static void backward_cb(void *opaque, NCTensor *yg, NCTensor *get_col_index)
{
    if (attribution_backward_model &&
        attribution_backward_model->named_gradient_capture)
        attribution_dump_named_gradient(attribution_backward_model,
                                        (NCParam *)opaque, yg);
#ifdef DUMP_GRAD_NORM""",
        "named-gradient callback",
    )
    source = replace_once(
        source,
        """                trf_set_gradient_range(s, 0, 32, 64);
                if (s->midpoint_arm == ATTR_O ||
                    s->midpoint_arm == ATTR_OK ||
                    s->midpoint_arm == ATTR_S) {
                    ((TransformerModel *)s)->head_only_backward = TRUE;
                    attribution_backward_model = (TransformerModel *)s;
                }
                s->model_class->model_eval_gradient(s, midpoint_expected);
                attribution_backward_model = NULL;
                ((TransformerModel *)s)->head_only_backward = FALSE;""",
        """                trf_set_gradient_range(s, 0, 32, 64);
                if (s->midpoint_arm == ATTR_F) {
                    ((TransformerModel *)s)->named_gradient_capture = TRUE;
                    ((TransformerModel *)s)->named_gradient_block = block_idx;
                    attribution_backward_model = (TransformerModel *)s;
                } else if (s->midpoint_arm == ATTR_O ||
                           s->midpoint_arm == ATTR_OK ||
                           s->midpoint_arm == ATTR_S) {
                    ((TransformerModel *)s)->head_only_backward = TRUE;
                    attribution_backward_model = (TransformerModel *)s;
                }
                s->model_class->model_eval_gradient(s, midpoint_expected);
                ((TransformerModel *)s)->named_gradient_capture = FALSE;
                ((TransformerModel *)s)->named_gradient_block = -1;
                attribution_backward_model = NULL;
                ((TransformerModel *)s)->head_only_backward = FALSE;""",
        "F-arm named-gradient window",
    )
    path.write_text(source)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    args = parser.parse_args()
    materialize(args.source_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
