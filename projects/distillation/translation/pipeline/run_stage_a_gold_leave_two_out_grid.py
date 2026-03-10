#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[4]
PIPELINE_DIR = PROJECT_ROOT / "projects" / "distillation" / "translation" / "pipeline"
TRAINING_DATA_DIR = PROJECT_ROOT / "projects" / "distillation" / "translation" / "training_data"
RUNS_DIR = PROJECT_ROOT / "projects" / "distillation" / "translation" / "runs"
GRID_SCRIPT = PIPELINE_DIR / "run_stage_a_gold_shard_grid.py"

DEFAULT_PACK_PATHS = {
    "pack_01": TRAINING_DATA_DIR / "gold_shards_rebucketed" / "gold_rebucketed_320.pack_01.q97_4484.rows320.jsonl",
    "pack_02": TRAINING_DATA_DIR / "gold_shards_rebucketed" / "gold_rebucketed_320.pack_02.q97_1397.rows320.jsonl",
    "pack_03": TRAINING_DATA_DIR / "gold_shards_rebucketed" / "gold_rebucketed_320.pack_03.q96_4352.rows320.jsonl",
    "pack_04": TRAINING_DATA_DIR / "gold_shards_rebucketed" / "gold_rebucketed_320.pack_04.q96_3328.rows320.jsonl",
    "pack_05": TRAINING_DATA_DIR / "gold_shards_rebucketed" / "gold_rebucketed_320.pack_05.q96_0642.rows320.jsonl",
    "pack_06": TRAINING_DATA_DIR / "gold_shards_rebucketed" / "gold_rebucketed_320.pack_06.q95_9634.rows320.jsonl",
    "pack_07": TRAINING_DATA_DIR / "gold_shards_rebucketed" / "gold_rebucketed_320.pack_07.q96_0567.rows320.jsonl",
    "pack_08": TRAINING_DATA_DIR / "gold_shards_rebucketed" / "gold_rebucketed_320.pack_08.q97_3716.rows320.jsonl",
}

DEFAULT_EXTERNAL_EVAL = TRAINING_DATA_DIR / "translate_distill_pairs.eval2_wmt13_enes_128.jsonl"
DEFAULT_INDOMAIN_EVAL = TRAINING_DATA_DIR / "translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl"

DONE_RE = re.compile(r"^\[done\] run_name=(\S+) scoreboard=(\S+)$")
CHECKPOINT_RE = re.compile(r"^checkpoint-(\d+)$")


@dataclass
class PlanEntry:
    label: str
    size: int
    included_packs: list[str]
    omitted_packs: list[str]
    dataset_paths: list[str]
    anchor: bool


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _short_pack_name(name: str) -> str:
    return name.split("_", 1)[1]


def _parse_csv_steps(value: str) -> list[int]:
    steps = []
    for part in value.split(","):
        item = part.strip()
        if not item:
            continue
        steps.append(int(item))
    if not steps:
        raise argparse.ArgumentTypeError("expected at least one checkpoint step")
    return steps


def _resolve_python_bin(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            path = (PROJECT_ROOT / path).resolve()
        return path
    candidate = PROJECT_ROOT / ".venv" / "bin" / "python"
    if candidate.is_file():
        return candidate
    return Path(sys.executable)


def _run_small_python(python_bin: Path, code: str, *, env: dict[str, str] | None = None) -> list[str]:
    proc = subprocess.run(
        [str(python_bin), "-c", code],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )
    output = proc.stdout.strip().splitlines()
    for line in output:
        print(line)
    return output


def _preflight(
    *,
    python_bin: Path,
    device: str,
    hsa_override_gfx_version: str,
    dataset_paths: Sequence[Path],
    eval_paths: Sequence[Path],
) -> None:
    print(f"[preflight] python_bin={python_bin}")
    if not python_bin.is_file():
        raise RuntimeError(f"python binary not found: {python_bin}")
    _run_small_python(python_bin, "import torch, transformers; print('torch_ok'); print('transformers_ok')")
    _run_small_python(
        python_bin,
        "import torch; print(f'cuda_available {torch.cuda.is_available()}'); print(f'cuda_device_count {torch.cuda.device_count()}')",
    )
    if device == "cuda":
        probe_env = os.environ.copy()
        runtime_mode = "normal_rocm"
        if hsa_override_gfx_version.strip():
            probe_env["HSA_OVERRIDE_GFX_VERSION"] = hsa_override_gfx_version.strip()
            runtime_mode = "rocm_gfx_override"
        _run_small_python(
            python_bin,
            "import torch; "
            "print(f'cuda_available {torch.cuda.is_available()}'); "
            "print(f'cuda_device_count {torch.cuda.device_count()}'); "
            "x=torch.randn(64,64,device='cuda'); "
            "y=torch.randn(64,64,device='cuda'); "
            "print(f'cuda_matmul_ok {float((x@y).mean().item())}')",
            env=probe_env,
        )
        print(f"[preflight] runtime_mode={runtime_mode}")
    missing = [str(path) for path in list(dataset_paths) + list(eval_paths) if not path.exists()]
    if missing:
        raise RuntimeError(f"missing required files: {missing}")
    for path in dataset_paths:
        print(f"[preflight] dataset={path}")
    for path in eval_paths:
        print(f"[preflight] eval={path}")


def _build_plan(include_anchors: bool, pack_paths: dict[str, Path]) -> list[PlanEntry]:
    pack_names = sorted(pack_paths)
    entries: list[PlanEntry] = []
    if include_anchors:
        entries.append(
            PlanEntry(
                label="rows1280_legacy_gold_control",
                size=1280,
                included_packs=[],
                omitted_packs=[],
                dataset_paths=[],
                anchor=True,
            )
        )
        entries.append(
            PlanEntry(
                label="rows2560_allpacks_clean",
                size=2560,
                included_packs=pack_names,
                omitted_packs=[],
                dataset_paths=[str(pack_paths[name]) for name in pack_names],
                anchor=True,
            )
        )
    for omitted in itertools.combinations(pack_names, 2):
        included = [name for name in pack_names if name not in omitted]
        entries.append(
            PlanEntry(
                label=f"rows1920_drop_{_short_pack_name(omitted[0])}_{_short_pack_name(omitted[1])}",
                size=1920,
                included_packs=included,
                omitted_packs=list(omitted),
                dataset_paths=[str(pack_paths[name]) for name in included],
                anchor=False,
            )
        )
    return entries


def _filter_plan(entries: list[PlanEntry], only_labels: Sequence[str], start_index: int, limit: int | None) -> list[PlanEntry]:
    filtered = entries
    if only_labels:
        wanted = set(only_labels)
        filtered = [entry for entry in filtered if entry.label in wanted]
    if start_index > 0:
        filtered = filtered[start_index:]
    if limit is not None:
        filtered = filtered[:limit]
    return filtered


def _build_grid_command(entry: PlanEntry, args: argparse.Namespace, python_bin: Path) -> list[str]:
    cmd = [
        str(python_bin),
        str(GRID_SCRIPT),
        "--sizes",
        str(entry.size),
        "--total-steps",
        str(args.total_steps),
        "--sft-steps",
        str(args.sft_steps),
        "--save-every",
        str(args.save_every),
        "--keep-checkpoints",
        str(len(args.keep_steps)),
        "--device",
        args.device,
        "--dtype",
        args.dtype,
        "--seed",
        str(args.seed),
    ]
    if args.hsa_override_gfx_version is not None:
        cmd.extend(["--hsa-override-gfx-version", args.hsa_override_gfx_version])
    if entry.dataset_paths:
        cmd.extend(["--dataset", f"{entry.size}={','.join(entry.dataset_paths)}"])
    if args.launch:
        cmd.append("--launch")
    return cmd


def _stream_command(cmd: Sequence[str], *, env: dict[str, str]) -> tuple[int, str | None]:
    proc = subprocess.Popen(
        list(cmd),
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    run_name: str | None = None
    assert proc.stdout is not None
    for raw_line in proc.stdout:
        line = raw_line.rstrip("\n")
        print(line)
        match = DONE_RE.match(line)
        if match:
            run_name = match.group(1)
    proc.wait()
    return proc.returncode, run_name


def _prune_stage_a_checkpoints(run_root: Path, keep_steps: set[int]) -> list[str]:
    stage_dir = run_root / "stage_a"
    if not stage_dir.is_dir():
        return []
    removed: list[str] = []
    for checkpoint_dir in sorted(stage_dir.glob("checkpoint-*")):
        match = CHECKPOINT_RE.match(checkpoint_dir.name)
        if not match:
            continue
        step = int(match.group(1))
        if step in keep_steps:
            continue
        shutil.rmtree(checkpoint_dir)
        removed.append(str(checkpoint_dir))
    return removed


def _write_manifest(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the gold leave-two-out 1920 grid plus anchors sequentially.")
    parser.add_argument("--python-bin", default=None, help="Python interpreter to use. Defaults to .venv/bin/python if present.")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dtype", default="bfloat16")
    parser.add_argument("--hsa-override-gfx-version", default="11.0.0")
    parser.add_argument("--total-steps", type=int, default=6000)
    parser.add_argument("--sft-steps", type=int, default=6000)
    parser.add_argument("--save-every", type=int, default=2000)
    parser.add_argument("--keep-steps", type=_parse_csv_steps, default=[2000, 4000, 6000])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--launch", action="store_true", help="Actually run the experiment sequence.")
    parser.add_argument("--include-anchors", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--only-label", action="append", default=[], help="Restrict execution to specific plan labels.")
    parser.add_argument("--start-index", type=int, default=0, help="Skip the first N plan entries after filtering.")
    parser.add_argument("--limit", type=int, default=None, help="Run at most N plan entries after filtering.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _make_parser()
    args = parser.parse_args(argv)

    if args.total_steps != args.sft_steps:
        raise RuntimeError("this launcher expects Stage A only, so total_steps must equal sft_steps")
    if any(step <= 0 for step in args.keep_steps):
        raise RuntimeError("keep steps must be positive")
    if any(step > args.total_steps for step in args.keep_steps):
        raise RuntimeError("keep steps cannot exceed total_steps")
    if any(step % args.save_every != 0 for step in args.keep_steps):
        raise RuntimeError("all keep steps must align with save_every")

    python_bin = _resolve_python_bin(args.python_bin)
    pack_paths = {name: path.resolve() for name, path in DEFAULT_PACK_PATHS.items()}
    eval_paths = [DEFAULT_EXTERNAL_EVAL.resolve(), DEFAULT_INDOMAIN_EVAL.resolve()]

    _preflight(
        python_bin=python_bin,
        device=args.device,
        hsa_override_gfx_version=args.hsa_override_gfx_version,
        dataset_paths=list(pack_paths.values()),
        eval_paths=eval_paths,
    )

    entries = _filter_plan(
        _build_plan(args.include_anchors, pack_paths),
        only_labels=args.only_label,
        start_index=args.start_index,
        limit=args.limit,
    )
    if not entries:
        raise RuntimeError("no plan entries selected")

    manifest_path = RUNS_DIR / "orchestrator_manifests" / f"gold_leave_two_out_grid_{_utc_timestamp()}.json"
    manifest = {
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "python_bin": str(python_bin),
        "device": args.device,
        "dtype": args.dtype,
        "hsa_override_gfx_version": args.hsa_override_gfx_version,
        "total_steps": args.total_steps,
        "sft_steps": args.sft_steps,
        "save_every": args.save_every,
        "keep_steps": args.keep_steps,
        "entries": [],
    }

    for idx, entry in enumerate(entries, start=1):
        cmd = _build_grid_command(entry, args, python_bin)
        record = {
            **asdict(entry),
            "index": idx,
            "command": cmd,
            "status": "pending" if args.launch else "planned",
            "returncode": None,
            "run_name": None,
            "run_root": None,
            "pruned_checkpoints": [],
        }
        manifest["entries"].append(record)
    _write_manifest(manifest_path, manifest)

    print(f"[plan] manifest={manifest_path}")
    print(f"[plan] runs={len(entries)} keep_steps={args.keep_steps}")
    for record in manifest["entries"]:
        print(f"[plan-entry] index={record['index']} label={record['label']} size={record['size']}")

    if not args.launch:
        return 0

    child_env = os.environ.copy()
    if args.hsa_override_gfx_version.strip():
        child_env["HSA_OVERRIDE_GFX_VERSION"] = args.hsa_override_gfx_version.strip()

    keep_steps = set(args.keep_steps)
    for record in manifest["entries"]:
        print(f"[launch] index={record['index']} label={record['label']}")
        record["status"] = "running"
        _write_manifest(manifest_path, manifest)

        returncode, run_name = _stream_command(record["command"], env=child_env)
        record["returncode"] = returncode
        record["run_name"] = run_name

        if returncode != 0:
            record["status"] = "failed"
            _write_manifest(manifest_path, manifest)
            raise RuntimeError(f"run failed for {record['label']} with returncode={returncode}")

        if run_name:
            run_root = RUNS_DIR / run_name
            record["run_root"] = str(run_root)
            record["pruned_checkpoints"] = _prune_stage_a_checkpoints(run_root, keep_steps)
        record["status"] = "completed"
        _write_manifest(manifest_path, manifest)
        print(
            f"[completed] index={record['index']} label={record['label']} "
            f"run_name={record['run_name']} pruned={len(record['pruned_checkpoints'])}"
        )

    print(f"[done] manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
