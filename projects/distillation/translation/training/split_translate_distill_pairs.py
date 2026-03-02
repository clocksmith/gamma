#!/usr/bin/env python3
"""Split translation distill pairs into train/eval JSONL files."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_TRANSLATE_PAIR_CANONICAL_KEYS = (
    "src_lang",
    "tgt_lang",
    "pair",
    "source",
    "target_pos",
    "target_neg",
)
REQUIRED_TRANSLATE_PAIR_COMPAT_KEYS = (
    "lang",
    "query",
    "pos",
    "neg",
)


def _safe_text(x: object | None) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _pair_key(obj: dict[str, object]) -> str:
    src_lang = _safe_text(obj.get("src_lang") or obj.get("source_lang") or obj.get("src"))
    tgt_lang = _safe_text(obj.get("tgt_lang") or obj.get("target_lang") or obj.get("tgt"))
    return f"{src_lang}-{tgt_lang}"


def _norm_text(value: object | None) -> str:
    return " ".join(_safe_text(value).split()).casefold()


def _group_key(obj: dict[str, object]) -> str:
    # Keep near-duplicate source variants in the same split bucket.
    source = _safe_text(obj.get("source") or obj.get("query"))
    return _norm_text(source)


def _contract_text(value: Any) -> str:
    return " ".join(_safe_text(value).split())


def _validate_pair_contract(
    obj: dict[str, Any],
    *,
    path: Path,
    line_no: int,
    allow_compat_mismatch: bool,
    allow_partial_contract: bool,
) -> None:
    required = REQUIRED_TRANSLATE_PAIR_CANONICAL_KEYS
    if not allow_partial_contract:
        required = REQUIRED_TRANSLATE_PAIR_CANONICAL_KEYS + REQUIRED_TRANSLATE_PAIR_COMPAT_KEYS
    missing = [k for k in required if k not in obj]
    if missing:
        raise RuntimeError(f"{path}:{line_no}: missing required keys: {missing}")

    src_lang = _contract_text(obj.get("src_lang") or obj.get("source_lang") or obj.get("src"))
    tgt_lang = _contract_text(obj.get("tgt_lang") or obj.get("target_lang") or obj.get("tgt"))
    pair = _contract_text(obj.get("pair"))
    source = _contract_text(obj.get("source"))
    target_pos = _contract_text(obj.get("target_pos") or obj.get("pos"))
    target_neg = _contract_text(obj.get("target_neg") or obj.get("neg"))
    if not src_lang or not tgt_lang or not source or not target_pos or not pair:
        raise RuntimeError(f"{path}:{line_no}: canonical translation fields contain empty values")
    expected_pair = f"{src_lang}-{tgt_lang}"
    if pair != expected_pair:
        raise RuntimeError(f"{path}:{line_no}: pair='{pair}' does not match src/tgt '{expected_pair}'")

    query = _contract_text(obj.get("query"))
    pos = _contract_text(obj.get("pos"))
    neg = _contract_text(obj.get("neg"))
    lang = _contract_text(obj.get("lang"))
    has_compat_alias = any(k in obj for k in REQUIRED_TRANSLATE_PAIR_COMPAT_KEYS)
    if has_compat_alias and not allow_compat_mismatch:
        if query and query != source:
            raise RuntimeError(f"{path}:{line_no}: source/query mismatch")
        if pos and pos != target_pos:
            raise RuntimeError(f"{path}:{line_no}: target_pos/pos mismatch")
        if target_neg and neg and neg != target_neg:
            raise RuntimeError(f"{path}:{line_no}: target_neg/neg mismatch")
        if lang and lang != tgt_lang:
            raise RuntimeError(f"{path}:{line_no}: lang='{lang}' does not match tgt_lang='{tgt_lang}'")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def _load_rows(
    paths: list[Path],
    *,
    allow_compat_mismatch: bool,
    allow_partial_contract: bool,
) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception as exc:
                    raise RuntimeError(f"{path}:{line_no}: invalid JSON row: {exc}") from exc
                if not isinstance(obj, dict):
                    raise RuntimeError(f"{path}:{line_no}: expected JSON object row")
                _validate_pair_contract(
                    obj,
                    path=path,
                    line_no=line_no,
                    allow_compat_mismatch=allow_compat_mismatch,
                    allow_partial_contract=allow_partial_contract,
                )
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
    ap.add_argument("--manifest-out", default="", help="Optional split manifest JSON output path.")
    ap.add_argument(
        "--allow-compat-mismatch",
        action="store_true",
        help="Allow source/query and target_pos/pos alias mismatches in input JSONL.",
    )
    ap.add_argument(
        "--allow-partial-contract",
        action="store_true",
        help="Allow rows that omit compatibility alias keys (lang/query/pos/neg).",
    )
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args()


def main() -> int:
    args = _parse_args()
    pair_inputs = _resolve_jsonl_inputs(str(args.pairs))
    pairs = _load_rows(
        pair_inputs,
        allow_compat_mismatch=bool(args.allow_compat_mismatch),
        allow_partial_contract=bool(args.allow_partial_contract),
    )
    if not pairs:
        raise SystemExit(f"No usable rows in {args.pairs}")

    eval_fraction = max(0.0, min(1.0, float(args.eval_fraction)))
    min_eval = max(0, int(args.min_eval_per_pair))
    max_eval = max(0, int(args.eval_max_rows))
    seed = int(args.seed)

    by_pair: dict[str, list[tuple[int, dict, str]]] = {}
    for i, row in enumerate(pairs):
        pair = _pair_key(row)
        if "-" not in pair:
            continue
        by_pair.setdefault(pair, []).append((i, row, _group_key(row)))

    rng = random.Random(seed)
    eval_indices: set[int] = set()
    pair_stats: list[dict[str, Any]] = []
    pair_requested: dict[str, int] = {}
    pair_min_required: dict[str, int] = {}

    for pair, rows in by_pair.items():
        if not rows:
            continue
        n = len(rows)
        pair_max_eval = (n - 1) if n > 1 else 0
        requested = int(round(n * eval_fraction))
        requested = max(requested, min_eval)
        requested = min(requested, pair_max_eval)
        pair_requested[pair] = max(0, requested)
        pair_min_required[pair] = min(max(0, min_eval), pair_max_eval)

    pair_budget: dict[str, int] = dict(pair_requested)
    if max_eval > 0:
        min_total = sum(pair_min_required.values())
        if max_eval < min_total:
            raise SystemExit(
                f"eval_max_rows={max_eval} is too small to satisfy min_eval_per_pair={min_eval} "
                f"across {len(pair_min_required)} language pairs (requires at least {min_total})."
            )
        pair_budget = dict(pair_min_required)
        remaining = int(max_eval - min_total)
        extras = {k: max(0, pair_requested[k] - pair_min_required[k]) for k in pair_requested}
        while remaining > 0:
            progressed = False
            for pair in sorted(extras.keys(), key=lambda p: (-extras[p], p)):
                if remaining <= 0:
                    break
                if extras[pair] <= 0:
                    continue
                pair_budget[pair] += 1
                extras[pair] -= 1
                remaining -= 1
                progressed = True
            if not progressed:
                break

    for pair, rows in by_pair.items():
        if not rows:
            continue
        n = len(rows)
        budget = max(0, min(int(pair_budget.get(pair, 0)), (n - 1) if n > 1 else 0))
        if budget <= 0:
            pair_stats.append(
                {
                    "pair": pair,
                    "rows_total": int(n),
                    "requested_eval": int(pair_requested.get(pair, 0)),
                    "final_eval": 0,
                    "partial_groups": 0,
                }
            )
            continue

        groups: dict[str, list[tuple[int, dict, str]]] = {}
        for item in rows:
            groups.setdefault(item[2], []).append(item)
        group_items = list(groups.values())
        rng.shuffle(group_items)

        selected: list[tuple[int, dict, str]] = []
        oversized: list[list[tuple[int, dict, str]]] = []
        partial_groups = 0

        for grp in group_items:
            if len(selected) >= budget:
                break
            if len(selected) + len(grp) <= budget:
                selected.extend(grp)
            else:
                oversized.append(grp)

        if len(selected) < budget:
            oversized.sort(key=len)
            for grp in oversized:
                if len(selected) >= budget:
                    break
                remaining = budget - len(selected)
                if remaining <= 0:
                    break
                if len(grp) <= remaining:
                    selected.extend(grp)
                else:
                    # Last-resort partial group fill when strict grouping cannot hit budget.
                    partial_groups += 1
                    shard = list(grp)
                    rng.shuffle(shard)
                    selected.extend(shard[:remaining])

        chosen = selected[:budget]
        eval_indices.update(i for i, _, _ in chosen)
        pair_stats.append(
            {
                "pair": pair,
                "rows_total": int(n),
                "requested_eval": int(pair_requested.get(pair, 0)),
                "final_eval": int(budget),
                "partial_groups": int(partial_groups),
            }
        )

    if max_eval > 0 and len(eval_indices) > max_eval:
        # Safety trim if future logic changes over-allocate.
        extras = sorted(eval_indices)
        rng.shuffle(extras)
        eval_indices = set(extras[:max_eval])

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

    eval_counts: dict[str, int] = {}
    for row in eval_rows:
        pair = _pair_key(row)
        eval_counts[pair] = eval_counts.get(pair, 0) + 1
    min_violations: list[dict[str, int]] = []
    for pair, min_needed in pair_min_required.items():
        observed = int(eval_counts.get(pair, 0))
        if observed < int(min_needed):
            min_violations.append(
                {
                    "pair": pair,
                    "required_min_eval": int(min_needed),
                    "observed_eval": observed,
                }
            )
    if min_violations:
        raise RuntimeError(f"eval split violated min-eval-per-pair constraints: {min_violations}")

    train_out = Path(args.train_out)
    eval_out = Path(args.eval_out)
    _write_rows(train_out, train_rows)
    _write_rows(eval_out, eval_rows)

    manifest_out = Path(args.manifest_out) if _safe_text(args.manifest_out) else train_out.with_suffix(".split_manifest.json")
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": [str(p) for p in pair_inputs],
        "input_checksums": [{"path": str(p), "sha256": _sha256_file(p)} for p in pair_inputs],
        "outputs": {
            "train_out": str(train_out),
            "eval_out": str(eval_out),
        },
        "params": {
            "eval_fraction": float(eval_fraction),
            "min_eval_per_pair": int(min_eval),
            "eval_max_rows": int(max_eval),
            "seed": int(seed),
            "allow_compat_mismatch": bool(args.allow_compat_mismatch),
            "allow_partial_contract": bool(args.allow_partial_contract),
        },
        "counts": {
            "input_rows": int(len(pairs)),
            "train_rows": int(len(train_rows)),
            "eval_rows": int(len(eval_rows)),
        },
        "checksums": {
            "train_sha256": _sha256_file(train_out),
            "eval_sha256": _sha256_file(eval_out),
        },
        "pair_stats": pair_stats,
        "pair_eval_counts": eval_counts,
        "min_eval_violations": min_violations,
    }
    manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"[split] inputs={len(pair_inputs)} files input_rows={len(pairs)} "
        f"train={len(train_rows)} eval={len(eval_rows)}"
    )
    for item in pair_stats:
        print(
            f"[split] {item['pair']}: total={item['rows_total']} requested_eval={item['requested_eval']} "
            f"final_eval={item['final_eval']} partial_groups={item['partial_groups']}"
        )
    print(f"[split] manifest={manifest_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
