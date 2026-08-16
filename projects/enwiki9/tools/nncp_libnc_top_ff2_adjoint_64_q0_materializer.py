#!/usr/bin/env python3
"""Freeze the production LibNC top-layer FF2 adjoint attribution gate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_ff2_adjoint_64_q0_v1"
PARENT_ID = "nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_top_ff2_adjoint_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T061820040240Z_b914054b9184.json"
)
PARENT_DECISION = ROOT / f"results/{PARENT_ID}/decision.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T061837Z_1dfa2ae8f8.json"
)
PARENT_RESIDUAL = ROOT / (
    f"results/{PARENT_ID}/open-final-norm-input-residual.bf16"
)
FIXTURE_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_ROOT = ROOT / "results" / FIXTURE_ID
FIXTURE_HOOK = ROOT / "tools/nncp_profile_update_fixture_hook_q3.c"
SOURCE_CEILING = 2_000_000


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


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    digest = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{digest}"


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


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    inputs = [
        reference(PARENT_DECISION, "parent-open-decision"),
        reference(PARENT_REFLECTION, "parent-open-reflection"),
        reference(PARENT_RESIDUAL, "parent-open-residual"),
        reference(FIXTURE_ROOT / "decision.json", "production-fixture-decision"),
        reference(
            FIXTURE_ROOT / "fixture-manifest.json", "production-fixture-manifest"
        ),
        reference(FIXTURE_ROOT / "guard.json", "production-fixture-guard"),
        reference(
            FIXTURE_ROOT / "fixture/gradients/0001_ff2_19.bin",
            "retained-ff2-gradient",
        ),
        reference(
            FIXTURE_ROOT / "fixture/gradients/0001_ff2_19.meta",
            "retained-ff2-gradient-meta",
        ),
        reference(PROGRAM / "top_ff2_probe.inc.c", "probe-source"),
        reference(PROGRAM / "source_ff2_gradient.cpp", "reducer-source"),
        reference(PROGRAM / "program.py", "program-descriptor"),
        reference(FIXTURE_HOOK, "production-fixture-hook"),
        reference(RUNNER, "runner"),
        reference(MATERIALIZER, "materializer"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_identifier(path)))
            present.add(relative)

    measurements = [
        measurement(
            "antecedentsPass",
            "boolean",
            "The exact production fixture and failed deterministic open FF2 reconstruction antecedents remain valid and digest-bound.",
        ),
        measurement(
            "sourceCaptureRepeatIdentical",
            "boolean",
            "Two independently instrumented production captures have identical complete directory aggregates.",
        ),
        measurement(
            "combinedReplayIdentical",
            "boolean",
            "Both captures combine to byte-identical FF2 inputs, adjoints, reconstructed gradients, and negative controls.",
        ),
        measurement(
            "parentFixtureIdentity",
            "boolean",
            "Every non-probe file in each instrumented capture is byte-identical to the retained production fixture.",
        ),
        measurement(
            "capturedStateCount",
            "states",
            "Sequential production states captured at the first retained update.",
        ),
        measurement(
            "sourceAdjointElementCount",
            "gradient elements",
            "Complete BF16 source post-FF2 residual-join adjoint population.",
        ),
        measurement(
            "sourceInputElementCount",
            "activation elements",
            "Complete BF16 source layer-19 FF2 input population.",
        ),
        measurement(
            "sourceFf2ElementCount",
            "gradient elements",
            "Complete reconstructed BF16 source ff2_19 parameter-gradient population.",
        ),
        measurement(
            "openAdjointMismatchCount",
            "gradient elements",
            "Source BF16 post-FF2 adjoint words that differ from the frozen open final-normalization input residual.",
        ),
        measurement(
            "maximumOpenAdjointAbsoluteError",
            "float32 value",
            "Maximum absolute source-adjoint versus open-residual difference.",
        ),
        measurement(
            "openAdjointMismatchFeatureCount",
            "output features",
            "Distinct output coordinates containing any source-adjoint versus open-residual mismatch.",
        ),
        measurement(
            "sourceFf2MismatchCount",
            "gradient elements",
            "Source-input and source-adjoint reconstruction words that differ from retained production ff2_19.",
        ),
        measurement(
            "maximumSourceFf2AbsoluteError",
            "float32 value",
            "Maximum absolute source reconstruction versus retained ff2_19 difference.",
        ),
        measurement(
            "negatedSourceAdjointControlDiffers",
            "boolean",
            "Sign-negating the complete source adjoint changes the reconstructed ff2_19 gradient.",
        ),
        measurement(
            "incrementalSourceBytes",
            "bytes",
            "Compressed dependency-closed instrumentation, reduction, and orchestration source package.",
        ),
        measurement(
            "guardedWorkRootPass",
            "boolean",
            "Generated builds and complete teacher captures remained under and were removed with the guarded work root.",
        ),
    ]
    expected = {
        "antecedentsPass": True,
        "sourceCaptureRepeatIdentical": True,
        "combinedReplayIdentical": True,
        "parentFixtureIdentity": True,
        "capturedStateCount": 64,
        "sourceAdjointElementCount": 2_097_152,
        "sourceInputElementCount": 6_291_456,
        "sourceFf2ElementCount": 3_145_728,
        "sourceFf2MismatchCount": 0,
        "maximumSourceFf2AbsoluteError": 0,
        "negatedSourceAdjointControlDiffers": True,
        "guardedWorkRootPass": True,
    }
    promotion = [
        predicate(f"p-{name.lower()}", name, "eq", threshold)
        for name, threshold in expected.items()
    ]
    promotion.extend(
        [
            predicate(
                "p-open-adjoint-differs", "openAdjointMismatchCount", "gt", 0
            ),
            predicate(
                "p-incremental-source-bytes",
                "incrementalSourceBytes",
                "lte",
                SOURCE_CEILING,
            ),
        ]
    )
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
                "path": PARENT_REVISION.relative_to(ROOT).as_posix(),
                "sha256": f"sha256:{sha256(PARENT_REVISION)}",
            },
        },
        "hypothesis": {
            "claim": "The source-captured post-FF2 adjoint differs from the open final-normalization residual, while source input plus source adjoint reconstruct every retained ff2_19 word under the frozen reducer.",
            "falsification": "Any antecedent drift, production-fixture mutation, capture or replay difference, dead control, geometry drift, guard or source-bound violation, exact source-adjoint equality, or one source-reconstructed ff2_19 mismatch prevents the proposed attribution.",
        },
        "changedMechanism": "Attach a zero-valued LibNC parameter after the production layer-19 FF2 bias at update block 256, capture its exact BF16 backward adjoint and the corresponding FF2 input, then reconstruct the full ff2_19 gradient with the frozen reduction before reading the retained comparator.",
        "invariants": [
            "Instrumentation adds only a zero tensor after ff_bias2_19; every pre-existing fixture file from both captures must remain byte-identical to the retained production fixture.",
            "All 64 states across all 32 streams are captured and both complete runs finish before the open residual or retained ff2_19 comparator is read.",
            "The source reconstruction uses the same 128-sample partial FMA accumulation and ordered partial addition already frozen for the open FF2 reducer.",
            "The closed teacher, its executable, captured inputs, adjoints, gradients, traces, and fixture receive zero objective score credit and may not ship in a submitted codec.",
            "This gate attributes one production backward boundary; it proves no open transformer backward, recursive adaptation, archive saving, package, transfer, or Hutter result.",
        ],
        "controls": [
            {
                "id": "zero-add-production-capture",
                "role": "treatment",
                "definition": "A zero-valued marked tensor exposes the post-FF2 residual-join adjoint without changing the production computation.",
            },
            {
                "id": "retained-complete-fixture",
                "role": "comparator",
                "definition": "Every non-probe artifact must match the retained production fixture byte-for-byte in both captures.",
            },
            {
                "id": "retained-ff2-gradient-delayed",
                "role": "comparator",
                "definition": "The retained ff2_19 gradient is read only after both complete source reconstructions exist.",
            },
            {
                "id": "independent-source-replay",
                "role": "replay",
                "definition": "The complete instrumented production capture and reconstruction execute twice and must reproduce identical bytes.",
            },
            {
                "id": "negated-source-adjoint",
                "role": "negative",
                "definition": "Sign-negating every captured source-adjoint value must change the reconstructed ff2_19 gradient.",
            },
        ],
        "population": {
            "unit": "one production state, BF16 activation word, adjoint word, or parameter-gradient word",
            "scopeBytes": None,
            "scopeSymbols": 2048,
            "selection": "All 64 sequential states across all 32 streams at update block 256, all 6,291,456 FF2 input words, all 2,097,152 post-FF2 adjoint words, and all 3,145,728 ff2_19 words.",
            "coordinate": "First retained production update over original transformed-symbol coordinates [256,320) independently within each of 32 contiguous streams.",
        },
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound production source, model, vocabulary, preprocessed corpus, complete q3 fixture, failed open residual, frozen reducer, and prospective predicates.",
                "Source FF2 inputs and adjoints only as zero-credit teacher attribution evidence; retained ff2_19 only after both reconstruction payloads are complete.",
            ],
            "forbiddenInformation": [
                "Using any source-captured tensor, teacher executable, hidden trace, LibNC dependency, or uncounted probability in a submitted codec.",
                "Changing coordinates, applying comparator-derived corrections, tolerating differing BF16 words, or claiming compression benefit from this attribution gate.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-top-ff2-input.bf16",
            f"results/{CANDIDATE_ID}/source-top-ff2-adjoint.bf16",
            f"results/{CANDIDATE_ID}/source-ff2-19-gradient.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-source-ff2-mismatch", "sourceFf2MismatchCount", "gt", 0),
            predicate("k-open-adjoint-equal", "openAdjointMismatchCount", "eq", 0),
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "pythonSourceClosureEntries": ["runner", "materializer"],
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "interactionRisk": 0.2,
            "uncertaintyRisk": 0.3,
        },
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
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
