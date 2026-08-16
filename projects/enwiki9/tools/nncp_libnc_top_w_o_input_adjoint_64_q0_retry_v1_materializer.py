#!/usr/bin/env python3
"""Freeze receipt-only salvage of the completed layer-19 w_o capture."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_top_w_o_input_adjoint_64_q0_v1"
SOURCE_RESULT = ROOT / "results" / PARENT_ID
SOURCE_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
SOURCE_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T160641Z_9c2e81181b.json"
)
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T160641Z_9c2e81181b.json"
)
FIXTURE_MANIFEST = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture-manifest.json"
)
RUNNER = ROOT / "tools/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
DESCRIPTOR = ROOT / "programs" / CANDIDATE_ID / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 2_000_000
HYPOTHESIS = (
    "Re-hashing both completed raw capture trees against the sealed manifests, "
    "reassembling all input and adjoint probes against the durable tensors, and "
    "validating the final receipt at its declared path preserves every scientific "
    "measurement and safely removes the transient source work without rerunning "
    "the teacher."
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
    failed_job = json.loads(SOURCE_JOB.read_text())
    parent_revision = ROOT / failed_job["candidate_revision"]["path"]
    inputs = [
        reference(SOURCE_EXPERIMENT, "source-experiment"),
        reference(SOURCE_JOB, "source-failed-job"),
        reference(SOURCE_RESULT / "decision.precleanup.json", "source-staged-decision"),
        reference(SOURCE_RESULT / "execution.json", "source-execution"),
        reference(SOURCE_RESULT / "guard.json", "source-guard"),
        reference(SOURCE_REFLECTION, "source-reflection"),
        reference(FIXTURE_MANIFEST, "production-fixture-manifest"),
        reference(SOURCE_RESULT / "incremental_source.tar.xz", "source-incremental-package"),
        reference(SOURCE_RESULT / "source-w-o-input.bf16", "source-w-o-input"),
        reference(SOURCE_RESULT / "source-w-o-input-adjoint.bf16", "source-w-o-input-adjoint"),
        reference(SOURCE_RESULT / "source-initial-w-o-19.bf16", "source-initial-w-o-19"),
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
        measurement("antecedentsPass", "boolean", "The failed job, staged receipt, execution manifests, guard, reflection, fixture, and tensors remain hash-bound."),
        measurement("captureCount", "captures", "Complete source capture populations preserved by the staged receipt."),
        measurement("sampleCount", "state-stream samples", "Chronological pre-w_o samples."),
        measurement("sourceInputElementCount", "BF16 elements", "Words in the sealed pre-w_o input."),
        measurement("sourceAdjointElementCount", "BF16 elements", "Words in the sealed pre-w_o input adjoint."),
        measurement("initialMatrixElementCount", "BF16 elements", "Words in the sealed initial w_o_19 matrix."),
        measurement("sourceCaptureDeterministic", "boolean", "The original complete captures were byte-identical."),
        measurement("declaredProbeFileCount", "files", "Declared probe paths across both captures."),
        measurement("declaredProbePopulationExact", "boolean", "Each re-hashed raw capture contains exactly the declared probe population."),
        measurement("fixturePayloadIdentical", "boolean", "Every re-hashed non-probe file matches the retained fixture."),
        measurement("fixturePayloadMismatchCount", "files", "Non-probe fixture mismatches across both raw captures."),
        measurement("inputLive", "boolean", "The sealed input is live."),
        measurement("adjointLive", "boolean", "The sealed adjoint is live."),
        measurement("rawCaptureManifestExact", "boolean", "Both re-hashed raw manifests equal their sealed execution manifests."),
        measurement("rawProbeTensorMismatchCount", "BF16 elements", "Reassembled raw input/adjoint words differing from the sealed tensors."),
        measurement("initialMatrixDigestExact", "boolean", "The sealed initial matrix matches its execution receipt."),
        measurement("resourceGuardsPass", "boolean", "The source capture stayed inside memory and temporary-disk limits; its nonzero return was receipt-only."),
        measurement("sourceWorkBytesBeforeCleanup", "bytes", "Raw completed source work removed after declared-path validation."),
        measurement("sourceWorkRootRemoved", "boolean", "The completed raw source work was removed only after a schema-valid declared decision existed."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed salvage source."),
        measurement("guardedWorkRootPass", "boolean", "The retry work root was removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-captures", "captureCount", "eq", 2),
        predicate("p-samples", "sampleCount", "eq", 2048),
        predicate("p-input-elements", "sourceInputElementCount", "eq", 2097152),
        predicate("p-adjoint-elements", "sourceAdjointElementCount", "eq", 2097152),
        predicate("p-matrix-elements", "initialMatrixElementCount", "eq", 1048576),
        predicate("p-deterministic", "sourceCaptureDeterministic", "eq", True),
        predicate("p-probe-files", "declaredProbeFileCount", "eq", 512),
        predicate("p-probe-population", "declaredProbePopulationExact", "eq", True),
        predicate("p-fixture", "fixturePayloadIdentical", "eq", True),
        predicate("p-fixture-count", "fixturePayloadMismatchCount", "eq", 0),
        predicate("p-input-live", "inputLive", "eq", True),
        predicate("p-adjoint-live", "adjointLive", "eq", True),
        predicate("p-raw-manifests", "rawCaptureManifestExact", "eq", True),
        predicate("p-raw-tensors", "rawProbeTensorMismatchCount", "eq", 0),
        predicate("p-matrix", "initialMatrixDigestExact", "eq", True),
        predicate("p-resources", "resourceGuardsPass", "eq", True),
        predicate("p-source-cleanup", "sourceWorkRootRemoved", "eq", True),
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
                    parent_revision, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": HYPOTHESIS,
            "falsification": "Any raw-manifest, probe-population, tensor, fixture, matrix, binding, declared-output, source, resource, or cleanup failure rejects the salvage.",
        },
        "changedMechanism": "Do not rerun the teacher. Re-hash both retained raw capture trees, reassemble every declared probe tensor against the sealed artifacts, validate decision.json at its declared path, then remove both raw source work and retry work.",
        "invariants": [
            "The captured input, adjoint, initial matrix, execution manifest, and scientific measurements are copied or checked without modification.",
            "Every raw file is re-hashed before the source work root is removed.",
            "A schema-valid decision.json exists before any raw capture is deleted.",
            "The retry performs no teacher execution and earns zero objective credit.",
        ],
        "controls": [
            {"id": "raw-manifest-replay", "role": "treatment", "definition": "Re-hash both raw trees and require exact equality with the sealed manifests."},
            {"id": "raw-tensor-reassembly", "role": "comparator", "definition": "Reassemble all four raw probe tensors and require zero BF16 mismatches against the sealed tensors."},
            {"id": "fixture-identity", "role": "shifted", "definition": "Require exact declared probe namespaces and unchanged non-probe fixture payloads."},
            {"id": "declared-output-validation", "role": "replay", "definition": "Validate the retry receipt at the exact prospectively declared decision.json path before cleanup."},
        ],
        "population": {
            "unit": "sealed and raw layer-19 pre-w_o source-capture evidence",
            "scopeBytes": 4194304,
            "scopeSymbols": 2097152,
            "selection": "Both complete 64-state by 32-stream source captures and all three sealed BF16 artifacts.",
            "coordinate": "capture, state-major, stream-major, feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The failed job, exact failure reflection, staged receipt, source execution manifests, raw capture trees, retained fixture manifest, and sealed tensors.",
                "The retry changes receipt and cleanup mechanics only.",
            ],
            "forbiddenInformation": [
                "Teacher execution, tensor recomputation, tolerance, fitted repair, broad wildcard exclusion, or future symbols.",
                "Claiming an open transpose, compression gain, transfer, package, or Hutter credit.",
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
            "uncertaintyRisk": 0.05,
            "interactionRisk": 0.0,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-raw-tensor-drift", "rawProbeTensorMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-w-o-input.bf16",
            f"results/{CANDIDATE_ID}/source-w-o-input-adjoint.bf16",
            f"results/{CANDIDATE_ID}/source-initial-w-o-19.bf16",
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
