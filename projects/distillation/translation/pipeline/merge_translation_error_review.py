#!/usr/bin/env python3
"""Merge two blinded reviews and a distinct adjudication into the diagnostic ledger."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ALLOWED_INPUT_STATUSES = {
    "usable",
    "source_issue",
    "reference_issue",
    "source_and_reference_issue",
}
ALLOWED_ERROR_CLASSES = {
    "omission",
    "morphology",
    "entity",
    "number",
    "negation",
    "idiom",
    "direction_contract",
}
ALLOWED_SEVERITIES = {"minor", "major", "critical"}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: expected a JSON object")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_receipt_core(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_receipt(value: dict[str, Any], *, label: str) -> None:
    observed = value.get("receiptHash")
    core = {key: entry for key, entry in value.items() if key != "receiptHash"}
    expected = _hash_receipt_core(core)
    if observed != expected:
        raise RuntimeError(f"{label}: receipt hash mismatch")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _validate_errors(errors: Any, *, label: str) -> list[dict[str, str]]:
    if not isinstance(errors, list):
        raise RuntimeError(f"{label}: errors must be an array")
    result: list[dict[str, str]] = []
    observed_classes: set[str] = set()
    for error in errors:
        if not isinstance(error, dict):
            raise RuntimeError(f"{label}: error must be an object")
        error_class = str(error.get("class", ""))
        severity = str(error.get("severity", ""))
        evidence = str(error.get("evidence", "")).strip()
        if error_class not in ALLOWED_ERROR_CLASSES:
            raise RuntimeError(f"{label}: unsupported error class {error_class!r}")
        if error_class in observed_classes:
            raise RuntimeError(f"{label}: duplicate error class {error_class!r}")
        if severity not in ALLOWED_SEVERITIES:
            raise RuntimeError(f"{label}: unsupported severity {severity!r}")
        if not evidence:
            raise RuntimeError(f"{label}: evidence is required")
        observed_classes.add(error_class)
        result.append({"class": error_class, "severity": severity, "evidence": evidence})
    return sorted(result, key=lambda entry: entry["class"])


def _validate_submission(
    submission: dict[str, Any],
    *,
    role: str,
    worklist: dict[str, Any],
) -> tuple[str, dict[str, dict[str, Any]]]:
    _verify_receipt(submission, label=f"{role} submission")
    if submission.get("role") != role:
        raise RuntimeError(f"expected a {role} submission")
    if submission.get("worklistId") != worklist.get("worklistId"):
        raise RuntimeError(f"{role} submission: worklist ID mismatch")
    if submission.get("worklistReceiptHash") != worklist.get("receiptHash"):
        raise RuntimeError(f"{role} submission: worklist receipt mismatch")
    actor_id = str(submission.get("actorId", "")).strip()
    if not actor_id or not _is_sha256(submission.get("qualificationReceiptSha256")):
        raise RuntimeError(f"{role} submission: actor identity or qualification receipt missing")

    expected_rows = {
        str(row["rowId"]): {str(output["outputLabel"]) for output in row["outputs"]}
        for row in worklist.get("rows", [])
    }
    observed_rows: dict[str, dict[str, Any]] = {}
    rows = submission.get("rows", [])
    if not isinstance(rows, list):
        raise RuntimeError(f"{role} submission: rows must be an array")
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError(f"{role} submission: row must be an object")
        row_id = str(row.get("rowId", ""))
        if row_id in observed_rows:
            raise RuntimeError(f"{role} submission: duplicate row {row_id!r}")
        if row_id not in expected_rows:
            raise RuntimeError(f"{role} submission: unexpected row {row_id!r}")
        input_assessment = row.get("inputAssessment", {})
        if not isinstance(input_assessment, dict):
            raise RuntimeError(f"{role} submission {row_id}: input assessment must be an object")
        input_status = str(input_assessment.get("status", ""))
        if input_status not in ALLOWED_INPUT_STATUSES:
            raise RuntimeError(f"{role} submission {row_id}: invalid input assessment")
        output_records = row.get("outputs", [])
        if not isinstance(output_records, list):
            raise RuntimeError(f"{role} submission {row_id}: outputs must be an array")
        outputs: dict[str, dict[str, Any]] = {}
        for output in output_records:
            if not isinstance(output, dict):
                raise RuntimeError(f"{role} submission {row_id}: output must be an object")
            output_label = str(output.get("outputLabel", ""))
            if output_label in outputs:
                raise RuntimeError(f"{role} submission {row_id}: duplicate output {output_label!r}")
            outputs[output_label] = {
                "errors": _validate_errors(
                    output.get("errors", []),
                    label=f"{role} submission {row_id} {output_label}",
                ),
                "notes": str(output.get("notes", "")),
            }
        if set(outputs) != expected_rows[row_id]:
            raise RuntimeError(f"{role} submission {row_id}: output matrix is incomplete")
        observed_rows[row_id] = {
            "inputAssessment": {
                "status": input_status,
                "notes": str(input_assessment.get("notes", "")),
            },
            "outputs": outputs,
            "notes": str(row.get("notes", "")),
        }
    if set(observed_rows) != set(expected_rows):
        raise RuntimeError(f"{role} submission: row matrix is incomplete")
    return actor_id, observed_rows


def merge_reviews(
    ledger_path: Path,
    worklist_path: Path,
    mapping_path: Path,
    reviewer_paths: list[Path],
    adjudicator_path: Path,
) -> dict[str, Any]:
    if len(reviewer_paths) != 2:
        raise RuntimeError("exactly two reviewer submissions are required")
    ledger = _load_json(ledger_path)
    worklist = _load_json(worklist_path)
    mapping = _load_json(mapping_path)
    _verify_receipt(worklist, label="review worklist")
    _verify_receipt(mapping, label="custodian mapping")
    if mapping.get("worklistReceiptHash") != worklist.get("receiptHash"):
        raise RuntimeError("custodian mapping does not bind the review worklist")
    if mapping.get("sourceLedgerSha256") != _sha256_file(ledger_path):
        raise RuntimeError("custodian mapping does not bind the diagnostic ledger")

    reviewer_submissions = [_load_json(path) for path in reviewer_paths]
    reviewer_results = [
        _validate_submission(submission, role="reviewer", worklist=worklist)
        for submission in reviewer_submissions
    ]
    reviewer_ids = [entry[0] for entry in reviewer_results]
    if len(set(reviewer_ids)) != 2:
        raise RuntimeError("reviewers must be distinct")
    reviewer_file_hashes = sorted(_sha256_file(path) for path in reviewer_paths)

    adjudicator_submission = _load_json(adjudicator_path)
    adjudicator_id, adjudicated_rows = _validate_submission(
        adjudicator_submission,
        role="adjudicator",
        worklist=worklist,
    )
    if adjudicator_id in reviewer_ids:
        raise RuntimeError("adjudicator must be distinct from both reviewers")
    if sorted(adjudicator_submission.get("reviewerSubmissionSha256s", [])) != reviewer_file_hashes:
        raise RuntimeError("adjudicator submission does not bind both reviewer submissions")

    mapping_by_row: dict[str, dict[str, str]] = {}
    for row in mapping.get("rows", []):
        row_id = str(row.get("rowId", ""))
        if row_id in mapping_by_row:
            raise RuntimeError(f"custodian mapping duplicates row {row_id!r}")
        mapping_by_row[row_id] = {
            str(output["outputLabel"]): str(output["systemId"])
            for output in row.get("outputs", [])
        }

    merged = copy.deepcopy(ledger)
    expected_systems = {str(entry["systemId"]) for entry in merged.get("systems", [])}
    adjudicator_file_hash = _sha256_file(adjudicator_path)
    mapping_receipt_hash = str(mapping["receiptHash"])
    worklist_receipt_hash = str(worklist["receiptHash"])
    for row in merged.get("rows", []):
        row_id = str(row["rowId"])
        if row_id not in adjudicated_rows or row_id not in mapping_by_row:
            raise RuntimeError(f"merged review is missing row {row_id!r}")
        output_to_system = mapping_by_row[row_id]
        if set(output_to_system.values()) != expected_systems:
            raise RuntimeError(f"custodian mapping {row_id}: system matrix is incomplete")
        final = adjudicated_rows[row_id]
        system_assessments: dict[str, Any] = {}
        for output_label, system_id in output_to_system.items():
            assessment = final["outputs"][output_label]
            system_assessments[system_id] = {
                "status": "complete",
                "errors": assessment["errors"],
                "notes": assessment["notes"],
            }
        row["adjudication"] = {
            "status": "complete",
            "inputAssessment": final["inputAssessment"],
            "systemAssessments": system_assessments,
            "reviewerIds": reviewer_ids,
            "adjudicatorId": adjudicator_id,
            "reviewerSubmissionSha256s": reviewer_file_hashes,
            "adjudicatorSubmissionSha256": adjudicator_file_hash,
            "worklistReceiptHash": worklist_receipt_hash,
            "mappingReceiptHash": mapping_receipt_hash,
            "notes": final["notes"],
        }
    return merged


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--worklist", required=True, type=Path)
    parser.add_argument("--mapping", required=True, type=Path)
    parser.add_argument("--reviewer", required=True, action="append", type=Path)
    parser.add_argument("--adjudicator", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    merged = merge_reviews(
        args.ledger,
        args.worklist,
        args.mapping,
        args.reviewer,
        args.adjudicator,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[translation-error-review-merge] rows={len(merged['rows'])} out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
