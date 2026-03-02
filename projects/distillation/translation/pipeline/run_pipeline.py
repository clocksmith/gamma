#!/usr/bin/env python3
"""Unified TranslateGemma distillation pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
VOCAB_SUBSET_SCRIPT = PROJECT_ROOT / "tools" / "vocab_subset.py"
SUBSET_TEXT_BUILDER = Path(__file__).resolve().parent / "build_vocab_subset_text.py"
MAKE_PAIRS_SCRIPT = Path(__file__).resolve().parents[4] / "projects" / "distillation" / "translation" / "training" / "make_translate_distill_pairs.py"
SPLIT_PAIRS_SCRIPT = Path(__file__).resolve().parents[4] / "projects" / "distillation" / "translation" / "training" / "split_translate_distill_pairs.py"
TRAINER_SCRIPT = Path(__file__).resolve().parents[4] / "projects" / "distillation" / "translation" / "training" / "train_translate_distill.py"
EVAL_SCRIPT = Path(__file__).resolve().parents[4] / "projects" / "distillation" / "translation" / "eval" / "run_translate_distill_eval.py"


def _parse_csv(value: str) -> list[str]:
    return [x.strip() for x in str(value).split(",") if x.strip()]


def _parse_steps(value: str) -> list[str]:
    valid = {"init", "pairs", "split", "subset", "train", "eval"}
    requested = []
    for token in _parse_csv(str(value)):
        if token not in valid:
            raise SystemExit(f"Invalid step: {token}. Valid: {sorted(valid)}")
        requested.append(token)
    return requested


def _has_subset_model_artifacts(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    if not (path / "config.json").exists():
        return False
    if (path / "model.safetensors").exists() or (path / "pytorch_model.bin").exists() or (path / "pytorch_model.bin.index.json").exists():
        return True
    for pat in ("*.safetensors", "*.bin"):
        for match in path.glob(pat):
            if match.is_file():
                return True
    return False


def _resolve_path(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else base / p


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _run(cmd: list[str], *, dry_run: bool) -> None:
    print("+", " ".join(cmd))
    if not dry_run:
        subprocess.run(cmd, check=True)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _config_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _write_done_manifest(path: Path, *, step: str, config_hash: str, outputs: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "step": step,
        "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config_hash": config_hash,
        "outputs": [
            {
                "path": str(p),
                "bytes": int(p.stat().st_size),
                "sha256": _sha256_file(p),
            }
            for p in outputs
            if p.exists() and p.is_file()
        ],
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _done_manifest_matches(path: Path, *, config_hash: str, outputs: list[Path]) -> bool:
    if not path.exists():
        return False
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if str(obj.get("config_hash", "")) != str(config_hash):
        return False
    by_path = {
        str(item.get("path", "")): item
        for item in obj.get("outputs", [])
        if isinstance(item, dict) and item.get("path")
    }
    for out in outputs:
        if not out.exists() or not out.is_file():
            return False
        rec = by_path.get(str(out))
        if not rec:
            return False
        try:
            want_bytes = int(rec.get("bytes", -1))
        except Exception:
            return False
        if int(out.stat().st_size) != want_bytes:
            return False
        if str(rec.get("sha256", "")) != _sha256_file(out):
            return False
    return True


def _build_pair_args(src_langs: list[str], tgt_langs: list[str], seed_dir: Path, *, allow_same_lang: bool) -> list[str]:
    pair_args: list[str] = []
    for src in src_langs:
        src_file = seed_dir / f"{src}.txt"
        if not src_file.exists():
            raise SystemExit(f"Missing source seed file: {src_file}")

        for tgt in tgt_langs:
            if not allow_same_lang and src == tgt:
                continue
            tgt_file = seed_dir / f"{src}_to_{tgt}.txt"
            if not tgt_file.exists():
                raise SystemExit(f"Missing target seed file: {tgt_file}")
            pair_args.extend(["--pair-file", src, tgt, str(src_file), str(tgt_file)])
    return pair_args


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-dir", default="projects/distillation/translation")
    ap.add_argument("--steps", default="pairs,split,subset,train,eval")

    ap.add_argument("--source-langs", default="en,es")
    ap.add_argument("--target-langs", default="en,es")
    ap.add_argument("--seed-dir", default="bitext")
    ap.add_argument("--allow-same-lang-pairs", action="store_true")

    ap.add_argument("--pairs", default="training_data/translate_distill_pairs.jsonl")
    ap.add_argument("--pairs-summary-out", default="")
    ap.add_argument("--pairs-per-pair", type=int, default=1250)
    ap.add_argument("--pairs-min-chars", type=int, default=8)
    ap.add_argument("--pairs-neg-strategy", default="lexical_hard")
    ap.add_argument("--pairs-hard-neg-pool", type=int, default=128)
    ap.add_argument("--pairs-seed", type=int, default=42)
    ap.add_argument("--pairs-max-rows-per-input", type=int, default=0)
    ap.add_argument(
        "--pairs-allow-line-mismatch",
        action="store_true",
        help="If set, truncate parallel pair files to shortest length on line mismatch.",
    )

    ap.add_argument("--split-train-out", default="training_data/translate_distill_pairs.train.jsonl")
    ap.add_argument("--split-eval-out", default="training_data/translate_distill_pairs.eval.jsonl")
    ap.add_argument("--split-eval-fraction", type=float, default=0.10)
    ap.add_argument("--split-eval-max-rows", type=int, default=0)
    ap.add_argument("--split-min-eval-per-pair", type=int, default=1)

    ap.add_argument("--teacher-model", default="google/translategemma-4b-it")
    ap.add_argument("--student-model", default="google/translategemma-4b-it")
    ap.add_argument("--vocab-subset-dir", default="")
    ap.add_argument(
        "--tokenizer-model",
        default="",
        help="Tokenizer/model reference for student tokenization when --vocab-subset-dir is set.",
    )
    ap.add_argument("--subset-top-k", type=int, default=50000)
    ap.add_argument("--subset-min-count", type=int, default=2)
    ap.add_argument("--subset-max-lines", type=int, default=None)
    ap.add_argument("--subset-model", default="")
    ap.add_argument("--subset-min-text-chars", type=int, default=4)
    ap.add_argument(
        "--subset-for-causal-lm",
        action="store_true",
        help="Build subset checkpoints with CausalLM compatibility (keeps lm_head/output projection).",
    )
    ap.add_argument(
        "--no-subset-for-causal-lm",
        dest="subset_for_causal_lm",
        action="store_false",
        help="Disable CausalLM-compatible subset outputs.",
    )
    ap.set_defaults(subset_for_causal_lm=True)
    ap.add_argument(
        "--subset-text",
        action="append",
        default=[],
        help="Optional extra text files to include in vocab subset construction (repeatable).",
    )
    ap.add_argument("--subset-write-checkpoint", action="store_true", help="Write pruned subset checkpoint files.")
    ap.add_argument("--no-subset-write-checkpoint", dest="subset_write_checkpoint", action="store_false")
    ap.set_defaults(subset_write_checkpoint=True)
    ap.add_argument("--subset-fill-to-top-k", action="store_true")
    ap.add_argument("--no-subset-fill-to-top-k", dest="subset_fill_to_top_k", action="store_false")
    ap.set_defaults(subset_fill_to_top_k=True)
    ap.add_argument("--subset-fill-strategy", default="spm_score", choices=["spm_score", "id"])
    ap.add_argument("--subset-dtype", default="auto", choices=["auto", "fp16", "bf16", "fp32"])
    ap.add_argument("--subset-also-prune-output", action="store_true")
    ap.add_argument("--subset-allow-download", action="store_true", help="Allow HF downloads for subset stage.")
    ap.add_argument("--subset-name", default="vocab_subset", help="Directory name under run root for generated subset.")
    ap.add_argument("--out-root", default="projects/distillation/translation/runs/exp01")
    ap.add_argument("--run-name", default="exp01")
    ap.add_argument("--schedule", default="A_then_B", choices=["A_then_B", "mixed_from_start"])
    ap.add_argument("--total-steps", type=int, default=100000)
    ap.add_argument("--sft-steps", type=int, default=50000)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--log-every", type=int, default=20)
    ap.add_argument("--save-every", type=int, default=200)
    ap.add_argument("--select-best-checkpoint", action="store_true")
    ap.add_argument("--no-select-best-checkpoint", dest="select_best_checkpoint", action="store_false")
    ap.set_defaults(select_best_checkpoint=True)
    ap.add_argument("--lambda-kd", type=float, default=0.5)
    ap.add_argument("--mu-triplet", type=float, default=0.1)
    ap.add_argument("--margin", type=float, default=0.2)
    ap.add_argument("--kd-temperature", type=float, default=1.0)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--grad-clip", type=float, default=1.0)
    ap.add_argument("--accum-steps", type=int, default=1)
    ap.add_argument("--max-prompt-length", type=int, default=256)
    ap.add_argument("--max-seq-length", type=int, default=1536)
    ap.add_argument("--predict-samples", type=int, default=0)
    ap.add_argument("--max-new-tokens", type=int, default=192)
    ap.add_argument("--summary-out", default="")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dtype", default="auto", choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument("--device", default="auto")
    ap.add_argument("--teacher-device", default="")
    ap.add_argument("--enable-lora", action="store_true")
    ap.add_argument("--lora-rank", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--lora-dropout", type=float, default=0.05)
    ap.add_argument("--lora-modules", default="q_proj,k_proj,v_proj,o_proj,up_proj,down_proj,gate_proj")
    ap.add_argument("--skip-kd-when-device-mismatch", action="store_true")

    ap.add_argument("--eval-model", default="final")
    ap.add_argument("--eval-out-dir", default="eval")
    ap.add_argument("--eval-samples", type=int, default=0)
    ap.add_argument("--eval-batch-size", type=int, default=2)
    ap.add_argument("--eval-max-prompt-length", type=int, default=256)
    ap.add_argument("--eval-max-new-tokens", type=int, default=192)
    ap.add_argument("--eval-seed", type=int, default=42)
    ap.add_argument("--eval-do-sample", action="store_true")
    ap.add_argument("--eval-temperature", type=float, default=0.0)
    ap.add_argument("--eval-top-p", type=float, default=1.0)
    ap.add_argument("--eval-top-k", type=int, default=50)
    ap.add_argument("--eval-teacher-model", default="")
    ap.add_argument("--eval-bleu", action="store_true", default=True)
    ap.add_argument("--eval-chrf", action="store_true", default=True)
    ap.add_argument("--eval-comet", action="store_true")
    ap.add_argument("--eval-comet-model", default="Unbabel/wmt22-comet-da")
    ap.add_argument("--eval-comet-batch-size", type=int, default=8)
    ap.add_argument("--eval-student-summary", default="student_eval_summary.json")
    ap.add_argument("--eval-teacher-summary", default="teacher_eval_summary.json")
    ap.add_argument("--eval-compare-summary", default="compare_eval_summary.json")
    ap.add_argument("--eval-student-predictions", default="student_predictions.jsonl")
    ap.add_argument("--eval-teacher-predictions", default="teacher_predictions.jsonl")

    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--resume-from", default="")
    ap.add_argument("--allow-download", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    workspace = _resolve_path(PROJECT_ROOT, args.workspace_dir)
    steps = _parse_steps(args.steps)
    source_langs = _parse_csv(args.source_langs)
    target_langs = _parse_csv(args.target_langs)
    source_seed_dir = _resolve_path(workspace, args.seed_dir)
    pairs_path = _resolve_path(workspace, args.pairs)
    split_train_path = _resolve_path(workspace, args.split_train_out)
    split_eval_path = _resolve_path(workspace, args.split_eval_out)
    out_root = _resolve_path(PROJECT_ROOT, args.out_root)
    run_root = out_root / args.run_name
    state_dir = run_root / "pipeline_state"
    py = sys.executable
    explicit_subset_dir = None
    if str(args.vocab_subset_dir).strip():
        explicit_subset_dir = _resolve_path(workspace, args.vocab_subset_dir)
    subset_dir_fallback = run_root / str(args.subset_name)
    subset_model = str(args.subset_model).strip() or str(args.student_model)
    subset_text_path = run_root / "vocab_subset_text_source.txt"
    extra_subset_texts: list[Path] = []
    for item in args.subset_text:
        p = Path(item)
        extra_subset_texts.append(p if p.is_absolute() else workspace / p)
        if not extra_subset_texts[-1].exists():
            raise SystemExit(f"Missing --subset-text file: {extra_subset_texts[-1]}")
    effective_subset_dir = explicit_subset_dir

    if "init" in steps:
        (workspace / "training_data").mkdir(parents=True, exist_ok=True)
        out_root.mkdir(parents=True, exist_ok=True)
        (run_root).mkdir(parents=True, exist_ok=True)
        (source_seed_dir).mkdir(parents=True, exist_ok=True)
        (workspace / "bitext").mkdir(parents=True, exist_ok=True)

    if "pairs" in steps:
        pair_summary_out = args.pairs_summary_out.strip()
        if not pair_summary_out:
            pair_summary_out = str(pairs_path.with_suffix(".summary.json"))
        pair_args = _build_pair_args(
            src_langs=source_langs,
            tgt_langs=target_langs,
            seed_dir=source_seed_dir,
            allow_same_lang=bool(args.allow_same_lang_pairs),
        )
        if not pair_args:
            raise SystemExit("No source-target pair files could be assembled.")
        pair_cfg_hash = _config_hash(
            {
                "source_langs": source_langs,
                "target_langs": target_langs,
                "allow_same_lang_pairs": bool(args.allow_same_lang_pairs),
                "pairs_min_chars": int(args.pairs_min_chars),
                "pairs_per_pair": int(args.pairs_per_pair),
                "pairs_neg_strategy": str(args.pairs_neg_strategy),
                "pairs_hard_neg_pool": int(args.pairs_hard_neg_pool),
                "pairs_seed": int(args.pairs_seed),
                "pairs_max_rows_per_input": int(args.pairs_max_rows_per_input),
                "pairs_allow_line_mismatch": bool(args.pairs_allow_line_mismatch),
                "seed_dir": str(source_seed_dir),
            }
        )
        pair_done = state_dir / "pairs.done.json"
        pair_cmd = [
            py,
            str(MAKE_PAIRS_SCRIPT),
            *pair_args,
            "--source-langs", ",".join(source_langs),
            "--target-langs", ",".join(target_langs),
            "--min-chars", str(int(args.pairs_min_chars)),
            "--pairs-per-pair", str(int(args.pairs_per_pair)),
            "--neg-strategy", str(args.pairs_neg_strategy),
            "--hard-neg-pool", str(int(args.pairs_hard_neg_pool)),
            "--seed", str(int(args.pairs_seed)),
            "--max-rows-per-input", str(int(args.pairs_max_rows_per_input)),
            "--out", str(pairs_path),
            "--summary-out", str(pair_summary_out),
        ]
        if bool(args.pairs_allow_line_mismatch):
            pair_cmd.append("--allow-mismatched-pair-lines")
        pair_outputs = [pairs_path, Path(pair_summary_out)]
        if args.resume and _done_manifest_matches(pair_done, config_hash=pair_cfg_hash, outputs=pair_outputs):
            print(f"[pairs] skip: done manifest verified at {pair_done}")
        else:
            _run(pair_cmd, dry_run=bool(args.dry_run))
            if not args.dry_run:
                _write_done_manifest(pair_done, step="pairs", config_hash=pair_cfg_hash, outputs=pair_outputs)

    if "split" in steps:
        split_cfg_hash = _config_hash(
            {
                "eval_fraction": float(args.split_eval_fraction),
                "eval_max_rows": int(args.split_eval_max_rows),
                "min_eval_per_pair": int(args.split_min_eval_per_pair),
                "pairs_path": str(pairs_path),
            }
        )
        split_done = state_dir / "split.done.json"
        split_cmd = [
            py,
            str(SPLIT_PAIRS_SCRIPT),
            "--pairs", str(pairs_path),
            "--train-out", str(split_train_path),
            "--eval-out", str(split_eval_path),
            "--eval-fraction", str(float(args.split_eval_fraction)),
            "--eval-max-rows", str(int(args.split_eval_max_rows)),
            "--min-eval-per-pair", str(int(args.split_min_eval_per_pair)),
        ]
        split_outputs = [split_train_path, split_eval_path]
        if args.resume and _done_manifest_matches(split_done, config_hash=split_cfg_hash, outputs=split_outputs):
            print(f"[split] skip: done manifest verified at {split_done}")
        else:
            _run(split_cmd, dry_run=bool(args.dry_run))
            if not args.dry_run:
                _write_done_manifest(split_done, step="split", config_hash=split_cfg_hash, outputs=split_outputs)

    if "subset" in steps:
        if not VOCAB_SUBSET_SCRIPT.exists():
            raise SystemExit(f"Missing vocab subset tool: {VOCAB_SUBSET_SCRIPT}")
        if not SUBSET_TEXT_BUILDER.exists():
            raise SystemExit(f"Missing subset text builder: {SUBSET_TEXT_BUILDER}")

        pair_paths: list[Path] = []
        if split_train_path.exists():
            pair_paths.append(split_train_path)
        if split_eval_path.exists():
            pair_paths.append(split_eval_path)
        if not pair_paths and pairs_path.exists():
            pair_paths.append(pairs_path)

        text_inputs: list[Path] = []
        for p in extra_subset_texts:
            text_inputs.append(p)

        # Ensure seed/parallel text coverage as a fallback/augmentation.
        for lang in sorted(set(source_langs + target_langs)):
            mono = source_seed_dir / f"{lang}.txt"
            if mono.exists():
                text_inputs.append(mono)
            for src in source_langs:
                for tgt in target_langs:
                    if src == tgt and not args.allow_same_lang_pairs:
                        continue
                    pair_file = source_seed_dir / f"{src}_to_{tgt}.txt"
                    if pair_file.exists():
                        text_inputs.append(pair_file)

        deduped_text_inputs: list[str] = []
        seen_text_inputs: set[str] = set()
        for p in text_inputs:
            p_s = str(p)
            if p_s not in seen_text_inputs:
                seen_text_inputs.add(p_s)
                deduped_text_inputs.append(p_s)

        if not deduped_text_inputs and not pair_paths:
            raise SystemExit(
                "[subset] no usable text inputs found. Ensure --subset-text points to files "
                "or run pairs/split with source/target seed files present."
            )

        subset_dir = effective_subset_dir or subset_dir_fallback
        subset_dir.mkdir(parents=True, exist_ok=True)
        subset_text_builder_cmd = [
            py,
            str(SUBSET_TEXT_BUILDER),
            "--out", str(subset_text_path),
            "--source-langs", ",".join(source_langs),
            "--target-langs", ",".join(target_langs),
            "--min-text-chars", str(int(args.subset_min_text_chars)),
        ]
        for path in pair_paths:
            subset_text_builder_cmd.extend(["--pair-jsonl", str(path)])
        for path in deduped_text_inputs:
            subset_text_builder_cmd.extend(["--text", path])
        _run(subset_text_builder_cmd, dry_run=bool(args.dry_run))

        subset_cmd = [
            py,
            str(VOCAB_SUBSET_SCRIPT),
            "--model", str(subset_model),
            "--out", str(subset_dir),
            "--text", str(subset_text_path),
            "--top-k", str(int(args.subset_top_k)),
            "--min-count", str(int(args.subset_min_count)),
            "--dtype", str(args.subset_dtype),
        ]
        if bool(args.subset_fill_to_top_k):
            subset_cmd.extend(["--fill-to-top-k", "--fill-strategy", str(args.subset_fill_strategy)])
        if bool(args.subset_allow_download):
            subset_cmd.append("--allow-download")
        if args.subset_max_lines is not None and int(args.subset_max_lines) > 0:
            subset_cmd.extend(["--max-lines", str(int(args.subset_max_lines))])
        if args.subset_write_checkpoint:
            subset_cmd.append("--write-checkpoint")
        if args.subset_also_prune_output:
            subset_cmd.append("--also-prune-output")
        if bool(args.subset_for_causal_lm):
            subset_cmd.append("--for-causal-lm")

        if args.resume and (subset_dir / "id_remap.json").exists():
            print(f"[subset] skip: existing subset dir {subset_dir}")
        else:
            _run(subset_cmd, dry_run=bool(args.dry_run))

        effective_subset_dir = subset_dir

    if "train" in steps:
        student_model_ref = str(args.student_model)
        if effective_subset_dir is not None and _has_subset_model_artifacts(effective_subset_dir):
            print(f"[train] using pruned subset model from {effective_subset_dir}")
            student_model_ref = str(effective_subset_dir)

        train_cmd = [
            py,
            str(TRAINER_SCRIPT),
            "--pairs", str(split_train_path),
            "--teacher-model", str(args.teacher_model),
            "--student-model", student_model_ref,
            "--source-langs", ",".join(source_langs),
            "--target-langs", ",".join(target_langs),
            "--out-root", str(out_root),
            "--run-name", str(args.run_name),
            "--schedule", str(args.schedule),
            "--total-steps", str(int(args.total_steps)),
            "--sft-steps", str(int(args.sft_steps)),
            "--batch-size", str(int(args.batch_size)),
            "--lr", str(float(args.lr)),
            "--log-every", str(int(args.log_every)),
            "--save-every", str(int(args.save_every)),
            "--select-best-checkpoint" if bool(args.select_best_checkpoint) else "--no-select-best-checkpoint",
            "--lambda-kd", str(float(args.lambda_kd)),
            "--mu-triplet", str(float(args.mu_triplet)),
            "--margin", str(float(args.margin)),
            "--kd-temperature", str(float(args.kd_temperature)),
            "--weight-decay", str(float(args.weight_decay)),
            "--grad-clip", str(float(args.grad_clip)),
            "--accum-steps", str(int(args.accum_steps)),
            "--max-prompt-length", str(int(args.max_prompt_length)),
            "--max-seq-length", str(int(args.max_seq_length)),
            "--predict-samples", str(int(args.predict_samples)),
            "--max-new-tokens", str(int(args.max_new_tokens)),
            "--summary-out", str(run_root / (args.summary_out or "train_summary.json")),
            "--dtype", str(args.dtype),
            "--device", str(args.device),
            "--teacher-device", str(args.teacher_device),
            "--seed", str(int(args.seed)),
            "--lora-rank", str(int(args.lora_rank)),
            "--lora-alpha", str(int(args.lora_alpha)),
            "--lora-dropout", str(float(args.lora_dropout)),
            "--lora-modules", str(args.lora_modules),
        ]

        if args.enable_lora:
            train_cmd.append("--enable-lora")
        if args.skip_kd_when_device_mismatch:
            train_cmd.append("--skip-kd-when-device-mismatch")
        if effective_subset_dir is not None:
            train_cmd.extend(["--vocab-subset-dir", str(effective_subset_dir)])
            tokenizer_model = str(args.tokenizer_model).strip() or str(subset_model)
            if tokenizer_model:
                train_cmd.extend(["--tokenizer-model", tokenizer_model])
        if args.resume:
            train_cmd.append("--resume")
            if args.resume_from.strip():
                train_cmd.extend(["--resume-from", str(_resolve_path(PROJECT_ROOT, args.resume_from))])
        if args.allow_download:
            train_cmd.append("--allow-download")

        _run(train_cmd, dry_run=bool(args.dry_run))

    if "eval" in steps:
        eval_model = str(args.eval_model).strip()
        if eval_model == "final":
            eval_model = str(run_root / "final")
        if not eval_model:
            eval_model = str(run_root / "final")
        eval_out_dir = _resolve_path(run_root, args.eval_out_dir)
        eval_teacher_model = str(args.eval_teacher_model).strip() or str(args.teacher_model)
        eval_cmd = [
            py,
            str(EVAL_SCRIPT),
            "--pairs", str(split_eval_path),
            "--model", eval_model,
            "--teacher-model", eval_teacher_model,
            "--source-langs", ",".join(source_langs),
            "--target-langs", ",".join(target_langs),
            "--out-dir", str(eval_out_dir),
            "--student-summary", str(eval_out_dir / args.eval_student_summary),
            "--teacher-summary", str(eval_out_dir / args.eval_teacher_summary),
            "--compare-summary", str(eval_out_dir / args.eval_compare_summary),
            "--student-predictions", str(eval_out_dir / args.eval_student_predictions),
            "--teacher-predictions", str(eval_out_dir / args.eval_teacher_predictions),
            "--max-prompt-length", str(int(args.eval_max_prompt_length)),
            "--max-new-tokens", str(int(args.eval_max_new_tokens)),
            "--batch-size", str(int(args.eval_batch_size)),
            "--eval-samples", str(int(args.eval_samples)),
            "--device", str(args.device),
            "--dtype", str(args.dtype),
            "--seed", str(int(args.eval_seed)),
            "--temperature", str(float(args.eval_temperature)),
            "--top-p", str(float(args.eval_top_p)),
            "--top-k", str(int(args.eval_top_k)),
        ]
        if args.eval_do_sample:
            eval_cmd.append("--do-sample")
        if args.eval_bleu:
            eval_cmd.append("--eval-bleu")
        if args.eval_chrf:
            eval_cmd.append("--eval-chrf")
        if args.eval_comet:
            eval_cmd.extend(["--eval-comet", "--comet-model", str(args.eval_comet_model), "--comet-batch-size", str(int(args.eval_comet_batch_size))])
        if effective_subset_dir is not None:
            eval_cmd.extend(["--vocab-subset-dir", str(effective_subset_dir)])
            tokenizer_model = str(args.tokenizer_model).strip() or str(subset_model)
            if tokenizer_model:
                eval_cmd.extend(["--tokenizer-model", tokenizer_model])
        if args.allow_download:
            eval_cmd.append("--allow-download")

        _run(eval_cmd, dry_run=bool(args.dry_run))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
