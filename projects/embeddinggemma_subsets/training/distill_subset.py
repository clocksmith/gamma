#!/usr/bin/env python3
"""
Distill + contrastive finetune a subset embedding model against a base teacher.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def _mean_pool(last_hidden, attention_mask):
    mask = attention_mask.unsqueeze(-1).to(dtype=last_hidden.dtype)
    summed = (last_hidden * mask).sum(dim=1)
    denom = mask.sum(dim=1).clamp_min(1.0)
    return summed / denom


def _encode_teacher(model, tok, texts: list[str], *, device: str, max_length: int) -> torch.Tensor:
    enc = tok(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
        add_special_tokens=True,
    )
    ids = enc["input_ids"].to(device)
    am = enc.get("attention_mask", torch.ones_like(ids)).to(device)
    with torch.no_grad():
        out = model(input_ids=ids, attention_mask=am, return_dict=True)
    pooled = getattr(out, "pooler_output", None)
    if pooled is None:
        pooled = _mean_pool(out.last_hidden_state, am)
    return F.normalize(pooled.float(), p=2, dim=-1)


def _remap_input_ids(input_ids: torch.Tensor, remap: dict[str, int], unk_old: int) -> torch.Tensor:
    unk_new = remap.get(str(int(unk_old)))
    if unk_new is None:
        raise RuntimeError("Remap missing unk mapping.")
    ids = input_ids.cpu().tolist()
    for i in range(len(ids)):
        row = ids[i]
        for j in range(len(row)):
            row[j] = int(remap.get(str(int(row[j])), int(unk_new)))
    return torch.tensor(ids, dtype=torch.long)


def _encode_student(model, tok, remap: dict[str, int], texts: list[str], *, device: str, max_length: int) -> torch.Tensor:
    enc = tok(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
        add_special_tokens=True,
    )
    ids_old = enc["input_ids"]
    am = enc.get("attention_mask", torch.ones_like(ids_old))
    ids_new = _remap_input_ids(ids_old, remap, int(tok.unk_token_id)).to(device)
    am = am.to(device)
    out = model(input_ids=ids_new, attention_mask=am, return_dict=True)
    pooled = getattr(out, "pooler_output", None)
    if pooled is None:
        pooled = _mean_pool(out.last_hidden_state, am)
    return F.normalize(pooled.float(), p=2, dim=-1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--teacher-model", required=True)
    ap.add_argument("--student-subset-dir", required=True)
    ap.add_argument("--pairs", required=True, help="JSONL from make_distill_pairs.py")
    ap.add_argument("--langs", default=None, help="Optional comma-separated language filter for pairs.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--max-length", type=int, default=128)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--temperature", type=float, default=0.05)
    ap.add_argument("--alpha-contrastive", type=float, default=1.0)
    ap.add_argument("--beta-distill", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))

    teacher = AutoModel.from_pretrained(str(args.teacher_model), local_files_only=True, low_cpu_mem_usage=True).to(args.device)
    teacher.eval()
    tok = AutoTokenizer.from_pretrained(str(args.teacher_model), local_files_only=True, use_fast=True)

    student_dir = Path(args.student_subset_dir)
    student = AutoModel.from_pretrained(str(student_dir), local_files_only=True, low_cpu_mem_usage=True).to(args.device)
    student.train()
    remap = _load_json(student_dir / "id_remap.json").get("old_to_new", {})
    if not isinstance(remap, dict) or not remap:
        raise RuntimeError("Invalid id_remap.json in student subset dir")

    rows = _load_jsonl(Path(args.pairs))
    if args.langs:
        want = {x.strip() for x in str(args.langs).split(",") if x.strip()}
        rows = [r for r in rows if str(r.get("lang", "")).strip() in want]
    if not rows:
        raise RuntimeError("No distillation pairs loaded.")
    rnd = random.Random(int(args.seed))
    rnd.shuffle(rows)

    optim = torch.optim.AdamW(student.parameters(), lr=float(args.lr), weight_decay=float(args.weight_decay))
    bsz = max(1, int(args.batch_size))
    total_steps = max(1, int(args.steps))
    losses: list[float] = []
    loss_con_list: list[float] = []
    loss_dis_list: list[float] = []

    for step in range(total_steps):
        batch = [rows[(step * bsz + i) % len(rows)] for i in range(bsz)]
        q = [x["query"] for x in batch]
        p = [x["pos"] for x in batch]
        # hard negatives are in batch via cross-example mismatch; explicit neg kept for future extensions.

        with torch.no_grad():
            tq = _encode_teacher(teacher, tok, q, device=args.device, max_length=int(args.max_length))
            tp = _encode_teacher(teacher, tok, p, device=args.device, max_length=int(args.max_length))

        sq = _encode_student(student, tok, remap, q, device=args.device, max_length=int(args.max_length))
        sp = _encode_student(student, tok, remap, p, device=args.device, max_length=int(args.max_length))

        # Distill to teacher geometry.
        loss_distill = F.mse_loss(sq, tq) + F.mse_loss(sp, tp)

        # Contrastive objective with in-batch negatives.
        logits = (sq @ sp.T) / float(args.temperature)
        target = torch.arange(logits.size(0), device=logits.device)
        loss_ctr = 0.5 * (F.cross_entropy(logits, target) + F.cross_entropy(logits.T, target))

        loss = float(args.alpha_contrastive) * loss_ctr + float(args.beta_distill) * loss_distill

        optim.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(student.parameters(), 1.0)
        optim.step()

        losses.append(float(loss.item()))
        loss_con_list.append(float(loss_ctr.item()))
        loss_dis_list.append(float(loss_distill.item()))
        if (step + 1) % 10 == 0 or step == 0:
            print(
                f"step={step+1}/{total_steps} "
                f"loss={losses[-1]:.4f} "
                f"contrastive={loss_con_list[-1]:.4f} "
                f"distill={loss_dis_list[-1]:.4f}"
            )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    student.save_pretrained(str(out), safe_serialization=True)
    tok.save_pretrained(str(out))
    # copy remap for runtime compatibility
    (out / "id_remap.json").write_text((student_dir / "id_remap.json").read_text(encoding="utf-8"), encoding="utf-8")
    summary = {
        "teacher_model": str(args.teacher_model),
        "student_input_dir": str(student_dir),
        "steps": int(total_steps),
        "batch_size": int(bsz),
        "max_length": int(args.max_length),
        "lr": float(args.lr),
        "temperature": float(args.temperature),
        "alpha_contrastive": float(args.alpha_contrastive),
        "beta_distill": float(args.beta_distill),
        "pairs": str(args.pairs),
        "pairs_count": len(rows),
        "loss_mean_last_20": float(sum(losses[-20:]) / max(1, len(losses[-20:]))),
        "contrastive_mean_last_20": float(sum(loss_con_list[-20:]) / max(1, len(loss_con_list[-20:]))),
        "distill_mean_last_20": float(sum(loss_dis_list[-20:]) / max(1, len(loss_dis_list[-20:]))),
    }
    (out / "train_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote distilled student -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
