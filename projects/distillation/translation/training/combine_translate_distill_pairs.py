#!/usr/bin/env python3
"""Combine one or more JSONL shards/files into a single JSONL file."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


def _safe_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _resolve_jsonl_inputs(specs: list[str]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for spec in specs:
        raw = _safe_text(spec)
        if not raw:
            continue
        parts = [p.strip() for p in raw.split(",") if p.strip()]
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
                    raise RuntimeError(f"Input path is not a file or directory: {part}")
                else:
                    raise RuntimeError(f"Input path does not exist: {part}")
            for m in matches:
                key = str(m.resolve())
                if key in seen:
                    continue
                seen.add(key)
                out.append(m)
    if not out:
        raise RuntimeError("No JSONL inputs were resolved.")
    return out


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input spec (repeatable): .jsonl file, directory of .jsonl shards, glob, or comma list.",
    )
    ap.add_argument("--out", required=True, help="Output combined JSONL path.")
    ap.add_argument("--manifest-out", default="", help="Optional manifest JSON path.")
    ap.add_argument("--dedupe-lines", action="store_true", help="Drop duplicate lines by exact text match.")
    ap.add_argument("--keep-empty", action="store_true", help="Keep empty lines (default drops them).")
    return ap.parse_args()


def main() -> int:
    args = _parse_args()
    inputs = _resolve_jsonl_inputs(list(args.input))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    seen_lines: set[str] = set()
    total_in = 0
    total_out = 0
    per_file: list[dict[str, Any]] = []

    with out_path.open("w", encoding="utf-8") as out:
        for in_path in inputs:
            in_rows = 0
            kept_rows = 0
            with in_path.open("r", encoding="utf-8") as src:
                for line in src:
                    if not args.keep_empty and not line.strip():
                        continue
                    in_rows += 1
                    total_in += 1
                    if args.dedupe_lines:
                        key = line.rstrip("\n")
                        if key in seen_lines:
                            continue
                        seen_lines.add(key)
                    out.write(line if line.endswith("\n") else line + "\n")
                    kept_rows += 1
                    total_out += 1
            per_file.append({"path": str(in_path), "rows_in": in_rows, "rows_out": kept_rows})

    manifest = {
        "inputs": [str(p) for p in inputs],
        "output": str(out_path),
        "dedupe_lines": bool(args.dedupe_lines),
        "rows_in": total_in,
        "rows_out": total_out,
        "files": per_file,
    }
    manifest_out = Path(args.manifest_out) if _safe_text(args.manifest_out) else out_path.with_suffix(".combine_manifest.json")
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[combine] input_files={len(inputs)} rows_in={total_in} rows_out={total_out}")
    print(f"[combine] output={out_path}")
    print(f"[combine] manifest={manifest_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
