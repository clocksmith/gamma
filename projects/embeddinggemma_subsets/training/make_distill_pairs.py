#!/usr/bin/env python3
"""
Build distillation pairs from per-language retrieval datasets.

Output format (JSONL):
{"lang":"en","query":"...","pos":"...","neg":"..."}
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets-dir", default="gamma/projects/embeddinggemma_subsets/datasets_hard_v3")
    ap.add_argument("--langs", default="en,es,zh,ja,ar,fr,pt,hi")
    ap.add_argument("--pairs-per-lang", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="gamma/projects/embeddinggemma_subsets/training_data/distill_pairs.jsonl")
    args = ap.parse_args()

    rnd = random.Random(int(args.seed))
    langs = [x.strip() for x in str(args.langs).split(",") if x.strip()]
    rows: list[dict[str, str]] = []
    for lang in langs:
        ds_path = Path(args.datasets_dir) / lang / "dataset.json"
        if not ds_path.exists():
            print(f"skip {lang}: missing {ds_path}")
            continue
        ds = _load_json(ds_path)
        queries = ds.get("queries", [])
        docs = ds.get("docs", [])
        rel = ds.get("relevant", [])
        if not isinstance(queries, list) or not isinstance(docs, list) or not isinstance(rel, list):
            continue
        rel_map: dict[int, list[int]] = {}
        for qi, di in rel:
            rel_map.setdefault(int(qi), []).append(int(di))
        qids = list(rel_map.keys())
        rnd.shuffle(qids)

        n = 0
        while n < int(args.pairs_per_lang) and qids:
            qi = qids[n % len(qids)]
            pos_docs = rel_map.get(qi, [])
            if not pos_docs:
                n += 1
                continue
            pos = int(pos_docs[0])
            neg = rnd.randrange(len(docs))
            tries = 0
            while neg in pos_docs and tries < 20:
                neg = rnd.randrange(len(docs))
                tries += 1
            rows.append(
                {
                    "lang": lang,
                    "query": str(queries[qi]),
                    "pos": str(docs[pos]),
                    "neg": str(docs[neg]),
                }
            )
            n += 1
        print(f"{lang}: {n} pairs")

    _write_jsonl(Path(args.out), rows)
    print(f"wrote {len(rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
