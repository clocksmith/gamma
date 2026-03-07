#!/usr/bin/env python3
"""Build a compact index of translation distillation runs and eval results."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


DATASET_SPECS: tuple[dict[str, Any], ...] = (
    {
        "label": "external_wmt13_en_es_translation_benchmark_128",
        "description": "External WMT13 EN-ES translation benchmark (128 rows)",
        "aliases": (
            "eval2_external",
            "translate_distill_pairs.eval2_wmt13_enes_128.jsonl",
        ),
    },
    {
        "label": "indomain_clean_merged_en_es_translation_benchmark_128",
        "description": "In-domain clean merged EN-ES translation benchmark (128 rows)",
        "aliases": (
            "eval3_indomain_clean",
            "translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl",
        ),
    },
)

STAGE_TOKEN_RE = re.compile(r"^(stage[_-]?)(a|b)(\d+)(k)?$", re.IGNORECASE)
MODEL_CHECKPOINT_RE = re.compile(r"/(stage_[ab])/checkpoint-(\d+)(?:/|$)")


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _fmt_float(value: Any) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.4f}"
    except Exception:
        return ""


def _fmt_int(value: Any) -> str:
    if value is None:
        return ""
    try:
        return str(int(value))
    except Exception:
        return ""


def _fmt_ts(value: Any) -> str:
    try:
        return dt.datetime.fromtimestamp(float(value), tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return ""


def _safe_rel(path: Path, start: Path) -> str:
    try:
        return str(path.relative_to(start))
    except Exception:
        return str(path)


def _as_repo_path(path: str | Path, repo_root: Path) -> Path:
    p = path if isinstance(path, Path) else Path(path)
    if p.is_absolute():
        return p
    return repo_root / p


def _fmt_bool(value: Any) -> str:
    return str(bool(value)).lower()


def _path_stem(path: str) -> str:
    if not path:
        return ""
    try:
        return Path(path).name
    except Exception:
        return str(path)


def _dataset_spec(value: str) -> dict[str, Any] | None:
    text = str(value or "").strip()
    if not text:
        return None
    stem = _path_stem(text)
    for spec in DATASET_SPECS:
        aliases = tuple(str(x) for x in spec.get("aliases", ()))
        if text == spec["label"] or stem == spec["label"]:
            return spec
        if text in aliases or stem in aliases:
            return spec
        for alias in aliases:
            if alias and alias in text:
                return spec
    return None


def _dataset_label(value: str) -> str:
    spec = _dataset_spec(value)
    if spec:
        return str(spec["label"])
    return str(value or "").strip()


def _dataset_description(value: str) -> str:
    spec = _dataset_spec(value)
    if spec:
        return str(spec["description"])
    return str(value or "").strip()


def _dataset_labels_csv(value: str) -> str:
    parts = [x.strip() for x in str(value or "").split(",") if x.strip()]
    labels: list[str] = []
    seen: set[str] = set()
    for part in parts:
        label = _dataset_label(part)
        if not label or label in seen:
            continue
        seen.add(label)
        labels.append(label)
    return ",".join(labels)


def _eval_display_label(eval_set: str, eval_variant: str, eval_checkpoint: str, decode: str) -> str:
    parts: list[str] = []
    label = str(eval_set or "").strip()
    variant = str(eval_variant or "").strip()
    checkpoint = str(eval_checkpoint or "").strip()
    decode_name = str(decode or "").strip()
    if label:
        parts.append(label)
    if variant:
        parts.append(variant)
    if checkpoint:
        parts.append(checkpoint)
    if decode_name:
        parts.append(decode_name)
    return " / ".join(parts)


def _timestamp_utc_from_file(path: Path) -> str:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return ""


def _parse_run_contract(path: Path) -> dict[str, str]:
    """Parse a minimal [run-contract] key/value file.

    The contract format is intentionally loose (single line, space separated key=value).
    """
    data: dict[str, str] = {}
    if not path.is_file():
        return data
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return data

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("[run-contract]"):
            continue
        body = line[len("[run-contract]") :].strip()
        for token in re.split(r"\s+", body):
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            data[key.strip()] = value.strip()
        break
    return data


def _parse_run_contract_from_logs(run_root: Path) -> tuple[dict[str, str], Path | None]:
    logs_dir = run_root / "logs"
    if not logs_dir.is_dir():
        return {}, None
    for log_path in sorted(logs_dir.rglob("*.log")):
        data = _parse_run_contract(log_path)
        if data:
            return data, log_path
    return {}, None


def _checkpoint_step(name: str) -> int:
    m = re.fullmatch(r"checkpoint-(\d+)", name)
    if not m:
        return -1
    try:
        return int(m.group(1))
    except Exception:
        return -1


def _checkpoint_name_from_step_value(value: int) -> str:
    if value < 0:
        return ""
    return f"checkpoint-{value:06d}"


def _normalize_stage_token(token: str) -> tuple[str, str]:
    text = str(token or "").strip()
    if not text:
        return "", ""
    lower = text.lower()
    if lower == "final":
        return "final", ""
    if lower.startswith("teacher"):
        return text, ""
    if lower.startswith("checkpoint-"):
        return "", text

    match = STAGE_TOKEN_RE.fullmatch(lower)
    if not match:
        return text, ""

    stage_letter = match.group(2).lower()
    raw_step = int(match.group(3))
    has_k_suffix = bool(match.group(4))
    if has_k_suffix or (stage_letter == "a" and raw_step < 1000):
        raw_step *= 1000
    return f"stage_{stage_letter}", _checkpoint_name_from_step_value(raw_step)


def _normalize_model_variant(model_path: str) -> tuple[str, str]:
    text = str(model_path or "").strip()
    if not text:
        return "", ""
    match = MODEL_CHECKPOINT_RE.search(text)
    if not match:
        return "", ""
    return match.group(1), _checkpoint_name_from_step_value(int(match.group(2)))


def _latest_checkpoint(path: Path, repo_root: Path) -> str:
    if not path.is_dir():
        return ""
    latest_step = -1
    latest_path: Path | None = None
    for child in path.iterdir():
        if not child.is_dir():
            continue
        step = _checkpoint_step(child.name)
        if step < 0:
            continue
        if step > latest_step:
            latest_step = step
            latest_path = child
    return _safe_rel(latest_path, repo_root) if latest_path else ""


def _mtime_utc(path: Path) -> str:
    return _timestamp_utc_from_file(path)


def _run_sort_key(row: dict[str, Any]) -> tuple[float, str]:
    ts = row.get("timestamp_epoch")
    try:
        return (float(ts), row.get("run_name", ""))
    except Exception:
        return (-1.0, row.get("run_name", ""))


def collect_run_rows(runs_root: Path, repo_root: Path) -> list[dict[str, str | float]]:
    rows: list[dict[str, str | float]] = []
    for child in sorted(runs_root.iterdir()):
        if not child.is_dir() or child.is_symlink():
            continue
        summary_path = child / "train_summary.json"
        contract_path = child / "run_contract.txt"
        contract_source_path: Path | None = contract_path if contract_path.is_file() else None

        summary: dict[str, Any] | None = _read_json(summary_path) if summary_path.is_file() else None
        contract = _parse_run_contract(contract_path)
        if not contract:
            contract, contract_source_path = _parse_run_contract_from_logs(child)

        source_langs = ""
        target_langs = ""

        if summary:
            source = "train_summary"
            timestamp_epoch = float(summary.get("timestamp", -1.0) or -1.0)
            timestamp_utc = _fmt_ts(summary.get("timestamp"))
            pair_count = _fmt_int(summary.get("pair_count"))
            pairs_input_spec = str(summary.get("pairs_input_spec", ""))
            eval_dataset_paths = ",".join((summary.get("eval_dataset_paths") or [])) if isinstance(summary.get("eval_dataset_paths"), list) else ""
            schedule = str(summary.get("schedule", ""))
            sft_steps = _fmt_int(summary.get("sft_steps"))
            distill_steps = _fmt_int(summary.get("distill_steps"))
            lambda_kd = _fmt_float(summary.get("lambda_kd"))
            mu_triplet = _fmt_float(summary.get("mu_triplet"))
            kd_temperature = _fmt_float(summary.get("kd_temperature"))
            margin = _fmt_float(summary.get("margin"))
            resumed = _fmt_bool(summary.get("resumed", False))
            resume_stage = str(summary.get("resume_stage", ""))
            resume_from = str(summary.get("resume_from", ""))
            selected_checkpoint = str(summary.get("selected_checkpoint", ""))
            selected_checkpoint_stage = str(summary.get("selected_checkpoint_stage", ""))
            selected_checkpoint_loss = _fmt_float(summary.get("selected_checkpoint_loss"))
            teacher_model = str(summary.get("teacher_model", ""))
            student_model = str(summary.get("student_model", ""))
            run_status = "completed"
            total_steps = _fmt_int(summary.get("total_steps"))
            final_out = str(summary.get("final_out", ""))
            source_langs = ",".join(summary.get("source_langs", []) or []) if isinstance(summary.get("source_langs"), list) else ""
            target_langs = ",".join(summary.get("target_langs", []) or []) if isinstance(summary.get("target_langs"), list) else ""
        elif contract:
            source = "run_contract"
            try:
                # contract format currently does not include a timestamp field.
                # keep deterministic fallback to file mtime for sorting.
                timestamp_epoch = float((contract_source_path or contract_path).stat().st_mtime)
            except Exception:
                timestamp_epoch = -1.0
            timestamp_utc = _mtime_utc(contract_source_path or contract_path)
            pair_count = ""
            pairs_input_spec = contract.get("pairs_input_spec", "")
            eval_dataset_paths = contract.get("eval_dataset_paths", "")
            schedule = contract.get("schedule", "")
            sft_steps = ""
            distill_steps = ""
            lambda_kd = ""
            mu_triplet = ""
            kd_temperature = ""
            margin = ""
            resumed = _fmt_bool(contract.get("resume_stage") not in ("", "none", None))
            resume_stage = contract.get("resume_stage", "none")
            resume_from = contract.get("resume_from", "")
            selected_checkpoint = ""
            selected_checkpoint_stage = ""
            selected_checkpoint_loss = ""
            teacher_model = ""
            student_model = ""
            run_status = "contract_only"
            total_steps = ""
            final_out = ""
        else:
            source = "none"
            try:
                timestamp_epoch = float(child.stat().st_mtime)
            except Exception:
                timestamp_epoch = -1.0
            timestamp_utc = _mtime_utc(child)
            pair_count = ""
            pairs_input_spec = ""
            eval_dataset_paths = ""
            schedule = ""
            sft_steps = ""
            distill_steps = ""
            lambda_kd = ""
            mu_triplet = ""
            kd_temperature = ""
            margin = ""
            resumed = "false"
            resume_stage = ""
            resume_from = ""
            selected_checkpoint = ""
            selected_checkpoint_stage = ""
            selected_checkpoint_loss = ""
            teacher_model = ""
            student_model = ""
            run_status = "sparse"
            total_steps = ""
            final_out = ""

        # Keep this lightweight to avoid crashes on sparse metadata.
        if not final_out:
            final_dir = child / "final"
            if final_dir.exists():
                final_out = _safe_rel(final_dir, repo_root)

        rows.append(
            {
                "run_name": child.name,
                "run_root": _safe_rel(child, repo_root),
                "run_status": run_status,
                "summary_source": source,
                "summary_path": _safe_rel(summary_path, repo_root) if summary_path.is_file() else (
                    _safe_rel(contract_source_path or contract_path, repo_root) if contract else ""
                ),
                "timestamp_epoch": float(timestamp_epoch),
                "timestamp_utc": timestamp_utc,
                "schedule": schedule,
                "pair_count": pair_count,
                "pairs_input_spec": pairs_input_spec,
                "source_langs": source_langs,
                "target_langs": target_langs,
                "eval_dataset_paths": eval_dataset_paths,
                "eval_dataset_labels": _dataset_labels_csv(eval_dataset_paths),
                "total_steps": total_steps,
                "sft_steps": sft_steps,
                "distill_steps": distill_steps,
                "lambda_kd": lambda_kd,
                "mu_triplet": mu_triplet,
                "kd_temperature": kd_temperature,
                "margin": margin,
                "teacher_model": teacher_model,
                "student_model": student_model,
                "resumed": resumed,
                "resume_stage": resume_stage,
                "resume_from": resume_from,
                "selected_checkpoint": selected_checkpoint,
                "selected_checkpoint_stage": selected_checkpoint_stage,
                "selected_checkpoint_loss": selected_checkpoint_loss,
                "latest_stage_a_checkpoint": _latest_checkpoint(child / "stage_a", repo_root),
                "latest_stage_b_checkpoint": _latest_checkpoint(child / "stage_b", repo_root),
                "final_model": final_out,
                "updated_utc": _mtime_utc(_as_repo_path(child, repo_root)),
            }
        )
    rows.sort(key=_run_sort_key, reverse=True)
    return rows


def _decode_from_path(path: Path) -> str:
    for part in reversed(path.parts):
        if part.endswith("__greedy") or part == "greedy":
            return "greedy"
        if part.endswith("__sampled") or part == "sampled":
            return "sampled"
        if "_greedy_" in part or part.endswith("_greedy"):
            return "greedy"
        if "_sampled_" in part or part.endswith("_sampled"):
            return "sampled"
    folder = path.name
    if folder.endswith("__greedy"):
        return "greedy"
    if folder.endswith("__sampled"):
        return "sampled"
    if "_greedy_" in folder or folder.endswith("_greedy"):
        return "greedy"
    if "_sampled_" in folder or folder.endswith("_sampled"):
        return "sampled"
    return ""


def _find_eval_dataset(summary: dict[str, Any], eval_name: str) -> str:
    pairs = str(summary.get("pairs") or "")
    if not pairs:
        pair_files = summary.get("pair_files")
        if isinstance(pair_files, list) and pair_files:
            first_pair = pair_files[0]
            if isinstance(first_pair, str):
                pairs = first_pair
    if pairs:
        return pairs
    return eval_name


def _infer_eval_components(eval_name: str, pairs: str = "", model_path: str = "") -> tuple[str, str, str]:
    if "__" in eval_name:
        parts = eval_name.split("__")
        eval_set = parts[0]
        checkpoint = ""
        variant = ""
        for part in parts[1:]:
            if part in {"greedy", "sampled"}:
                continue
            parsed_variant, parsed_checkpoint = _normalize_stage_token(part)
            if parsed_variant and not variant:
                variant = parsed_variant
            if parsed_checkpoint and not checkpoint:
                checkpoint = parsed_checkpoint
        if (not variant or not checkpoint) and model_path:
            model_variant, model_checkpoint = _normalize_model_variant(model_path)
            if not variant and model_variant:
                variant = model_variant
            if not checkpoint and model_checkpoint:
                checkpoint = model_checkpoint
        return eval_set, variant, checkpoint

    tokens = [token for token in eval_name.split("_") if token]
    variant = ""
    checkpoint = ""
    if tokens and tokens[0] == "eval" and len(tokens) > 1:
        variant, checkpoint = _normalize_stage_token(tokens[1])
    if (not variant or not checkpoint) and model_path:
        model_variant, model_checkpoint = _normalize_model_variant(model_path)
        if not variant and model_variant:
            variant = model_variant
        if not checkpoint and model_checkpoint:
            checkpoint = model_checkpoint
    return pairs or eval_name, variant, checkpoint


def _eval_timestamp_epoch(path: Path) -> str:
    try:
        return str(float(path.stat().st_mtime))
    except Exception:
        return ""


def _collect_eval_row(path: Path, summary: dict[str, Any], repo_root: Path) -> dict[str, str]:
    eval_name = path.name
    student = summary.get("student") if isinstance(summary.get("student"), dict) else {}
    model = str(student.get("model", "")) if isinstance(student, dict) else ""
    pairs = _find_eval_dataset(summary, eval_name)
    eval_set_alias, eval_variant, eval_checkpoint = _infer_eval_components(eval_name, pairs, model)
    pred_path = ""
    if isinstance(student, dict):
        pred = student.get("predictions")
        if isinstance(pred, dict):
            pred_path = str(pred.get("path", ""))
        elif isinstance(pred, str):
            pred_path = pred
    return {
        "run_name": str(path.parent.parent.name),
        "eval_dir": eval_name,
        "eval_set": _dataset_label(eval_set_alias or pairs),
        "eval_set_alias": eval_set_alias,
        "eval_set_description": _dataset_description(eval_set_alias or pairs),
        "eval_variant": eval_variant,
        "eval_checkpoint": eval_checkpoint,
        "eval_label": _eval_display_label(_dataset_label(eval_set_alias or pairs), eval_variant, eval_checkpoint, _decode_from_path(path)),
        "eval_dir_path": _safe_rel(path, repo_root),
        "decode": _decode_from_path(path),
        "eval_samples": _fmt_int(summary.get("eval_samples")),
        "eval_timestamp_utc": _timestamp_utc_from_file(path),
        "pairs": pairs,
        "pairs_stem": _path_stem(pairs),
        "student_model": model,
        "bleu": _fmt_float(((summary.get("student", {}) or {}).get("metrics_overall", {}).get("bleu", {}) or {}).get("score")),
        "chrf": _fmt_float(((summary.get("student", {}) or {}).get("metrics_overall", {}).get("chrf", {}) or {}).get("score")),
        "predictions_path": _safe_rel(Path(pred_path), repo_root) if pred_path else "",
        "compare_summary_path": _safe_rel(path, repo_root),
        "_eval_timestamp_epoch": _eval_timestamp_epoch(path),
    }


def _collect_eval_rows_for_path(compare_path: Path, runs_root: Path, repo_root: Path) -> dict[str, str] | None:
    summary = _read_json(compare_path)
    if not summary:
        return None
    summary_path = compare_path.resolve()
    run_root = next((p for p in summary_path.parents if p.parent == runs_root), None)
    if run_root is None:
        run_root = summary_path.parent.parent
    run_name = run_root.name if run_root else ""
    if not run_name:
        return None
    row = _collect_eval_row(summary_path.parent, summary, repo_root)
    row["run_name"] = run_name
    return row


def _collect_eval_rows_from_manifest(manifest_path: Path, runs_root: Path, repo_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not manifest_path.is_file():
        return rows

    manifest_rows: list[dict[str, Any]] = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            obj = json.loads(text)
        except Exception:
            continue
        if isinstance(obj, dict):
            manifest_rows.append(obj)

    for item in manifest_rows:
        try:
            status = int(item.get("status", 1))
        except Exception:
            status = 1
        if status != 0:
            continue

        compare_summary = str(item.get("compare_summary", "")).strip()
        if not compare_summary:
            continue

        compare_path = _as_repo_path(compare_summary, repo_root)
        if compare_path.is_file():
            # Prefer the richer compare-summary parser when the file exists.
            continue

        run_root_value = str(item.get("run_root", "")).strip()
        if run_root_value:
            run_root = _as_repo_path(run_root_value, repo_root)
        else:
            run_root = next((p for p in manifest_path.resolve().parents if p.parent == runs_root), None)
        if not run_root:
            continue

        run_name = Path(run_root).name
        eval_name = str(item.get("eval_name", "")).strip()
        checkpoint_name = str(item.get("checkpoint_name", "")).strip()
        checkpoint_path = str(item.get("checkpoint_path", "")).strip()
        decode = str(item.get("decode", "")).strip()
        out_dir = str(item.get("out_dir", "")).strip()
        eval_dir_name = Path(out_dir).name if out_dir else eval_name

        pairs = str(item.get("pairs", ""))
        eval_set_alias, eval_variant, eval_checkpoint = _infer_eval_components(eval_dir_name, pairs, checkpoint_path)
        if checkpoint_name and not eval_checkpoint:
            eval_checkpoint = checkpoint_name
        eval_key = eval_set_alias or eval_name or pairs

        rows.append(
            {
                "run_name": run_name,
                "eval_dir": eval_dir_name,
                "eval_set": _dataset_label(eval_key),
                "eval_set_alias": eval_set_alias,
                "eval_set_description": _dataset_description(eval_key),
                "eval_variant": eval_variant,
                "eval_checkpoint": eval_checkpoint,
                "eval_label": _eval_display_label(_dataset_label(eval_key), eval_variant, eval_checkpoint, decode),
                "eval_dir_path": _safe_rel(_as_repo_path(out_dir, repo_root), repo_root) if out_dir else "",
                "decode": decode,
                "eval_samples": _fmt_int(item.get("samples")),
                "eval_timestamp_utc": str(item.get("timestamp_utc", "")),
                "pairs": pairs,
                "pairs_stem": _path_stem(pairs),
                "student_model": checkpoint_path,
                "bleu": _fmt_float(item.get("bleu")),
                "chrf": _fmt_float(item.get("chrf")),
                "predictions_path": _safe_rel(_as_repo_path(str(item.get("student_predictions", "")), repo_root), repo_root)
                if str(item.get("student_predictions", "")).strip()
                else "",
                "compare_summary_path": compare_summary,
                "_eval_timestamp_epoch": "",
            }
        )
    return rows


def collect_eval_rows(runs_root: Path, repo_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[Path] = set()
    seen_compare_paths: set[str] = set()
    for compare_path in runs_root.rglob("compare_eval_summary.json"):
        try:
            resolved = compare_path.resolve()
        except Exception:
            resolved = compare_path
        if resolved in seen:
            continue
        seen.add(resolved)
        row = _collect_eval_rows_for_path(compare_path, runs_root, repo_root)
        if not row:
            continue
        rows.append(row)
        seen_compare_paths.add(str(row.get("compare_summary_path", "")))

    for manifest_path in runs_root.rglob("manifest.jsonl"):
        for row in _collect_eval_rows_from_manifest(manifest_path, runs_root, repo_root):
            compare_key = str(row.get("compare_summary_path", ""))
            if compare_key and compare_key in seen_compare_paths:
                continue
            rows.append(row)
            if compare_key:
                seen_compare_paths.add(compare_key)

    deduped: dict[tuple[str, str, str, str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (
            str(row.get("run_name", "")),
            str(row.get("eval_set", "")),
            str(row.get("eval_variant", "")),
            str(row.get("eval_checkpoint", "")),
            str(row.get("decode", "")),
            str(row.get("student_model", "")),
        )
        current = deduped.get(key)
        if current is None:
            deduped[key] = row
            continue
        current_ts = _as_float_or_none(current.get("_eval_timestamp_epoch"))
        row_ts = _as_float_or_none(row.get("_eval_timestamp_epoch"))
        if row_ts is not None and (current_ts is None or row_ts >= current_ts):
            deduped[key] = row

    final_rows = list(deduped.values())
    final_rows.sort(
        key=lambda x: (
            x["run_name"],
            x.get("eval_variant", ""),
            x.get("eval_checkpoint", ""),
            x["eval_set"],
            x["decode"],
        )
    )
    return final_rows


def write_csv(path: Path, rows: list[dict[str, str | float]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def _md_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return "\n".join([header, sep] + body)


def write_markdown(
    path: Path,
    run_rows: list[dict[str, str | float]],
    eval_rows: list[dict[str, str]],
    runs_root: Path,
) -> None:
    generated_utc = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    run_view = [
        {
            "run_name": row["run_name"],
            "run_status": row["run_status"],
            "run_root": row["run_root"],
            "timestamp_utc": row["timestamp_utc"],
            "updated_utc": row["updated_utc"],
            "source_langs": row["source_langs"],
            "target_langs": row["target_langs"],
            "eval_dataset_labels": row["eval_dataset_labels"],
            "eval_dataset_paths": row["eval_dataset_paths"],
            "pair_count": row["pair_count"],
            "pairs_input_spec": row["pairs_input_spec"],
            "total_steps": row["total_steps"],
            "schedule": row["schedule"],
            "sft_steps": row["sft_steps"] if row["sft_steps"] != "" else "",
            "distill_steps": row["distill_steps"] if row["distill_steps"] != "" else "",
            "lambda_kd": row["lambda_kd"],
            "mu_triplet": row["mu_triplet"],
            "kd_temperature": row["kd_temperature"],
            "margin": row["margin"],
            "teacher_model": row["teacher_model"],
            "student_model": row["student_model"],
            "resumed": row["resumed"],
            "summary_path": row["summary_path"],
            "latest_stage_a_checkpoint": Path(row["latest_stage_a_checkpoint"]).name if row["latest_stage_a_checkpoint"] else "",
            "latest_stage_b_checkpoint": Path(row["latest_stage_b_checkpoint"]).name if row["latest_stage_b_checkpoint"] else "",
            "final_model": row["final_model"],
            "summary_source": row["summary_source"],
        }
        for row in run_rows
    ]
    eval_view = [
        {
            "run_name": row["run_name"],
            "eval_label": row.get("eval_label", row["eval_dir"]),
            "eval_dir": row["eval_dir"],
            "eval_set": row["eval_set"],
            "eval_set_alias": row.get("eval_set_alias", ""),
            "eval_set_description": row.get("eval_set_description", ""),
            "eval_variant": row["eval_variant"],
            "eval_checkpoint": row["eval_checkpoint"],
            "decode": row["decode"],
            "bleu": row["bleu"],
            "chrf": row["chrf"],
            "pairs": row["pairs"],
            "eval_timestamp_utc": row["eval_timestamp_utc"],
            "samples": row["eval_samples"],
            "student_model": row["student_model"],
            "compare_summary_path": row["compare_summary_path"],
            "predictions_path": row["predictions_path"],
            "eval_dir_path": row["eval_dir_path"],
        }
        for row in eval_rows
    ]
    md = []
    md.append("# Translation Distillation Run Index")
    md.append("")
    md.append(f"Generated: {generated_utc}")
    md.append(f"Runs root: `{runs_root}`")
    md.append("")
    md.append("## Training Runs")
    md.append("")
    if run_view:
        md.append(
            _md_table(
                run_view,
                [
                    ("run_name", "run"),
                    ("run_status", "status"),
                    ("run_root", "run_path"),
                    ("timestamp_utc", "timestamp_utc"),
                    ("updated_utc", "updated_utc"),
                    ("source_langs", "source_langs"),
                    ("target_langs", "target_langs"),
                    ("eval_dataset_labels", "eval_datasets"),
                    ("pair_count", "pair_count"),
                    ("pairs_input_spec", "pairs_input"),
                    ("total_steps", "total_steps"),
                    ("schedule", "schedule"),
                    ("sft_steps", "sft_steps"),
                    ("distill_steps", "distill_steps"),
                    ("lambda_kd", "lambda_kd"),
                    ("mu_triplet", "mu_triplet"),
                    ("kd_temperature", "kd_temperature"),
                    ("margin", "margin"),
                    ("teacher_model", "teacher_model"),
                    ("student_model", "student_model"),
                    ("resumed", "resumed"),
                    ("summary_source", "summary_source"),
                    ("summary_path", "summary"),
                    ("latest_stage_a_checkpoint", "latest_stage_a_ckpt"),
                    ("latest_stage_b_checkpoint", "latest_stage_b_ckpt"),
                    ("final_model", "final_model"),
                ],
            )
        )
    else:
        md.append("_No run folders found._")
    md.append("")
    md.append("## Eval Results")
    md.append("")
    if eval_view:
        md.append(
            _md_table(
                eval_view,
                [
                    ("run_name", "run"),
                    ("eval_label", "eval"),
                    ("eval_set", "eval_set"),
                    ("eval_set_description", "eval_set_description"),
                    ("eval_variant", "eval_variant"),
                    ("eval_checkpoint", "eval_checkpoint"),
                    ("decode", "decode"),
                    ("bleu", "bleu"),
                    ("chrf", "chrf"),
                    ("pairs", "pairs"),
                    ("eval_timestamp_utc", "evaluated_utc"),
                    ("samples", "samples"),
                    ("student_model", "student_model"),
                    ("predictions_path", "predictions"),
                    ("compare_summary_path", "compare_summary"),
                    ("eval_dir_path", "eval_dir_path"),
                ],
            )
        )
    else:
        md.append("_No compare_eval_summary.json files found._")
    md.append("")
    md.append("## Notes")
    md.append("")
    md.append("### Dataset Labels")
    md.append("")
    for spec in DATASET_SPECS:
        md.append(f"- `{spec['label']}`: {spec['description']}")
    md.append("")
    md.append("- `pair_count` is the effective row count used by training.")
    md.append("- `pairs_input` is the exact training file/spec the run consumed.")
    md.append("- For conclusions and next actions, see `SESSION_STATUS.md` in the same folder.")
    md.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build run/eval index for translation distillation.")
    ap.add_argument(
        "--runs-root",
        default="projects/distillation/translation/runs",
        help="Root directory containing run folders.",
    )
    ap.add_argument(
        "--out-md",
        default="projects/distillation/translation/runs/RUN_INDEX.md",
        help="Output markdown index path.",
    )
    ap.add_argument(
        "--out-runs-csv",
        default="projects/distillation/translation/runs/run_index_runs.csv",
        help="Output CSV for training runs.",
    )
    ap.add_argument(
        "--out-evals-csv",
        default="projects/distillation/translation/runs/run_index_evals.csv",
        help="Output CSV for eval summaries.",
    )
    ap.add_argument(
        "--out-compare-csv",
        default="projects/distillation/translation/runs/run_index_compare.csv",
        help="Output merged comparison CSV (strict columns for run params + eval metrics).",
    )
    ap.add_argument(
        "--out-compare-md",
        default="projects/distillation/translation/runs/RUN_COMPARE.md",
        help="Output merged comparison markdown table.",
    )
    return ap.parse_args()


def _as_float_or_none(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except Exception:
        return None


def _comparison_group_label(eval_variant: str, eval_checkpoint: str) -> str:
    variant = (eval_variant or "").strip()
    ckpt = (eval_checkpoint or "").strip()
    if variant and ckpt:
        return f"{variant}__{ckpt}"
    if variant:
        return variant
    if ckpt:
        return ckpt
    return "default"


EXTERNAL_WMT13_LABEL = "external_wmt13_en_es_translation_benchmark_128"
INDOMAIN_CLEAN_LABEL = "indomain_clean_merged_en_es_translation_benchmark_128"


def build_comparison_rows(run_rows: list[dict[str, Any]], eval_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    run_map = {str(row.get("run_name", "")): row for row in run_rows}
    grouped: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}

    for ev in eval_rows:
        run_name = str(ev.get("run_name", ""))
        eval_variant = str(ev.get("eval_variant", ""))
        eval_checkpoint = str(ev.get("eval_checkpoint", ""))
        decode = str(ev.get("decode", ""))
        eval_student_model = str(ev.get("student_model", ""))
        key = (run_name, eval_variant, eval_checkpoint, decode, eval_student_model)
        run = run_map.get(run_name, {})
        bucket = grouped.get(key)
        if bucket is None:
            bucket = {
                "run_name": run_name,
                "run_status": str(run.get("run_status", "")),
                "summary_source": str(run.get("summary_source", "")),
                "timestamp_utc": str(run.get("timestamp_utc", "")),
                "updated_utc": str(run.get("updated_utc", "")),
                "source_langs": str(run.get("source_langs", "")),
                "target_langs": str(run.get("target_langs", "")),
                "pair_count": str(run.get("pair_count", "")),
                "pairs_input_spec": str(run.get("pairs_input_spec", "")),
                "schedule": str(run.get("schedule", "")),
                "total_steps": str(run.get("total_steps", "")),
                "sft_steps": str(run.get("sft_steps", "")),
                "distill_steps": str(run.get("distill_steps", "")),
                "lambda_kd": str(run.get("lambda_kd", "")),
                "mu_triplet": str(run.get("mu_triplet", "")),
                "kd_temperature": str(run.get("kd_temperature", "")),
                "margin": str(run.get("margin", "")),
                "teacher_model_cfg": str(run.get("teacher_model", "")),
                "student_model_cfg": str(run.get("student_model", "")),
                "resumed": str(run.get("resumed", "")),
                "resume_stage": str(run.get("resume_stage", "")),
                "resume_from": str(run.get("resume_from", "")),
                "group_label": _comparison_group_label(eval_variant, eval_checkpoint),
                "eval_variant": eval_variant,
                "eval_checkpoint": eval_checkpoint,
                "decode": decode,
                "evaluated_model": eval_student_model,
                f"{EXTERNAL_WMT13_LABEL}_bleu": "",
                f"{EXTERNAL_WMT13_LABEL}_chrf": "",
                f"{EXTERNAL_WMT13_LABEL}_pairs": "",
                f"{EXTERNAL_WMT13_LABEL}_eval_dir": "",
                f"{INDOMAIN_CLEAN_LABEL}_bleu": "",
                f"{INDOMAIN_CLEAN_LABEL}_chrf": "",
                f"{INDOMAIN_CLEAN_LABEL}_pairs": "",
                f"{INDOMAIN_CLEAN_LABEL}_eval_dir": "",
                "other_eval_sets": "",
                "other_eval_count": 0,
                "_other_eval_sets": set(),
                "_sort_ts": float(run.get("timestamp_epoch", -1.0) or -1.0),
            }
            grouped[key] = bucket

        eval_set = str(ev.get("eval_set", "")).strip()
        if eval_set == EXTERNAL_WMT13_LABEL:
            bucket[f"{EXTERNAL_WMT13_LABEL}_bleu"] = str(ev.get("bleu", ""))
            bucket[f"{EXTERNAL_WMT13_LABEL}_chrf"] = str(ev.get("chrf", ""))
            bucket[f"{EXTERNAL_WMT13_LABEL}_pairs"] = str(ev.get("pairs", ""))
            bucket[f"{EXTERNAL_WMT13_LABEL}_eval_dir"] = str(ev.get("eval_dir", ""))
        elif eval_set == INDOMAIN_CLEAN_LABEL:
            bucket[f"{INDOMAIN_CLEAN_LABEL}_bleu"] = str(ev.get("bleu", ""))
            bucket[f"{INDOMAIN_CLEAN_LABEL}_chrf"] = str(ev.get("chrf", ""))
            bucket[f"{INDOMAIN_CLEAN_LABEL}_pairs"] = str(ev.get("pairs", ""))
            bucket[f"{INDOMAIN_CLEAN_LABEL}_eval_dir"] = str(ev.get("eval_dir", ""))
        else:
            bucket["_other_eval_sets"].add(eval_set or str(ev.get("eval_dir", "")))

    rows: list[dict[str, Any]] = []
    for bucket in grouped.values():
        other_sets = sorted(x for x in bucket.pop("_other_eval_sets") if x)
        bucket["other_eval_sets"] = ",".join(other_sets)
        bucket["other_eval_count"] = len(other_sets)
        bucket[f"{EXTERNAL_WMT13_LABEL}_bleu"] = _fmt_float(bucket[f"{EXTERNAL_WMT13_LABEL}_bleu"])
        bucket[f"{EXTERNAL_WMT13_LABEL}_chrf"] = _fmt_float(bucket[f"{EXTERNAL_WMT13_LABEL}_chrf"])
        bucket[f"{INDOMAIN_CLEAN_LABEL}_bleu"] = _fmt_float(bucket[f"{INDOMAIN_CLEAN_LABEL}_bleu"])
        bucket[f"{INDOMAIN_CLEAN_LABEL}_chrf"] = _fmt_float(bucket[f"{INDOMAIN_CLEAN_LABEL}_chrf"])
        # Optional convenience deltas (teacher-style rows get blanks).
        eval2_bleu = _as_float_or_none(bucket[f"{EXTERNAL_WMT13_LABEL}_bleu"])
        eval3_bleu = _as_float_or_none(bucket[f"{INDOMAIN_CLEAN_LABEL}_bleu"])
        bucket["external_minus_indomain_bleu"] = _fmt_float(eval2_bleu - eval3_bleu) if eval2_bleu is not None and eval3_bleu is not None else ""
        # Keep merged comparison focused on comparable eval-set rows.
        if not bucket[f"{EXTERNAL_WMT13_LABEL}_bleu"] and not bucket[f"{INDOMAIN_CLEAN_LABEL}_bleu"]:
            continue
        group_label = str(bucket.get("group_label", ""))
        is_primary_group = (
            group_label in {"final", "teacher4b"}
            or group_label.startswith("stage_a__")
            or group_label.startswith("stage_b__")
        )
        if not is_primary_group and (eval2_bleu is None or eval3_bleu is None):
            continue
        rows.append(bucket)

    rows.sort(
        key=lambda r: (
            float(r.get("_sort_ts", -1.0)),
            str(r.get("run_name", "")),
            str(r.get("group_label", "")),
            str(r.get("decode", "")),
        ),
        reverse=True,
    )
    for r in rows:
        r.pop("_sort_ts", None)
    return rows


def write_comparison_markdown(path: Path, rows: list[dict[str, Any]], runs_root: Path) -> None:
    generated_utc = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    md: list[str] = []
    md.append("# Translation Distillation Merged Comparison")
    md.append("")
    md.append(f"Generated: {generated_utc}")
    md.append(f"Runs root: `{runs_root}`")
    md.append("")
    md.append("One row = one comparable eval group (run + variant/checkpoint + decode), with strict run-parameter columns.")
    md.append("")
    if rows:
        md.append(
            _md_table(
                rows,
                [
                    ("run_name", "run"),
                    ("group_label", "group"),
                    ("decode", "decode"),
                    ("pair_count", "train_rows"),
                    ("sft_steps", "stage_a_steps"),
                    ("distill_steps", "stage_b_steps"),
                    ("teacher_model_cfg", "teacher_model_cfg"),
                    ("student_model_cfg", "student_model_cfg"),
                    ("evaluated_model", "evaluated_model"),
                    ("source_langs", "source_langs"),
                    ("target_langs", "target_langs"),
                    ("lambda_kd", "lambda_kd"),
                    ("mu_triplet", "mu_triplet"),
                    (f"{EXTERNAL_WMT13_LABEL}_bleu", f"{EXTERNAL_WMT13_LABEL}_bleu"),
                    (f"{EXTERNAL_WMT13_LABEL}_chrf", f"{EXTERNAL_WMT13_LABEL}_chrf"),
                    (f"{INDOMAIN_CLEAN_LABEL}_bleu", f"{INDOMAIN_CLEAN_LABEL}_bleu"),
                    (f"{INDOMAIN_CLEAN_LABEL}_chrf", f"{INDOMAIN_CLEAN_LABEL}_chrf"),
                ],
            )
        )
    else:
        md.append("_No merged comparison rows available._")
    md.append("")
    md.append("## Dataset Labels")
    md.append("")
    for spec in DATASET_SPECS:
        md.append(f"- `{spec['label']}`: {spec['description']}")
    md.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[4]
    runs_root = Path(args.runs_root).resolve()
    out_md = Path(args.out_md).resolve()
    out_runs_csv = Path(args.out_runs_csv).resolve()
    out_evals_csv = Path(args.out_evals_csv).resolve()
    out_compare_csv = Path(args.out_compare_csv).resolve()
    out_compare_md = Path(args.out_compare_md).resolve()

    run_rows = collect_run_rows(runs_root, repo_root)
    eval_rows = collect_eval_rows(runs_root, repo_root)

    write_csv(
        out_runs_csv,
        run_rows,
        [
            "run_name",
            "run_root",
            "run_status",
            "summary_source",
            "timestamp_utc",
            "updated_utc",
            "source_langs",
            "target_langs",
            "eval_dataset_labels",
            "eval_dataset_paths",
            "pair_count",
            "pairs_input_spec",
            "schedule",
            "total_steps",
            "sft_steps",
            "distill_steps",
            "lambda_kd",
            "mu_triplet",
            "kd_temperature",
            "margin",
            "teacher_model",
            "student_model",
            "resumed",
            "resume_stage",
            "resume_from",
            "selected_checkpoint",
            "selected_checkpoint_stage",
            "selected_checkpoint_loss",
            "summary_path",
            "latest_stage_a_checkpoint",
            "latest_stage_b_checkpoint",
            "final_model",
        ],
    )
    write_csv(
        out_evals_csv,
        eval_rows,
        [
            "run_name",
            "eval_dir",
            "eval_label",
            "eval_set",
            "eval_set_alias",
            "eval_set_description",
            "eval_variant",
            "eval_checkpoint",
            "decode",
            "eval_dir_path",
            "eval_timestamp_utc",
            "eval_samples",
            "pairs_stem",
            "bleu",
            "chrf",
            "pairs",
            "student_model",
            "predictions_path",
            "compare_summary_path",
        ],
    )

    compare_rows = build_comparison_rows(run_rows, eval_rows)
    write_csv(
        out_compare_csv,
        compare_rows,
        [
            "run_name",
            "run_status",
            "summary_source",
            "timestamp_utc",
            "updated_utc",
            "source_langs",
            "target_langs",
            "pair_count",
            "pairs_input_spec",
            "schedule",
            "total_steps",
            "sft_steps",
            "distill_steps",
            "lambda_kd",
            "mu_triplet",
            "kd_temperature",
            "margin",
            "teacher_model_cfg",
            "student_model_cfg",
            "resumed",
            "resume_stage",
            "resume_from",
            "group_label",
            "eval_variant",
            "eval_checkpoint",
            "decode",
            "evaluated_model",
            f"{EXTERNAL_WMT13_LABEL}_bleu",
            f"{EXTERNAL_WMT13_LABEL}_chrf",
            f"{EXTERNAL_WMT13_LABEL}_pairs",
            f"{EXTERNAL_WMT13_LABEL}_eval_dir",
            f"{INDOMAIN_CLEAN_LABEL}_bleu",
            f"{INDOMAIN_CLEAN_LABEL}_chrf",
            f"{INDOMAIN_CLEAN_LABEL}_pairs",
            f"{INDOMAIN_CLEAN_LABEL}_eval_dir",
            "other_eval_sets",
            "other_eval_count",
            "external_minus_indomain_bleu",
        ],
    )
    write_markdown(out_md, run_rows, eval_rows, runs_root)
    write_comparison_markdown(out_compare_md, compare_rows, runs_root)
    print(f"wrote: {out_md}")
    print(f"wrote: {out_runs_csv}")
    print(f"wrote: {out_evals_csv}")
    print(f"wrote: {out_compare_csv}")
    print(f"wrote: {out_compare_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
