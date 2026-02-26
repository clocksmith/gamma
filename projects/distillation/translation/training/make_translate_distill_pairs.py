#!/usr/bin/env python3
"""
Build translation distillation triplets from multilingual bitext inputs.

Output format (JSONL):
{
  "src_lang": "fr",
  "tgt_lang": "en",
  "pair": "fr-en",
  "source": "...",
  "target_pos": "...",
  "target_neg": "...",
  "lang": "en",
  "query": "...",
  "pos": "...",
  "neg": "..."
}

`query/pos/neg/lang` are compatibility fields so existing embedding distillation
tools can consume the file without extra conversion.
"""

from __future__ import annotations

import argparse
import json
import random
import unicodedata
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PairRow:
    src_lang: str
    tgt_lang: str
    source: str
    target: str


def _safe_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _norm_text(s: str) -> str:
    return " ".join(str(s).split()).strip().casefold()


def _parse_csv_set(s: str) -> set[str]:
    return {x.strip() for x in str(s).split(",") if x.strip()}


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


def _iter_jsonl(path: Path, *, max_rows: int | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if max_rows is not None and len(rows) >= max_rows:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def _extract_from_translation_map(
    translation: dict[str, Any],
    *,
    source_langs: set[str],
    target_langs: set[str],
) -> list[PairRow]:
    clean: dict[str, str] = {}
    for k, v in translation.items():
        lang = _safe_text(k)
        txt = _safe_text(v)
        if lang and txt:
            clean[lang] = txt
    if not clean:
        return []

    all_langs = sorted(clean.keys())
    src_candidates = [l for l in all_langs if not source_langs or l in source_langs]
    tgt_candidates = [l for l in all_langs if not target_langs or l in target_langs]

    out: list[PairRow] = []
    for tgt in tgt_candidates:
        ttxt = clean.get(tgt, "")
        if not ttxt:
            continue
        for src in src_candidates:
            if src == tgt:
                continue
            stxt = clean.get(src, "")
            if not stxt:
                continue
            out.append(PairRow(src_lang=src, tgt_lang=tgt, source=stxt, target=ttxt))
    return out


def _extract_from_explicit_fields(
    obj: dict[str, Any],
    *,
    source_key: str,
    target_key: str,
    src_lang_key: str,
    tgt_lang_key: str,
    default_src_lang: str | None,
    default_tgt_lang: str | None,
) -> PairRow | None:
    src_lang = _safe_text(obj.get(src_lang_key, "")) or _safe_text(default_src_lang)
    tgt_lang = _safe_text(obj.get(tgt_lang_key, "")) or _safe_text(default_tgt_lang)
    source = _safe_text(obj.get(source_key, ""))
    target = _safe_text(obj.get(target_key, ""))
    if not src_lang or not tgt_lang or not source or not target:
        return None
    return PairRow(src_lang=src_lang, tgt_lang=tgt_lang, source=source, target=target)


def _load_parallel_text_pairs(
    *,
    src_lang: str,
    tgt_lang: str,
    src_path: Path,
    tgt_path: Path,
    max_rows: int | None,
) -> list[PairRow]:
    rows: list[PairRow] = []
    with src_path.open("r", encoding="utf-8", errors="replace") as fs:
        with tgt_path.open("r", encoding="utf-8", errors="replace") as ft:
            for line_no, pair in enumerate(zip_longest(fs, ft, fillvalue=None), start=1):
                if max_rows is not None and len(rows) >= max_rows:
                    break
                src_line, tgt_line = pair
                if src_line is None or tgt_line is None:
                    raise RuntimeError(
                        f"Line mismatch between {src_path} and {tgt_path} at line {line_no}. "
                        "Files must be line-aligned."
                    )
                source = _safe_text(src_line)
                target = _safe_text(tgt_line)
                if not source or not target:
                    continue
                rows.append(
                    PairRow(
                        src_lang=str(src_lang).strip(),
                        tgt_lang=str(tgt_lang).strip(),
                        source=source,
                        target=target,
                    )
                )
    return rows


def _choose_hard_negative(
    *,
    pos_text: str,
    pos_norm: str,
    docs: list[str],
    doc_norms: list[str],
    doc_word_sets: list[set[str]],
    inv: dict[str, list[int]],
    rnd: random.Random,
    pool: int,
) -> int | None:
    if len(docs) <= 1:
        return None
    excluded = {i for i, n in enumerate(doc_norms) if n == pos_norm}
    if len(excluded) >= len(docs):
        return None

    q_words = set(_tokenize_words(pos_text))
    if not q_words:
        while True:
            neg = rnd.randrange(len(docs))
            if neg not in excluded:
                return neg

    cand: set[int] = set()
    for w in q_words:
        ids = inv.get(w)
        if ids:
            cand.update(ids)
    cand.difference_update(excluded)

    if not cand:
        while True:
            neg = rnd.randrange(len(docs))
            if neg not in excluded:
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


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _tag_text(lang: str, text: str, *, use_tags: bool) -> str:
    if not use_tags:
        return text
    return f"[{lang}] {text}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--jsonl",
        action="append",
        default=[],
        help="Input JSONL file(s). Supports explicit source/target fields or a `translation` language map.",
    )
    ap.add_argument(
        "--pair-file",
        nargs=4,
        action="append",
        metavar=("SRC_LANG", "TGT_LANG", "SRC_TEXT", "TGT_TEXT"),
        default=[],
        help="Line-aligned text files: source and target lines must match by line number. Repeatable.",
    )
    ap.add_argument("--jsonl-source-key", default="source", help="Explicit-source mode: source text field.")
    ap.add_argument("--jsonl-target-key", default="target", help="Explicit-source mode: target text field.")
    ap.add_argument("--jsonl-src-lang-key", default="src_lang", help="Explicit-source mode: source language field.")
    ap.add_argument("--jsonl-tgt-lang-key", default="tgt_lang", help="Explicit-source mode: target language field.")
    ap.add_argument(
        "--jsonl-translation-key",
        default="translation",
        help="Translation-map mode: dict field mapping lang -> text.",
    )
    ap.add_argument("--default-src-lang", default=None, help="Fallback source language for explicit JSONL rows.")
    ap.add_argument("--default-tgt-lang", default=None, help="Fallback target language for explicit JSONL rows.")
    ap.add_argument("--source-langs", default="", help="Optional comma-separated source language allowlist.")
    ap.add_argument("--target-langs", default="", help="Optional comma-separated target language allowlist.")
    ap.add_argument("--min-chars", type=int, default=8)
    ap.add_argument("--max-rows-per-input", type=int, default=0, help="0 means no per-input row cap.")
    ap.add_argument("--pairs-per-pair", type=int, default=20000, help="Max output rows per src-tgt pair. 0 means no cap.")
    ap.add_argument("--neg-strategy", choices=["random", "lexical_hard"], default="lexical_hard")
    ap.add_argument(
        "--hard-neg-pool",
        type=int,
        default=128,
        help="Candidate pool size for lexical_hard negatives (0 = all candidates).",
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--add-lang-tags",
        action="store_true",
        help="Prefix query/pos/neg compatibility fields with [lang] tags.",
    )
    ap.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parents[1] / "training_data" / "translate_distill_pairs.jsonl"),
    )
    ap.add_argument(
        "--summary-out",
        default="",
        help="Optional JSON summary output path.",
    )
    args = ap.parse_args()

    if not args.jsonl and not args.pair_file:
        raise SystemExit("Provide at least one input via --jsonl or --pair-file.")

    rnd = random.Random(int(args.seed))
    source_langs = _parse_csv_set(str(args.source_langs))
    target_langs = _parse_csv_set(str(args.target_langs))
    max_rows = int(args.max_rows_per_input)
    max_rows = max_rows if max_rows > 0 else None

    loaded: list[PairRow] = []
    stats = {
        "loaded_raw": 0,
        "skipped_short": 0,
        "skipped_lang_filter": 0,
        "dedup_dropped": 0,
        "skipped_no_negative": 0,
    }

    for spec in list(args.pair_file):
        src_lang, tgt_lang, src_text_path, tgt_text_path = spec
        rows = _load_parallel_text_pairs(
            src_lang=str(src_lang),
            tgt_lang=str(tgt_lang),
            src_path=Path(src_text_path),
            tgt_path=Path(tgt_text_path),
            max_rows=max_rows,
        )
        loaded.extend(rows)

    for path_s in list(args.jsonl):
        path = Path(path_s)
        for obj in _iter_jsonl(path, max_rows=max_rows):
            translation = obj.get(str(args.jsonl_translation_key))
            if isinstance(translation, dict):
                loaded.extend(
                    _extract_from_translation_map(
                        translation,
                        source_langs=source_langs,
                        target_langs=target_langs,
                    )
                )
                continue

            row = _extract_from_explicit_fields(
                obj,
                source_key=str(args.jsonl_source_key),
                target_key=str(args.jsonl_target_key),
                src_lang_key=str(args.jsonl_src_lang_key),
                tgt_lang_key=str(args.jsonl_tgt_lang_key),
                default_src_lang=args.default_src_lang,
                default_tgt_lang=args.default_tgt_lang,
            )
            if row is not None:
                loaded.append(row)

    stats["loaded_raw"] = len(loaded)

    filtered: list[PairRow] = []
    seen: set[tuple[str, str, str, str]] = set()
    for r in loaded:
        if source_langs and r.src_lang not in source_langs:
            stats["skipped_lang_filter"] += 1
            continue
        if target_langs and r.tgt_lang not in target_langs:
            stats["skipped_lang_filter"] += 1
            continue
        if len(r.source) < int(args.min_chars) or len(r.target) < int(args.min_chars):
            stats["skipped_short"] += 1
            continue
        key = (r.src_lang, r.tgt_lang, _norm_text(r.source), _norm_text(r.target))
        if key in seen:
            stats["dedup_dropped"] += 1
            continue
        seen.add(key)
        filtered.append(r)

    if not filtered:
        raise SystemExit("No usable rows after filtering.")

    by_pair: dict[str, list[PairRow]] = {}
    for r in filtered:
        pair = f"{r.src_lang}-{r.tgt_lang}"
        by_pair.setdefault(pair, []).append(r)

    selected: list[PairRow] = []
    per_pair_kept: dict[str, int] = {}
    pair_limit = int(args.pairs_per_pair)
    for pair, rows in by_pair.items():
        rows2 = list(rows)
        rnd.shuffle(rows2)
        if pair_limit > 0:
            rows2 = rows2[:pair_limit]
        selected.extend(rows2)
        per_pair_kept[pair] = len(rows2)

    if not selected:
        raise SystemExit("No rows selected after per-pair capping.")

    target_docs: dict[str, list[str]] = {}
    target_doc_norms: dict[str, list[str]] = {}
    target_doc_word_sets: dict[str, list[set[str]]] = {}
    target_inv: dict[str, dict[str, list[int]]] = {}
    target_norm_to_index: dict[str, dict[str, int]] = {}

    for r in selected:
        lang = r.tgt_lang
        target_docs.setdefault(lang, [])
        target_doc_norms.setdefault(lang, [])
        target_doc_word_sets.setdefault(lang, [])
        target_inv.setdefault(lang, {})
        target_norm_to_index.setdefault(lang, {})

        n = _norm_text(r.target)
        if n in target_norm_to_index[lang]:
            continue
        idx = len(target_docs[lang])
        target_norm_to_index[lang][n] = idx
        target_docs[lang].append(r.target)
        target_doc_norms[lang].append(n)
        ws = set(_tokenize_words(r.target))
        target_doc_word_sets[lang].append(ws)
        for w in ws:
            target_inv[lang].setdefault(w, []).append(idx)

    out_rows: list[dict[str, Any]] = []
    for r in selected:
        lang = r.tgt_lang
        docs = target_docs.get(lang, [])
        doc_norms = target_doc_norms.get(lang, [])
        if len(docs) <= 1:
            stats["skipped_no_negative"] += 1
            continue

        pos_norm = _norm_text(r.target)
        if str(args.neg_strategy) == "lexical_hard":
            neg_idx = _choose_hard_negative(
                pos_text=r.target,
                pos_norm=pos_norm,
                docs=docs,
                doc_norms=doc_norms,
                doc_word_sets=target_doc_word_sets[lang],
                inv=target_inv[lang],
                rnd=rnd,
                pool=int(args.hard_neg_pool),
            )
        else:
            excluded = {i for i, n in enumerate(doc_norms) if n == pos_norm}
            if len(excluded) >= len(docs):
                neg_idx = None
            else:
                while True:
                    cand = rnd.randrange(len(docs))
                    if cand not in excluded:
                        neg_idx = int(cand)
                        break

        if neg_idx is None:
            stats["skipped_no_negative"] += 1
            continue

        neg_text = docs[int(neg_idx)]
        row = {
            "src_lang": r.src_lang,
            "tgt_lang": r.tgt_lang,
            "pair": f"{r.src_lang}-{r.tgt_lang}",
            "source": r.source,
            "target_pos": r.target,
            "target_neg": neg_text,
            # Compatibility aliases for existing distill consumers.
            "lang": r.tgt_lang,
            "query": _tag_text(r.src_lang, r.source, use_tags=bool(args.add_lang_tags)),
            "pos": _tag_text(r.tgt_lang, r.target, use_tags=bool(args.add_lang_tags)),
            "neg": _tag_text(r.tgt_lang, neg_text, use_tags=bool(args.add_lang_tags)),
        }
        out_rows.append(row)

    if not out_rows:
        raise SystemExit("No output rows were produced (check inputs / filters / negatives).")

    _write_jsonl(Path(args.out), out_rows)

    per_target_lang: dict[str, int] = {}
    for row in out_rows:
        lang = str(row["tgt_lang"])
        per_target_lang[lang] = per_target_lang.get(lang, 0) + 1

    summary = {
        "inputs": {
            "jsonl": list(args.jsonl),
            "pair_file_count": len(args.pair_file),
            "source_langs": sorted(source_langs),
            "target_langs": sorted(target_langs),
        },
        "params": {
            "min_chars": int(args.min_chars),
            "max_rows_per_input": int(max_rows) if max_rows is not None else 0,
            "pairs_per_pair": int(args.pairs_per_pair),
            "neg_strategy": str(args.neg_strategy),
            "hard_neg_pool": int(args.hard_neg_pool),
            "seed": int(args.seed),
            "add_lang_tags": bool(args.add_lang_tags),
        },
        "stats": stats,
        "kept_pairs": dict(sorted(per_pair_kept.items())),
        "kept_target_langs": dict(sorted(per_target_lang.items())),
        "output_rows": len(out_rows),
        "output_path": str(args.out),
    }
    if str(args.summary_out).strip():
        outp = Path(str(args.summary_out).strip())
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"loaded_raw={stats['loaded_raw']} filtered={len(filtered)} "
        f"output_rows={len(out_rows)} neg_strategy={args.neg_strategy}"
    )
    print(f"wrote {len(out_rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
