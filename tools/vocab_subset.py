#!/usr/bin/env python3
"""
Vocabulary subsetting for large-vocab HF models (e.g., Gemma 3 family).

This tool:
1) Scans one or more text files and counts tokenizer token-id frequency.
2) Writes a "keep list" of token IDs (special tokens + top-K most frequent).
3) Optionally writes a pruned safetensors checkpoint that keeps only those rows
   in the input embedding (and output embedding / lm_head when present).

Important:
- The pruned checkpoint is NOT directly compatible with the original tokenizer,
  because the tokenizer will still emit original IDs (up to the original vocab).
  Use the emitted id remap (old_id -> new_id) to remap input_ids at runtime,
  mapping unknown/removed IDs to unk (or another fallback) before feeding the model.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


def _iter_lines(paths: list[Path], max_lines: int | None) -> Iterable[str]:
    seen = 0
    for p in paths:
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                yield line
                seen += 1
                if max_lines is not None and seen >= max_lines:
                    return


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _human(n: int) -> str:
    if n < 1024:
        return str(n)
    units = ["Ki", "Mi", "Gi", "Ti"]
    v = float(n)
    u = ""
    for u in units:
        v /= 1024.0
        if v < 1024.0:
            break
    return f"{v:.2f}{u}"


@dataclass(frozen=True)
class KeepSpec:
    keep_ids: list[int]
    old_to_new: dict[int, int]
    new_to_old: list[int]


def _resolve_sentencepiece_model_path(model_ref: str, *, local_files_only: bool) -> Path | None:
    # 1) Local directory or file path.
    p = Path(model_ref)
    if p.exists():
        if p.is_file() and p.name.endswith(".model"):
            return p
        if p.is_dir():
            cand = p / "tokenizer.model"
            if cand.exists():
                return cand
        return None

    # 2) HF cache (offline). Avoid any network calls.
    try:
        from transformers.utils.hub import cached_file

        path = cached_file(model_ref, "tokenizer.model", local_files_only=local_files_only)
        if path:
            return Path(path)
    except Exception:
        return None
    return None


def _fill_keep_ids_to_top_k(
    keep_ids: list[int],
    *,
    model_ref: str,
    top_k: int,
    vocab_limit: int | None,
    local_files_only: bool,
    strategy: str,
) -> tuple[list[int], dict[str, int]]:
    """
    If corpus coverage is small (unique tokens < top_k), fill to reach `top_k` in a stable way.

    For SentencePiece tokenizers, `spm_score` fills by piece score (most probable pieces).
    This avoids the current "tiny vocab" failure mode when your corpus is small.
    """
    out_meta: dict[str, int] = {"fill_added": 0, "fill_candidates": 0}
    if len(keep_ids) >= top_k:
        return keep_ids, out_meta

    keep_set = set(keep_ids)
    need = top_k - len(keep_ids)

    if strategy == "spm_score":
        spm_path = _resolve_sentencepiece_model_path(model_ref, local_files_only=local_files_only)
        if spm_path is not None and spm_path.exists():
            import sentencepiece as spm

            sp = spm.SentencePieceProcessor()
            sp.load(str(spm_path))
            size = int(sp.get_piece_size())
            ids = list(range(size))
            ids.sort(key=lambda i: float(sp.get_score(i)), reverse=True)

            out_meta["fill_candidates"] = size
            for tid in ids:
                if vocab_limit is not None and not (0 <= tid < vocab_limit):
                    continue
                if tid in keep_set:
                    continue
                keep_ids.append(int(tid))
                keep_set.add(int(tid))
                out_meta["fill_added"] += 1
                if out_meta["fill_added"] >= need:
                    break
            return keep_ids, out_meta

        # Fallback: try id-fill if tokenizer.model isn't available.
        strategy = "id"

    if strategy == "id":
        if vocab_limit is None:
            return keep_ids, out_meta
        out_meta["fill_candidates"] = int(vocab_limit)
        for tid in range(int(vocab_limit)):
            if tid in keep_set:
                continue
            keep_ids.append(int(tid))
            keep_set.add(int(tid))
            out_meta["fill_added"] += 1
            if out_meta["fill_added"] >= need:
                break
        return keep_ids, out_meta

    raise ValueError(f"Unknown fill strategy: {strategy}")


def _compute_keep_ids(
    token_counts: Counter[int],
    *,
    special_ids: list[int],
    top_k: int,
    min_count: int,
    order: str,
) -> KeepSpec:
    specials = []
    seen = set()
    for tid in special_ids:
        if tid is None:
            continue
        if tid in seen:
            continue
        specials.append(int(tid))
        seen.add(int(tid))

    # Exclude specials from the frequency selection so specials don't "waste" slots.
    items = [(tid, cnt) for tid, cnt in token_counts.items() if tid not in seen and cnt >= min_count]
    if order == "frequency":
        # Sort by count desc, then token id asc for stability.
        items.sort(key=lambda x: (-x[1], x[0]))
    elif order == "id":
        items.sort(key=lambda x: x[0])
    else:
        raise ValueError(f"Unknown --order: {order}")

    kept = specials + [tid for tid, _ in items[: max(0, top_k - len(specials))]]
    # Ensure unique + deterministic.
    uniq = []
    seen = set()
    for tid in kept:
        if tid in seen:
            continue
        uniq.append(int(tid))
        seen.add(int(tid))

    old_to_new = {old: new for new, old in enumerate(uniq)}
    new_to_old = list(uniq)
    return KeepSpec(keep_ids=uniq, old_to_new=old_to_new, new_to_old=new_to_old)


def _set_vocab_size(config: Any, new_vocab: int) -> None:
    # Common configs (incl. Gemma 3) expose vocab_size; some have nested text_config.
    if hasattr(config, "vocab_size"):
        setattr(config, "vocab_size", int(new_vocab))
    if hasattr(config, "text_config") and getattr(config, "text_config") is not None:
        tc = getattr(config, "text_config")
        if hasattr(tc, "vocab_size"):
            setattr(tc, "vocab_size", int(new_vocab))


def _select_rows(weight, keep_ids: list[int]):
    # weight: torch.Tensor
    import torch

    idx = torch.tensor(keep_ids, dtype=torch.long, device=weight.device)
    return torch.index_select(weight, 0, idx)


def _select_cols(weight, keep_ids: list[int]):
    # weight: torch.Tensor
    import torch

    idx = torch.tensor(keep_ids, dtype=torch.long, device=weight.device)
    return torch.index_select(weight, 1, idx)


def _prune_model_weights(
    model,
    keep_ids: list[int],
    *,
    also_prune_output: bool,
) -> dict[str, Any]:
    """
    Mutates `model` in-place to have a smaller vocab-dependent weight set.

    Returns a small dict of info for reporting.
    """
    import torch
    import torch.nn as nn

    info: dict[str, Any] = {}

    inp = model.get_input_embeddings()
    if inp is None or not hasattr(inp, "weight"):
        raise RuntimeError("Model has no input embeddings (get_input_embeddings() returned None).")

    in_w = inp.weight.data
    if in_w.ndim != 2:
        raise RuntimeError(f"Unexpected input embedding weight rank: {in_w.ndim} (expected 2).")
    old_vocab, hidden = in_w.shape
    info["input_embedding_shape_before"] = [int(old_vocab), int(hidden)]

    new_w = _select_rows(in_w, keep_ids).contiguous()
    new_vocab = new_w.shape[0]

    # Preserve padding_idx where possible, but note: after pruning it may no longer
    # match the original meaning. We keep it only if it is still in-vocab.
    padding_idx = getattr(inp, "padding_idx", None)
    if isinstance(padding_idx, int) and (padding_idx < 0 or padding_idx >= new_vocab):
        padding_idx = None

    new_inp = nn.Embedding(new_vocab, hidden, padding_idx=padding_idx, device=in_w.device, dtype=in_w.dtype)
    with torch.no_grad():
        new_inp.weight.copy_(new_w)
    model.set_input_embeddings(new_inp)
    info["input_embedding_shape_after"] = [int(new_vocab), int(hidden)]

    # Output embeddings / lm_head (if any).
    if also_prune_output:
        out = None
        try:
            out = model.get_output_embeddings()
        except Exception:
            out = None

        if out is not None and hasattr(out, "weight") and out.weight is not None:
            out_w = out.weight.data
            if out_w.ndim == 2:
                # Common case: [vocab, hidden]
                if out_w.shape[0] == old_vocab:
                    out_new_w = _select_rows(out_w, keep_ids).contiguous()
                    new_out = nn.Linear(hidden, new_vocab, bias=getattr(out, "bias", None) is not None, device=out_w.device, dtype=out_w.dtype)
                    # Transformers output embeddings may be Linear or Embedding. Handle both.
                    if isinstance(out, nn.Embedding):
                        new_out = nn.Embedding(new_vocab, hidden, device=out_w.device, dtype=out_w.dtype)
                        with torch.no_grad():
                            new_out.weight.copy_(out_new_w)
                    else:
                        # Linear weight is [out_features, in_features] = [vocab, hidden]
                        with torch.no_grad():
                            new_out.weight.copy_(out_new_w)
                            if getattr(out, "bias", None) is not None and out.bias is not None:
                                # Bias is [vocab]
                                bias_new = torch.index_select(out.bias.data, 0, torch.tensor(keep_ids, device=out.bias.device, dtype=torch.long))
                                new_out.bias.copy_(bias_new)
                    model.set_output_embeddings(new_out)
                    info["output_embedding_pruned"] = True
                # Less common case: [hidden, vocab] (some tied/projection layouts)
                elif out_w.shape[1] == old_vocab:
                    out_new_w = _select_cols(out_w, keep_ids).contiguous()
                    with torch.no_grad():
                        out.weight.copy_(out_new_w)
                    info["output_embedding_pruned"] = True
            else:
                info["output_embedding_pruned"] = False

    # Update config vocab size(s).
    _set_vocab_size(model.config, new_vocab)
    info["vocab_size_after"] = int(new_vocab)
    return info


def main() -> int:
    ap = argparse.ArgumentParser(description="Subset vocab for a HF model using an English corpus.")
    ap.add_argument("--model", required=True, help="HF model id or local path (e.g., google/embeddinggemma-300m)")
    ap.add_argument("--text", required=True, action="append", help="Path to a UTF-8 text file (repeatable).")
    ap.add_argument("--out", required=True, help="Output directory for keep-list / mapping / optional checkpoint.")

    ap.add_argument("--max-lines", type=int, default=None, help="Stop after N lines (across all files).")
    ap.add_argument("--top-k", type=int, default=50000, help="Keep this many tokens total (including specials).")
    ap.add_argument("--min-count", type=int, default=1, help="Only consider tokens with at least this frequency.")
    ap.add_argument("--order", choices=["frequency", "id"], default="frequency", help="Ordering for non-special keep tokens.")
    ap.add_argument(
        "--fill-to-top-k",
        action="store_true",
        help="If corpus doesn't cover enough unique tokens, fill keep-list to reach --top-k (recommended).",
    )
    ap.add_argument(
        "--fill-strategy",
        choices=["spm_score", "id"],
        default="spm_score",
        help="How to fill tokens when corpus coverage < top_k. spm_score requires tokenizer.model.",
    )

    ap.add_argument("--allow-download", action="store_true", help="Allow HF downloads if model/tokenizer not cached.")
    ap.add_argument("--trust-remote-code", action="store_true", help="Pass trust_remote_code=True to from_pretrained.")

    ap.add_argument("--write-checkpoint", action="store_true", help="Write a pruned safetensors checkpoint to --out.")
    ap.add_argument("--also-prune-output", action="store_true", help="Also prune output embeddings / lm_head if present.")
    ap.add_argument("--dtype", choices=["auto", "fp16", "bf16", "fp32"], default="auto", help="Load dtype for model pruning.")

    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Force offline mode unless the caller explicitly allowed downloads.
    # Some hub calls still attempt to hit the network even with local_files_only=True.
    if not args.allow_download:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    text_paths = [Path(p) for p in args.text]
    missing = [str(p) for p in text_paths if not p.exists()]
    if missing:
        raise SystemExit(f"Missing --text file(s): {', '.join(missing)}")

    # Lazy imports so `--help` works without deps.
    from transformers import AutoTokenizer

    local_files_only = not bool(args.allow_download)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        local_files_only=local_files_only,
        trust_remote_code=bool(args.trust_remote_code),
        use_fast=True,
    )

    # Collect special ids in a stable-ish order, starting with common ones.
    special_ids: list[int] = []
    vocab_limit = None
    try:
        vs = getattr(tokenizer, "vocab_size", None)
        if isinstance(vs, int) and vs > 0:
            vocab_limit = int(vs)
    except Exception:
        vocab_limit = None

    for name in ("bos_token_id", "eos_token_id", "pad_token_id", "unk_token_id", "mask_token_id"):
        tid = getattr(tokenizer, name, None)
        if isinstance(tid, int):
            if vocab_limit is None or (0 <= tid < vocab_limit):
                special_ids.append(tid)
    if hasattr(tokenizer, "all_special_ids"):
        for tid in getattr(tokenizer, "all_special_ids"):
            if isinstance(tid, int):
                if vocab_limit is None or (0 <= tid < vocab_limit):
                    special_ids.append(tid)

    counts: Counter[int] = Counter()
    total_tokens = 0
    total_lines = 0

    for line in _iter_lines(text_paths, args.max_lines):
        total_lines += 1
        # Avoid allocating giant sequences if the input has long lines.
        # Tokenizers handle truncation differently across models, so just rely on natural tokenization.
        ids = tokenizer.encode(line, add_special_tokens=False)
        counts.update(ids)
        total_tokens += len(ids)

    keep = _compute_keep_ids(
        counts,
        special_ids=special_ids,
        top_k=int(args.top_k),
        min_count=int(args.min_count),
        order=str(args.order),
    )
    fill_meta = {"fill_added": 0, "fill_candidates": 0}
    if bool(args.fill_to_top_k):
        filled_ids, fill_meta = _fill_keep_ids_to_top_k(
            list(keep.keep_ids),
            model_ref=str(args.model),
            top_k=int(args.top_k),
            vocab_limit=vocab_limit,
            local_files_only=local_files_only,
            strategy=str(args.fill_strategy),
        )
        keep = KeepSpec(
            keep_ids=filled_ids,
            old_to_new={old: new for new, old in enumerate(filled_ids)},
            new_to_old=list(filled_ids),
        )

    # Summary + artifacts.
    stats = {
        "model": args.model,
        "text_files": [str(p) for p in text_paths],
        "lines_scanned": int(total_lines),
        "tokens_scanned": int(total_tokens),
        "unique_token_ids_seen": int(len(counts)),
        "tokenizer_vocab_size": int(getattr(tokenizer, "vocab_size", -1) or -1),
        "special_token_ids": [int(x) for x in special_ids if isinstance(x, int)],
        "kept_token_count": int(len(keep.keep_ids)),
        "kept_token_target": int(args.top_k),
        "fill_to_top_k": bool(args.fill_to_top_k),
        "fill_strategy": str(args.fill_strategy),
        "fill_added": int(fill_meta.get("fill_added", 0)),
        "kept_token_ids_file": "kept_token_ids.json",
        "id_remap_file": "id_remap.json",
    }

    _write_json(out_dir / "stats.json", stats)
    _write_json(out_dir / "kept_token_ids.json", keep.keep_ids)
    _write_json(
        out_dir / "id_remap.json",
        {
            # json keys must be strings; keep both directions for convenience
            "old_to_new": {str(k): int(v) for k, v in keep.old_to_new.items()},
            "new_to_old": [int(x) for x in keep.new_to_old],
        },
    )

    # Keep a compact frequency table for debugging/inspection.
    top_items = counts.most_common(2000)
    _write_json(out_dir / "top_token_ids.json", [{"id": int(t), "count": int(c)} for t, c in top_items])

    print(
        "\n".join(
            [
                f"Scanned: lines={total_lines}, tokens={total_tokens}, unique_ids={len(counts)}",
                f"Keeping: {len(keep.keep_ids)} token ids (top_k={args.top_k}, min_count={args.min_count})",
                f"Wrote: {out_dir / 'kept_token_ids.json'}",
                f"Wrote: {out_dir / 'id_remap.json'}",
                f"Wrote: {out_dir / 'stats.json'}",
            ]
        )
    )

    if args.write_checkpoint:
        from transformers import AutoConfig, AutoModel

        # Dtype controls memory use while pruning. We avoid changing saved dtype; safe_serialization
        # will write whatever tensor dtypes are currently in the model.
        torch_dtype = None
        if args.dtype != "auto":
            import torch

            torch_dtype = {
                "fp16": torch.float16,
                "bf16": torch.bfloat16,
                "fp32": torch.float32,
            }[args.dtype]

        cfg = AutoConfig.from_pretrained(
            args.model,
            local_files_only=local_files_only,
            trust_remote_code=bool(args.trust_remote_code),
        )
        model = AutoModel.from_pretrained(
            args.model,
            config=cfg,
            local_files_only=local_files_only,
            trust_remote_code=bool(args.trust_remote_code),
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
        )

        info = _prune_model_weights(model, keep.keep_ids, also_prune_output=bool(args.also_prune_output))
        _write_json(out_dir / "prune_info.json", info)

        # Avoid saving the original tokenizer here; it's easy to accidentally load it and feed
        # unremapped ids into the pruned model.
        model.save_pretrained(out_dir, safe_serialization=True)

        # Approx disk size estimate from vocab reduction (only embeddings; ignores other weights).
        before = info.get("input_embedding_shape_before")
        after = info.get("input_embedding_shape_after")
        if before and after:
            # bytes per element is unknown here (depends on dtype), so just report element delta.
            before_elems = int(before[0]) * int(before[1])
            after_elems = int(after[0]) * int(after[1])
            delta_elems = before_elems - after_elems
            print(f"Pruned checkpoint written to: {out_dir}")
            print(f"Embedding elements reduced by: {delta_elems} ({_human(delta_elems)} elements)")
        else:
            print(f"Pruned checkpoint written to: {out_dir}")

        readme = out_dir / "README_SUBSET.txt"
        readme.write_text(
            "\n".join(
                [
                    "This directory contains a pruned HF checkpoint with a reduced vocab-dependent embedding table.",
                    "",
                    "Important:",
                    "- The original tokenizer still emits the original token IDs.",
                    "- You MUST remap input_ids using id_remap.json before calling the model, or map unknown IDs to unk.",
                    "",
                    "Files:",
                    "- kept_token_ids.json: original token IDs retained, in new-vocab order",
                    "- id_remap.json: old_to_new and new_to_old mappings",
                    "- stats.json: corpus scan summary",
                    "- prune_info.json: embedding shapes and pruning details",
                    "",
                    "Typical runtime flow:",
                    "1) Load the base tokenizer from the original model id",
                    "2) Tokenize English text (base tokenizer) -> input_ids (original ids)",
                    "3) Remap ids: old_id -> new_id, else fallback to unk_id",
                    "4) Feed remapped input_ids to this pruned model",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
