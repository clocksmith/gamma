#!/usr/bin/env python3
"""GEPA-style no-compression screen for enwiki9 page ordering.

This mutates reversible page-order key recipes and scores neighboring pages by
token-set continuity. It is a cheap selector for ordering hypotheses; it does
not run cmix, xz, or any compression benchmark.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import re
import sys
from dataclasses import dataclass
from typing import Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import page_order_screen as pos  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT = ROOT / "results" / "page_order_gepa"


def words(data: bytes, limit: int = 32) -> tuple[bytes, ...]:
    return tuple(re.findall(rb"[a-z0-9]{2,32}", data.lower())[:limit])


def unique_words(data: bytes, limit: int = 32) -> tuple[bytes, ...]:
    out: list[bytes] = []
    seen: set[bytes] = set()
    for token in words(data, limit * 4):
        if token not in seen:
            out.append(token)
            seen.add(token)
            if len(out) >= limit:
                break
    return tuple(out)


@dataclass(frozen=True)
class Page:
    index: int
    page_id: int
    size: int
    title: bytes
    title_tokens: tuple[bytes, ...]
    title_tail: tuple[bytes, ...]
    categories: tuple[bytes, ...]
    templates: tuple[bytes, ...]
    params: tuple[bytes, ...]
    links: tuple[bytes, ...]
    headings: tuple[bytes, ...]
    infobox: bytes
    redirect: bytes
    body_tokens: frozenset[bytes]


def first_unique(pattern: bytes, page: bytes, limit: int) -> tuple[bytes, ...]:
    out: list[bytes] = []
    seen: set[bytes] = set()
    for raw in re.findall(pattern, page, re.I):
        token = pos.norm(raw, 80)
        if token and token not in seen:
            out.append(token)
            seen.add(token)
            if len(out) >= limit:
                break
    return tuple(out)


def parse_pages(data: bytes) -> tuple[bytes, list[bytes], bytes, list[Page]]:
    head, pages, tail, ids = pos.split_pages(data)
    parsed: list[Page] = []
    for index, page in enumerate(pages):
        title = pos.title(page)
        title_tokens = unique_words(title, 12)
        cats = first_unique(rb"\[\[Category:([^\]\|\n]{1,100})", page, 8)
        templates = first_unique(rb"\{\{\s*([a-z0-9 _-]{1,48})(?:[|}\n])", page, 8)
        params = first_unique(rb"\|\s*([a-z0-9 _-]{1,36})\s*=", page, 8)
        links = first_unique(rb"\[\[([^\]\|\n]{1,80})", page, 16)
        headings = first_unique(rb"={2,}\s*([^=\n]{1,80})\s*={2,}", page, 8)
        infobox = pos.field(page, rb"\{\{\s*(infobox[^\|\}\n]{0,80})")
        redirect = pos.field(page, rb"#redirect\s*\[\[([^\]\|\n]{1,140})")
        body_tokens = frozenset(
            unique_words(
                b" ".join(
                    [
                        title,
                        b" ".join(cats),
                        b" ".join(templates),
                        b" ".join(params),
                        b" ".join(links[:8]),
                        b" ".join(headings),
                        page[:4096],
                    ]
                ),
                96,
            )
        )
        parsed.append(
            Page(
                index=index,
                page_id=ids[index],
                size=len(page),
                title=title,
                title_tokens=title_tokens,
                title_tail=title_tokens[-3:],
                categories=cats,
                templates=templates,
                params=params,
                links=links,
                headings=headings,
                infobox=pos.norm(infobox, 80),
                redirect=pos.norm(redirect, 120),
                body_tokens=body_tokens,
            )
        )
    return head, pages, tail, parsed


def bucket(n: int) -> int:
    out = 0
    while n > 15 and out < 31:
        n >>= 1
        out += 1
    return out


def component(name: str, page: Page) -> object:
    if name == "role":
        if page.redirect:
            return b"z"
        if page.categories:
            return b"c"
        if page.infobox:
            return b"i"
        if page.templates:
            return b"t"
        return b"x"
    if name == "title":
        return page.title_tokens
    if name == "title_head":
        return page.title_tokens[:3]
    if name == "title_tail":
        return page.title_tail
    if name == "rev_title":
        return tuple(reversed(page.title_tokens))
    if name == "cat":
        return page.categories[:5]
    if name == "cat_first":
        return page.categories[:1]
    if name == "template":
        return page.templates[:5]
    if name == "template_first":
        return page.templates[:1]
    if name == "params":
        return page.params[:6]
    if name == "links":
        return page.links[:8]
    if name == "headings":
        return page.headings[:5]
    if name == "infobox":
        return page.infobox
    if name == "redirect":
        return page.redirect
    if name == "size":
        return bucket(page.size)
    if name == "id":
        return page.page_id
    raise ValueError(name)


@dataclass(frozen=True)
class Recipe:
    name: str
    parts: tuple[str, ...]

    def key(self, page: Page) -> tuple[object, ...]:
        return tuple(component(part, page) for part in self.parts) + (page.page_id,)


BASE_RECIPES = [
    Recipe("role_cat_template_title", ("role", "cat", "template", "title")),
    Recipe("role_template_cat_tail", ("role", "template", "cat", "title_tail")),
    Recipe("role_cat_tail_template", ("role", "cat", "title_tail", "template")),
    Recipe("role_infobox_cat_title", ("role", "infobox", "cat", "title")),
    Recipe("role_template_params_cat_tail", ("role", "template", "params", "cat", "title_tail")),
    Recipe("role_links_template_cat_tail", ("role", "links", "template", "cat", "title_tail")),
    Recipe("role_headings_template_cat_title", ("role", "headings", "template", "cat", "title")),
    Recipe("role_size_template_cat_tail", ("role", "size", "template", "cat", "title_tail")),
    Recipe("role_rev_title_cat_template", ("role", "rev_title", "cat", "template")),
    Recipe("role_cat_first_template_title", ("role", "cat_first", "template", "title")),
]

PART_POOL = (
    "role",
    "cat",
    "cat_first",
    "template",
    "template_first",
    "params",
    "links",
    "headings",
    "infobox",
    "title",
    "title_head",
    "title_tail",
    "rev_title",
    "size",
)


def mutate(recipe: Recipe, rng: random.Random, index: int) -> Recipe:
    parts = list(recipe.parts)
    op = rng.choice(["swap", "replace", "insert", "delete"])
    if op == "swap" and len(parts) >= 2:
        a, b = rng.sample(range(len(parts)), 2)
        parts[a], parts[b] = parts[b], parts[a]
    elif op == "replace" and parts:
        parts[rng.randrange(len(parts))] = rng.choice(PART_POOL)
    elif op == "insert" and len(parts) < 6:
        parts.insert(rng.randrange(len(parts) + 1), rng.choice(PART_POOL))
    elif op == "delete" and len(parts) > 2:
        del parts[rng.randrange(len(parts))]
    return Recipe(f"{recipe.name}_m{index:03d}", tuple(parts))


def jaccard(a: frozenset[bytes], b: frozenset[bytes]) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def same_nonempty(a: tuple[bytes, ...], b: tuple[bytes, ...]) -> bool:
    return bool(a and b and set(a) & set(b))


def score_order(order: list[int], pages: list[Page]) -> dict[str, object]:
    if len(order) < 2:
        return {"adjacency_score": 0.0, "mean_jaccard": 0.0}
    total = 0.0
    j_total = 0.0
    cat_hits = 0
    template_hits = 0
    title_hits = 0
    size_penalty = 0.0
    for left_i, right_i in zip(order, order[1:]):
        left = pages[left_i]
        right = pages[right_i]
        jac = jaccard(left.body_tokens, right.body_tokens)
        j_total += jac
        cat = same_nonempty(left.categories, right.categories)
        tmpl = same_nonempty(left.templates, right.templates)
        title = same_nonempty(left.title_tokens, right.title_tokens)
        cat_hits += int(cat)
        template_hits += int(tmpl)
        title_hits += int(title)
        size_penalty += abs(bucket(left.size) - bucket(right.size)) / 31.0
        total += jac * 100.0
        total += 8.0 if cat else 0.0
        total += 5.0 if tmpl else 0.0
        total += 2.0 if title else 0.0
        total -= 0.5 * abs(bucket(left.size) - bucket(right.size))
    denom = len(order) - 1
    return {
        "adjacency_score": round(total, 6),
        "mean_jaccard": round(j_total / denom, 6),
        "category_neighbor_hits": cat_hits,
        "template_neighbor_hits": template_hits,
        "title_neighbor_hits": title_hits,
        "mean_size_bucket_delta": round(size_penalty / denom, 6),
    }


def run_screen(data: bytes, seed: int, mutations: int, keep: int) -> dict[str, object]:
    _head, raw_pages, _tail, pages = parse_pages(data)
    rng = random.Random(seed)
    recipes = list(BASE_RECIPES)
    for index in range(mutations):
        parent = rng.choice(recipes[: min(len(recipes), 20)])
        recipes.append(mutate(parent, rng, index))

    rows: list[dict[str, object]] = []
    seen: set[tuple[str, ...]] = set()
    for recipe in recipes:
        if recipe.parts in seen:
            continue
        seen.add(recipe.parts)
        order = sorted(range(len(pages)), key=lambda i: recipe.key(pages[i]))
        stats = score_order(order, pages)
        ordered_id_sample = [pages[i].page_id for i in order[:12]]
        digest = hashlib.sha256(
            b",".join(str(pages[i].page_id).encode() for i in order)
        ).hexdigest()
        rows.append(
            {
                "recipe": recipe.name,
                "parts": list(recipe.parts),
                "pages": len(pages),
                "raw_pages": len(raw_pages),
                "order_sha256": digest,
                "first_page_ids": ordered_id_sample,
                **stats,
            }
        )
    rows.sort(
        key=lambda row: (
            -float(row["adjacency_score"]),
            -float(row["mean_jaccard"]),
            str(row["parts"]),
        )
    )
    return {
        "seed": seed,
        "mutations": mutations,
        "pages": len(pages),
        "rows": rows[:keep],
        "best": rows[0] if rows else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--limit", type=int, default=10_000_000)
    parser.add_argument("--seed", type=int, default=923)
    parser.add_argument("--mutations", type=int, default=400)
    parser.add_argument("--keep", type=int, default=40)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    data = args.data.read_bytes()[: args.limit]
    result = run_screen(data, args.seed, args.mutations, args.keep)
    result["input_bytes"] = len(data)
    result["basis"] = "no-compression adjacency screen; use only to select exact gates"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"limit{args.limit}_seed{args.seed}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"out": str(out), "best": result["best"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
