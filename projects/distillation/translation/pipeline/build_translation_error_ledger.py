#!/usr/bin/env python3
"""Build a deterministic row-level translation error ledger.

Automated signals identify rows for review. They are not semantic error labels;
the ledger leaves morphology, idiom, and final category decisions to blinded
qualified reviewers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ERROR_TAXONOMY = [
    "omission",
    "morphology",
    "entity",
    "number",
    "negation",
    "idiom",
    "direction_contract",
]

_NUMBER_RE = re.compile(r"(?<!\w)[+-]?\d+(?:[.,]\d+)*(?:\s?%|\b)")
_WORD_RE = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", re.UNICODE)
_NEGATION_TERMS = {
    "en": {"no", "not", "never", "neither", "nor", "nothing", "nobody", "without"},
    "es": {"no", "nunca", "jamás", "nadie", "nada", "ni", "ningún", "ninguna", "sin"},
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            value = json.loads(text)
            if not isinstance(value, dict):
                raise RuntimeError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    if not rows:
        raise RuntimeError(f"{path}: no rows")
    return rows


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _numbers(text: str) -> list[str]:
    return [match.group(0).replace(" ", "") for match in _NUMBER_RE.finditer(text)]


def _negations(text: str, language: str) -> list[str]:
    words = {word.casefold() for word in _WORD_RE.findall(text)}
    return sorted(words & _NEGATION_TERMS.get(language, set()))


def _entities(text: str) -> list[str]:
    words = _WORD_RE.findall(text)
    entities: list[str] = []
    for index, word in enumerate(words):
        if index == 0:
            continue
        if len(word) > 1 and word[0].isupper() and word.casefold() not in {"i"}:
            entities.append(word)
    return sorted(set(entities), key=str.casefold)


def _signals(reference: str, prediction: str, target_language: str) -> dict[str, Any]:
    reference_numbers = _numbers(reference)
    prediction_numbers = _numbers(prediction)
    reference_negations = _negations(reference, target_language)
    prediction_negations = _negations(prediction, target_language)
    reference_entities = _entities(reference)
    prediction_casefold = prediction.casefold()
    missing_entities = [entity for entity in reference_entities if entity.casefold() not in prediction_casefold]
    length_ratio = len(prediction) / max(1, len(reference))
    return {
        "emptyOutput": not bool(prediction),
        "characterSimilarity": round(SequenceMatcher(None, reference.casefold(), prediction.casefold()).ratio(), 6),
        "lengthRatio": round(length_ratio, 6),
        "possibleOmission": bool(prediction) and length_ratio < 0.67,
        "referenceNumberCount": len(reference_numbers),
        "predictionNumberCount": len(prediction_numbers),
        "numberMismatch": reference_numbers != prediction_numbers,
        "referenceNegationCount": len(reference_negations),
        "predictionNegationCount": len(prediction_negations),
        "negationMismatch": reference_negations != prediction_negations,
        "referenceEntityCount": len(reference_entities),
        "missingReferenceEntityCount": len(missing_entities),
        "entitySignal": bool(missing_entities),
        "requiresHumanMorphologyReview": True,
        "requiresHumanIdiomReview": True,
    }


def _row_identity(direction: str, source: str, reference: str) -> str:
    payload = json.dumps(
        {"direction": direction, "source": source, "reference": reference},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"translation-row-{_sha256_bytes(payload)[:20]}"


def _parse_system_spec(spec: str) -> tuple[str, Path]:
    system_id, separator, raw_path = spec.partition("=")
    if not separator or not system_id.strip() or not raw_path.strip():
        raise RuntimeError(f"invalid --system value {spec!r}; expected system_id=predictions.jsonl")
    return system_id.strip(), Path(raw_path.strip())


def build_error_ledger(
    population_path: Path,
    systems: list[tuple[str, Path]],
    *,
    ledger_id: str,
) -> dict[str, Any]:
    population_rows = _load_jsonl(population_path)
    if len({system_id for system_id, _ in systems}) != len(systems):
        raise RuntimeError("system IDs must be unique")
    if len(systems) < 2:
        raise RuntimeError("at least two systems are required")

    system_rows: dict[str, list[dict[str, Any]]] = {}
    system_metadata: list[dict[str, Any]] = []
    for system_id, path in systems:
        predictions = _load_jsonl(path)
        if len(predictions) != len(population_rows):
            raise RuntimeError(
                f"{system_id}: prediction rows {len(predictions)} != population rows {len(population_rows)}"
            )
        system_rows[system_id] = predictions
        system_metadata.append({
            "systemId": system_id,
            "predictionsPath": str(path),
            "predictionsSha256": _sha256_file(path),
        })

    ledger_rows: list[dict[str, Any]] = []
    for index, population_row in enumerate(population_rows):
        direction = _text(population_row, "pair")
        source = _text(population_row, "source", "query")
        reference = _text(population_row, "target_pos", "pos")
        target_language = _text(population_row, "tgt_lang", "target_lang", "lang")
        if direction not in {"en-es", "es-en"} or not source or not reference:
            raise RuntimeError(f"population row {index}: invalid direction/source/reference")

        row_systems: dict[str, Any] = {}
        for system_id, _ in systems:
            prediction_row = system_rows[system_id][index]
            prediction = _text(prediction_row, "pred", "prediction", "output")
            prediction_direction = _text(prediction_row, "pair")
            prediction_source = _text(prediction_row, "source", "query")
            prediction_reference = _text(prediction_row, "target_pos", "pos", "reference")
            if prediction_direction and prediction_direction != direction:
                raise RuntimeError(f"{system_id} row {index}: direction mismatch")
            if prediction_source and prediction_source != source:
                raise RuntimeError(f"{system_id} row {index}: source mismatch")
            if prediction_reference and prediction_reference != reference:
                raise RuntimeError(f"{system_id} row {index}: reference mismatch")
            row_systems[system_id] = {
                "predictionSha256": _sha256_text(prediction),
                "automatedSignals": _signals(reference, prediction, target_language),
            }

        ledger_rows.append({
            "rowId": _row_identity(direction, source, reference),
            "rowIndex": index,
            "direction": direction,
            "sourceSha256": _sha256_text(source),
            "referenceSha256": _sha256_text(reference),
            "systems": row_systems,
            "adjudication": {
                "status": "pending",
                "inputAssessment": {
                    "status": "pending",
                    "notes": "",
                },
                "systemAssessments": {
                    system_id: {
                        "status": "pending",
                        "errors": [],
                        "notes": "",
                    }
                    for system_id, _ in systems
                },
                "reviewerIds": [],
                "adjudicatorId": None,
                "reviewerSubmissionSha256s": [],
                "adjudicatorSubmissionSha256": None,
                "worklistReceiptHash": None,
                "mappingReceiptHash": None,
                "notes": "",
            },
        })

    return {
        "$schema": "./error-ledger.schema.json",
        "schemaVersion": 1,
        "ledgerId": ledger_id,
        "role": "diagnostic_only",
        "population": {
            "path": str(population_path),
            "sha256": _sha256_file(population_path),
            "rows": len(population_rows),
        },
        "systems": system_metadata,
        "errorTaxonomy": ERROR_TAXONOMY,
        "rows": ledger_rows,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--population", required=True, type=Path)
    parser.add_argument(
        "--system",
        action="append",
        default=[],
        help="Repeat system_id=predictions.jsonl for each system.",
    )
    parser.add_argument("--ledger-id", required=True)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    systems = [_parse_system_spec(spec) for spec in args.system]
    ledger = build_error_ledger(args.population, systems, ledger_id=args.ledger_id)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[translation-error-ledger] rows={len(ledger['rows'])} out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
