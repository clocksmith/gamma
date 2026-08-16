#!/usr/bin/env python3
"""Freeze the open layer-19 w_o post-dot-add gradient slice."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_w_o_weight_slice_post_add_64_q0_v1"
PARENT_ID = "nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T162351Z_97a6519638.json"
)
UPSTREAM = ROOT / "results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1"
UPSTREAM_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T155508Z_53d5388d2c.json"
)
SCHEDULE = ROOT / "results/nncp_open_ff1_weight_slice_post_add_64_q0_v1"
SCHEDULE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T120602Z_ec1474d292.json"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture"
RUNNER = ROOT / "tools/nncp_open_w_o_weight_slice_post_add_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
EVALUATOR = ROOT / (
    "programs/nncp_open_w_o_weight_slice_post_add_64_q0_v1/"
    "w_o_weight_slice_post_add.cpp"
)
DESCRIPTOR = ROOT / "programs" / CANDIDATE_ID / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 500_000
HYPOTHESIS = (
    "The previously attributed LibNC-free chronological post-dot prior-add "
    "BF16/FMA kernel exactly reconstructs the first 128 output rows of the "
    "retained w_o_19 gradient from the sealed pre-w_o input and independently "
    "opened post-w_o adjoint, while reversed and sign-negated controls differ."
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
        reference(PARENT_RESULT / "source-w-o-input.bf16", "source-w-o-input"),
        reference(UPSTREAM / "decision.json", "upstream-decision"),
        reference(UPSTREAM / "execution.json", "upstream-execution"),
        reference(UPSTREAM / "guard.json", "upstream-guard"),
        reference(UPSTREAM_REFLECTION, "upstream-reflection"),
        reference(UPSTREAM / "source-exact-pre-ff-total-adjoint.bf16", "open-post-w-o-adjoint"),
        reference(SCHEDULE / "decision.json", "schedule-decision"),
        reference(SCHEDULE / "execution.json", "schedule-execution"),
        reference(SCHEDULE_REFLECTION, "schedule-reflection"),
        reference(FIXTURE / "gradients/0007_w_o_19.bin", "retained-w-o-gradient"),
        reference(FIXTURE / "gradients/0007_w_o_19.meta", "retained-w-o-gradient-meta"),
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
        measurement("antecedentsPass", "boolean", "The exact source input, open output adjoint, retained gradient, and prior arithmetic contract remain hash-bound."),
        measurement("sliceElementCount", "BF16 elements", "Words in the 128-by-1,024 w_o_19 gradient slice."),
        measurement("treatmentMismatchCount", "BF16 elements", "Post-dot-add treatment words differing from the retained gradient slice."),
        measurement("maximumTreatmentAbsoluteError", "float32 value", "Maximum treatment/comparator error."),
        measurement("priorControlMismatchCount", "BF16 elements", "Prior-initialized FMA control words differing from the retained slice."),
        measurement("nonfusedControlMismatchCount", "BF16 elements", "Nonfused control words differing from the retained slice."),
        measurement("reverseControlMismatchCount", "BF16 elements", "Reverse-state control words differing from the retained slice."),
        measurement("negatedControlMismatchCount", "BF16 elements", "Sign-negated control words differing from the retained slice."),
        measurement("evaluationReplayIdentical", "boolean", "Two complete open evaluations are byte-identical."),
        measurement("forbiddenDynamicDependencyCount", "libraries", "Evaluator dependencies on LibNC, GGML, CUDA, OpenMP, or BLAS."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source."),
        measurement("guardedWorkRootPass", "boolean", "Transient work was removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-elements", "sliceElementCount", "eq", 131072),
        predicate("p-treatment", "treatmentMismatchCount", "eq", 0),
        predicate("p-maximum", "maximumTreatmentAbsoluteError", "eq", 0.0),
        predicate("p-reverse-control", "reverseControlMismatchCount", "gt", 0),
        predicate("p-negated-control", "negatedControlMismatchCount", "gt", 0),
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
            "falsification": "Any treatment mismatch, dead control, nondeterministic replay, forbidden dependency, source failure, or resource failure rejects transfer of the arithmetic contract to w_o_19.",
        },
        "changedMechanism": "Apply the already attributed LibNC-free 32-stream post-dot prior-add BF16/FMA state update to a prospectively frozen 128-row w_o_19 slice, with prior-initialized, nonfused, reverse-state, and sign-negated controls.",
        "invariants": [
            "The source pre-w_o input and independently opened post-w_o adjoint are used verbatim in state-major order.",
            "The comparator is a prospectively bound slice of the retained production w_o_19 gradient.",
            "The evaluator has no LibNC, GGML, CUDA, OpenMP, or BLAS dependency.",
            "No source tensor or retained gradient can ship in a Gamma codec; this lane earns zero objective credit.",
        ],
        "controls": [
            {"id": "post-dot-add", "role": "treatment", "definition": "Accumulate 32 sequential AVX2 FMAs from zero, add the prior BF16 value, then round to BF16 after each chronological state."},
            {"id": "prior-fma", "role": "comparator", "definition": "Initialize the FMA chain with the decoded prior gradient."},
            {"id": "nonfused", "role": "comparator", "definition": "Use separate multiply and add operations."},
            {"id": "reverse-state", "role": "shifted", "definition": "Apply the treatment in reverse state order."},
            {"id": "negated", "role": "negative", "definition": "Negate every incoming adjoint while preserving the treatment schedule."},
            {"id": "replay", "role": "replay", "definition": "Repeat all five cells byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 w_o_19 matrix-gradient words",
            "scopeBytes": 262144,
            "scopeSymbols": 131072,
            "selection": "The first 128 output features for all 1,024 input features over all 64 chronological states and 32 streams.",
            "coordinate": "input-feature-major, output-feature-minor",
        },
        "causalBoundary": {
            "availableInformation": [
                "The sealed source pre-w_o input, exact open post-w_o adjoint, prior exact FF1 arithmetic contract, and retained w_o_19 comparator slice.",
                "Only the prospectively frozen cells are evaluated.",
            ],
            "forbiddenInformation": [
                "LibNC execution, fitting to mismatch coordinates, tolerance, future symbols, or editing the sealed source oracle.",
                "Claiming open forward completion, a full w_o_19 gradient, compression improvement, or Hutter credit from this slice.",
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
            "uncertaintyRisk": 0.1,
            "interactionRisk": 0.1,
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
            f"results/{CANDIDATE_ID}/source-exact-w-o-gradient-slice.bf16",
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
