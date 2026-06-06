#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path


def load_words(path: Path) -> list[str]:
    words: list[str] = []
    seen: set[str] = set()
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        word = "".join(c for c in raw.strip().lower() if "a" <= c <= "z")
        if word and word not in seen:
            words.append(word)
            seen.add(word)
    return words


def scan_counts(path: Path, vocab: set[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    word: list[str] = []

    def flush() -> None:
        if not word:
            return
        token = "".join(word)
        if token in vocab:
            counts[token] += 1
        word.clear()

    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            for b in chunk:
                if 65 <= b <= 90:
                    word.append(chr(b + 32))
                elif 97 <= b <= 122:
                    word.append(chr(b))
                else:
                    flush()
        flush()
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dictionary", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stats", required=True)
    args = parser.parse_args()

    words = load_words(Path(args.dictionary))
    counts = scan_counts(Path(args.input), set(words))
    original_index = {word: i for i, word in enumerate(words)}
    reordered = sorted(words, key=lambda w: (-counts[w], original_index[w]))

    Path(args.output).write_text("".join(f"{word}\n" for word in reordered),
                                 encoding="utf-8")
    covered = sum(counts.values())
    moved = sum(1 for i, word in enumerate(reordered) if original_index[word] != i)
    top = [
        {
            "word": word,
            "count": counts[word],
            "original_index": original_index[word],
            "new_index": i,
        }
        for i, word in enumerate(reordered[:80])
    ]
    payload = {
        "input": args.input,
        "dictionary": args.dictionary,
        "output": args.output,
        "words": len(words),
        "matched_tokens": covered,
        "moved_words": moved,
        "top": top,
    }
    Path(args.stats).write_text(json.dumps(payload, indent=2) + "\n",
                                 encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
