#!/usr/bin/env python3
"""Assemble a balanced curated shard 04 from authored rows plus top filler rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_gold_natural_draft_shards import DEFAULT_AUTHORED, PROJECT_ROOT, _loose_key, _load_rows


DEFAULT_STRICT_POOL = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards_draft"
    / "gold_natural_draft.strict_mined_pool.jsonl"
)
DEFAULT_MANUAL_POOL = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards_draft"
    / "gold_natural_draft.review_promoted_manual.jsonl"
)
DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards_draft"
)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--authored", action="append", default=[])
    ap.add_argument("--strict-pool", default=str(DEFAULT_STRICT_POOL))
    ap.add_argument("--manual-pool", default=str(DEFAULT_MANUAL_POOL))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--prefix", default="gold_natural_curated_shard04")
    ap.add_argument("--per-pair", type=int, default=280)
    return ap.parse_args()


def _resolve(path_text: str) -> Path:
    path = Path(str(path_text).strip())
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def _sort_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            -float(row.get("draft_score", 0.0)),
            bool(row.get("draft_has_digit")),
            str(row.get("source", "")),
            str(row.get("row_id", "")),
        ),
    )


def _counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    out = {"en-es": 0, "es-en": 0}
    for row in rows:
        pair = str(row.get("pair", ""))
        if pair in out:
            out[pair] += 1
    return out


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    args = _parse_args()
    authored_paths = [_resolve(text) for text in (args.authored or [])] or list(DEFAULT_AUTHORED)
    strict_path = _resolve(str(args.strict_pool))
    manual_path = _resolve(str(args.manual_pool))
    out_dir = _resolve(str(args.out_dir))
    prefix = str(args.prefix).strip() or "gold_natural_curated_shard04"
    per_pair = int(args.per_pair)

    human_by_loose: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for path in authored_paths:
        if not path.is_file():
            continue
        for row in _load_rows(path):
            loose = _loose_key(row)
            incumbent = human_by_loose.get(loose)
            row_copy = dict(row)
            row_copy["draft_origin"] = "authored_curated"
            row_copy["draft_score"] = 200.0
            row_copy["draft_has_digit"] = False
            if incumbent is None or str(row_copy["row_id"]) < str(incumbent["row_id"]):
                human_by_loose[loose] = row_copy

    manual_rows = []
    if manual_path.is_file():
        for row in _load_rows(manual_path):
            row_copy = dict(row)
            row_copy["draft_origin"] = row_copy.get("draft_origin", "review_mined_pool")
            manual_rows.append(row_copy)

    strict_rows = []
    if strict_path.is_file():
        for row in _load_rows(strict_path):
            row_copy = dict(row)
            row_copy["draft_origin"] = row_copy.get("draft_origin", "strict_mined_pool")
            strict_rows.append(row_copy)

    selected: list[dict[str, Any]] = []
    seen = set()
    counts = {"en-es": 0, "es-en": 0}

    def try_add(row: dict[str, Any]) -> bool:
        loose = _loose_key(row)
        pair = str(row.get("pair", ""))
        if pair not in counts:
            return False
        if loose in seen:
            return False
        if counts[pair] >= per_pair:
            return False
        seen.add(loose)
        counts[pair] += 1
        selected.append(row)
        return True

    for row in _sort_rows(list(human_by_loose.values())):
        try_add(row)
    for row in _sort_rows(manual_rows):
        try_add(row)
    for row in _sort_rows(strict_rows):
        try_add(row)
        if counts["en-es"] >= per_pair and counts["es-en"] >= per_pair:
            break

    selected = _sort_rows(selected)
    out_path = out_dir / f"{prefix}.jsonl"
    summary_path = out_dir / f"{prefix}.summary.md"
    manifest_path = out_dir / f"{prefix}.manifest.json"
    _write_jsonl(out_path, selected)

    remaining = {pair: max(0, per_pair - value) for pair, value in counts.items()}
    summary_lines = [
        "# Curated Shard 04",
        "",
        f"- output: `{_safe_rel(out_path)}`",
        f"- selected_rows: `{len(selected)}`",
        f"- counts: `{counts}`",
        f"- remaining_to_target: `{remaining}`",
        f"- authored_paths: `{len([p for p in authored_paths if p.is_file()])}` files",
        "",
    ]
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    manifest = {
        "builder": _safe_rel(Path(__file__)),
        "authored_paths": [_safe_rel(path) for path in authored_paths if path.is_file()],
        "strict_pool": _safe_rel(strict_path),
        "manual_pool": _safe_rel(manual_path),
        "per_pair": per_pair,
        "selected_rows": len(selected),
        "counts": counts,
        "remaining_to_target": remaining,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[curated-shard4] out={_safe_rel(out_path)}")
    print(f"[curated-shard4] counts={counts}")
    print(f"[curated-shard4] remaining={remaining}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
