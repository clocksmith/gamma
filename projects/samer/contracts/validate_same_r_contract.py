#!/usr/bin/env python3
"""Validate a SAME-R contract suite and its cross-object invariants."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
import json
from pathlib import Path
import re
from typing import Any


CONTRACT_DIR = Path(__file__).resolve().parent
DEFAULT_SUITE = CONTRACT_DIR / "example.same-r-contract-suite.json"
DEFAULT_SCHEMA = CONTRACT_DIR / "same-r-contract-suite.schema.json"

ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

BUDGET_FIELDS = (
    "proposalCalls",
    "criticCalls",
    "teacherCalls",
    "generationCalls",
    "materializations",
    "trainingRuns",
    "evaluationCalls",
    "evaluationLooks",
    "checkpointEvaluations",
    "itemEvaluations",
    "adjudications",
    "humanDecisions",
    "sealedHoldoutLooks",
    "recursionDepth",
    "childCount",
)
HISTORY_FIELDS = (
    "accepted",
    "rejected",
    "blocked",
    "invalidated",
    "saturated",
    "promoted",
)
REQUIRED_POPULATIONS = {
    "qualification",
    "prompt_development",
    "construction",
    "training",
    "public_diagnostic",
    "sealed_promotion",
    "selector_meta_evaluation",
}
TERMINAL_SATURATION_REASONS = {
    "promotion_achieved",
    "candidate_budget_exhausted",
    "eligible_registry_exhausted",
    "predeclared_diminishing_returns_rule_met",
    "domain_owner_stop",
}


class ContractValidationError(ValueError):
    """Raised when a SAME-R bundle violates its declared contract."""


def _error(path: str, message: str) -> None:
    raise ContractValidationError(f"{path}: {message}")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"{path}: cannot load JSON: {exc}") from exc


def _json_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    _error("schema", f"unsupported JSON Schema type {expected!r}")
    return False


def _resolve_ref(root: Mapping[str, Any], ref: str) -> Mapping[str, Any]:
    if not ref.startswith("#/"):
        _error("schema", f"only local JSON pointers are supported, got {ref!r}")
    value: Any = root
    for raw_part in ref[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or part not in value:
            _error("schema", f"unresolved reference {ref!r}")
        value = value[part]
    if not isinstance(value, dict):
        _error("schema", f"reference {ref!r} does not resolve to an object")
    return value


def _validate_schema_instance(
    value: Any,
    schema: Mapping[str, Any],
    root: Mapping[str, Any],
    path: str = "$",
) -> None:
    """Validate the JSON Schema subset used by the checked-in SAME-R schema."""
    if "$ref" in schema:
        _validate_schema_instance(value, _resolve_ref(root, schema["$ref"]), root, path)
        return

    if "const" in schema and value != schema["const"]:
        _error(path, f"must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        _error(path, f"must be one of {schema['enum']!r}")

    declared_type = schema.get("type")
    if declared_type is not None:
        types = [declared_type] if isinstance(declared_type, str) else declared_type
        if not any(_json_type_matches(value, item) for item in types):
            _error(path, f"must have JSON type {types!r}")

    if isinstance(value, dict):
        required = set(schema.get("required", []))
        missing = sorted(required - set(value))
        if missing:
            _error(path, f"missing required fields {missing}")
        minimum = schema.get("minProperties")
        if minimum is not None and len(value) < minimum:
            _error(path, f"must contain at least {minimum} properties")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            item_path = f"{path}.{key}"
            if key in properties:
                _validate_schema_instance(item, properties[key], root, item_path)
            elif additional is False:
                _error(path, f"unknown field {key!r}")
            elif isinstance(additional, dict):
                _validate_schema_instance(item, additional, root, item_path)

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if minimum is not None and len(value) < minimum:
            _error(path, f"must contain at least {minimum} items")
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True) for item in value]
            if len(canonical) != len(set(canonical)):
                _error(path, "must contain unique items")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _validate_schema_instance(item, item_schema, root, f"{path}[{index}]")

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if minimum is not None and len(value) < minimum:
            _error(path, f"must contain at least {minimum} characters")
        pattern = schema.get("pattern")
        if pattern is not None and re.fullmatch(pattern, value) is None:
            _error(path, f"does not match {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            _error(path, f"must be at least {schema['minimum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            _error(path, f"must exceed {schema['exclusiveMinimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            _error(path, f"must be at most {schema['maximum']}")


def validate_schema_alignment(schema_path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    """Validate the validator/schema handshake and return the parsed schema."""
    schema = _load_json(schema_path)
    if not isinstance(schema, dict):
        _error("schema", "root must be an object")
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        _error("schema.$schema", "must declare JSON Schema draft 2020-12")
    expected_defs = {
        "approachRegistry",
        "participantRegistry",
        "labelAuthority",
        "causalContract",
        "runContract",
        "contaminationAudit",
        "metricEvidence",
        "trialReceipt",
        "selectionReceipt",
        "saturationDecision",
    }
    missing_defs = sorted(expected_defs - set(schema.get("$defs", {})))
    if missing_defs:
        _error("schema.$defs", f"missing canonical definitions {missing_defs}")
    if schema.get("additionalProperties") is not False:
        _error("schema", "top-level additionalProperties must be false")
    return schema


def _require_unique(values: Iterable[str], path: str) -> set[str]:
    values = list(values)
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        _error(path, f"contains duplicate identifiers {duplicates}")
    return set(values)


def _require_id(value: Any, path: str) -> str:
    if not isinstance(value, str) or ID_PATTERN.fullmatch(value) is None:
        _error(path, "must be a nonempty stable identifier")
    return value


def _validate_budget_references(
    budget: Mapping[str, Any], participant_ids: set[str], path: str
) -> None:
    for participant_id in budget["modelTokensByParticipant"]:
        if participant_id not in participant_ids:
            _error(
                f"{path}.modelTokensByParticipant",
                f"references unknown participant {participant_id!r}",
            )


def _assert_budget_sum(
    total: Mapping[str, Any],
    spent: Mapping[str, Any],
    remaining: Mapping[str, Any],
    path: str,
) -> None:
    for field in BUDGET_FIELDS:
        if total[field] != spent[field] + remaining[field]:
            _error(
                f"{path}.{field}",
                f"declared {total[field]} != spent {spent[field]} + remaining {remaining[field]}",
            )
    token_ids = (
        set(total["modelTokensByParticipant"])
        | set(spent["modelTokensByParticipant"])
        | set(remaining["modelTokensByParticipant"])
    )
    for participant_id in token_ids:
        declared = total["modelTokensByParticipant"].get(participant_id, 0)
        debit = spent["modelTokensByParticipant"].get(participant_id, 0)
        balance = remaining["modelTokensByParticipant"].get(participant_id, 0)
        if declared != debit + balance:
            _error(
                f"{path}.modelTokensByParticipant.{participant_id}",
                f"declared {declared} != spent {debit} + remaining {balance}",
            )


def _validate_registry(
    suite: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], set[str]]:
    registry = suite["approachRegistry"]
    entries = registry["entries"]
    approach_ids = _require_unique(
        (_require_id(entry["approachId"], "approachRegistry.entries[].approachId") for entry in entries),
        "approachRegistry.entries",
    )
    approaches = {entry["approachId"]: entry for entry in entries}

    history = registry["history"]
    seen: dict[str, str] = {}
    for disposition in HISTORY_FIELDS:
        for trial_id in history[disposition]:
            previous = seen.get(trial_id)
            if previous is not None:
                _error(
                    "approachRegistry.history",
                    f"trial {trial_id!r} appears in both {previous!r} and {disposition!r}",
                )
            seen[trial_id] = disposition

    causal = suite["causalContract"]
    approach_id = causal["approachId"]
    if approach_id not in approach_ids:
        _error("causalContract.approachId", "is absent from the approach registry")
    approach = approaches[approach_id]
    if approach["status"] != "eligible":
        _error("causalContract.approachId", "must select an eligible approach")
    if causal["domain"] not in approach["eligibleDomains"]:
        _error("causalContract.domain", "is outside the approach's eligible domains")
    if causal["capability"] not in approach["eligibleCapabilities"]:
        _error(
            "causalContract.capability",
            "is outside the approach's eligible capabilities",
        )
    return approaches, set(seen)


def _validate_participants_and_authority(
    suite: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    participants = suite["participantRegistry"]["participants"]
    _require_unique(
        (
            _require_id(
                participant["participantId"],
                "participantRegistry.participants[].participantId",
            )
            for participant in participants
        ),
        "participantRegistry.participants",
    )
    by_id = {participant["participantId"]: participant for participant in participants}
    authority_ids = _require_unique(
        (authority["authorityId"] for authority in suite["labelAuthorities"]),
        "labelAuthorities",
    )
    authority_by_id = {
        authority["authorityId"]: authority for authority in suite["labelAuthorities"]
    }

    for participant in participants:
        participant_id = participant["participantId"]
        for authority_id in participant["labelAuthorityIds"]:
            authority = authority_by_id.get(authority_id)
            if authority is None:
                _error(
                    f"participantRegistry.{participant_id}.labelAuthorityIds",
                    f"references unknown authority {authority_id!r}",
                )
            if authority["participantId"] != participant_id:
                _error(
                    f"participantRegistry.{participant_id}.labelAuthorityIds",
                    f"authority {authority_id!r} belongs to another participant",
                )
        _validate_budget_references(
            participant["budget"], set(by_id), f"participantRegistry.{participant_id}.budget"
        )

    run_manifest_ids = {run["data"]["manifestId"] for run in suite["runContracts"]}
    for authority_id in authority_ids:
        authority = authority_by_id[authority_id]
        participant_id = authority["participantId"]
        participant = by_id.get(participant_id)
        if participant is None:
            _error(
                f"labelAuthorities.{authority_id}.participantId",
                f"references unknown participant {participant_id!r}",
            )
        if "teacher" not in participant["roles"]:
            _error(
                f"labelAuthorities.{authority_id}.participantId",
                "label authority requires the teacher role",
            )
        if authority_id not in participant["labelAuthorityIds"]:
            _error(
                f"labelAuthorities.{authority_id}",
                "must be listed by its owning participant",
            )
        if authority["scope"]["domain"] not in participant["domains"]:
            _error(
                f"labelAuthorities.{authority_id}.scope.domain",
                "is outside the participant's registered domains",
            )
        unknown_manifests = set(authority["downstreamManifestIds"]) - run_manifest_ids
        if unknown_manifests:
            _error(
                f"labelAuthorities.{authority_id}.downstreamManifestIds",
                f"references unknown run manifests {sorted(unknown_manifests)}",
            )
    return by_id


def _lineage_projection(run: Mapping[str, Any]) -> dict[str, Any]:
    student = run["student"]
    training = run["training"]
    return {
        "modelId": student["modelId"],
        "modelRevision": student["modelRevision"],
        "baseCheckpointId": student["baseCheckpointId"],
        "baseCheckpointSha256": student["baseCheckpointSha256"],
        "tokenizerRevision": student["tokenizerRevision"],
        "tokenizerSha256": student["tokenizerSha256"],
        "parameterManifestSha256": student["parameterManifestSha256"],
        "adapter": student["adapter"],
        "optimizerHash": training["optimizerHash"],
        "scheduleHash": training["scheduleHash"],
        "precision": training["precision"],
        "deviceClass": training["deviceClass"],
        "runtimeMode": training["runtimeMode"],
        "updateBudget": training["updateBudget"],
        "retryPolicy": training["retryPolicy"],
        "checkpointPolicy": training["checkpointPolicy"],
        "evaluatorId": run["evaluation"]["evaluatorId"],
        "evaluatorHash": run["evaluation"]["evaluatorHash"],
        "decodePolicyHash": run["evaluation"]["decodePolicyHash"],
    }


def _validate_denominator(
    denominator: Mapping[str, Any], path: str, *, allow_disputed: bool
) -> None:
    counted = (
        denominator["scored"]
        + denominator["missing"]
        + denominator["malformed"]
        + denominator["excluded"]
    )
    if denominator["expected"] != counted:
        _error(
            path,
            f"expected {denominator['expected']} != scored/missing/malformed/excluded total {counted}",
        )
    if allow_disputed and denominator.get("disputed", 0) > denominator["scored"]:
        _error(path, "disputed count cannot exceed scored count")


def _validate_run_contracts(
    suite: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    causal = suite["causalContract"]
    runs = suite["runContracts"]
    _require_unique((run["runId"] for run in runs), "runContracts[].runId")
    _require_unique((run["laneId"] for run in runs), "runContracts[].laneId")
    by_lane = {run["laneId"]: run for run in runs}
    by_id = {run["runId"]: run for run in runs}
    required_lanes = set(causal["lanes"].values())
    if set(by_lane) != required_lanes or len(required_lanes) != 3:
        _error(
            "runContracts[].laneId",
            "must contain exactly the causal anchor, targeted, and random-control lanes",
        )

    baseline = causal["baselineArtifact"]
    reference_lineage = _lineage_projection(runs[0])
    for index, run in enumerate(runs):
        path = f"runContracts[{index}]"
        if run["experimentId"] != causal["experimentId"]:
            _error(path, "experimentId differs from the causal contract")
        if run["interventionId"] != causal["interventionId"]:
            _error(path, "interventionId differs from the causal contract")
        if run["causalContractSha256"] != causal["sha256"]:
            _error(path, "causal contract hash mismatch")
        for field in (
            "modelId",
            "modelRevision",
            "baseCheckpointId",
            "baseCheckpointSha256",
            "tokenizerRevision",
            "tokenizerSha256",
            "parameterManifestSha256",
        ):
            if run["student"][field] != baseline[field]:
                _error(f"{path}.student.{field}", "does not match baselineArtifact")
        if _lineage_projection(run) != reference_lineage:
            _error(path, "model, adapter, training, or evaluation lineage drifted")

        data = run["data"]
        row_ids = data["orderedRowIds"]
        if data["rowCount"] != len(row_ids):
            _error(f"{path}.data.rowCount", "does not match orderedRowIds length")
        _require_unique(row_ids, f"{path}.data.orderedRowIds")
        if data["consumedRowCount"] > data["rowCount"]:
            _error(f"{path}.data.consumedRowCount", "exceeds rowCount")
        if data["consumedRowCount"] == data["rowCount"] and data["resumeCursor"] is not None:
            _error(f"{path}.data.resumeCursor", "must be null after full consumption")
        if data["consumedRowCount"] < data["rowCount"] and data["resumeCursor"] is None:
            _error(f"{path}.data.resumeCursor", "is required for partial consumption")

        expected_checkpoints = run["training"]["checkpointPolicy"]["expectedCheckpointIds"]
        denominator = run["evaluation"]["checkpointDenominator"]
        if set(expected_checkpoints) != set(denominator["expected"]):
            _error(f"{path}.evaluation.checkpointDenominator", "expected set differs from checkpoint policy")
        parts = [set(denominator[name]) for name in ("evaluated", "failed", "omitted")]
        if any(parts[left] & parts[right] for left in range(3) for right in range(left + 1, 3)):
            _error(f"{path}.evaluation.checkpointDenominator", "partitions overlap")
        if set(denominator["expected"]) != set().union(*parts):
            _error(f"{path}.evaluation.checkpointDenominator", "expected checkpoints are not fully accounted")
        for name, item_denominator in run["evaluation"]["itemDenominators"].items():
            _validate_denominator(
                item_denominator,
                f"{path}.evaluation.itemDenominators.{name}",
                allow_disputed=False,
            )

        validity = run["contractValidity"]
        if validity["status"] == "invalidated" and not validity["invalidationReceiptIds"]:
            _error(f"{path}.contractValidity", "invalidated run lacks an invalidation receipt")
        if validity["status"] == "valid" and validity["invalidationReceiptIds"]:
            _error(f"{path}.contractValidity", "valid run cannot cite invalidation receipts")

    operation = causal["matchedOperation"]
    positions = operation["positions"]
    if operation["count"] != len(positions) or len(set(positions)) != len(positions):
        _error("causalContract.matchedOperation", "count and unique positions disagree")
    anchor_ids = by_lane[causal["lanes"]["anchor"]]["data"]["orderedRowIds"]
    for lane_name in ("targeted", "randomControl"):
        ids = by_lane[causal["lanes"][lane_name]]["data"]["orderedRowIds"]
        if len(ids) != len(anchor_ids):
            _error(f"runContracts.{lane_name}.data", "matched lane row count differs from anchor")
        changed = [index for index, pair in enumerate(zip(anchor_ids, ids)) if pair[0] != pair[1]]
        if changed != positions:
            _error(
                f"runContracts.{lane_name}.data.orderedRowIds",
                f"changed positions {changed} do not match declared positions {positions}",
            )
    targeted_ids = by_lane[causal["lanes"]["targeted"]]["data"]["orderedRowIds"]
    random_ids = by_lane[causal["lanes"]["randomControl"]]["data"]["orderedRowIds"]
    if operation["operation"] == "replace" and any(
        targeted_ids[position] == random_ids[position] for position in positions
    ):
        _error("runContracts", "targeted and random-control replacements must be distinct")
    return by_id


def _validate_contamination(
    suite: Mapping[str, Any], participant_ids: set[str]
) -> None:
    audit = suite["contaminationAudit"]
    populations = set(audit["populations"])
    missing = sorted(REQUIRED_POPULATIONS - populations)
    if missing:
        _error("contaminationAudit.populations", f"missing required populations {missing}")

    for check in audit["checks"]:
        for side in ("leftPopulation", "rightPopulation"):
            if check[side] not in populations:
                _error(f"contaminationAudit.checks.{side}", "references an unknown population")
        if check["overlapCount"] != len(check["overlapItemIds"]):
            _error("contaminationAudit.checks", "overlapCount differs from overlapItemIds")
        if check["overlapCount"] > check["denominator"]:
            _error("contaminationAudit.checks", "overlapCount exceeds denominator")

    for access in audit["accessAudit"]:
        if access["participantId"] not in participant_ids:
            _error("contaminationAudit.accessAudit.participantId", "references an unknown participant")
        if access["population"] not in populations:
            _error("contaminationAudit.accessAudit.population", "references an unknown population")
        if access["accessType"] == "unknown" and access["status"] == "pass":
            _error("contaminationAudit.accessAudit", "unknown access cannot pass")

    if audit["overallStatus"] == "pass":
        nonpassing_checks = [check["checkId"] for check in audit["checks"] if check["status"] != "pass"]
        nonpassing_access = [
            access["participantId"] + ":" + access["population"]
            for access in audit["accessAudit"]
            if access["status"] != "pass"
        ]
        if nonpassing_checks or nonpassing_access or audit["blockingIssueIds"]:
            _error(
                "contaminationAudit.overallStatus",
                "pass conflicts with failed/blocked checks, access, or blocking issues",
            )
    elif not audit["blockingIssueIds"]:
        _error("contaminationAudit.blockingIssueIds", "fail/blocked audit requires issue IDs")


def _validate_metrics(
    suite: Mapping[str, Any], participants: Mapping[str, Mapping[str, Any]]
) -> set[str]:
    metrics = suite["metricEvidence"]
    metric_evidence_ids = _require_unique(
        (metric["metricEvidenceId"] for metric in metrics), "metricEvidence"
    )
    causal = suite["causalContract"]
    required_metric_ids = {causal["primaryMetric"]["metricId"]} | {
        guardrail["metricId"] for guardrail in causal["guardrails"]
    }
    present_metric_ids = {metric["metricId"] for metric in metrics}
    if not required_metric_ids <= present_metric_ids:
        _error("metricEvidence", f"missing causal metrics {sorted(required_metric_ids - present_metric_ids)}")
    for metric in metrics:
        path = f"metricEvidence.{metric['metricEvidenceId']}"
        participant = participants.get(metric["scorerId"])
        if participant is None or "evaluator" not in participant["roles"]:
            _error(f"{path}.scorerId", "must reference a registered evaluator")
        _validate_denominator(metric["denominator"], f"{path}.denominator", allow_disputed=True)
        if metric["measurementType"] == "deterministic_measurement" and metric["adjudicationType"] == "human_adjudicated":
            _error(path, "deterministic measurement cannot erase its machine adjudication")
    return metric_evidence_ids


def _validate_trial(
    suite: Mapping[str, Any],
    runs: Mapping[str, Mapping[str, Any]],
    metric_evidence_ids: set[str],
) -> None:
    trial = suite["trialReceipt"]
    if trial["causalContractSha256"] != suite["causalContract"]["sha256"]:
        _error("trialReceipt.causalContractSha256", "does not match causal contract")
    if set(trial["runContractIds"]) != set(runs):
        _error("trialReceipt.runContractIds", "must name every and only bundled run")
    if not set(trial["metricEvidenceIds"]) <= metric_evidence_ids:
        _error("trialReceipt.metricEvidenceIds", "references unknown metric evidence")
    if trial["contaminationAuditId"] != suite["contaminationAudit"]["auditId"]:
        _error("trialReceipt.contaminationAuditId", "does not match bundled audit")

    _require_unique((attempt["attemptId"] for attempt in trial["attempts"]), "trialReceipt.attempts")
    attempts_by_run: dict[str, list[Mapping[str, Any]]] = {run_id: [] for run_id in runs}
    for attempt in trial["attempts"]:
        run_id = attempt["runId"]
        if run_id not in runs:
            _error("trialReceipt.attempts.runId", f"references unknown run {run_id!r}")
        attempts_by_run[run_id].append(attempt)
        if attempt["status"] == "success" and attempt["failureCode"] is not None:
            _error("trialReceipt.attempts.failureCode", "successful attempt must have null failureCode")
        if attempt["status"] != "success" and attempt["failureCode"] is None:
            _error("trialReceipt.attempts.failureCode", "failed attempt must retain a failureCode")
    for run_id, attempts in attempts_by_run.items():
        if not attempts:
            _error("trialReceipt.attempts", f"run {run_id!r} has no retained attempt")
        numbers = sorted(attempt["attemptNumber"] for attempt in attempts)
        if numbers != list(range(1, len(numbers) + 1)):
            _error("trialReceipt.attempts", f"run {run_id!r} attempt numbers are not contiguous from one")
        maximum = runs[run_id]["training"]["retryPolicy"]["maximumAttempts"]
        if numbers[-1] > maximum:
            _error("trialReceipt.attempts", f"run {run_id!r} exceeds its retry maximum")

    scoreboard = trial["checkpointScoreboard"]
    expected = sum(len(run["evaluation"]["checkpointDenominator"]["expected"]) for run in runs.values())
    evaluated = sum(len(run["evaluation"]["checkpointDenominator"]["evaluated"]) for run in runs.values())
    failed = sum(len(run["evaluation"]["checkpointDenominator"]["failed"]) for run in runs.values())
    omitted = sum(len(run["evaluation"]["checkpointDenominator"]["omitted"]) for run in runs.values())
    if scoreboard["expected"] != expected or scoreboard["evaluated"] != evaluated or scoreboard["failed"] != failed or scoreboard["omitted"] != omitted:
        _error("trialReceipt.checkpointScoreboard", "does not aggregate run checkpoint denominators")
    if scoreboard["attempted"] != evaluated + failed or expected != evaluated + failed + omitted:
        _error("trialReceipt.checkpointScoreboard", "expected/attempted/evaluated/failed/omitted do not reconcile")
    if scoreboard["selectedCheckpointId"] is not None:
        evaluated_ids = {
            checkpoint
            for run in runs.values()
            for checkpoint in run["evaluation"]["checkpointDenominator"]["evaluated"]
        }
        if scoreboard["selectedCheckpointId"] not in evaluated_ids:
            _error("trialReceipt.checkpointScoreboard.selectedCheckpointId", "was not evaluated")

    history = suite["approachRegistry"]["history"]
    disposition_history = "invalidated" if trial["invalidated"] else trial["disposition"]
    if disposition_history in history and trial["trialId"] not in history[disposition_history]:
        _error("trialReceipt.disposition", "does not agree with typed registry history")
    if trial["invalidated"] and not any(
        run["contractValidity"]["status"] == "invalidated" for run in runs.values()
    ):
        _error("trialReceipt.invalidated", "has no invalidated run contract")
    if not trial["invalidated"] and any(
        run["contractValidity"]["status"] == "invalidated" for run in runs.values()
    ):
        _error("trialReceipt.invalidated", "is false despite an invalidated run")


def _validate_selection_and_saturation(
    suite: Mapping[str, Any],
    approaches: Mapping[str, Mapping[str, Any]],
    participants: Mapping[str, Mapping[str, Any]],
) -> None:
    selection = suite["selectionReceipt"]
    saturation = suite["saturationDecision"]
    selector = participants.get(selection["selectorParticipantId"])
    if selector is None or "selector" not in selector["roles"]:
        _error("selectionReceipt.selectorParticipantId", "must reference a registered selector")
    if selection["registryHash"] != suite["approachRegistry"]["sha256"]:
        _error("selectionReceipt.registryHash", "does not match approach registry")
    if selection["frozenContractHash"] != suite["causalContract"]["sha256"]:
        _error("selectionReceipt.frozenContractHash", "does not match causal contract")
    if selection["causalContractSha256"] != suite["causalContract"]["sha256"]:
        _error("selectionReceipt.causalContractSha256", "does not match causal contract")
    if selection["saturationDecisionId"] != saturation["decisionId"]:
        _error("selectionReceipt.saturationDecisionId", "does not match saturation decision")

    considered = selection["candidatesConsidered"]
    considered_ids = _require_unique(
        (candidate["proposalId"] for candidate in considered),
        "selectionReceipt.candidatesConsidered",
    )
    rejected_ids = _require_unique(
        (candidate["proposalId"] for candidate in selection["candidatesRejected"]),
        "selectionReceipt.candidatesRejected",
    )
    if not rejected_ids <= considered_ids:
        _error("selectionReceipt.candidatesRejected", "contains a proposal that was not considered")
    selected = [
        candidate
        for candidate in considered
        if candidate["approachId"] == selection["selectedApproachId"]
        and candidate["interventionId"] == selection["selectedInterventionId"]
    ]
    if len(selected) != 1 or not selected[0]["valid"]:
        _error("selectionReceipt", "selected intervention must be one valid considered candidate")
    selected_id = selected[0]["proposalId"]
    expected_rejections = considered_ids - {selected_id}
    if rejected_ids != expected_rejections:
        _error(
            "selectionReceipt.candidatesRejected",
            f"must explain every non-selected proposal; expected {sorted(expected_rejections)}",
        )
    for candidate in considered:
        if candidate["approachId"] not in approaches:
            _error("selectionReceipt.candidatesConsidered.approachId", "references an unknown approach")
        participant = participants.get(candidate["participantId"])
        if participant is None or "proposer" not in participant["roles"]:
            _error("selectionReceipt.candidatesConsidered.participantId", "must reference a registered proposer")
    if selection["selectedApproachId"] != suite["causalContract"]["approachId"]:
        _error("selectionReceipt.selectedApproachId", "does not match causal contract")
    if selection["selectedInterventionId"] != suite["causalContract"]["interventionId"]:
        _error("selectionReceipt.selectedInterventionId", "does not match causal contract")

    gate = selection["humanGate"]
    if gate["required"]:
        authority = participants.get(gate["authority"])
        if authority is None or "adjudicator" not in authority["roles"]:
            _error("selectionReceipt.humanGate.authority", "must reference a registered adjudicator")
        if gate["status"] not in {"approved", "rejected"}:
            _error("selectionReceipt.humanGate.status", "required gate needs a terminal disposition")

    for budget_name in ("budgetBefore", "budgetDebit", "budgetRemaining"):
        _validate_budget_references(selection[budget_name], set(participants), f"selectionReceipt.{budget_name}")
    _assert_budget_sum(selection["budgetBefore"], selection["budgetDebit"], selection["budgetRemaining"], "selectionReceipt")
    if selection["budgetDebit"] != suite["trialReceipt"]["budgetDebit"]:
        _error("selectionReceipt.budgetDebit", "does not match the selected trial budget debit")
    if len(selection["recursivePath"]) != len(set(selection["recursivePath"])):
        _error("selectionReceipt.recursivePath", "contains a recursion cycle")
    if max(0, len(selection["recursivePath"]) - 1) > selection["budgetBefore"]["recursionDepth"]:
        _error("selectionReceipt.recursivePath", "exceeds declared recursion depth")

    scope = saturation["scope"]
    expected_scope = {
        "capability": suite["causalContract"]["capability"],
        "frozenContractHash": suite["causalContract"]["sha256"],
        "approachRegistryHash": suite["approachRegistry"]["sha256"],
        "historyHash": selection["historyHash"],
    }
    for field, expected in expected_scope.items():
        if scope[field] != expected:
            _error(f"saturationDecision.scope.{field}", f"does not match {field} input")
    if saturation["budgetDeclared"] != selection["budgetBefore"]:
        _error("saturationDecision.budgetDeclared", "does not match selector budgetBefore")
    if saturation["budgetSpent"] != selection["budgetDebit"]:
        _error("saturationDecision.budgetSpent", "does not match selector budgetDebit")
    if saturation["budgetRemaining"] != selection["budgetRemaining"]:
        _error("saturationDecision.budgetRemaining", "does not match selector budgetRemaining")
    _assert_budget_sum(
        saturation["budgetDeclared"],
        saturation["budgetSpent"],
        saturation["budgetRemaining"],
        "saturationDecision",
    )
    for approach_id in saturation["eligibleUntriedApproachIds"]:
        approach = approaches.get(approach_id)
        if approach is None or approach["status"] != "eligible":
            _error("saturationDecision.eligibleUntriedApproachIds", "contains an ineligible or unknown approach")
    if set(saturation["blockedTrialIds"]) & set(saturation["terminalTrialIds"]):
        _error("saturationDecision", "blocked trials cannot also be terminal trials")
    if saturation["saturated"]:
        if saturation["reasonCode"] not in TERMINAL_SATURATION_REASONS:
            _error("saturationDecision.reasonCode", "is not a terminal saturation reason")
        if saturation["pendingRequiredTrialIds"]:
            _error("saturationDecision.pendingRequiredTrialIds", "pending work prevents saturation")
        if saturation["reasonCode"] == "eligible_registry_exhausted" and saturation["eligibleUntriedApproachIds"]:
            _error("saturationDecision.reasonCode", "registry cannot be exhausted with eligible untried approaches")
        if saturation["reasonCode"] == "candidate_budget_exhausted" and any(
            saturation["budgetRemaining"][field] > 0
            for field in ("proposalCalls", "materializations", "trainingRuns", "evaluationCalls")
        ):
            _error("saturationDecision.reasonCode", "candidate budget is not exhausted")
    else:
        nonterminal_reasons = {
            "required_evaluations_pending",
            "eligible_candidates_remain",
            "budget_or_evidence_unresolved",
        }
        if saturation["reasonCode"] not in nonterminal_reasons:
            _error("saturationDecision.reasonCode", "false saturation requires a nonterminal reason")
        if (
            saturation["reasonCode"] == "required_evaluations_pending"
            and not saturation["pendingRequiredTrialIds"]
        ):
            _error(
                "saturationDecision.pendingRequiredTrialIds",
                "required_evaluations_pending needs at least one pending trial",
            )
        if (
            saturation["reasonCode"] == "eligible_candidates_remain"
            and not saturation["eligibleUntriedApproachIds"]
        ):
            _error(
                "saturationDecision.eligibleUntriedApproachIds",
                "eligible_candidates_remain requires an eligible next approach",
            )


def validate_contract_suite(
    suite_path: Path = DEFAULT_SUITE,
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    """Validate one complete suite and return the parsed object unchanged."""
    schema = validate_schema_alignment(schema_path)
    suite = _load_json(suite_path)
    _validate_schema_instance(suite, schema, schema)

    approaches, _ = _validate_registry(suite)
    participants = _validate_participants_and_authority(suite)
    for budget_name, budget in (
        ("causalContract.search.budget", suite["causalContract"]["search"]["budget"]),
        ("trialReceipt.budgetDebit", suite["trialReceipt"]["budgetDebit"]),
    ):
        _validate_budget_references(budget, set(participants), budget_name)
    runs = _validate_run_contracts(suite)
    _validate_contamination(suite, set(participants))
    metric_evidence_ids = _validate_metrics(suite, participants)
    _validate_trial(suite, runs, metric_evidence_ids)
    _validate_selection_and_saturation(suite, approaches, participants)
    return suite


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", nargs="?", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    suite = validate_contract_suite(args.suite, args.schema)
    print(
        "validated SAME-R contract suite "
        f"{suite['suiteId']}: {len(suite['runContracts'])} runs, "
        f"{len(suite['metricEvidence'])} metric receipts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
