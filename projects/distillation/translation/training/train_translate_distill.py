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
import re
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


@dataclass(frozen=True)
class VocabRemap:
    old_to_new: dict[int, int]
    new_to_old: list[int]
    unk_old: int
    unk_new: int


def _safe_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_csv_set(value: str) -> set[str]:
    return {x.strip() for x in str(value).split(",") if x.strip()}


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True, help="Input translation triplets JSONL from make_translate_distill_pairs.py.")
    ap.add_argument("--teacher-model", required=True, help="Teacher model id/path (HF model id or local snapshot).")
    ap.add_argument("--student-model", required=True, help="Student base model id/path.")
    ap.add_argument(
        "--vocab-subset-dir",
        default="",
        help="Optional pruned-student directory containing id_remap.json (from tools/vocab_subset.py).",
    )
    ap.add_argument(
        "--tokenizer-model",
        default="",
        help=(
            "Optional tokenizer/model reference for student tokenization when --vocab-subset-dir is set. "
            "Defaults to --teacher-model."
        ),
    )
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
    ap.add_argument("--resume", action="store_true", help="Resume from checkpoints in the current run output dir.")
    ap.add_argument(
        "--resume-from",
        default="",
        help="Optional resume source path (checkpoint dir, stage dir, or run root). Defaults to --out-root/--run-name.",
    )

    ap.add_argument("--grad-clip", type=float, default=1.0)
    ap.add_argument("--skip-kd-when-device-mismatch", action="store_true")
    return ap.parse_args()


def _load_vocab_remap(path: str, tokenizer) -> VocabRemap | None:
    if not str(path).strip():
        return None
    subset_dir = Path(path)
    if not subset_dir.exists():
        raise RuntimeError(f"vocab subset dir does not exist: {subset_dir}")
    remap_path = subset_dir / "id_remap.json"
    if not remap_path.exists():
        raise RuntimeError(f"missing id_remap.json in vocab subset dir: {remap_path}")
    remap_data = _load_json(remap_path)
    raw = remap_data.get("old_to_new", {})
    if not isinstance(raw, dict) or not raw:
        raise RuntimeError(f"invalid id_remap.json (old_to_new missing/empty): {remap_path}")

    old_to_new: dict[int, int] = {}
    for k, v in raw.items():
        try:
            old = int(k)
            new = int(v)
        except Exception:
            continue
        old_to_new[old] = new
    if not old_to_new:
        raise RuntimeError(f"could not parse old_to_new ids from: {remap_path}")

    new_to_old = remap_data.get("new_to_old")
    parsed_new_to_old: list[int] | None = None
    if isinstance(new_to_old, list):
        parsed: list[int] = []
        for x in new_to_old:
            try:
                parsed.append(int(x))
            except Exception:
                continue
        if parsed:
            parsed_new_to_old = parsed

    if parsed_new_to_old is None:
        if not old_to_new:
            raise RuntimeError(f"invalid vocab remap in: {remap_path}")
        size = max(old_to_new.values()) + 1
        rev: list[int] = [-1] * int(size)
        for old, new in old_to_new.items():
            if 0 <= int(new) < int(size):
                rev[int(new)] = int(old)
        parsed_new_to_old = [int(x) for x in rev if int(x) >= 0]

    if not parsed_new_to_old:
        raise RuntimeError(f"could not parse new_to_old from: {remap_path}")

    unk_old = tokenizer.unk_token_id
    if unk_old is None:
        raise RuntimeError(f"tokenizer has no unk_token_id; cannot load subset remap: {tokenizer}")
    unk_old = int(unk_old)
    unk_new = old_to_new.get(unk_old)
    if unk_new is None:
        raise RuntimeError(f"id_remap.json is missing unk mapping for token id {unk_old}: {remap_path}")
    return VocabRemap(
        old_to_new=old_to_new,
        new_to_old=parsed_new_to_old,
        unk_old=int(unk_old),
        unk_new=int(unk_new),
    )


def _remap_ids(input_ids: torch.Tensor, remap: VocabRemap) -> torch.Tensor:
    if not remap.old_to_new:
        return input_ids
    ids = input_ids.cpu().tolist()
    unk = int(remap.unk_new)
    remapped: list[list[int]] = []
    for row in ids:
        out: list[int] = []
        for value in row:
            try:
                token = int(value)
            except Exception:
                token = unk
            if token < 0:
                out.append(int(token))
            else:
                out.append(int(remap.old_to_new.get(token, unk)))
        remapped.append(out)
    return torch.tensor(remapped, dtype=torch.long, device=input_ids.device)


def _remap_labels(labels: torch.Tensor, remap: VocabRemap) -> torch.Tensor:
    ids = labels.cpu().tolist()
    unk = int(remap.unk_new)
    remapped: list[list[int]] = []
    for row in ids:
        out: list[int] = []
        for value in row:
            try:
                token = int(value)
            except Exception:
                token = -100
            if token < 0:
                out.append(-100)
            else:
                out.append(int(remap.old_to_new.get(token, unk)))
        remapped.append(out)
    return torch.tensor(remapped, dtype=torch.long, device=labels.device)


def _project_teacher_logits_to_subset(teacher_logits: torch.Tensor, remap: VocabRemap) -> torch.Tensor:
    if int(teacher_logits.size(-1)) == len(remap.new_to_old):
        return teacher_logits
    idx = torch.as_tensor(remap.new_to_old, device=teacher_logits.device, dtype=torch.long)
    if idx.numel() <= 0:
        return teacher_logits
    if idx.max().item() >= teacher_logits.size(-1):
        raise RuntimeError(
            f"subset remap contains old token id >= teacher vocab ({int(idx.max().item())} >= {teacher_logits.size(-1)})."
        )
    return teacher_logits.index_select(dim=-1, index=idx)


def _restore_ids_to_old_vocab(token_ids: torch.Tensor, remap: VocabRemap) -> torch.Tensor:
    ids = token_ids.cpu().tolist()
    unk_old = int(remap.unk_old)
    restored: list[list[int]] = []
    for row in ids:
        out: list[int] = []
        for value in row:
            try:
                token = int(value)
            except Exception:
                token = -1
            if token < 0 or token >= len(remap.new_to_old):
                out.append(int(unk_old))
            else:
                out.append(int(remap.new_to_old[token]))
        restored.append(out)
    return torch.tensor(restored, dtype=torch.long, device=token_ids.device)


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

    input_ids = full_enc["input_ids"]
    attention_mask = full_enc["attention_mask"]
    token_type_ids = full_enc.get("token_type_ids")
    if isinstance(token_type_ids, torch.Tensor):
        token_type_ids = token_type_ids.clone()
    else:
        # Gemma3 requires token_type_ids for training, even when not returned by tokenizer.
        # Use a neutral all-zero tensor (one type segment) to satisfy model requirements.
        try:
            token_type_ids = torch.zeros(input_ids.shape, dtype=input_ids.dtype)
        except Exception:
            # Some ROCm/AMD kernels may fail to allocate this op on-device; generate on CPU then move to device.
            token_type_ids = torch.zeros(input_ids.shape, dtype=input_ids.dtype)
    batch_labels = full_enc["input_ids"].clone()
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
    return (
        input_ids.to(device),
        attention_mask.to(device),
        token_type_ids.to(device),
        batch_labels.to(device),
    )


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
    if shift_labels.numel() == 0 or not torch.any(shift_labels.ne(-100)):
        return torch.tensor(0.0, device=logits.device)
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


def _checkpoint_step_from_path(path: Path) -> int:
    name = path.name if path else ""
    m = re.fullmatch(r"checkpoint-(\d+)", name)
    if not m:
        return 0
    try:
        return int(m.group(1))
    except Exception:
        return 0


def _checkpoint_step(path: Path) -> int:
    state_path = Path(path) / "training_state.pt"
    if state_path.exists():
        try:
            state = torch.load(state_path, map_location="cpu")
            if isinstance(state, dict) and "step" in state:
                step = state["step"]
                if isinstance(step, torch.Tensor):
                    if step.numel() == 1:
                        return int(step.item())
                elif isinstance(step, int | float):
                    return int(step)
        except Exception:
            pass
    return _checkpoint_step_from_path(path)


def _latest_checkpoint_with_step(dir_path: Path) -> tuple[Path | None, int]:
    ckpt = _latest_checkpoint(dir_path)
    if ckpt is None:
        return None, 0
    return ckpt, _checkpoint_step(ckpt)


def _resolve_explicit_checkpoint(
    source: Path,
    schedule: str,
    sft_steps: int,
    distill_steps: int,
    total_steps: int,
) -> tuple[Path | None, str | None, int]:
    if not source.exists():
        raise RuntimeError(f"resume source missing: {source}")
    if source.is_dir() and source.name.startswith("checkpoint-"):
        stage = source.parent.name
        return source, stage if stage else None, _checkpoint_step(source)
    if source.is_dir() and source.name in {"mixed", "stage_a", "stage_b"}:
        ckpt, step = _latest_checkpoint_with_step(source)
        if ckpt is not None:
            return ckpt, source.name, step
        return None, None, 0
    return _resolve_auto_resume(source, schedule=schedule, sft_steps=sft_steps, distill_steps=distill_steps, total_steps=total_steps)


def _resolve_auto_resume(
    run_root: Path,
    schedule: str,
    sft_steps: int,
    distill_steps: int,
    total_steps: int,
) -> tuple[Path | None, str | None, int]:
    if schedule == "mixed_from_start":
        mixed_ckpt, mixed_step = _latest_checkpoint_with_step(run_root / "mixed")
        if mixed_ckpt is not None and mixed_step < int(total_steps):
            return mixed_ckpt, "mixed", mixed_step
        return None, None, 0

    stage_a_ckpt, stage_a_step = _latest_checkpoint_with_step(run_root / "stage_a")
    if stage_a_ckpt is not None and stage_a_step < int(sft_steps):
        return stage_a_ckpt, "stage_a", stage_a_step

    stage_b_ckpt, stage_b_step = _latest_checkpoint_with_step(run_root / "stage_b")
    if stage_b_ckpt is not None and stage_b_step < int(distill_steps):
        return stage_b_ckpt, "stage_b", stage_b_step

    return None, None, 0


def _load_checkpoint_state(path: Path) -> dict[str, Any]:
    p = Path(path)
    state_path = p / "training_state.pt"
    if not state_path.exists():
        return {}
    try:
        state = torch.load(state_path, map_location="cpu")
    except Exception:
        return {}
    return state if isinstance(state, dict) else {}


def _restore_rng_state(state: dict[str, Any], rng: random.Random, device: str) -> None:
    random_state = state.get("random_state")
    if random_state is not None:
        try:
            rng.setstate(random_state)
        except Exception:
            pass

    torch_rng = state.get("torch_rng_state")
    if isinstance(torch_rng, torch.Tensor):
        try:
            torch.set_rng_state(torch_rng)
        except Exception:
            pass

    cuda_rng = state.get("torch_cuda_rng_state")
    if isinstance(cuda_rng, list):
        try:
            if torch.cuda.is_available():
                torch.cuda.set_rng_state_all(cuda_rng)
        except Exception:
            pass

    if str(device).startswith("cuda") and isinstance(cuda_rng, torch.Tensor):
        try:
            torch.cuda.set_rng_state(cuda_rng)
        except Exception:
            pass


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


def _save_checkpoint(
    model,
    tokenizer,
    stage_dir: Path,
    step: int,
    optimizer: torch.optim.Optimizer | None = None,
    scheduler: Any | None = None,
    rng: random.Random | None = None,
) -> None:
    ckpt = stage_dir / f"checkpoint-{step:06d}"
    ckpt.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(ckpt))
    tokenizer.save_pretrained(str(ckpt))
    state = {
        "step": int(step),
        "timer": time.time(),
    }
    if optimizer is not None:
        try:
            state["optimizer_state_dict"] = optimizer.state_dict()
        except Exception:
            pass
    if scheduler is not None:
        try:
            state["scheduler_state_dict"] = scheduler.state_dict()
        except Exception:
            pass
    if rng is not None:
        try:
            state["random_state"] = rng.getstate()
        except Exception:
            pass
    state["torch_rng_state"] = torch.get_rng_state()
    if torch.cuda.is_available():
        try:
            state["torch_cuda_rng_state"] = torch.cuda.get_rng_state_all()
        except Exception:
            pass
    torch.save(
        state,
        ckpt / "training_state.pt",
    )


def _save_predictions(
    model,
    tokenizer,
    vocab_remap: VocabRemap | None,
    examples: list[Example],
    args: argparse.Namespace,
    stage_dir: Path,
    device: str,
) -> Path:
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
            if vocab_remap is not None:
                enc["input_ids"] = _remap_ids(enc["input_ids"], vocab_remap)
            prompt_len = int(enc["input_ids"].shape[1])
            gen = model.generate(
                **enc,
                max_new_tokens=int(args.max_new_tokens),
                do_sample=False,
            )
            pred_ids = gen[0][prompt_len:]
            if vocab_remap is not None:
                pred_ids = _restore_ids_to_old_vocab(pred_ids, vocab_remap)
            gen_text = tokenizer.decode(pred_ids, skip_special_tokens=True)
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
    vocab_remap: VocabRemap | None,
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
    start = max(0, int(start_step))
    total = max(0, int(num_steps))
    if start >= total:
        pred_path = stage_dir / "predictions.jsonl"
        return {
            "stage": stage_name,
            "steps": 0.0,
            "loss_final": 0.0,
            "loss_ce_final": 0.0,
            "loss_kd_final": 0.0,
            "loss_triplet_final": 0.0,
            "predictions": str(pred_path),
        }

    remaining_steps = max(0, total - start)
    for local_step in range(remaining_steps):
        step = start + local_step
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
        pos_ids_student = _remap_ids(pos_ids, vocab_remap) if vocab_remap is not None else pos_ids
        pos_labels_student = _remap_labels(pos_labels, vocab_remap) if vocab_remap is not None else pos_labels
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

        student_out = _forward_model(student, pos_ids_student, pos_mask, pos_token_types)
        student_logits = student_out.logits
        student_logits_loss = (
            _project_teacher_logits_to_subset(student_logits, vocab_remap)
            if vocab_remap is not None
            else student_logits
        )
        loss_pos = _ce_loss(student_logits_loss, pos_labels_student)

        loss_kd = torch.tensor(0.0, device=student_logits.device)
        if use_kd and teacher is not None:
            with torch.no_grad():
                teacher_out = _forward_model(teacher, pos_ids, pos_mask, pos_token_types)
                teacher_logits = teacher_out.logits
                if vocab_remap is not None:
                    teacher_logits = _project_teacher_logits_to_subset(teacher_logits, vocab_remap)
            loss_kd = _kd_loss(student_logits_loss, teacher_logits, pos_labels_student, float(args.kd_temperature))

        loss_triplet = torch.tensor(0.0, device=student_logits.device)
        if batch_use_triplet and neg_ids is not None:
            with torch.no_grad():
                # Triplet always uses student logits; no gradient from neg through this term.
                neg_ids_student = _remap_ids(neg_ids, vocab_remap) if vocab_remap is not None else neg_ids
                neg_labels_student = _remap_labels(neg_labels, vocab_remap) if vocab_remap is not None else neg_labels
                neg_out = _forward_model(student, neg_ids_student, neg_mask, neg_token_types)
                neg_logits = (
                    _project_teacher_logits_to_subset(neg_out.logits, vocab_remap)
                    if vocab_remap is not None
                    else neg_out.logits
                )
            loss_triplet = _triplet_loss(
                pos_logits=student_logits_loss,
                pos_labels=pos_labels_student,
                neg_logits=neg_logits,
                neg_labels=neg_labels_student,
                margin=float(args.margin),
            )

        loss = loss_pos + float(args.lambda_kd) * loss_kd + float(args.mu_triplet) * loss_triplet
        if (not torch.isfinite(loss)) or (not loss.requires_grad):
            continue

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

        global_step = step + 1
        if global_step % max(1, int(args.log_every)) == 0:
            lr = float(optimizer.param_groups[0]["lr"])
            rec = {
                "stage": stage_name,
                "global_step": int(global_step),
                "stage_step": int(global_step),
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

        if int(args.save_every) > 0 and global_step % int(args.save_every) == 0:
            _save_checkpoint(student, tokenizer, stage_dir, step=global_step, optimizer=optimizer, scheduler=scheduler, rng=rng)
    if not losses or total > 0:
        _save_checkpoint(student, tokenizer, stage_dir, step=total, optimizer=optimizer, scheduler=scheduler, rng=rng)

    pred_path = _save_predictions(student, tokenizer, vocab_remap, rows, args, stage_dir, device=device)
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

    stage_a_ckpt, stage_a_step = _latest_checkpoint_with_step(run_root / "stage_a")
    stage_b_ckpt, stage_b_step = _latest_checkpoint_with_step(run_root / "stage_b")
    mixed_ckpt, mixed_step = _latest_checkpoint_with_step(run_root / "mixed")

    resume_checkpoint = None
    resume_stage: str | None = None
    resume_step = 0
    if bool(args.resume):
        resume_source = Path(args.resume_from).expanduser() if str(args.resume_from).strip() else run_root
        resume_checkpoint, resume_stage, resume_step = _resolve_explicit_checkpoint(
            resume_source,
            schedule=str(args.schedule),
            sft_steps=int(sft_steps),
            distill_steps=int(distill_steps),
            total_steps=int(max_steps),
        )
        if resume_checkpoint is not None:
            print(f"[resume] checkpoint={resume_checkpoint} stage={resume_stage} step={resume_step}")
        else:
            print(f"[resume] no checkpoint found in {resume_source}; starting from scratch.")

    teacher, teacher_tok = _load_model_and_tokenizer(
        str(args.teacher_model),
        teacher_device,
        dtype=dtype,
        local_files_only=bool(args.local_files_only),
    )
    student_model_ref = str(args.student_model)
    if resume_checkpoint is not None:
        student_model_ref = str(resume_checkpoint)

    vocab_remap = None
    student_tokenizer_ref = str(args.tokenizer_model).strip()
    if str(args.vocab_subset_dir).strip():
        if not student_tokenizer_ref:
            student_tokenizer_ref = str(args.teacher_model)
        if not student_tokenizer_ref:
            student_tokenizer_ref = str(student_model_ref)
        if not student_tokenizer_ref:
            raise RuntimeError("vocab subset remap requested but no tokenizer model available for student tokenization.")

        tok = AutoTokenizer.from_pretrained(str(student_tokenizer_ref), local_files_only=bool(args.local_files_only))
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        vocab_remap = _load_vocab_remap(str(args.vocab_subset_dir), tokenizer=tok)
        student = AutoModelForCausalLM.from_pretrained(
            student_model_ref,
            torch_dtype=dtype,
            local_files_only=bool(args.local_files_only),
        ).to(device)
        student.eval()
    else:
        student, tok = _load_model_and_tokenizer(
            student_model_ref,
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
    if resume_checkpoint is not None:
        resume_state = _load_checkpoint_state(resume_checkpoint)
        _restore_rng_state(resume_state, rng=rng, device=str(device))
        if resume_state:
            state_step = resume_state.get("step")
            if isinstance(state_step, torch.Tensor):
                if state_step.numel() == 1:
                    resume_step = int(state_step.item())
            elif isinstance(state_step, (int, float)):
                resume_step = int(state_step)
            optim_state = resume_state.get("optimizer_state_dict")
            if isinstance(optim_state, dict):
                try:
                    optimizer.load_state_dict(optim_state)
                except Exception:
                    print("[resume] failed to restore optimizer state; continuing without it.")
            sched_state = resume_state.get("scheduler_state_dict")
            if isinstance(sched_state, dict):
                try:
                    scheduler.load_state_dict(sched_state)
                except Exception:
                    print("[resume] failed to restore scheduler state; continuing without it.")

    stage_a_complete = int(stage_a_step) >= int(sft_steps)
    stage_b_complete = int(stage_b_step) >= int(distill_steps)
    mixed_complete = int(mixed_step) >= int(max_steps)

    stage_a_start = 0
    stage_b_start = 0
    mixed_start = 0

    if args.schedule == "A_then_B":
        if resume_stage == "stage_a":
            stage_a_start = max(0, min(int(resume_step), int(sft_steps)))
        if resume_stage == "stage_b":
            stage_b_start = max(0, min(int(resume_step), int(distill_steps)))
    else:
        if resume_stage == "mixed":
            mixed_start = max(0, min(int(resume_step), int(max_steps)))

    if resume_step > 0:
        resume_step = max(0, int(resume_step))
        if resume_stage == "stage_a":
            stage_a_start = min(resume_step, int(sft_steps))
        elif resume_stage == "stage_b":
            stage_b_start = min(resume_step, int(distill_steps))
        elif resume_stage == "mixed":
            mixed_start = min(resume_step, int(max_steps))

    stage_results: list[dict[str, Any]] = []

    if args.schedule == "A_then_B":
        run_stage_a = True
        run_stage_b = True
        if bool(args.resume):
            run_stage_a = (resume_stage == "stage_a" and stage_a_start < int(sft_steps)) or (
                resume_stage is None and not stage_a_complete
            )
            run_stage_b = (resume_stage == "stage_b" and stage_b_start < int(distill_steps)) or (
                resume_stage is None and stage_a_complete and not stage_b_complete
            )
        stage_a_dir = run_root / "stage_a"
        stage_a: dict[str, float] = {}
        if run_stage_a:
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
                start_step=stage_a_start,
                num_steps=max(0, int(sft_steps)),
                use_kd=False,
                use_triplet=False,
                seed=int(args.seed),
                device=device,
                rng=rng,
                vocab_remap=vocab_remap,
            )
            stage_results.append(stage_a)

        stage_b_dir = run_root / "stage_b"
        stage_b: dict[str, float] = {}
        if run_stage_b:
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
                start_step=stage_b_start,
                num_steps=max(0, int(distill_steps)),
                use_kd=(not skip_kd),
                use_triplet=not (args.mu_triplet <= 0),
                seed=int(args.seed),
                device=device,
                rng=rng,
                vocab_remap=vocab_remap,
            )
            stage_results.append(stage_b)
    else:
        run_stage_mixed = True
        if bool(args.resume):
            run_stage_mixed = (resume_stage == "mixed" and mixed_start < int(max_steps)) or (
                resume_stage is None and not mixed_complete
            )
        stage_mix_dir = run_root / "mixed"
        stage_mix: dict[str, float] = {}
        if run_stage_mixed:
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
                start_step=mixed_start,
                num_steps=max(0, int(max_steps)),
                use_kd=(not skip_kd),
                use_triplet=not (args.mu_triplet <= 0),
                seed=int(args.seed),
                device=device,
                rng=rng,
                vocab_remap=vocab_remap,
            )
            stage_results.append(stage_mix)

    final_ckpt = run_root / "final"
    final_ckpt.mkdir(parents=True, exist_ok=True)
    student.save_pretrained(str(final_ckpt))
    tok.save_pretrained(str(final_ckpt))
    summary = {
        "timestamp": time.time(),
        "teacher_model": str(args.teacher_model),
        "student_model": student_model_ref,
        "student_subset_dir": str(args.vocab_subset_dir).strip(),
        "student_tokenizer_model": str(student_tokenizer_ref),
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
        "vocab_subset_active": bool(vocab_remap is not None),
        "student_vocab_size": int(len(vocab_remap.new_to_old)) if vocab_remap is not None else -1,
        "resumed": bool(args.resume) and resume_checkpoint is not None,
        "resume_from": str(resume_checkpoint) if resume_checkpoint is not None else "",
        "resume_stage": resume_stage,
        "resume_step": int(resume_step),
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
