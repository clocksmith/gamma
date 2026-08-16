#!/usr/bin/env python3
"""Retry the GEGLU branch capture with a unique source anchor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import nncp_libnc_top_geglu_branch_adjoints_64_q0_v1 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
FAILURE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T100841Z_829771fc57.json"
)
original_require_inputs = parent.require_inputs


def patch_teacher(source: str) -> str:
    source_parent = parent.parent
    source = source_parent.capture.base.patch_teacher(source)
    source = source_parent.capture.replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        parent.PROBE_SOURCE.read_text() + "\nstatic FILE *teacher_trace_file;\n",
    )
    source = source_parent.capture.replace_once(
        source,
        "static NCTensor *layer_norm(",
        parent.DECLARATIONS + "static NCTensor *layer_norm(",
    )
    source = source_parent.capture.replace_once(
        source,
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n",
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n"
        "        gamma_top_geglu_probe_set_block(block_idx);\n",
    )
    old_geglu = (
        "        case FF_ACT_GEGLU:\n"
        "            {\n"
        "                NCTensor *tab2[2];\n"
        "                nc_split(tab2, t0, 2, NULL, 0);\n"
        "#if 1\n"
    )
    new_geglu = (
        "        case FF_ACT_GEGLU:\n"
        "            {\n"
        "                NCTensor *tab2[2];\n"
        "                nc_split(tab2, t0, 2, NULL, 0);\n"
        "                gamma_top_geglu_input_dump(\n"
        "                    tab2[0], layer_idx, output_index, 0);\n"
        "                gamma_top_geglu_input_dump(\n"
        "                    tab2[1], layer_idx, output_index, 1);\n"
        "                tab2[0] = gamma_top_geglu_probe_attach(\n"
        "                    tab2[0], layer_idx, output_index, 0);\n"
        "                tab2[1] = gamma_top_geglu_probe_attach(\n"
        "                    tab2[1], layer_idx, output_index, 1);\n"
        "#if 1\n"
    )
    source = source_parent.capture.replace_once(source, old_geglu, new_geglu)
    source = source_parent.capture.replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_top_geglu_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


def require_inputs(experiment: dict[str, Any]) -> None:
    original_require_inputs(experiment)
    inputs = {item["id"]: item for item in experiment["inputs"]}
    identifier = "source-anchor-failure-reflection"
    if inputs.get(identifier) != parent.parent.capture.reference(
        FAILURE_REFLECTION, identifier
    ):
        raise ValueError("source-anchor failure reflection drifted")
    reflection = json.loads(FAILURE_REFLECTION.read_text())
    if not (
        reflection["validity"]["classification"] == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
    ):
        raise ValueError("source-anchor retry is not authorized")


def main() -> int:
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.PROGRAM = PROGRAM
    parent.RESULT = RESULT
    parent.WORK = RESULT / "work"
    parent.PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
    parent.RUNNER = Path(__file__).resolve()
    parent.MATERIALIZER = ROOT / (
        "tools/nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v1_materializer.py"
    )
    parent.patch_teacher = patch_teacher
    parent.require_inputs = require_inputs
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
