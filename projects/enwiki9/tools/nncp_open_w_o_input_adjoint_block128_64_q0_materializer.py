#!/usr/bin/env python3
"""Freeze the ordered-panel open layer-19 w_o transpose."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_w_o_input_adjoint_block128_64_q0_v1"
PARENT_ID = "nncp_open_w_o_gradient_full_post_add_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T163533Z_7a29124cd9.json"
)
SOURCE = ROOT / "results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T162351Z_97a6519638.json"
)
INCOMING = ROOT / (
    "results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/"
    "source-exact-pre-ff-total-adjoint.bf16"
)
PANEL = ROOT / "results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1"
PANEL_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T123635Z_f1f6615808.json"
)
RUNNER = ROOT / "tools/nncp_open_w_o_input_adjoint_block128_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
EVALUATOR = ROOT / (
    "programs/nncp_open_w_o_input_adjoint_block128_64_q0_v1/"
    "w_o_transpose_block128.cpp"
)
DESCRIPTOR = ROOT / "programs" / CANDIDATE_ID / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 500_000
HYPOTHESIS = (
    "Eight ordered 128-feature FMA panels over the sealed initial w_o_19 "
    "matrix and exact open post-w_o adjoint reproduce all 2,097,152 source "
    "pre-w_o input-adjoint words, while an unblocked reduction and sign-negated "
    "input differ."
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
        reference(SOURCE / "decision.json", "source-decision"),
        reference(SOURCE / "execution.json", "source-execution"),
        reference(SOURCE_REFLECTION, "source-reflection"),
        reference(SOURCE / "source-w-o-input-adjoint.bf16", "source-w-o-input-adjoint"),
        reference(SOURCE / "source-initial-w-o-19.bf16", "source-initial-w-o-19"),
        reference(INCOMING, "open-post-w-o-adjoint"),
        reference(PANEL / "decision.json", "panel-decision"),
        reference(PANEL / "execution.json", "panel-execution"),
        reference(PANEL_REFLECTION, "panel-reflection"),
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
        measurement("antecedentsPass", "boolean", "The exact full gradient, source oracle, initial matrix, open incoming adjoint, and prior panel contract remain hash-bound."),
        measurement("adjointElementCount", "BF16 elements", "Words in the complete pre-w_o input adjoint."),
        measurement("reductionPanelCount", "panels", "Ordered 128-feature reduction panels."),
        measurement("block128SourceMismatchCount", "BF16 elements", "Ordered-panel treatment words differing from the source oracle."),
        measurement("maximumBlock128AbsoluteError", "float32 value", "Maximum treatment/oracle error."),
        measurement("unblockedSourceMismatchCount", "BF16 elements", "Unblocked control words differing from the source oracle."),
        measurement("negatedControlMismatchCount", "BF16 elements", "Sign-negated control words differing from the source oracle."),
        measurement("arithmeticCellsDiffer", "boolean", "Ordered-panel and unblocked populations differ."),
        measurement("evaluationReplayIdentical", "boolean", "Two complete three-cell evaluations are byte-identical."),
        measurement("forbiddenDynamicDependencyCount", "libraries", "Dependencies on LibNC, GGML, CUDA, OpenMP, or BLAS."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source."),
        measurement("guardedWorkRootPass", "boolean", "Transient work was removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-elements", "adjointElementCount", "eq", 2097152),
        predicate("p-panels", "reductionPanelCount", "eq", 8),
        predicate("p-treatment", "block128SourceMismatchCount", "eq", 0),
        predicate("p-maximum", "maximumBlock128AbsoluteError", "eq", 0.0),
        predicate("p-unblocked", "unblockedSourceMismatchCount", "gt", 0),
        predicate("p-negated", "negatedControlMismatchCount", "gt", 0),
        predicate("p-cells", "arithmeticCellsDiffer", "eq", True),
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
            "falsification": "Any treatment mismatch, dead control, nondeterministic replay, forbidden dependency, source failure, or resource failure rejects the transpose contract.",
        },
        "changedMechanism": "Apply the independently exact ordered 128-feature panel transpose contract to the 1,024-feature w_o_19 reduction, with unblocked and sign-negated controls and complete replay.",
        "invariants": [
            "The initial BF16 matrix and exact open incoming adjoint are consumed verbatim in state-major order.",
            "The source input adjoint is used only as an independently captured comparator.",
            "The evaluator has no LibNC, GGML, CUDA, OpenMP, or BLAS dependency.",
            "The source comparator and matrix remain zero-credit oracle evidence and cannot ship.",
        ],
        "controls": [
            {"id": "block128", "role": "treatment", "definition": "Accumulate eight ordered 128-feature FMA panels, add completed panels, and round once to BF16."},
            {"id": "unblocked", "role": "comparator", "definition": "Accumulate all 1,024 reduction features in one FMA chain."},
            {"id": "negated", "role": "negative", "definition": "Negate the incoming adjoint under the ordered-panel treatment."},
            {"id": "replay", "role": "replay", "definition": "Repeat all three complete populations byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 pre-w_o input-adjoint words",
            "scopeBytes": 4194304,
            "scopeSymbols": 2097152,
            "selection": "Every one of 1,024 input features for all 64 states and 32 streams.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The sealed initial matrix, exact open post-w_o adjoint, exact source input-adjoint comparator, and independently validated panel schedule.",
                "Only the three prospectively frozen arithmetic cells are evaluated.",
            ],
            "forbiddenInformation": [
                "LibNC execution, fitting to mismatch coordinates, tolerance, future symbols, or editing the source comparator.",
                "Claiming an open pre-w_o forward path, compression gain, or Hutter credit.",
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
            predicate("k-treatment", "block128SourceMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-exact-w-o-input-adjoint.bf16",
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
