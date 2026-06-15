#!/usr/bin/env python3
"""Boundary-aware reranker for GEPA page-order candidates.

The first GEPA screen rewards total adjacent-page similarity. This pass keeps
that signal, but penalizes candidates that create low-similarity edges between
otherwise dense blocks. It is still model-free; exact compression gates remain
the only promotion evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from collections import Counter
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import page_order_gepa as base  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_RESULTS_DIR = ROOT / "results" / "page_order_gepa"
DEFAULT_PROGRAMS = ROOT / "programs"
SECTION_NAMES = (
    "top_by_score",
    "diverse_top",
    "top_by_smooth",
    "top_by_boundary",
    "frontier",
    "top",
    "rows",
)


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def quantile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    index = fraction * (len(values) - 1)
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return values[low]
    weight = index - low
    return values[low] * (1.0 - weight) + values[high] * weight


def pair_values(
    features: list[dict[str, Any]],
    order: list[int],
    pair_cache: dict[tuple[int, int], float] | None = None,
) -> list[float]:
    values: list[float] = []
    for left, right in zip(order, order[1:]):
        key = (left, right)
        if pair_cache is not None and key in pair_cache:
            values.append(pair_cache[key])
            continue
        value = base.pair_score(features[left], features[right])
        if pair_cache is not None:
            pair_cache[key] = value
        values.append(value)
    return values


def key_values(
    features: list[dict[str, Any]], order: list[int], fields: tuple[str, ...], width: int
) -> list[tuple[Any, ...]]:
    selected = fields[:width]
    if not selected:
        return [() for _ in order]
    return [
        tuple(base.FEATURES[name](features[index]) for name in selected)
        for index in order
    ]


def edge_stats(
    features: list[dict[str, Any]],
    order: list[int],
    fields: tuple[str, ...],
    weak_threshold: float,
    pair_cache: dict[tuple[int, int], float] | None = None,
) -> dict[str, float]:
    values = pair_values(features, order, pair_cache)
    ordered = sorted(values)
    weak_edges = sum(1 for value in values if value < weak_threshold)
    zero_edges = sum(1 for value in values if value <= 0.0)
    tear_deficit = sum(max(0.0, weak_threshold - value) for value in values)

    primary_keys = key_values(features, order, fields, 1)
    prefix_keys = key_values(features, order, fields, 2)
    primary_break_weak = 0
    prefix_break_weak = 0
    for index, score in enumerate(values):
        if score >= weak_threshold:
            continue
        if primary_keys[index] != primary_keys[index + 1]:
            primary_break_weak += 1
        if prefix_keys[index] != prefix_keys[index + 1]:
            prefix_break_weak += 1

    return {
        "min_pair_score": ordered[0] if ordered else 0.0,
        "p01_pair_score": quantile(ordered, 0.01),
        "p05_pair_score": quantile(ordered, 0.05),
        "p10_pair_score": quantile(ordered, 0.10),
        "median_pair_score": quantile(ordered, 0.50),
        "weak_edges": float(weak_edges),
        "zero_edges": float(zero_edges),
        "tear_deficit": tear_deficit,
        "primary_break_weak_edges": float(primary_break_weak),
        "prefix_break_weak_edges": float(prefix_break_weak),
    }


def load_result_specs(paths: list[pathlib.Path]) -> dict[tuple[str, ...], dict[str, Any]]:
    specs: dict[tuple[str, ...], dict[str, Any]] = {}
    for path in paths:
        payload = load_json(path)
        if not isinstance(payload, dict):
            continue
        for section in SECTION_NAMES:
            rows = payload.get(section)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                fields = row.get("fields") or row.get("parts")
                if not isinstance(fields, list):
                    continue
                normalized = tuple(str(field) for field in fields if field in base.FEATURES)
                if len(normalized) < 2:
                    continue
                slot = specs.setdefault(
                    normalized,
                    {"fields": normalized, "sources": [], "source_hits": []},
                )
                slot["sources"].append(str(path))
                slot["source_hits"].append(
                    {
                        "source": str(path),
                        "section": section,
                        "name": row.get("name"),
                        "score_delta_vs_original": row.get("score_delta_vs_original"),
                        "adjacency_score": row.get("adjacency_score"),
                        "order_sha256": row.get("order_sha256"),
                    }
                )
    return specs


def load_meta_specs(programs: pathlib.Path) -> dict[tuple[str, ...], dict[str, Any]]:
    specs: dict[tuple[str, ...], dict[str, Any]] = {}
    for meta_path in programs.glob("*/meta.json"):
        try:
            meta = load_json(meta_path)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(meta, dict) or meta.get("family") != "fx2-gepa-order":
            continue
        fields = meta.get("order_fields")
        if not isinstance(fields, list):
            continue
        normalized = tuple(str(field) for field in fields if field in base.FEATURES)
        if len(normalized) < 2:
            continue
        specs.setdefault(normalized, {"fields": normalized, "sources": [], "source_hits": []})
        specs[normalized].setdefault("candidate_ids", []).append(meta_path.parent.name)
    return specs


def merge_specs(*groups: dict[tuple[str, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, ...], dict[str, Any]] = {}
    for group in groups:
        for fields, row in group.items():
            slot = merged.setdefault(
                fields,
                {"fields": fields, "sources": [], "source_hits": [], "candidate_ids": []},
            )
            slot["sources"].extend(row.get("sources", []))
            slot["source_hits"].extend(row.get("source_hits", []))
            slot["candidate_ids"].extend(row.get("candidate_ids", []))
    for slot in merged.values():
        slot["sources"] = sorted(set(slot["sources"]))
        slot["candidate_ids"] = sorted(set(slot["candidate_ids"]))
    return list(merged.values())


def row_for(
    features: list[dict[str, Any]],
    original_order: list[int],
    original_metrics: dict[str, float],
    original_edges: dict[str, float],
    spec: dict[str, Any],
    weak_threshold: float,
    weights: dict[str, float],
) -> dict[str, Any]:
    fields = tuple(spec["fields"])
    order = base.order_for(features, fields)
    restored = sorted(order, key=lambda index: features[index]["pid"])
    if restored != original_order:
        raise SystemExit(f"{fields}: restore-by-id check failed")

    metrics = base.score_order(features, order)
    edges = edge_stats(features, order, fields, weak_threshold)
    adjacency_delta = metrics["adjacency_score"] - original_metrics["adjacency_score"]
    tear_delta = original_edges["tear_deficit"] - edges["tear_deficit"]
    weak_edge_delta = original_edges["weak_edges"] - edges["weak_edges"]
    p05_delta = edges["p05_pair_score"] - original_edges["p05_pair_score"]
    p10_delta = edges["p10_pair_score"] - original_edges["p10_pair_score"]
    boundary_penalty = edges["prefix_break_weak_edges"] + 0.5 * edges["primary_break_weak_edges"]
    smooth_objective = (
        adjacency_delta
        + weights["tear"] * tear_delta
        + weights["weak_edge"] * weak_edge_delta
        + weights["p05"] * p05_delta
        + weights["p10"] * p10_delta
        - weights["boundary"] * boundary_penalty
    )

    return {
        "name": "boundary__" + "__".join(fields),
        "fields": list(fields),
        "candidate_ids": spec.get("candidate_ids", []),
        "source_count": len(spec.get("source_hits", [])),
        "sources": spec.get("sources", []),
        "source_hits": spec.get("source_hits", [])[:8],
        "pages": len(features),
        "moved_pages": sum(1 for old, new in enumerate(order) if old != new),
        "first_ids": [features[index]["pid"] for index in order[:10]],
        "adjacency_score": metrics["adjacency_score"],
        "score_delta_vs_original": adjacency_delta,
        "topic_runs": metrics["topic_runs"],
        "mean_pair_score": metrics["mean_pair_score"],
        **edges,
        "tear_deficit_delta_vs_original": tear_delta,
        "weak_edge_delta_vs_original": weak_edge_delta,
        "p05_delta_vs_original": p05_delta,
        "p10_delta_vs_original": p10_delta,
        "boundary_penalty": boundary_penalty,
        "smooth_objective": smooth_objective,
    }


def default_result_paths(results_dir: pathlib.Path) -> list[pathlib.Path]:
    return sorted(
        path
        for path in results_dir.glob("*.json")
        if path.name.startswith(("hybrid_", "feature_", "limit"))
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    data = args.data.read_bytes()[: args.limit]
    head, pages, tail, ids = base.split_pages(data)
    if not pages:
        raise SystemExit("no pages found")
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate page ids in slice")

    features = [base.page_features(page, pid) for page, pid in zip(pages, ids)]
    original_order = list(range(len(features)))
    original_metrics = base.score_order(features, original_order)
    original_edges = edge_stats(features, original_order, (), args.weak_threshold)

    result_paths = args.result_json or default_result_paths(args.results_dir)
    specs = merge_specs(
        load_result_specs(result_paths),
        load_meta_specs(args.programs) if args.include_meta else {},
    )

    base_specs: list[dict[str, Any]] = []
    if args.include_base_specs:
        for name, fields in base.SEEDS:
            base_specs.append(
                {
                    "fields": fields,
                    "sources": ["page_order_gepa.SEEDS"],
                    "source_hits": [{"source": "page_order_gepa.SEEDS", "name": name}],
                    "candidate_ids": [],
                }
            )
    rows = [
        row_for(
            features,
            original_order,
            original_metrics,
            original_edges,
            spec,
            args.weak_threshold,
            {
                "tear": args.tear_weight,
                "weak_edge": args.weak_edge_weight,
                "p05": args.p05_weight,
                "p10": args.p10_weight,
                "boundary": args.boundary_weight,
            },
        )
        for spec in merge_specs({tuple(spec["fields"]): spec for spec in specs}, {tuple(spec["fields"]): spec for spec in base_specs})
    ]
    rows.sort(key=lambda row: (row["smooth_objective"], row["score_delta_vs_original"]), reverse=True)

    return {
        "input_bytes": len(data),
        "pages": len(pages),
        "head": len(head),
        "tail": len(tail),
        "weak_threshold": args.weak_threshold,
        "weights": {
            "tear": args.tear_weight,
            "weak_edge": args.weak_edge_weight,
            "p05": args.p05_weight,
            "p10": args.p10_weight,
            "boundary": args.boundary_weight,
        },
        "basis": (
            "Model-free GEPA boundary rerank; smooth_objective penalizes low-similarity "
            "page edges and still requires exact compression validation."
        ),
        "source_files": [str(path) for path in result_paths],
        "candidate_count": len(rows),
        "kind_counts": {
            key.decode("ascii", "replace"): value
            for key, value in Counter(feature["kind"] for feature in features).items()
        },
        "original": {**original_metrics, **original_edges},
        "top_by_smooth": rows[: args.top],
        "top_by_adjacency": sorted(
            rows,
            key=lambda row: (row["score_delta_vs_original"], row["adjacency_score"]),
            reverse=True,
        )[: args.top],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--limit", type=int, default=10_000_000)
    parser.add_argument("--result-json", action="append", type=pathlib.Path, default=[])
    parser.add_argument("--results-dir", type=pathlib.Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--programs", type=pathlib.Path, default=DEFAULT_PROGRAMS)
    parser.add_argument("--top", type=int, default=40)
    parser.add_argument("--weak-threshold", type=float, default=1.0)
    parser.add_argument("--tear-weight", type=float, default=2.0)
    parser.add_argument("--weak-edge-weight", type=float, default=4.0)
    parser.add_argument("--p05-weight", type=float, default=80.0)
    parser.add_argument("--p10-weight", type=float, default=40.0)
    parser.add_argument("--boundary-weight", type=float, default=1.0)
    parser.add_argument("--include-base-specs", action="store_true")
    parser.add_argument("--include-meta", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--out", type=pathlib.Path)
    args = parser.parse_args()

    if args.top <= 0:
        raise SystemExit("--top must be positive")
    if args.weak_threshold < 0:
        raise SystemExit("--weak-threshold must be non-negative")

    result = run(args)
    if args.out is None:
        args.out = args.results_dir / f"boundary_limit{args.limit}.json"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "best_smooth": result["top_by_smooth"][:5],
                "best_adjacency": result["top_by_adjacency"][:5],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
