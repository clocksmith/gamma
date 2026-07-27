#!/usr/bin/env python3
"""Verify the BPD-1 learner and emit a finite prefix receipt."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib


def learn(prefix: bytes, limit: int) -> bytes:
    counts: dict[bytes, int] = collections.defaultdict(int)
    first: dict[bytes, int] = {}
    i = 0
    while i < len(prefix):
        if not (65 <= prefix[i] <= 90 or 97 <= prefix[i] <= 122):
            i += 1
            continue
        start = i
        token = bytearray()
        while i < len(prefix) and (
            65 <= prefix[i] <= 90 or 97 <= prefix[i] <= 122
        ):
            value = prefix[i]
            token.append(value + 32 if 65 <= value <= 90 else value)
            i += 1
        word = bytes(token)
        counts[word] += 1
        first.setdefault(word, start)
    ordered = sorted(counts, key=lambda word: (-counts[word], first[word], word))
    return b"".join(word + b"\n" for word in ordered[:limit])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=pathlib.Path, required=True)
    parser.add_argument("--reference-dictionary", type=pathlib.Path)
    parser.add_argument("--prefix", type=int, default=262144)
    parser.add_argument("--limit", type=int, default=44515)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    if args.prefix < 0 or args.limit < 0:
        raise SystemExit("prefix and limit must be nonnegative")
    data = args.input.read_bytes()[: args.prefix]
    dictionary = learn(data, args.limit)
    if learn(data, args.limit) != dictionary:
        raise AssertionError("learner is not deterministic")
    words = dictionary.splitlines()
    if len(words) != len(set(words)):
        raise AssertionError("dictionary contains duplicates")
    if any(not word or any(not 97 <= byte <= 122 for byte in word) for word in words):
        raise AssertionError("dictionary token grammar violation")

    receipt: dict[str, object] = {
        "schema": "bootstrap_prefix_dictionary_verifier_v1",
        "input": {
            "path": str(args.input),
            "prefix_bytes": len(data),
            "prefix_sha256": hashlib.sha256(data).hexdigest(),
        },
        "learner": {
            "limit": args.limit,
            "dictionary_bytes": len(dictionary),
            "dictionary_sha256": hashlib.sha256(dictionary).hexdigest(),
            "words": len(words),
            "unique": True,
            "deterministic_second_build": True,
        },
        "score_credit_bytes": 0,
        "verdict": "pass",
    }
    if args.reference_dictionary is not None:
        reference = args.reference_dictionary.read_bytes().splitlines()
        reference_set = set(reference)
        overlap = sum(word in reference_set for word in words)
        receipt["reference"] = {
            "path": str(args.reference_dictionary),
            "words": len(reference),
            "overlap_words": overlap,
            "overlap_fraction": overlap / len(words) if words else 0.0,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

