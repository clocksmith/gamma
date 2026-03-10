#!/usr/bin/env python3
"""Launch a gold-shard Stage A grid and sweep greedy evals as checkpoints land."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
TRAINER_SCRIPT = PROJECT_ROOT / "projects" / "distillation" / "translation" / "training" / "train_translate_distill.py"
SWEEP_SCRIPT = PROJECT_ROOT / "projects" / "distillation" / "translation" / "pipeline" / "run_stage_b_checkpoint_sweep.py"
BUILD_INDEX_SCRIPT = PROJECT_ROOT / "projects" / "distillation" / "translation" / "pipeline" / "build_run_index.py"
REBUILD_BUNDLE_SCRIPT = (
    PROJECT_ROOT / "projects" / "distillation" / "translation" / "pipeline" / "rebuild_translation_results_bundle.py"
)
DEFAULT_PYTHON_BIN = PROJECT_ROOT / ".venv" / "bin" / "python"
DEFAULT_TEACHER_MODEL = (
    "/home/x/.cache/huggingface/hub/models--google--translategemma-4b-it/"
    "snapshots/10042cb0e6e7fdce748996a71dc3dc432a4e0c89"
)
DEFAULT_STUDENT_MODEL = (
    "/home/x/.cache/huggingface/hub/models--google--gemma-3-1b-it/"
    "snapshots/dcc83ea841ab6100d6b47a070329e1ba4cf78752"
)
DEFAULT_GOLD_1280 = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold"
    / "translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl"
)
DEFAULT_GOLD_1920 = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.train_3x640.jsonl"
)
DEFAULT_GOLD_2560 = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.train_4x640.jsonl"
)
DEFAULT_EVAL2 = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "translate_distill_pairs.eval2_wmt13_enes_128.jsonl"
)
DEFAULT_EVAL3 = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl"
)
DEFAULT_DATASETS: dict[int, tuple[Path, ...]] = {
    1280: (DEFAULT_GOLD_1280,),
    1920: (DEFAULT_GOLD_1920,),
    2560: (DEFAULT_GOLD_2560,),
}


def _parse_sizes(value: str) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()
    for raw in str(value).split(","):
        text = raw.strip()
        if not text:
            continue
        size = int(text)
        if size <= 0:
            raise ValueError(f"grid sizes must be positive: {text}")
        if size in seen:
            continue
        out.append(size)
        seen.add(size)
    if not out:
        raise ValueError("at least one grid size is required")
    return out


def _resolve_path(value: str | Path) -> Path:
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


def _runtime_mode(device: str, hsa_override: str) -> str:
    if str(device).strip().lower() == "cpu":
        return "cpu"
    return "rocm_gfx_override" if str(hsa_override).strip() else "normal_rocm"


def _now_utc() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _safe_rel(path: Path, root: Path = PROJECT_ROOT) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def _count_jsonl_rows(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


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
            "'hip_version': getattr(torch.version, 'hip', ''), "
            "'target_device': '" + str(device) + "'"
            "}, sort_keys=True))"
        ),
    ]
    proc = subprocess.run(probe, check=True, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    lines = (proc.stdout or "").strip().splitlines()
    if not lines:
        raise RuntimeError("empty preflight output")
    return json.loads(lines[-1])


def _probe_compute(python_bin: Path, *, hsa_override_gfx_version: str) -> dict[str, Any]:
    env = os.environ.copy()
    if str(hsa_override_gfx_version).strip():
        env["HSA_OVERRIDE_GFX_VERSION"] = str(hsa_override_gfx_version).strip()
    probe = [
        str(python_bin),
        "-c",
        (
            "import json\n"
            "import torch\n"
            "out = {\n"
            "    'cuda_available': bool(torch.cuda.is_available()),\n"
            "    'cuda_device_count': int(torch.cuda.device_count()),\n"
            "}\n"
            "if torch.cuda.is_available() and torch.cuda.device_count() > 0:\n"
            "    x = torch.randn(256, 256, device='cuda')\n"
            "    y = torch.randn(256, 256, device='cuda')\n"
            "    out['cuda_matmul_ok'] = float((x @ y).mean().item())\n"
            "print(json.dumps(out, sort_keys=True))\n"
        ),
    ]
    proc = subprocess.run(probe, capture_output=True, text=True, cwd=str(PROJECT_ROOT), env=env)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"compute probe failed in runtime mode {_runtime_mode('cuda', hsa_override_gfx_version)}: {detail}")
    lines = (proc.stdout or "").strip().splitlines()
    if not lines:
        raise RuntimeError("compute probe produced no output")
    return json.loads(lines[-1])


def _parse_dataset_paths(value: str) -> list[Path]:
    out: list[Path] = []
    for raw in str(value).split(","):
        text = raw.strip()
        if not text:
            continue
        out.append(_resolve_path(text))
    if not out:
        raise RuntimeError("dataset override must include at least one jsonl path")
    return out


def _dataset_specs(args: argparse.Namespace) -> dict[int, list[Path]]:
    dataset_map = {size: list(paths) for size, paths in DEFAULT_DATASETS.items()}
    overridden: set[int] = set()
    for spec in args.dataset:
        if "=" not in spec:
            raise RuntimeError(f"invalid --dataset spec, expected size=path: {spec}")
        size_text, path_text = spec.split("=", 1)
        size = int(size_text.strip())
        if size not in overridden:
            dataset_map[size] = []
            overridden.add(size)
        dataset_map[size].extend(_parse_dataset_paths(path_text.strip()))
    return dataset_map


def _dataset_spec_text(paths: list[Path]) -> str:
    if len(paths) == 1:
        return str(paths[0])
    return "merge_jsonl(" + ",".join(str(path) for path in paths) + ")"


def _materialized_dataset_path(*, run_root: Path, size: int, source_paths: list[Path]) -> Path:
    if len(source_paths) == 1:
        return source_paths[0]
    return run_root / "inputs" / f"train_pairs.rows{size}.merged.jsonl"


def _normalize_translation_pair_row(obj: dict[str, Any], *, path: Path, line_no: int) -> dict[str, Any]:
    src_lang = str(obj.get("src_lang") or obj.get("source_lang") or obj.get("src") or "").strip()
    tgt_lang = str(obj.get("tgt_lang") or obj.get("target_lang") or obj.get("tgt") or "").strip()
    source = str(obj.get("source") or obj.get("query") or "").strip()
    target_pos = str(obj.get("target_pos") or obj.get("pos") or "").strip()
    target_neg = str(obj.get("target_neg") or obj.get("neg") or "").strip()
    pair = str(obj.get("pair") or "").strip()
    if not pair and src_lang and tgt_lang:
        pair = f"{src_lang}-{tgt_lang}"
    missing: list[str] = []
    if not src_lang:
        missing.append("src_lang")
    if not tgt_lang:
        missing.append("tgt_lang")
    if not source:
        missing.append("source")
    if not target_pos:
        missing.append("target_pos")
    if not target_neg:
        missing.append("target_neg")
    if not pair:
        missing.append("pair")
    if missing:
        raise RuntimeError(f"{path}:{line_no}: cannot normalize translation pair row; missing {missing}")
    expected_pair = f"{src_lang}-{tgt_lang}"
    if pair != expected_pair:
        raise RuntimeError(f"{path}:{line_no}: pair='{pair}' does not match src/tgt '{expected_pair}'")
    out = dict(obj)
    out["src_lang"] = src_lang
    out["tgt_lang"] = tgt_lang
    out["pair"] = pair
    out["source"] = source
    out["target_pos"] = target_pos
    out["target_neg"] = target_neg
    out["query"] = source
    out["pos"] = target_pos
    out["neg"] = target_neg
    out["lang"] = tgt_lang
    return out


def _write_merged_dataset(output_path: Path, source_paths: list[Path]) -> tuple[int, Path]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output_path.with_suffix(output_path.suffix + ".sources.json")
    row_count = 0
    source_rows: list[dict[str, Any]] = []
    with output_path.open("w", encoding="utf-8") as out_fh:
        for source_path in source_paths:
            source_count = 0
            with source_path.open("r", encoding="utf-8") as in_fh:
                for line_no, line in enumerate(in_fh, 1):
                    text = line.strip()
                    if not text:
                        continue
                    try:
                        obj = json.loads(text)
                    except Exception as exc:
                        raise RuntimeError(f"{source_path}:{line_no}: invalid JSON row: {exc}") from exc
                    if not isinstance(obj, dict):
                        raise RuntimeError(f"{source_path}:{line_no}: expected JSON object row")
                    normalized = _normalize_translation_pair_row(obj, path=source_path, line_no=line_no)
                    out_fh.write(json.dumps(normalized, ensure_ascii=True) + "\n")
                    row_count += 1
                    source_count += 1
            source_rows.append({"path": str(source_path), "rows": source_count})
    manifest_path.write_text(
        json.dumps(
            {
                "output_path": str(output_path),
                "sources": source_rows,
                "total_rows": row_count,
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return row_count, manifest_path


def _run_name(size: int, tag: str) -> str:
    return f"translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows{size}_bf16_{tag}"


def _run_contract_line(
    *,
    run_name: str,
    pairs_input_spec: str,
    eval_paths: list[Path],
    args: argparse.Namespace,
) -> str:
    eval_text = ",".join(str(path) for path in eval_paths)
    return (
        "[run-contract] "
        f"run_name={run_name} "
        f"pairs_input_spec={pairs_input_spec} "
        "resume_from=none "
        "resume_stage=none "
        "decode=greedy "
        f"eval_dataset_paths={eval_text} "
        f"device={args.device} "
        "schedule=A_then_B "
        f"runtime_mode={_runtime_mode(str(args.device), str(args.hsa_override_gfx_version))}"
    )


def _build_train_cmd(
    args: argparse.Namespace,
    *,
    python_bin: Path,
    dataset_path: Path,
    run_name: str,
    out_root: Path,
) -> list[str]:
    summary_out = out_root / run_name / "train_summary.json"
    cmd = [
        str(python_bin),
        "-u",
        str(TRAINER_SCRIPT),
        "--pairs",
        str(dataset_path),
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
    if str(args.teacher_device).strip():
        cmd.extend(["--teacher-device", str(args.teacher_device).strip()])
    return cmd


def _checkpoint_step(path: Path) -> int:
    name = path.name
    if not name.startswith("checkpoint-"):
        return -1
    try:
        return int(name.split("-", 1)[1])
    except Exception:
        return -1


def _checkpoint_ready(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / "model.safetensors").is_file()
        and (path / "config.json").is_file()
        and (path / "training_state.pt").is_file()
    )


def _ready_checkpoints(stage_dir: Path) -> list[Path]:
    items = [child for child in stage_dir.glob("checkpoint-*") if _checkpoint_ready(child)]
    return sorted(items, key=_checkpoint_step)


def _build_sweep_cmd(
    args: argparse.Namespace,
    *,
    python_bin: Path,
    run_root: Path,
    checkpoints: list[Path],
) -> list[str]:
    out_dir = run_root / "stage_a_checkpoint_sweep_greedy"
    cmd = [
        str(python_bin),
        str(SWEEP_SCRIPT),
        "--run-root",
        str(run_root),
        "--stage-dir",
        "stage_a",
        "--checkpoints",
        ",".join(path.name for path in checkpoints),
        "--eval",
        f"eval2_external={args.eval2_pairs}",
        "--eval",
        f"eval3_indomain_clean={args.eval3_pairs}",
        "--source-langs",
        str(args.source_langs),
        "--target-langs",
        str(args.target_langs),
        "--batch-size",
        str(int(args.eval_batch_size)),
        "--max-prompt-length",
        str(int(args.eval_max_prompt_length)),
        "--max-new-tokens",
        str(int(args.eval_max_new_tokens)),
        "--device",
        str(args.eval_device),
        "--dtype",
        str(args.eval_dtype),
        "--seed",
        str(int(args.seed)),
        "--decode",
        "greedy",
        "--teacher-model",
        str(args.teacher_model),
        "--python-bin",
        str(python_bin),
        "--out-dir",
        str(out_dir),
        "--resume",
    ]
    if str(args.hsa_override_gfx_version).strip():
        cmd.extend(["--hsa-override-gfx-version", str(args.hsa_override_gfx_version).strip()])
    return cmd


def _log_line(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(text.rstrip() + "\n")


def _run_and_log(cmd: list[str], *, env: dict[str, str], log_path: Path) -> int:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), env=env)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.open("a", encoding="utf-8").write(
        "\n".join(
            [
                f"[timestamp] {_now_utc()}",
                f"[cmd] {shlex.join(cmd)}",
                f"[returncode] {proc.returncode}",
                "",
                "=== STDOUT ===",
                proc.stdout or "",
                "",
                "=== STDERR ===",
                proc.stderr or "",
                "",
            ]
        )
    )
    return int(proc.returncode)


def _refresh_reporting(python_bin: Path, *, log_path: Path) -> None:
    env = os.environ.copy()
    for script in (BUILD_INDEX_SCRIPT, REBUILD_BUNDLE_SCRIPT):
        rc = _run_and_log([str(python_bin), str(script)], env=env, log_path=log_path)
        if rc != 0:
            raise RuntimeError(f"report refresh failed for {script}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Launch the gold-shard Stage A grid with resumable checkpoint eval sweeps.")
    ap.add_argument("--sizes", default="1280,1920,2560", help="Comma-separated dataset sizes to run.")
    ap.add_argument(
        "--dataset",
        action="append",
        default=[],
        help=(
            "Optional override in form size=/abs/or/relative/path.jsonl or "
            "size=path_a.jsonl,path_b.jsonl. Repeat the same size to merge multiple files in order."
        ),
    )
    ap.add_argument("--tag", default="", help="Run-name suffix. Defaults to current UTC timestamp.")
    ap.add_argument("--teacher-model", default=DEFAULT_TEACHER_MODEL)
    ap.add_argument("--student-model", default=DEFAULT_STUDENT_MODEL)
    ap.add_argument("--out-root", default="projects/distillation/translation/runs")
    ap.add_argument("--python-bin", default="")
    ap.add_argument("--total-steps", type=int, default=8000)
    ap.add_argument("--sft-steps", type=int, default=8000)
    ap.add_argument("--save-every", type=int, default=2000)
    ap.add_argument("--keep-checkpoints", type=int, default=6)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--log-every", type=int, default=20)
    ap.add_argument("--max-prompt-length", type=int, default=256)
    ap.add_argument("--max-new-tokens", type=int, default=192)
    ap.add_argument("--dtype", default="bfloat16", choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--teacher-device", default="")
    ap.add_argument("--source-langs", default="en,es")
    ap.add_argument("--target-langs", default="en,es")
    ap.add_argument("--eval2-pairs", default=str(DEFAULT_EVAL2))
    ap.add_argument("--eval3-pairs", default=str(DEFAULT_EVAL3))
    ap.add_argument("--eval-batch-size", type=int, default=2)
    ap.add_argument("--eval-max-prompt-length", type=int, default=256)
    ap.add_argument("--eval-max-new-tokens", type=int, default=192)
    ap.add_argument("--eval-device", default="cuda")
    ap.add_argument("--eval-dtype", default="bfloat16", choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--poll-seconds", type=float, default=30.0)
    ap.add_argument(
        "--hsa-override-gfx-version",
        default="11.0.0",
        help="Runtime-mode override used for compute probe, training, and eval sweep.",
    )
    ap.add_argument("--launch", action="store_true", help="Run the planned grid instead of printing it.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    sizes = _parse_sizes(args.sizes)
    dataset_map = _dataset_specs(args)
    out_root = _resolve_path(args.out_root)
    python_bin = _resolve_python_bin(args.python_bin)
    eval2_pairs = _resolve_path(args.eval2_pairs)
    eval3_pairs = _resolve_path(args.eval3_pairs)
    tag = str(args.tag).strip() or dt.datetime.now(tz=dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if not TRAINER_SCRIPT.is_file():
        raise RuntimeError(f"trainer script not found: {TRAINER_SCRIPT}")
    if not SWEEP_SCRIPT.is_file():
        raise RuntimeError(f"sweep script not found: {SWEEP_SCRIPT}")
    for eval_path in (eval2_pairs, eval3_pairs):
        if not eval_path.is_file():
            raise RuntimeError(f"eval pairs file not found: {eval_path}")

    plans: list[dict[str, Any]] = []
    for size in sizes:
        source_paths = dataset_map.get(size)
        if source_paths is None:
            raise RuntimeError(f"no dataset configured for size {size}")
        resolved_sources = [_resolve_path(path) for path in source_paths]
        for source_path in resolved_sources:
            if not source_path.is_file():
                raise RuntimeError(f"dataset file not found for size {size}: {source_path}")
        row_count = sum(_count_jsonl_rows(source_path) for source_path in resolved_sources)
        if row_count != size:
            raise RuntimeError(
                f"dataset row count mismatch for size {size}: expected {size}, found {row_count} in {_dataset_spec_text(resolved_sources)}"
            )
        run_name = _run_name(size=size, tag=tag)
        run_root = out_root / run_name
        dataset_path = _materialized_dataset_path(run_root=run_root, size=size, source_paths=resolved_sources)
        dataset_spec = _dataset_spec_text(resolved_sources)
        contract_line = _run_contract_line(
            run_name=run_name,
            pairs_input_spec=dataset_spec,
            eval_paths=[eval2_pairs, eval3_pairs],
            args=args,
        )
        train_cmd = _build_train_cmd(
            args,
            python_bin=python_bin,
            dataset_path=dataset_path,
            run_name=run_name,
            out_root=out_root,
        )
        plans.append(
            {
                "size": size,
                "source_paths": resolved_sources,
                "dataset_spec": dataset_spec,
                "dataset_path": dataset_path,
                "row_count": row_count,
                "run_name": run_name,
                "run_root": run_root,
                "contract_line": contract_line,
                "train_cmd": train_cmd,
            }
        )

    preflight = _preflight(python_bin, str(args.device))
    print(
        "[preflight] "
        f"python={preflight['python']} "
        f"torch={preflight['torch_version']} "
        f"transformers={preflight['transformers_version']} "
        f"hip={preflight['hip_version']}"
    )
    print(
        "[preflight] "
        f"torch.cuda.is_available()={preflight['cuda_available']} "
        f"torch.cuda.device_count()={preflight['cuda_device_count']} "
        f"target_device={preflight['target_device']}"
    )
    if str(args.device).strip().lower() != "cpu":
        probe = _probe_compute(python_bin, hsa_override_gfx_version=str(args.hsa_override_gfx_version))
        print(
            "[preflight] "
            f"runtime_mode={_runtime_mode(str(args.device), str(args.hsa_override_gfx_version))} "
            f"cuda_available={probe['cuda_available']} "
            f"cuda_device_count={probe['cuda_device_count']} "
            f"cuda_matmul_ok={probe.get('cuda_matmul_ok')}"
        )

    for plan in plans:
        print(f"[plan] run_name={plan['run_name']} size={plan['size']} rows={plan['row_count']}")
        print(f"[plan] pairs_input_spec={plan['dataset_spec']}")
        print(f"[plan] dataset={plan['dataset_path']}")
        print(plan["contract_line"])
        print(f"[train-cmd] {shlex.join(plan['train_cmd'])}")
        print(
            "[eval-sweep] "
            f"eval2={eval2_pairs} "
            f"eval3={eval3_pairs} "
            f"device={args.eval_device} dtype={args.eval_dtype}"
        )

    if not args.launch:
        return 0

    child_env = os.environ.copy()
    if str(args.hsa_override_gfx_version).strip():
        child_env["HSA_OVERRIDE_GFX_VERSION"] = str(args.hsa_override_gfx_version).strip()

    for plan in plans:
        run_root = Path(plan["run_root"])
        if run_root.exists():
            raise RuntimeError(f"run root already exists: {run_root}")
        logs_dir = run_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        if len(plan["source_paths"]) > 1:
            merged_rows, manifest_path = _write_merged_dataset(Path(plan["dataset_path"]), list(plan["source_paths"]))
            if merged_rows != int(plan["row_count"]):
                raise RuntimeError(
                    f"merged dataset row count mismatch for {plan['run_name']}: expected {plan['row_count']}, found {merged_rows}"
                )
        else:
            manifest_path = None
        contract_path = run_root / "run_contract.txt"
        contract_path.write_text(str(plan["contract_line"]) + "\n", encoding="utf-8")

        train_log = logs_dir / "stage_a_gold_grid_train.log"
        sweep_log = logs_dir / "stage_a_gold_grid_sweep.log"
        supervisor_log = logs_dir / "stage_a_gold_grid_supervisor.log"
        reporting_log = logs_dir / "report_refresh.log"

        _log_line(supervisor_log, str(plan["contract_line"]))
        _log_line(supervisor_log, f"[dataset] rows={plan['row_count']} path={plan['dataset_path']}")
        _log_line(supervisor_log, f"[dataset] pairs_input_spec={plan['dataset_spec']}")
        if manifest_path is not None:
            _log_line(supervisor_log, f"[dataset-merge] manifest={manifest_path}")
        _log_line(supervisor_log, f"[train-run] cmd={shlex.join(plan['train_cmd'])}")

        swept_checkpoint_names: set[str] = set()
        with train_log.open("w", encoding="utf-8") as train_fh:
            train_proc = subprocess.Popen(
                plan["train_cmd"],
                cwd=str(PROJECT_ROOT),
                stdout=train_fh,
                stderr=subprocess.STDOUT,
                text=True,
                env=child_env,
            )
            _log_line(supervisor_log, f"[train-pid] pid={train_proc.pid}")
            while True:
                stage_dir = run_root / "stage_a"
                ready = _ready_checkpoints(stage_dir) if stage_dir.is_dir() else []
                pending = [path for path in ready if path.name not in swept_checkpoint_names]
                if pending:
                    sweep_cmd = _build_sweep_cmd(args, python_bin=python_bin, run_root=run_root, checkpoints=pending)
                    _log_line(supervisor_log, f"[sweep-run] checkpoints={','.join(path.name for path in pending)}")
                    rc = _run_and_log(sweep_cmd, env=child_env, log_path=sweep_log)
                    _log_line(supervisor_log, f"[sweep-done] returncode={rc}")
                    if rc == 0:
                        swept_checkpoint_names.update(path.name for path in pending)
                rc = train_proc.poll()
                if rc is not None:
                    break
                time.sleep(max(1.0, float(args.poll_seconds)))
            train_fh.flush()

        ready = _ready_checkpoints(run_root / "stage_a")
        pending = [path for path in ready if path.name not in swept_checkpoint_names]
        if pending:
            sweep_cmd = _build_sweep_cmd(args, python_bin=python_bin, run_root=run_root, checkpoints=pending)
            _log_line(supervisor_log, f"[sweep-final] checkpoints={','.join(path.name for path in pending)}")
            rc = _run_and_log(sweep_cmd, env=child_env, log_path=sweep_log)
            _log_line(supervisor_log, f"[sweep-final-done] returncode={rc}")

        _log_line(supervisor_log, f"[train-done] run_name={plan['run_name']} returncode={train_proc.returncode}")
        if train_proc.returncode != 0:
            raise RuntimeError(f"training failed for {plan['run_name']}; see {train_log}")
        _refresh_reporting(python_bin, log_path=reporting_log)
        print(f"[done] run_name={plan['run_name']} scoreboard={run_root / 'stage_a_checkpoint_sweep_greedy' / 'scoreboard.md'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
