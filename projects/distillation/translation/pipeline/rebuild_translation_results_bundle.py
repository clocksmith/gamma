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
    model_role = "teacher" if eval_variant.lower().startswith("teacher") or group_label.lower().startswith("teacher") else "student"
    if model_role == "teacher":
        result_category = "teacher_baseline"
    elif eval_variant == "stage_a":
        result_category = "student_stage_a"
    elif eval_variant == "stage_b":
        result_category = "student_stage_b"
    elif eval_variant == "final":
        result_category = "student_final"
    else:
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
        "active_run_rows": len(active_runs),
        "python_bin": str(python_bin),
        "skip_backfill": bool(args.skip_backfill),
        "skip_index": bool(args.skip_index),
    }
    _write_json(out_dir / "summary.json", {"summary": summary, "backfilled": backfilled})
    _write_summary_md(out_dir / "summary.md", summary=summary, best_rows=best_rows, backfilled=backfilled)
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
