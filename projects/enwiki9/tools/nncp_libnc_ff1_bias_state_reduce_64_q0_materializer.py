#!/usr/bin/env python3
"""Freeze LibNC FF1 bias state-reduction attribution."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_ff1_bias_state_reduce_64_q0_v1"
PARENT_ID = "nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_ff1_bias_state_reduce_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR = PROGRAM / "ff1_bias_state_reduce.c"
DESCRIPTOR = PROGRAM / "program.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / "operations/adaptive/reflections/20260816T104952Z_2204470800.json"
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
PARENT_REVISION = ROOT / json.loads((PARENT_RESULT / "decision.json").read_text())[
    "candidateRevision"
]["receipt"]["path"]
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
    return {
        "id": identifier,
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }


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
        reference(PARENT_RESULT / "open-ff1-output-residual.bf16", "source-exact-ff1-output-residual"),
        reference(PARENT_RESULT / "open-ff-bias1-19-gradient.bf16", "baseline-open-bias-gradient"),
        reference(FIXTURE_ROOT / "decision.json", "fixture-decision"),
        reference(FIXTURE_ROOT / "fixture-manifest.json", "fixture-manifest"),
        reference(FIXTURE_ROOT / "fixture/gradients/0005_ff_bias1_19.bin", "retained-ff-bias1-19-gradient"),
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
        measurement("antecedentsPass", "boolean", "The exact FF2 and GEGLU adjoints, parent failure localization, fixture, comparator, and guards remain hash-bound."),
        measurement("featureCount", "features", "Bias features in every state-panel reduction."),
        measurement("streamCount", "streams", "BF16 columns reduced per decoder state."),
        measurement("stateCount", "states", "Chronological decoder-state panels accumulated."),
        measurement("inputElementCount", "BF16 elements", "Complete source-exact FF1-output adjoint population consumed by each replay."),
        measurement("stateReductionCallCount", "calls", "Chronological nc_reduce_sum(existing_gradient, state_panel, 1) calls."),
        measurement("treatmentMismatchCount", "BF16 gradient elements", "Production-scheduled LibNC treatment words differing from the retained ff_bias1_19 gradient."),
        measurement("maximumTreatmentAbsoluteError", "float32 value", "Maximum absolute treatment/comparator error."),
        measurement("baselineMismatchCount", "BF16 gradient elements", "Prior flattened chronological reduction words differing from the retained gradient."),
        measurement("reverseMismatchCount", "BF16 gradient elements", "Reverse-state control words differing from the retained gradient."),
        measurement("negatedControlDiffers", "boolean", "Sign-negating every input adjoint changes the treatment projection."),
        measurement("evaluationReplayIdentical", "boolean", "Two complete treatment/control populations reproduce byte-for-byte."),
        measurement("sourceLibraryDigestBound", "boolean", "Execution uses the SHA-256-attributed production LibNC library."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed evaluator and orchestration source."),
        measurement("guardedWorkRootPass", "boolean", "Compiled and transient payloads were removed with the guarded work root."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-features", "featureCount", "eq", 6144),
        predicate("p-streams", "streamCount", "eq", 32),
        predicate("p-states", "stateCount", "eq", 64),
        predicate("p-input", "inputElementCount", "eq", 12582912),
        predicate("p-reductions", "stateReductionCallCount", "eq", 64),
        predicate("p-treatment", "treatmentMismatchCount", "eq", 0),
        predicate("p-treatment-maximum", "maximumTreatmentAbsoluteError", "eq", 0.0),
        predicate("p-baseline", "baselineMismatchCount", "eq", 4708),
        predicate("p-control", "negatedControlDiffers", "eq", True),
        predicate("p-replay", "evaluationReplayIdentical", "eq", True),
        predicate("p-library", "sourceLibraryDigestBound", "eq", True),
        predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
        predicate("p-work-root", "guardedWorkRootPass", "eq", True),
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
                    PARENT_REVISION, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": "Applying LibNC's production add_dup1 backward schedule—one nc_reduce_sum(existing_gradient, 6144x32 BF16 state panel, 1) call for each of 64 chronological states—to the source-exact FF1-output adjoint reproduces every retained ff_bias1_19 gradient word.",
            "falsification": "Any nonzero treatment/comparator mismatch after both complete replays falsifies this state-panel schedule as the remaining arithmetic contract.",
        },
        "changedMechanism": "Replace one flattened 2,048-sample float accumulation with the statically attributed production graph schedule: 64 chronological BF16 32-stream reductions accumulated through nc_reduce_sum's existing-gradient operand.",
        "invariants": [
            "The complete source-exact FF2 and GEGLU adjoints are consumed without coordinate repair or tolerance.",
            "The retained gradient is unavailable until both complete treatment/control populations exist.",
            "LibNC remains a zero-credit teacher and no result receives Hutter score credit.",
        ],
        "controls": [
            {"id": "chronological-state-panels", "role": "treatment", "definition": "LibNC reduces one 6,144-by-32 BF16 panel into the existing gradient for each of 64 chronological states."},
            {"id": "flattened-baseline", "role": "comparator", "definition": "The prior complete scalar chronological projection must retain its frozen 4,708-word mismatch."},
            {"id": "reverse-state-order", "role": "negative", "definition": "The same 32-stream panel reductions are accumulated in reverse state order and reported without influencing selection."},
            {"id": "negated-residual", "role": "negative", "definition": "Every BF16 input adjoint has only its sign bit inverted before the identical chronological schedule."},
            {"id": "independent-replay", "role": "replay", "definition": "The complete treatment and both controls execute twice."},
        ],
        "population": {
            "unit": "BF16 FF1-output adjoint elements",
            "scopeBytes": 25165824,
            "scopeSymbols": 12582912,
            "selection": "All 64 chronological decoder states, all 32 streams, and all 6,144 FF1-output features from the source-exact parent artifact.",
            "coordinate": "state-major, then stream-major, then feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The complete source-exact BF16 FF1-output adjoint.",
                "The statically attributed add_dup1 backward call shape and chronological graph order.",
                "The digest-bound production LibNC implementation."
            ],
            "forbiddenInformation": [
                "The retained ff_bias1_19 gradient before both complete replay populations exist.",
                "Coordinate-specific repairs, tolerances, or fitted reduction orders."
            ],
        },
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 0.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "uncertaintyRisk": 0.1,
            "interactionRisk": 0.1,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-treatment-mismatch", "treatmentMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-exact-ff-bias1-19-gradient.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
            f"results/{CANDIDATE_ID}/decision.json",
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
