#!/usr/bin/env python3
"""Fail-closed readiness gate for the EN/ES single-student campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema


REPO_ROOT = Path(__file__).resolve().parents[4]
PROMOTION_ROOT = REPO_ROOT / "projects" / "distillation" / "translation" / "promotion"
DEFAULT_CONTRACT = PROMOTION_ROOT / "promotion-contract.v1.json"
DEFAULT_SCHEMA = PROMOTION_ROOT / "promotion-contract.schema.json"
DEFAULT_CATALOG = PROMOTION_ROOT / "data-license-catalog.v1.json"
DEFAULT_LEDGER = PROMOTION_ROOT / "error-ledger.wmt13-nativekd2.v1.json"
DEFAULT_LEDGER_SCHEMA = PROMOTION_ROOT / "error-ledger.schema.json"
DEFAULT_HUMAN_REVIEW_CONTRACT = PROMOTION_ROOT / "human-review-contract.v1.json"
DEFAULT_HUMAN_REVIEW_SCHEMA = PROMOTION_ROOT / "human-review-contract.schema.json"
DEFAULT_POPULATION_PROCUREMENT_CONTRACT = PROMOTION_ROOT / "population-procurement-contract.v1.json"
DEFAULT_POPULATION_PROCUREMENT_SCHEMA = PROMOTION_ROOT / "population-procurement-contract.schema.json"

EXPECTED_POPULATION_ROLES = (
    "calibration",
    "checkpoint_selection",
    "seed_confirmation",
    "promotion",
)

MATCHED_TRAINING_BLOCKERS = frozenset(
    {
        "diagnostic_error_ledger_human_adjudication_pending",
        "human_review_rubric_and_threshold_absent",
        "license_catalog_contains_unverified_sources",
        "licensed_checkpoint_selection_sources_absent",
        "licensed_promotion_sources_absent",
        "licensed_seed_confirmation_sources_absent",
        "licensed_training_sources_absent",
        "matched_run_contract_absent",
        "population_calibration_identity_absent",
        "population_calibration_unmaterialized",
        "population_checkpoint_selection_identity_absent",
        "population_checkpoint_selection_unmaterialized",
        "population_contamination_audit_absent",
        "population_manifests_and_hashes_absent",
        "population_materialization_contract_absent",
        "population_promotion_identity_absent",
        "population_promotion_unmaterialized",
        "population_seed_confirmation_identity_absent",
        "population_seed_confirmation_unmaterialized",
    }
)

CHECKPOINT_SELECTION_BLOCKERS = MATCHED_TRAINING_BLOCKERS | {
    "matched_lane_receipts_absent",
}

BF16_WINNER_BLOCKERS = CHECKPOINT_SELECTION_BLOCKERS | {
    "bf16_quality_target_not_met",
    "comet_evidence_absent",
    "seed_confirmation_absent",
}

DOPPLER_ARTIFACT_COMPETITION_BLOCKERS = BF16_WINNER_BLOCKERS | {
    "gamma_bf16_selection_receipt_absent",
}

PROMOTION_SUBMISSION_BLOCKERS = DOPPLER_ARTIFACT_COMPETITION_BLOCKERS | {
    "hosted_artifact_quality_target_not_met",
}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: expected a JSON object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_receipt_core(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _population_state(contract: dict[str, Any], blockers: set[str]) -> dict[str, Any]:
    declared = {
        str(entry.get("role", "")): entry
        for entry in contract.get("populationPolicy", {}).get("roles", [])
        if isinstance(entry, dict)
    }
    result: dict[str, Any] = {}
    for role in EXPECTED_POPULATION_ROLES:
        entry = declared.get(role)
        status = str(entry.get("status", "missing")) if entry else "missing"
        result[role] = {
            "status": status,
            "manifestPath": entry.get("manifestPath") if entry else None,
            "populationHash": entry.get("populationHash") if entry else None,
        }
        if status != "frozen":
            blockers.add(f"population_{role}_unmaterialized")
            continue
        if not result[role]["manifestPath"] or not result[role]["populationHash"]:
            blockers.add(f"population_{role}_identity_absent")
    return result


def _license_state(catalog: dict[str, Any], blockers: set[str]) -> dict[str, Any]:
    entries = [entry for entry in catalog.get("entries", []) if isinstance(entry, dict)]
    verified = [entry for entry in entries if entry.get("licenseStatus") == "verified"]
    training_eligible = [entry for entry in entries if entry.get("trainingEligible") is True]
    selection_eligible = [entry for entry in entries if entry.get("selectionEligible") is True]
    confirmation_eligible = [entry for entry in entries if entry.get("confirmationEligible") is True]
    promotion_eligible = [entry for entry in entries if entry.get("promotionEligible") is True]
    if catalog.get("status") != "ready":
        blockers.add("license_catalog_contains_unverified_sources")
    if not training_eligible:
        blockers.add("licensed_training_sources_absent")
    if not selection_eligible:
        blockers.add("licensed_checkpoint_selection_sources_absent")
    if not confirmation_eligible:
        blockers.add("licensed_seed_confirmation_sources_absent")
    if not promotion_eligible:
        blockers.add("licensed_promotion_sources_absent")
    return {
        "catalogId": catalog.get("catalogId"),
        "status": catalog.get("status"),
        "entryCount": len(entries),
        "verifiedEntryCount": len(verified),
        "trainingEligibleCount": len(training_eligible),
        "selectionEligibleCount": len(selection_eligible),
        "confirmationEligibleCount": len(confirmation_eligible),
        "promotionEligibleCount": len(promotion_eligible),
    }


def build_readiness_receipt(
    *,
    contract_path: Path = DEFAULT_CONTRACT,
    schema_path: Path = DEFAULT_SCHEMA,
    catalog_path: Path = DEFAULT_CATALOG,
    ledger_path: Path = DEFAULT_LEDGER,
    ledger_schema_path: Path = DEFAULT_LEDGER_SCHEMA,
    human_review_contract_path: Path = DEFAULT_HUMAN_REVIEW_CONTRACT,
    human_review_schema_path: Path = DEFAULT_HUMAN_REVIEW_SCHEMA,
    population_procurement_contract_path: Path = DEFAULT_POPULATION_PROCUREMENT_CONTRACT,
    population_procurement_schema_path: Path = DEFAULT_POPULATION_PROCUREMENT_SCHEMA,
) -> dict[str, Any]:
    contract = _load_json(contract_path)
    schema = _load_json(schema_path)
    catalog = _load_json(catalog_path)
    ledger = _load_json(ledger_path)
    ledger_schema = _load_json(ledger_schema_path)
    human_review_contract = _load_json(human_review_contract_path)
    human_review_schema = _load_json(human_review_schema_path)
    population_procurement_contract = _load_json(population_procurement_contract_path)
    population_procurement_schema = _load_json(population_procurement_schema_path)
    jsonschema.Draft202012Validator(schema).validate(contract)
    jsonschema.Draft202012Validator(ledger_schema).validate(ledger)
    jsonschema.Draft202012Validator(human_review_schema).validate(human_review_contract)
    jsonschema.Draft202012Validator(population_procurement_schema).validate(population_procurement_contract)

    blockers: set[str] = set()
    populations = _population_state(contract, blockers)
    licenses = _license_state(catalog, blockers)

    population_policy = contract.get("populationPolicy", {})
    observed_procurement_path = str(population_procurement_contract_path.relative_to(REPO_ROOT))
    observed_procurement_hash = _sha256_file(population_procurement_contract_path)
    procurement_contract_bound = (
        population_policy.get("procurementContractPath") == observed_procurement_path
        and population_policy.get("procurementContractSha256") == observed_procurement_hash
        and population_policy.get("procurementStatus") == "frozen_requirements_awaiting_materialization"
        and population_procurement_contract.get("status") == "frozen_requirements_awaiting_materialization"
    )
    if not procurement_contract_bound:
        blockers.add("population_materialization_contract_absent")

    human_review = contract.get("humanReview", {})
    human_status = human_review.get("thresholdStatus")
    declared_human_path = human_review.get("contractPath")
    observed_human_path = str(human_review_contract_path.relative_to(REPO_ROOT))
    declared_human_hash = human_review.get("contractSha256")
    observed_human_hash = _sha256_file(human_review_contract_path)
    human_contract_bound = (
        human_status == "frozen"
        and human_review_contract.get("status") == "frozen_protocol_no_outcome_evidence"
        and declared_human_path == observed_human_path
        and declared_human_hash == observed_human_hash
    )
    if not human_contract_bound:
        blockers.add("human_review_rubric_and_threshold_absent")

    matched_campaign = contract.get("matchedCampaign", {})
    if not matched_campaign.get("runContract"):
        blockers.add("matched_run_contract_absent")

    for blocker in contract.get("promotionDecision", {}).get("blockers", []):
        blockers.add(str(blocker))

    adjudication_totals: dict[str, int] = {}
    input_assessment_totals: dict[str, int] = {}
    system_assessment_totals: dict[str, int] = {}
    diagnostic_rows_complete = True
    for row in ledger.get("rows", []):
        adjudication = row.get("adjudication", {})
        status = str(adjudication.get("status", "missing"))
        adjudication_totals[status] = adjudication_totals.get(status, 0) + 1
        input_status = str(adjudication.get("inputAssessment", {}).get("status", "missing"))
        input_assessment_totals[input_status] = input_assessment_totals.get(input_status, 0) + 1
        system_assessments = adjudication.get("systemAssessments", {})
        row_system_statuses = [
            str(assessment.get("status", "missing"))
            for assessment in system_assessments.values()
            if isinstance(assessment, dict)
        ]
        for system_status in row_system_statuses:
            system_assessment_totals[system_status] = system_assessment_totals.get(system_status, 0) + 1
        if (
            status != "complete"
            or input_status == "pending"
            or len(row_system_statuses) != len(ledger.get("systems", []))
            or any(system_status != "complete" for system_status in row_system_statuses)
        ):
            diagnostic_rows_complete = False
    if not diagnostic_rows_complete:
        blockers.add("diagnostic_error_ledger_human_adjudication_pending")

    sorted_blockers = sorted(blockers)
    blocker_set = set(sorted_blockers)

    def phase_blockers(required: frozenset[str] | set[str]) -> list[str]:
        return sorted(blocker_set.intersection(required))

    admission_blockers = {
        "matchedTraining": phase_blockers(MATCHED_TRAINING_BLOCKERS),
        "checkpointSelection": phase_blockers(CHECKPOINT_SELECTION_BLOCKERS),
        "bf16WinnerDeclaration": phase_blockers(BF16_WINNER_BLOCKERS),
        "dopplerArtifactCompetition": phase_blockers(DOPPLER_ARTIFACT_COMPETITION_BLOCKERS),
        "promotionSubmission": phase_blockers(PROMOTION_SUBMISSION_BLOCKERS),
    }
    core = {
        "schemaVersion": 1,
        "readinessId": "gamma.translation.enes.single-student.readiness.v1",
        "contractId": contract.get("contractId"),
        "status": "ready" if not sorted_blockers else "blocked",
        "identity": {
            "contract": {"path": str(contract_path.relative_to(REPO_ROOT)), "sha256": _sha256_file(contract_path)},
            "contractSchema": {"path": str(schema_path.relative_to(REPO_ROOT)), "sha256": _sha256_file(schema_path)},
            "licenseCatalog": {"path": str(catalog_path.relative_to(REPO_ROOT)), "sha256": _sha256_file(catalog_path)},
            "diagnosticErrorLedger": {"path": str(ledger_path.relative_to(REPO_ROOT)), "sha256": _sha256_file(ledger_path)},
            "diagnosticErrorLedgerSchema": {
                "path": str(ledger_schema_path.relative_to(REPO_ROOT)),
                "sha256": _sha256_file(ledger_schema_path),
            },
            "humanReviewContract": {
                "path": observed_human_path,
                "sha256": observed_human_hash,
            },
            "humanReviewSchema": {
                "path": str(human_review_schema_path.relative_to(REPO_ROOT)),
                "sha256": _sha256_file(human_review_schema_path),
            },
            "populationProcurementContract": {
                "path": observed_procurement_path,
                "sha256": observed_procurement_hash,
            },
            "populationProcurementSchema": {
                "path": str(population_procurement_schema_path.relative_to(REPO_ROOT)),
                "sha256": _sha256_file(population_procurement_schema_path),
            },
        },
        "presentClaim": contract.get("presentClaim", {}).get("status"),
        "populations": populations,
        "populationProcurement": {
            "status": population_procurement_contract.get("status"),
            "identityBound": procurement_contract_bound,
            "blockingConditions": population_procurement_contract.get("blockingConditions", []),
        },
        "licenses": licenses,
        "humanReview": {
            "thresholdStatus": human_status,
            "contractStatus": human_review_contract.get("status"),
            "identityBound": human_contract_bound,
            "role": human_review.get("role"),
        },
        "diagnosticErrorLedger": {
            "role": ledger.get("role"),
            "rows": len(ledger.get("rows", [])),
            "adjudicationStatusTotals": adjudication_totals,
            "inputAssessmentStatusTotals": input_assessment_totals,
            "systemAssessmentStatusTotals": system_assessment_totals,
            "complete": diagnostic_rows_complete,
        },
        "selection": {
            "authority": contract.get("baselineHandoff", {}).get("selectionAuthority"),
            "status": "not_selected",
            "receipt": contract.get("baselineHandoff", {}).get("selectionReceipt"),
        },
        "admission": {
            "matchedTrainingAllowed": not admission_blockers["matchedTraining"],
            "checkpointSelectionAllowed": not admission_blockers["checkpointSelection"],
            "bf16WinnerDeclarationAllowed": not admission_blockers["bf16WinnerDeclaration"],
            "dopplerArtifactCompetitionAllowed": not admission_blockers["dopplerArtifactCompetition"],
            "promotionAllowed": not admission_blockers["promotionSubmission"],
        },
        "admissionBlockers": admission_blockers,
        "blockers": sorted_blockers,
    }
    return {**core, "receiptHash": _hash_receipt_core(core)}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--ledger-schema", type=Path, default=DEFAULT_LEDGER_SCHEMA)
    parser.add_argument("--human-review-contract", type=Path, default=DEFAULT_HUMAN_REVIEW_CONTRACT)
    parser.add_argument("--human-review-schema", type=Path, default=DEFAULT_HUMAN_REVIEW_SCHEMA)
    parser.add_argument(
        "--population-procurement-contract",
        type=Path,
        default=DEFAULT_POPULATION_PROCUREMENT_CONTRACT,
    )
    parser.add_argument(
        "--population-procurement-schema",
        type=Path,
        default=DEFAULT_POPULATION_PROCUREMENT_SCHEMA,
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Return success after emitting a blocked receipt for audit workflows.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    receipt = build_readiness_receipt(
        contract_path=args.contract,
        schema_path=args.schema,
        catalog_path=args.catalog,
        ledger_path=args.ledger,
        ledger_schema_path=args.ledger_schema,
        human_review_contract_path=args.human_review_contract,
        human_review_schema_path=args.human_review_schema,
        population_procurement_contract_path=args.population_procurement_contract,
        population_procurement_schema_path=args.population_procurement_schema,
    )
    output = json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if receipt["status"] == "ready" or args.allow_blocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
