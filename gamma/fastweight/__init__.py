"""Opt-in prompt-conditioned fast-weight adaptation (`FastWeightSession`, v3/v4)."""

from gamma.fastweight.adapter import (
    ClosedFormLayerLoRA,
    FastWeightAdapter,
    FastWeightSession,
    compile_closed_form_layer_lora,
    derive_continuous_cache_knn,
    derive_fastweight,
    discover_support_anchors,
    extract_query_features_for_donor,
    find_default_context_split,
    make_random_adapter,
    make_random_layer_lora,
    make_zero_adapter,
    make_zero_layer_lora,
)

__all__ = [
    "ClosedFormLayerLoRA",
    "FastWeightAdapter",
    "FastWeightSession",
    "compile_closed_form_layer_lora",
    "derive_continuous_cache_knn",
    "derive_fastweight",
    "discover_support_anchors",
    "extract_query_features_for_donor",
    "find_default_context_split",
    "make_random_adapter",
    "make_random_layer_lora",
    "make_zero_adapter",
    "make_zero_layer_lora",
]
