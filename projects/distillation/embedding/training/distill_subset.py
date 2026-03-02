#!/usr/bin/env python3
"""
Distill + contrastive finetune a subset embedding model against a base teacher.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import time
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


def _safe_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x)


def _validate_model_ref(model_ref: str, *, arg_name: str) -> None:
    s = str(model_ref).strip()
    if not s:
        raise RuntimeError(
            f"{arg_name} is empty. If this came from $BASE_MODEL, export it first or pass an explicit path."
        )
    p = Path(s)
    if p.exists() and p.is_dir() and not (p / "config.json").exists():
        raise RuntimeError(
            f"{arg_name} points to a directory without config.json: {p}. "
            "Use a HF model id or a local snapshot directory."
        )


_TOKENIZER_ARTIFACT_FILES = (
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "tokenizer.model",
    "sentencepiece.bpe.model",
    "spiece.model",
    "vocab.json",
    "merges.txt",
    "added_tokens.json",
)


def _remove_tokenizer_artifacts(out_dir: Path) -> list[str]:
    removed: list[str] = []
    for name in _TOKENIZER_ARTIFACT_FILES:
        p = out_dir / name
        if p.exists() and p.is_file():
            p.unlink()
            removed.append(name)
    return removed


def _write_runtime_note(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "This distilled checkpoint uses a pruned vocabulary.",
                "",
                "Important:",
                "- Do NOT feed tokenizer ids directly unless they are remapped.",
                "- Use the base tokenizer from the teacher/base model.",
                "- Remap base-tokenizer ids with id_remap.json (old_to_new).",
                "- Map missing ids to the remapped unk id.",
                "",
                "This avoids index errors and keeps runtime behavior aligned with training/eval.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _is_valid_checkpoint_dir(path: Path) -> bool:
    ckpt = Path(path)
    if not ckpt.is_dir():
        return False
    if not re.fullmatch(r"checkpoint-(\d+)", ckpt.name):
        return False
    if not (ckpt / "training_state.pt").exists():
        return False
    if not (ckpt / "config.json").exists():
        return False
    has_model = (ckpt / "model.safetensors").is_file() or (ckpt / "pytorch_model.bin").is_file()
    if not has_model and not any(ckpt.glob("*.safetensors")) and not any(ckpt.glob("*.bin")):
        return False
    return True


def _checkpoint_step(path: Path) -> int:
    m = re.fullmatch(r"checkpoint-(\d+)", Path(path).name)
    if not m:
        return 0
    try:
        return int(m.group(1))
    except Exception:
        return 0


def _latest_checkpoint(path: Path) -> Path | None:
    p = Path(path)
    if p.is_dir() and _is_valid_checkpoint_dir(p):
        return p
    root = p / "checkpoints" if p.is_dir() else p
    if not root.exists() or not root.is_dir():
        return None
    cands = sorted((x for x in root.glob("checkpoint-*") if _is_valid_checkpoint_dir(x)), key=_checkpoint_step)
    return cands[-1] if cands else None


def _load_checkpoint_state(path: Path) -> dict[str, Any]:
    state_path = Path(path) / "training_state.pt"
    if not state_path.exists():
        return {}
    try:
        state = torch.load(state_path, map_location="cpu")
    except Exception:
        return {}
    return state if isinstance(state, dict) else {}


def _save_checkpoint(
    *,
    student,
    optimizer: torch.optim.Optimizer,
    checkpoint_root: Path,
    step: int,
    loss_last: float | None,
    loss_mean20: float | None,
) -> Path:
    ckpt = checkpoint_root / f"checkpoint-{int(step):06d}"
    ckpt.mkdir(parents=True, exist_ok=True)
    student.save_pretrained(str(ckpt), safe_serialization=True)
    state: dict[str, Any] = {
        "step": int(step),
        "saved_at": float(time.time()),
        "optimizer_state_dict": optimizer.state_dict(),
        "random_state": random.getstate(),
        "torch_rng_state": torch.get_rng_state(),
    }
    if torch.cuda.is_available():
        try:
            state["torch_cuda_rng_state"] = torch.cuda.get_rng_state_all()
        except Exception:
            pass
    if loss_last is not None:
        state["loss_last"] = float(loss_last)
    if loss_mean20 is not None:
        state["loss_mean20"] = float(loss_mean20)
    torch.save(state, ckpt / "training_state.pt")
    return ckpt


def _select_best_checkpoint(checkpoint_root: Path) -> Path | None:
    if not checkpoint_root.exists():
        return None
    cands = sorted((x for x in checkpoint_root.glob("checkpoint-*") if _is_valid_checkpoint_dir(x)), key=_checkpoint_step)
    if not cands:
        return None
    best = None
    best_loss = math.inf
    for ckpt in cands:
        state = _load_checkpoint_state(ckpt)
        raw = state.get("loss_mean20", state.get("loss_last"))
        if isinstance(raw, torch.Tensor):
            if raw.numel() == 1:
                raw = float(raw.item())
            else:
                raw = None
        if isinstance(raw, (int, float)) and math.isfinite(float(raw)):
            val = float(raw)
            if val < best_loss:
                best_loss = val
                best = ckpt
    if best is not None:
        return best
    return cands[-1]


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
    ap.add_argument("--alpha-triplet", type=float, default=0.25)
    ap.add_argument("--triplet-margin", type=float, default=0.05)
    ap.add_argument("--alpha-sim-distill", type=float, default=0.25)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--save-every", type=int, default=100, help="Checkpoint interval in optimization steps.")
    ap.add_argument("--resume", action="store_true", help="Resume from the latest checkpoint under --out or --resume-from.")
    ap.add_argument("--resume-from", default="", help="Optional resume source (checkpoint dir or run dir).")
    ap.add_argument("--select-best-checkpoint", action="store_true", help="Export best loss checkpoint as final output.")
    ap.add_argument("--no-select-best-checkpoint", dest="select_best_checkpoint", action="store_false")
    ap.set_defaults(select_best_checkpoint=True)
    ap.add_argument(
        "--export-teacher-tokenizer",
        action="store_true",
        help=(
            "Also export the full teacher tokenizer into --out. "
            "Off by default because the distilled checkpoint expects id_remap.json at runtime."
        ),
    )
    args = ap.parse_args()

    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    run_start = time.perf_counter()

    if str(args.device).startswith("cuda"):
        cuda_ok = torch.cuda.is_available()
        if cuda_ok:
            dev_idx = torch.cuda.current_device()
            dev_name = torch.cuda.get_device_name(dev_idx)
            print(f"[distill_subset] device={args.device} cuda_available=true gpu={dev_name} (index={dev_idx})")
        else:
            print(f"[distill_subset] device={args.device} cuda_available=false")
    else:
        print(f"[distill_subset] device={args.device}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    checkpoint_root = out / "checkpoints"
    checkpoint_root.mkdir(parents=True, exist_ok=True)

    resume_checkpoint: Path | None = None
    resume_state: dict[str, Any] = {}
    start_step = 0
    if bool(args.resume):
        resume_source = Path(args.resume_from).expanduser() if str(args.resume_from).strip() else out
        resume_checkpoint = _latest_checkpoint(resume_source)
        if resume_checkpoint is not None:
            resume_state = _load_checkpoint_state(resume_checkpoint)
            raw_step = resume_state.get("step", _checkpoint_step(resume_checkpoint))
            if isinstance(raw_step, torch.Tensor):
                if raw_step.numel() == 1:
                    start_step = int(raw_step.item())
            elif isinstance(raw_step, (int, float)):
                start_step = int(raw_step)
            print(f"[distill_subset] resume checkpoint={resume_checkpoint} step={start_step}")
        else:
            print(f"[distill_subset] resume requested but no valid checkpoint found at {resume_source}; starting fresh")

    _validate_model_ref(str(args.teacher_model), arg_name="--teacher-model")
    teacher = AutoModel.from_pretrained(str(args.teacher_model), local_files_only=True, low_cpu_mem_usage=True).to(args.device)
    teacher.eval()
    tok = AutoTokenizer.from_pretrained(str(args.teacher_model), local_files_only=True, use_fast=True)

    student_dir = Path(args.student_subset_dir)
    student_source = resume_checkpoint if resume_checkpoint is not None else student_dir
    student = AutoModel.from_pretrained(str(student_source), local_files_only=True, low_cpu_mem_usage=True).to(args.device)
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
    print(f"[distill_subset] loaded_pairs={len(rows)} langs_filter={args.langs if args.langs else 'ALL'}")
    rnd = random.Random(int(args.seed))
    rnd.shuffle(rows)

    optim = torch.optim.AdamW(student.parameters(), lr=float(args.lr), weight_decay=float(args.weight_decay))
    if resume_state:
        optim_state = resume_state.get("optimizer_state_dict")
        if isinstance(optim_state, dict):
            try:
                optim.load_state_dict(optim_state)
            except Exception:
                print("[distill_subset] warning: failed to restore optimizer state; continuing with fresh optimizer")
        random_state = resume_state.get("random_state")
        if random_state is not None:
            try:
                random.setstate(random_state)
            except Exception:
                pass
        torch_rng_state = resume_state.get("torch_rng_state")
        if isinstance(torch_rng_state, torch.Tensor):
            try:
                torch.set_rng_state(torch_rng_state)
            except Exception:
                pass
        torch_cuda_rng_state = resume_state.get("torch_cuda_rng_state")
        if isinstance(torch_cuda_rng_state, list):
            try:
                if torch.cuda.is_available():
                    torch.cuda.set_rng_state_all(torch_cuda_rng_state)
            except Exception:
                pass

    bsz = max(1, int(args.batch_size))
    total_steps = max(1, int(args.steps))
    save_every = max(1, int(args.save_every))
    losses: list[float] = []
    loss_con_list: list[float] = []
    loss_dis_list: list[float] = []
    loss_triplet_list: list[float] = []
    loss_simdist_list: list[float] = []
    step_start = time.perf_counter()

    for step in range(max(0, int(start_step)), total_steps):
        batch = [rows[(step * bsz + i) % len(rows)] for i in range(bsz)]
        q = [_safe_text(x.get("query", "")) for x in batch]
        p = [_safe_text(x.get("pos", "")) for x in batch]
        n = [_safe_text(x.get("neg", "")) for x in batch]
        use_explicit_neg = any(t.strip() for t in n)

        with torch.no_grad():
            tq = _encode_teacher(teacher, tok, q, device=args.device, max_length=int(args.max_length))
            tp = _encode_teacher(teacher, tok, p, device=args.device, max_length=int(args.max_length))
            tn = _encode_teacher(teacher, tok, n, device=args.device, max_length=int(args.max_length)) if use_explicit_neg else None

        sq = _encode_student(student, tok, remap, q, device=args.device, max_length=int(args.max_length))
        sp = _encode_student(student, tok, remap, p, device=args.device, max_length=int(args.max_length))
        sn = _encode_student(student, tok, remap, n, device=args.device, max_length=int(args.max_length)) if use_explicit_neg else None

        # Distill to teacher geometry.
        loss_distill = F.mse_loss(sq, tq) + F.mse_loss(sp, tp)
        if use_explicit_neg and tn is not None and sn is not None:
            loss_distill = loss_distill + F.mse_loss(sn, tn)

        # Contrastive objective with in-batch negatives.
        logits = (sq @ sp.T) / float(args.temperature)
        target = torch.arange(logits.size(0), device=logits.device)
        loss_ctr = 0.5 * (F.cross_entropy(logits, target) + F.cross_entropy(logits.T, target))

        # Explicit triplet with the per-row negative from pairs.
        if use_explicit_neg and sn is not None:
            sim_qp = (sq * sp).sum(dim=-1)
            sim_qn = (sq * sn).sum(dim=-1)
            loss_triplet = F.relu(float(args.triplet_margin) + sim_qn - sim_qp).mean()
        else:
            loss_triplet = torch.zeros((), device=sq.device)

        # Distill similarity structure (teacher/student alignment on positive and negative similarities).
        if use_explicit_neg and tn is not None and sn is not None:
            t_qp = (tq * tp).sum(dim=-1)
            t_qn = (tq * tn).sum(dim=-1)
            s_qp = (sq * sp).sum(dim=-1)
            s_qn = (sq * sn).sum(dim=-1)
            loss_simdist = F.mse_loss(s_qp, t_qp) + F.mse_loss(s_qn, t_qn)
        else:
            loss_simdist = torch.zeros((), device=sq.device)

        loss = (
            float(args.alpha_contrastive) * loss_ctr
            + float(args.beta_distill) * loss_distill
            + float(args.alpha_triplet) * loss_triplet
            + float(args.alpha_sim_distill) * loss_simdist
        )

        optim.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(student.parameters(), 1.0)
        optim.step()

        losses.append(float(loss.item()))
        loss_con_list.append(float(loss_ctr.item()))
        loss_dis_list.append(float(loss_distill.item()))
        loss_triplet_list.append(float(loss_triplet.item()))
        loss_simdist_list.append(float(loss_simdist.item()))
        if (step + 1) % 10 == 0 or step == 0:
            now = time.perf_counter()
            elapsed = now - step_start
            steps_done = step + 1
            sps = steps_done / elapsed if elapsed > 0 else 0.0
            print(
                f"step={step+1}/{total_steps} "
                f"loss={losses[-1]:.4f} "
                f"contrastive={loss_con_list[-1]:.4f} "
                f"distill={loss_dis_list[-1]:.4f} "
                f"triplet={loss_triplet_list[-1]:.4f} "
                f"simdist={loss_simdist_list[-1]:.4f} "
                f"elapsed={elapsed:.1f}s "
                f"steps_per_s={sps:.2f}"
            )

        checkpoint_step = step + 1
        if (checkpoint_step % save_every == 0) or (checkpoint_step >= total_steps):
            _save_checkpoint(
                student=student,
                optimizer=optim,
                checkpoint_root=checkpoint_root,
                step=checkpoint_step,
                loss_last=losses[-1] if losses else None,
                loss_mean20=(sum(losses[-20:]) / max(1, len(losses[-20:]))) if losses else None,
            )

    selected_checkpoint = None
    if bool(args.select_best_checkpoint):
        selected = _select_best_checkpoint(checkpoint_root)
        if selected is not None:
            selected_checkpoint = selected
    else:
        selected_checkpoint = _latest_checkpoint(checkpoint_root)

    if selected_checkpoint is not None:
        final_model = AutoModel.from_pretrained(str(selected_checkpoint), local_files_only=True, low_cpu_mem_usage=True)
        final_model.save_pretrained(str(out), safe_serialization=True)
    else:
        student.save_pretrained(str(out), safe_serialization=True)

    removed_tokenizer_files = _remove_tokenizer_artifacts(out)
    if bool(args.export_teacher_tokenizer):
        tok.save_pretrained(str(out))
    # copy remap for runtime compatibility
    (out / "id_remap.json").write_text((student_dir / "id_remap.json").read_text(encoding="utf-8"), encoding="utf-8")
    _write_runtime_note(out / "README_REMAP.txt")
    loss_mean_last_20 = float(sum(losses[-20:]) / max(1, len(losses[-20:]))) if losses else 0.0
    contrastive_mean_last_20 = float(sum(loss_con_list[-20:]) / max(1, len(loss_con_list[-20:]))) if loss_con_list else 0.0
    distill_mean_last_20 = float(sum(loss_dis_list[-20:]) / max(1, len(loss_dis_list[-20:]))) if loss_dis_list else 0.0
    triplet_mean_last_20 = float(sum(loss_triplet_list[-20:]) / max(1, len(loss_triplet_list[-20:]))) if loss_triplet_list else 0.0
    simdist_mean_last_20 = float(sum(loss_simdist_list[-20:]) / max(1, len(loss_simdist_list[-20:]))) if loss_simdist_list else 0.0
    summary = {
        "teacher_model": str(args.teacher_model),
        "student_input_dir": str(student_dir),
        "student_loaded_from": str(student_source),
        "steps": int(total_steps),
        "start_step": int(start_step),
        "batch_size": int(bsz),
        "max_length": int(args.max_length),
        "lr": float(args.lr),
        "save_every": int(save_every),
        "temperature": float(args.temperature),
        "alpha_contrastive": float(args.alpha_contrastive),
        "beta_distill": float(args.beta_distill),
        "alpha_triplet": float(args.alpha_triplet),
        "triplet_margin": float(args.triplet_margin),
        "alpha_sim_distill": float(args.alpha_sim_distill),
        "pairs": str(args.pairs),
        "pairs_count": len(rows),
        "device": str(args.device),
        "resumed": bool(args.resume) and resume_checkpoint is not None,
        "resume_checkpoint": str(resume_checkpoint) if resume_checkpoint is not None else "",
        "select_best_checkpoint": bool(args.select_best_checkpoint),
        "selected_checkpoint": str(selected_checkpoint) if selected_checkpoint is not None else "",
        "duration_s": float(time.perf_counter() - run_start),
        "loss_mean_last_20": loss_mean_last_20,
        "contrastive_mean_last_20": contrastive_mean_last_20,
        "distill_mean_last_20": distill_mean_last_20,
        "triplet_mean_last_20": triplet_mean_last_20,
        "simdist_mean_last_20": simdist_mean_last_20,
        "export_teacher_tokenizer": bool(args.export_teacher_tokenizer),
        "removed_stale_tokenizer_files": removed_tokenizer_files,
    }
    (out / "train_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote distilled student -> {out}")
    if removed_tokenizer_files:
        print(f"[distill_subset] removed_stale_tokenizer_files={','.join(removed_tokenizer_files)}")
    if not bool(args.export_teacher_tokenizer):
        print("[distill_subset] note: tokenizer not exported; use base tokenizer + id_remap.json at runtime")
    print(f"[distill_subset] done elapsed={summary['duration_s']:.2f}s out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
