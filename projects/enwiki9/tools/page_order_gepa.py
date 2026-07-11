#!/usr/bin/env python3
"""Model-free GEPA-style search for reversible enwiki page order keys."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from collections import Counter
from itertools import combinations, product
from typing import Any


PAGE_OPEN = b"  <page>\n"
PAGE_CLOSE = b"  </page>\n"


def field(page: bytes, pat: bytes) -> bytes:
    match = re.search(pat, page, re.S | re.I)
    return match.group(1) if match else b""


def norm(value: bytes, limit: int = 180) -> bytes:
    return re.sub(rb"[^a-z0-9]+", b" ", value.lower()).strip()[:limit]


def words(value: bytes, limit: int = 64) -> tuple[bytes, ...]:
    out: list[bytes] = []
    seen: set[bytes] = set()
    for match in re.finditer(rb"[a-z][a-z0-9]{2,24}", value.lower()):
        token = match.group(0)
        if token in seen:
            continue
        seen.add(token)
        out.append(token)
        if len(out) >= limit:
            break
    return tuple(out)


def bucket(value: int) -> int:
    out = 0
    while value > 15 and out < 31:
        value >>= 1
        out += 1
    return out


def split_pages(data: bytes) -> tuple[bytes, list[bytes], bytes, list[int]]:
    first = data.find(PAGE_OPEN)
    if first < 0:
        return data, [], b"", []
    pages: list[bytes] = []
    offset = first
    while True:
        start = data.find(PAGE_OPEN, offset)
        if start < 0:
            break
        end = data.find(PAGE_CLOSE, start)
        if end < 0:
            break
        end += len(PAGE_CLOSE)
        pages.append(data[start:end])
        offset = end
    ids = [int(field(page, rb"<id>(\d+)</id>") or 10**30) for page in pages]
    return data[:first], pages, data[offset:], ids


def unique_norm(values: list[bytes], limit: int, item_limit: int = 80) -> tuple[bytes, ...]:
    out: list[bytes] = []
    seen: set[bytes] = set()
    for value in values:
        item = norm(value, item_limit)
        if item and item not in seen:
            out.append(item)
            seen.add(item)
            if len(out) >= limit:
                break
    return tuple(out)


def minhash(tokens: tuple[bytes, ...], bands: int = 8) -> tuple[int, ...]:
    if not tokens:
        return (0,) * bands
    out: list[int] = []
    for band in range(bands):
        seed = band.to_bytes(1, "little")
        best = (1 << 64) - 1
        for token in tokens:
            h = int.from_bytes(hashlib.blake2s(seed + token, digest_size=8).digest(), "little")
            if h < best:
                best = h
        out.append(best >> 40)
    return tuple(out)


def simhash(tokens: tuple[bytes, ...], bits: int = 64) -> bytes:
    """Return a locality-preserving content signature for lexicographic sort."""
    if not tokens:
        return b"\0" * (bits // 8)
    accum = [0] * bits
    for token in tokens:
        digest = int.from_bytes(hashlib.blake2s(token, digest_size=bits // 8).digest(), "big")
        for bit in range(bits):
            accum[bit] += 1 if digest & (1 << bit) else -1
    value = 0
    for bit, weight in enumerate(accum):
        if weight >= 0:
            value |= 1 << bit
    return value.to_bytes(bits // 8, "big")


def shape_sig(page: bytes) -> bytes:
    sig = bytearray()
    for raw in page.splitlines()[:160]:
        line = raw.strip()
        if not line:
            sig.extend(b"_;")
        elif line.startswith(b"<"):
            match = re.match(rb"</?([a-zA-Z0-9:_-]+)", line)
            sig.extend((match.group(1).lower()[:8] if match else b"<") + b";")
        elif line.startswith(b"{{"):
            name = norm(field(line, rb"\{\{\s*([^\|\}\n]{1,64})"), 32)
            sig.extend(b"T" + name + b";")
        elif line.startswith(b"|"):
            sig.extend(b"P;")
        elif line.startswith(b"=="):
            sig.extend(b"H;")
        elif line.startswith((b"*", b"#", b":", b";")):
            sig.extend(line[:1] + b";")
        else:
            sig.extend(b"W;")
    return hashlib.blake2s(bytes(sig), digest_size=8).digest()


def page_kind(title: bytes, page: bytes, categories: tuple[bytes, ...], templates: tuple[bytes, ...]) -> bytes:
    lower = page[:4096].lower()
    if b"#redirect" in lower:
        return b"redirect"
    if title.startswith(b"category "):
        return b"category"
    if title.startswith(b"list of"):
        return b"list"
    if b"disambiguation" in title:
        return b"disambig"
    if templates and any(b"taxobox" in item or b"speciesbox" in item for item in templates):
        return b"taxon"
    if templates and any(b"infobox" in item for item in templates):
        return b"infobox"
    if categories:
        return b"category_tagged"
    return b"plain"


def title_parts(title: bytes) -> tuple[bytes, bytes, bytes, bytes]:
    tokens = words(title, 16)
    prefix = b" ".join(tokens[:3])
    suffix = b" ".join(tokens[-3:])
    reversed_title = b" ".join(reversed(tokens))
    namespace = tokens[0] if len(tokens) > 1 and b":" in title[:64] else b""
    return prefix, suffix, reversed_title, namespace


def page_features(page: bytes, pid: int) -> dict[str, Any]:
    raw_title = field(page, rb"<title>(.*?)</title>")
    title = norm(raw_title, 220)
    text = field(page, rb"<text[^>]*>(.*?)</text>") or page
    categories = unique_norm(re.findall(rb"\[\[Category:([^\]\|\n]{1,120})", page, re.I), 8)
    templates = unique_norm(re.findall(rb"\{\{\s*([a-z0-9 _-]{1,80})(?:[|}\n])", page, re.I), 8)
    params = unique_norm(re.findall(rb"\|\s*([a-z0-9 _-]{1,50})\s*=", page, re.I), 10, 50)
    redirect = norm(field(page, rb"#redirect\s*\[\[([^\]\|\n]{1,140})"), 140)
    first_link = norm(field(page, rb"\[\[([^\]\|\n]{1,120})(?:\|[^\]\n]*)?\]\]"), 120)
    token_set = words(text, 160)
    prefix, suffix, reversed_title, namespace = title_parts(raw_title)
    kind = page_kind(title, page, categories, templates)
    topic = (
        b" ".join(categories[:4])
        or b" ".join(templates[:4])
        or first_link
        or prefix
        or title
    )
    return {
        "pid": pid,
        "title": title,
        "title_prefix": prefix,
        "title_suffix": suffix,
        "rev_title": reversed_title,
        "namespace": namespace,
        "categories": categories,
        "category_head": b" ".join(categories[:4]),
        "templates": templates,
        "template_head": b" ".join(templates[:4]),
        "params": b" ".join(params[:6]),
        "redirect": redirect,
        "first_link": first_link,
        "kind": kind,
        "topic": topic,
        "shape": shape_sig(page),
        "size_bucket": bucket(len(page)),
        "line_bucket": bucket(page.count(b"\n")),
        "tokens": set(token_set),
        "minhash": minhash(token_set),
        "simhash": simhash(token_set),
    }


FEATURES = {
    "kind": lambda f: f["kind"],
    "topic": lambda f: f["topic"],
    "category": lambda f: f["category_head"],
    "template": lambda f: f["template_head"],
    "params": lambda f: f["params"],
    "title": lambda f: f["title"],
    "title_prefix": lambda f: f["title_prefix"],
    "title_suffix": lambda f: f["title_suffix"],
    "rev_title": lambda f: f["rev_title"],
    "namespace": lambda f: f["namespace"],
    "first_link": lambda f: f["first_link"],
    "redirect": lambda f: f["redirect"],
    "shape": lambda f: f["shape"],
    "size": lambda f: f["size_bucket"],
    "lines": lambda f: f["line_bucket"],
    "mh2": lambda f: f["minhash"][:2],
    "mh3": lambda f: f["minhash"][:3],
    "mh4": lambda f: f["minhash"][:4],
    "simhash": lambda f: f["simhash"],
}


SEEDS = [
    ("geometry", ("redirect", "category", "template", "topic")),
    ("geometry_title", ("redirect", "category", "template", "topic", "title")),
    ("geometry_suffix", ("redirect", "category", "template", "topic", "title_suffix")),
    ("geometry_simhash", ("redirect", "category", "template", "topic", "simhash")),
    ("topic_mh3", ("topic", "mh3", "kind", "size")),
    ("template_params", ("template", "params", "category", "title_suffix")),
    ("shape_topic", ("shape", "topic", "kind", "size")),
    ("kind_simhash", ("kind", "simhash", "shape", "size")),
]


def candidate_specs(max_specs: int) -> list[tuple[str, tuple[str, ...]]]:
    specs: list[tuple[str, tuple[str, ...]]] = list(SEEDS)
    seen = {fields for _, fields in specs}
    heads = [
        "topic",
        "category",
        "template",
        "kind",
        "shape",
        "mh3",
        "simhash",
        "namespace",
    ]
    mids = ["title_prefix", "title_suffix", "rev_title", "params", "first_link", "mh2", "size"]
    tails = ["title", "title_suffix", "size", "lines", "mh4"]
    for width in (2, 3, 4):
        pools = [heads, mids, tails, ["kind", "size", "lines"]][:width]
        for fields in product(*pools):
            deduped = tuple(dict.fromkeys(fields))
            if len(deduped) != width or deduped in seen:
                continue
            name = "gepa__" + "__".join(deduped)
            specs.append((name, deduped))
            seen.add(deduped)
            if len(specs) >= max_specs:
                return specs
    for fields in combinations(FEATURES, 4):
        if fields in seen:
            continue
        specs.append(("gepa__" + "__".join(fields), fields))
        seen.add(fields)
        if len(specs) >= max_specs:
            break
    return specs


def order_for(features: list[dict[str, Any]], fields: tuple[str, ...]) -> list[int]:
    def key(index: int) -> tuple[Any, ...]:
        item = features[index]
        return tuple(FEATURES[name](item) for name in fields) + (item["pid"],)

    return sorted(range(len(features)), key=key)


def pair_score(left: dict[str, Any], right: dict[str, Any]) -> float:
    score = 0.0
    if left["topic"] and left["topic"] == right["topic"]:
        score += 4.0
    if left["kind"] == right["kind"]:
        score += 1.0
    if left["category_head"] and left["category_head"] == right["category_head"]:
        score += 2.0
    if left["template_head"] and left["template_head"] == right["template_head"]:
        score += 1.5
    if left["shape"] == right["shape"]:
        score += 0.75
    mh_matches = sum(1 for a, b in zip(left["minhash"], right["minhash"]) if a == b)
    score += 0.4 * mh_matches
    tokens_l = left["tokens"]
    tokens_r = right["tokens"]
    if tokens_l and tokens_r:
        inter = len(tokens_l & tokens_r)
        union = len(tokens_l | tokens_r)
        score += 6.0 * inter / union
    return score


def score_order(features: list[dict[str, Any]], order: list[int]) -> dict[str, float]:
    if len(order) < 2:
        return {"adjacency_score": 0.0, "mean_pair_score": 0.0, "topic_runs": 0.0}
    total = 0.0
    topic_runs = 0
    for a, b in zip(order, order[1:]):
        left = features[a]
        right = features[b]
        total += pair_score(left, right)
        if left["topic"] and left["topic"] == right["topic"]:
            topic_runs += 1
    mean = total / (len(order) - 1)
    return {
        "adjacency_score": total,
        "mean_pair_score": mean,
        "topic_runs": float(topic_runs),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=pathlib.Path("data/enwik9"))
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--max-candidates", type=int, default=250)
    args = parser.parse_args()

    with args.data.open("rb") as handle:
        data = handle.read(args.limit)
    head, pages, tail, ids = split_pages(data)
    if not pages:
        raise SystemExit("no pages found")
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate page ids in slice")
    features = [page_features(page, pid) for page, pid in zip(pages, ids)]
    original_order = list(range(len(pages)))
    original_score = score_order(features, original_order)
    rows: list[dict[str, Any]] = []
    for name, fields in candidate_specs(args.max_candidates):
        order = order_for(features, fields)
        restored = sorted(order, key=lambda index: features[index]["pid"])
        if restored != original_order:
            raise SystemExit(f"{name}: restore-by-id check failed")
        metrics = score_order(features, order)
        moved = sum(1 for old, new in enumerate(order) if old != new)
        rows.append(
            {
                "name": name,
                "fields": list(fields),
                "pages": len(pages),
                "moved_pages": moved,
                "score_delta_vs_original": metrics["adjacency_score"]
                - original_score["adjacency_score"],
                **metrics,
                "first_ids": [features[index]["pid"] for index in order[:8]],
            }
        )
    rows.sort(key=lambda row: (row["score_delta_vs_original"], row["adjacency_score"]), reverse=True)
    role_counts = Counter(feature["kind"] for feature in features)
    result = {
        "input_bytes": len(data),
        "pages": len(pages),
        "head": len(head),
        "tail": len(tail),
        "candidate_count": len(rows),
        "scoring": "deterministic model-free adjacency score over topic/template/category/shape/minhash/token overlap; not a compression score",
        "role_counts": {
            key.decode("ascii", "replace"): value for key, value in role_counts.items()
        },
        "original": original_score,
        "top": rows[: args.top],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
