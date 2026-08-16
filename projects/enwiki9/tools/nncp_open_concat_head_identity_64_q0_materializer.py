#!/usr/bin/env python3
"""Freeze the exact open concat-head identity experiment."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_w_o_input_adjoint_64_q0_v1_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_concat_head_identity_64_q0_v1"
PARENT_ID = "nncp_libnc_top_attention_product_oracle_64_q0_retry_v2"
PARENT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T174722Z_8b88b4a53d.json"
)
OPEN_FORWARD = ROOT / "results/nncp_open_top_w_o_input_forward_64_q0_retry_v2"
OPEN_FORWARD_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T171305Z_fdae41e74c.json"
)
OPEN_ADJOINT = ROOT / "results/nncp_open_w_o_input_adjoint_block128_64_q0_v1"
OPEN_ADJOINT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T164348Z_ff5718724e.json"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RUNNER = ROOT / "tools/nncp_open_concat_head_identity_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
DESCRIPTOR = PROGRAM / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 500_000
HYPOTHESIS = (
    "In the retained state-stream-head-feature serialization, concat_head and "
    "its backward are byte-order identities: the complete source attended "
    "input equals the exact open pre-w_o value and the complete source "
    "attended adjoint equals the exact open pre-w_o adjoint, while a head-major "
    "reinterpretation differs in both directions."
)


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{suffix}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_revision = ROOT / json.loads(PARENT.joinpath("decision.json").read_text())[
        "candidateRevision"
    ]["receipt"]["path"]
    inputs = [
        base.reference(PARENT / "decision.json", "parent-decision"),
        base.reference(PARENT / "execution.json", "parent-execution"),
        base.reference(PARENT / "guard.json", "parent-guard"),
        base.reference(PARENT_REFLECTION, "parent-reflection"),
        base.reference(
            PARENT / "source-attended-heads-input.bf16",
            "source-attended-input",
        ),
        base.reference(
            PARENT / "source-attended-heads-adjoint.bf16",
            "source-attended-adjoint",
        ),
        base.reference(
            OPEN_FORWARD / "decision.json", "open-forward-decision"
        ),
        base.reference(
            OPEN_FORWARD / "execution.json", "open-forward-execution"
        ),
        base.reference(OPEN_FORWARD / "guard.json", "open-forward-guard"),
        base.reference(
            OPEN_FORWARD_REFLECTION, "open-forward-reflection"
        ),
        base.reference(
            OPEN_FORWARD / "open-exact-w-o-input.bf16", "open-pre-w-o-input"
        ),
        base.reference(
            OPEN_ADJOINT / "decision.json", "open-adjoint-decision"
        ),
        base.reference(
            OPEN_ADJOINT / "execution.json", "open-adjoint-execution"
        ),
        base.reference(OPEN_ADJOINT / "guard.json", "open-adjoint-guard"),
        base.reference(
            OPEN_ADJOINT_REFLECTION, "open-adjoint-reflection"
        ),
        base.reference(
            OPEN_ADJOINT / "source-exact-w-o-input-adjoint.bf16",
            "open-pre-w-o-adjoint",
        ),
        base.reference(RUNNER, "runner"),
        base.reference(MATERIALIZER, "materializer"),
        base.reference(DESCRIPTOR, "program-descriptor"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(base.reference(path, source_identifier(path)))
            present.add(relative)
    measurements = [
        base.measurement("antecedentsPass", "boolean", "The exact source and open forward/backward receipts remain hash-bound."),
        base.measurement("elementCount", "BF16 elements", "Complete serialized attended adjoint population."),
        base.measurement("forwardMismatchCount", "BF16 elements", "Direct source attended-input words differing from the open pre-w_o value."),
        base.measurement("maximumForwardAbsoluteError", "float32 value", "Maximum direct forward identity error."),
        base.measurement("adjointMismatchCount", "BF16 elements", "Direct source attended-adjoint words differing from the open pre-w_o adjoint."),
        base.measurement("maximumAdjointAbsoluteError", "float32 value", "Maximum direct adjoint identity error."),
        base.measurement("forwardHeadMajorControlMismatchCount", "BF16 elements", "Wrong-order forward control mismatches."),
        base.measurement("adjointHeadMajorControlMismatchCount", "BF16 elements", "Wrong-order adjoint control mismatches."),
        base.measurement("replayIdentical", "boolean", "Two independent identity materializations reproduce byte-for-byte."),
        base.measurement("artifactDigestExact", "boolean", "The durable attended adjoint exactly copies the open input adjoint."),
        base.measurement("teacherExecutionCount", "executions", "Teacher executions performed by the open identity."),
        base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed identity source."),
        base.measurement("guardedWorkRootPass", "boolean", "Transient control and replay files were removed."),
    ]
    promotion = [
        base.predicate("p-antecedents", "antecedentsPass", "eq", True),
        base.predicate("p-elements", "elementCount", "eq", 2097152),
        base.predicate("p-forward", "forwardMismatchCount", "eq", 0),
        base.predicate("p-forward-maximum", "maximumForwardAbsoluteError", "eq", 0.0),
        base.predicate("p-adjoint", "adjointMismatchCount", "eq", 0),
        base.predicate("p-adjoint-maximum", "maximumAdjointAbsoluteError", "eq", 0.0),
        base.predicate("p-forward-control", "forwardHeadMajorControlMismatchCount", "gt", 0),
        base.predicate("p-adjoint-control", "adjointHeadMajorControlMismatchCount", "gt", 0),
        base.predicate("p-replay", "replayIdentical", "eq", True),
        base.predicate("p-artifact", "artifactDigestExact", "eq", True),
        base.predicate("p-no-teacher", "teacherExecutionCount", "eq", 0),
        base.predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
        base.predicate("p-work", "guardedWorkRootPass", "eq", True),
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
                for key, value in base.reference(
                    parent_revision, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": HYPOTHESIS,
            "falsification": "Any source/open mismatch, dead wrong-order control, replay drift, artifact drift, teacher execution, source failure, or cleanup failure rejects the identity.",
        },
        "changedMechanism": "Treat concat_head as an explicit serialized identity contract, compare both forward and adjoint full populations directly, retain head-major permutations as negative controls, and emit the exact open attended adjoint without teacher execution.",
        "invariants": [
            "The source and open tensors are immutable hash-bound antecedents.",
            "No arithmetic, tolerance, fitted mapping, or teacher execution may change the treatment values.",
            "Both forward and backward identities cover all states, streams, heads, and features.",
            "The durable artifact remains zero-credit intermediate evidence and cannot ship as codec data.",
        ],
        "controls": [
            {"id": "direct-forward", "role": "treatment", "definition": "Compare the source attended input directly to the exact open pre-w_o tensor."},
            {"id": "direct-adjoint", "role": "comparator", "definition": "Compare the source attended adjoint directly to the exact open pre-w_o adjoint."},
            {"id": "head-major-forward", "role": "negative", "definition": "Apply the rejected head-major forward permutation and require mismatches."},
            {"id": "head-major-adjoint", "role": "shifted", "definition": "Apply the rejected head-major adjoint permutation and require mismatches."},
            {"id": "copy-replay", "role": "replay", "definition": "Materialize the exact open adjoint twice and require byte identity."},
        ],
        "population": {
            "unit": "BF16 attended forward and adjoint words",
            "scopeBytes": 4194304,
            "scopeSymbols": 2097152,
            "selection": "Every feature for 64 states, 32 streams, and eight 128-feature heads.",
            "coordinate": "state-major, stream-major, head-major, feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The independently exact source attended tensors and open pre-w_o forward/backward tensors."
            ],
            "forbiddenInformation": [
                "Teacher execution, tolerance, coordinate fitting, tensor mutation, shipping captured data, compression credit, or claims about value-attention arithmetic."
            ],
        },
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 0.01,
            "expectedMemoryRatio": 0.01,
            "uncertaintyRisk": 0.01,
            "interactionRisk": 0.0,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            base.predicate("k-antecedents", "antecedentsPass", "eq", True),
            base.predicate("k-adjoint", "adjointMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-exact-attended-adjoint.bf16",
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
