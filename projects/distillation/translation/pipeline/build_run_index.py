#!/usr/bin/env python3
"""Build a compact index of translation distillation runs and eval results."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any


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
        if not summary_path.is_file():
            continue
        summary = _read_json(summary_path)
        if not summary:
            continue
        rows.append(
            {
                "run_name": child.name,
                "summary_path": _safe_rel(summary_path, repo_root),
                "timestamp_epoch": float(summary.get("timestamp", -1.0) or -1.0),
                "timestamp_utc": _fmt_ts(summary.get("timestamp")),
                "schedule": str(summary.get("schedule", "")),
                "pair_count": _fmt_int(summary.get("pair_count")),
                "pairs_input_spec": str(summary.get("pairs_input_spec", "")),
                "source_langs": ",".join(summary.get("source_langs", []) or []),
                "target_langs": ",".join(summary.get("target_langs", []) or []),
                "total_steps": _fmt_int(summary.get("total_steps")),
                "sft_steps": _fmt_int(summary.get("sft_steps")),
                "distill_steps": _fmt_int(summary.get("distill_steps")),
                "lambda_kd": _fmt_float(summary.get("lambda_kd")),
                "mu_triplet": _fmt_float(summary.get("mu_triplet")),
                "resumed": str(bool(summary.get("resumed", False))).lower(),
                "resume_stage": str(summary.get("resume_stage", "")),
                "resume_from": str(summary.get("resume_from", "")),
                "selected_checkpoint": str(summary.get("selected_checkpoint", "")),
                "selected_checkpoint_stage": str(summary.get("selected_checkpoint_stage", "")),
                "selected_checkpoint_loss": _fmt_float(summary.get("selected_checkpoint_loss")),
            }
        )
    rows.sort(key=_run_sort_key, reverse=True)
    return rows


def _decode_from_path(path: Path) -> str:
    for part in path.parts:
        if "__greedy" in part:
            return "greedy"
        if "__sampled" in part:
            return "sampled"
    return ""


def collect_eval_rows(runs_root: Path, repo_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[Path] = set()
    for compare_path in runs_root.rglob("compare_eval_summary.json"):
        try:
            resolved = compare_path.resolve()
        except Exception:
            resolved = compare_path
        if resolved in seen:
            continue
        seen.add(resolved)
        summary = _read_json(compare_path)
        if not summary:
            continue
        rel = compare_path.relative_to(runs_root)
        if len(rel.parts) < 2:
            continue
        run_name = rel.parts[0]
        student = summary.get("student") or {}
        overall = student.get("metrics_overall") or {}
        bleu = (overall.get("bleu") or {}).get("score")
        chrf = (overall.get("chrf") or {}).get("score")
        rows.append(
            {
                "run_name": run_name,
                "eval_dir": compare_path.parent.name,
                "decode": _decode_from_path(compare_path),
                "eval_samples": _fmt_int(summary.get("eval_samples")),
                "pairs": str(summary.get("pairs", "")),
                "student_model": str(student.get("model", "")),
                "bleu": _fmt_float(bleu),
                "chrf": _fmt_float(chrf),
                "compare_summary_path": _safe_rel(compare_path, repo_root),
            }
        )
    rows.sort(key=lambda x: (x["run_name"], x["eval_dir"], x["decode"]))
    return rows


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
            "timestamp_utc": row["timestamp_utc"],
            "pair_count": row["pair_count"],
            "pairs_input_spec": row["pairs_input_spec"],
            "schedule": row["schedule"],
            "sft_steps": row["sft_steps"],
            "distill_steps": row["distill_steps"],
            "lambda_kd": row["lambda_kd"],
            "mu_triplet": row["mu_triplet"],
            "resumed": row["resumed"],
            "summary_path": row["summary_path"],
        }
        for row in run_rows
    ]
    eval_view = [
        {
            "run_name": row["run_name"],
            "eval_dir": row["eval_dir"],
            "decode": row["decode"],
            "bleu": row["bleu"],
            "chrf": row["chrf"],
            "pairs": row["pairs"],
            "compare_summary_path": row["compare_summary_path"],
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
                    ("timestamp_utc", "timestamp_utc"),
                    ("pair_count", "pair_count"),
                    ("pairs_input_spec", "pairs_input"),
                    ("schedule", "schedule"),
                    ("sft_steps", "sft_steps"),
                    ("distill_steps", "distill_steps"),
                    ("lambda_kd", "lambda_kd"),
                    ("mu_triplet", "mu_triplet"),
                    ("resumed", "resumed"),
                    ("summary_path", "summary"),
                ],
            )
        )
    else:
        md.append("_No runs with train_summary.json found._")
    md.append("")
    md.append("## Eval Results")
    md.append("")
    if eval_view:
        md.append(
            _md_table(
                eval_view,
                [
                    ("run_name", "run"),
                    ("eval_dir", "eval"),
                    ("decode", "decode"),
                    ("bleu", "bleu"),
                    ("chrf", "chrf"),
                    ("pairs", "pairs"),
                    ("compare_summary_path", "summary"),
                ],
            )
        )
    else:
        md.append("_No compare_eval_summary.json files found._")
    md.append("")
    md.append("## Notes")
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
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[4]
    runs_root = Path(args.runs_root).resolve()
    out_md = Path(args.out_md).resolve()
    out_runs_csv = Path(args.out_runs_csv).resolve()
    out_evals_csv = Path(args.out_evals_csv).resolve()

    run_rows = collect_run_rows(runs_root, repo_root)
    eval_rows = collect_eval_rows(runs_root, repo_root)

    write_csv(
        out_runs_csv,
        run_rows,
        [
            "run_name",
            "timestamp_utc",
            "pair_count",
            "pairs_input_spec",
            "schedule",
            "sft_steps",
            "distill_steps",
            "lambda_kd",
            "mu_triplet",
            "resumed",
            "resume_stage",
            "resume_from",
            "selected_checkpoint",
            "selected_checkpoint_stage",
            "selected_checkpoint_loss",
            "summary_path",
        ],
    )
    write_csv(
        out_evals_csv,
        eval_rows,
        [
            "run_name",
            "eval_dir",
            "decode",
            "eval_samples",
            "bleu",
            "chrf",
            "pairs",
            "student_model",
            "compare_summary_path",
        ],
    )
    write_markdown(out_md, run_rows, eval_rows, runs_root)
    print(f"wrote: {out_md}")
    print(f"wrote: {out_runs_csv}")
    print(f"wrote: {out_evals_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
