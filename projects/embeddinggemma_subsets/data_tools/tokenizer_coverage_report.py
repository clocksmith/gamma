#!/usr/bin/env python3
"""
Report tokenizer coverage/statistics for language corpora.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_lines(path: Path, max_lines: int | None) -> list[str]:
    out: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if max_lines is not None and i >= max_lines:
                break
            t = line.strip()
            if t:
                out.append(t)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", required=True, help="Local tokenizer/model path (HF snapshot dir preferred)")
    ap.add_argument("--langs", default="en,es,zh,ja,ar,fr,pt,hi")
    ap.add_argument("--data-dir", default="gamma/projects/embeddinggemma_subsets/data")
    ap.add_argument("--max-lines", type=int, default=100000)
    ap.add_argument("--out", default="gamma/projects/embeddinggemma_subsets/eval_output/tokenizer_coverage.json")
    args = ap.parse_args()

    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(args.tokenizer), local_files_only=True, use_fast=True)
    langs = [x.strip() for x in str(args.langs).split(",") if x.strip()]

    out: dict[str, Any] = {
        "tokenizer": str(args.tokenizer),
        "vocab_size": int(tok.vocab_size),
        "special_tokens": tok.special_tokens_map,
        "langs": {},
    }
    for lang in langs:
        p = Path(args.data_dir) / f"{lang}.txt"
        if not p.exists():
            continue
        lines = _load_lines(p, args.max_lines)
        enc = tok(lines, add_special_tokens=True, truncation=False)
        ids_all = [int(t) for row in enc["input_ids"] for t in row]
        total = len(ids_all)
        cnt = Counter(ids_all)
        unk_id = tok.unk_token_id
        unk_cnt = int(cnt.get(int(unk_id), 0)) if unk_id is not None else 0
        top = cnt.most_common(25)
        top_pieces = []
        for tid, freq in top:
            try:
                piece = tok.convert_ids_to_tokens(int(tid))
            except Exception:
                piece = None
            top_pieces.append({"id": int(tid), "piece": piece, "freq": int(freq)})

        out["langs"][lang] = {
            "lines": len(lines),
            "tokens_total": total,
            "tokens_unique": len(cnt),
            "unk_id": int(unk_id) if unk_id is not None else None,
            "unk_rate": float(unk_cnt / total) if total > 0 else 0.0,
            "top_tokens": top_pieces,
        }

    _write_json(Path(args.out), out)
    print(f"Wrote: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
