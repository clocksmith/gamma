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
import unicodedata
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _tokenize_words(text: str) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    for ch in str(text):
        cat = unicodedata.category(ch)
        is_letter_or_digit = cat.startswith("L") or cat.startswith("N") or ch.isalpha() or ch.isdigit()
        is_mark = cat in ("Mn", "Mc", "Me")
        if is_letter_or_digit or (is_mark and buf):
            buf.append(ch)
            continue
        if buf:
            w = "".join(buf).casefold().strip()
            if len(w) >= 2:
                out.append(w)
            buf = []
    if buf:
        w = "".join(buf).casefold().strip()
        if len(w) >= 2:
            out.append(w)
    return out


def _choose_hard_negative(
    *,
    query: str,
    pos_docs: set[int],
    docs: list[str],
    doc_word_sets: list[set[str]],
    inv: dict[str, list[int]],
    rnd: random.Random,
    pool: int,
) -> int:
    if not docs:
        return 0
    q_words = set(_tokenize_words(query))
    if not q_words:
        # Fall back to random.
        while True:
            neg = rnd.randrange(len(docs))
            if neg not in pos_docs:
                return neg

    cand: set[int] = set()
    for w in q_words:
        ids = inv.get(w)
        if not ids:
            continue
        cand.update(ids)
    cand.difference_update(pos_docs)

    if not cand:
        while True:
            neg = rnd.randrange(len(docs))
            if neg not in pos_docs:
                return neg

    cand_list = list(cand)
    rnd.shuffle(cand_list)
    if pool > 0:
        cand_list = cand_list[: max(1, int(pool))]

    best = cand_list[0]
    best_score = -1
    for di in cand_list:
        overlap = len(q_words.intersection(doc_word_sets[di]))
        if overlap > best_score:
            best_score = overlap
            best = di
    return int(best)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets-dir", default="gamma/projects/embeddinggemma_subsets/datasets_hard_v3")
    ap.add_argument("--langs", default="en,es,zh,ja,ar,fr,pt,hi")
    ap.add_argument("--pairs-per-lang", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--neg-strategy",
        choices=["random", "lexical_hard"],
        default="lexical_hard",
        help="Negative sampling strategy. lexical_hard picks lexical-overlap distractors.",
    )
    ap.add_argument(
        "--hard-neg-pool",
        type=int,
        default=128,
        help="Candidate pool size for lexical_hard negatives (0 = use all candidates).",
    )
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

        doc_word_sets: list[set[str]] = []
        inv: dict[str, list[int]] = {}
        if str(args.neg_strategy) == "lexical_hard":
            for di, d in enumerate(docs):
                ws = set(_tokenize_words(str(d)))
                doc_word_sets.append(ws)
                for w in ws:
                    inv.setdefault(w, []).append(int(di))

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
            if str(args.neg_strategy) == "lexical_hard":
                neg = _choose_hard_negative(
                    query=str(queries[qi]),
                    pos_docs=set(int(x) for x in pos_docs),
                    docs=docs,
                    doc_word_sets=doc_word_sets,
                    inv=inv,
                    rnd=rnd,
                    pool=int(args.hard_neg_pool),
                )
            else:
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
        print(f"{lang}: {n} pairs neg_strategy={args.neg_strategy}")

    _write_jsonl(Path(args.out), rows)
    print(f"wrote {len(rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
