#!/usr/bin/env python3
"""Analyze token and phrase coverage gaps between gold-core and extension shard pools."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CORE_DATASETS = [
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.shard_01_gold_core_a.jsonl",
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.shard_02_gold_core_b.jsonl",
]
DEFAULT_EXTENSION_DATASETS = [
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards_draft"
    / "gold_natural_draft.shard_03_draft_full.jsonl",
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards_draft"
    / "gold_natural_draft.shard_04_seed_plus_manual.jsonl",
]
DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "qa"
)

WORD_RE = re.compile(r"[a-zà-öø-ÿ]+(?:'[a-zà-öø-ÿ]+)?", re.IGNORECASE)

STOPWORDS = {
    "en": {
        "a", "an", "and", "are", "as", "at", "be", "before", "but", "by", "can",
        "could", "did", "do", "does", "for", "from", "had", "has", "have", "he",
        "her", "his", "i", "if", "in", "into", "is", "it", "its", "of", "on",
        "or", "our", "she", "so", "that", "the", "their", "them", "they", "this",
        "to", "too", "up", "was", "we", "were", "while", "with", "would", "you",
        "your", "after", "during", "than", "then", "there", "these", "those",
        "through", "very", "more", "most", "much", "just", "now", "only", "over",
        "under", "out", "off", "all", "any", "every", "each", "same", "both",
        "not", "no", "nor", "such", "until", "because", "about", "across", "once",
    },
    "es": {
        "a", "al", "algo", "antes", "aquí", "cada", "como", "con", "contra", "de",
        "del", "desde", "donde", "dos", "el", "ella", "ellas", "ellos", "en", "entre",
        "era", "es", "esa", "ese", "eso", "esta", "estaba", "estar", "este", "esto",
        "fue", "ha", "hay", "la", "las", "le", "les", "lo", "los", "más", "mi", "muy",
        "no", "nos", "o", "para", "pero", "por", "que", "se", "sin", "sobre", "su",
        "sus", "te", "tiene", "todo", "tu", "un", "una", "uno", "unos", "unas", "ya",
        "y", "durante", "mientras", "hasta", "después", "cuando", "porque", "solo",
        "sólo", "también", "además", "mucho", "poco", "casi", "otro", "otra", "otros",
        "otras", "mismo", "misma", "mismos", "mismas",
    },
}


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--core",
        action="append",
        default=[],
        help="Core/gold dataset path. Can be supplied multiple times.",
    )
    ap.add_argument(
        "--extension",
        action="append",
        default=[],
        help="Extension/draft dataset path. Can be supplied multiple times.",
    )
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--prefix", default="gold_vocab_gap")
    ap.add_argument("--top-words", type=int, default=30)
    ap.add_argument("--top-phrases", type=int, default=20)
    ap.add_argument("--top-gaps", type=int, default=25)
    ap.add_argument("--min-core-count", type=int, default=3)
    ap.add_argument("--gap-ratio", type=float, default=0.35)
    return ap.parse_args()


def _resolve(path_text: str) -> Path:
    path = Path(str(path_text).strip())
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def _normalize_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _tokenize(text: Any) -> list[str]:
    return WORD_RE.findall(_normalize_text(text))


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for idx, line in enumerate(fh, start=1):
            text = line.strip()
            if not text:
                continue
            obj = json.loads(text)
            if not isinstance(obj, dict):
                raise RuntimeError(f"{path}:{idx}: expected JSON object")
            rows.append(obj)
    return rows


def _iter_language_texts(rows: list[dict[str, Any]]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for row in rows:
        src_lang = str(row.get("src_lang", "")).strip().lower()
        tgt_lang = str(row.get("tgt_lang", "")).strip().lower()
        source = str(row.get("source", "")).strip()
        target = str(row.get("target_pos", row.get("pos", ""))).strip()
        if src_lang in {"en", "es"} and source:
            out.append((src_lang, source))
        if tgt_lang in {"en", "es"} and target:
            out.append((tgt_lang, target))
    return out


def _is_content_token(lang: str, token: str) -> bool:
    if not token:
        return False
    if any(ch.isdigit() for ch in token):
        return False
    return token not in STOPWORDS[lang]


def _count_ngrams(tokens: list[str], n: int, lang: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    if len(tokens) < n:
        return counter
    for idx in range(len(tokens) - n + 1):
        gram_tokens = tokens[idx : idx + n]
        if not all(_is_content_token(lang, token) for token in gram_tokens):
            continue
        counter[" ".join(gram_tokens)] += 1
    return counter


def _build_profile(paths: list[Path]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(_load_rows(path))
    texts = _iter_language_texts(rows)

    profile: dict[str, Any] = {
        "rows": len(rows),
        "texts": len(texts),
        "paths": [_safe_rel(path) for path in paths],
        "languages": {},
    }
    for lang in ("en", "es"):
        token_counter: Counter[str] = Counter()
        content_counter: Counter[str] = Counter()
        bigram_counter: Counter[str] = Counter()
        trigram_counter: Counter[str] = Counter()
        text_count = 0
        total_tokens = 0
        for text_lang, text in texts:
            if text_lang != lang:
                continue
            text_count += 1
            tokens = _tokenize(text)
            total_tokens += len(tokens)
            token_counter.update(tokens)
            content_counter.update(token for token in tokens if _is_content_token(lang, token))
            bigram_counter.update(_count_ngrams(tokens, 2, lang))
            trigram_counter.update(_count_ngrams(tokens, 3, lang))
        profile["languages"][lang] = {
            "text_count": text_count,
            "total_tokens": total_tokens,
            "token_counter": token_counter,
            "content_counter": content_counter,
            "bigram_counter": bigram_counter,
            "trigram_counter": trigram_counter,
        }
    return profile


def _rate(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return (10000.0 * float(count)) / float(total)


def _top_items(counter: Counter[str], total: int, n: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item, count in counter.most_common(n):
        out.append({"item": item, "count": count, "per_10k": round(_rate(count, total), 2)})
    return out


def _gap_items(
    *,
    core_counter: Counter[str],
    ext_counter: Counter[str],
    core_total: int,
    ext_total: int,
    min_core_count: int,
    gap_ratio: float,
    top_n: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item, core_count in core_counter.items():
        if core_count < min_core_count:
            continue
        ext_count = ext_counter.get(item, 0)
        core_rate = _rate(core_count, core_total)
        ext_rate = _rate(ext_count, ext_total)
        if core_rate <= 0:
            continue
        ratio = 0.0 if core_rate <= 0 else (ext_rate / core_rate)
        if ratio > gap_ratio:
            continue
        rows.append(
            {
                "item": item,
                "core_count": core_count,
                "ext_count": ext_count,
                "core_per_10k": round(core_rate, 2),
                "ext_per_10k": round(ext_rate, 2),
                "gap_per_10k": round(core_rate - ext_rate, 2),
                "coverage_ratio": round(ratio, 3),
            }
        )
    rows.sort(key=lambda row: (-row["gap_per_10k"], -row["core_count"], row["item"]))
    return rows[:top_n]


def _language_label(lang: str) -> str:
    return "English" if lang == "en" else "Spanish"


def _render_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["| none |", "| --- |"]
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    out = [header, sep]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return out


def _write_outputs(
    *,
    out_dir: Path,
    prefix: str,
    core_profile: dict[str, Any],
    extension_profile: dict[str, Any],
    total_profile: dict[str, Any],
    top_words: int,
    top_phrases: int,
    top_gaps: int,
    min_core_count: int,
    gap_ratio: float,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{prefix}.md"
    json_path = out_dir / f"{prefix}.json"

    payload: dict[str, Any] = {
        "core_paths": core_profile["paths"],
        "extension_paths": extension_profile["paths"],
        "total_paths": total_profile["paths"],
        "min_core_count": min_core_count,
        "gap_ratio": gap_ratio,
        "languages": {},
    }

    lines = [
        "# Translation Vocabulary Gap Report",
        "",
        f"- core_paths: `{', '.join(core_profile['paths'])}`",
        f"- extension_paths: `{', '.join(extension_profile['paths'])}`",
        f"- total_rows: `{total_profile['rows']}`",
        "",
        "This report uses stopword-filtered content words and contiguous content bigrams.",
        "",
    ]

    for lang in ("en", "es"):
        total_lang = total_profile["languages"][lang]
        core_lang = core_profile["languages"][lang]
        ext_lang = extension_profile["languages"][lang]

        top_total_words = _top_items(total_lang["content_counter"], total_lang["total_tokens"], top_words)
        top_total_bigrams = _top_items(total_lang["bigram_counter"], total_lang["total_tokens"], top_phrases)
        gap_words = _gap_items(
            core_counter=core_lang["content_counter"],
            ext_counter=ext_lang["content_counter"],
            core_total=core_lang["total_tokens"],
            ext_total=ext_lang["total_tokens"],
            min_core_count=min_core_count,
            gap_ratio=gap_ratio,
            top_n=top_gaps,
        )
        gap_bigrams = _gap_items(
            core_counter=core_lang["bigram_counter"],
            ext_counter=ext_lang["bigram_counter"],
            core_total=core_lang["total_tokens"],
            ext_total=ext_lang["total_tokens"],
            min_core_count=min_core_count,
            gap_ratio=gap_ratio,
            top_n=top_gaps,
        )

        payload["languages"][lang] = {
            "text_count_total": total_lang["text_count"],
            "token_total": total_lang["total_tokens"],
            "top_total_words": top_total_words,
            "top_total_bigrams": top_total_bigrams,
            "underserved_words": gap_words,
            "underserved_bigrams": gap_bigrams,
        }

        lines.extend(
            [
                f"## {_language_label(lang)}",
                "",
                f"- total_texts: `{total_lang['text_count']}`",
                f"- total_tokens: `{total_lang['total_tokens']}`",
                "",
                f"### Most Common Content Words",
                "",
            ]
        )
        lines.extend(_render_table(top_total_words, [("item", "word"), ("count", "count"), ("per_10k", "per_10k")]))
        lines.extend(
            [
                "",
                "### Most Common Content Bigrams",
                "",
            ]
        )
        lines.extend(_render_table(top_total_bigrams, [("item", "phrase"), ("count", "count"), ("per_10k", "per_10k")]))
        lines.extend(
            [
                "",
                "### Under-Served Content Words",
                "",
                f"Core terms with count >= `{min_core_count}` and extension/core rate <= `{gap_ratio}`.",
                "",
            ]
        )
        lines.extend(
            _render_table(
                gap_words,
                [
                    ("item", "word"),
                    ("core_count", "core_count"),
                    ("ext_count", "ext_count"),
                    ("core_per_10k", "core_per_10k"),
                    ("ext_per_10k", "ext_per_10k"),
                    ("coverage_ratio", "coverage_ratio"),
                ],
            )
        )
        lines.extend(
            [
                "",
                "### Under-Served Content Bigrams",
                "",
            ]
        )
        lines.extend(
            _render_table(
                gap_bigrams,
                [
                    ("item", "phrase"),
                    ("core_count", "core_count"),
                    ("ext_count", "ext_count"),
                    ("core_per_10k", "core_per_10k"),
                    ("ext_per_10k", "ext_per_10k"),
                    ("coverage_ratio", "coverage_ratio"),
                ],
            )
        )
        lines.append("")

    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return md_path, json_path


def main() -> int:
    args = _parse_args()
    core_paths = [_resolve(text) for text in (args.core or [])] or list(DEFAULT_CORE_DATASETS)
    extension_paths = [_resolve(text) for text in (args.extension or [])] or list(DEFAULT_EXTENSION_DATASETS)
    total_paths = core_paths + extension_paths

    core_profile = _build_profile(core_paths)
    extension_profile = _build_profile(extension_paths)
    total_profile = _build_profile(total_paths)

    md_path, json_path = _write_outputs(
        out_dir=_resolve(args.out_dir),
        prefix=str(args.prefix),
        core_profile=core_profile,
        extension_profile=extension_profile,
        total_profile=total_profile,
        top_words=int(args.top_words),
        top_phrases=int(args.top_phrases),
        top_gaps=int(args.top_gaps),
        min_core_count=int(args.min_core_count),
        gap_ratio=float(args.gap_ratio),
    )
    print(f"[vocab-gap] md={_safe_rel(md_path)}")
    print(f"[vocab-gap] json={_safe_rel(json_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
