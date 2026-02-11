#!/usr/bin/env python3
"""
Build a language corpus and a simple retrieval eval set from Wikipedia text.

This is meant to be the data source for:
- vocab keep-list generation (token frequency)
- sanity evals that are large enough to be meaningful

Input options:
1) Wikiextractor output directory (offline):
   - Download Wikimedia dump for a language (e.g. enwiki-latest-pages-articles.xml.bz2)
   - Run wikiextractor to produce text files containing <doc> blocks
   - Point --wikiextractor-dir at the extracted directory

2) JSONL file with {"text": "..."} per line (exported from HF datasets or elsewhere):
   - Point --jsonl at that file

Outputs:
- --out-corpus: plain text file (one line per paragraph)
- --out-dataset: dataset.json with {"queries","docs","relevant"}
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Iterable


_DOC_OPEN_RE = re.compile(r"^<doc\\b")
_DOC_CLOSE_RE = re.compile(r"^</doc>")


def _iter_wikiextractor_paragraphs(root: Path) -> Iterable[str]:
    # Wikiextractor writes many small text files under nested dirs.
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        # Common pattern: AA/wiki_00
        if path.name.startswith("."):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        in_doc = False
        buf: list[str] = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                if in_doc and buf:
                    para = " ".join(buf).strip()
                    if para:
                        yield para
                    buf = []
                continue

            if _DOC_OPEN_RE.match(line):
                in_doc = True
                buf = []
                continue
            if _DOC_CLOSE_RE.match(line):
                in_doc = False
                if buf:
                    para = " ".join(buf).strip()
                    if para:
                        yield para
                buf = []
                continue

            if not in_doc:
                continue

            # Skip markup-ish lines that sometimes appear.
            if line.startswith("[[") and line.endswith("]]"):
                continue

            buf.append(line)

        if in_doc and buf:
            para = " ".join(buf).strip()
            if para:
                yield para


def _iter_jsonl_texts(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            text = obj.get("text")
            if isinstance(text, str):
                t = text.strip()
                if t:
                    yield t


def _write_lines(path: Path, lines: Iterable[str], *, limit: int | None) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for s in lines:
            f.write(s.replace("\n", " ").strip() + "\n")
            n += 1
            if limit is not None and n >= limit:
                break
    return n


def _split_sentences(text: str) -> list[str]:
    # Heuristic, language-agnostic-ish. Good enough for eval bootstrapping.
    parts = re.split(r"(?<=[\\.!?。！？])\\s+", text.strip())
    out = []
    for p in parts:
        p = p.strip()
        if len(p) < 8:
            continue
        out.append(p)
    return out


def _build_retrieval_dataset(paragraphs: list[str], *, seed: int, max_docs: int, max_queries: int) -> dict:
    rnd = random.Random(seed)
    paras = [p for p in paragraphs if len(p) >= 64]
    rnd.shuffle(paras)

    docs: list[str] = []
    queries: list[str] = []
    relevant: list[list[int]] = []

    for p in paras:
        if len(docs) >= max_docs:
            break

        sents = _split_sentences(p)
        if not sents:
            continue

        # Pick a sentence that is likely to be informative, not the whole paragraph.
        sent = sents[0]
        if len(sent) > 220:
            sent = sent[:220].rstrip()

        di = len(docs)
        docs.append(p)

        if len(queries) < max_queries:
            qi = len(queries)
            queries.append(sent)
            relevant.append([qi, di])

    return {"queries": queries, "docs": docs, "relevant": relevant}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, help="Language tag (e.g., en, es, ja, ar).")
    ap.add_argument("--wikiextractor-dir", default=None, help="Root dir of wikiextractor output.")
    ap.add_argument("--jsonl", default=None, help="JSONL input with {'text': ...} per line.")
    ap.add_argument("--out-corpus", required=True, help="Output corpus text file.")
    ap.add_argument("--out-dataset", required=True, help="Output dataset.json file.")
    ap.add_argument("--max-paragraphs", type=int, default=200000, help="Max paragraphs to write into corpus.")
    ap.add_argument("--max-docs", type=int, default=5000, help="Max docs in retrieval dataset.")
    ap.add_argument("--max-queries", type=int, default=5000, help="Max queries in retrieval dataset.")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    if bool(args.wikiextractor_dir) == bool(args.jsonl):
        raise SystemExit("Provide exactly one of --wikiextractor-dir or --jsonl")

    if args.wikiextractor_dir:
        paragraphs_iter = _iter_wikiextractor_paragraphs(Path(args.wikiextractor_dir))
    else:
        paragraphs_iter = _iter_jsonl_texts(Path(args.jsonl))

    # Materialize a bounded list so we can sample for dataset generation.
    paragraphs: list[str] = []
    for p in paragraphs_iter:
        paragraphs.append(p)
        if len(paragraphs) >= int(args.max_paragraphs):
            break

    out_corpus = Path(args.out_corpus)
    n_written = _write_lines(out_corpus, paragraphs, limit=int(args.max_paragraphs))

    ds = _build_retrieval_dataset(
        paragraphs,
        seed=int(args.seed),
        max_docs=int(args.max_docs),
        max_queries=int(args.max_queries),
    )
    out_dataset = Path(args.out_dataset)
    out_dataset.parent.mkdir(parents=True, exist_ok=True)
    out_dataset.write_text(json.dumps(ds, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"lang={args.lang} paragraphs={len(paragraphs)} corpus_written={n_written}")
    print(f"dataset docs={len(ds['docs'])} queries={len(ds['queries'])} pairs={len(ds['relevant'])}")
    print(f"wrote corpus: {out_corpus}")
    print(f"wrote dataset: {out_dataset}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

