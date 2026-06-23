#!/usr/bin/env python3
"""Use precomputed page embeddings as an offline teacher for page-order keys.

The embedding model is never part of a counted decompressor.  This tool only
uses externally generated vectors to rank tiny deterministic page-order keys
that can later be packaged by fx2_gepa_order_package.py.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from typing import Any

import page_order_gepa as gepa


Vector = tuple[float, ...]


def read_json_or_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        rows: list[dict[str, Any]] = []
        with path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("rows", "pages", "embeddings"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    raise SystemExit(f"unsupported embedding file shape: {path}")


def normalize_vector(raw: Any) -> Vector:
    if not isinstance(raw, list) or not raw:
        raise ValueError("embedding must be a non-empty list")
    vals = tuple(float(x) for x in raw)
    mag = math.sqrt(sum(x * x for x in vals))
    if not mag:
        raise ValueError("embedding magnitude is zero")
    return tuple(x / mag for x in vals)


def load_embeddings(path: pathlib.Path) -> dict[int, Vector]:
    out: dict[int, Vector] = {}
    for row in read_json_or_jsonl(path):
        pid = row.get("pid", row.get("page_id", row.get("id")))
        vec = row.get("embedding", row.get("vector"))
        if pid is None or vec is None:
            continue
        try:
            out[int(pid)] = normalize_vector(vec)
        except (TypeError, ValueError):
            continue
    return out


def dot(left: Vector, right: Vector) -> float:
    return sum(a * b for a, b in zip(left, right))


def embedding_order(vectors: list[Vector], dims: int) -> list[int]:
    if not vectors:
        return []
    usable_dims = min(dims, min(len(vec) for vec in vectors))

    def key(index: int) -> tuple[int, ...]:
        vec = vectors[index]
        buckets = []
        for value in vec[:usable_dims]:
            buckets.append(max(-127, min(127, int(round(value * 127)))))
        return tuple(buckets)

    return sorted(range(len(vectors)), key=key)


def embedding_adjacency(vectors: list[Vector], order: list[int]) -> dict[str, float]:
    if len(order) < 2:
        return {"cosine_total": 0.0, "cosine_mean": 0.0}
    total = 0.0
    for left, right in zip(order, order[1:]):
        total += dot(vectors[left], vectors[right])
    return {
        "cosine_total": total,
        "cosine_mean": total / (len(order) - 1),
    }


def rank_distilled_keys(
    features: list[dict[str, Any]],
    vectors: list[Vector],
    specs: list[tuple[str, tuple[str, ...]]],
) -> list[dict[str, Any]]:
    original = list(range(len(features)))
    original_metrics = embedding_adjacency(vectors, original)
    rows: list[dict[str, Any]] = []
    for name, fields in specs:
        order = gepa.order_for(features, fields)
        metrics = embedding_adjacency(vectors, order)
        rows.append(
            {
                "name": name,
                "fields": list(fields),
                "cosine_total": metrics["cosine_total"],
                "cosine_mean": metrics["cosine_mean"],
                "delta_vs_original": metrics["cosine_total"]
                - original_metrics["cosine_total"],
                "first_ids": [features[index]["pid"] for index in order[:8]],
            }
        )
    rows.sort(key=lambda row: (row["delta_vs_original"], row["cosine_total"]), reverse=True)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=pathlib.Path("data/enwik9"))
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--embeddings", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--max-candidates", type=int, default=250)
    parser.add_argument("--teacher-dims", type=int, default=8)
    args = parser.parse_args()

    data = args.data.read_bytes()[: args.limit]
    _head, pages, _tail, ids = gepa.split_pages(data)
    if not pages:
        raise SystemExit("no pages found")
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate page ids in slice")

    all_embeddings = load_embeddings(args.embeddings)
    kept_pages: list[bytes] = []
    kept_ids: list[int] = []
    vectors: list[Vector] = []
    missing = 0
    for page, pid in zip(pages, ids):
        vec = all_embeddings.get(pid)
        if vec is None:
            missing += 1
            continue
        kept_pages.append(page)
        kept_ids.append(pid)
        vectors.append(vec)
    if len(kept_pages) < 2:
        raise SystemExit("fewer than two pages have embeddings")

    features = [gepa.page_features(page, pid) for page, pid in zip(kept_pages, kept_ids)]
    specs = gepa.candidate_specs(args.max_candidates)
    distilled = rank_distilled_keys(features, vectors, specs)
    teacher_order = embedding_order(vectors, args.teacher_dims)
    teacher_metrics = embedding_adjacency(vectors, teacher_order)
    original_metrics = embedding_adjacency(vectors, list(range(len(vectors))))

    result = {
        "input_bytes": len(data),
        "pages_in_slice": len(pages),
        "embedded_pages": len(kept_pages),
        "missing_embedding_pages": missing,
        "embedding_teacher": {
            "status": "oracle_only_not_decoder_payload",
            "order": "quantized normalized embedding dimensions",
            "teacher_dims": args.teacher_dims,
            "metrics": teacher_metrics,
            "delta_vs_original": teacher_metrics["cosine_total"]
            - original_metrics["cosine_total"],
            "first_ids": [features[index]["pid"] for index in teacher_order[:8]],
        },
        "distilled_key_scoring": {
            "basis": "GEPA-compatible deterministic page keys ranked by embedding-neighbor cosine adjacency",
            "original": original_metrics,
        },
        "top_distilled_keys": distilled[: args.top],
        "next_step": "Package a top fields row with fx2_gepa_order_package.py, then validate with gepa_validation_queue.py.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
