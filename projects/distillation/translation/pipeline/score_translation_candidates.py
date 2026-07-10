#!/usr/bin/env python3
"""Score sampled translation candidates with their student's conditional log-probability."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _safe_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


def _build_user_message(source_lang: str, target_lang: str, source_text: str) -> dict[str, Any]:
    return {
        "role": "user",
        "content": [
            {
                "type": "text",
                "source_lang_code": source_lang,
                "target_lang_code": target_lang,
                "text": source_text,
            }
        ],
    }


def _to_chat_text(tokenizer: Any, source_lang: str, target_lang: str, source_text: str) -> str:
    user_message = _build_user_message(source_lang, target_lang, source_text)
    fallback = f"[{source_lang} -> {target_lang}] {source_text}"
    try:
        return tokenizer.apply_chat_template([user_message], tokenize=False, add_generation_prompt=True)
    except Exception:
        user_message["content"] = json.dumps(user_message["content"], ensure_ascii=False)
        try:
            return tokenizer.apply_chat_template([user_message], tokenize=False, add_generation_prompt=True)
        except Exception:
            return fallback


def _longest_common_prefix(left: list[int], right: list[int]) -> int:
    size = min(len(left), len(right))
    index = 0
    while index < size and left[index] == right[index]:
        index += 1
    return index


def _choose_dtype(value: str) -> torch.dtype:
    if value == "float16":
        return torch.float16
    if value == "bfloat16":
        return torch.bfloat16
    if value == "float32":
        return torch.float32
    return torch.bfloat16 if torch.cuda.is_available() else torch.float32


def _resolve_device(value: str) -> str:
    if value and value != "auto":
        return value
    return "cuda" if torch.cuda.is_available() else "cpu"


def _validated_score_key(value: str) -> str:
    key = str(value).strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", key):
        raise RuntimeError(f"Invalid --score-key: {value!r}")
    return key


def _target_logprob_scores(
    logits: torch.Tensor,
    input_ids: torch.Tensor,
    raw_lengths: list[int],
    target_starts: list[int],
) -> list[dict[str, float | int]]:
    shift_logits = logits[:, :-1, :].float()
    shift_targets = input_ids[:, 1:]
    token_nll = F.cross_entropy(
        shift_logits.transpose(1, 2),
        shift_targets,
        reduction="none",
    )
    scores: list[dict[str, float | int]] = []
    padded_length = int(input_ids.shape[1])
    for row_index, (raw_length, target_start) in enumerate(zip(raw_lengths, target_starts, strict=True)):
        pad_count = padded_length - raw_length
        shift_start = max(0, pad_count + target_start - 1)
        shift_end = pad_count + raw_length - 1
        losses = token_nll[row_index, shift_start:shift_end]
        token_count = int(losses.numel())
        if token_count <= 0:
            raise RuntimeError("Candidate scoring produced zero target tokens.")
        sum_logprob = -float(losses.sum().item())
        scores.append(
            {
                "sum_logprob": sum_logprob,
                "mean_logprob": sum_logprob / token_count,
                "token_count": token_count,
            }
        )
    return scores


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise RuntimeError(f"{path}:{line_number}: expected a JSON object")
            candidates = row.get("candidates")
            if not isinstance(candidates, list) or not candidates:
                raise RuntimeError(f"{path}:{line_number}: candidates must be a non-empty list")
            rows.append(row)
    if not rows:
        raise RuntimeError(f"No candidate rows found in {path}")
    return rows


def _score_candidate_batch(
    *,
    model: Any,
    tokenizer: Any,
    prompt: str,
    candidates: list[str],
    device: str,
    max_seq_length: int,
) -> list[dict[str, float | int]]:
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    full_texts = [prompt + candidate for candidate in candidates]
    raw_full_ids = [tokenizer(text, add_special_tokens=False)["input_ids"] for text in full_texts]
    too_long = [len(ids) for ids in raw_full_ids if len(ids) > max_seq_length]
    if too_long:
        raise RuntimeError(
            f"Candidate sequence exceeds --max-seq-length={max_seq_length}; longest={max(too_long)}"
        )
    target_starts = [_longest_common_prefix(prompt_ids, ids) for ids in raw_full_ids]
    if any(start <= 0 or start >= len(ids) for start, ids in zip(target_starts, raw_full_ids, strict=True)):
        raise RuntimeError("Could not resolve a non-empty candidate token boundary.")

    encoded = tokenizer(
        full_texts,
        return_tensors="pt",
        padding=True,
        add_special_tokens=False,
    )
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask).logits
    return _target_logprob_scores(
        logits,
        input_ids,
        [len(ids) for ids in raw_full_ids],
        target_starts,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary-out", required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dtype", default="auto", choices=["auto", "float16", "bfloat16", "float32"])
    parser.add_argument("--max-seq-length", type=int, default=448)
    parser.add_argument("--log-every", type=int, default=16)
    parser.add_argument("--score-key", default="candidate_model_scores")
    parser.add_argument("--allow-download", action="store_false", dest="local_files_only", default=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    score_key = _validated_score_key(str(args.score_key))
    input_path = Path(args.predictions).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    summary_path = Path(args.summary_out).expanduser().resolve()
    if not input_path.is_file():
        raise RuntimeError(f"Predictions do not exist: {input_path}")
    rows = _load_rows(input_path)
    device = _resolve_device(str(args.device))
    dtype = _choose_dtype(str(args.dtype))
    tokenizer = AutoTokenizer.from_pretrained(str(args.model), local_files_only=bool(args.local_files_only))
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        str(args.model),
        torch_dtype=dtype,
        local_files_only=bool(args.local_files_only),
    ).to(device)
    model.eval()

    output_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=1):
        source_lang = _safe_text(row.get("src_lang"))
        target_lang = _safe_text(row.get("tgt_lang"))
        source = _safe_text(row.get("source"))
        candidates = [_safe_text(value) for value in row["candidates"]]
        if not source_lang or not target_lang or not source or any(not value for value in candidates):
            raise RuntimeError(f"Row {row_index} has empty translation fields or candidates.")
        prompt = _to_chat_text(tokenizer, source_lang, target_lang, source)
        scores = _score_candidate_batch(
            model=model,
            tokenizer=tokenizer,
            prompt=prompt,
            candidates=candidates,
            device=device,
            max_seq_length=int(args.max_seq_length),
        )
        if score_key in row:
            raise RuntimeError(f"Row {row_index} already contains score key {score_key!r}.")
        output_rows.append({**row, score_key: scores})
        if int(args.log_every) > 0 and row_index % int(args.log_every) == 0:
            print(f"[candidate-score] rows={row_index}/{len(rows)}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in output_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {
        "model": str(args.model),
        "device": device,
        "dtype": str(args.dtype),
        "rows": len(output_rows),
        "candidates": sum(len(row["candidates"]) for row in output_rows),
        "input": {"path": _project_path(input_path), "sha256": _sha256_path(input_path)},
        "output": {"path": _project_path(out_path), "sha256": _sha256_path(out_path)},
        "scoring": "student_conditional_logprob_candidate_tokens",
        "score_key": score_key,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[candidate-score] out={out_path}")
    print(f"[candidate-score] summary={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
