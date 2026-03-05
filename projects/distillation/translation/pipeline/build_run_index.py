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


def _checkpoint_step(name: str) -> int:
    m = re.fullmatch(r"checkpoint-(\d+)", name)
    if not m:
        return -1
    try:
        return int(m.group(1))
    except Exception:
        return -1


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

        summary: dict[str, Any] | None = _read_json(summary_path) if summary_path.is_file() else None
        contract = _parse_run_contract(contract_path)

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
            resumed = _fmt_bool(summary.get("resumed", False))
            resume_stage = str(summary.get("resume_stage", ""))
            resume_from = str(summary.get("resume_from", ""))
            selected_checkpoint = str(summary.get("selected_checkpoint", ""))
            selected_checkpoint_stage = str(summary.get("selected_checkpoint_stage", ""))
            selected_checkpoint_loss = _fmt_float(summary.get("selected_checkpoint_loss"))
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
                timestamp_epoch = float(contract_path.stat().st_mtime)
            except Exception:
                timestamp_epoch = -1.0
            timestamp_utc = _mtime_utc(contract_path)
            pair_count = ""
            pairs_input_spec = contract.get("pairs_input_spec", "")
            eval_dataset_paths = contract.get("eval_dataset_paths", "")
            schedule = contract.get("schedule", "")
            sft_steps = ""
            distill_steps = ""
            lambda_kd = ""
            mu_triplet = ""
            resumed = _fmt_bool(contract.get("resume_stage") not in ("", "none", None))
            resume_stage = contract.get("resume_stage", "none")
            resume_from = contract.get("resume_from", "")
            selected_checkpoint = ""
            selected_checkpoint_stage = ""
            selected_checkpoint_loss = ""
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
            resumed = "false"
            resume_stage = ""
            resume_from = ""
            selected_checkpoint = ""
            selected_checkpoint_stage = ""
            selected_checkpoint_loss = ""
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
                    _safe_rel(contract_path, repo_root) if contract else ""
                ),
                "timestamp_epoch": float(timestamp_epoch),
                "timestamp_utc": timestamp_utc,
                "schedule": schedule,
                "pair_count": pair_count,
                "pairs_input_spec": pairs_input_spec,
                "source_langs": source_langs,
                "target_langs": target_langs,
                "eval_dataset_paths": eval_dataset_paths,
                "total_steps": total_steps,
                "sft_steps": sft_steps,
                "distill_steps": distill_steps,
                "lambda_kd": lambda_kd,
                "mu_triplet": mu_triplet,
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
    folder = path.name
    if folder.endswith("__greedy"):
        return "greedy"
    if folder.endswith("__sampled"):
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


def _infer_eval_components(eval_name: str) -> tuple[str, str, str]:
    parts = eval_name.split("__")
    if len(parts) == 1:
        return eval_name, "", ""
    eval_set = parts[0]
    checkpoint = ""
    variant_parts: list[str] = []
    for part in parts[1:]:
        if part.startswith("checkpoint-"):
            checkpoint = part
            continue
        if part in {"greedy", "sampled"}:
            continue
        if part:
            variant_parts.append(part)
    return eval_set, "__".join(variant_parts), checkpoint


def _collect_eval_row(path: Path, summary: dict[str, Any], repo_root: Path) -> dict[str, str]:
    eval_name = path.name
    eval_set, eval_variant, eval_checkpoint = _infer_eval_components(eval_name)
    student = summary.get("student") if isinstance(summary.get("student"), dict) else {}
    model = str(student.get("model", "")) if isinstance(student, dict) else ""
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
        "eval_set": eval_set,
        "eval_variant": eval_variant,
        "eval_checkpoint": eval_checkpoint,
        "eval_dir_path": _safe_rel(path, repo_root),
        "decode": _decode_from_path(path),
        "eval_samples": _fmt_int(summary.get("eval_samples")),
        "eval_timestamp_utc": _timestamp_utc_from_file(path),
        "pairs": _find_eval_dataset(summary, eval_name),
        "pairs_stem": _path_stem(_find_eval_dataset(summary, eval_name)),
        "student_model": model,
        "bleu": _fmt_float(((summary.get("student", {}) or {}).get("metrics_overall", {}).get("bleu", {}) or {}).get("score")),
        "chrf": _fmt_float(((summary.get("student", {}) or {}).get("metrics_overall", {}).get("chrf", {}) or {}).get("score")),
        "predictions_path": _safe_rel(Path(pred_path), repo_root) if pred_path else "",
        "compare_summary_path": _safe_rel(path, repo_root),
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
        row = _collect_eval_rows_for_path(compare_path, runs_root, repo_root)
        if not row:
            continue
        rows.append(row)
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
            "run_status": row["run_status"],
            "run_root": row["run_root"],
            "timestamp_utc": row["timestamp_utc"],
            "updated_utc": row["updated_utc"],
            "source_langs": row["source_langs"],
            "target_langs": row["target_langs"],
            "eval_dataset_paths": row["eval_dataset_paths"],
            "pair_count": row["pair_count"],
            "pairs_input_spec": row["pairs_input_spec"],
            "total_steps": row["total_steps"],
            "schedule": row["schedule"],
            "sft_steps": row["sft_steps"] if row["sft_steps"] != "" else "",
            "distill_steps": row["distill_steps"] if row["distill_steps"] != "" else "",
            "lambda_kd": row["lambda_kd"],
            "mu_triplet": row["mu_triplet"],
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
            "eval_dir": row["eval_dir"],
            "eval_set": row["eval_set"],
            "eval_variant": row["eval_variant"],
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
                    ("eval_dataset_paths", "eval_datasets"),
                    ("pair_count", "pair_count"),
                    ("pairs_input_spec", "pairs_input"),
                    ("total_steps", "total_steps"),
                    ("schedule", "schedule"),
                    ("sft_steps", "sft_steps"),
                    ("distill_steps", "distill_steps"),
                    ("lambda_kd", "lambda_kd"),
                    ("mu_triplet", "mu_triplet"),
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
                    ("eval_dir", "eval"),
                    ("eval_set", "eval_set"),
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
            "run_root",
            "run_status",
            "summary_source",
            "timestamp_utc",
            "updated_utc",
            "source_langs",
            "target_langs",
            "eval_dataset_paths",
            "pair_count",
            "pairs_input_spec",
            "schedule",
            "total_steps",
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
            "eval_set",
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
    write_markdown(out_md, run_rows, eval_rows, runs_root)
    print(f"wrote: {out_md}")
    print(f"wrote: {out_runs_csv}")
    print(f"wrote: {out_evals_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
