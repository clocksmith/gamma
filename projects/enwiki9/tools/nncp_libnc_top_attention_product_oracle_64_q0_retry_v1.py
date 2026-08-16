#!/usr/bin/env python3
"""Retry the top attention oracle after repairing C declaration order."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import nncp_libnc_top_attention_product_oracle_64_q0_v1 as base


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_attention_product_oracle_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T172243Z_21e3211378.json"
)
FAILED_GUARD = ROOT / (
    "results/nncp_libnc_top_attention_product_oracle_64_q0_v1/guard.json"
)
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_attention_product_oracle_64_q0_retry_v1_materializer.py"
)
DECLARATIONS = """enum GammaTopAttnKind {
    GAMMA_TOP_ATTN_PROBABILITY,
    GAMMA_TOP_ATTN_ATTENDED,
    GAMMA_TOP_ATTN_KIND_COUNT,
};

static NCTensor *gamma_top_attn_probe_attach(
    NCTensor *value, int layer, int state, enum GammaTopAttnKind kind);
static int gamma_top_attn_probe_capture(
    void *opaque, NCTensor *gradient, NCTensor *column_index);

"""
LATE_ENUM = """enum GammaTopAttnKind {
    GAMMA_TOP_ATTN_PROBABILITY = 0,
    GAMMA_TOP_ATTN_ATTENDED = 1,
    GAMMA_TOP_ATTN_KIND_COUNT = 2,
};

"""


base.CANDIDATE_ID = CANDIDATE_ID
base.PROGRAM = PROGRAM
base.RESULT = RESULT
base.WORK = RESULT / "work"
base.PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
base.RUNNER = Path(__file__).resolve()
base.MATERIALIZER = MATERIALIZER
base.DECLARATIONS = DECLARATIONS


def patch_teacher(source: str) -> str:
    capture = base.capture_base.source_capture.capture
    source = capture.base.patch_teacher(source)
    helper = base.PROBE_SOURCE.read_text()
    if helper.count(LATE_ENUM) != 1:
        raise ValueError("late top-attention enum source differs")
    helper = helper.replace(LATE_ENUM, "", 1)
    source = capture.replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        helper + "\nstatic FILE *teacher_trace_file;\n",
    )
    source = capture.replace_once(
        source,
        "static NCTensor *layer_norm(",
        DECLARATIONS + "static NCTensor *layer_norm(",
    )
    source = capture.replace_once(
        source,
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n",
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n"
        "        gamma_top_attn_probe_set_block(block_idx);\n",
    )
    source = capture.replace_once(
        source,
        "            t1 = nc_soft_max(t0);\n"
        "            t0 = nc_matmul(value, nc_dup_tensor(t1));",
        "            t1 = nc_soft_max(t0);\n"
        "            t1 = gamma_top_attn_probe_attach(\n"
        "                t1, layer_idx, output_index,\n"
        "                GAMMA_TOP_ATTN_PROBABILITY);\n"
        "            t0 = nc_matmul(value, nc_dup_tensor(t1));",
    )
    source = capture.replace_once(
        source,
        "            tl->va_nodes[output_index] = node;\n"
        "        }\n"
        "        \n"
        "        if (tl->w_o) {",
        "            tl->va_nodes[output_index] = node;\n"
        "            t0 = gamma_top_attn_probe_attach(\n"
        "                t0, layer_idx, output_index,\n"
        "                GAMMA_TOP_ATTN_ATTENDED);\n"
        "        }\n"
        "        \n"
        "        if (tl->w_o) {",
    )
    source = capture.replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_top_attn_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


base.patch_teacher = patch_teacher
base.capture_base.patch_teacher = patch_teacher
base.capture_base.PROGRAM_DESCRIPTOR = base.PROGRAM_DESCRIPTOR
base.capture_base.RUNNER = base.RUNNER
base.capture_base.MATERIALIZER = base.MATERIALIZER

original_require_inputs = base.require_inputs


def require_inputs(experiment: dict[str, Any]) -> None:
    original_require_inputs(experiment)
    inputs = {item["id"]: item for item in experiment["inputs"]}
    if inputs.get("failed-attempt-reflection") != base.reference(
        FAILED_REFLECTION, "failed-attempt-reflection"
    ):
        raise ValueError("retry experiment does not bind the failed reflection")
    if inputs.get("failed-attempt-guard") != base.reference(
        FAILED_GUARD, "failed-attempt-guard"
    ):
        raise ValueError("retry experiment does not bind the failed guard")
    reflection = json.loads(FAILED_REFLECTION.read_text())
    guard = json.loads(FAILED_GUARD.read_text())
    if not (
        reflection["validity"]["classification"] == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
        and guard["status"] == "complete"
        and guard["returncode"] == 1
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
    ):
        raise ValueError("failed attempt does not authorize the retry")


base.require_inputs = require_inputs


if __name__ == "__main__":
    raise SystemExit(base.main())
