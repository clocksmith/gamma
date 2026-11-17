"""Opt-in prompt-conditioned fast-weight adaptation (`FastWeightSession`, v3)."""

from gamma.fastweight.adapter import (
    FastWeightAdapter,
    FastWeightSession,
    derive_fastweight,
    extract_query_features_for_donor,
    find_default_context_split,
    make_random_adapter,
    make_zero_adapter,
)

__all__ = [
    "FastWeightAdapter",
    "FastWeightSession",
    "derive_fastweight",
    "extract_query_features_for_donor",
    "find_default_context_split",
    "make_random_adapter",
    "make_zero_adapter",
]
