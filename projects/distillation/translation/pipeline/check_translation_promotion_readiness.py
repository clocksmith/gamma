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

EXPECTED_POPULATION_ROLES = (
    "calibration",
    "checkpoint_selection",
    "seed_confirmation",
    "promotion",
)


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
) -> dict[str, Any]:
    contract = _load_json(contract_path)
    schema = _load_json(schema_path)
    catalog = _load_json(catalog_path)
    ledger = _load_json(ledger_path)
    jsonschema.Draft202012Validator(schema).validate(contract)

    blockers: set[str] = set()
    populations = _population_state(contract, blockers)
    licenses = _license_state(catalog, blockers)

    human_review = contract.get("humanReview", {})
    human_status = human_review.get("thresholdStatus")
    if human_status != "frozen":
        blockers.add("human_review_rubric_and_threshold_absent")

    matched_campaign = contract.get("matchedCampaign", {})
    if not matched_campaign.get("runContract"):
        blockers.add("matched_run_contract_absent")

    for blocker in contract.get("promotionDecision", {}).get("blockers", []):
        blockers.add(str(blocker))

    adjudication_totals: dict[str, int] = {}
    for row in ledger.get("rows", []):
        status = str(row.get("adjudication", {}).get("status", "missing"))
        adjudication_totals[status] = adjudication_totals.get(status, 0) + 1
    if adjudication_totals.get("pending", 0):
        blockers.add("diagnostic_error_ledger_human_adjudication_pending")

    sorted_blockers = sorted(blockers)
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
        },
        "presentClaim": contract.get("presentClaim", {}).get("status"),
        "populations": populations,
        "licenses": licenses,
        "humanReview": {
            "thresholdStatus": human_status,
            "role": human_review.get("role"),
        },
        "diagnosticErrorLedger": {
            "role": ledger.get("role"),
            "rows": len(ledger.get("rows", [])),
            "adjudicationStatusTotals": adjudication_totals,
        },
        "selection": {
            "authority": contract.get("baselineHandoff", {}).get("selectionAuthority"),
            "status": "not_selected",
            "receipt": contract.get("baselineHandoff", {}).get("selectionReceipt"),
        },
        "admission": {
            "matchedTrainingAllowed": not sorted_blockers,
            "checkpointSelectionAllowed": not sorted_blockers,
            "bf16WinnerDeclarationAllowed": False,
            "dopplerArtifactCompetitionAllowed": False,
            "promotionAllowed": False,
        },
        "blockers": sorted_blockers,
    }
    return {**core, "receiptHash": _hash_receipt_core(core)}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
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
    )
    output = json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if receipt["status"] == "ready" or args.allow_blocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
