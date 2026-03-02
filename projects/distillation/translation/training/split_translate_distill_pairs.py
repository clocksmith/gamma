#!/usr/bin/env python3
"""Split translation distill pairs into train/eval JSONL files."""

from __future__ import annotations

import argparse
import glob
import json
import random
from pathlib import Path


def _safe_text(x: object | None) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _pair_key(obj: dict[str, object]) -> str:
    src_lang = _safe_text(obj.get("src_lang") or obj.get("source_lang") or obj.get("src"))
    tgt_lang = _safe_text(obj.get("tgt_lang") or obj.get("target_lang") or obj.get("tgt"))
    return f"{src_lang}-{tgt_lang}"


def _resolve_jsonl_inputs(spec: str) -> list[Path]:
    raw = _safe_text(spec)
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        return []

    out: list[Path] = []
    seen: set[str] = set()
    for part in parts:
        matches: list[Path] = []
        if any(ch in part for ch in "*?["):
            matches = [Path(p) for p in sorted(glob.glob(part))]
        else:
            p = Path(part)
            if p.is_dir():
                matches = sorted(x for x in p.iterdir() if x.is_file() and x.suffix == ".jsonl")
            elif p.is_file():
                matches = [p]
            elif p.exists():
                raise RuntimeError(f"--pairs path is not a file or directory: {part}")
            else:
                raise RuntimeError(f"--pairs path does not exist: {part}")
        for m in matches:
            key = str(m.resolve())
            if key in seen:
                continue
            seen.add(key)
            out.append(m)
    if not out:
        raise RuntimeError(
            f"--pairs resolved to zero JSONL files from: {spec}. "
            "Provide a .jsonl file, a directory containing .jsonl shards, or a glob."
        )
    return out


def _load_rows(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if not isinstance(obj, dict):
                    continue
                if _safe_text(obj.get("source")) and _safe_text(obj.get("target_pos") or obj.get("pos")):
                    rows.append(obj)
    return rows


def _write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--pairs",
        required=True,
        help=(
            "Input pair data: .jsonl file, directory of .jsonl shards, "
            "glob pattern, or comma-separated list of those."
        ),
    )
    ap.add_argument("--train-out", required=True, help="Output train JSONL.")
    ap.add_argument("--eval-out", required=True, help="Output eval JSONL.")
    ap.add_argument("--eval-fraction", type=float, default=0.1, help="Eval split fraction.")
    ap.add_argument("--eval-max-rows", type=int, default=0, help="Hard max eval rows (0 = no limit).")
    ap.add_argument("--min-eval-per-pair", type=int, default=0, help="Minimum eval rows per source-target pair.")
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args()


def main() -> int:
    args = _parse_args()
    pair_inputs = _resolve_jsonl_inputs(str(args.pairs))
    pairs = _load_rows(pair_inputs)
    if not pairs:
        raise SystemExit(f"No usable rows in {args.pairs}")

    eval_fraction = max(0.0, min(1.0, float(args.eval_fraction)))
    min_eval = max(0, int(args.min_eval_per_pair))
    max_eval = max(0, int(args.eval_max_rows))
    seed = int(args.seed)

    by_pair: dict[str, list[tuple[int, dict]]] = {}
    for i, row in enumerate(pairs):
        pair = _pair_key(row)
        if "-" not in pair:
            continue
        by_pair.setdefault(pair, []).append((i, row))

    rng = random.Random(seed)
    eval_indices: set[int] = set()
    pair_stats: list[tuple[str, int, int]] = []

    for pair, rows in by_pair.items():
        if not rows:
            continue
        rng.shuffle(rows)
        n = len(rows)
        requested = int(round(n * eval_fraction))
        requested = max(requested, min_eval)
        requested = min(requested, n - 1) if n > 1 else 0
        requested = min(requested, n)
        # Keep the split stable and deterministic by using a per-run seed.
        pair_eval = rows[:requested]
        eval_indices.update(i for i, _ in pair_eval)
        pair_stats.append((pair, n, len(pair_eval)))

    if max_eval > 0 and len(eval_indices) > max_eval:
        extras = list(eval_indices)
        rng.shuffle(extras)
        keep = set(extras[:max_eval])
        eval_indices = keep

    train_rows: list[dict] = []
    eval_rows: list[dict] = []
    for i, row in enumerate(pairs):
        if i in eval_indices:
            eval_rows.append(row)
        else:
            train_rows.append(row)

    if not eval_rows:
        # Ensure at least one eval row when split fraction was too small.
        if pairs:
            eval_rows.append(pairs[-1])
            train_rows = pairs[:-1]

    _write_rows(Path(args.train_out), train_rows)
    _write_rows(Path(args.eval_out), eval_rows)

    print(f"[split] inputs={len(pair_inputs)} files input_rows={len(pairs)} train={len(train_rows)} eval={len(eval_rows)}")
    for pair, total, ev in pair_stats:
        print(f"[split] {pair}: total={total} eval={ev}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
