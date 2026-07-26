#!/usr/bin/env python3
"""Independently materialize and gate a bounded Clockwork residual expert."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import clockwork_contracts as contracts


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRANSFER_TRACE = (
    ROOT
    / "operations"
    / "clockwork"
    / "residual_expert_search_v1"
    / "transfer-trace.json"
)
EXPECTED_CHALLENGE_ID = "clockwork.residual_expert_search.v1"
EXPECTED_KERNEL_DIGEST = (
    "sha256:992fe87276b18210e3f3f8bc8cf0c4edd6c32ed716cc8a7b02337f52397876f3"
)
EXPECTED_EVALUATOR_DIGEST = (
    "sha256:ccd30e06114f3c1f424917af01d549e3295622a07faca597d9574fd0f30de5bf"
)
EXPECTED_GENOME_SCHEMA_DIGEST = (
    "sha256:c5f6742d1d5fbdd21f2bec6b86591bd07d7e5db897e4ae13959fdb286724ee9e"
)
BUNDLE_FILES = {
    "challenge": "challenge.json",
    "candidate": "candidate.json",
    "search_receipt": "search-receipt.json",
    "development_trace": "development-trace.json",
    "import_manifest": "import-manifest.json",
}


def _load_array(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not value:
        raise ValueError(f"{path} must contain a non-empty JSON array")
    if not all(isinstance(row, dict) for row in value):
        raise ValueError(f"{path} rows must be JSON objects")
    return value


def _safe_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if abs(value) > 9_007_199_254_740_991:
        raise ValueError(f"{label} exceeds the shared safe-integer range")
    return value


def _trunc_div(value: int, divisor: int) -> int:
    if value >= 0:
        return value // divisor
    return -((-value) // divisor)


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def validate_genome(genome: dict[str, Any], feature_count: int = 3) -> list[str]:
    expected = {
        "enabled",
        "biasQ15",
        "featureWeightsQ15",
        "stateWeightQ15",
        "stateDecayQ8",
    }
    reasons: list[str] = []
    if set(genome) != expected:
        reasons.append("genome fields do not match the residual-expert contract")
    if not isinstance(genome.get("enabled"), bool):
        reasons.append("enabled must be boolean")
    for field, minimum, maximum in (
        ("biasQ15", -4096, 4096),
        ("stateWeightQ15", -4096, 4096),
        ("stateDecayQ8", 0, 255),
    ):
        value = genome.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < minimum
            or value > maximum
        ):
            reasons.append(f"{field} must be an integer in [{minimum}, {maximum}]")
    weights = genome.get("featureWeightsQ15")
    if not isinstance(weights, list) or len(weights) != feature_count:
        reasons.append(f"featureWeightsQ15 must contain {feature_count} integers")
    else:
        for index, value in enumerate(weights):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < -4096
                or value > 4096
            ):
                reasons.append(
                    f"featureWeightsQ15[{index}] must be an integer in [-4096, 4096]"
                )
    return reasons


def evaluate_genome(
    genome: dict[str, Any],
    trace: list[dict[str, Any]],
) -> dict[str, Any]:
    reasons = validate_genome(genome)
    if reasons:
        raise ValueError(f"invalid residual-expert genome: {'; '.join(reasons)}")
    weights = genome["featureWeightsQ15"]
    state_q8 = 0
    baseline_loss = 0
    candidate_loss = 0
    estimated_cycles = 0
    for index, row in enumerate(trace):
        probability = _safe_integer(
            row.get("baselineProbabilityQ15"),
            f"trace[{index}].baselineProbabilityQ15",
        )
        if probability < 1 or probability > 32767:
            raise ValueError(
                f"trace[{index}].baselineProbabilityQ15 must be in [1, 32767]"
            )
        target = _safe_integer(row.get("target"), f"trace[{index}].target")
        if target not in (0, 1):
            raise ValueError(f"trace[{index}].target must be 0 or 1")
        features = row.get("features")
        if not isinstance(features, list) or len(features) != len(weights):
            raise ValueError(f"trace[{index}].features does not match genome")
        correction = genome["biasQ15"] if genome["enabled"] else 0
        if genome["enabled"]:
            for feature_index, feature_value in enumerate(features):
                feature = _safe_integer(
                    feature_value,
                    f"trace[{index}].features[{feature_index}]",
                )
                if feature < -8 or feature > 8:
                    raise ValueError(
                        f"trace[{index}].features[{feature_index}] exceeds [-8, 8]"
                    )
                correction += weights[feature_index] * feature
            correction += _trunc_div(genome["stateWeightQ15"] * state_q8, 256)
            estimated_cycles += 13 + len(features) * 3
        else:
            estimated_cycles += 1
        candidate_probability = _clamp(probability + correction, 1, 32767)
        expected = 32768 if target == 1 else 0
        baseline_loss += (expected - probability) ** 2
        candidate_loss += (expected - candidate_probability) ** 2
        if genome["enabled"]:
            signed_error_q8 = _trunc_div(expected - candidate_probability, 128)
            state_q8 = _clamp(
                _trunc_div(state_q8 * genome["stateDecayQ8"], 256)
                + signed_error_q8,
                -512,
                512,
            )
        else:
            state_q8 = 0
    genome_bytes = contracts.canonical_bytes(genome)
    peak_state_bytes = 8 if genome["enabled"] else 0
    return {
        "objectives": {
            "developmentLossUnits": candidate_loss,
            "canonicalGenomeBytes": len(genome_bytes),
            "estimatedCycles": estimated_cycles,
            "peakStateBytes": peak_state_bytes,
        },
        "rawLedger": {
            "rows": len(trace),
            "baselineLossUnits": baseline_loss,
            "candidateLossUnits": candidate_loss,
            "developmentSavingsUnits": baseline_loss - candidate_loss,
            "canonicalGenomeBytes": len(genome_bytes),
            "estimatedCycles": estimated_cycles,
            "peakStateBytes": peak_state_bytes,
            "finalStateQ8": state_q8,
        },
    }


def _gate(status: str, evidence: dict[str, Any]) -> dict[str, str]:
    return {
        "status": status,
        "evidenceDigest": contracts.sha256_digest(contracts.canonical_bytes(evidence)),
    }


def _read_bundle(bundle: Path) -> dict[str, Any]:
    return {
        "challenge": contracts.load_json(bundle / BUNDLE_FILES["challenge"]),
        "candidate": contracts.load_json(bundle / BUNDLE_FILES["candidate"]),
        "search_receipt": contracts.load_json(bundle / BUNDLE_FILES["search_receipt"]),
        "development_trace": _load_array(bundle / BUNDLE_FILES["development_trace"]),
        "import_manifest": contracts.load_json(bundle / BUNDLE_FILES["import_manifest"]),
    }


def evaluate_bundle(
    bundle: Path,
    *,
    transfer_trace_path: Path = DEFAULT_TRANSFER_TRACE,
    created_at: str | None = None,
) -> dict[str, Any]:
    values = _read_bundle(bundle)
    challenge = values["challenge"]
    candidate = values["candidate"]
    search_receipt = values["search_receipt"]
    development_trace = values["development_trace"]
    import_manifest = values["import_manifest"]
    if import_manifest.get("schema") != "gamma.clockwork_import_manifest.v1":
        raise ValueError("unsupported Clockwork import manifest")
    source_commit = import_manifest.get("sourceCommit")
    if (
        not isinstance(source_commit, str)
        or len(source_commit) != 40
        or any(character not in "0123456789abcdef" for character in source_commit)
    ):
        raise ValueError("import manifest sourceCommit must be a full Git SHA-1")
    expected_source_revision = contracts.sha256_digest(
        f"git:clocksmith/m3t4@{source_commit}".encode("utf-8")
    )
    if import_manifest.get("sourceRevision") != expected_source_revision:
        raise ValueError("import manifest sourceRevision mismatch")
    for name in ("challenge", "candidate", "search_receipt", "development_trace"):
        filename = BUNDLE_FILES[name]
        expected_digest = import_manifest.get("files", {}).get(filename)
        actual_digest = contracts.sha256_digest((bundle / filename).read_bytes())
        if expected_digest != actual_digest:
            raise ValueError(f"import manifest digest mismatch for {filename}")
    contracts.validate_artifact(bundle / BUNDLE_FILES["challenge"])
    contracts.validate_artifact(bundle / BUNDLE_FILES["candidate"])
    contracts.validate_artifact(bundle / BUNDLE_FILES["search_receipt"])
    if challenge["challengeId"] != EXPECTED_CHALLENGE_ID:
        raise ValueError("unsupported Clockwork challenge")
    if challenge["kernelDigest"] != EXPECTED_KERNEL_DIGEST:
        raise ValueError("challenge kernel digest is not implemented by Gamma")
    if challenge["evaluatorDigest"] != EXPECTED_EVALUATOR_DIGEST:
        raise ValueError("challenge evaluator digest is not implemented by Gamma")
    if candidate["genomeSchemaDigest"] != EXPECTED_GENOME_SCHEMA_DIGEST:
        raise ValueError("candidate genome schema digest is not implemented by Gamma")
    if candidate["challengeDigest"] != challenge["challengeDigest"]:
        raise ValueError("candidate challenge digest mismatch")
    if search_receipt["challengeDigest"] != challenge["challengeDigest"]:
        raise ValueError("search receipt challenge digest mismatch")
    if search_receipt["authority"] != "advisory":
        raise ValueError("M3T4 search receipt must be advisory")
    development_digest = contracts.sha256_digest(
        contracts.canonical_bytes(development_trace)
    )
    if challenge["population"]["digest"] != development_digest:
        raise ValueError("development trace digest mismatch")
    transfer_trace = _load_array(transfer_trace_path)

    canonical_genome = contracts.canonical_bytes(candidate["genome"])
    roundtrip_evidence = {
        "candidateDigest": candidate["candidateDigest"],
        "canonicalGenomeDigest": contracts.sha256_digest(canonical_genome),
        "roundtripCanonical": (
            contracts.canonical_bytes(json.loads(canonical_genome)) == canonical_genome
        ),
        "literalIdentityFallback": candidate["literalIdentityFallback"],
    }
    roundtrip_ok = (
        roundtrip_evidence["roundtripCanonical"]
        and roundtrip_evidence["literalIdentityFallback"]
        and roundtrip_evidence["canonicalGenomeDigest"] == candidate["candidateDigest"]
    )

    development_first = evaluate_genome(candidate["genome"], development_trace)
    development_second = evaluate_genome(candidate["genome"], development_trace)
    chronological_evidence = {
        "first": development_first,
        "second": development_second,
        "byteIdentical": (
            contracts.canonical_bytes(development_first)
            == contracts.canonical_bytes(development_second)
        ),
        "traceDigest": development_digest,
    }
    chronological_ok = chronological_evidence["byteIdentical"]

    matching_search_rows = [
        row
        for row in search_receipt["evaluations"]
        if row["candidateDigest"] == candidate["candidateDigest"]
    ]
    resource_declaration = candidate["resourceDeclaration"]
    source_evidence = {
        "matchingSearchRows": len(matching_search_rows),
        "gammaEvaluation": development_first,
        "m3t4Evaluation": matching_search_rows[0] if len(matching_search_rows) == 1 else None,
        "declaredCanonicalGenomeBytes": resource_declaration.get(
            "canonicalGenomeBytes"
        ),
        "actualCanonicalGenomeBytes": len(canonical_genome),
        "declaredUpstreamMutations": resource_declaration.get("upstreamMutations"),
        "traceClosed": candidate["traceClosureDeclaration"]["closed"],
        "mutatesUpstream": candidate["traceClosureDeclaration"]["mutatesUpstream"],
    }
    source_ok = (
        len(matching_search_rows) == 1
        and matching_search_rows[0]["valid"] is True
        and matching_search_rows[0]["objectives"] == development_first["objectives"]
        and matching_search_rows[0]["rawLedger"] == development_first["rawLedger"]
        and resource_declaration.get("canonicalGenomeBytes") == len(canonical_genome)
        and resource_declaration.get("upstreamMutations") == 0
        and source_evidence["traceClosed"] is True
        and source_evidence["mutatesUpstream"] is False
    )

    transfer = evaluate_genome(candidate["genome"], transfer_trace)
    transfer_evidence = {
        "traceDigest": contracts.sha256_digest(
            contracts.canonical_bytes(transfer_trace)
        ),
        "evaluation": transfer,
        "requiredSavingsUnits": 0,
    }
    transfer_ok = transfer["rawLedger"]["developmentSavingsUnits"] >= 0

    budgets = challenge["budgets"]
    runtime_evidence = {
        "estimatedCycles": development_first["objectives"]["estimatedCycles"],
        "rows": development_first["rawLedger"]["rows"],
        "estimatedCyclesPerRow": (
            development_first["objectives"]["estimatedCycles"]
            // development_first["rawLedger"]["rows"]
        ),
        "maximum": budgets["maxEstimatedCyclesPerRow"],
    }
    runtime_ok = (
        runtime_evidence["estimatedCyclesPerRow"]
        <= budgets["maxEstimatedCyclesPerRow"]
    )
    memory_evidence = {
        "peakStateBytes": development_first["objectives"]["peakStateBytes"],
        "declaredPeakStateBytes": resource_declaration.get("peakStateBytes"),
        "maximum": budgets["maxPeakStateBytes"],
    }
    memory_ok = (
        memory_evidence["peakStateBytes"] == memory_evidence["declaredPeakStateBytes"]
        and memory_evidence["peakStateBytes"] <= budgets["maxPeakStateBytes"]
        and len(canonical_genome) <= budgets["maxCanonicalGenomeBytes"]
    )
    gate_results = {
        "roundtrip": _gate("passed" if roundtrip_ok else "failed", roundtrip_evidence),
        "chronologicalReplay": _gate(
            "passed" if chronological_ok else "failed",
            chronological_evidence,
        ),
        "sourceAccounting": _gate(
            "passed" if source_ok else "failed",
            source_evidence,
        ),
        "transfer": _gate("passed" if transfer_ok else "failed", transfer_evidence),
        "runtime": _gate("passed" if runtime_ok else "failed", runtime_evidence),
        "memory": _gate("passed" if memory_ok else "failed", memory_evidence),
    }
    first_failed = next(
        (name for name, result in gate_results.items() if result["status"] != "passed"),
        None,
    )
    result = "accepted" if first_failed is None else "rejected"
    materialization = {
        "challengeDigest": challenge["challengeDigest"],
        "candidateDigest": candidate["candidateDigest"],
        "genomeSchemaDigest": candidate["genomeSchemaDigest"],
        "kernelDigest": challenge["kernelDigest"],
        "evaluatorDigest": challenge["evaluatorDigest"],
        "upstreamSourceRevision": import_manifest["sourceRevision"],
    }
    gamma_source_revision = contracts.sha256_digest(Path(__file__).read_bytes())
    now = created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    base = {
        "schema": "gamma.candidate_receipt.v1",
        "authority": "gamma",
        "contractSetDigest": challenge["contractSetDigest"],
        "challengeDigest": challenge["challengeDigest"],
        "candidateDigest": candidate["candidateDigest"],
        "proofReceiptDigest": None,
        "searchReceiptDigest": search_receipt["receiptDigest"],
        "gammaMaterialization": {
            "id": f"clockwork-residual-expert-{candidate['candidateDigest'][7:19]}",
            "digest": contracts.sha256_digest(contracts.canonical_bytes(materialization)),
            "upstreamSourceRevision": import_manifest["sourceRevision"],
        },
        "gates": gate_results,
        "ledgers": {
            "bytes": {
                "unit": "integer-brier-loss-unit",
                "development": development_first["rawLedger"],
                "transfer": transfer["rawLedger"],
                "compressionBytesClaimed": False,
            },
            "package": {
                "canonicalGenomeBytes": len(canonical_genome),
                "maximum": budgets["maxCanonicalGenomeBytes"],
                "upstreamSourceRevision": import_manifest["sourceRevision"],
            },
            "runtime": runtime_evidence,
            "memory": memory_evidence,
        },
        "result": result,
        "firstFailedGate": first_failed,
        "sourceRevision": gamma_source_revision,
        "environment": {
            "implementation": "gamma.clockwork-candidate-gate/v1",
            "arithmetic": "python-integer-truncating-division-v1",
            "independentFromM3t4": True,
        },
        "createdAt": now,
    }
    return {
        **base,
        "receiptDigest": contracts.artifact_digest(base, "receiptDigest"),
    }


def import_bundle(args: argparse.Namespace) -> None:
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sources = {
        "challenge": args.challenge.resolve(),
        "candidate": args.candidate.resolve(),
        "search_receipt": args.search_receipt.resolve(),
        "development_trace": args.development_trace.resolve(),
    }
    contracts.validate_artifact(sources["challenge"])
    contracts.validate_artifact(sources["candidate"])
    contracts.validate_artifact(sources["search_receipt"])
    for name, source in sources.items():
        shutil.copyfile(source, output / BUNDLE_FILES[name])
    source_revision = contracts.sha256_digest(
        f"git:clocksmith/m3t4@{args.m3t4_revision}".encode("utf-8")
    )
    manifest = {
        "schema": "gamma.clockwork_import_manifest.v1",
        "sourceRepository": "clocksmith/m3t4",
        "sourceCommit": args.m3t4_revision,
        "sourceRevision": source_revision,
        "files": {
            BUNDLE_FILES[name]: contracts.sha256_digest(source.read_bytes())
            for name, source in sources.items()
        },
    }
    (output / BUNDLE_FILES["import_manifest"]).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


def run_gate(args: argparse.Namespace) -> None:
    receipt = evaluate_bundle(
        args.bundle.resolve(),
        transfer_trace_path=args.transfer_trace.resolve(),
        created_at=args.created_at,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    contracts.validate_artifact(args.output)
    print(json.dumps(receipt, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    importer = subparsers.add_parser("import")
    importer.add_argument("--challenge", required=True, type=Path)
    importer.add_argument("--candidate", required=True, type=Path)
    importer.add_argument("--search-receipt", required=True, type=Path)
    importer.add_argument("--development-trace", required=True, type=Path)
    importer.add_argument("--m3t4-revision", required=True)
    importer.add_argument("--output-dir", required=True, type=Path)
    importer.set_defaults(handler=import_bundle)
    gate = subparsers.add_parser("gate")
    gate.add_argument("--bundle", required=True, type=Path)
    gate.add_argument("--transfer-trace", type=Path, default=DEFAULT_TRANSFER_TRACE)
    gate.add_argument("--created-at")
    gate.add_argument("--output", required=True, type=Path)
    gate.set_defaults(handler=run_gate)
    args = parser.parse_args()
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
