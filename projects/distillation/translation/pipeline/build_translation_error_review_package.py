#!/usr/bin/env python3
"""Build a blinded review worklist and separately custodied system mapping."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: expected a JSON object")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise RuntimeError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    return rows


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _hash_receipt_core(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _blind_order(key: bytes, worklist_id: str, row_id: str, system_ids: list[str]) -> list[str]:
    def order_key(system_id: str) -> tuple[bytes, str]:
        payload = f"{worklist_id}\0{row_id}\0{system_id}".encode("utf-8")
        return hmac.new(key, payload, hashlib.sha256).digest(), system_id

    return sorted(system_ids, key=order_key)


def build_review_package(
    ledger_path: Path,
    blinding_key: bytes,
    *,
    worklist_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if len(blinding_key) < 32:
        raise RuntimeError("blinding key must contain at least 32 bytes")
    if not worklist_id.strip():
        raise RuntimeError("worklist ID must not be empty")

    ledger = _load_json(ledger_path)
    population_metadata = ledger.get("population", {})
    population_path = Path(str(population_metadata.get("path", "")))
    if _sha256_file(population_path) != population_metadata.get("sha256"):
        raise RuntimeError("population bytes do not match the diagnostic ledger")
    population_rows = _load_jsonl(population_path)

    systems = ledger.get("systems", [])
    system_ids = [str(entry.get("systemId", "")) for entry in systems]
    if len(system_ids) < 2 or len(set(system_ids)) != len(system_ids):
        raise RuntimeError("diagnostic ledger system identities are missing or duplicated")
    predictions: dict[str, list[dict[str, Any]]] = {}
    for entry in systems:
        system_id = str(entry["systemId"])
        predictions_path = Path(str(entry["predictionsPath"]))
        if _sha256_file(predictions_path) != entry.get("predictionsSha256"):
            raise RuntimeError(f"{system_id}: prediction bytes do not match the diagnostic ledger")
        predictions[system_id] = _load_jsonl(predictions_path)

    ledger_rows = ledger.get("rows", [])
    if len(population_rows) != len(ledger_rows):
        raise RuntimeError("population and ledger row counts differ")
    for system_id, rows in predictions.items():
        if len(rows) != len(ledger_rows):
            raise RuntimeError(f"{system_id}: prediction and ledger row counts differ")

    worklist_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []
    for index, ledger_row in enumerate(ledger_rows):
        population_row = population_rows[index]
        row_id = str(ledger_row["rowId"])
        direction = _text(population_row, "pair")
        source = _text(population_row, "source", "query")
        reference = _text(population_row, "target_pos", "pos")
        if direction != ledger_row.get("direction"):
            raise RuntimeError(f"row {index}: direction does not match the diagnostic ledger")
        if _sha256_text(source) != ledger_row.get("sourceSha256"):
            raise RuntimeError(f"row {index}: source does not match the diagnostic ledger")
        if _sha256_text(reference) != ledger_row.get("referenceSha256"):
            raise RuntimeError(f"row {index}: reference does not match the diagnostic ledger")

        ordered_systems = _blind_order(blinding_key, worklist_id, row_id, system_ids)
        visible_outputs: list[dict[str, Any]] = []
        mapping_outputs: list[dict[str, str]] = []
        for output_index, system_id in enumerate(ordered_systems, start=1):
            output_label = f"output_{output_index}"
            prediction = _text(predictions[system_id][index], "pred", "prediction", "output")
            expected_prediction_hash = ledger_row["systems"][system_id]["predictionSha256"]
            if _sha256_text(prediction) != expected_prediction_hash:
                raise RuntimeError(f"{system_id} row {index}: prediction does not match the ledger")
            visible_outputs.append(
                {
                    "outputLabel": output_label,
                    "prediction": prediction,
                    "predictionSha256": expected_prediction_hash,
                }
            )
            mapping_outputs.append(
                {
                    "outputLabel": output_label,
                    "systemId": system_id,
                    "predictionSha256": expected_prediction_hash,
                }
            )
        worklist_rows.append(
            {
                "rowId": row_id,
                "rowIndex": index,
                "direction": direction,
                "source": source,
                "sourceSha256": ledger_row["sourceSha256"],
                "reference": reference,
                "referenceSha256": ledger_row["referenceSha256"],
                "outputs": visible_outputs,
            }
        )
        mapping_rows.append({"rowId": row_id, "outputs": mapping_outputs})

    key_commitment = _sha256_bytes(blinding_key)
    worklist_core = {
        "schemaVersion": 1,
        "worklistId": worklist_id,
        "role": "diagnostic_only",
        "sourceLedgerSha256": _sha256_file(ledger_path),
        "populationSha256": population_metadata.get("sha256"),
        "systemCount": len(system_ids),
        "rowCount": len(worklist_rows),
        "blinding": {
            "method": "hmac_sha256_ordering",
            "keyCommitmentSha256": key_commitment,
            "systemMapping": "separately_custodied",
        },
        "instructions": {
            "inputAssessment": [
                "usable",
                "source_issue",
                "reference_issue",
                "source_and_reference_issue",
            ],
            "errorClasses": ledger.get("errorTaxonomy"),
            "severities": ["minor", "major", "critical"],
            "rule": "Assess every output independently. Automated signals are intentionally hidden. Do not infer system identity. Record evidence for every error.",
        },
        "rows": worklist_rows,
    }
    worklist = {**worklist_core, "receiptHash": _hash_receipt_core(worklist_core)}

    mapping_core = {
        "schemaVersion": 1,
        "mappingId": f"{worklist_id}.mapping",
        "worklistId": worklist_id,
        "worklistReceiptHash": worklist["receiptHash"],
        "sourceLedgerId": ledger.get("ledgerId"),
        "sourceLedgerPath": str(ledger_path),
        "sourceLedgerSha256": _sha256_file(ledger_path),
        "keyCommitmentSha256": key_commitment,
        "rows": mapping_rows,
    }
    mapping = {**mapping_core, "receiptHash": _hash_receipt_core(mapping_core)}
    return worklist, mapping


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--blinding-key", required=True, type=Path)
    parser.add_argument("--worklist-id", required=True)
    parser.add_argument("--out-worklist", required=True, type=Path)
    parser.add_argument("--out-mapping", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.out_worklist.resolve() == args.out_mapping.resolve():
        raise RuntimeError("reviewer worklist and custodian mapping paths must differ")
    worklist, mapping = build_review_package(
        args.ledger,
        args.blinding_key.read_bytes(),
        worklist_id=args.worklist_id,
    )
    args.out_worklist.parent.mkdir(parents=True, exist_ok=True)
    args.out_mapping.parent.mkdir(parents=True, exist_ok=True)
    args.out_worklist.write_text(
        json.dumps(worklist, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.out_mapping.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(args.out_mapping, 0o600)
    print(
        f"[translation-error-review] rows={worklist['rowCount']} "
        f"worklist={args.out_worklist} mapping={args.out_mapping}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
