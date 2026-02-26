#!/usr/bin/env python3
"""
Run MTEB with a pruned-vocab subset/distilled checkpoint using id_remap.json.

Why this exists:
- Subset/distilled checkpoints use reduced vocab rows.
- Base tokenizer ids must be remapped (old_id -> new_id) before model forward.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from mteb import MTEB
from transformers import AutoModel, AutoTokenizer


def _set_offline_env() -> None:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean_pool(last_hidden, attention_mask):
    mask = attention_mask.unsqueeze(-1).to(dtype=last_hidden.dtype)
    summed = (last_hidden * mask).sum(dim=1)
    denom = mask.sum(dim=1).clamp_min(1.0)
    return summed / denom


class RemapHFEmbedder:
    def __init__(
        self,
        *,
        base_tokenizer: str,
        subset_dir: str,
        device: str,
        max_length: int,
        default_batch_size: int,
        local_files_only: bool,
    ) -> None:
        self.device = str(device)
        self.max_length = int(max_length)
        self.default_batch_size = max(1, int(default_batch_size))
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(base_tokenizer),
            local_files_only=bool(local_files_only),
            use_fast=True,
        )
        self.model = AutoModel.from_pretrained(
            str(subset_dir),
            local_files_only=bool(local_files_only),
            low_cpu_mem_usage=True,
        ).to(self.device)
        self.model.eval()

        remap_path = Path(subset_dir) / "id_remap.json"
        remap = _load_json(remap_path).get("old_to_new", {})
        if not isinstance(remap, dict) or not remap:
            raise RuntimeError(f"Invalid remap file: {remap_path}")
        self.remap = remap

        unk_old = self.tokenizer.unk_token_id
        if unk_old is None:
            raise RuntimeError("Tokenizer has no unk_token_id.")
        unk_new = self.remap.get(str(int(unk_old)))
        if unk_new is None:
            raise RuntimeError("Remap missing unk mapping.")
        self.unk_new = int(unk_new)
        self.hidden_size = int(getattr(self.model.config, "hidden_size", 0) or 0)

    @staticmethod
    def _normalize_texts(sentences: Any) -> list[str]:
        if isinstance(sentences, str):
            return [sentences]
        out: list[str] = []
        for x in sentences:
            if isinstance(x, dict):
                title = str(x.get("title", "")).strip()
                text = str(x.get("text", "")).strip()
                if title and text:
                    out.append(f"{title}\n{text}")
                elif text:
                    out.append(text)
                else:
                    out.append(title)
            else:
                out.append(str(x))
        return out

    def _embed_batch(self, texts: list[str]) -> np.ndarray:
        enc = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length,
            add_special_tokens=True,
        )
        ids_old = enc["input_ids"].cpu().tolist()
        ids_new = [
            [int(self.remap.get(str(int(tid)), self.unk_new)) for tid in row]
            for row in ids_old
        ]
        input_ids = torch.tensor(ids_new, dtype=torch.long, device=self.device)
        attention_mask = enc.get("attention_mask", torch.ones_like(enc["input_ids"]))
        attention_mask = attention_mask.to(self.device)

        with torch.no_grad():
            out = self.model(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
        pooled = getattr(out, "pooler_output", None)
        if pooled is None:
            pooled = _mean_pool(out.last_hidden_state, attention_mask)
        pooled = F.normalize(pooled.float(), p=2, dim=-1)
        return pooled.cpu().numpy()

    def encode(self, sentences: Any, batch_size: int | None = None, **kwargs) -> np.ndarray:
        del kwargs
        texts = self._normalize_texts(sentences)
        if not texts:
            if self.hidden_size <= 0:
                return np.zeros((0, 0), dtype=np.float32)
            return np.zeros((0, self.hidden_size), dtype=np.float32)

        bsz = max(1, int(batch_size) if batch_size is not None else self.default_batch_size)
        chunks = []
        for i in range(0, len(texts), bsz):
            chunks.append(self._embed_batch(texts[i : i + bsz]))
        return np.concatenate(chunks, axis=0)

    def encode_queries(self, queries: Any, **kwargs) -> np.ndarray:
        return self.encode(queries, **kwargs)

    def encode_corpus(self, corpus: Any, **kwargs) -> np.ndarray:
        return self.encode(corpus, **kwargs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-tokenizer", required=True, help="Base/teacher tokenizer path or HF id.")
    ap.add_argument("--subset-dir", required=True, help="Subset/distilled model dir with id_remap.json.")
    ap.add_argument("--output-folder", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--task-types", default=None, help="Comma list, e.g. Retrieval,STS")
    ap.add_argument("--task-langs", default="eng", help="Comma list, e.g. eng,spa,zho")
    ap.add_argument("--tasks", default=None, help="Explicit task names, overrides --task-types/--task-langs.")
    ap.add_argument("--allow-download", action="store_true")
    args = ap.parse_args()

    if not bool(args.allow_download):
        _set_offline_env()

    embedder = RemapHFEmbedder(
        base_tokenizer=str(args.base_tokenizer),
        subset_dir=str(args.subset_dir),
        device=str(args.device),
        max_length=int(args.max_length),
        default_batch_size=int(args.batch_size),
        local_files_only=not bool(args.allow_download),
    )

    if args.tasks:
        task_names = [x.strip() for x in str(args.tasks).split(",") if x.strip()]
        if not task_names:
            raise RuntimeError("Empty --tasks after parsing.")
        eval_obj = MTEB(tasks=task_names)
    else:
        task_types = None
        if args.task_types:
            task_types = [x.strip() for x in str(args.task_types).split(",") if x.strip()]
        task_langs = [x.strip() for x in str(args.task_langs).split(",") if x.strip()]
        eval_obj = MTEB(task_types=task_types, task_langs=task_langs)

    out = Path(args.output_folder)
    out.mkdir(parents=True, exist_ok=True)
    eval_obj.run(embedder, output_folder=str(out))
    print(f"[run_mteb_remap] wrote results -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
