#!/usr/bin/env python3
"""Correction-only sequential fixture manifest-order successor."""

import nncp_ggml_profile_forward_parity_64_qm2 as parent


base = parent.base
base.CANDIDATE_ID = "nncp_ggml_profile_forward_parity_64_qm3_v1"
base.PROGRAM = base.ROOT / "programs" / base.CANDIDATE_ID
base.RESULT = base.ROOT / "results" / base.CANDIDATE_ID


def one_position_labels() -> list[str]:
    labels = ["embedding_input"]
    layer_labels = (
        "attention_input",
        "relative_weight",
        "relative_bias",
        "key_state",
        "value_state",
        "attention_probability",
        "attention_residual",
        "attention_output",
        "ff1_output",
        "geglu_output",
        "feedforward_residual",
        "layer_hidden",
    )
    for layer in range(20):
        labels.extend(f"layer_{layer:02d}_{label}" for label in layer_labels)
    labels.extend(("final_hidden", "logits", "output"))
    return labels


def expected_internal_labels() -> list[str]:
    return one_position_labels() * 64


parent.one_position_labels = one_position_labels
base.expected_internal_labels = expected_internal_labels


if __name__ == "__main__":
    raise SystemExit(base.main())
