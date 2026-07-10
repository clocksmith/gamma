#!/usr/bin/env python3
"""Verify the Savant 1B versus TranslateGemma 4B paired claim artifacts."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

import sacrebleu


REPO_ROOT = Path(__file__).resolve().parents[5]
RUN_DIR = Path(__file__).resolve().parent
EVAL_PATH = (
    REPO_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl"
)
TRAIN_PATH = (
    REPO_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "runs"
    / "translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1"
    / "inputs"
    / "train_pairs.rows1600.normalized.jsonl"
)
PROOF_DIR = RUN_DIR / "indomain_clean_128"
SUMMARY_PATH = PROOF_DIR / "compare_eval_summary.json"
STUDENT_PATH = PROOF_DIR / "student_predictions.jsonl"
TEACHER_PATH = PROOF_DIR / "teacher_predictions.jsonl"
EXPECTED_HASHES = {
    EVAL_PATH: "0bef72ecdc09eb0d65564312f76c0333d756d5a4978608b4f69a6b5ad4857e39",
    TRAIN_PATH: "2cfea3f81a44cb469d9229862a98763c7e31a78d1ae78a3b90fc54fd8c543e92",
    SUMMARY_PATH: "c7dbdfb6b780a4a35bde28a048ca49abbcd8d90d8a4be81e6d356ecd82b4676a",
    STUDENT_PATH: "5ccff143480f3a23e5ad6ad5036c914b5de57c070a1a65039d079ea8da859cf9",
    TEACHER_PATH: "dc0e61a09cb41564aa0ff05b0daafa531e95025707d5ae109ee0c7c50ce405b7",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.casefold()))


def _metrics(rows: list[dict[str, Any]]) -> tuple[float, float]:
    predictions = [str(row["pred"]) for row in rows]
    references = [str(row["target_pos"]) for row in rows]
    return (
        float(sacrebleu.corpus_bleu(predictions, [references]).score),
        float(sacrebleu.corpus_chrf(predictions, [references]).score),
    )


def _assert_close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9):
        raise RuntimeError(f"{label} mismatch: actual={actual} expected={expected}")


def main() -> int:
    for path, expected in EXPECTED_HASHES.items():
        actual = _sha256(path)
        if actual != expected:
            raise RuntimeError(f"SHA-256 mismatch for {path}: {actual}")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    eval_rows = _load_jsonl(EVAL_PATH)
    train_rows = _load_jsonl(TRAIN_PATH)
    model_rows = {
        "student": _load_jsonl(STUDENT_PATH),
        "teacher": _load_jsonl(TEACHER_PATH),
    }
    if len(eval_rows) != 128 or any(len(rows) != 128 for rows in model_rows.values()):
        raise RuntimeError("Expected 128 ordered evaluation rows for both models.")

    for label, rows in model_rows.items():
        for index, (prediction, reference) in enumerate(zip(rows, eval_rows, strict=True)):
            identity = ("src_lang", "tgt_lang", "source", "target_pos")
            if tuple(prediction[key] for key in identity) != tuple(reference[key] for key in identity):
                raise RuntimeError(f"{label} row order mismatch at index {index}")
            if not str(prediction.get("pred", "")).strip():
                raise RuntimeError(f"{label} has an empty prediction at index {index}")

    train_sources = {(row["src_lang"], _normalize(row["query"])) for row in train_rows}
    eval_sources = {(row["src_lang"], _normalize(row["query"])) for row in eval_rows}
    train_pairs = {
        (row["src_lang"], row["tgt_lang"], _normalize(row["query"]), _normalize(row["pos"]))
        for row in train_rows
    }
    eval_pairs = {
        (row["src_lang"], row["tgt_lang"], _normalize(row["query"]), _normalize(row["pos"]))
        for row in eval_rows
    }
    source_overlap = len(train_sources & eval_sources)
    pair_overlap = len(train_pairs & eval_pairs)
    if source_overlap or pair_overlap:
        raise RuntimeError(
            f"Holdout overlap detected: sources={source_overlap} pairs={pair_overlap}"
        )

    results: dict[str, dict[str, tuple[float, float]]] = {}
    for label, rows in model_rows.items():
        results[label] = {"overall": _metrics(rows)}
        for direction in ("en-es", "es-en"):
            results[label][direction] = _metrics(
                [row for row in rows if row["pair"] == direction]
            )

        expected_model = summary[label]
        _assert_close(
            results[label]["overall"][0],
            float(expected_model["metrics_overall"]["bleu"]["score"]),
            f"{label} overall BLEU",
        )
        _assert_close(
            results[label]["overall"][1],
            float(expected_model["metrics_overall"]["chrf"]["score"]),
            f"{label} overall chrF",
        )
        for direction in ("en-es", "es-en"):
            _assert_close(
                results[label][direction][0],
                float(expected_model["metrics_by_pair"][direction]["bleu"]["score"]),
                f"{label} {direction} BLEU",
            )
            _assert_close(
                results[label][direction][1],
                float(expected_model["metrics_by_pair"][direction]["chrf"]["score"]),
                f"{label} {direction} chrF",
            )

    print("PASS: Savant Gemma 3 1B beats TranslateGemma 4B on this holdout")
    print(f"rows=128 source_overlap={source_overlap} pair_overlap={pair_overlap}")
    print("scope      student BLEU  teacher BLEU  student chrF  teacher chrF")
    for scope in ("overall", "en-es", "es-en"):
        student_bleu, student_chrf = results["student"][scope]
        teacher_bleu, teacher_chrf = results["teacher"][scope]
        if student_bleu <= teacher_bleu or student_chrf <= teacher_chrf:
            raise RuntimeError(f"Student does not win both metrics for {scope}.")
        print(
            f"{scope:<10} {student_bleu:>12.4f} {teacher_bleu:>13.4f} "
            f"{student_chrf:>13.4f} {teacher_chrf:>13.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
