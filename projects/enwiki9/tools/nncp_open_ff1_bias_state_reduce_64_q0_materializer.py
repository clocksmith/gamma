#!/usr/bin/env python3
"""Freeze LibNC-free FF1 bias state-boundary reduction."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_ff1_bias_state_reduce_64_q0_v1"
PARENT_ID = "nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_ff1_bias_state_reduce_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR = PROGRAM / "ff1_bias_state_reduce.cpp"
DESCRIPTOR = PROGRAM / "program.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / "operations/adaptive/reflections/20260816T111831Z_64dcc1173e.json"
EXACT_RESIDUAL = ROOT / "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/open-ff1-output-residual.bf16"
BASELINE = ROOT / "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/open-ff-bias1-19-gradient.bf16"
PARENT_REVISION = ROOT / json.loads((PARENT_RESULT / "decision.json").read_text())["candidateRevision"]["receipt"]["path"]
SOURCE_CEILING = 500_000


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
    return {"id": identifier, "path": resolved.relative_to(ROOT.resolve()).as_posix(), "sha256": f"sha256:{sha256(resolved)}"}


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(identifier: str, measurement_id: str, operator: str, threshold: object) -> dict[str, object]:
    return {"id": identifier, "measurement": measurement_id, "operator": operator, "threshold": threshold}


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return f"runtime-source-{path.stem}-{hashlib.sha256(relative.encode()).hexdigest()[:12]}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    inputs = [
        reference(PARENT_RESULT / "decision.json", "parent-decision"),
        reference(PARENT_RESULT / "execution.json", "parent-execution"),
        reference(PARENT_RESULT / "guard.json", "parent-guard"),
        reference(PARENT_REFLECTION, "parent-reflection"),
        reference(EXACT_RESIDUAL, "source-exact-ff1-output-residual"),
        reference(PARENT_RESULT / "source-exact-ff-bias1-19-gradient.bf16", "independent-bias-gradient-oracle"),
        reference(BASELINE, "flattened-baseline-gradient"),
        reference(RUNNER, "runner"),
        reference(MATERIALIZER, "materializer"),
        reference(EVALUATOR, "evaluator-source"),
        reference(DESCRIPTOR, "program-descriptor"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_identifier(path)))
            present.add(relative)
    measurements = [
        measurement("antecedentsPass", "boolean", "The exact LibNC state-panel oracle, its reflection and guards, the complete FF1 adjoint, and the frozen flat baseline remain hash-bound."),
        measurement("inputElementCount", "BF16 elements", "Complete FF1-output adjoint population consumed per variant."),
        measurement("outputElementCount", "BF16 elements", "Complete FF1 bias gradient population emitted per variant."),
        measurement("treatmentMismatchCount", "BF16 elements", "Open chronological state-boundary words differing from the independent oracle."),
        measurement("maximumTreatmentAbsoluteError", "float32 value", "Maximum open treatment/oracle absolute error."),
        measurement("flatMismatchCount", "BF16 elements", "Flat chronological control words differing from the oracle."),
        measurement("reverseMismatchCount", "BF16 elements", "Reverse-state control words differing from the oracle."),
        measurement("negatedControlDiffers", "boolean", "Sign-negated treatment differs from the oracle."),
        measurement("flatBaselineByteIdentical", "boolean", "The independently recomputed flat control equals the frozen parent flat projection byte-for-byte."),
        measurement("evaluationReplayIdentical", "boolean", "Two complete treatment/control executions reproduce byte-for-byte."),
        measurement("forbiddenDynamicDependencyCount", "dependencies", "Runtime dependencies on LibNC, GGML, BLAS, or OpenMP."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed open evaluator and orchestration source."),
        measurement("guardedWorkRootPass", "boolean", "Transient build and evaluation files were removed with the guarded work root."),
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
        "parent": {"candidateId": PARENT_ID, "revision": {key: value for key, value in reference(PARENT_REVISION, "parent-revision").items() if key != "id"}},
        "hypothesis": {
            "claim": "A LibNC-free reducer that accumulates 32 BF16 stream adjoints sequentially into the prior BF16 gradient and materializes BF16 once after each of 64 chronological states reproduces every independent oracle ff_bias1_19 word.",
            "falsification": "Any nonzero treatment/oracle mismatch after both complete populations, or any dependency, replay, baseline, control, source, or guard failure, prevents promotion.",
        },
        "changedMechanism": "Replace the digest-bound LibNC teacher call with explicit float32 sequential stream adds and round-to-nearest-even BF16 materialization at every chronological state boundary.",
        "invariants": [
            "The complete source-exact FF1-output adjoint is consumed without repair or tolerance.",
            "The independent oracle is unavailable until both complete open populations exist.",
            "The treatment has no LibNC, GGML, BLAS, or OpenMP runtime dependency.",
            "No result receives Hutter score credit because no archive is produced.",
        ],
        "controls": [
            {"id": "open-state-boundary", "role": "treatment", "definition": "Sequentially add streams 0 through 31 into the prior BF16 gradient and materialize BF16 after every state from 0 through 63."},
            {"id": "flat-chronological", "role": "comparator", "definition": "Accumulate all 2,048 samples in one float32 chain and materialize only once."},
            {"id": "reverse-state-order", "role": "negative", "definition": "Apply the treatment with state panels accumulated from 63 down to 0."},
            {"id": "negated-residual", "role": "negative", "definition": "Invert only each input BF16 sign bit before the treatment arithmetic."},
            {"id": "independent-replay", "role": "replay", "definition": "Execute all four variants twice."},
        ],
        "population": {"unit": "BF16 FF1-output adjoint elements", "scopeBytes": 25165824, "scopeSymbols": 12582912, "selection": "All 64 states, 32 streams, and 6,144 features from the source-exact parent artifact.", "coordinate": "state-major, stream-major, feature-major"},
        "causalBoundary": {
            "availableInformation": ["The complete source-exact FF1-output adjoint and the prospectively frozen open arithmetic."],
            "forbiddenInformation": ["The independent bias-gradient oracle before both populations complete, retained-gradient coordinate repair, tolerance, or fitted order."],
        },
        "budget": {"expectedGrossSavingsBytes": 0, "maximumAddedPackageBytes": SOURCE_CEILING, "expectedNetSavingsBytes": -SOURCE_CEILING},
        "search": {"expectedTransferRetention": 0.0, "expectedRuntimeRatio": 1.0, "expectedMemoryRatio": 1.0, "uncertaintyRisk": 0.1, "interactionRisk": 0.1},
        "measurements": measurements,
        "promotionPredicates": [
            predicate("p-antecedents", "antecedentsPass", "eq", True),
            predicate("p-input", "inputElementCount", "eq", 12582912),
            predicate("p-output", "outputElementCount", "eq", 6144),
            predicate("p-treatment", "treatmentMismatchCount", "eq", 0),
            predicate("p-maximum", "maximumTreatmentAbsoluteError", "eq", 0.0),
            predicate("p-flat", "flatMismatchCount", "eq", 4708),
            predicate("p-reverse", "reverseMismatchCount", "eq", 5099),
            predicate("p-negated", "negatedControlDiffers", "eq", True),
            predicate("p-flat-identity", "flatBaselineByteIdentical", "eq", True),
            predicate("p-replay", "evaluationReplayIdentical", "eq", True),
            predicate("p-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
            predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
            predicate("p-work-root", "guardedWorkRootPass", "eq", True),
        ],
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-treatment", "treatmentMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-source-exact-ff-bias1-19-gradient.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
            f"results/{CANDIDATE_ID}/decision.json",
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
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
