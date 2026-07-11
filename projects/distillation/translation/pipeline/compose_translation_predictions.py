#!/usr/bin/env python3
"""Compose aligned directional predictions and produce an offline comparison receipt."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

import sacrebleu


PROJECT_ROOT = Path(__file__).resolve().parents[4]
ALIGNMENT_FIELDS = ("pair", "src_lang", "tgt_lang", "source", "target_pos")


def _safe_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise RuntimeError(f"{path}:{line_number}: expected a JSON object")
            if any(not _safe_text(row.get(field)) for field in ALIGNMENT_FIELDS):
                raise RuntimeError(f"{path}:{line_number}: missing alignment field")
            if not _safe_text(row.get("pred")):
                raise RuntimeError(f"{path}:{line_number}: empty prediction")
            rows.append(row)
    if not rows:
        raise RuntimeError(f"No prediction rows found in {path}")
    return rows


def _alignment_key(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(_safe_text(row.get(field)) for field in ALIGNMENT_FIELDS)


def _compose_rows(
    base_rows: list[dict[str, Any]],
    override_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    overrides: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in override_rows:
        key = _alignment_key(row)
        if key in overrides:
            raise RuntimeError("Duplicate override alignment key")
        overrides[key] = row
    output: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    matched: set[tuple[str, ...]] = set()
    for row in base_rows:
        key = _alignment_key(row)
        override = overrides.get(key)
        if override is None:
            output.append(dict(row))
            counts["base"] += 1
            continue
        selected = dict(row)
        selected["pred"] = _safe_text(override["pred"])
        selected["composition"] = {
            "source": "override",
            "override_selector": override.get("selector"),
        }
        output.append(selected)
        matched.add(key)
        counts["override"] += 1
    missing = set(overrides) - matched
    if missing:
        raise RuntimeError(f"{len(missing)} override rows did not match the base predictions")
    return output, counts


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _metric_payload(predictions: list[str], references: list[str]) -> dict[str, Any]:
    return {
        "bleu": {"available": True, "score": float(sacrebleu.corpus_bleu(predictions, [references]).score)},
        "chrf": {
            "available": True,
            "score": float(sacrebleu.metrics.CHRF().corpus_score(predictions, [references]).score),
        },
        "exact_match": {
            "available": True,
            "score": 100.0
            * sum(prediction == reference for prediction, reference in zip(predictions, references, strict=True))
            / len(predictions),
        },
        "n": len(predictions),
    }


def _model_summary(
    rows: list[dict[str, Any]],
    *,
    label: str,
    model_id: str,
    predictions_path: Path,
    candidate_selection: str,
) -> dict[str, Any]:
    pair_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        pair_rows.setdefault(_safe_text(row["pair"]), []).append(row)
    by_pair: dict[str, Any] = {}
    for pair, values in sorted(pair_rows.items()):
        by_pair[pair] = _metric_payload(
            [_safe_text(row["pred"]) for row in values],
            [_safe_text(row["target_pos"]) for row in values],
        )
    return {
        "model": model_id,
        "label": label,
        "count": len(rows),
        "predictions": {"path": _project_path(predictions_path)},
        "metrics_overall": _metric_payload(
            [_safe_text(row["pred"]) for row in rows],
            [_safe_text(row["target_pos"]) for row in rows],
        ),
        "metrics_by_pair": by_pair,
        "candidate_selection": candidate_selection,
    }


def _direction_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    total = 0
    for pair, metrics in sorted(summary["metrics_by_pair"].items()):
        key = pair.replace("-", "_")
        output[f"{key}_bleu"] = metrics["bleu"]["score"]
        output[f"{key}_chrf"] = metrics["chrf"]["score"]
        output[f"{key}_comet"] = None
        output[f"{key}_sample_count"] = metrics["n"]
        total += int(metrics["n"])
    output["total_sample_count"] = total
    return output


def _delta(student: dict[str, Any], teacher: dict[str, Any]) -> dict[str, float | None]:
    output: dict[str, float | None] = {"comet": None}
    for metric in ("bleu", "chrf"):
        output[metric] = float(student["metrics_overall"][metric]["score"]) - float(
            teacher["metrics_overall"][metric]["score"]
        )
    return output


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--override", required=True)
    parser.add_argument("--teacher-predictions", default="")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--teacher-model-id", default="")
    parser.add_argument("--eval-dataset-path", required=True)
    parser.add_argument("--candidate-selection", default="reference_free_ridge_selector")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    base_path = Path(args.base).expanduser().resolve()
    override_path = Path(args.override).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    base_rows = _load_rows(base_path)
    override_rows = _load_rows(override_path)
    student_rows, composition_counts = _compose_rows(base_rows, override_rows)
    student_predictions_path = out_dir / "student_predictions.jsonl"
    student_summary_path = out_dir / "student_eval_summary.json"
    compare_summary_path = out_dir / "compare_eval_summary.json"
    composition_summary_path = out_dir / "composition_summary.json"
    _write_jsonl(student_predictions_path, student_rows)
    student_summary = _model_summary(
        student_rows,
        label="student",
        model_id=str(args.model_id),
        predictions_path=student_predictions_path,
        candidate_selection=str(args.candidate_selection),
    )
    _write_json(student_summary_path, student_summary)

    teacher_summary = None
    if str(args.teacher_predictions).strip():
        teacher_input_path = Path(args.teacher_predictions).expanduser().resolve()
        teacher_rows = _load_rows(teacher_input_path)
        if [_alignment_key(row) for row in teacher_rows] != [_alignment_key(row) for row in base_rows]:
            raise RuntimeError("Teacher prediction rows do not align with the composed base rows")
        teacher_predictions_path = out_dir / "teacher_predictions.jsonl"
        teacher_summary_path = out_dir / "teacher_eval_summary.json"
        _write_jsonl(teacher_predictions_path, teacher_rows)
        teacher_summary = _model_summary(
            teacher_rows,
            label="teacher",
            model_id=str(args.teacher_model_id or "teacher"),
            predictions_path=teacher_predictions_path,
            candidate_selection="first",
        )
        _write_json(teacher_summary_path, teacher_summary)

    compare_summary = {
        "pairs": str(args.eval_dataset_path),
        "pair_files": [str(args.eval_dataset_path)],
        "eval_samples": len(student_rows),
        "student": student_summary,
        "teacher": teacher_summary,
        "delta": _delta(student_summary, teacher_summary) if teacher_summary else None,
        "direction_metrics": _direction_metrics(student_summary),
        "decode_metadata": {
            "decode_mode": "directional_composed",
            "candidate_selection": str(args.candidate_selection),
            "num_candidates": 2,
        },
        "provenance": {
            "model_id": str(args.model_id),
            "teacher_model_id": str(args.teacher_model_id),
            "eval_dataset_path": str(args.eval_dataset_path),
            "execution_mode": "offline_aligned_prediction_composition",
            "selection_target_access": False,
        },
    }
    _write_json(compare_summary_path, compare_summary)
    composition_summary = {
        "base": {"path": _project_path(base_path), "sha256": _sha256_path(base_path)},
        "override": {"path": _project_path(override_path), "sha256": _sha256_path(override_path)},
        "output": {
            "path": _project_path(student_predictions_path),
            "sha256": _sha256_path(student_predictions_path),
        },
        "rows": len(student_rows),
        "composition_counts": dict(composition_counts),
        "candidate_selection": str(args.candidate_selection),
        "selection_target_access": False,
    }
    _write_json(composition_summary_path, composition_summary)
    overall = student_summary["metrics_overall"]
    delta = compare_summary["delta"] or {}
    print(
        f"[prediction-compose] rows={len(student_rows)} base={composition_counts['base']} "
        f"override={composition_counts['override']} bleu={overall['bleu']['score']:.4f} "
        f"chrf={overall['chrf']['score']:.4f} delta_bleu={delta.get('bleu')} delta_chrf={delta.get('chrf')}"
    )
    print(f"[prediction-compose] out={student_predictions_path}")
    print(f"[prediction-compose] compare={compare_summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
