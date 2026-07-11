#!/usr/bin/env python3
"""Score deterministic page-order keys against the upstream embedding order."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import page_order_gepa as gepa


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_ORDER = (
    ROOT
    / "external"
    / "fx2-cmix"
    / "src"
    / "readalike_prepr"
    / "data"
    / "new_article_order"
)


def is_redirect(page: bytes) -> bool:
    text = gepa.field(page, rb'<text[^>]*>(.*?)</text>') or page
    prefix = text.lstrip()[:64].lower()
    return prefix.startswith(b"#redirect") or prefix.startswith(b"{{softredirect")


def teacher_ranks(path: pathlib.Path) -> dict[int, int]:
    ranks: dict[int, int] = {}
    for rank, line in enumerate(path.read_text().splitlines()):
        try:
            ordinal = int(line)
        except ValueError:
            continue
        if ordinal not in ranks:
            ranks[ordinal] = rank
    return ranks


def metrics(order: list[int], ranks: list[int]) -> dict[str, float | int]:
    if len(order) < 2:
        return {
            "pairs": 0,
            "mean_teacher_rank_distance": 0.0,
            "teacher_neighbor_recall_at_8": 0.0,
            "teacher_neighbor_recall_at_32": 0.0,
            "teacher_exact_adjacency": 0.0,
        }
    distances = [abs(ranks[left] - ranks[right]) for left, right in zip(order, order[1:])]
    pairs = len(distances)
    return {
        "pairs": pairs,
        "mean_teacher_rank_distance": sum(distances) / pairs,
        "teacher_neighbor_recall_at_8": sum(value <= 8 for value in distances) / pairs,
        "teacher_neighbor_recall_at_32": sum(value <= 32 for value in distances) / pairs,
        "teacher_exact_adjacency": sum(value == 1 for value in distances) / pairs,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    with args.data.open("rb") as handle:
        data = handle.read(args.limit)
    _head, pages, _tail, ids = gepa.split_pages(data)
    ranks_by_ordinal = teacher_ranks(args.article_order)

    kept_pages: list[bytes] = []
    kept_ids: list[int] = []
    ranks: list[int] = []
    nonredirect_ordinal = 0
    for page, page_id in zip(pages, ids):
        if is_redirect(page):
            continue
        rank = ranks_by_ordinal.get(nonredirect_ordinal)
        nonredirect_ordinal += 1
        if rank is None:
            continue
        kept_pages.append(page)
        kept_ids.append(page_id)
        ranks.append(rank)

    features = [
        gepa.page_features(page, page_id)
        for page, page_id in zip(kept_pages, kept_ids)
    ]
    rows: list[dict[str, Any]] = []
    for name, fields in gepa.candidate_specs(args.max_candidates):
        order = gepa.order_for(features, fields)
        row = {"name": name, "fields": list(fields), **metrics(order, ranks)}
        row["first_ids"] = [kept_ids[index] for index in order[:8]]
        rows.append(row)
    rows.sort(
        key=lambda row: (
            -float(row["teacher_neighbor_recall_at_32"]),
            float(row["mean_teacher_rank_distance"]),
        )
    )
    by_name = {row["name"]: row for row in rows}
    geometry = by_name.get("geometry")
    for row in rows:
        if geometry is None:
            row["mean_distance_delta_vs_geometry"] = None
            row["recall_at_32_delta_vs_geometry"] = None
            continue
        row["mean_distance_delta_vs_geometry"] = (
            float(row["mean_teacher_rank_distance"])
            - float(geometry["mean_teacher_rank_distance"])
        )
        row["recall_at_32_delta_vs_geometry"] = (
            float(row["teacher_neighbor_recall_at_32"])
            - float(geometry["teacher_neighbor_recall_at_32"])
        )

    return {
        "receipt_type": "article_order_teacher_distillation",
        "evidence_level": "offline_teacher_only",
        "data_bytes": len(data),
        "pages": len(pages),
        "nonredirect_pages_scored": len(kept_pages),
        "teacher": {
            "path": str(args.article_order),
            "rows": len(ranks_by_ordinal),
            "provenance": "Voyage embeddings -> t-SNE 1D -> k-means -> manual strata",
            "payload_rule": "teacher order is not available to the final decoder unless counted",
        },
        "promotion_rule": (
            "a distilled key must beat geometry on the model-free adjacency proxy; "
            "teacher-neighborhood deltas diagnose mechanism but do not veto an exact "
            "fx2 gate because the geometry baseline already beats the shipped teacher order"
        ),
        "top": rows[: args.top],
        "geometry": geometry,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--article-order", type=pathlib.Path, default=DEFAULT_ORDER)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--max-candidates", type=int, default=250)
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    result = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
