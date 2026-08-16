#!/usr/bin/env python3
"""Freeze the state-reduced layer-19 pre-FF backward retry."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1"
FAILED_ID = "nncp_open_top_pre_ff_rmsnorm_backward_64_q0_v1"
FAILED_EXPERIMENT = ROOT / (
    f"operations/adaptive/experiments/{FAILED_ID}.json"
)
FAILED_RESULT = ROOT / "results" / FAILED_ID
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T130752Z_2641246e8c.json"
)
RUNNER = ROOT / (
    "tools/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0.py"
)
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
BACKWARD_MATERIALIZER = PROGRAM / "materialize_pre_ff_backward.py"
DESCRIPTOR = PROGRAM / "program.py"
DIRECT_ADJOINT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    experiment = json.loads(FAILED_EXPERIMENT.read_text())
    failed_decision = json.loads((FAILED_RESULT / "decision.json").read_text())
    failed_revision = ROOT / failed_decision["candidateRevision"]["receipt"][
        "path"
    ]
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": FAILED_ID,
        "revision": {
            "path": failed_revision.relative_to(ROOT).as_posix(),
            "sha256": f"sha256:{base.sha256(failed_revision)}",
        },
    }
    experiment["hypothesis"] = {
        "claim": (
            "The correct final-normalization input adjoint, width-scaled "
            "centered normalization arithmetic, and chronological 32-stream "
            "BF16 state reductions reproduce every layer-19 pre-FF total-"
            "adjoint, ln_g_39, and ln_b_39 word exactly."
        ),
        "falsification": (
            "Any total-adjoint or affine-gradient mismatch, dead control, "
            "replay failure, dependency violation, or resource failure "
            "rejects the combined boundary correction."
        ),
    }
    experiment["changedMechanism"] = (
        "Replace the pre-final-normalization direct branch with the exact "
        "final-normalization input adjoint, use the previously distinguished "
        "width-scaled centered normalization order, and replace flat affine "
        "reductions with chronological 32-stream panels rounded to BF16 after "
        "each of 64 states."
    )
    experiment["controls"][0] = {
        "id": "state-reduced-width-scaled-backward",
        "role": "treatment",
        "definition": (
            "Use the corrected direct branch, width-scaled centered input "
            "backward, and state-wise BF16 affine reductions."
        ),
    }
    experiment["causalBoundary"]["availableInformation"] = [
        "The failed exact replay and its mismatch counts, not comparator coordinates.",
        "The prior exact final-normalization input adjoint and independently promoted state-wise BF16 reduction contract.",
        "The prior source-attributed mean-versus-width normalization arithmetic variants.",
        "The source total-adjoint and retained affine-gradient comparators only after both new open populations exist.",
    ]
    experiment["invariants"] = [
        "The forward model, parameters, state, sample order, normalized FF adjoint, retained gradients, and source comparators remain unchanged.",
        "Only direct-branch identity, centered scalar placement, and affine reduction schedule change.",
        "The arithmetic implementation is digest-frozen before either complete replay is compared with source outputs.",
        "Both complete open replays are generated before source comparison; tolerance and coordinate repair are forbidden.",
        "Neither executable has a LibNC, GGML, BLAS, OpenMP, or CUDA dynamic dependency.",
        "The source oracle is zero-credit validation and cannot ship in a Gamma codec.",
    ]
    replacements = {
        "direct-residual-adjoint": base.reference(
            DIRECT_ADJOINT, "direct-residual-adjoint"
        ),
        "pre-ff-backward-materializer": base.reference(
            BACKWARD_MATERIALIZER, "pre-ff-backward-materializer"
        ),
        "runner": base.reference(RUNNER, "runner"),
        "materializer": base.reference(MATERIALIZER, "materializer"),
        "program-descriptor": base.reference(DESCRIPTOR, "program-descriptor"),
    }
    inputs = [replacements.get(item["id"], item) for item in experiment["inputs"]]
    additions = [
        base.reference(FAILED_RESULT / "decision.json", "failed-decision"),
        base.reference(FAILED_RESULT / "execution.json", "failed-execution"),
        base.reference(FAILED_RESULT / "guard.json", "failed-guard"),
        base.reference(FAILED_REFLECTION, "failed-reflection"),
    ]
    existing_ids = {item["id"] for item in inputs}
    inputs.extend(item for item in additions if item["id"] not in existing_ids)
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present_paths.add(relative)
    experiment["inputs"] = inputs
    experiment["outputs"] = [
        f"results/{CANDIDATE_ID}/{Path(path).name}"
        for path in experiment["outputs"]
    ]
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    )
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    try:
        research_contracts.validate_artifact(OUTPUT)
    except Exception:
        OUTPUT.unlink(missing_ok=True)
        raise
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
