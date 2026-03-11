#!/usr/bin/env python3
"""Rebuild a cohesive translation-results bundle from whatever artifacts already exist."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

BOOTSTRAP_ROOT = Path(__file__).resolve().parents[4]
if str(BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(BOOTSTRAP_ROOT))

from projects.distillation.translation.pipeline import build_run_index
from projects.distillation.translation.pipeline import run_stage_a_cpu_matrix as stage_a_matrix
from projects.distillation.translation.pipeline import run_stage_b_checkpoint_sweep as stage_b_sweep


PROJECT_ROOT = BOOTSTRAP_ROOT
DEFAULT_RUNS_ROOT = PROJECT_ROOT / "projects" / "distillation" / "translation" / "runs"
DEFAULT_BUNDLE_DIR = DEFAULT_RUNS_ROOT / "results_bundle"
DEFAULT_EXTERNAL_EVAL = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "translate_distill_pairs.eval2_wmt13_enes_128.jsonl"
)
BAR_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]
RUN_NAME_PREFIX = "translategemma4b_es_en_gemma3_1b_"
GOLD_LEGACY_DATASET_REL = (
    "projects/distillation/translation/training_data/gold/"
    "translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl"
)
GOLD_LEGACY_LABEL = "Gold Legacy 1280"
GOLD_LEGACY_RUN_NAMES = {
    "translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100",
}
RESULT_CATEGORY_LABELS = {
    "teacher_baseline": "Teacher Baseline",
    "student_stage_a": "Student Stage A",
    "student_stage_b": "Student Stage B",
    "student_final": "Student Final",
    "student_other": "Student Other",
    "external_baseline": "External Baseline",
}
LEADERBOARD_SLUGS = {
    build_run_index.EXTERNAL_WMT13_LABEL: "external_wmt13_en_es_translation_benchmark_128",
    build_run_index.INDOMAIN_CLEAN_LABEL: "indomain_clean_merged_en_es_translation_benchmark_128",
}


def _now_utc() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def _looks_like_path(text: str) -> bool:
    raw = str(text or "").strip()
    return bool(raw) and (
        raw.startswith("/")
        or raw.startswith("projects/")
        or raw.startswith("./")
        or raw.startswith("../")
    )


def _resolve_repo_path(value: str, repo_root: Path) -> Path:
    raw = str(value or "").strip()
    path = Path(raw)
    if path.is_absolute():
        return path
    return repo_root / path


def _normalize_path_text(value: str, repo_root: Path) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "," in raw:
        parts = [part.strip() for part in raw.split(",")]
        return ",".join(_normalize_path_text(part, repo_root) for part in parts if part)
    if not _looks_like_path(raw):
        return raw
    return _safe_rel(_resolve_repo_path(raw, repo_root), repo_root)


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _md_escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|")


def _fmt_float(value: Any, digits: int = 4) -> str:
    if value in ("", None):
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return ""


def _as_float(value: Any) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(value)
    except Exception:
        return None


def _as_int(value: Any) -> int | None:
    try:
        if value in ("", None):
            return None
        return int(value)
    except Exception:
        return None


def _first_nonempty(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        text = str(row.get(key, "")).strip()
        if text:
            return text
    return ""


def _checkpoint_step(text: str) -> int:
    match = re.search(r"checkpoint-(\d+)", str(text or ""))
    if not match:
        return -1
    return int(match.group(1))


def _short_run_name(run_name: str) -> str:
    text = str(run_name or "").strip()
    if not text:
        return ""
    if text.startswith("baseline__"):
        # Strip baseline__ prefix and timestamp suffix.
        text = text[len("baseline__"):]
        text = re.sub(r"__\d{4}-\d{2}-\d{2}T\d{6}Z$", "", text)
        return text or str(run_name or "")
    if text.startswith(RUN_NAME_PREFIX):
        text = text[len(RUN_NAME_PREFIX) :]
    text = re.sub(r"_(?:\d{8}T\d{6}Z|\d{8}_\d{6})$", "", text)
    return text or str(run_name or "")


def _infer_pair_count(row: dict[str, Any]) -> str:
    raw = str(row.get("pair_count", "")).strip()
    if raw:
        return raw
    candidates = [
        str(row.get("pairs_input_spec", "")).strip(),
        str(row.get("run_name", "")).strip(),
    ]
    for text in candidates:
        if not text:
            continue
        for pattern in (r"subset[_-]?(\d+)", r"train(\d+)", r"full_(\d+)"):
            match = re.search(pattern, text)
            if match:
                return match.group(1)
    return ""


def _dataset_label(row: dict[str, Any]) -> str:
    run_name = str(row.get("run_name", "")).strip()
    pairs_input_spec = str(row.get("pairs_input_spec", "")).strip()
    pair_count = _infer_pair_count(row)
    if run_name in GOLD_LEGACY_RUN_NAMES:
        return GOLD_LEGACY_LABEL
    if pairs_input_spec == GOLD_LEGACY_DATASET_REL:
        return GOLD_LEGACY_LABEL
    match = re.search(r"train\.merged\.subset_(\d+)\.seed\d+\.jsonl$", pairs_input_spec)
    if match:
        return f"Merged Subset {match.group(1)}"
    if pairs_input_spec.endswith("translate_distill_pairs_en_es_2way.train.merged.jsonl"):
        return f"Merged Full {pair_count}" if pair_count else "Merged Full"
    if pairs_input_spec.endswith("translate_distill_pairs.jsonl"):
        return f"Legacy 1280 Path"
    if pairs_input_spec.endswith(".jsonl"):
        return Path(pairs_input_spec).name
    return ""


def _annotate_dataset_labels(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        item = dict(row)
        item["dataset_label"] = _dataset_label(item)
        out.append(item)
    return out


def _compare_row_metadata(row: dict[str, Any]) -> dict[str, str]:
    run_name = str(row.get("run_name", "")).strip()
    eval_variant = str(row.get("eval_variant", "")).strip()
    group_label = str(row.get("group_label", "")).strip()
    checkpoint = str(row.get("eval_checkpoint", "")).strip()
    decode = str(row.get("decode", "")).strip()
    schedule = str(row.get("schedule", "")).strip()
    is_baseline_run = run_name.startswith("baseline__") or schedule == "baseline"
    if is_baseline_run:
        model_role = "baseline"
        result_category = "external_baseline"
    elif eval_variant.lower().startswith("teacher") or group_label.lower().startswith("teacher"):
        model_role = "teacher"
        result_category = "teacher_baseline"
    elif eval_variant == "stage_a":
        model_role = "student"
        result_category = "student_stage_a"
    elif eval_variant == "stage_b":
        model_role = "student"
        result_category = "student_stage_b"
    elif eval_variant == "final":
        model_role = "student"
        result_category = "student_final"
    else:
        model_role = "student"
        result_category = "student_other"
    display_category = RESULT_CATEGORY_LABELS.get(result_category, result_category.replace("_", " ").title())
    label_parts = [display_category]
    if checkpoint:
        label_parts.append(checkpoint)
    if decode:
        label_parts.append(decode)
    display_label = " | ".join(label_parts)
    short_run_name = _short_run_name(run_name)
    chart_label = " | ".join(part for part in [display_category, short_run_name] if part)
    return {
        "model_role": model_role,
        "result_category": result_category,
        "display_category": display_category,
        "display_label": display_label,
        "short_run_name": short_run_name,
        "chart_label": chart_label,
    }


def _normalize_rows(rows: list[dict[str, str]], path_fields: set[str], repo_root: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        normalized: dict[str, str] = {}
        for key, value in row.items():
            if key in path_fields:
                normalized[key] = _normalize_path_text(str(value or ""), repo_root)
            else:
                normalized[key] = str(value or "")
        out.append(normalized)
    return out


def _infer_stage_b_eval_specs(rows: list[dict[str, Any]], repo_root: Path) -> list[tuple[str, Path]]:
    seen: dict[str, Path] = {}
    for row in rows:
        eval_name = str(row.get("eval_name", "")).strip()
        pairs = str(row.get("pairs", "")).strip()
        if not eval_name or not pairs:
            continue
        path = _resolve_repo_path(pairs, repo_root)
        if path.is_file():
            seen[eval_name] = path
    return sorted(seen.items(), key=lambda item: item[0])


def _backfill_stage_a_live_eval(manifest_path: Path, repo_root: Path) -> dict[str, Any]:
    out_dir = manifest_path.parent
    run_root = out_dir.parent
    rows = stage_a_matrix._read_manifest(manifest_path)
    pairs = _first_nonempty(rows, "pairs")
    eval_pairs = _resolve_repo_path(pairs, repo_root) if pairs else DEFAULT_EXTERNAL_EVAL
    if not eval_pairs.is_file():
        eval_pairs = DEFAULT_EXTERNAL_EVAL
    stage_a_matrix._write_live_eval_artifacts(
        out_dir,
        rows,
        repo_root=repo_root,
        run_root=run_root,
        eval_pairs=eval_pairs,
    )
    return {
        "manifest_path": _safe_rel(manifest_path, repo_root),
        "artifact_dir": _safe_rel(out_dir, repo_root),
        "kind": "stage_a_live_eval",
        "rows": len(rows),
    }


def _backfill_generic_manifest(manifest_path: Path, repo_root: Path) -> dict[str, Any] | None:
    if manifest_path.parent.name == "stage_a_live_eval":
        return None
    rows = stage_b_sweep._read_manifest(manifest_path)
    if not rows:
        return None
    decode_values = sorted({str(row.get("decode", "")).strip() for row in rows if str(row.get("decode", "")).strip()})
    if len(decode_values) != 1:
        return None
    eval_specs = _infer_stage_b_eval_specs(rows, repo_root)
    if not eval_specs:
        return None
    run_root_text = _first_nonempty(rows, "run_root")
    run_root = _resolve_repo_path(run_root_text, repo_root) if run_root_text else manifest_path.parent.parent
    stage_b_sweep._write_scoreboard(
        manifest_path.parent,
        rows,
        repo_root,
        run_root,
        decode_values[0],
        eval_specs,
    )
    return {
        "manifest_path": _safe_rel(manifest_path, repo_root),
        "artifact_dir": _safe_rel(manifest_path.parent, repo_root),
        "kind": "generic_manifest",
        "rows": len(rows),
        "decode": decode_values[0],
        "eval_count": len(eval_specs),
    }


def _infer_baseline_entry_from_compare(compare_path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(compare_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
    baseline_metadata = payload.get("baseline_metadata") if isinstance(payload.get("baseline_metadata"), dict) else {}
    source_langs = payload.get("source_langs") if isinstance(payload.get("source_langs"), list) else []
    target_langs = payload.get("target_langs") if isinstance(payload.get("target_langs"), list) else []
    pairs = str(payload.get("pairs", "")).strip()
    model_id = str(provenance.get("model_id", "")).strip() or str(((payload.get("student") or {}).get("model", ""))).strip()
    if not model_id:
        return None
    return {
        "model_id": model_id,
        "display_name": str(baseline_metadata.get("display_name", "")).strip(),
        "arch": str(provenance.get("arch", "")).strip(),
        "execution_mode": str(provenance.get("execution_mode", "")).strip(),
        "prompt_adapter": str(provenance.get("adapter_name", "")).strip(),
        "directions": [str(x) for x in (baseline_metadata.get("directions") or []) if str(x).strip()],
        "params": str(baseline_metadata.get("params", "")).strip(),
        "license": str(baseline_metadata.get("license", "")).strip(),
        "revision": str(provenance.get("model_revision", "")).strip(),
        "tokenizer_id": str(provenance.get("tokenizer_id", "")).strip(),
        "tokenizer_revision": str(provenance.get("tokenizer_revision", "")).strip(),
        "quality_tier": baseline_metadata.get("quality_tier", ""),
        "runtime_device": str(provenance.get("runtime_device", "")).strip(),
        "dtype": str(provenance.get("dtype", "")).strip(),
        "source_langs": [str(x) for x in source_langs if str(x).strip()],
        "target_langs": [str(x) for x in target_langs if str(x).strip()],
        "pairs": pairs,
    }


def _write_missing_baseline_manifest(run_root: Path, compare_paths: list[Path]) -> Path | None:
    manifest_path = run_root / "baseline_manifest.json"
    if manifest_path.is_file() or not compare_paths:
        return manifest_path if manifest_path.is_file() else None
    inferred = _infer_baseline_entry_from_compare(compare_paths[0])
    if inferred is None:
        return None
    eval_dataset_paths = []
    for compare_path in compare_paths:
        item = _infer_baseline_entry_from_compare(compare_path)
        if item is None:
            continue
        pairs = str(item.get("pairs", "")).strip()
        if pairs and pairs not in eval_dataset_paths:
            eval_dataset_paths.append(pairs)
    timestamp = 0.0
    candidates = [run_root / "run_contract.txt", *compare_paths]
    for path in candidates:
        try:
            timestamp = max(timestamp, float(path.stat().st_mtime))
        except Exception:
            continue
    quality_tier = inferred.get("quality_tier", "")
    try:
        quality_tier = int(quality_tier)
    except Exception:
        quality_tier = ""
    manifest = {
        "baseline": True,
        "model_id": inferred["model_id"],
        "display_name": inferred["display_name"],
        "arch": inferred["arch"],
        "execution_mode": inferred["execution_mode"],
        "prompt_adapter": inferred["prompt_adapter"],
        "directions": list(inferred.get("directions", [])),
        "params": inferred["params"],
        "license": inferred["license"],
        "revision": inferred["revision"],
        "tokenizer_id": inferred["tokenizer_id"],
        "tokenizer_revision": inferred["tokenizer_revision"],
        "quality_tier": quality_tier,
        "timestamp": timestamp,
        "eval_dataset_paths": eval_dataset_paths,
        "source_langs": inferred["source_langs"],
        "target_langs": inferred["target_langs"],
        "runtime_device": inferred["runtime_device"],
        "dtype": inferred["dtype"],
    }
    if not manifest["directions"]:
        for src in inferred["source_langs"]:
            for tgt in inferred["target_langs"]:
                if src and tgt and src != tgt:
                    manifest["directions"].append(f"{src}-{tgt}")
    manifest["directions"] = sorted(set(manifest["directions"]))
    _write_json(manifest_path, manifest)
    return manifest_path


def _backfill_legacy_baseline_run(run_root: Path, repo_root: Path) -> dict[str, Any] | None:
    if not run_root.is_dir() or not run_root.name.startswith("baseline__"):
        return None
    sweep_dir = run_root / "baseline_checkpoint_sweep_greedy"
    manifest_path = sweep_dir / "manifest.jsonl"
    if manifest_path.is_file():
        return None
    compare_paths = sorted(
        path for path in run_root.glob("*__greedy/compare_eval_summary.json")
        if path.is_file()
    )
    if not compare_paths:
        return None
    _write_missing_baseline_manifest(run_root, compare_paths)
    manifest_rows: list[dict[str, Any]] = []
    eval_specs: list[tuple[str, Path]] = []
    for compare_path in compare_paths:
        try:
            payload = json.loads(compare_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        eval_dir = compare_path.parent
        eval_name = eval_dir.name.split("__", 1)[0]
        pairs = str(payload.get("pairs", "")).strip()
        if not pairs:
            continue
        pairs_path = _resolve_repo_path(pairs, repo_root)
        if pairs_path.is_file():
            spec = (eval_name, pairs_path)
            if spec not in eval_specs:
                eval_specs.append(spec)
        student = payload.get("student") if isinstance(payload.get("student"), dict) else {}
        metrics = student.get("metrics_overall") if isinstance(student.get("metrics_overall"), dict) else {}
        manifest_rows.append(
            {
                "checkpoint_name": "final",
                "checkpoint_step": 0,
                "checkpoint_path": "",
                "compare_summary": str(compare_path),
                "decode": str((payload.get("decode_metadata") or {}).get("decode_mode", "greedy") or "greedy"),
                "duration_s": "",
                "eval_name": eval_name,
                "log_path": "",
                "out_dir": str(eval_dir),
                "pairs": pairs,
                "run_root": str(run_root),
                "runtime_device": str((payload.get("provenance") or {}).get("runtime_device", "")),
                "samples": payload.get("eval_samples", metrics.get("n", "")),
                "status": 0,
                "student_predictions": str((((student.get("predictions") or {}).get("path", "")) if isinstance(student.get("predictions"), dict) else "")),
                "timestamp_utc": _now_utc(),
                "bleu": ((metrics.get("bleu") or {}).get("score")) if isinstance(metrics, dict) else "",
                "chrf": ((metrics.get("chrf") or {}).get("score")) if isinstance(metrics, dict) else "",
            }
        )
    if not manifest_rows or not eval_specs:
        return None
    sweep_dir.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as fh:
        for row in manifest_rows:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")
    stage_b_sweep._write_scoreboard(
        sweep_dir,
        manifest_rows,
        repo_root,
        run_root,
        "greedy",
        eval_specs,
    )
    return {
        "manifest_path": _safe_rel(manifest_path, repo_root),
        "artifact_dir": _safe_rel(sweep_dir, repo_root),
        "kind": "legacy_baseline_backfill",
        "rows": len(manifest_rows),
        "eval_count": len(eval_specs),
    }


def _rebuild_run_index(python_bin: Path, repo_root: Path) -> None:
    cmd = [
        str(python_bin),
        str(repo_root / "projects" / "distillation" / "translation" / "pipeline" / "build_run_index.py"),
    ]
    proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "build_run_index.py failed\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )


def _best_external_by_run(compare_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ext_key = f"{build_run_index.EXTERNAL_WMT13_LABEL}_bleu"
    ext_chrf_key = f"{build_run_index.EXTERNAL_WMT13_LABEL}_chrf"
    ind_key = f"{build_run_index.INDOMAIN_CLEAN_LABEL}_bleu"
    best: dict[str, dict[str, str]] = {}
    for row in compare_rows:
        ext_bleu = _as_float(row.get(ext_key))
        if ext_bleu is None:
            continue
        run_name = str(row.get("run_name", ""))
        metadata = _compare_row_metadata(row)
        current = best.get(run_name)
        current_score = _as_float(current.get("external_bleu")) if current else None
        if current is None or current_score is None or ext_bleu > current_score:
            best[run_name] = {
                "run_name": run_name,
                "run_status": str(row.get("run_status", "")),
                "dataset_label": _dataset_label(row),
                "pair_count": _infer_pair_count(row),
                "pairs_input_spec": str(row.get("pairs_input_spec", "")),
                "schedule": str(row.get("schedule", "")),
                "group_label": str(row.get("group_label", "")),
                "eval_variant": str(row.get("eval_variant", "")),
                "eval_checkpoint": str(row.get("eval_checkpoint", "")),
                "decode": str(row.get("decode", "")),
                "external_bleu": _fmt_float(ext_bleu),
                "external_chrf": _fmt_float(row.get(ext_chrf_key)),
                "indomain_bleu": _fmt_float(row.get(ind_key)),
                "evaluated_model": str(row.get("evaluated_model", "")),
                "model_role": metadata["model_role"],
                "result_category": metadata["result_category"],
                "display_category": metadata["display_category"],
                "display_label": metadata["display_label"],
                "short_run_name": metadata["short_run_name"],
                "chart_label": metadata["chart_label"],
            }
    rows = list(best.values())
    rows.sort(key=lambda row: (_as_float(row.get("external_bleu")) or -1e9, row.get("run_name", "")), reverse=True)
    return rows


def _paired_external_vs_indomain(compare_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ext_key = f"{build_run_index.EXTERNAL_WMT13_LABEL}_bleu"
    ind_key = f"{build_run_index.INDOMAIN_CLEAN_LABEL}_bleu"
    out: list[dict[str, str]] = []
    for row in compare_rows:
        ext_bleu = _as_float(row.get(ext_key))
        ind_bleu = _as_float(row.get(ind_key))
        if ext_bleu is None or ind_bleu is None:
            continue
        metadata = _compare_row_metadata(row)
        out.append(
            {
                "run_name": str(row.get("run_name", "")),
                "dataset_label": _dataset_label(row),
                "pair_count": _infer_pair_count(row),
                "group_label": str(row.get("group_label", "")),
                "eval_variant": str(row.get("eval_variant", "")),
                "eval_checkpoint": str(row.get("eval_checkpoint", "")),
                "decode": str(row.get("decode", "")),
                "external_bleu": _fmt_float(ext_bleu),
                "indomain_bleu": _fmt_float(ind_bleu),
                "model_role": metadata["model_role"],
                "result_category": metadata["result_category"],
                "display_category": metadata["display_category"],
                "display_label": metadata["display_label"],
            }
        )
    out.sort(key=lambda row: ((_as_float(row.get("external_bleu")) or -1e9), row.get("run_name", "")), reverse=True)
    return out


def _label_eval_set(pairs_text: str) -> str:
    raw = str(pairs_text or "").strip()
    if not raw:
        return ""
    stem = Path(raw).name
    for spec in build_run_index.DATASET_SPECS:
        aliases = tuple(str(alias) for alias in spec.get("aliases", ()))
        if raw == spec.get("label") or stem == spec.get("label"):
            return str(spec.get("label", ""))
        for alias in aliases:
            if raw == alias or stem == alias or alias in raw:
                return str(spec.get("label", ""))
    return stem or raw


def _leaderboard_model_role(eval_dir: str, run_name: str = "") -> str:
    text = str(eval_dir or "").lower()
    rn = str(run_name or "").lower()
    if rn.startswith("baseline__"):
        return "baseline"
    if "teacher4b" in text or "/teacher" in text or "__teacher" in text:
        return "teacher_baseline"
    return "student"


def _canonical_compare_relpath(path: Path, runs_root: Path) -> str:
    rel = path.relative_to(runs_root)
    parts = list(rel.parts)
    if len(parts) >= 2 and re.fullmatch(r"attempt_\d+_.+", parts[-2]):
        parts.pop(-2)
    return str(Path(*parts))


def _raw_compare_leaderboard_rows(runs_root: Path, repo_root: Path) -> list[dict[str, str]]:
    rows_by_key: dict[tuple[str, ...], dict[str, str]] = {}
    for compare_path in sorted(runs_root.rglob("compare_eval_summary.json")):
        try:
            payload = json.loads(compare_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        pairs = str(payload.get("pairs", "")).strip()
        if not pairs:
            continue
        student_metrics = (payload.get("student") or {}).get("metrics_overall") or {}
        teacher_metrics = (payload.get("teacher") or {}).get("metrics_overall") or {}
        student_bleu = _as_float((student_metrics.get("bleu") or {}).get("score"))
        student_chrf = _as_float((student_metrics.get("chrf") or {}).get("score"))
        if student_bleu is None:
            continue
        canonical_rel = _canonical_compare_relpath(compare_path, runs_root)
        canonical_path = runs_root / canonical_rel
        rel_parts = Path(canonical_rel).parts
        if len(rel_parts) < 2:
            continue
        run_name = rel_parts[0]
        eval_dir = "/".join(rel_parts[1:-1])
        row = {
            "run_name": run_name,
            "eval_set": _label_eval_set(pairs),
            "pairs": _normalize_path_text(pairs, repo_root),
            "eval_dir": eval_dir,
            "model_role": _leaderboard_model_role(eval_dir, run_name),
            "student_bleu": _fmt_float(student_bleu),
            "student_chrf": _fmt_float(student_chrf),
            "teacher_bleu": _fmt_float((teacher_metrics.get("bleu") or {}).get("score")),
            "teacher_chrf": _fmt_float((teacher_metrics.get("chrf") or {}).get("score")),
            "delta_bleu": _fmt_float(((payload.get("delta") or {}).get("bleu"))),
            "delta_chrf": _fmt_float(((payload.get("delta") or {}).get("chrf"))),
            "student_model": _normalize_path_text(str((payload.get("student") or {}).get("model", "")), repo_root),
            "teacher_model": _normalize_path_text(str((payload.get("teacher") or {}).get("model", "")), repo_root),
            "eval_samples": str(payload.get("eval_samples", "")),
            "compare_summary_path": _safe_rel(canonical_path, repo_root),
        }
        # Add per-direction metrics and provenance if available.
        direction_metrics = payload.get("direction_metrics") or {}
        for dk in ("en_es_bleu", "en_es_chrf", "en_es_comet", "en_es_sample_count",
                    "es_en_bleu", "es_en_chrf", "es_en_comet", "es_en_sample_count",
                    "total_sample_count"):
            val = direction_metrics.get(dk)
            row[dk] = _fmt_float(val) if isinstance(val, (int, float)) else ""
        provenance = payload.get("provenance") or {}
        row["execution_mode"] = str(provenance.get("execution_mode", ""))
        row["arch"] = str(provenance.get("arch", ""))
        row["comet_available"] = str(provenance.get("comet_available", "")).lower()
        baseline_meta = payload.get("baseline_metadata") or {}
        row["is_baseline"] = str(baseline_meta.get("is_baseline", False)).lower()
        row["display_name"] = str(baseline_meta.get("display_name", ""))
        row["quality_tier"] = str(baseline_meta.get("quality_tier", ""))
        row["params"] = str(baseline_meta.get("params", ""))
        key = (
            row["run_name"],
            row["eval_set"],
            row["eval_dir"],
            row["student_model"],
            row["student_bleu"],
            row["student_chrf"],
        )
        rows_by_key[key] = row
    rows = list(rows_by_key.values())
    rows.sort(
        key=lambda row: (
            row.get("eval_set", ""),
            -(_as_float(row.get("student_bleu")) or -1e9),
            -(_as_float(row.get("student_chrf")) or -1e9),
            row.get("run_name", ""),
            row.get("eval_dir", ""),
        )
    )
    return rows


def _leaderboard_rows_for_eval(rows: list[dict[str, str]], eval_set: str) -> list[dict[str, str]]:
    filtered = [row for row in rows if str(row.get("eval_set", "")) == eval_set]
    filtered.sort(
        key=lambda row: (
            -(_as_float(row.get("student_bleu")) or -1e9),
            -(_as_float(row.get("student_chrf")) or -1e9),
            row.get("run_name", ""),
            row.get("eval_dir", ""),
        )
    )
    return filtered


def _grid_checkpoint_rows(compare_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ext_key = f"{build_run_index.EXTERNAL_WMT13_LABEL}_bleu"
    out: list[dict[str, str]] = []
    for row in compare_rows:
        run_name = str(row.get("run_name", ""))
        if "stagea_cpu_subset" not in run_name:
            continue
        ext_bleu = _as_float(row.get(ext_key))
        checkpoint = str(row.get("eval_checkpoint", ""))
        step = _checkpoint_step(checkpoint)
        if ext_bleu is None or step < 0:
            continue
        pair_count = _as_int(_infer_pair_count(row))
        label = f"{pair_count or '?'} rows"
        out.append(
            {
                "run_name": run_name,
                "series_label": label,
                "pair_count": str(pair_count or ""),
                "checkpoint_step": str(step),
                "checkpoint_name": checkpoint,
                "external_bleu": _fmt_float(ext_bleu),
            }
        )
    out.sort(key=lambda row: (_as_int(row.get("pair_count")) or -1, _as_int(row.get("checkpoint_step")) or -1))
    return out


def _svg_bar_chart(items: list[dict[str, str]], *, label_key: str, value_key: str, title: str, max_items: int = 12) -> str:
    rows = items[:max_items]
    width = 900
    left = 280
    right = 40
    top = 40
    bar_h = 24
    gap = 12
    chart_w = width - left - right
    height = top + max(1, len(rows)) * (bar_h + gap) + 30
    max_value = max((_as_float(row.get(value_key)) or 0.0) for row in rows) if rows else 1.0
    max_value = max(max_value, 1.0)
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="auto" role="img" aria-label="{html.escape(title)}">',
        f'<text x="{left}" y="24" font-size="18" font-family="monospace" text-anchor="middle">{html.escape(title)}</text>',
    ]
    for idx, row in enumerate(rows):
        y = top + idx * (bar_h + gap)
        label = str(row.get(label_key, ""))
        value = _as_float(row.get(value_key)) or 0.0
        bar_w = 0 if max_value <= 0 else (value / max_value) * chart_w
        color = BAR_COLORS[idx % len(BAR_COLORS)]
        parts.append(
            f'<text x="{left - 8}" y="{y + 17}" font-size="12" font-family="monospace" text-anchor="end">{html.escape(label[:40])}</text>'
        )
        parts.append(
            f'<rect x="{left}" y="{y}" width="{bar_w:.2f}" height="{bar_h}" fill="{color}" opacity="0.85" />'
        )
        parts.append(
            f'<text x="{left + bar_w + 8:.2f}" y="{y + 17}" font-size="12" font-family="monospace">{html.escape(_fmt_float(value))}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def _svg_scatter(points: list[dict[str, str]], *, title: str) -> str:
    width = 760
    height = 480
    left = 70
    right = 30
    top = 40
    bottom = 50
    plot_w = width - left - right
    plot_h = height - top - bottom
    xs = [_as_float(row.get("external_bleu")) for row in points]
    ys = [_as_float(row.get("indomain_bleu")) for row in points]
    xs = [value for value in xs if value is not None]
    ys = [value for value in ys if value is not None]
    x_max = max(xs) if xs else 1.0
    y_max = max(ys) if ys else 1.0
    x_max = max(x_max, 1.0)
    y_max = max(y_max, 1.0)
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="auto" role="img" aria-label="{html.escape(title)}">',
        f'<text x="{width / 2:.1f}" y="24" font-size="18" font-family="monospace" text-anchor="middle">{html.escape(title)}</text>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#444" />',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#444" />',
        f'<text x="{left + plot_w / 2:.1f}" y="{height - 12}" font-size="12" font-family="monospace" text-anchor="middle">external BLEU</text>',
        f'<text x="16" y="{top + plot_h / 2:.1f}" font-size="12" font-family="monospace" transform="rotate(-90 16,{top + plot_h / 2:.1f})" text-anchor="middle">indomain BLEU</text>',
    ]
    for idx, row in enumerate(points[:80]):
        x = _as_float(row.get("external_bleu"))
        y = _as_float(row.get("indomain_bleu"))
        if x is None or y is None:
            continue
        px = left + (x / x_max) * plot_w
        py = top + plot_h - (y / y_max) * plot_h
        color = BAR_COLORS[idx % len(BAR_COLORS)]
        label = f"{row.get('run_name', '')} | {row.get('display_label', '')}".strip(" |")
        parts.append(
            f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4.5" fill="{color}"><title>{html.escape(label)} | ext={_fmt_float(x)} ind={_fmt_float(y)}</title></circle>'
        )
    for tick in range(0, 6):
        x_val = x_max * tick / 5
        y_val = y_max * tick / 5
        tx = left + plot_w * tick / 5
        ty = top + plot_h - plot_h * tick / 5
        parts.append(f'<text x="{tx:.2f}" y="{top + plot_h + 18}" font-size="10" font-family="monospace" text-anchor="middle">{_fmt_float(x_val, 1)}</text>')
        parts.append(f'<text x="{left - 8}" y="{ty + 4:.2f}" font-size="10" font-family="monospace" text-anchor="end">{_fmt_float(y_val, 1)}</text>')
        parts.append(f'<line x1="{tx:.2f}" y1="{top}" x2="{tx:.2f}" y2="{top + plot_h}" stroke="#ddd" />')
        parts.append(f'<line x1="{left}" y1="{ty:.2f}" x2="{left + plot_w}" y2="{ty:.2f}" stroke="#ddd" />')
    parts.append("</svg>")
    return "\n".join(parts)


def _svg_line_chart(grid_rows: list[dict[str, str]], *, title: str) -> str:
    width = 920
    height = 520
    left = 70
    right = 30
    top = 40
    bottom = 60
    plot_w = width - left - right
    plot_h = height - top - bottom
    by_series: dict[str, list[tuple[int, float, str]]] = {}
    max_x = 1
    max_y = 1.0
    for row in grid_rows:
        label = str(row.get("series_label", ""))
        step = _as_int(row.get("checkpoint_step"))
        bleu = _as_float(row.get("external_bleu"))
        checkpoint = str(row.get("checkpoint_name", ""))
        if not label or step is None or bleu is None:
            continue
        by_series.setdefault(label, []).append((step, bleu, checkpoint))
        max_x = max(max_x, step)
        max_y = max(max_y, bleu)
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="auto" role="img" aria-label="{html.escape(title)}">',
        f'<text x="{width / 2:.1f}" y="24" font-size="18" font-family="monospace" text-anchor="middle">{html.escape(title)}</text>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#444" />',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#444" />',
        f'<text x="{left + plot_w / 2:.1f}" y="{height - 12}" font-size="12" font-family="monospace" text-anchor="middle">checkpoint step</text>',
        f'<text x="16" y="{top + plot_h / 2:.1f}" font-size="12" font-family="monospace" transform="rotate(-90 16,{top + plot_h / 2:.1f})" text-anchor="middle">external BLEU</text>',
    ]
    for tick in range(0, 5):
        x_val = max_x * tick / 4
        tx = left + plot_w * tick / 4
        parts.append(f'<text x="{tx:.2f}" y="{top + plot_h + 18}" font-size="10" font-family="monospace" text-anchor="middle">{int(x_val)}</text>')
        parts.append(f'<line x1="{tx:.2f}" y1="{top}" x2="{tx:.2f}" y2="{top + plot_h}" stroke="#ddd" />')
    for tick in range(0, 6):
        y_val = max_y * tick / 5
        ty = top + plot_h - plot_h * tick / 5
        parts.append(f'<text x="{left - 8}" y="{ty + 4:.2f}" font-size="10" font-family="monospace" text-anchor="end">{_fmt_float(y_val, 1)}</text>')
        parts.append(f'<line x1="{left}" y1="{ty:.2f}" x2="{left + plot_w}" y2="{ty:.2f}" stroke="#ddd" />')
    legend_y = top
    for idx, (label, points) in enumerate(sorted(by_series.items())):
        color = BAR_COLORS[idx % len(BAR_COLORS)]
        points.sort(key=lambda item: item[0])
        coords = []
        for step, bleu, checkpoint in points:
            px = left + (step / max_x) * plot_w
            py = top + plot_h - (bleu / max_y) * plot_h
            coords.append((px, py, checkpoint, bleu))
        if len(coords) >= 2:
            parts.append(
                '<polyline fill="none" stroke="{color}" stroke-width="2" points="{points}" />'.format(
                    color=color,
                    points=" ".join(f"{px:.2f},{py:.2f}" for px, py, _, _ in coords),
                )
            )
        for px, py, checkpoint, bleu in coords:
            parts.append(
                f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4" fill="{color}"><title>{html.escape(label)} {html.escape(checkpoint)} BLEU={_fmt_float(bleu)}</title></circle>'
            )
        parts.append(f'<rect x="{width - 220}" y="{legend_y - 10}" width="14" height="14" fill="{color}" />')
        parts.append(f'<text x="{width - 200}" y="{legend_y + 2}" font-size="12" font-family="monospace">{html.escape(label)}</text>')
        legend_y += 22
    parts.append("</svg>")
    return "\n".join(parts)


def _html_table(rows: list[dict[str, str]], columns: list[tuple[str, str]], limit: int = 12) -> str:
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body_rows = []
    for row in rows[:limit]:
        body_rows.append(
            "<tr>"
            + "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>" for key, _ in columns)
            + "</tr>"
        )
    body = "\n".join(body_rows) if body_rows else '<tr><td colspan="{n}">no rows</td></tr>'.format(n=len(columns))
    return (
        '<table class="grid-table"><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + body
        + "</tbody></table>"
    )


def _render_dashboard(
    out_path: Path,
    *,
    summary: dict[str, Any],
    best_rows: list[dict[str, str]],
    scatter_rows: list[dict[str, str]],
    grid_rows: list[dict[str, str]],
    active_runs: list[dict[str, str]],
) -> None:
    cards = [
        ("Runs", str(summary.get("run_rows", 0))),
        ("Evals", str(summary.get("eval_rows", 0))),
        ("Compare Rows", str(summary.get("compare_rows", 0))),
        ("Backfilled", str(summary.get("backfilled_artifact_dirs", 0))),
    ]
    card_html = "".join(
        f'<div class="card"><div class="card-label">{html.escape(label)}</div><div class="card-value">{html.escape(value)}</div></div>'
        for label, value in cards
    )
    best_chart = _svg_bar_chart(best_rows, label_key="chart_label", value_key="external_bleu", title="Best External BLEU Rows by Run")
    scatter_chart = _svg_scatter(scatter_rows, title="External vs Indomain BLEU")
    grid_chart = _svg_line_chart(grid_rows, title="Grid External BLEU by Checkpoint")
    best_table = _html_table(
        best_rows,
        [
            ("run_name", "run"),
            ("dataset_label", "dataset"),
            ("display_category", "category"),
            ("display_label", "top_row"),
            ("external_bleu", "best_external_bleu"),
            ("indomain_bleu", "indomain_bleu"),
            ("eval_checkpoint", "checkpoint"),
            ("pair_count", "pair_count"),
        ],
    )
    active_table = _html_table(
        active_runs,
        [
            ("run_name", "run"),
            ("run_status", "status"),
            ("dataset_label", "dataset"),
            ("pair_count", "pair_count"),
            ("pairs_input_spec", "pairs_input"),
        ],
        limit=20,
    )
    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Translation Results Bundle</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      --bg: #f6f1e8;
      --panel: #fffdfa;
      --ink: #1f2329;
      --muted: #5f6b76;
      --line: #d9d1c4;
      --accent: #1f77b4;
    }}
    body {{
      margin: 0;
      padding: 24px;
      background: linear-gradient(180deg, #efe6d6 0%, var(--bg) 24%, #faf7f1 100%);
      color: var(--ink);
      font: 14px/1.45 "Iosevka", "Menlo", "Consolas", monospace;
    }}
    .wrap {{
      max-width: 1280px;
      margin: 0 auto;
    }}
    h1, h2 {{
      margin: 0 0 12px;
      font-weight: 700;
    }}
    .sub {{
      color: var(--muted);
      margin-bottom: 20px;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .card, .panel {{
      background: rgba(255, 253, 250, 0.88);
      border: 1px solid var(--line);
      border-radius: 14px;
      box-shadow: 0 8px 24px rgba(31, 35, 41, 0.05);
    }}
    .card {{
      padding: 14px 16px;
    }}
    .card-label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .card-value {{
      font-size: 28px;
      margin-top: 6px;
    }}
    .panel {{
      padding: 18px;
      margin-bottom: 18px;
    }}
    .grid-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    .grid-table th, .grid-table td {{
      border-top: 1px solid var(--line);
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }}
    .grid-table th {{
      color: var(--muted);
      font-weight: 600;
      border-top: 0;
    }}
    .two {{
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 18px;
    }}
    @media (max-width: 980px) {{
      .two {{
        grid-template-columns: 1fr;
      }}
    }}
    code {{
      background: #f1eadf;
      padding: 1px 5px;
      border-radius: 5px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Translation Results Bundle</h1>
    <div class="sub">Generated: {html.escape(str(summary.get("generated_utc", "")))} | Re-run safe | Source-of-truth rebuilt from manifests + canonical run index</div>
    <div class="cards">{card_html}</div>
    <div class="panel">
      {best_chart}
    </div>
    <div class="two">
      <div class="panel">
        {scatter_chart}
      </div>
      <div class="panel">
        <h2>Best External Rows</h2>
        {best_table}
      </div>
    </div>
    <div class="two">
      <div class="panel">
        {grid_chart}
      </div>
      <div class="panel">
        <h2>Active / Incomplete Runs</h2>
        {active_table}
      </div>
    </div>
    <div class="panel">
      <h2>Bundle Files</h2>
      <p>
        <code>runs.csv</code>,
        <code>evals.csv</code>,
        <code>compare.csv</code>,
        <code>best_external_by_run.csv</code>,
        <code>external_vs_indomain.csv</code>,
        <code>grid_checkpoint_timeline.csv</code>,
        <code>leaderboard_all_compare_rows.csv</code>,
        <code>leaderboard.md</code>,
        <code>summary.md</code>,
        <code>summary.json</code>
      </p>
    </div>
  </div>
</body>
</html>
"""
    out_path.write_text(html_text, encoding="utf-8")


def _write_summary_md(
    out_path: Path,
    *,
    summary: dict[str, Any],
    best_rows: list[dict[str, str]],
    backfilled: list[dict[str, Any]],
    leaderboard_rows: list[dict[str, str]],
) -> None:
    lines = [
        "# Translation Results Bundle",
        "",
        f"Generated: {summary['generated_utc']}",
        "",
        "## Counts",
        "",
        f"- runs: {summary['run_rows']}",
        f"- eval rows: {summary['eval_rows']}",
        f"- compare rows: {summary['compare_rows']}",
        f"- manifests scanned: {summary['manifest_count']}",
        f"- artifact dirs backfilled: {summary['backfilled_artifact_dirs']}",
        "",
        "## Best External BLEU Rows by Run",
        "",
        "| run | dataset | category | top_row | best_external_bleu | indomain_bleu | checkpoint | pair_count |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in best_rows[:12]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_escape(row.get("run_name", "")),
                    _md_escape(row.get("dataset_label", "")),
                    _md_escape(row.get("display_category", "")),
                    _md_escape(row.get("display_label", "")),
                    _md_escape(row.get("external_bleu", "")),
                    _md_escape(row.get("indomain_bleu", "")),
                    _md_escape(row.get("eval_checkpoint", "")),
                    _md_escape(row.get("pair_count", "")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Deduped Eval Leaderboards",
            "",
            "- `leaderboard_all_compare_rows.csv`",
            "- `leaderboard_external_wmt13_en_es_translation_benchmark_128.csv`",
            "- `leaderboard_indomain_clean_merged_en_es_translation_benchmark_128.csv`",
            "- `leaderboard.md`",
            "",
            "### External WMT13 EN/ES 128",
            "",
            "| rank | student_bleu | student_chrf | role | run | eval_dir |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    external_rows = _leaderboard_rows_for_eval(leaderboard_rows, build_run_index.EXTERNAL_WMT13_LABEL)
    for index, row in enumerate(external_rows[:15], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _md_escape(row.get("student_bleu", "")),
                    _md_escape(row.get("student_chrf", "")),
                    _md_escape(row.get("model_role", "")),
                    _md_escape(row.get("run_name", "")),
                    _md_escape(row.get("eval_dir", "")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "### In-Domain Clean EN/ES 128",
            "",
            "| rank | student_bleu | student_chrf | role | run | eval_dir |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    indomain_rows = _leaderboard_rows_for_eval(leaderboard_rows, build_run_index.INDOMAIN_CLEAN_LABEL)
    for index, row in enumerate(indomain_rows[:15], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _md_escape(row.get("student_bleu", "")),
                    _md_escape(row.get("student_chrf", "")),
                    _md_escape(row.get("model_role", "")),
                    _md_escape(row.get("run_name", "")),
                    _md_escape(row.get("eval_dir", "")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Backfilled Artifact Dirs",
            "",
        ]
    )
    if backfilled:
        lines.append("| kind | artifact_dir | rows |")
        lines.append("| --- | --- | --- |")
        for item in backfilled:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_escape(item.get("kind", "")),
                        _md_escape(item.get("artifact_dir", "")),
                        _md_escape(item.get("rows", "")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("_No artifact dirs required backfill._")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Rebuild a cohesive translation-results bundle from existing artifacts.")
    ap.add_argument("--runs-root", default=str(DEFAULT_RUNS_ROOT))
    ap.add_argument("--out-dir", default=str(DEFAULT_BUNDLE_DIR))
    ap.add_argument("--python-bin", default="")
    ap.add_argument("--skip-backfill", action="store_true")
    ap.add_argument("--skip-index", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = _parse_args()
    runs_root = _resolve_repo_path(str(args.runs_root), PROJECT_ROOT)
    out_dir = _resolve_repo_path(str(args.out_dir), PROJECT_ROOT)
    python_bin = (
        _resolve_repo_path(str(args.python_bin), PROJECT_ROOT)
        if str(args.python_bin).strip()
        else (PROJECT_ROOT / ".venv" / "bin" / "python")
    )
    if not python_bin.is_file():
        python_bin = Path(sys.executable)
    if not runs_root.is_dir():
        raise RuntimeError(f"runs root not found: {runs_root}")

    backfilled: list[dict[str, Any]] = []
    if not args.skip_backfill:
        for run_root in sorted(runs_root.glob("baseline__*")):
            item = _backfill_legacy_baseline_run(run_root, PROJECT_ROOT)
            if item is not None:
                backfilled.append(item)
    manifest_paths = sorted(runs_root.rglob("manifest.jsonl"))
    if not args.skip_backfill:
        for manifest_path in manifest_paths:
            if manifest_path.parent.name == "stage_a_live_eval":
                backfilled.append(_backfill_stage_a_live_eval(manifest_path, PROJECT_ROOT))
                continue
            item = _backfill_generic_manifest(manifest_path, PROJECT_ROOT)
            if item is not None:
                backfilled.append(item)

    if not args.skip_index:
        _rebuild_run_index(python_bin, PROJECT_ROOT)

    runs_csv = runs_root / "run_index_runs.csv"
    evals_csv = runs_root / "run_index_evals.csv"
    compare_csv = runs_root / "run_index_compare.csv"
    run_rows = _load_csv_rows(runs_csv)
    eval_rows = _load_csv_rows(evals_csv)
    compare_rows = _load_csv_rows(compare_csv)

    normalized_runs = _normalize_rows(
        run_rows,
        {
            "run_root",
            "eval_dataset_paths",
            "pairs_input_spec",
            "teacher_model",
            "student_model",
            "resume_from",
            "recommended_resume_from",
            "selected_checkpoint",
            "summary_path",
            "latest_stage_a_checkpoint",
            "latest_stage_b_checkpoint",
            "final_model",
        },
        PROJECT_ROOT,
    )
    normalized_runs = _annotate_dataset_labels(normalized_runs)
    normalized_evals = _normalize_rows(
        eval_rows,
        {
            "eval_dir_path",
            "pairs",
            "student_model",
            "predictions_path",
            "compare_summary_path",
        },
        PROJECT_ROOT,
    )
    normalized_compare = _normalize_rows(
        compare_rows,
        {
            "pairs_input_spec",
            "recommended_resume_from",
            "evaluated_model",
            f"{build_run_index.EXTERNAL_WMT13_LABEL}_pairs",
            f"{build_run_index.EXTERNAL_WMT13_LABEL}_eval_dir",
            f"{build_run_index.INDOMAIN_CLEAN_LABEL}_pairs",
            f"{build_run_index.INDOMAIN_CLEAN_LABEL}_eval_dir",
        },
        PROJECT_ROOT,
    )
    normalized_compare = _annotate_dataset_labels(normalized_compare)

    best_rows = _best_external_by_run(normalized_compare)
    scatter_rows = _paired_external_vs_indomain(normalized_compare)
    grid_rows = _grid_checkpoint_rows(normalized_compare)
    leaderboard_rows = _raw_compare_leaderboard_rows(runs_root, PROJECT_ROOT)
    active_runs = [row for row in normalized_runs if str(row.get("run_status", "")) != "completed"]
    active_runs.sort(key=lambda row: row.get("run_name", ""))

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "runs.csv", normalized_runs, list(normalized_runs[0].keys()) if normalized_runs else [])
    _write_csv(out_dir / "evals.csv", normalized_evals, list(normalized_evals[0].keys()) if normalized_evals else [])
    _write_csv(out_dir / "compare.csv", normalized_compare, list(normalized_compare[0].keys()) if normalized_compare else [])
    _write_csv(
        out_dir / "best_external_by_run.csv",
        best_rows,
        [
            "run_name",
            "run_status",
            "dataset_label",
            "model_role",
            "result_category",
            "display_category",
            "display_label",
            "short_run_name",
            "chart_label",
            "pair_count",
            "pairs_input_spec",
            "schedule",
            "group_label",
            "eval_variant",
            "eval_checkpoint",
            "decode",
            "external_bleu",
            "external_chrf",
            "indomain_bleu",
            "evaluated_model",
        ],
    )
    _write_csv(
        out_dir / "external_vs_indomain.csv",
        scatter_rows,
        [
            "run_name",
            "dataset_label",
            "pair_count",
            "group_label",
            "eval_variant",
            "eval_checkpoint",
            "decode",
            "external_bleu",
            "indomain_bleu",
        ],
    )
    _write_csv(
        out_dir / "grid_checkpoint_timeline.csv",
        grid_rows,
        [
            "run_name",
            "series_label",
            "pair_count",
            "checkpoint_step",
            "checkpoint_name",
            "external_bleu",
        ],
    )
    leaderboard_fields = [
        "run_name",
        "eval_set",
        "pairs",
        "eval_dir",
        "is_baseline",
        "display_name",
        "model_role",
        "student_bleu",
        "student_chrf",
        "teacher_bleu",
        "teacher_chrf",
        "delta_bleu",
        "delta_chrf",
        "student_model",
        "teacher_model",
        "eval_samples",
        "compare_summary_path",
        "en_es_bleu",
        "en_es_chrf",
        "en_es_comet",
        "en_es_sample_count",
        "es_en_bleu",
        "es_en_chrf",
        "es_en_comet",
        "es_en_sample_count",
        "total_sample_count",
        "execution_mode",
        "arch",
        "comet_available",
        "quality_tier",
        "params",
    ]
    _write_csv(out_dir / "leaderboard_all_compare_rows.csv", leaderboard_rows, leaderboard_fields)
    for eval_set, slug in LEADERBOARD_SLUGS.items():
        _write_csv(
            out_dir / f"leaderboard_{slug}.csv",
            _leaderboard_rows_for_eval(leaderboard_rows, eval_set),
            leaderboard_fields,
        )

    summary = {
        "generated_utc": _now_utc(),
        "runs_root": _safe_rel(runs_root, PROJECT_ROOT),
        "bundle_dir": _safe_rel(out_dir, PROJECT_ROOT),
        "manifest_count": len(manifest_paths),
        "backfilled_artifact_dirs": len(backfilled),
        "run_rows": len(normalized_runs),
        "eval_rows": len(normalized_evals),
        "compare_rows": len(normalized_compare),
        "best_external_rows": len(best_rows),
        "paired_external_indomain_rows": len(scatter_rows),
        "grid_checkpoint_rows": len(grid_rows),
        "leaderboard_rows": len(leaderboard_rows),
        "active_run_rows": len(active_runs),
        "python_bin": str(python_bin),
        "skip_backfill": bool(args.skip_backfill),
        "skip_index": bool(args.skip_index),
    }
    _write_json(out_dir / "summary.json", {"summary": summary, "backfilled": backfilled})
    leaderboard_md_lines = [
        "# Eval Leaderboards",
        "",
        f"Generated: {summary['generated_utc']}",
        "",
    ]
    for eval_set in sorted({row.get('eval_set', '') for row in leaderboard_rows if row.get('eval_set', '')}):
        leaderboard_md_lines.extend(
            [
                f"## {eval_set}",
                "",
                "| rank | student_bleu | student_chrf | teacher_bleu | teacher_chrf | delta_bleu | delta_chrf | role | run | eval_dir |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for index, row in enumerate(_leaderboard_rows_for_eval(leaderboard_rows, eval_set), start=1):
            leaderboard_md_lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        _md_escape(row.get("student_bleu", "")),
                        _md_escape(row.get("student_chrf", "")),
                        _md_escape(row.get("teacher_bleu", "")),
                        _md_escape(row.get("teacher_chrf", "")),
                        _md_escape(row.get("delta_bleu", "")),
                        _md_escape(row.get("delta_chrf", "")),
                        _md_escape(row.get("model_role", "")),
                        _md_escape(row.get("run_name", "")),
                        _md_escape(row.get("eval_dir", "")),
                    ]
                )
                + " |"
            )
        leaderboard_md_lines.append("")
    (out_dir / "leaderboard.md").write_text("\n".join(leaderboard_md_lines), encoding="utf-8")
    _write_summary_md(
        out_dir / "summary.md",
        summary=summary,
        best_rows=best_rows,
        backfilled=backfilled,
        leaderboard_rows=leaderboard_rows,
    )
    _render_dashboard(
        out_dir / "dashboard.html",
        summary=summary,
        best_rows=best_rows,
        scatter_rows=scatter_rows,
        grid_rows=grid_rows,
        active_runs=active_runs,
    )

    print(f"[bundle] generated: {summary['generated_utc']}")
    print(f"[bundle] out_dir={_safe_rel(out_dir, PROJECT_ROOT)}")
    print(f"[bundle] backfilled_artifact_dirs={summary['backfilled_artifact_dirs']}")
    print(f"[bundle] run_rows={summary['run_rows']} eval_rows={summary['eval_rows']} compare_rows={summary['compare_rows']}")
    print(f"[bundle] dashboard={_safe_rel(out_dir / 'dashboard.html', PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
