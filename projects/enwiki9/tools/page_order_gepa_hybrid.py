#!/usr/bin/env python3
"""Hybrid GEPA screen for reversible enwiki page-order genotypes.

This is intentionally model-free: it mutates ordering keys and scores adjacent
page continuity without running cmix, xz, lzma, or bench.py. The output is a
selector for later exact gates under the heavy benchmark lock.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import sys
from dataclasses import dataclass
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import page_order_gepa as base  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT = ROOT / "results" / "page_order_gepa"

FEATURE_NAMES = tuple(base.FEATURES)
HIGH_VALUE_FEATURES = (
    "kind",
    "template",
    "redirect",
    "first_link",
    "mh3",
    "mh4",
    "category",
    "topic",
    "title_suffix",
    "params",
    "shape",
    "size",
)

MANUAL_SEEDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("hybrid__kind__template__redirect__mh3", ("kind", "template", "redirect", "mh3")),
    ("hybrid__kind__template__first_link__mh3", ("kind", "template", "first_link", "mh3")),
    ("hybrid__kind__template__first_link__category__title_suffix", ("kind", "template", "first_link", "category", "title_suffix")),
    ("hybrid__kind__template__params__category__title_suffix", ("kind", "template", "params", "category", "title_suffix")),
    ("hybrid__kind__template__first_link__category__mh3", ("kind", "template", "first_link", "category", "mh3")),
    ("hybrid__kind__topic__category__title_suffix__mh3", ("kind", "topic", "category", "title_suffix", "mh3")),
    ("hybrid__shape__template__topic__mh3", ("shape", "template", "topic", "mh3")),
    ("hybrid__kind__template__shape__first_link__mh3", ("kind", "template", "shape", "first_link", "mh3")),
)


@dataclass(frozen=True)
class Genotype:
    name: str
    fields: tuple[str, ...]
    origin: str


def normalize(fields: tuple[str, ...], max_width: int) -> tuple[str, ...]:
    out: list[str] = []
    for field in fields:
        if field in base.FEATURES and field not in out:
            out.append(field)
        if len(out) >= max_width:
            break
    if len(out) < 2:
        for field in HIGH_VALUE_FEATURES:
            if field not in out:
                out.append(field)
            if len(out) >= 2:
                break
    return tuple(out)


def random_fields(rng: random.Random, max_width: int) -> tuple[str, ...]:
    width = rng.randint(2, max_width)
    head_pool = HIGH_VALUE_FEATURES if rng.random() < 0.75 else FEATURE_NAMES
    fields: list[str] = []
    while len(fields) < width:
        pool = head_pool if not fields else FEATURE_NAMES
        field = rng.choice(pool)
        if field not in fields:
            fields.append(field)
    return tuple(fields)


def mutate(fields: tuple[str, ...], rng: random.Random, max_width: int) -> tuple[str, ...]:
    out = list(fields)
    op = rng.choice(
        [
            "replace",
            "insert",
            "delete",
            "swap",
            "shuffle",
            "minhash_flip",
            "template_pull",
            "semantic_pull",
        ]
    )
    if op == "replace" and out:
        out[rng.randrange(len(out))] = rng.choice(FEATURE_NAMES)
    elif op == "insert" and len(out) < max_width:
        out.insert(rng.randrange(len(out) + 1), rng.choice(FEATURE_NAMES))
    elif op == "delete" and len(out) > 2:
        del out[rng.randrange(len(out))]
    elif op == "swap" and len(out) >= 2:
        a, b = rng.sample(range(len(out)), 2)
        out[a], out[b] = out[b], out[a]
    elif op == "shuffle" and len(out) >= 3:
        rng.shuffle(out)
    elif op == "minhash_flip":
        choices = ["mh2", "mh3", "mh4"]
        for i, field in enumerate(out):
            if field in choices:
                out[i] = rng.choice([item for item in choices if item != field])
                break
        else:
            out.append(rng.choice(choices))
    elif op == "template_pull":
        out = ["kind", "template"] + [field for field in out if field not in {"kind", "template"}]
    elif op == "semantic_pull":
        out = ["kind", "topic"] + [field for field in out if field not in {"kind", "topic"}]
    return normalize(tuple(out), max_width)


def crossover(left: tuple[str, ...], right: tuple[str, ...], rng: random.Random, max_width: int) -> tuple[str, ...]:
    if len(left) < 2 or len(right) < 2:
        return normalize(left + right, max_width)
    a = rng.randrange(1, len(left) + 1)
    b = rng.randrange(0, len(right))
    return normalize(left[:a] + right[b:], max_width)


def candidate_pool(rng: random.Random, max_candidates: int, max_width: int, seed_specs: int) -> list[Genotype]:
    seen: set[tuple[str, ...]] = set()
    pool: list[Genotype] = []

    def add(name: str, fields: tuple[str, ...], origin: str) -> None:
        fields = normalize(fields, max_width)
        if fields in seen:
            return
        seen.add(fields)
        pool.append(Genotype(name, fields, origin))

    for name, fields in MANUAL_SEEDS:
        add(name, fields, "manual_hybrid")
    for name, fields in base.candidate_specs(seed_specs):
        add(name, fields, "enumerated")

    mutation_index = 0
    while len(pool) < max_candidates:
        roll = rng.random()
        if roll < 0.20:
            fields = random_fields(rng, max_width)
            origin = "random"
        elif roll < 0.70:
            parent = rng.choice(pool).fields
            fields = mutate(parent, rng, max_width)
            origin = "mutation"
        else:
            left, right = rng.sample(pool, 2)
            fields = crossover(left.fields, right.fields, rng, max_width)
            origin = "crossover"
        add(f"hybrid_m{mutation_index:05d}", fields, origin)
        mutation_index += 1
    return pool


def order_for(features: list[dict[str, Any]], fields: tuple[str, ...]) -> list[int]:
    def key(index: int) -> tuple[Any, ...]:
        item = features[index]
        return tuple(base.FEATURES[name](item) for name in fields) + (item["pid"],)

    return sorted(range(len(features)), key=key)


def fields_distance(left: list[str], right: list[str]) -> float:
    a = set(left)
    b = set(right)
    if not a and not b:
        return 0.0
    return 1.0 - (len(a & b) / len(a | b))


def select_diverse(rows: list[dict[str, Any]], limit: int, diversity_weight: float) -> list[dict[str, Any]]:
    if not rows:
        return []
    selected = [rows[0]]
    remaining = rows[1:]
    while remaining and len(selected) < limit:
        best_index = 0
        best_objective = float("-inf")
        for index, row in enumerate(remaining):
            min_distance = min(fields_distance(row["fields"], chosen["fields"]) for chosen in selected)
            objective = float(row["score_delta_vs_original"]) + diversity_weight * min_distance
            if objective > best_objective:
                best_index = index
                best_objective = objective
        selected.append(remaining.pop(best_index))
    return selected


def run(data: bytes, seed: int, max_candidates: int, max_width: int, top: int, seed_specs: int, diversity_weight: float) -> dict[str, Any]:
    head, pages, tail, ids = base.split_pages(data)
    if not pages:
        raise SystemExit("no pages found")
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate page ids in slice")

    features = [base.page_features(page, pid) for page, pid in zip(pages, ids)]
    original_order = list(range(len(pages)))
    original_score = base.score_order(features, original_order)
    rng = random.Random(seed)
    candidates = candidate_pool(rng, max_candidates, max_width, seed_specs)

    rows: list[dict[str, Any]] = []
    for genotype in candidates:
        order = order_for(features, genotype.fields)
        restored = sorted(order, key=lambda index: features[index]["pid"])
        if restored != original_order:
            raise SystemExit(f"{genotype.name}: restore-by-id check failed")
        metrics = base.score_order(features, order)
        digest = hashlib.sha256(
            b",".join(str(features[index]["pid"]).encode() for index in order)
        ).hexdigest()
        rows.append(
            {
                "name": genotype.name,
                "origin": genotype.origin,
                "fields": list(genotype.fields),
                "pages": len(pages),
                "moved_pages": sum(1 for old, new in enumerate(order) if old != new),
                "score_delta_vs_original": metrics["adjacency_score"] - original_score["adjacency_score"],
                "order_sha256": digest,
                "first_ids": [features[index]["pid"] for index in order[:10]],
                **metrics,
            }
        )
    rows.sort(key=lambda row: (row["score_delta_vs_original"], row["adjacency_score"]), reverse=True)
    return {
        "input_bytes": len(data),
        "pages": len(pages),
        "head": len(head),
        "tail": len(tail),
        "seed": seed,
        "candidate_count": len(rows),
        "basis": "hybrid GEPA no-compression adjacency screen; exact compression required before promotion",
        "original": original_score,
        "top_by_score": rows[:top],
        "diverse_top": select_diverse(rows, top, diversity_weight),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--limit", type=int, default=10_000_000)
    parser.add_argument("--seed", type=int, default=271828)
    parser.add_argument("--max-candidates", type=int, default=5000)
    parser.add_argument("--max-width", type=int, default=6)
    parser.add_argument("--seed-specs", type=int, default=1200)
    parser.add_argument("--top", type=int, default=40)
    parser.add_argument("--diversity-weight", type=float, default=120.0)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    data = args.data.read_bytes()[: args.limit]
    result = run(
        data=data,
        seed=args.seed,
        max_candidates=args.max_candidates,
        max_width=args.max_width,
        top=args.top,
        seed_specs=args.seed_specs,
        diversity_weight=args.diversity_weight,
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"hybrid_limit{args.limit}_seed{args.seed}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "out": str(out),
                "best": result["top_by_score"][0] if result["top_by_score"] else None,
                "diverse_first": result["diverse_top"][:5],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
