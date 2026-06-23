#!/usr/bin/env python3
"""Train a small from-scratch hierarchical chunk embedding teacher on enwiki9.

This tool is intentionally outside the counted decompressor.  It learns compact
hashed TF-IDF embeddings from Wikipedia pages/sections/templates and clusters
them into semantic-ish buckets.  Those buckets are teacher labels: they tell us
which deterministic low-cardinality keys are worth distilling into a compressor.

No external model weights are required.  This is the local alternative to using
Gemma embeddings as an offline teacher.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Iterable

import page_order_gepa as gepa


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT = ROOT / "results" / "hierarchical_chunk_embedding_teacher" / "latest.json"
TOKEN_RE = re.compile(rb"[A-Za-z][A-Za-z0-9_-]{1,31}")
TITLE_RE = re.compile(rb"<title>(.*?)</title>", re.S | re.I)
TEXT_RE = re.compile(rb"<text[^>]*>(.*?)</text>", re.S | re.I)
ID_RE = re.compile(rb"<id>([0-9]+)</id>", re.I)
HEADING_RE = re.compile(rb"(^|\n)(={2,6})([^=\n][^\n]*?)(\2)(?=\n|$)")
TEMPLATE_RE = re.compile(rb"\{\{\s*([A-Za-z0-9 _:-]{2,64})")
CATEGORY_RE = re.compile(rb"\[\[\s*Category\s*:\s*([^\]\|]{2,96})", re.I)
LINK_RE = re.compile(rb"\[\[\s*([A-Za-z0-9 _:/.-]{2,96})(?:\||\]\])")


def split_pages(data: bytes) -> list[bytes]:
    pages: list[bytes] = []
    start = 0
    while True:
        left = data.find(b"<page>", start)
        if left < 0:
            break
        right = data.find(b"</page>", left)
        if right < 0:
            break
        right += len(b"</page>")
        pages.append(data[left:right])
        start = right
    return pages


def clean_text(value: bytes) -> str:
    return re.sub(rb"\s+", b" ", value.strip().lower()).decode("utf-8", "ignore")


def hash_token(token: str, dims: int) -> tuple[int, float]:
    h = 2166136261
    for byte in token.encode("utf-8", "ignore"):
        h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
    sign = 1.0 if (h & 0x80000000) == 0 else -1.0
    return h % dims, sign


@dataclass
class Chunk:
    page_index: int
    page_id: int
    kind: str
    title: str
    label: str
    order: int
    tokens: Counter[str] = field(default_factory=Counter)
    cheap_keys: dict[str, str] = field(default_factory=dict)


def first_match(pattern: re.Pattern[bytes], data: bytes) -> bytes:
    match = pattern.search(data)
    return match.group(1) if match else b""


def token_counts(raw: bytes, prefix: str, limit: int) -> Counter[str]:
    counts: Counter[str] = Counter()
    for i, match in enumerate(TOKEN_RE.finditer(raw.lower())):
        if i >= limit:
            break
        token = match.group(0).decode("utf-8", "ignore")
        if len(token) >= 2:
            counts[f"{prefix}{token}"] += 1
    return counts


def extract_page_chunks(page: bytes, page_index: int, max_tokens: int) -> list[Chunk]:
    title_raw = first_match(TITLE_RE, page)
    title = clean_text(title_raw) or f"page_{page_index}"
    id_raw = first_match(ID_RE, page)
    try:
        page_id = int(id_raw) if id_raw else page_index
    except ValueError:
        page_id = page_index
    text_match = TEXT_RE.search(page)
    text = text_match.group(1) if text_match else page

    title_tokens = token_counts(title_raw, "title:", max_tokens)
    categories = [clean_text(match.group(1)) for match in CATEGORY_RE.finditer(text)]
    templates = [clean_text(match.group(1)) for match in TEMPLATE_RE.finditer(text)]
    links = [clean_text(match.group(1)) for match in LINK_RE.finditer(text)]
    cheap = {
        "title_prefix": title[:3],
        "title_suffix": title[-3:],
        "category0": categories[0][:24] if categories else "",
        "template0": templates[0][:24] if templates else "",
        "template_set": "|".join(sorted(set(templates[:8]))[:4]),
    }

    chunks: list[Chunk] = []
    page_counts = token_counts(text[:8192], "body:", max_tokens)
    page_counts.update(title_tokens)
    for value in categories[:8]:
        page_counts[f"category:{value[:32]}"] += 2
    for value in templates[:16]:
        page_counts[f"template:{value[:32]}"] += 2
    for value in links[:16]:
        page_counts[f"link:{value[:32]}"] += 1
    chunks.append(
        Chunk(
            page_index=page_index,
            page_id=page_id,
            kind="page",
            title=title,
            label=title,
            order=0,
            tokens=page_counts,
            cheap_keys=cheap,
        )
    )

    spans: list[tuple[int, int, str]] = []
    headings = list(HEADING_RE.finditer(text))
    for idx, match in enumerate(headings[:24]):
        start = match.end()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        label = clean_text(match.group(3))[:80] or f"section_{idx}"
        spans.append((start, min(end, start + 4096), label))
    for idx, (start, end, label) in enumerate(spans):
        counts = token_counts(text[start:end], "section:", max_tokens // 2)
        counts.update(title_tokens)
        counts[f"heading:{label[:40]}"] += 3
        if counts:
            chunks.append(
                Chunk(
                    page_index=page_index,
                    page_id=page_id,
                    kind="section",
                    title=title,
                    label=label,
                    order=idx + 1,
                    tokens=counts,
                    cheap_keys=cheap | {"heading": label[:32]},
                )
            )
    return chunks


def document_frequency(chunks: list[Chunk]) -> Counter[str]:
    df: Counter[str] = Counter()
    for chunk in chunks:
        df.update(chunk.tokens.keys())
    return df


def dense_vector(chunk: Chunk, df: Counter[str], n_docs: int, dims: int) -> list[float]:
    vec = [0.0] * dims
    for token, count in chunk.tokens.items():
        idx, sign = hash_token(token, dims)
        idf = math.log((n_docs + 1.0) / (df[token] + 1.0)) + 1.0
        vec[idx] += sign * (1.0 + math.log(count)) * idf
    norm = math.sqrt(sum(value * value for value in vec))
    if norm:
        vec = [value / norm for value in vec]
    return vec


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def add_to(left: list[float], right: list[float]) -> None:
    for i, value in enumerate(right):
        left[i] += value


def normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vec))
    if not norm:
        return vec
    return [value / norm for value in vec]


def initial_centers(vectors: list[list[float]], k: int) -> list[list[float]]:
    if not vectors:
        return []
    centers = [vectors[0][:]]
    if k == 1:
        return centers
    step = max(1, len(vectors) // k)
    for index in range(step, len(vectors), step):
        centers.append(vectors[index][:])
        if len(centers) >= k:
            break
    while len(centers) < k:
        centers.append(vectors[len(centers) % len(vectors)][:])
    return centers


def spherical_kmeans(vectors: list[list[float]], k: int, passes: int) -> tuple[list[int], list[list[float]]]:
    centers = initial_centers(vectors, k)
    labels = [0] * len(vectors)
    for _ in range(max(1, passes)):
        sums = [[0.0] * len(vectors[0]) for _ in centers]
        counts = [0] * len(centers)
        for i, vec in enumerate(vectors):
            label = max(range(len(centers)), key=lambda c: dot(vec, centers[c]))
            labels[i] = label
            counts[label] += 1
            add_to(sums[label], vec)
        for i, total in enumerate(sums):
            if counts[i]:
                centers[i] = normalize(total)
    return labels, centers


def top_tokens_for_cluster(
    chunks: list[Chunk], labels: list[int], cluster: int, limit: int
) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for chunk, label in zip(chunks, labels):
        if label == cluster:
            counts.update(chunk.tokens)
    return counts.most_common(limit)


def cheap_key_purity(chunks: list[Chunk], labels: list[int], key_name: str) -> dict[str, float | int]:
    by_key: dict[str, Counter[int]] = defaultdict(Counter)
    for chunk, label in zip(chunks, labels):
        key = chunk.cheap_keys.get(key_name, "")
        if key:
            by_key[key][label] += 1
    if not by_key:
        return {"keys": 0, "samples": 0, "purity": 0.0}
    correct = 0
    total = 0
    for counts in by_key.values():
        total += sum(counts.values())
        correct += counts.most_common(1)[0][1]
    return {"keys": len(by_key), "samples": total, "purity": correct / total if total else 0.0}


def adjacency_score(vectors: list[list[float]], order: Iterable[int]) -> float:
    indices = list(order)
    total = 0.0
    for left, right in zip(indices, indices[1:]):
        total += dot(vectors[left], vectors[right])
    return total


def cluster_order(labels: list[int], chunks: list[Chunk]) -> list[int]:
    return sorted(range(len(chunks)), key=lambda i: (labels[i], chunks[i].page_index, chunks[i].order))


def rank_gepa_keys(
    pages: list[bytes],
    chunks: list[Chunk],
    vectors: list[list[float]],
    max_specs: int,
    top: int,
) -> list[dict[str, object]]:
    page_vectors_by_index: dict[int, list[float]] = {}
    page_ids_by_index: dict[int, int] = {}
    for chunk, vector in zip(chunks, vectors):
        if chunk.kind == "page":
            page_vectors_by_index[chunk.page_index] = vector
            page_ids_by_index[chunk.page_index] = chunk.page_id
    usable_indices = sorted(page_vectors_by_index)
    if len(usable_indices) < 2:
        return []
    local_vectors = [page_vectors_by_index[index] for index in usable_indices]
    local_pages = [pages[index] for index in usable_indices]
    local_ids = [page_ids_by_index[index] for index in usable_indices]
    features = [gepa.page_features(page, pid) for page, pid in zip(local_pages, local_ids)]
    original = list(range(len(features)))
    original_score = adjacency_score(local_vectors, original)
    rows: list[dict[str, object]] = []
    for name, fields in gepa.candidate_specs(max_specs):
        order = gepa.order_for(features, fields)
        score = adjacency_score(local_vectors, order)
        moved = sum(1 for old, new in enumerate(order) if old != new)
        rows.append(
            {
                "name": name,
                "fields": list(fields),
                "pages": len(features),
                "moved_pages": moved,
                "embedding_adjacency": score,
                "delta_vs_original": score - original_score,
                "first_ids": [features[index]["pid"] for index in order[:8]],
            }
        )
    rows.sort(key=lambda row: (row["delta_vs_original"], row["embedding_adjacency"]), reverse=True)
    return rows[:top]


def summarize_gepa_controls(rows: list[dict[str, object]]) -> dict[str, object]:
    control_names = {"geometry", "geometry_title", "geometry_suffix"}
    controls = [row for row in rows if row.get("name") in control_names]
    novel = [row for row in rows if row.get("name") not in control_names]
    best_control = controls[0] if controls else None
    best_novel = novel[0] if novel else None
    control_delta = None
    if best_control and best_novel:
        control_delta = (
            float(best_novel["delta_vs_original"])
            - float(best_control["delta_vs_original"])
        )
    return {
        "known_controls": controls,
        "best_known_control": best_control,
        "best_novel_key": best_novel,
        "best_novel_minus_best_control": control_delta,
        "promotion_rule": (
            "A novel key must beat the known geometry controls in the teacher "
            "and then improve exact archive bytes before promotion."
        ),
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    data = args.data.read_bytes()
    if args.limit > 0:
        data = data[: args.limit]
    pages = split_pages(data)
    if args.max_pages > 0:
        pages = pages[: args.max_pages]
    chunks: list[Chunk] = []
    for page_index, page in enumerate(pages):
        chunks.extend(extract_page_chunks(page, page_index, args.max_tokens_per_chunk))
        if args.max_chunks > 0 and len(chunks) >= args.max_chunks:
            chunks = chunks[: args.max_chunks]
            break
    if len(chunks) < 2:
        raise SystemExit("not enough chunks extracted")

    df = document_frequency(chunks)
    vectors = [dense_vector(chunk, df, len(chunks), args.dims) for chunk in chunks]
    labels, _centers = spherical_kmeans(vectors, min(args.clusters, len(chunks)), args.passes)
    cluster_counts = Counter(labels)
    original_order = list(range(len(chunks)))
    ordered_by_cluster = cluster_order(labels, chunks)
    original_adj = adjacency_score(vectors, original_order)
    cluster_adj = adjacency_score(vectors, ordered_by_cluster)

    purities = {
        name: cheap_key_purity(chunks, labels, name)
        for name in ("title_prefix", "title_suffix", "category0", "template0", "template_set", "heading")
    }
    cluster_rows = []
    for cluster, count in cluster_counts.most_common(args.clusters):
        examples = [
            {
                "page_id": chunk.page_id,
                "kind": chunk.kind,
                "title": chunk.title[:80],
                "label": chunk.label[:80],
            }
            for chunk, label in zip(chunks, labels)
            if label == cluster
        ][:5]
        cluster_rows.append(
            {
                "cluster": cluster,
                "chunks": count,
                "top_tokens": top_tokens_for_cluster(chunks, labels, cluster, 12),
                "examples": examples,
            }
        )

    gepa_rows = rank_gepa_keys(pages, chunks, vectors, args.max_gepa_candidates, args.top_gepa)

    return {
        "mode": "from_scratch_hierarchical_chunk_embedding_teacher",
        "input": {
            "data": str(args.data),
            "bytes_used": len(data),
            "pages": len(pages),
            "chunks": len(chunks),
            "dims": args.dims,
            "clusters": min(args.clusters, len(chunks)),
        },
        "ledger_policy": {
            "teacher_status": "offline only",
            "decoder_payload": "none from this tool",
            "distillation_required": (
                "only cheap keys with high cluster purity or residual gain should be "
                "compiled into a decompressor"
            ),
        },
        "embedding": {
            "type": "hashed tf-idf, normalized",
            "trained_on": "the provided enwiki9 slice",
            "external_model_weights": False,
        },
        "adjacency_teacher": {
            "original_cosine_total": original_adj,
            "cluster_order_cosine_total": cluster_adj,
            "delta_vs_original": cluster_adj - original_adj,
            "first_cluster_order": [
                {
                    "page_id": chunks[i].page_id,
                    "kind": chunks[i].kind,
                    "cluster": labels[i],
                    "title": chunks[i].title[:80],
                    "label": chunks[i].label[:80],
                }
                for i in ordered_by_cluster[:12]
            ],
        },
        "distillation_purity": purities,
        "gepa_distilled_keys": {
            "basis": "GEPA-compatible page-order keys ranked by from-scratch page embedding adjacency",
            "controls": summarize_gepa_controls(gepa_rows),
            "top": gepa_rows,
        },
        "clusters": cluster_rows,
        "next_step": (
            "Feed the strongest cheap key or cluster-derived ordering into exact "
            "compression gates; for predictor work, add the distilled low-cardinality "
            "cluster key to hierarchical_retrieval_shadow and require held-out gain."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--limit", type=int, default=1_000_000)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--dims", type=int, default=128)
    parser.add_argument("--clusters", type=int, default=16)
    parser.add_argument("--passes", type=int, default=4)
    parser.add_argument("--max-pages", type=int, default=0)
    parser.add_argument("--max-chunks", type=int, default=2000)
    parser.add_argument("--max-tokens-per-chunk", type=int, default=256)
    parser.add_argument("--max-gepa-candidates", type=int, default=250)
    parser.add_argument("--top-gepa", type=int, default=20)
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"missing data: {args.data}")
    if args.limit < 0:
        raise SystemExit("--limit must be non-negative")
    if args.dims <= 0 or args.clusters <= 0 or args.passes <= 0:
        raise SystemExit("--dims, --clusters, and --passes must be positive")
    if args.max_pages < 0 or args.max_chunks < 0 or args.max_tokens_per_chunk <= 0:
        raise SystemExit("invalid max-* argument")
    if args.max_gepa_candidates <= 0 or args.top_gepa <= 0:
        raise SystemExit("--max-gepa-candidates and --top-gepa must be positive")

    result = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
