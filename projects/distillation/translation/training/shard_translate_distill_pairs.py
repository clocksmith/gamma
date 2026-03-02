#!/usr/bin/env python3
"""Shard a JSONL file into smaller numbered JSONL parts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _safe_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input JSONL file.")
    ap.add_argument("--out-dir", required=True, help="Output directory for shard files.")
    ap.add_argument("--rows-per-shard", type=int, default=5000, help="Rows per output shard.")
    ap.add_argument("--prefix", default="", help="Shard filename prefix. Default: input stem.")
    ap.add_argument("--start-index", type=int, default=1, help="Starting shard index.")
    ap.add_argument("--manifest-out", default="", help="Optional manifest JSON path.")
    ap.add_argument("--keep-empty", action="store_true", help="Keep empty lines (default drops them).")
    return ap.parse_args()


def _open_shard(out_dir: Path, prefix: str, idx: int):
    shard_path = out_dir / f"{prefix}.shard-{idx:05d}.jsonl"
    return shard_path, shard_path.open("w", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    in_path = Path(args.input)
    if not in_path.is_file():
        raise SystemExit(f"Input JSONL not found: {in_path}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = _safe_text(args.prefix) or in_path.stem
    rows_per_shard = max(1, int(args.rows_per_shard))
    shard_idx = max(1, int(args.start_index))

    total_rows = 0
    shard_rows = 0
    shard_files: list[dict[str, Any]] = []
    current_path = None
    current_file = None

    try:
        with in_path.open("r", encoding="utf-8") as src:
            for line in src:
                if not args.keep_empty and not line.strip():
                    continue
                if current_file is None or shard_rows >= rows_per_shard:
                    if current_file is not None:
                        current_file.close()
                        shard_files.append({"path": str(current_path), "rows": shard_rows})
                    current_path, current_file = _open_shard(out_dir, prefix, shard_idx)
                    shard_idx += 1
                    shard_rows = 0
                current_file.write(line if line.endswith("\n") else line + "\n")
                shard_rows += 1
                total_rows += 1
    finally:
        if current_file is not None:
            current_file.close()
            shard_files.append({"path": str(current_path), "rows": shard_rows})

    if total_rows == 0:
        raise SystemExit(f"No rows were written from input: {in_path}")

    manifest = {
        "input": str(in_path),
        "out_dir": str(out_dir),
        "prefix": prefix,
        "rows_per_shard": rows_per_shard,
        "total_rows": total_rows,
        "shard_count": len(shard_files),
        "shards": shard_files,
    }
    manifest_out = Path(args.manifest_out) if _safe_text(args.manifest_out) else out_dir / f"{prefix}.shards.json"
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[shard] input={in_path}")
    print(f"[shard] rows={total_rows} shard_count={len(shard_files)} rows_per_shard={rows_per_shard}")
    print(f"[shard] manifest={manifest_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
