#!/usr/bin/env python3
"""Launch a CPU Stage A matrix and eval external BLEU as checkpoints land."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
TRAINER_SCRIPT = PROJECT_ROOT / "projects" / "distillation" / "translation" / "training" / "train_translate_distill.py"
EVAL_SCRIPT = PROJECT_ROOT / "projects" / "distillation" / "translation" / "eval" / "run_translate_distill_eval.py"
DEFAULT_PYTHON_BIN = PROJECT_ROOT / ".venv" / "bin" / "python"
DEFAULT_EVAL_PAIRS = (
    PROJECT_ROOT / "projects" / "distillation" / "translation" / "training_data" / "translate_distill_pairs.eval2_wmt13_enes_128.jsonl"
)
DEFAULT_TEACHER_MODEL = (
    "/home/x/.cache/huggingface/hub/models--google--translategemma-4b-it/"
    "snapshots/10042cb0e6e7fdce748996a71dc3dc432a4e0c89"
)
DEFAULT_STUDENT_MODEL = (
    "/home/x/.cache/huggingface/hub/models--google--gemma-3-1b-it/"
    "snapshots/dcc83ea841ab6100d6b47a070329e1ba4cf78752"
)


def _parse_sizes(value: str) -> list[int]:
    out: list[int] = []
    for raw in str(value).split(","):
        text = raw.strip()
        if not text:
            continue
        size = int(text)
        if size <= 0:
            raise ValueError(f"subset sizes must be positive: {text}")
        out.append(size)
    if not out:
        raise ValueError("at least one subset size is required")
    return sorted(set(out))


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (PROJECT_ROOT / path)


def _resolve_python_bin(value: str) -> Path:
    raw = str(value).strip()
    if raw:
        py = _resolve_path(raw)
    elif DEFAULT_PYTHON_BIN.is_file():
        py = DEFAULT_PYTHON_BIN
    else:
        py = Path(sys.executable)
    if not py.is_file():
        raise RuntimeError(f"python binary not found: {py}")
    return py


def _runtime_mode(device: str) -> str:
    return "cpu" if str(device).strip().lower() == "cpu" else "normal_rocm"


def _preflight(python_bin: Path, device: str) -> dict[str, object]:
    probe = [
        str(python_bin),
        "-c",
        (
            "import json; import torch; import transformers; "
            "print(json.dumps({"
            "'python': '" + str(python_bin) + "', "
            "'torch_version': torch.__version__, "
            "'transformers_version': transformers.__version__, "
            "'cuda_available': bool(torch.cuda.is_available()), "
            "'cuda_device_count': int(torch.cuda.device_count()), "
            "'target_device': '" + str(device) + "'"
            "}, sort_keys=True))"
        ),
    ]
    proc = subprocess.run(probe, check=True, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    lines = (proc.stdout or "").strip().splitlines()
    if not lines:
        raise RuntimeError("empty preflight output")
    return json.loads(lines[-1])


def _subset_path(subset_dir: Path, size: int, seed: int) -> Path:
    return subset_dir / f"translate_distill_pairs_en_es_2way.train.merged.subset_{size}.seed{seed}.jsonl"


def _run_name(size: int, seed: int, tag: str) -> str:
    return f"translategemma4b_es_en_gemma3_1b_stagea_cpu_subset{size}_seed{seed}_{tag}"


def _checkpoint_step(path: Path) -> int:
    name = path.name
    if not name.startswith("checkpoint-"):
        return -1
    try:
        return int(name.split("-", 1)[1])
    except Exception:
        return -1


def _checkpoint_token(step: int) -> str:
    if step > 0 and step % 1000 == 0:
        return f"stagea{step // 1000}k"
    return f"stagea{step}"


def _checkpoint_ready(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / "model.safetensors").is_file()
        and (path / "config.json").is_file()
        and (path / "training_state.pt").is_file()
    )


def _extract_bleu(compare_summary_path: Path) -> float | None:
    if not compare_summary_path.is_file():
        return None
    try:
        summary = json.loads(compare_summary_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    student = summary.get("student") or {}
    overall = student.get("metrics_overall") or {}
    bleu = ((overall.get("bleu") or {}).get("score")) if isinstance(overall, dict) else None
    try:
        return float(bleu) if bleu is not None else None
    except Exception:
        return None


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


def _write_scoreboard(path: Path, rows: list[dict[str, Any]]) -> None:
    done_rows = [row for row in rows if int(row.get("status", 1)) == 0]
    done_rows.sort(key=lambda row: int(row.get("checkpoint_step", -1)))
    lines = [
        "# Stage A External BLEU",
        "",
        f"Updated: {dt.datetime.now(tz=dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
    ]
    if not done_rows:
        lines.append("_No successful eval rows yet._")
    else:
        lines.extend(
            [
                "| checkpoint | step | bleu | out_dir |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in done_rows:
            bleu = row.get("bleu")
            bleu_text = f"{float(bleu):.4f}" if isinstance(bleu, (float, int)) else ""
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row.get("checkpoint_name", "")),
                        str(row.get("checkpoint_step", "")),
                        bleu_text,
                        str(row.get("out_dir", "")),
                    ]
                )
                + " |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_contract_line(*, run_name: str, subset_path: Path, eval_pairs: Path, args: argparse.Namespace) -> str:
    return (
        "[run-contract] "
        f"run_name={run_name} "
        f"pairs_input_spec={subset_path} "
        "resume_from=none "
        "resume_stage=none "
        "decode=greedy "
        f"eval_dataset_paths={eval_pairs} "
        f"device={args.device} "
        "schedule=A_then_B "
        f"runtime_mode={_runtime_mode(str(args.device))}"
    )


def _build_train_cmd(
    args: argparse.Namespace,
    *,
    python_bin: Path,
    subset_path: Path,
    run_name: str,
    out_root: Path,
) -> list[str]:
    summary_out = out_root / run_name / "train_summary.json"
    return [
        str(python_bin),
        "-u",
        str(TRAINER_SCRIPT),
        "--pairs",
        str(subset_path),
        "--teacher-model",
        str(args.teacher_model),
        "--student-model",
        str(args.student_model),
        "--source-langs",
        str(args.source_langs),
        "--target-langs",
        str(args.target_langs),
        "--out-root",
        str(out_root),
        "--run-name",
        run_name,
        "--schedule",
        "A_then_B",
        "--total-steps",
        str(int(args.total_steps)),
        "--sft-steps",
        str(int(args.sft_steps)),
        "--batch-size",
        str(int(args.batch_size)),
        "--lr",
        str(args.lr),
        "--log-every",
        str(int(args.log_every)),
        "--save-every",
        str(int(args.save_every)),
        "--keep-checkpoints",
        str(int(args.keep_checkpoints)),
        "--lambda-kd",
        "0.0",
        "--mu-triplet",
        "0.0",
        "--margin",
        "0.2",
        "--device",
        str(args.device),
        "--teacher-device",
        str(args.teacher_device),
        "--dtype",
        str(args.dtype),
        "--max-prompt-length",
        str(int(args.max_prompt_length)),
        "--max-new-tokens",
        str(int(args.max_new_tokens)),
        "--summary-out",
        str(summary_out),
        "--seed",
        str(int(args.seed)),
        "--select-best-checkpoint",
    ]


def _build_eval_cmd(
    args: argparse.Namespace,
    *,
    python_bin: Path,
    eval_pairs: Path,
    checkpoint_path: Path,
    case_dir: Path,
) -> list[str]:
    return [
        str(python_bin),
        str(EVAL_SCRIPT),
        "--pairs",
        str(eval_pairs),
        "--model",
        str(checkpoint_path),
        "--source-langs",
        str(args.source_langs),
        "--target-langs",
        str(args.target_langs),
        "--out-dir",
        str(case_dir),
        "--student-summary",
        str(case_dir / "student_eval_summary.json"),
        "--compare-summary",
        str(case_dir / "compare_eval_summary.json"),
        "--student-predictions",
        str(case_dir / "student_predictions.jsonl"),
        "--max-prompt-length",
        str(int(args.eval_max_prompt_length)),
        "--max-new-tokens",
        str(int(args.eval_max_new_tokens)),
        "--batch-size",
        str(int(args.eval_batch_size)),
        "--device",
        str(args.eval_device),
        "--dtype",
        str(args.eval_dtype),
        "--seed",
        str(int(args.seed)),
        "--temperature",
        "0.0",
        "--top-p",
        "1.0",
        "--top-k",
        "50",
        "--eval-bleu",
        "--allow-partial-contract",
    ]


def _scan_checkpoints(stage_a_dir: Path) -> list[Path]:
    candidates = [child for child in stage_a_dir.glob("checkpoint-*") if _checkpoint_ready(child)]
    return sorted(candidates, key=_checkpoint_step)


def _log_line(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(text.rstrip() + "\n")


def _maybe_eval_new_checkpoints(
    args: argparse.Namespace,
    *,
    python_bin: Path,
    eval_pairs: Path,
    run_root: Path,
    manifest_path: Path,
    scoreboard_path: Path,
    supervisor_log: Path,
    evaluated: set[str],
) -> None:
    stage_a_dir = run_root / "stage_a"
    if not stage_a_dir.is_dir():
        return
    manifest_rows = _read_manifest(manifest_path)
    for row in manifest_rows:
        checkpoint_name = str(row.get("checkpoint_name", "")).strip()
        if checkpoint_name:
            evaluated.add(checkpoint_name)
    for checkpoint_path in _scan_checkpoints(stage_a_dir):
        checkpoint_name = checkpoint_path.name
        if checkpoint_name in evaluated:
            continue
        step = _checkpoint_step(checkpoint_path)
        case_name = f"eval_{_checkpoint_token(step)}_eval2_greedy_live"
        case_dir = run_root / case_name
        case_dir.mkdir(parents=True, exist_ok=True)
        log_path = case_dir / "eval.log"
        compare_summary = case_dir / "compare_eval_summary.json"
        cmd = _build_eval_cmd(
            args,
            python_bin=python_bin,
            eval_pairs=eval_pairs,
            checkpoint_path=checkpoint_path,
            case_dir=case_dir,
        )
        _log_line(supervisor_log, f"[eval-run] checkpoint={checkpoint_name} cmd={shlex.join(cmd)}")
        started = time.monotonic()
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        duration_s = time.monotonic() - started
        log_text = []
        log_text.append(f"[command] {shlex.join(cmd)}")
        log_text.append(f"[returncode] {proc.returncode}")
        log_text.append(f"[duration_s] {duration_s:.2f}")
        log_text.append("")
        log_text.append("=== STDOUT ===")
        log_text.append(proc.stdout or "")
        log_text.append("")
        log_text.append("=== STDERR ===")
        log_text.append(proc.stderr or "")
        log_path.write_text("\n".join(log_text), encoding="utf-8")
        bleu = _extract_bleu(compare_summary)
        row = {
            "timestamp_utc": dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "checkpoint_name": checkpoint_name,
            "checkpoint_step": step,
            "status": int(proc.returncode),
            "bleu": bleu,
            "out_dir": str(case_dir),
            "compare_summary": str(compare_summary),
            "log_path": str(log_path),
            "pairs": str(eval_pairs),
            "command": shlex.join(cmd),
            "duration_s": float(duration_s),
        }
        _append_manifest(manifest_path, row)
        evaluated.add(checkpoint_name)
        manifest_rows.append(row)
        _write_scoreboard(scoreboard_path, manifest_rows)
        _log_line(
            supervisor_log,
            (
                f"[eval-done] checkpoint={checkpoint_name} "
                f"status={proc.returncode} bleu={f'{bleu:.4f}' if bleu is not None else ''}"
            ),
        )


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Launch a CPU Stage A matrix with live external BLEU eval.")
    ap.add_argument("--sizes", default="1280,2560,5120", help="Comma-separated subset sizes.")
    ap.add_argument(
        "--subset-dir",
        default="projects/distillation/translation/training_data/subsets",
        help="Directory containing subset JSONL files.",
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--tag", default="", help="Optional run-name suffix. Defaults to current UTC timestamp.")
    ap.add_argument("--teacher-model", default=DEFAULT_TEACHER_MODEL)
    ap.add_argument("--student-model", default=DEFAULT_STUDENT_MODEL)
    ap.add_argument("--out-root", default="projects/distillation/translation/runs")
    ap.add_argument(
        "--python-bin",
        default="",
        help="Python executable to use (default: .venv/bin/python if present, else current interpreter).",
    )
    ap.add_argument("--total-steps", type=int, default=32000)
    ap.add_argument("--sft-steps", type=int, default=32000)
    ap.add_argument("--save-every", type=int, default=4000)
    ap.add_argument("--keep-checkpoints", type=int, default=9)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--log-every", type=int, default=20)
    ap.add_argument("--max-prompt-length", type=int, default=256)
    ap.add_argument("--max-new-tokens", type=int, default=192)
    ap.add_argument("--dtype", default="float32", choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--teacher-device", default="cpu")
    ap.add_argument("--source-langs", default="en,es")
    ap.add_argument("--target-langs", default="en,es")
    ap.add_argument(
        "--eval-pairs",
        default=str(DEFAULT_EVAL_PAIRS),
        help="External eval2 JSONL for live checkpoint scoring.",
    )
    ap.add_argument("--eval-batch-size", type=int, default=2)
    ap.add_argument("--eval-max-prompt-length", type=int, default=256)
    ap.add_argument("--eval-max-new-tokens", type=int, default=192)
    ap.add_argument("--eval-device", default="cpu")
    ap.add_argument("--eval-dtype", default="float32", choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument("--poll-seconds", type=float, default=30.0)
    ap.add_argument("--launch", action="store_true", help="Run the matrix instead of only printing the plan.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    sizes = _parse_sizes(args.sizes)
    subset_dir = _resolve_path(args.subset_dir)
    out_root = _resolve_path(args.out_root)
    eval_pairs = _resolve_path(args.eval_pairs)
    python_bin = _resolve_python_bin(args.python_bin)
    tag = str(args.tag).strip() or dt.datetime.now(tz=dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if not eval_pairs.is_file():
        raise RuntimeError(f"eval pairs file not found: {eval_pairs}")
    if not TRAINER_SCRIPT.is_file():
        raise RuntimeError(f"trainer script not found: {TRAINER_SCRIPT}")
    if not EVAL_SCRIPT.is_file():
        raise RuntimeError(f"eval script not found: {EVAL_SCRIPT}")

    preflight = _preflight(python_bin, str(args.device))
    print(
        "[preflight] "
        f"python={preflight['python']} "
        f"torch={preflight['torch_version']} "
        f"transformers={preflight['transformers_version']}"
    )
    print(
        "[preflight] "
        f"torch.cuda.is_available()={preflight['cuda_available']} "
        f"torch.cuda.device_count()={preflight['cuda_device_count']} "
        f"target_device={preflight['target_device']}"
    )

    plans: list[tuple[str, Path, Path, str, list[str]]] = []
    for size in sizes:
        subset_path = _subset_path(subset_dir, size=size, seed=int(args.seed))
        if not subset_path.is_file():
            raise RuntimeError(f"missing subset file: {subset_path}")
        run_name = _run_name(size=size, seed=int(args.seed), tag=tag)
        run_root = out_root / run_name
        contract_line = _run_contract_line(run_name=run_name, subset_path=subset_path, eval_pairs=eval_pairs, args=args)
        train_cmd = _build_train_cmd(args, python_bin=python_bin, subset_path=subset_path, run_name=run_name, out_root=out_root)
        plans.append((run_name, subset_path, run_root, contract_line, train_cmd))

    for run_name, subset_path, _, contract_line, train_cmd in plans:
        print(f"[plan] run_name={run_name} subset={subset_path}")
        print(contract_line)
        print("[train-cmd]", shlex.join(train_cmd))
        print("[eval] pairs=", eval_pairs)

    if not args.launch:
        return 0

    for run_name, _, run_root, contract_line, train_cmd in plans:
        logs_dir = run_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        contract_path = run_root / "run_contract.txt"
        contract_path.write_text(contract_line + "\n", encoding="utf-8")
        train_log = logs_dir / "stage_a_cpu_matrix.log"
        supervisor_log = logs_dir / "stage_a_live_eval.log"
        manifest_path = run_root / "stage_a_live_eval" / "manifest.jsonl"
        scoreboard_path = run_root / "stage_a_live_eval" / "scoreboard.md"
        evaluated: set[str] = set()
        _log_line(supervisor_log, contract_line)
        _log_line(supervisor_log, f"[train-run] cmd={shlex.join(train_cmd)}")
        with train_log.open("w", encoding="utf-8") as train_fh:
            train_proc = subprocess.Popen(
                train_cmd,
                cwd=str(PROJECT_ROOT),
                stdout=train_fh,
                stderr=subprocess.STDOUT,
                text=True,
            )
            _log_line(supervisor_log, f"[train-pid] pid={train_proc.pid}")
            while True:
                _maybe_eval_new_checkpoints(
                    args,
                    python_bin=python_bin,
                    eval_pairs=eval_pairs,
                    run_root=run_root,
                    manifest_path=manifest_path,
                    scoreboard_path=scoreboard_path,
                    supervisor_log=supervisor_log,
                    evaluated=evaluated,
                )
                rc = train_proc.poll()
                if rc is not None:
                    break
                time.sleep(max(1.0, float(args.poll_seconds)))
            train_fh.flush()
        _maybe_eval_new_checkpoints(
            args,
            python_bin=python_bin,
            eval_pairs=eval_pairs,
            run_root=run_root,
            manifest_path=manifest_path,
            scoreboard_path=scoreboard_path,
            supervisor_log=supervisor_log,
            evaluated=evaluated,
        )
        _log_line(supervisor_log, f"[train-done] run_name={run_name} returncode={train_proc.returncode}")
        if train_proc.returncode != 0:
            raise RuntimeError(f"training failed for {run_name}; see {train_log}")
        print(f"[done] run_name={run_name} scoreboard={scoreboard_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
