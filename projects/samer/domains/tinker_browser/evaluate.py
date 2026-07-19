#!/usr/bin/env python3
"""Evaluate a Tinker-trained PEFT adapter for Doppler browser admission."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any


INPUT_SCHEMA = "gamma.tinker-browser-evaluation-input/v1"
RECEIPT_SCHEMA = "gamma.tinker-browser-selection-receipt/v1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
DETERMINISM_LEVELS = (
    "sameDeviceRunToRun",
    "sameDeviceBatchInvariant",
    "crossDeviceNumerical",
    "crossDeviceOutputAgreement",
)


class EvaluationContractError(ValueError):
    """Raised when an evaluation input violates the frozen contract."""


def _require_object(value: Any, field: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise EvaluationContractError(
            f"{field} fields must be {sorted(keys)}; received {actual}"
        )
    return value


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvaluationContractError(f"{field} must be a nonempty string")
    return value.strip()


def _require_sha256(value: Any, field: str) -> str:
    digest = _require_text(value, field).removeprefix("sha256:").lower()
    if not SHA256_PATTERN.fullmatch(digest):
        raise EvaluationContractError(f"{field} must be a SHA-256 digest")
    return digest


def _require_fraction(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise EvaluationContractError(f"{field} must be a number from 0 through 1")
    result = float(value)
    if not math.isfinite(result) or result < 0 or result > 1:
        raise EvaluationContractError(f"{field} must be a finite number from 0 through 1")
    return result


def _require_nonnegative(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise EvaluationContractError(f"{field} must be a nonnegative number")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise EvaluationContractError(f"{field} must be a finite nonnegative number")
    return result


def _require_positive_integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise EvaluationContractError(f"{field} must be a positive integer")
    return value


def _require_nonnegative_integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EvaluationContractError(f"{field} must be a nonnegative integer")
    return value


def _require_boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise EvaluationContractError(f"{field} must be a boolean")
    return value


def _normalize_population(value: Any, field: str, expected_role: str) -> dict[str, Any]:
    population = _require_object(value, field, {"id", "role", "sha256", "sampleCount"})
    role = _require_text(population["role"], f"{field}.role")
    if role != expected_role:
        raise EvaluationContractError(f'{field}.role must be "{expected_role}"')
    return {
        "id": _require_text(population["id"], f"{field}.id"),
        "role": role,
        "sha256": _require_sha256(population["sha256"], f"{field}.sha256"),
        "sampleCount": _require_positive_integer(
            population["sampleCount"], f"{field}.sampleCount"
        ),
    }


def _normalize_evidence(value: Any, field: str) -> dict[str, str]:
    evidence = _require_object(value, field, {"receiptSha256", "decision"})
    decision = _require_text(evidence["decision"], f"{field}.decision")
    if decision not in {"pass", "block"}:
        raise EvaluationContractError(f'{field}.decision must be "pass" or "block"')
    return {
        "receiptSha256": _require_sha256(
            evidence["receiptSha256"], f"{field}.receiptSha256"
        ),
        "decision": decision,
    }


def _normalize_task_metric(value: Any, field: str) -> dict[str, Any]:
    metric = _require_object(
        value,
        field,
        {"metricId", "base", "candidate", "minimumCandidate", "minimumGain"},
    )
    return {
        "metricId": _require_text(metric["metricId"], f"{field}.metricId"),
        "base": _require_fraction(metric["base"], f"{field}.base"),
        "candidate": _require_fraction(metric["candidate"], f"{field}.candidate"),
        "minimumCandidate": _require_fraction(
            metric["minimumCandidate"], f"{field}.minimumCandidate"
        ),
        "minimumGain": _require_fraction(
            metric["minimumGain"], f"{field}.minimumGain"
        ),
    }


def _normalize_retention_metric(value: Any, field: str) -> dict[str, Any]:
    metric = _require_object(
        value,
        field,
        {"metricId", "base", "candidate", "maximumRegression"},
    )
    return {
        "metricId": _require_text(metric["metricId"], f"{field}.metricId"),
        "base": _require_fraction(metric["base"], f"{field}.base"),
        "candidate": _require_fraction(metric["candidate"], f"{field}.candidate"),
        "maximumRegression": _require_fraction(
            metric["maximumRegression"], f"{field}.maximumRegression"
        ),
    }


def _normalize_numerical_level(value: Any, field: str) -> dict[str, Any]:
    level = _require_object(value, field, {"required", "maxAbsDifference", "tolerance"})
    return {
        "required": _require_boolean(level["required"], f"{field}.required"),
        "maxAbsDifference": _require_nonnegative(
            level["maxAbsDifference"], f"{field}.maxAbsDifference"
        ),
        "tolerance": _require_nonnegative(level["tolerance"], f"{field}.tolerance"),
    }


def _normalize_output_agreement(value: Any, field: str) -> dict[str, Any]:
    level = _require_object(
        value,
        field,
        {"required", "matchingOutputs", "totalOutputs", "minimumAgreement"},
    )
    matching = _require_nonnegative_integer(
        level["matchingOutputs"], f"{field}.matchingOutputs"
    )
    total = _require_positive_integer(level["totalOutputs"], f"{field}.totalOutputs")
    if matching > total:
        raise EvaluationContractError(f"{field}.matchingOutputs cannot exceed totalOutputs")
    return {
        "required": _require_boolean(level["required"], f"{field}.required"),
        "matchingOutputs": matching,
        "totalOutputs": total,
        "minimumAgreement": _require_fraction(
            level["minimumAgreement"], f"{field}.minimumAgreement"
        ),
    }


def validate_input(value: Any) -> dict[str, Any]:
    """Validate and normalize one evaluation input."""
    root = _require_object(
        value,
        "input",
        {
            "schema",
            "evaluationId",
            "artifact",
            "populations",
            "evidence",
            "metrics",
            "determinism",
            "claimBoundary",
        },
    )
    if root["schema"] != INPUT_SCHEMA:
        raise EvaluationContractError(f'input.schema must be "{INPUT_SCHEMA}"')
    artifact = _require_object(
        root["artifact"],
        "artifact",
        {
            "baseModelId",
            "baseCheckpointSha256",
            "adapterId",
            "adapterSha256",
            "trainer",
            "trainingRunId",
        },
    )
    populations = _require_object(root["populations"], "populations", {"task", "retention"})
    evidence = _require_object(root["evidence"], "evidence", {"dopplerIdentity", "dopplerParity"})
    metrics = _require_object(root["metrics"], "metrics", {"task", "retention"})
    determinism = _require_object(
        root["determinism"], "determinism", set(DETERMINISM_LEVELS)
    )
    trainer = _require_text(artifact["trainer"], "artifact.trainer")
    if trainer != "thinking-machines/tinker":
        raise EvaluationContractError(
            'artifact.trainer must be "thinking-machines/tinker" for this profile'
        )
    return {
        "schema": INPUT_SCHEMA,
        "evaluationId": _require_text(root["evaluationId"], "evaluationId"),
        "artifact": {
            "baseModelId": _require_text(artifact["baseModelId"], "artifact.baseModelId"),
            "baseCheckpointSha256": _require_sha256(
                artifact["baseCheckpointSha256"], "artifact.baseCheckpointSha256"
            ),
            "adapterId": _require_text(artifact["adapterId"], "artifact.adapterId"),
            "adapterSha256": _require_sha256(
                artifact["adapterSha256"], "artifact.adapterSha256"
            ),
            "trainer": trainer,
            "trainingRunId": _require_text(
                artifact["trainingRunId"], "artifact.trainingRunId"
            ),
        },
        "populations": {
            "task": _normalize_population(populations["task"], "populations.task", "sealed_task"),
            "retention": _normalize_population(
                populations["retention"], "populations.retention", "sealed_retention"
            ),
        },
        "evidence": {
            "dopplerIdentity": _normalize_evidence(
                evidence["dopplerIdentity"], "evidence.dopplerIdentity"
            ),
            "dopplerParity": _normalize_evidence(
                evidence["dopplerParity"], "evidence.dopplerParity"
            ),
        },
        "metrics": {
            "task": _normalize_task_metric(metrics["task"], "metrics.task"),
            "retention": _normalize_retention_metric(
                metrics["retention"], "metrics.retention"
            ),
        },
        "determinism": {
            "sameDeviceRunToRun": _normalize_numerical_level(
                determinism["sameDeviceRunToRun"], "determinism.sameDeviceRunToRun"
            ),
            "sameDeviceBatchInvariant": _normalize_numerical_level(
                determinism["sameDeviceBatchInvariant"],
                "determinism.sameDeviceBatchInvariant",
            ),
            "crossDeviceNumerical": _normalize_numerical_level(
                determinism["crossDeviceNumerical"], "determinism.crossDeviceNumerical"
            ),
            "crossDeviceOutputAgreement": _normalize_output_agreement(
                determinism["crossDeviceOutputAgreement"],
                "determinism.crossDeviceOutputAgreement",
            ),
        },
        "claimBoundary": _require_text(root["claimBoundary"], "claimBoundary"),
    }


def _numerical_decision(level: dict[str, Any]) -> dict[str, Any]:
    passed = level["maxAbsDifference"] <= level["tolerance"]
    return {**level, "passed": passed}


def _agreement_decision(level: dict[str, Any]) -> dict[str, Any]:
    agreement = level["matchingOutputs"] / level["totalOutputs"]
    return {**level, "agreement": agreement, "passed": agreement >= level["minimumAgreement"]}


def _stable_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evaluate(value: Any) -> dict[str, Any]:
    """Return a deterministic Gamma selection receipt."""
    contract = validate_input(value)
    blockers: list[str] = []
    for evidence_id, evidence in contract["evidence"].items():
        if evidence["decision"] != "pass":
            blockers.append(f"{evidence_id}_blocked")

    task = contract["metrics"]["task"]
    task_gain = task["candidate"] - task["base"]
    task_passed = (
        task["candidate"] >= task["minimumCandidate"]
        and task_gain >= task["minimumGain"]
    )
    if not task_passed:
        blockers.append("sealed_task_gain_failed")

    retention = contract["metrics"]["retention"]
    retention_regression = max(0.0, retention["base"] - retention["candidate"])
    retention_passed = retention_regression <= retention["maximumRegression"]
    if not retention_passed:
        blockers.append("sealed_retention_floor_failed")

    determinism = {
        "sameDeviceRunToRun": _numerical_decision(
            contract["determinism"]["sameDeviceRunToRun"]
        ),
        "sameDeviceBatchInvariant": _numerical_decision(
            contract["determinism"]["sameDeviceBatchInvariant"]
        ),
        "crossDeviceNumerical": _numerical_decision(
            contract["determinism"]["crossDeviceNumerical"]
        ),
        "crossDeviceOutputAgreement": _agreement_decision(
            contract["determinism"]["crossDeviceOutputAgreement"]
        ),
    }
    for level_id, level in determinism.items():
        if level["required"] and not level["passed"]:
            blockers.append(f"determinism_{level_id}_failed")

    decision = "gamma_selected" if not blockers else "blocked"
    core = {
        "schema": RECEIPT_SCHEMA,
        "evaluationId": contract["evaluationId"],
        "artifact": contract["artifact"],
        "populations": contract["populations"],
        "evidence": contract["evidence"],
        "task": {**task, "gain": task_gain, "passed": task_passed},
        "retention": {
            **retention,
            "regression": retention_regression,
            "passed": retention_passed,
        },
        "determinism": determinism,
        "decision": decision,
        "blockers": sorted(blockers),
        "admission": {
            "candidateCompetitionAllowed": decision == "gamma_selected",
            "promotionAllowed": False,
        },
        "claimBoundary": contract["claimBoundary"],
    }
    return {**core, "receiptSha256": _stable_hash(core)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0 if result["decision"] == "gamma_selected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
