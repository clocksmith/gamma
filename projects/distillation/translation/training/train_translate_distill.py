#!/usr/bin/env python3
"""
Train TranslateGemma-style students on translation triplets with optional
distillation and triplet mining objectives.

Supported schedules:
- A_then_B: Stage A does SFT on (query -> target_pos), Stage B adds KD + triplet.
- mixed_from_start: SFT and KD + triplet from step 1.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer, get_linear_schedule_with_warmup

try:
    from peft import LoraConfig, TaskType, get_peft_model
except Exception:  # pragma: no cover - optional dependency
    LoraConfig = None
    TaskType = None
    get_peft_model = None


@dataclass(frozen=True)
class Example:
    source_lang: str
    target_lang: str
    source: str
    target_pos: str
    target_neg: str
    pair: str


def _safe_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _parse_csv_set(value: str) -> set[str]:
    return {x.strip() for x in str(value).split(",") if x.strip()}


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True, help="Input translation triplets JSONL from make_translate_distill_pairs.py.")
    ap.add_argument("--teacher-model", required=True, help="Teacher model id/path (HF model id or local snapshot).")
    ap.add_argument("--student-model", required=True, help="Student base model id/path.")
    ap.add_argument(
        "--source-langs",
        default="",
        help="Optional comma-separated source language filter (empty=all).",
    )
    ap.add_argument(
        "--target-langs",
        default="",
        help='Optional comma-separated target language filter (example: "en,es").',
    )
    ap.add_argument("--out-root", default="projects/distillation/translation/runs/exp01")
    ap.add_argument("--summary-out", default="")
    ap.add_argument("--run-name", default="")

    ap.add_argument("--schedule", choices=["A_then_B", "mixed_from_start"], default="A_then_B")
    ap.add_argument("--total-steps", type=int, default=1000)
    ap.add_argument("--sft-steps", type=int, default=0, help="For A_then_B, step split for Stage A. 0 = half of total.")

    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--accum-steps", type=int, default=1, help="Gradient accumulation steps.")
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--max-steps-per-row", type=int, default=0)
    ap.add_argument("--max-seq-length", type=int, default=1536)
    ap.add_argument("--max-prompt-length", type=int, default=256)
    ap.add_argument("--predict-samples", type=int, default=0)
    ap.add_argument("--max-new-tokens", type=int, default=192)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--lr-warmup-steps", type=int, default=20)
    ap.add_argument("--save-every", type=int, default=200)
    ap.add_argument("--log-every", type=int, default=20)
    ap.add_argument("--lambda-kd", type=float, default=0.5)
    ap.add_argument("--mu-triplet", type=float, default=0.1)
    ap.add_argument("--margin", type=float, default=0.2)
    ap.add_argument("--kd-temperature", type=float, default=1.0)

    ap.add_argument("--enable-lora", action="store_true", help="Enable PEFT LoRA on the student model.")
    ap.add_argument("--lora-rank", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--lora-dropout", type=float, default=0.05)
    ap.add_argument("--lora-modules", default="q_proj,k_proj,v_proj,o_proj,up_proj,down_proj,gate_proj")

    ap.add_argument("--device", default="auto")
    ap.add_argument("--teacher-device", default="")
    ap.add_argument("--dtype", default="auto", choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument(
        "--allow-download",
        action="store_false",
        dest="local_files_only",
        default=True,
        help="Allow fetching missing models from network (default uses local cache only).",
    )

    ap.add_argument("--grad-clip", type=float, default=1.0)
    ap.add_argument("--skip-kd-when-device-mismatch", action="store_true")
    return ap.parse_args()


def _load_pairs(path: Path, source_langs: set[str], target_langs: set[str]) -> list[Example]:
    path = Path(path)
    if not path.exists():
        raise RuntimeError(f"pairs file missing: {path}")
    rows: list[Example] = []
    with path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if not isinstance(obj, dict):
                continue
            source_lang = _safe_text(obj.get("src_lang") or obj.get("source_lang") or obj.get("src"))
            target_lang = _safe_text(obj.get("tgt_lang") or obj.get("target_lang") or obj.get("tgt"))
            source = _safe_text(obj.get("source"))
            target_pos = _safe_text(obj.get("target_pos") or obj.get("pos"))
            target_neg = _safe_text(obj.get("target_neg") or obj.get("neg"))
            pair = _safe_text(obj.get("pair"))

            if source_langs and source_lang not in source_langs:
                continue
            if target_langs and target_lang not in target_langs:
                continue
            if not source or not target_pos or not source_lang or not target_lang:
                continue
            if not pair:
                pair = f"{source_lang}-{target_lang}"
            rows.append(
                Example(
                    source_lang=source_lang,
                    target_lang=target_lang,
                    source=source,
                    target_pos=target_pos,
                    target_neg=target_neg,
                    pair=pair,
                )
            )
    return rows


def _choose_torch_dtype(dtype: str) -> torch.dtype:
    if dtype == "float16":
        return torch.float16
    if dtype == "bfloat16":
        return torch.bfloat16
    if dtype == "float32":
        return torch.float32
    if torch.cuda.is_available():
        return torch.bfloat16
    return torch.float32


def _resolve_device(device: str, *, fallback: str = "cpu") -> str:
    if device and device != "auto":
        return str(device)
    if torch.cuda.is_available():
        return "cuda"
    return fallback


def _build_user_message(source_lang: str, target_lang: str, source_text: str, use_list_payload: bool) -> dict[str, Any]:
    item = {
        "type": "text",
        "source_lang_code": source_lang,
        "target_lang_code": target_lang,
        "text": source_text,
    }
    if use_list_payload:
        content = [item]
    else:
        content = json.dumps(item, ensure_ascii=False)
    return {"role": "user", "content": content}


def _to_chat_text(
    tokenizer,
    source_lang: str,
    target_lang: str,
    source_text: str,
    answer_text: str | None = None,
) -> tuple[str, str]:
    user_message = _build_user_message(source_lang, target_lang, source_text, use_list_payload=True)
    fallback_prompt = f"[{source_lang} -> {target_lang}] {source_text}"
    fallback_full = f"[{source_lang} -> {target_lang}] {source_text}\n{answer_text}" if answer_text else fallback_prompt
    prompt_text = fallback_prompt
    full_text = fallback_full
    use_list_payload = False

    try:
        has_chat_template = getattr(tokenizer, "chat_template", None) is not None
    except Exception:
        has_chat_template = False

    if has_chat_template and tokenizer is not None:
        try:
            prompt_text = tokenizer.apply_chat_template([user_message], tokenize=False, add_generation_prompt=True)
            if answer_text is None:
                full_text = prompt_text
            else:
                assistant_message = {"role": "assistant", "content": answer_text}
                full_text = tokenizer.apply_chat_template(
                    [user_message, assistant_message],
                    tokenize=False,
                    add_generation_prompt=False,
                )
            use_list_payload = True
        except Exception:
            use_list_payload = False

    if not use_list_payload:
        try:
            user_message["content"] = json.dumps(user_message["content"], ensure_ascii=False)
            if has_chat_template and tokenizer is not None:
                if answer_text is None:
                    prompt_text = tokenizer.apply_chat_template([user_message], tokenize=False, add_generation_prompt=True)
                else:
                    assistant_message = {"role": "assistant", "content": answer_text}
                    full_text = tokenizer.apply_chat_template(
                        [user_message, assistant_message],
                        tokenize=False,
                        add_generation_prompt=False,
                    )
            else:
                prompt_text = fallback_prompt
                full_text = fallback_full if answer_text is not None else fallback_prompt
        except Exception:
            prompt_text = fallback_prompt
            full_text = fallback_full if answer_text is not None else fallback_prompt

    return prompt_text, full_text


def _encode_chat_batch(
    tokenizer,
    rows: Iterable[Example],
    max_seq_length: int,
    max_prompt_length: int,
    device: str,
    target_key: str = "target_pos",
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None, torch.Tensor]:
    prompt_texts: list[str] = []
    full_texts: list[str] = []

    for ex in rows:
        prompt_text, full_text = _to_chat_text(
            tokenizer,
            ex.source_lang,
            ex.target_lang,
            ex.source,
            ex.target_pos if target_key == "target_pos" else ex.target_neg,
        )
        prompt_text = prompt_text[:2048]
        prompt_texts.append(prompt_text)
        full_texts.append(full_text)

    prompt_enc = tokenizer(
        prompt_texts,
        return_tensors="pt",
        truncation=True,
        max_length=max_prompt_length,
        padding=True,
        add_special_tokens=False,
    )
    full_enc = tokenizer(
        full_texts,
        return_tensors="pt",
        truncation=True,
        max_length=max_seq_length,
        padding=True,
    )

    input_ids = full_enc["input_ids"].to(device)
    attention_mask = full_enc["attention_mask"].to(device)
    token_type_ids = full_enc.get("token_type_ids")
    if isinstance(token_type_ids, torch.Tensor):
        token_type_ids = token_type_ids.to(device)
    else:
        # Gemma3 requires token_type_ids for training, even when not returned by tokenizer.
        # Use a neutral all-zero tensor (one type segment) to satisfy model requirements.
        token_type_ids = torch.zeros_like(input_ids)
    batch_labels = full_enc["input_ids"].clone()
    batch_labels[:, :] = -100
    for i in range(input_ids.size(0)):
        plen = int(prompt_enc["attention_mask"][i].sum().item())
        if plen < input_ids.size(1):
            batch_labels[i, :plen] = -100
        else:
            # prompt alone consumed all tokens; no target tokens for this sample.
            batch_labels[i, :] = -100
        pad_mask = attention_mask[i].eq(0)
        if pad_mask.any():
            batch_labels[i, pad_mask] = -100
    return input_ids, attention_mask, token_type_ids, batch_labels.to(device)


def _forward_model(model, input_ids, attention_mask, token_type_ids, labels=None):
    kwargs = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
    }
    if token_type_ids is not None:
        kwargs["token_type_ids"] = token_type_ids
    if labels is not None:
        kwargs["labels"] = labels
    try:
        return model(**kwargs)
    except TypeError as exc:
        if token_type_ids is None:
            raise
        # Some model implementations do not accept token_type_ids; retry without it.
        kwargs.pop("token_type_ids", None)
        try:
            return model(**kwargs)
        except TypeError:
            raise exc


def _shift_logits_and_labels(logits: torch.Tensor, labels: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    shift_logits = logits[:, :-1, :].contiguous()
    shift_labels = labels[:, 1:].contiguous()
    return shift_logits, shift_labels


def _ce_loss(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    shift_logits, shift_labels = _shift_logits_and_labels(logits, labels)
    return F.cross_entropy(
        shift_logits.view(-1, shift_logits.size(-1)),
        shift_labels.view(-1),
        ignore_index=-100,
    )


def _kd_loss(student_logits: torch.Tensor, teacher_logits: torch.Tensor, labels: torch.Tensor, temperature: float) -> torch.Tensor:
    shift_s, shift_labels = _shift_logits_and_labels(student_logits, labels)
    shift_t, _ = _shift_logits_and_labels(teacher_logits, labels)
    if temperature <= 0:
        temperature = 1.0
    mask = shift_labels.ne(-100).view(-1)
    if not torch.any(mask):
        return torch.tensor(0.0, device=student_logits.device)
    flat_s = shift_s.view(-1, shift_s.size(-1))[mask]
    flat_t = shift_t.view(-1, shift_t.size(-1))[mask]
    t = float(temperature)
    sl = F.log_softmax(flat_s / t, dim=-1)
    tp = F.softmax(flat_t / t, dim=-1)
    return F.kl_div(sl, tp, reduction="batchmean") * (t * t)


def _sequence_score(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    shift_logits, shift_labels = _shift_logits_and_labels(logits, labels)
    logp = F.log_softmax(shift_logits, dim=-1)
    batch, seqlen, vocab = logp.shape
    label_flat = shift_labels.view(-1)
    mask = label_flat.ne(-100)
    if not torch.any(mask):
        return torch.zeros((batch,), device=logits.device)
    idx = label_flat.clamp_min(0).unsqueeze(-1)
    token_logp = logp.view(-1, vocab).gather(-1, idx).squeeze(-1)
    token_logp = token_logp * mask.to(logp.dtype)
    token_logp = token_logp.view(batch, seqlen)
    mask_b = shift_labels.ne(-100).to(logp.dtype)
    tok_counts = mask_b.sum(dim=1).clamp_min(1.0)
    scores = (token_logp * mask_b).sum(dim=1) / tok_counts
    return scores


def _triplet_loss(pos_logits: torch.Tensor, pos_labels: torch.Tensor, neg_logits: torch.Tensor, neg_labels: torch.Tensor, margin: float) -> torch.Tensor:
    pos_score = _sequence_score(pos_logits, pos_labels)
    neg_score = _sequence_score(neg_logits, neg_labels)
    if pos_score.numel() == 0 or neg_score.numel() == 0:
        return torch.tensor(0.0, device=pos_logits.device)
    return F.relu(torch.tensor(float(margin), device=pos_logits.device) + neg_score - pos_score).mean()


def _latest_checkpoint(dir_path: Path) -> Path | None:
    if not dir_path.exists():
        return None
    candidates = sorted(dir_path.glob("checkpoint-*"), key=lambda p: p.name)
    return candidates[-1] if candidates else None


def _load_model_and_tokenizer(model_ref: str, device: str, dtype: torch.dtype, local_files_only: bool):
    tok = AutoTokenizer.from_pretrained(model_ref, local_files_only=local_files_only)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_ref,
        torch_dtype=dtype,
        local_files_only=local_files_only,
    )
    model.to(device)
    model.eval()
    return model, tok


def _apply_lora(model, args: argparse.Namespace):
    if not bool(args.enable_lora):
        return model, False
    if LoraConfig is None or TaskType is None or get_peft_model is None:
        raise RuntimeError(
            "LoRA requested but 'peft' is not installed. Install `peft` or run without --enable-lora."
        )
    target_modules = [x.strip() for x in str(args.lora_modules).split(",") if x.strip()]
    config = LoraConfig(
        r=int(args.lora_rank),
        lora_alpha=int(args.lora_alpha),
        lora_dropout=float(args.lora_dropout),
        target_modules=target_modules or ["q_proj", "k_proj", "v_proj", "o_proj", "up_proj", "down_proj", "gate_proj"],
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    return get_peft_model(model, config), True


def _count_trainable_parameters(model) -> dict[str, float]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {
        "param_count_total": float(total),
        "param_count_trainable": float(trainable),
        "trainable_ratio": float(trainable / max(1, total)),
    }


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _save_checkpoint(model, tokenizer, stage_dir: Path, step: int) -> None:
    ckpt = stage_dir / f"checkpoint-{step:06d}"
    ckpt.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(ckpt))
    tokenizer.save_pretrained(str(ckpt))
    torch.save(
        {"step": int(step)},
        ckpt / "training_state.pt",
    )


def _save_predictions(model, tokenizer, examples: list[Example], args: argparse.Namespace, stage_dir: Path, device: str) -> Path:
    if args.predict_samples <= 0:
        return stage_dir / "predictions.jsonl"
    out_path = stage_dir / "predictions.jsonl"
    model.eval()
    preds: list[dict[str, Any]] = []
    n = min(int(args.predict_samples), len(examples))
    with torch.no_grad():
        for ex in examples[:n]:
            prompt_text, _ = _to_chat_text(tokenizer, ex.source_lang, ex.target_lang, ex.source, None)
            enc = tokenizer(
                prompt_text,
                return_tensors="pt",
                truncation=True,
                max_length=int(args.max_prompt_length),
            ).to(device)
            prompt_len = int(enc["input_ids"].shape[1])
            gen = model.generate(
                **enc,
                max_new_tokens=int(args.max_new_tokens),
                do_sample=False,
            )
            gen_text = tokenizer.decode(gen[0][prompt_len:], skip_special_tokens=True)
            pred = _safe_text(gen_text)
            preds.append(
                {
                    "pair": ex.pair,
                    "src_lang": ex.source_lang,
                    "tgt_lang": ex.target_lang,
                    "source": ex.source,
                    "target_pos": ex.target_pos,
                    "target_neg": ex.target_neg,
                    "pred": pred,
                }
            )
    out_path.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in preds) + ("\n" if preds else ""),
        encoding="utf-8",
    )
    return out_path


def _train_stage(
    stage_name: str,
    rows: list[Example],
    student,
    tokenizer,
    teacher,
    optimizer,
    scheduler,
    args: argparse.Namespace,
    stage_dir: Path,
    start_step: int,
    num_steps: int,
    use_kd: bool,
    use_triplet: bool,
    seed: int,
    device: str,
    rng: random.Random,
) -> dict[str, float]:
    if num_steps <= 0:
        return {}
    stage_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = stage_dir / "metrics.jsonl"
    if not metrics_path.exists():
        _append_jsonl(
            metrics_path,
            {
                "stage": stage_name,
                "seed": int(seed),
                "batch_size": int(args.batch_size),
                "use_kd": bool(use_kd),
                "use_triplet": bool(use_triplet),
            },
        )

    student.train()
    if teacher is not None:
        teacher.eval()
    losses = []
    ce_hist: list[float] = []
    kd_hist: list[float] = []
    tri_hist: list[float] = []
    step_start = time.perf_counter()

    for step in range(num_steps):
        batch_idx = [rng.randrange(len(rows)) for _ in range(int(args.batch_size))]
        batch = [rows[i] for i in batch_idx]
        pos_ids, pos_mask, pos_token_types, pos_labels = _encode_chat_batch(
            tokenizer,
            batch,
            max_seq_length=int(args.max_seq_length),
            max_prompt_length=int(args.max_prompt_length),
            device=device,
            target_key="target_pos",
        )
        has_neg = any(bool(_safe_text(ex.target_neg)) for ex in batch)
        batch_use_triplet = bool(use_triplet and has_neg)
        if has_neg:
            neg_ids, neg_mask, neg_token_types, neg_labels = _encode_chat_batch(
                tokenizer,
                batch,
                max_seq_length=int(args.max_seq_length),
                max_prompt_length=int(args.max_prompt_length),
                device=device,
                target_key="target_neg",
            )
        else:
            neg_ids = neg_mask = neg_labels = None

        student_out = _forward_model(student, pos_ids, pos_mask, pos_token_types)
        student_logits = student_out.logits
        loss_pos = _ce_loss(student_logits, pos_labels)

        loss_kd = torch.tensor(0.0, device=student_logits.device)
        if use_kd and teacher is not None:
            with torch.no_grad():
                teacher_out = _forward_model(teacher, pos_ids, pos_mask, pos_token_types)
            loss_kd = _kd_loss(student_logits, teacher_out.logits, pos_labels, float(args.kd_temperature))

        loss_triplet = torch.tensor(0.0, device=student_logits.device)
        if batch_use_triplet and neg_ids is not None:
            with torch.no_grad():
                # Triplet always uses student logits; no gradient from neg through this term.
                neg_out = _forward_model(student, neg_ids, neg_mask, neg_token_types)
            loss_triplet = _triplet_loss(
                pos_logits=student_logits,
                pos_labels=pos_labels,
                neg_logits=neg_out.logits,
                neg_labels=neg_labels,
                margin=float(args.margin),
            )

        loss = loss_pos + float(args.lambda_kd) * loss_kd + float(args.mu_triplet) * loss_triplet
        loss.backward()
        if (step + 1) % int(args.accum_steps) == 0:
            if float(args.grad_clip) > 0:
                torch.nn.utils.clip_grad_norm_(student.parameters(), float(args.grad_clip))
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)

        loss_val = float(loss.item())
        losses.append(loss_val)
        ce_hist.append(float(loss_pos.item()))
        kd_hist.append(float(loss_kd.item()))
        tri_hist.append(float(loss_triplet.item()))

        global_step = start_step + step + 1
        if (step + 1) % max(1, int(args.log_every)) == 0:
            lr = float(optimizer.param_groups[0]["lr"])
            rec = {
                "stage": stage_name,
                "global_step": int(global_step),
                "stage_step": int(step + 1),
                "loss": statistics.fmean(losses[-min(len(losses), 20):]) if losses else 0.0,
                "loss_ce": statistics.fmean(ce_hist[-min(len(ce_hist), 20):]) if ce_hist else 0.0,
                "loss_kd": statistics.fmean(kd_hist[-min(len(kd_hist), 20):]) if kd_hist else 0.0,
                "loss_triplet": statistics.fmean(tri_hist[-min(len(tri_hist), 20):]) if tri_hist else 0.0,
                "lr": lr,
                "elapsed_s": float(time.perf_counter() - step_start),
            }
            _append_jsonl(metrics_path, rec)
            print(
                f"[{stage_name}] step={global_step} loss={rec['loss']:.4f} ce={rec['loss_ce']:.4f} "
                f"kd={rec['loss_kd']:.4f} tri={rec['loss_triplet']:.4f} lr={lr:.2e}"
            )

        if int(args.save_every) > 0 and (step + 1) % int(args.save_every) == 0:
            _save_checkpoint(student, tokenizer, stage_dir, step=global_step)

    _save_checkpoint(student, tokenizer, stage_dir, step=start_step + num_steps)

    pred_path = _save_predictions(student, tokenizer, rows, args, stage_dir, device=device)
    return {
        "stage": stage_name,
        "steps": float(num_steps),
        "loss_final": float(losses[-1]) if losses else 0.0,
        "loss_ce_final": float(ce_hist[-1]) if ce_hist else 0.0,
        "loss_kd_final": float(kd_hist[-1]) if kd_hist else 0.0,
        "loss_triplet_final": float(tri_hist[-1]) if tri_hist else 0.0,
        "predictions": str(pred_path),
    }


def _build_optimizer(model, args: argparse.Namespace) -> torch.optim.Optimizer:
    return torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=float(args.lr),
        weight_decay=float(args.weight_decay),
    )


def _build_scheduler(optimizer, args: argparse.Namespace, total_updates: int):
    total_updates = max(1, int(total_updates))
    warmup = int(args.lr_warmup_steps)
    warmup = min(warmup, total_updates)
    return get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup, num_training_steps=total_updates)


def main() -> int:
    args = _parse_args()
    torch.manual_seed(int(args.seed))
    random.seed(int(args.seed))
    device = _resolve_device(str(args.device))
    teacher_device = _resolve_device(str(args.teacher_device) or device)
    dtype = _choose_torch_dtype(str(args.dtype))

    source_langs = _parse_csv_set(str(args.source_langs))
    target_langs = _parse_csv_set(str(args.target_langs))
    pair_rows = _load_pairs(Path(args.pairs), source_langs=source_langs, target_langs=target_langs)
    if args.max_steps_per_row > 0:
        pair_rows = pair_rows[: int(args.max_steps_per_row)]
    if not pair_rows:
        raise RuntimeError("No training rows after filtering.")
    random.shuffle(pair_rows)
    max_steps = int(args.total_steps)
    sft_steps = int(args.sft_steps)
    if args.schedule == "A_then_B":
        if sft_steps <= 0:
            sft_steps = max(1, max_steps // 2)
        distill_steps = max(1, max_steps - sft_steps)
    else:
        sft_steps = 0
        distill_steps = 0

    out_root = Path(args.out_root)
    run_name = _safe_text(args.run_name) or "translate_distill"
    run_root = out_root / run_name
    run_root.mkdir(parents=True, exist_ok=True)

    print(f"[config] run_root={run_root}")
    print(
        f"[config] schedule={args.schedule} total_steps={max_steps} sft_steps={sft_steps} "
        f"distill_steps={distill_steps} batch={args.batch_size}"
    )

    teacher, teacher_tok = _load_model_and_tokenizer(
        str(args.teacher_model),
        teacher_device,
        dtype=dtype,
        local_files_only=bool(args.local_files_only),
    )
    student, tok = _load_model_and_tokenizer(
        str(args.student_model),
        device,
        dtype=dtype,
        local_files_only=bool(args.local_files_only),
    )

    if str(teacher_tok.get_vocab()) != str(tok.get_vocab()) and args.skip_kd_when_device_mismatch:
        print("[warn] teacher/student tokenizers appear incompatible; KD disabled.")
        # still keep teacher loaded, but we will not use it if incompatible.
        skip_kd = True
    else:
        skip_kd = False

    student, lora_enabled = _apply_lora(student, args)
    if lora_enabled:
        print("[lora] enabled")
    print("[model] trainable counts:", _count_trainable_parameters(student))

    student.train()
    optimizer = _build_optimizer(student, args)
    total_updates = sft_steps + (distill_steps if args.schedule == "A_then_B" else max_steps)
    scheduler = _build_scheduler(optimizer, args, max(1, total_updates))

    rng = random.Random(int(args.seed))
    stage_results: list[dict[str, Any]] = []

    if args.schedule == "A_then_B":
        stage_a_dir = run_root / "stage_a"
        stage_a = _train_stage(
            stage_name="A_then_B_stage_a",
            rows=pair_rows,
            student=student,
            tokenizer=tok,
            teacher=None,
            optimizer=optimizer,
            scheduler=scheduler,
            args=args,
            stage_dir=stage_a_dir,
            start_step=0,
            num_steps=max(0, int(sft_steps)),
            use_kd=False,
            use_triplet=False,
            seed=int(args.seed),
            device=device,
            rng=rng,
        )
        if stage_a:
            stage_results.append(stage_a)

        stage_b_dir = run_root / "stage_b"
        stage_b = _train_stage(
            stage_name="A_then_B_stage_b",
            rows=pair_rows,
            student=student,
            tokenizer=tok,
            teacher=teacher if not skip_kd else None,
            optimizer=optimizer,
            scheduler=scheduler,
            args=args,
            stage_dir=stage_b_dir,
            start_step=0,
            num_steps=max(0, int(distill_steps)),
            use_kd=(not skip_kd),
            use_triplet=not (args.mu_triplet <= 0),
            seed=int(args.seed),
            device=device,
            rng=rng,
        )
        if stage_b:
            stage_results.append(stage_b)
    else:
        stage_mix_dir = run_root / "mixed"
        stage_mix = _train_stage(
            stage_name="mixed_from_start",
            rows=pair_rows,
            student=student,
            tokenizer=tok,
            teacher=teacher if not skip_kd else None,
            optimizer=optimizer,
            scheduler=scheduler,
            args=args,
            stage_dir=stage_mix_dir,
            start_step=0,
            num_steps=max(0, int(max_steps)),
            use_kd=(not skip_kd),
            use_triplet=not (args.mu_triplet <= 0),
            seed=int(args.seed),
            device=device,
            rng=rng,
        )
        if stage_mix:
            stage_results.append(stage_mix)

    final_ckpt = run_root / "final"
    final_ckpt.mkdir(parents=True, exist_ok=True)
    student.save_pretrained(str(final_ckpt))
    tok.save_pretrained(str(final_ckpt))
    summary = {
        "timestamp": time.time(),
        "teacher_model": str(args.teacher_model),
        "student_model": str(args.student_model),
        "schedule": str(args.schedule),
        "source_langs": sorted(source_langs),
        "target_langs": sorted(target_langs),
        "out_root": str(run_root),
        "pair_count": int(len(pair_rows)),
        "total_steps": int(max_steps),
        "sft_steps": int(sft_steps),
        "distill_steps": int(distill_steps),
        "lora_enabled": bool(lora_enabled),
        "lambda_kd": float(args.lambda_kd),
        "mu_triplet": float(args.mu_triplet),
        "margin": float(args.margin),
        "kd_temperature": float(args.kd_temperature),
        "stages": stage_results,
        "final_out": str(final_ckpt),
    }

    sum_out = Path(args.summary_out) if args.summary_out else run_root / "train_summary.json"
    sum_out.parent.mkdir(parents=True, exist_ok=True)
    sum_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote summary -> {sum_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
