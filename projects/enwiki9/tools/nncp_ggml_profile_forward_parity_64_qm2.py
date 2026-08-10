#!/usr/bin/env python3
"""Capture and compare the decoder-compatible sequential production path."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

import nncp_ggml_profile_forward_parity_64_qm1 as parent


base = parent.base
base.CANDIDATE_ID = "nncp_ggml_profile_forward_parity_64_qm2_v1"
base.PROGRAM = base.ROOT / "programs" / base.CANDIDATE_ID
base.RESULT = base.ROOT / "results" / base.CANDIDATE_ID
base.HOOK_SOURCE = base.ROOT / "tools/nncp_production_fixture_hook_qm2.c"

_parent_patch_teacher = base.patch_teacher


def patch_teacher(source: str) -> str:
    source = _parent_patch_teacher(source)
    source = base.replace_once(
        source,
        "#ifdef DUMP_HASH\n"
        "        gamma_dump_layer_tensor(layer_idx, \"key_state\", key);\n"
        "        gamma_dump_layer_tensor(layer_idx, \"value_state\", value);\n"
        "#endif\n",
        "",
    )
    source = base.replace_once(
        source,
        "            value = nc_dup_tensor(tl->mem_value);\n            \n"
        "            /* cross product term */",
        "            value = nc_dup_tensor(tl->mem_value);\n"
        "#ifdef DUMP_HASH\n"
        "            gamma_dump_layer_tensor(layer_idx, \"key_state\", key);\n"
        "            gamma_dump_layer_tensor(layer_idx, \"value_state\", value);\n"
        "#endif\n"
        "            \n"
        "            /* cross product term */",
    )
    source = base.replace_once(
        source,
        "            t1 = nc_soft_max(t0);\n"
        "            t0 = nc_matmul(value, nc_dup_tensor(t1));",
        "            t1 = nc_soft_max(t0);\n"
        "#ifdef DUMP_HASH\n"
        "            gamma_dump_layer_tensor(layer_idx, \"attention_probability\", t1);\n"
        "#endif\n"
        "            t0 = nc_matmul(value, nc_dup_tensor(t1));",
    )
    source = base.replace_first_of(
        source,
        "                output_host = s->model_class->model_eval(s, cur_state, input);",
        "                if (cur_state == 0)\n"
        "                    gamma_fixture_begin(s, input, block_buf, block_stride,\n"
        "                                        block_rem, block_idx);\n"
        "                output_host = s->model_class->model_eval(s, cur_state, input);",
        2,
    )
    source = base.replace_first_of(
        source,
        "                nc_free_tensor(output_host);\n"
        "            }\n"
        "        } else {",
        "                nc_free_tensor(output_host);\n"
        "            }\n"
        "            if (gamma_fixture_active) {\n"
        "                gamma_fixture_finish();\n"
        "                exit(0);\n"
        "            }\n"
        "        } else {",
        2,
    )
    return source


def one_position_labels() -> list[str]:
    labels = ["embedding_input"]
    layer_labels = (
        "attention_input",
        "key_state",
        "value_state",
        "relative_weight",
        "relative_bias",
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


def digest_records(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def compare_forward(
    fixture: Path, manifest: dict[str, object], observed: Path
) -> tuple[list[dict[str, object]], dict[str, object]]:
    unique_labels = one_position_labels()
    expected_names = {f"{label}.f32" for label in unique_labels} | {
        "tree_path.u32le",
        "complete.marker",
    }
    actual_names = {path.name for path in observed.iterdir() if path.is_file()}
    if actual_names != expected_names:
        raise ValueError(
            f"open output set mismatch: missing={sorted(expected_names-actual_names)} "
            f"extra={sorted(actual_names-expected_names)}"
        )
    grouped: dict[str, list[dict[str, object]]] = {label: [] for label in unique_labels}
    for record in manifest["internal"]:
        grouped[record["label"]].append(record)
    comparisons = []
    singleton_suffixes = (
        "_key_state",
        "_value_state",
        "_relative_weight",
        "_relative_bias",
    )
    for label in unique_labels:
        records = grouped[label]
        if len(records) != 64:
            raise ValueError(f"sequential fixture population mismatch: {label}")
        if label.endswith(("_key_state", "_value_state")):
            chosen = [records[-1]]
        elif label.endswith(("_relative_weight", "_relative_bias")):
            chosen = [records[0]]
        else:
            chosen = records
        paths = [fixture / "internal" / record["payload"] for record in chosen]
        reference = np.concatenate(
            [np.fromfile(path, dtype="<f4") for path in paths]
        )
        candidate_path = observed / f"{label}.f32"
        candidate = np.fromfile(candidate_path, dtype="<f4")
        if label.endswith("_attention_probability"):
            candidate = (
                candidate.reshape((8, 64, 320)).transpose((1, 0, 2)).reshape(-1)
            )
        if reference.shape != candidate.shape or not np.isfinite(candidate).all():
            raise ValueError(f"sequential open tensor geometry mismatch: {label}")
        difference = candidate.astype(np.float64) - reference.astype(np.float64)
        comparisons.append(
            {
                "label": label,
                "elements": int(reference.size),
                "maximum_absolute_error": float(np.abs(difference).max(initial=0.0)),
                "mean_absolute_error": float(np.abs(difference).mean()),
                "expected_aggregate_sha256": digest_records(paths),
                "observed_sha256": base.sha256(candidate_path),
            }
        )

    expected_tree = (fixture / "tree_path.u32le").read_bytes()
    observed_tree = (observed / "tree_path.u32le").read_bytes()
    if expected_tree[:16] != observed_tree[:16] or len(expected_tree) != len(observed_tree):
        raise ValueError("tree header or row-count mismatch")
    expected_rows = np.frombuffer(expected_tree[16:], dtype="<u4").reshape((-1, 8))
    observed_rows = np.frombuffer(observed_tree[16:], dtype="<u4").reshape((-1, 8))
    topology_columns = [0, 1, 2, 3, 4, 5, 7]
    branch = {
        "rows": int(expected_rows.shape[0]),
        "tree_topology_and_symbol_order_disagreements": int(
            np.count_nonzero(
                expected_rows[:, topology_columns] != observed_rows[:, topology_columns]
            )
        ),
        "truth_path_disagreements": int(
            np.count_nonzero(expected_rows[:, 7] != observed_rows[:, 7])
        ),
        "maximum_integer_probability_count_difference": int(
            np.abs(
                expected_rows[:, 6].astype(np.int64)
                - observed_rows[:, 6].astype(np.int64)
            ).max(initial=0)
        ),
        "expected_sha256": base.sha256(fixture / "tree_path.u32le"),
        "observed_sha256": base.sha256(observed / "tree_path.u32le"),
    }
    return comparisons, branch


base.patch_teacher = patch_teacher
base.expected_internal_labels = expected_internal_labels
base.compare_forward = compare_forward


if __name__ == "__main__":
    raise SystemExit(base.main())
