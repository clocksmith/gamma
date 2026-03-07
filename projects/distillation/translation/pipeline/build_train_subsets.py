#!/usr/bin/env python3
"""Build nested reproducible train subsets from a canonical translation JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


REQUIRED_KEYS = (
    "src_lang",
    "tgt_lang",
    "source",
    "target_pos",
    "target_neg",
)
ROW_ID_KEYS = (
    "src_lang",
    "tgt_lang",
    "source",
    "target_pos",
    "target_neg",
)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _row_pair(obj: dict[str, Any]) -> str:
    pair = _safe_text(obj.get("pair"))
    if pair:
        return pair
    src = _safe_text(obj.get("src_lang"))
    tgt = _safe_text(obj.get("tgt_lang"))
    return f"{src}-{tgt}" if src and tgt else ""


def _row_id(obj: dict[str, Any]) -> str:
    parts = []
    for key in ROW_ID_KEYS:
        parts.append(_safe_text(obj.get(key)))
    return hashlib.sha256("\t".join(parts).encode("utf-8")).hexdigest()


def _parse_sizes(value: str) -> list[int]:
    out: list[int] = []
    for raw in str(value).split(","):
        text = raw.strip()
        if not text:
            continue
        size = int(text)
        if size <= 0:
            raise ValueError(f"subset sizes must be positive: {text}")
        out.append(size)
    if not out:
        raise ValueError("at least one subset size is required")
    return sorted(set(out))


def _allocate_equal_counts(target_size: int, grouped: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    strata = sorted(grouped)
    if not strata:
        raise RuntimeError("cannot allocate equal counts across zero strata")
    if target_size % len(strata) != 0:
        raise RuntimeError(
            f"requested size {target_size} is not divisible by stratum count {len(strata)} for exact_equal mode"
        )
    per_stratum = target_size // len(strata)
    counts: dict[str, int] = {}
    for stratum in strata:
        available = len(grouped[stratum])
        if per_stratum > available:
            raise RuntimeError(
                f"requested {per_stratum} rows for stratum {stratum}, but only {available} are available"
            )
        counts[stratum] = per_stratum
    return counts


def _load_rows(path: Path, stratify_key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_row_ids: set[str] = set()
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            text = line.strip()
            if not text:
                continue
            obj = json.loads(text)
            if not isinstance(obj, dict):
                raise RuntimeError(f"line {lineno}: expected JSON object")
            missing = [key for key in REQUIRED_KEYS if not _safe_text(obj.get(key))]
            if missing:
                raise RuntimeError(f"line {lineno}: missing required keys: {','.join(missing)}")
            obj = dict(obj)
            obj["pair"] = _row_pair(obj)
            row_id = _row_id(obj)
            if row_id in seen_row_ids:
                raise RuntimeError(f"line {lineno}: duplicate row_id detected: {row_id}")
            seen_row_ids.add(row_id)
            obj["row_id"] = row_id
            stratum = _safe_text(obj.get(stratify_key))
            if not stratum:
                raise RuntimeError(f"line {lineno}: missing stratify key: {stratify_key}")
            obj["_stratum"] = stratum
            rows.append(obj)
    if not rows:
        raise RuntimeError(f"no rows loaded from {path}")
    return rows


def _shuffle_by_stratum(rows: list[dict[str, Any]], seed: int) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["_stratum"])].append(row)
    for stratum in sorted(grouped):
        rng = random.Random(f"{seed}:{stratum}")
        rng.shuffle(grouped[stratum])
    return dict(grouped)


def _allocate_counts(target_size: int, grouped: dict[str, list[dict[str, Any]]], allocation_mode: str) -> dict[str, int]:
    if allocation_mode == "exact_equal":
        return _allocate_equal_counts(target_size, grouped)
    total_rows = sum(len(rows) for rows in grouped.values())
    if target_size > total_rows:
        raise RuntimeError(f"requested size {target_size} exceeds universe size {total_rows}")

    exact: dict[str, float] = {}
    counts: dict[str, int] = {}
    used = 0
    for stratum, rows in grouped.items():
        share = (target_size * len(rows)) / float(total_rows)
        exact[stratum] = share
        base = int(math.floor(share))
        counts[stratum] = base
        used += base

    remainder = target_size - used
    ordering = sorted(
        grouped.keys(),
        key=lambda key: (exact[key] - counts[key], -len(grouped[key]), key),
        reverse=True,
    )
    for stratum in ordering:
        if remainder <= 0:
            break
        if counts[stratum] >= len(grouped[stratum]):
            continue
        counts[stratum] += 1
        remainder -= 1

    if remainder != 0:
        raise RuntimeError(f"failed to allocate subset size {target_size}; remainder={remainder}")
    return counts


def _subset_basename(universe: Path, size: int, seed: int) -> str:
    stem = universe.name
    if stem.endswith(".jsonl"):
        stem = stem[:-6]
    return f"{stem}.subset_{size}.seed{seed}"


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            clean = {k: v for k, v in row.items() if not k.startswith("_")}
            fh.write(json.dumps(clean, ensure_ascii=True) + "\n")


def _write_row_ids(path: Path, row_ids: list[str]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(f"{row_id}\n" for row_id in row_ids)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_subsets(
    universe_path: Path,
    out_dir: Path,
    sizes: list[int],
    seed: int,
    stratify_key: str,
    allocation_mode: str,
) -> dict[str, Any]:
    rows = _load_rows(universe_path, stratify_key=stratify_key)
    grouped = _shuffle_by_stratum(rows, seed=seed)
    universe_sha256 = _sha256_path(universe_path)

    overall_manifest: dict[str, Any] = {
        "universe_path": str(universe_path),
        "universe_sha256": universe_sha256,
        "universe_rows": len(rows),
        "seed": int(seed),
        "stratify_key": str(stratify_key),
        "allocation_mode": str(allocation_mode),
        "strata": {key: len(value) for key, value in sorted(grouped.items())},
        "subsets": [],
    }

    previous_name = ""
    for size in sizes:
        counts = _allocate_counts(size, grouped, allocation_mode=allocation_mode)
        selected: list[dict[str, Any]] = []
        for stratum in sorted(grouped):
            selected.extend(grouped[stratum][: counts[stratum]])
        selected.sort(key=lambda row: str(row["row_id"]))

        base = _subset_basename(universe_path, size=size, seed=seed)
        subset_path = out_dir / f"{base}.jsonl"
        row_ids_path = out_dir / f"{base}.row_ids.txt"
        manifest_path = out_dir / f"{base}.manifest.json"

        _write_jsonl(subset_path, selected)
        row_ids = [str(row["row_id"]) for row in selected]
        row_ids_sha256 = _write_row_ids(row_ids_path, row_ids)

        manifest = {
            "universe_path": str(universe_path),
            "universe_sha256": universe_sha256,
            "subset_path": str(subset_path),
            "subset_rows": len(selected),
            "seed": int(seed),
            "stratify_key": str(stratify_key),
            "allocation_mode": str(allocation_mode),
            "counts_by_stratum": {key: counts[key] for key in sorted(counts)},
            "row_ids_path": str(row_ids_path),
            "row_ids_sha256": row_ids_sha256,
            "parent_subset": previous_name,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        overall_manifest["subsets"].append(
            {
                "name": base,
                "size": len(selected),
                "subset_path": str(subset_path),
                "manifest_path": str(manifest_path),
                "row_ids_path": str(row_ids_path),
                "parent_subset": previous_name,
            }
        )
        previous_name = base

    return overall_manifest


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build nested reproducible train subsets from a canonical universe JSONL.")
    ap.add_argument(
        "--universe",
        default="projects/distillation/translation/training_data/translate_distill_pairs_en_es_2way.train.merged.jsonl",
        help="Canonical universe JSONL file.",
    )
    ap.add_argument(
        "--out-dir",
        default="projects/distillation/translation/training_data/subsets",
        help="Directory for subset JSONL files and manifests.",
    )
    ap.add_argument(
        "--sizes",
        required=True,
        help="Comma-separated subset sizes, for example: 1280,2048,4096",
    )
    ap.add_argument("--seed", type=int, default=42, help="Sampling seed.")
    ap.add_argument("--stratify-key", default="pair", help="Row key used for stratified sampling.")
    ap.add_argument(
        "--allocation-mode",
        default="proportional",
        choices=["proportional", "exact_equal"],
        help="How to allocate subset size across strata.",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    universe_path = Path(args.universe)
    out_dir = Path(args.out_dir)
    sizes = _parse_sizes(args.sizes)

    overall_manifest = build_subsets(
        universe_path=universe_path,
        out_dir=out_dir,
        sizes=sizes,
        seed=int(args.seed),
        stratify_key=str(args.stratify_key),
        allocation_mode=str(args.allocation_mode),
    )

    overall_manifest_path = out_dir / f"{universe_path.stem}.subsets.seed{int(args.seed)}.manifest.json"
    overall_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    overall_manifest_path.write_text(json.dumps(overall_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[subsets] universe={universe_path}")
    print(f"[subsets] overall_manifest={overall_manifest_path}")
    for subset in overall_manifest["subsets"]:
        print(f"[subsets] size={subset['size']} path={subset['subset_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
