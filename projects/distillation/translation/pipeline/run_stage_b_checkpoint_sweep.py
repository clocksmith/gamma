#!/usr/bin/env python3
"""Deterministic Stage B checkpoint sweep with live-updated scoreboard outputs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


DATASET_LABELS: dict[str, str] = {
    "eval2_external": "external_wmt13_en_es_translation_benchmark_128",
    "translate_distill_pairs.eval2_wmt13_enes_128.jsonl": "external_wmt13_en_es_translation_benchmark_128",
    "eval3_indomain_clean": "indomain_clean_merged_en_es_translation_benchmark_128",
    "translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl": "indomain_clean_merged_en_es_translation_benchmark_128",
}


def _now_utc() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def _checkpoint_step_from_name(name: str) -> int:
    m = re.fullmatch(r"checkpoint-(\d+)", name)
    if not m:
        return -1
    return int(m.group(1))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_float(value: Any) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.4f}"
    except Exception:
        return ""


def _path_stem(path: str) -> str:
    try:
        return Path(path).name
    except Exception:
        return str(path)


def _dataset_label(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    stem = _path_stem(text)
    for key, label in DATASET_LABELS.items():
        if text == key or stem == key or key in text:
            return label
    return text


def _collect_checkpoints(stage_b_dir: Path, checkpoints_arg: str) -> list[Path]:
    if checkpoints_arg.strip().lower() == "auto":
        all_ckpts = [p for p in stage_b_dir.glob("checkpoint-*") if p.is_dir()]
        return sorted(all_ckpts, key=lambda p: _checkpoint_step_from_name(p.name))

    out: list[Path] = []
    for raw in checkpoints_arg.split(","):
        token = raw.strip()
        if not token:
            continue
        if token.isdigit():
            name = f"checkpoint-{int(token):06d}"
        elif token.startswith("checkpoint-"):
            name = token
        else:
            raise RuntimeError(f"Invalid checkpoint token: {token}")
        ckpt = stage_b_dir / name
        if not ckpt.is_dir():
            raise RuntimeError(f"Checkpoint not found: {ckpt}")
        out.append(ckpt)
    out.sort(key=lambda p: _checkpoint_step_from_name(p.name))
    return out


def _parse_eval_specs(eval_specs: list[str]) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for spec in eval_specs:
        if "=" not in spec:
            raise RuntimeError(f"Invalid --eval spec (expected name=path): {spec}")
        name, raw_path = spec.split("=", 1)
        eval_name = name.strip()
        eval_path = Path(raw_path.strip())
        if not eval_name:
            raise RuntimeError(f"Empty eval name in --eval spec: {spec}")
        if not eval_path.is_file():
            raise RuntimeError(f"Eval pairs file not found: {eval_path}")
        out.append((eval_name, eval_path))
    if not out:
        raise RuntimeError("No --eval specs provided.")
    return out


def _read_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            rows.append(json.loads(text))
        except Exception:
            continue
    return rows


def _append_manifest(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=True) + "\n")


def _is_done(manifest_rows: list[dict[str, Any]], checkpoint_name: str, eval_name: str, decode: str) -> bool:
    for row in manifest_rows:
        if (
            str(row.get("checkpoint_name", "")) == checkpoint_name
            and str(row.get("eval_name", "")) == eval_name
            and str(row.get("decode", "")) == decode
            and int(row.get("status", 1)) == 0
        ):
            return True
    return False


def _extract_metrics(compare_summary_path: Path) -> tuple[float | None, float | None, int | None]:
    if not compare_summary_path.is_file():
        return None, None, None
    try:
        summary = _load_json(compare_summary_path)
    except Exception:
        return None, None, None
    student = summary.get("student") or {}
    overall = student.get("metrics_overall") or {}
    bleu = ((overall.get("bleu") or {}).get("score")) if isinstance(overall, dict) else None
    chrf = ((overall.get("chrf") or {}).get("score")) if isinstance(overall, dict) else None
    n = overall.get("n") if isinstance(overall, dict) else None
    try:
        bleu = float(bleu) if bleu is not None else None
    except Exception:
        bleu = None
    try:
        chrf = float(chrf) if chrf is not None else None
    except Exception:
        chrf = None
    try:
        n = int(n) if n is not None else None
    except Exception:
        n = None
    return bleu, chrf, n


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def _md_table(rows: list[dict[str, Any]], cols: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(key, "")) for key, _ in cols) + " |")
    return "\n".join([header, sep] + body)


def _write_scoreboard(
    out_dir: Path,
    manifest_rows: list[dict[str, Any]],
    repo_root: Path,
    run_root: Path,
    decode: str,
    eval_specs: list[tuple[str, Path]],
) -> None:
    eval_rows: list[dict[str, Any]] = []
    for row in manifest_rows:
        if str(row.get("decode", "")) != decode:
            continue
        if int(row.get("status", 1)) != 0:
            continue
        eval_name = str(row.get("eval_name", ""))
        eval_rows.append(
            {
                "checkpoint_name": row.get("checkpoint_name", ""),
                "checkpoint_step": row.get("checkpoint_step", ""),
                "eval_name": _dataset_label(eval_name),
                "bleu": _fmt_float(row.get("bleu")),
                "chrf": _fmt_float(row.get("chrf")),
                "samples": row.get("samples", ""),
                "duration_s": _fmt_float(row.get("duration_s")),
                "pairs": row.get("pairs", ""),
                "compare_summary": row.get("compare_summary", ""),
                "log_path": row.get("log_path", ""),
            }
        )
    eval_rows.sort(key=lambda r: (str(r["eval_name"]), int(r["checkpoint_step"])))

    # Aggregate per checkpoint across eval sets.
    agg: dict[str, dict[str, Any]] = {}
    expected_evals = [_dataset_label(name) for name, _ in eval_specs]
    for row in manifest_rows:
        if str(row.get("decode", "")) != decode or int(row.get("status", 1)) != 0:
            continue
        ck = str(row.get("checkpoint_name", ""))
        bucket = agg.setdefault(
            ck,
            {
                "checkpoint_name": ck,
                "checkpoint_step": row.get("checkpoint_step", ""),
                "evals_done": 0,
                "bleu_values": [],
                "chrf_values": [],
                "evals": {},
            },
        )
        bucket["evals_done"] = int(bucket["evals_done"]) + 1
        ev_name = _dataset_label(str(row.get("eval_name", "")))
        bleu = row.get("bleu")
        chrf = row.get("chrf")
        if isinstance(bleu, (float, int)):
            bucket["bleu_values"].append(float(bleu))
        if isinstance(chrf, (float, int)):
            bucket["chrf_values"].append(float(chrf))
        bucket["evals"][ev_name] = {"bleu": bleu, "chrf": chrf}

    agg_rows: list[dict[str, Any]] = []
    for ck_name, item in agg.items():
        bleu_values = item.get("bleu_values", [])
        chrf_values = item.get("chrf_values", [])
        avg_bleu = (sum(bleu_values) / len(bleu_values)) if bleu_values else None
        avg_chrf = (sum(chrf_values) / len(chrf_values)) if chrf_values else None
        row: dict[str, Any] = {
            "checkpoint_name": ck_name,
            "checkpoint_step": item.get("checkpoint_step", ""),
            "evals_done": item.get("evals_done", 0),
            "evals_expected": len(expected_evals),
            "avg_bleu": _fmt_float(avg_bleu),
            "avg_chrf": _fmt_float(avg_chrf),
        }
        eval_map = item.get("evals", {})
        for ev_name in expected_evals:
            ev = eval_map.get(ev_name) or {}
            row[f"{ev_name}_bleu"] = _fmt_float(ev.get("bleu"))
            row[f"{ev_name}_chrf"] = _fmt_float(ev.get("chrf"))
        agg_rows.append(row)

    agg_rows.sort(
        key=lambda r: (
            float(r["avg_bleu"]) if str(r.get("avg_bleu", "")).strip() else -1e9,
            int(r.get("checkpoint_step", -1)),
        ),
        reverse=True,
    )

    eval_csv = out_dir / "scoreboard_eval_rows.csv"
    agg_csv = out_dir / "scoreboard_checkpoints.csv"
    _write_csv(
        eval_csv,
        eval_rows,
        [
            "checkpoint_name",
            "checkpoint_step",
            "eval_name",
            "bleu",
            "chrf",
            "samples",
            "duration_s",
            "pairs",
            "compare_summary",
            "log_path",
        ],
    )

    agg_fields = [
        "checkpoint_name",
        "checkpoint_step",
        "evals_done",
        "evals_expected",
        "avg_bleu",
        "avg_chrf",
    ]
    for ev_name in expected_evals:
        agg_fields.append(f"{ev_name}_bleu")
        agg_fields.append(f"{ev_name}_chrf")
    _write_csv(agg_csv, agg_rows, agg_fields)

    md_lines: list[str] = []
    md_lines.append("# Stage B Checkpoint Sweep Scoreboard")
    md_lines.append("")
    md_lines.append(f"Updated: {_now_utc()}")
    md_lines.append(f"Run root: `{_safe_rel(run_root, repo_root)}`")
    md_lines.append(f"Decode: `{decode}`")
    md_lines.append("")
    md_lines.append("## Checkpoint Ranking")
    md_lines.append("")
    if agg_rows:
        cols: list[tuple[str, str]] = [
            ("checkpoint_name", "checkpoint"),
            ("checkpoint_step", "step"),
            ("evals_done", "evals_done"),
            ("evals_expected", "evals_expected"),
            ("avg_bleu", "avg_bleu"),
            ("avg_chrf", "avg_chrf"),
        ]
        for ev_name in expected_evals:
            cols.append((f"{ev_name}_bleu", f"{ev_name}_bleu"))
            cols.append((f"{ev_name}_chrf", f"{ev_name}_chrf"))
        md_lines.append(_md_table(agg_rows, cols))
    else:
        md_lines.append("_No successful eval rows yet._")

    md_lines.append("")
    md_lines.append("## Eval Rows")
    md_lines.append("")
    if eval_rows:
        md_lines.append(
            _md_table(
                eval_rows,
                [
                    ("checkpoint_name", "checkpoint"),
                    ("checkpoint_step", "step"),
                    ("eval_name", "eval"),
                    ("bleu", "bleu"),
                    ("chrf", "chrf"),
                    ("samples", "samples"),
                    ("duration_s", "duration_s"),
                ],
            )
        )
    else:
        md_lines.append("_No successful eval rows yet._")

    md_lines.append("")
    md_lines.append("## Files")
    md_lines.append("")
    md_lines.append(f"- Manifest: `{_safe_rel(out_dir / 'manifest.jsonl', repo_root)}`")
    md_lines.append(f"- Eval rows CSV: `{_safe_rel(eval_csv, repo_root)}`")
    md_lines.append(f"- Checkpoint ranking CSV: `{_safe_rel(agg_csv, repo_root)}`")
    md_lines.append("")
    (out_dir / "scoreboard.md").write_text("\n".join(md_lines), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run deterministic Stage B checkpoint sweep.")
    ap.add_argument(
        "--run-root",
        required=True,
        help="Run root that contains stage_b/checkpoint-* directories.",
    )
    ap.add_argument(
        "--stage-dir",
        default="stage_b",
        help="Stage directory under run root (default: stage_b).",
    )
    ap.add_argument(
        "--checkpoints",
        default="auto",
        help=(
            "Comma list of checkpoint ids/names (e.g., 1000,2000 or checkpoint-001000,checkpoint-002000), "
            "or 'auto' for all checkpoint-* in the stage dir."
        ),
    )
    ap.add_argument(
        "--eval",
        action="append",
        default=[],
        help="Eval spec in form name=path/to/pairs.jsonl. Repeat for multiple eval sets.",
    )
    ap.add_argument("--source-langs", default="en,es")
    ap.add_argument("--target-langs", default="en,es")
    ap.add_argument("--batch-size", type=int, default=2)
    ap.add_argument("--max-prompt-length", type=int, default=256)
    ap.add_argument("--max-new-tokens", type=int, default=192)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--dtype", default="auto", choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--decode", default="greedy", choices=["greedy"])
    ap.add_argument("--teacher-model", default="")
    ap.add_argument("--allow-download", action="store_true")
    ap.add_argument(
        "--hsa-override-gfx-version",
        default="",
        help="Optional HSA_OVERRIDE_GFX_VERSION value for ROCm stability (example: 11.0.0).",
    )
    ap.add_argument(
        "--python-bin",
        default="",
        help="Python executable used to run eval script (default: .venv/bin/python if present, else current Python).",
    )
    ap.add_argument(
        "--out-dir",
        default="",
        help="Sweep output dir (default: <run-root>/checkpoint_sweep_<timestamp>).",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="Skip already successful (checkpoint, eval, decode) entries from manifest.",
    )
    return ap.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[4]
    run_root = Path(args.run_root).resolve()
    stage_dir = run_root / args.stage_dir
    if not run_root.is_dir():
        raise RuntimeError(f"run root not found: {run_root}")
    if not stage_dir.is_dir():
        raise RuntimeError(f"stage dir not found: {stage_dir}")

    eval_specs = _parse_eval_specs(args.eval)
    checkpoints = _collect_checkpoints(stage_dir, args.checkpoints)
    if not checkpoints:
        raise RuntimeError(f"No checkpoints found in {stage_dir}")

    ts_tag = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir).resolve() if str(args.out_dir).strip() else (run_root / f"checkpoint_sweep_{ts_tag}")
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "manifest.jsonl"
    manifest_rows = _read_manifest(manifest_path)

    eval_script = repo_root / "projects" / "distillation" / "translation" / "eval" / "run_translate_distill_eval.py"
    if not eval_script.is_file():
        raise RuntimeError(f"eval script not found: {eval_script}")

    python_bin = Path(str(args.python_bin).strip()) if str(args.python_bin).strip() else None
    if python_bin is None:
        venv_py = repo_root / ".venv" / "bin" / "python"
        python_bin = venv_py if venv_py.is_file() else Path(sys.executable)
    if not python_bin.is_file():
        raise RuntimeError(f"python binary not found: {python_bin}")

    print(f"[sweep] started: {_now_utc()}")
    print(f"[sweep] run_root={_safe_rel(run_root, repo_root)}")
    print(f"[sweep] stage_dir={_safe_rel(stage_dir, repo_root)}")
    print(f"[sweep] out_dir={_safe_rel(out_dir, repo_root)}")
    print(f"[sweep] checkpoints={','.join(p.name for p in checkpoints)}")
    print(f"[sweep] evals={','.join(_dataset_label(name) for name, _ in eval_specs)}")
    print(f"[sweep] decode={args.decode}")

    _write_scoreboard(out_dir, manifest_rows, repo_root, run_root, args.decode, eval_specs)

    for ckpt in checkpoints:
        ckpt_step = _checkpoint_step_from_name(ckpt.name)
        for eval_name, eval_pairs in eval_specs:
            if args.resume and _is_done(manifest_rows, ckpt.name, eval_name, args.decode):
                print(f"[skip] {ckpt.name} x {eval_name} already completed")
                continue

            case_name = f"{eval_name}__{ckpt.name}__{args.decode}"
            case_dir = out_dir / case_name
            case_dir.mkdir(parents=True, exist_ok=True)
            log_path = case_dir / "eval_run.log"
            compare_summary = case_dir / "compare_eval_summary.json"
            student_summary = case_dir / "student_eval_summary.json"
            student_predictions = case_dir / "student_predictions.jsonl"
            teacher_summary = case_dir / "teacher_eval_summary.json"
            teacher_predictions = case_dir / "teacher_predictions.jsonl"

            cmd = [
                str(python_bin),
                str(eval_script),
                "--pairs",
                str(eval_pairs),
                "--model",
                str(ckpt),
                "--source-langs",
                str(args.source_langs),
                "--target-langs",
                str(args.target_langs),
                "--out-dir",
                str(case_dir),
                "--student-summary",
                str(student_summary),
                "--teacher-summary",
                str(teacher_summary),
                "--compare-summary",
                str(compare_summary),
                "--student-predictions",
                str(student_predictions),
                "--teacher-predictions",
                str(teacher_predictions),
                "--max-prompt-length",
                str(int(args.max_prompt_length)),
                "--max-new-tokens",
                str(int(args.max_new_tokens)),
                "--batch-size",
                str(int(args.batch_size)),
                "--device",
                str(args.device),
                "--dtype",
                str(args.dtype),
                "--seed",
                str(int(args.seed)),
                "--temperature",
                "0.0",
                "--top-p",
                "1.0",
                "--top-k",
                "50",
                "--eval-bleu",
                "--eval-chrf",
                "--allow-partial-contract",
            ]
            if str(args.teacher_model).strip():
                cmd.extend(["--teacher-model", str(args.teacher_model).strip()])
            if args.allow_download:
                cmd.append("--allow-download")

            command_str = shlex.join(cmd)
            print(f"[run] {ckpt.name} x {eval_name}")
            print(f"[cmd] {command_str}")
            start = time.monotonic()
            started_utc = _now_utc()
            child_env = os.environ.copy()
            if str(args.hsa_override_gfx_version).strip():
                child_env["HSA_OVERRIDE_GFX_VERSION"] = str(args.hsa_override_gfx_version).strip()
            proc = subprocess.run(cmd, capture_output=True, text=True, env=child_env)
            duration_s = time.monotonic() - start
            ended_utc = _now_utc()

            log_text = []
            log_text.append(f"[started] {started_utc}")
            log_text.append(f"[ended] {ended_utc}")
            log_text.append(f"[duration_s] {duration_s:.2f}")
            log_text.append(f"[returncode] {proc.returncode}")
            log_text.append(f"[cmd] {command_str}")
            log_text.append("")
            log_text.append("=== STDOUT ===")
            log_text.append(proc.stdout or "")
            log_text.append("")
            log_text.append("=== STDERR ===")
            log_text.append(proc.stderr or "")
            log_path.write_text("\n".join(log_text), encoding="utf-8")

            bleu, chrf, samples = _extract_metrics(compare_summary)
            row = {
                "timestamp_utc": ended_utc,
                "run_root": _safe_rel(run_root, repo_root),
                "checkpoint_name": ckpt.name,
                "checkpoint_step": ckpt_step,
                "checkpoint_path": _safe_rel(ckpt, repo_root),
                "eval_name": eval_name,
                "pairs": _safe_rel(eval_pairs, repo_root),
                "decode": args.decode,
                "status": int(proc.returncode),
                "duration_s": float(duration_s),
                "bleu": bleu,
                "chrf": chrf,
                "samples": samples,
                "out_dir": _safe_rel(case_dir, repo_root),
                "compare_summary": _safe_rel(compare_summary, repo_root),
                "student_summary": _safe_rel(student_summary, repo_root),
                "student_predictions": _safe_rel(student_predictions, repo_root),
                "log_path": _safe_rel(log_path, repo_root),
                "command": command_str,
                "hsa_override_gfx_version": str(args.hsa_override_gfx_version).strip(),
            }
            _append_manifest(manifest_path, row)
            manifest_rows.append(row)
            _write_scoreboard(out_dir, manifest_rows, repo_root, run_root, args.decode, eval_specs)

            if proc.returncode == 0:
                print(
                    f"[ok] {ckpt.name} x {eval_name} "
                    f"BLEU={_fmt_float(bleu)} chrF={_fmt_float(chrf)} duration_s={duration_s:.2f}"
                )
            else:
                print(f"[fail] {ckpt.name} x {eval_name} returncode={proc.returncode} (see {log_path})")

    print(f"[sweep] done: {_now_utc()}")
    print(f"[sweep] manifest={_safe_rel(manifest_path, repo_root)}")
    print(f"[sweep] scoreboard={_safe_rel(out_dir / 'scoreboard.md', repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
