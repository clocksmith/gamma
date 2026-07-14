#!/usr/bin/env python3
"""Evaluate a blinded EN/ES human-review ledger under the frozen promotion rule."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import jsonschema


REPO_ROOT = Path(__file__).resolve().parents[4]
PROMOTION_ROOT = REPO_ROOT / "projects" / "distillation" / "translation" / "promotion"
DEFAULT_CONTRACT = PROMOTION_ROOT / "human-review-contract.v1.json"
DEFAULT_SCHEMA = PROMOTION_ROOT / "human-review-contract.schema.json"


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


def exact_one_sided_sign_p(candidate_wins: int, comparator_wins: int) -> float:
    """Return P[X >= candidate_wins] for X~Binomial(n, 0.5), excluding ties."""

    if candidate_wins < 0 or comparator_wins < 0:
        raise ValueError("win counts must be non-negative")
    trials = candidate_wins + comparator_wins
    if trials == 0:
        return 1.0
    numerator = sum(math.comb(trials, value) for value in range(candidate_wins, trials + 1))
    return numerator / (2**trials)


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    """Apply Holm-Bonferroni and return monotone adjusted p-values by key."""

    ordered = sorted(p_values.items(), key=lambda entry: (entry[1], entry[0]))
    adjusted: dict[str, float] = {}
    running = 0.0
    family_size = len(ordered)
    for index, (key, value) in enumerate(ordered):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"p-value for {key!r} is outside [0, 1]")
        running = max(running, min(1.0, (family_size - index) * value))
        adjusted[key] = running
    return adjusted


def _canonical_preference(blinded: str, candidate_side: str) -> str:
    if blinded == "tie":
        return "tie"
    if blinded not in {"output_a_better", "output_b_better"}:
        raise ValueError(f"unsupported blinded preference: {blinded!r}")
    winning_side = "output_a" if blinded == "output_a_better" else "output_b"
    return "candidate_better" if winning_side == candidate_side else "comparator_better"


def _canonical_errors(
    adjudication: dict[str, Any],
    candidate_side: str,
) -> tuple[list[str], list[str]]:
    output_a = [str(value) for value in adjudication.get("outputAErrors", [])]
    output_b = [str(value) for value in adjudication.get("outputBErrors", [])]
    if candidate_side == "output_a":
        return output_a, output_b
    return output_b, output_a


def _counts(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def evaluate_review(
    ledger: dict[str, Any],
    contract: dict[str, Any],
    *,
    contract_sha256: str | None = None,
) -> dict[str, Any]:
    blockers: set[str] = set()
    review_contract_id = contract["reviewContractId"]
    if ledger.get("reviewContractId") != review_contract_id:
        blockers.add("review_contract_id_mismatch")

    phase = str(ledger.get("phase", "missing"))
    if phase not in contract["scope"]["blockingPhases"]:
        blockers.add("unsupported_review_phase")

    expected_comparators = list(contract["blockingComparators"])
    comparator_entries = ledger.get("comparators", [])
    observed_comparators = [
        str(entry.get("modelId", ""))
        for entry in comparator_entries
        if isinstance(entry, dict)
    ]
    if sorted(observed_comparators) != sorted(expected_comparators):
        blockers.add("blocking_comparator_set_mismatch")
    for entry in comparator_entries:
        if not isinstance(entry, dict) or not _is_sha256(entry.get("artifactSha256")):
            blockers.add("comparator_artifact_identity_missing")

    candidate = ledger.get("candidate", {})
    if not isinstance(candidate, dict) or not _is_sha256(candidate.get("artifactSha256")):
        blockers.add("candidate_artifact_identity_missing")

    population = ledger.get("population", {})
    if not isinstance(population, dict) or not _is_sha256(population.get("populationSha256")):
        blockers.add("population_identity_missing")
    expected_distinct_items = population.get("expectedDistinctItems") if isinstance(population, dict) else None
    if not isinstance(expected_distinct_items, int) or expected_distinct_items < 1:
        blockers.add("population_expected_item_count_missing")

    preference_counts: dict[str, Counter[str]] = {
        comparator: Counter() for comparator in expected_comparators
    }
    stratum_counts: dict[str, dict[str, Counter[str]]] = {
        comparator: defaultdict(Counter) for comparator in expected_comparators
    }
    candidate_errors: dict[str, Counter[str]] = {
        comparator: Counter() for comparator in expected_comparators
    }
    comparator_errors: dict[str, Counter[str]] = {
        comparator: Counter() for comparator in expected_comparators
    }

    unit_ids: set[str] = set()
    item_metadata: dict[str, tuple[str, str]] = {}
    item_candidate_outputs: dict[str, str] = {}
    item_candidate_errors: dict[str, tuple[str, ...]] = {}
    observed_pairs: set[tuple[str, str]] = set()
    complete_pairs = 0
    rows = ledger.get("rows", [])
    if not isinstance(rows, list):
        rows = []
        blockers.add("review_rows_not_an_array")

    allowed_directions = set(contract["scope"]["directions"])
    allowed_domains = set(contract["scope"]["domains"])
    allowed_errors = set(contract["rubric"]["criticalErrorClasses"])
    blinded_labels = set(contract["rubric"]["blindedPreferenceLabels"])

    for index, row in enumerate(rows):
        row_blocker = f"row_{index:06d}"
        if not isinstance(row, dict):
            blockers.add(f"{row_blocker}_not_an_object")
            continue
        unit_id = str(row.get("unitId", ""))
        item_id = str(row.get("itemId", ""))
        comparator_id = str(row.get("comparatorId", ""))
        direction = str(row.get("direction", ""))
        domain = str(row.get("domain", ""))
        candidate_side = str(row.get("candidateSide", ""))
        candidate_output_sha256 = row.get("candidateOutputSha256")
        comparator_output_sha256 = row.get("comparatorOutputSha256")

        if not unit_id or unit_id in unit_ids:
            blockers.add("duplicate_or_missing_unit_id")
        unit_ids.add(unit_id)
        if not item_id:
            blockers.add(f"{row_blocker}_item_id_missing")
        previous_metadata = item_metadata.setdefault(item_id, (direction, domain))
        if previous_metadata != (direction, domain):
            blockers.add("item_metadata_inconsistent_across_comparators")
        pair = (item_id, comparator_id)
        if pair in observed_pairs:
            blockers.add("duplicate_item_comparator_pair")
        observed_pairs.add(pair)
        if comparator_id not in expected_comparators:
            blockers.add("unexpected_comparator_in_review_rows")
        if direction not in allowed_directions:
            blockers.add("unexpected_direction_in_review_rows")
        if domain not in allowed_domains:
            blockers.add("unexpected_domain_in_review_rows")
        if candidate_side not in {"output_a", "output_b"}:
            blockers.add(f"{row_blocker}_candidate_side_missing")
        if not _is_sha256(candidate_output_sha256) or not _is_sha256(comparator_output_sha256):
            blockers.add(f"{row_blocker}_output_identity_missing")
        elif item_candidate_outputs.setdefault(item_id, candidate_output_sha256) != candidate_output_sha256:
            blockers.add("candidate_output_identity_inconsistent_across_comparators")
        if not _is_sha256(row.get("blindingReceiptSha256")):
            blockers.add(f"{row_blocker}_blinding_receipt_missing")
        if not _is_sha256(row.get("mappingReceiptSha256")):
            blockers.add(f"{row_blocker}_mapping_receipt_missing")

        reviewers = row.get("reviewers", [])
        reviewer_ids: list[str] = []
        if not isinstance(reviewers, list) or len(reviewers) != contract["assignment"]["independentReviewersPerUnit"]:
            blockers.add(f"{row_blocker}_reviewer_count_invalid")
            reviewers = []
        for reviewer in reviewers:
            if not isinstance(reviewer, dict):
                blockers.add(f"{row_blocker}_reviewer_record_invalid")
                continue
            reviewer_id = str(reviewer.get("reviewerId", ""))
            reviewer_ids.append(reviewer_id)
            if not reviewer_id or not _is_sha256(reviewer.get("qualificationReceiptSha256")):
                blockers.add(f"{row_blocker}_reviewer_qualification_missing")
            if reviewer.get("preference") not in blinded_labels:
                blockers.add(f"{row_blocker}_reviewer_preference_invalid")
            for field in ("outputAErrors", "outputBErrors"):
                values = reviewer.get(field, [])
                if not isinstance(values, list) or len(values) != len(set(values)) or not set(values).issubset(allowed_errors):
                    blockers.add(f"{row_blocker}_reviewer_errors_invalid")
        if len(set(reviewer_ids)) != len(reviewer_ids):
            blockers.add(f"{row_blocker}_reviewers_not_independent")

        adjudication = row.get("adjudication", {})
        if not isinstance(adjudication, dict) or adjudication.get("status") != "complete":
            blockers.add(f"{row_blocker}_adjudication_incomplete")
            continue
        adjudicator_id = str(adjudication.get("adjudicatorId", ""))
        if (
            not adjudicator_id
            or adjudicator_id in reviewer_ids
            or not _is_sha256(adjudication.get("qualificationReceiptSha256"))
        ):
            blockers.add(f"{row_blocker}_adjudicator_not_distinct_or_unqualified")
        blinded_preference = adjudication.get("preference")
        if blinded_preference not in blinded_labels:
            blockers.add(f"{row_blocker}_adjudicated_preference_invalid")
            continue
        error_values_valid = True
        for field in ("outputAErrors", "outputBErrors"):
            values = adjudication.get(field, [])
            if not isinstance(values, list) or len(values) != len(set(values)) or not set(values).issubset(allowed_errors):
                blockers.add(f"{row_blocker}_adjudicated_errors_invalid")
                error_values_valid = False
        if (
            comparator_id not in expected_comparators
            or direction not in allowed_directions
            or domain not in allowed_domains
            or candidate_side not in {"output_a", "output_b"}
            or not error_values_valid
        ):
            continue

        canonical = _canonical_preference(str(blinded_preference), candidate_side)
        preference_counts[comparator_id][canonical] += 1
        for stratum in (
            f"direction:{direction}",
            f"domain:{domain}",
            f"cell:{direction}:{domain}",
        ):
            stratum_counts[comparator_id][stratum][canonical] += 1
        row_candidate_errors, row_comparator_errors = _canonical_errors(adjudication, candidate_side)
        canonical_candidate_errors = tuple(sorted(row_candidate_errors))
        if item_candidate_errors.setdefault(item_id, canonical_candidate_errors) != canonical_candidate_errors:
            blockers.add("candidate_error_labels_inconsistent_across_comparators")
        candidate_errors[comparator_id].update(row_candidate_errors)
        comparator_errors[comparator_id].update(row_comparator_errors)
        complete_pairs += 1

    item_ids = set(item_metadata)
    expected_pairs = {
        (item_id, comparator)
        for item_id in item_ids
        for comparator in expected_comparators
    }
    if observed_pairs != expected_pairs:
        blockers.add("item_comparator_matrix_incomplete")
    if expected_distinct_items != len(item_ids):
        blockers.add("population_expected_item_count_mismatch")

    cell_counts = Counter(item_metadata.values())
    minimum = None
    if phase in contract["populationMinimums"]:
        minimum = contract["populationMinimums"][phase]["distinctItemsPerDirectionDomainCell"]
        for direction in contract["scope"]["directions"]:
            for domain in contract["scope"]["domains"]:
                if cell_counts[(direction, domain)] < minimum:
                    blockers.add(f"population_cell_below_minimum:{direction}:{domain}")

    raw_p_values = {
        comparator: exact_one_sided_sign_p(
            preference_counts[comparator]["candidate_better"],
            preference_counts[comparator]["comparator_better"],
        )
        for comparator in expected_comparators
    }
    adjusted_p_values = holm_adjust(raw_p_values)
    alpha = float(contract["statisticalDecision"]["alpha"])
    comparison_results: dict[str, Any] = {}
    for comparator in expected_comparators:
        counts = preference_counts[comparator]
        overall_pass = (
            counts["candidate_better"] > counts["comparator_better"]
            and adjusted_p_values[comparator] <= alpha
        )
        if not overall_pass:
            blockers.add(f"overall_human_preference_failed:{comparator}")
        comparison_results[comparator] = {
            "candidateBetter": counts["candidate_better"],
            "ties": counts["tie"],
            "comparatorBetter": counts["comparator_better"],
            "nonTies": counts["candidate_better"] + counts["comparator_better"],
            "rawExactOneSidedP": raw_p_values[comparator],
            "holmAdjustedP": adjusted_p_values[comparator],
            "passed": overall_pass,
        }

    stratum_results: dict[str, Any] = {}
    for comparator in expected_comparators:
        comparator_strata: dict[str, Any] = {}
        for stratum, counts in sorted(stratum_counts[comparator].items()):
            passed = counts["candidate_better"] >= counts["comparator_better"]
            if not passed:
                blockers.add(f"human_preference_stratum_regression:{comparator}:{stratum}")
            comparator_strata[stratum] = {
                "candidateBetter": counts["candidate_better"],
                "ties": counts["tie"],
                "comparatorBetter": counts["comparator_better"],
                "passed": passed,
            }
        stratum_results[comparator] = comparator_strata

    critical_error_results: dict[str, Any] = {}
    direction_contract_total = 0
    for comparator in expected_comparators:
        by_class: dict[str, Any] = {}
        for error_class in contract["rubric"]["criticalErrorClasses"]:
            candidate_count = candidate_errors[comparator][error_class]
            comparator_count = comparator_errors[comparator][error_class]
            passed = candidate_count <= comparator_count
            if not passed:
                blockers.add(f"critical_error_regression:{comparator}:{error_class}")
            by_class[error_class] = {
                "candidate": candidate_count,
                "comparator": comparator_count,
                "passed": passed,
            }
        direction_contract_total += candidate_errors[comparator]["direction_contract"]
        critical_error_results[comparator] = by_class
    if direction_contract_total:
        blockers.add("candidate_direction_contract_error_present")

    sorted_blockers = sorted(blockers)
    core = {
        "schemaVersion": 1,
        "reviewId": ledger.get("reviewId"),
        "reviewContractId": review_contract_id,
        "reviewContractSha256": contract_sha256,
        "phase": phase,
        "status": "passed" if not sorted_blockers else "failed",
        "candidate": candidate,
        "comparators": comparator_entries,
        "population": {
            "populationId": population.get("populationId") if isinstance(population, dict) else None,
            "populationSha256": population.get("populationSha256") if isinstance(population, dict) else None,
            "expectedDistinctItems": expected_distinct_items,
            "observedDistinctItems": len(item_ids),
            "minimumDistinctItemsPerDirectionDomainCell": minimum,
            "observedCellCounts": [
                {"direction": direction, "domain": domain, "count": cell_counts[(direction, domain)]}
                for direction in contract["scope"]["directions"]
                for domain in contract["scope"]["domains"]
            ],
        },
        "completeness": {
            "expectedItemComparatorPairs": len(expected_pairs),
            "observedItemComparatorPairs": len(observed_pairs),
            "completeAdjudicatedPairs": complete_pairs,
        },
        "overallComparisons": comparison_results,
        "stratumGuardrails": stratum_results,
        "criticalErrorGuardrails": critical_error_results,
        "candidateDirectionContractErrorCountAcrossComparisons": direction_contract_total,
        "blockers": sorted_blockers,
    }
    return {**core, "receiptHash": _hash_receipt_core(core)}


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    contract = _load_json(args.contract)
    schema = _load_json(args.schema)
    jsonschema.Draft202012Validator(schema).validate(contract)
    ledger = _load_json(args.ledger)
    receipt = evaluate_review(
        ledger,
        contract,
        contract_sha256=_sha256_file(args.contract),
    )
    output = json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
