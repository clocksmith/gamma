#!/usr/bin/env python3
"""Freeze the complete open layer-19 w_o gradient evaluation."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_w_o_gradient_full_post_add_64_q0_v1"
PARENT_ID = "nncp_open_w_o_weight_slice_post_add_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T163008Z_9e18c10ab5.json"
)
SOURCE_INPUT = ROOT / (
    "results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1/"
    "source-w-o-input.bf16"
)
UPSTREAM_ADJOINT = ROOT / (
    "results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/"
    "source-exact-pre-ff-total-adjoint.bf16"
)
RETAINED_GRADIENT = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture/"
    "gradients/0007_w_o_19.bin"
)
RETAINED_GRADIENT_META = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture/"
    "gradients/0007_w_o_19.meta"
)
RUNNER = ROOT / "tools/nncp_open_w_o_gradient_full_post_add_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
EVALUATOR = ROOT / (
    "programs/nncp_open_w_o_gradient_full_post_add_64_q0_v1/"
    "w_o_gradient_full_post_add.cpp"
)
DESCRIPTOR = ROOT / "programs" / CANDIDATE_ID / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 500_000
HYPOTHESIS = (
    "The slice-validated LibNC-free chronological post-dot prior-add BF16/FMA "
    "kernel exactly reconstructs all 1,048,576 retained w_o_19 gradient words "
    "with deterministic replay, while a sign-negated control differs."
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"experiment input is not a project file: {path}")
    return {
        "id": identifier,
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(
    identifier: str, measurement_id: str, operator: str, threshold: object
) -> dict[str, object]:
    return {
        "id": identifier,
        "measurement": measurement_id,
        "operator": operator,
        "threshold": threshold,
    }


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{suffix}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_revision = ROOT / json.loads(
        (PARENT_RESULT / "decision.json").read_text()
    )["candidateRevision"]["receipt"]["path"]
    inputs = [
        reference(PARENT_RESULT / "decision.json", "parent-decision"),
        reference(PARENT_RESULT / "execution.json", "parent-execution"),
        reference(PARENT_RESULT / "guard.json", "parent-guard"),
        reference(PARENT_REFLECTION, "parent-reflection"),
        reference(SOURCE_INPUT, "source-w-o-input"),
        reference(UPSTREAM_ADJOINT, "open-post-w-o-adjoint"),
        reference(RETAINED_GRADIENT, "retained-w-o-gradient"),
        reference(RETAINED_GRADIENT_META, "retained-w-o-gradient-meta"),
        reference(EVALUATOR, "evaluator-source"),
        reference(RUNNER, "runner"),
        reference(MATERIALIZER, "materializer"),
        reference(DESCRIPTOR, "program-descriptor"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_identifier(path)))
            present.add(relative)
    measurements = [
        measurement("antecedentsPass", "boolean", "The exact slice result and full operands remain hash-bound."),
        measurement("gradientElementCount", "BF16 elements", "Words in the complete 1,024-by-1,024 w_o_19 gradient."),
        measurement("treatmentMismatchCount", "BF16 elements", "Treatment words differing from the retained full gradient."),
        measurement("maximumTreatmentAbsoluteError", "float32 value", "Maximum treatment/comparator error."),
        measurement("negatedControlMismatchCount", "BF16 elements", "Sign-negated control words differing from the retained full gradient."),
        measurement("evaluationReplayIdentical", "boolean", "Both complete treatment/control evaluations are byte-identical."),
        measurement("forbiddenDynamicDependencyCount", "libraries", "Dependencies on LibNC, GGML, CUDA, OpenMP, or BLAS."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source."),
        measurement("guardedWorkRootPass", "boolean", "Transient work was removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-elements", "gradientElementCount", "eq", 1048576),
        predicate("p-treatment", "treatmentMismatchCount", "eq", 0),
        predicate("p-maximum", "maximumTreatmentAbsoluteError", "eq", 0.0),
        predicate("p-negative", "negatedControlMismatchCount", "gt", 0),
        predicate("p-replay", "evaluationReplayIdentical", "eq", True),
        predicate("p-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
        predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
        predicate("p-work", "guardedWorkRootPass", "eq", True),
    ]
    experiment = {
        "schema": "gamma.enwiki9.adaptive-experiment-contract.v1",
        "objective": research_contracts.objective_binding(),
        "experimentId": CANDIDATE_ID,
        "proposalId": CANDIDATE_ID,
        "status": "frozen",
        "registrationTiming": "prospective",
        "evidenceClass": "oracle",
        "objectiveCreditBytes": 0,
        "parent": {
            "candidateId": PARENT_ID,
            "revision": {
                key: value
                for key, value in reference(
                    parent_revision, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": HYPOTHESIS,
            "falsification": "Any full-gradient mismatch, dead negative control, replay difference, forbidden dependency, source failure, or resource failure rejects full expansion.",
        },
        "changedMechanism": "Expand only the exact slice-validated post-dot-add treatment from 128 to all 1,024 output features, retain sign negation as the causal control, and replay both populations.",
        "invariants": [
            "The input, output adjoint, state order, stream reduction, arithmetic cell, BF16 materialization, and comparator remain unchanged from the exact slice.",
            "The evaluator has no LibNC, GGML, CUDA, OpenMP, or BLAS dependency.",
            "The source input and retained gradient remain zero-credit oracle evidence and cannot ship.",
        ],
        "controls": [
            {"id": "full-treatment", "role": "treatment", "definition": "Apply the exact post-dot-add cell to every w_o_19 feature."},
            {"id": "retained-full-gradient", "role": "comparator", "definition": "Compare every treatment word to the independently retained production w_o_19 gradient."},
            {"id": "sign-negated", "role": "negative", "definition": "Negate every incoming adjoint under the identical full schedule."},
            {"id": "replay", "role": "replay", "definition": "Repeat both complete full-matrix populations byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 w_o_19 matrix-gradient words",
            "scopeBytes": 2097152,
            "scopeSymbols": 1048576,
            "selection": "Every output and input feature over all 64 chronological states and 32 streams.",
            "coordinate": "input-feature-major, output-feature-minor",
        },
        "causalBoundary": {
            "availableInformation": [
                "The exact 128-row treatment, sealed source input, exact open output adjoint, and retained full gradient comparator.",
                "The expansion changes coverage only.",
            ],
            "forbiddenInformation": [
                "LibNC execution, tuning to full-gradient mismatches, tolerance, fitted correction, or future symbols.",
                "Claiming open forward completion, transpose completion, compression gain, or Hutter credit.",
            ],
        },
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "uncertaintyRisk": 0.05,
            "interactionRisk": 0.0,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-treatment", "treatmentMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-exact-w-o-19-gradient.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
