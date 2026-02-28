#!/usr/bin/env python3
"""Build a corpus text file for vocab subsetting.

The inputs are:
- translation pair JSONL files (objects with source/target language and text fields)
- raw text files

This is shared by the translation run pipeline and shell wrapper so both distillation
entrypoints use the same extraction semantics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _norm(value: str) -> str:
    return " ".join(str(value).split()).strip().casefold()


def _parse_csv(value: str) -> list[str]:
    return [x.strip() for x in str(value).split(",") if x.strip()]


def _iter_pairs(path: Path, min_chars: int, wanted_src: set[str], wanted_tgt: set[str], seen: set[str]) -> list[str]:
    out: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
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
            source_text = _safe_text(obj.get("source") or obj.get("query"))
            target_text = _safe_text(obj.get("target_pos") or obj.get("pos") or obj.get("target"))
            source_ok = not wanted_src or source_lang in wanted_src
            target_ok = not wanted_tgt or target_lang in wanted_tgt
            if source_ok and len(source_text) >= int(min_chars):
                norm = _norm(source_text)
                if norm and norm not in seen:
                    seen.add(norm)
                    out.append(source_text)
            if target_ok and len(target_text) >= int(min_chars):
                norm = _norm(target_text)
                if norm and norm not in seen:
                    seen.add(norm)
                    out.append(target_text)
    return out


def _iter_lines(path: Path, min_chars: int, seen: set[str]) -> list[str]:
    out: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            text = line.strip()
            if len(text) < int(min_chars):
                continue
            norm = _norm(text)
            if norm and norm not in seen:
                seen.add(norm)
                out.append(text)
    return out


def build_subset_text_file(
    *,
    pair_jsonls: list[Path],
    text_files: list[Path],
    source_langs: list[str],
    target_langs: list[str],
    min_text_chars: int,
    out_path: Path,
) -> int:
    wanted_src = set(_parse_csv(",".join(source_langs)))
    wanted_tgt = set(_parse_csv(",".join(target_langs)))
    seen: set[str] = set()
    out: list[str] = []

    for pair_path in pair_jsonls:
        if not pair_path.exists():
            continue
        out.extend(_iter_pairs(pair_path, int(min_text_chars), wanted_src, wanted_tgt, seen))

    for text_path in text_files:
        if not text_path.exists():
            continue
        out.extend(_iter_lines(text_path, int(min_text_chars), seen))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for line in out:
            f.write(line + "\n")

    return len(out)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build subset source text from pair jsonl + raw text.")
    ap.add_argument("--pair-jsonl", action="append", default=[], help="Translation pair JSONL file (repeatable).")
    ap.add_argument("--text", action="append", default=[], help="Raw text file path (repeatable).")
    ap.add_argument("--source-langs", default="", help="Comma-separated source language filter (empty = all).")
    ap.add_argument("--target-langs", default="", help="Comma-separated target language filter (empty = all).")
    ap.add_argument("--min-text-chars", type=int, default=4)
    ap.add_argument("--out", required=True)
    return ap.parse_args()


def main() -> int:
    args = _parse_args()

    pair_paths = [Path(p) for p in args.pair_jsonl]
    text_paths = [Path(p) for p in args.text]

    missing_pairs = [str(p) for p in pair_paths if not p.exists()]
    missing_text = [str(p) for p in text_paths if not p.exists()]
    if missing_pairs:
        raise SystemExit(f"Missing --pair-jsonl file(s): {', '.join(missing_pairs)}")
    if missing_text:
        raise SystemExit(f"Missing --text file(s): {', '.join(missing_text)}")
    if not pair_paths and not text_paths:
        raise SystemExit("No --pair-jsonl or --text inputs provided.")

    count = build_subset_text_file(
        pair_jsonls=pair_paths,
        text_files=text_paths,
        source_langs=_parse_csv(str(args.source_langs)),
        target_langs=_parse_csv(str(args.target_langs)),
        min_text_chars=int(args.min_text_chars),
        out_path=Path(args.out),
    )
    print(f"[subset-text] wrote {count} unique lines to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
