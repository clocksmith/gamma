#!/usr/bin/env python3
"""
Run distillation training for multiple language subset students.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_K_MAP = {
    "en": 50000,
    "es": 50000,
    "ar": 50000,
    "fr": 50000,
    "pt": 50000,
    "zh": 80000,
    "ja": 80000,
    "hi": 80000,
}


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--teacher-model", required=True)
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--langs", default="en,es,zh,ja,ar,fr,pt,hi")
    ap.add_argument("--subset-root", default="gamma/projects/distillation/embedding/output")
    ap.add_argument("--subset-pattern", default="google__embeddinggemma-300m-{lang}-vocab{k}")
    ap.add_argument("--out-root", default="gamma/projects/distillation/embedding/models/distilled")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--max-length", type=int, default=128)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--temperature", type=float, default=0.05)
    ap.add_argument("--alpha-contrastive", type=float, default=1.0)
    ap.add_argument("--beta-distill", type=float, default=1.0)
    ap.add_argument("--alpha-triplet", type=float, default=0.25)
    ap.add_argument("--triplet-margin", type=float, default=0.05)
    ap.add_argument("--alpha-sim-distill", type=float, default=0.25)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true", help="Skip language if output dir already has train_summary.json")
    args = ap.parse_args()

    langs = [x.strip() for x in str(args.langs).split(",") if x.strip()]
    subset_root = Path(args.subset_root)
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    distill_script = Path("gamma/projects/distillation/embedding/training/distill_subset.py")
    if not distill_script.exists():
        raise SystemExit(f"Missing script: {distill_script}")

    for lang in langs:
        k = int(DEFAULT_K_MAP.get(lang, 50000))
        student_dir = subset_root / str(args.subset_pattern).format(lang=lang, k=k)
        if not student_dir.exists():
            print(f"skip {lang}: missing student subset dir {student_dir}")
            continue
        out_dir = out_root / f"{student_dir.name}-distilled"
        if bool(args.resume) and (out_dir / "train_summary.json").exists():
            print(f"skip {lang}: resume enabled and output already exists: {out_dir}")
            continue
        cmd = [
            sys.executable,
            str(distill_script),
            "--teacher-model",
            str(args.teacher_model),
            "--student-subset-dir",
            str(student_dir),
            "--pairs",
            str(args.pairs),
            "--langs",
            lang,
            "--out",
            str(out_dir),
            "--device",
            str(args.device),
            "--max-length",
            str(int(args.max_length)),
            "--batch-size",
            str(int(args.batch_size)),
            "--steps",
            str(int(args.steps)),
            "--lr",
            str(float(args.lr)),
            "--weight-decay",
            str(float(args.weight_decay)),
            "--temperature",
            str(float(args.temperature)),
            "--alpha-contrastive",
            str(float(args.alpha_contrastive)),
            "--beta-distill",
            str(float(args.beta_distill)),
            "--alpha-triplet",
            str(float(args.alpha_triplet)),
            "--triplet-margin",
            str(float(args.triplet_margin)),
            "--alpha-sim-distill",
            str(float(args.alpha_sim_distill)),
            "--seed",
            str(int(args.seed)),
        ]
        _run(cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
