#!/usr/bin/env python3
"""
Batch driver for language-targeted vocab subsets.

Reads a JSON config (see `gamma/projects/embeddinggemma_subsets/config/subsets.json`)
and runs `gamma/tools/vocab_subset.py` for each subset.

This script intentionally shells out to the single-subset tool so the pipeline
remains usable without treating `gamma/tools/` as a Python package.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_list(value: Any, *, name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise ValueError(f"{name} must be a list of strings")
    return list(value)


def _resolve_out_dir(out_root: Path, base_model: str, tag: str, top_k: int) -> Path:
    # Keep a stable layout. Avoid slashes in HF ids.
    safe_model = base_model.replace("/", "__")
    return out_root / f"{safe_model}-{tag}-vocab{top_k}"


def _run(cmd: list[str]) -> None:
    print(f"+ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch vocab subset builder for embedding models.")
    ap.add_argument("--config", required=True, help="Path to subsets.json")
    ap.add_argument("--dry-run", action="store_true", help="Print commands but do not execute.")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    cfg = _load_json(cfg_path)

    base_model = cfg.get("base_model")
    out_root = cfg.get("out_root")
    if not isinstance(base_model, str) or not base_model:
        raise SystemExit("config.base_model must be a non-empty string")
    if not isinstance(out_root, str) or not out_root:
        raise SystemExit("config.out_root must be a non-empty string")

    defaults = cfg.get("defaults", {})
    if not isinstance(defaults, dict):
        raise SystemExit("config.defaults must be an object")

    subsets = cfg.get("subsets", [])
    if not isinstance(subsets, list) or not subsets:
        raise SystemExit("config.subsets must be a non-empty list")

    out_root_p = Path(out_root)
    out_root_p.mkdir(parents=True, exist_ok=True)

    tool = Path("gamma/tools/vocab_subset.py")
    if not tool.exists():
        raise SystemExit(f"Missing tool: {tool}")

    for entry in subsets:
        if not isinstance(entry, dict):
            raise SystemExit("Each subset entry must be an object")
        tag = entry.get("tag")
        if not isinstance(tag, str) or not tag:
            raise SystemExit("subset.tag must be a non-empty string")

        texts = entry.get("texts")
        texts = _ensure_list(texts, name=f"subset[{tag}].texts")

        top_k = int(entry.get("top_k", defaults.get("top_k", 50000)))
        min_count = int(entry.get("min_count", defaults.get("min_count", 1)))
        max_lines = entry.get("max_lines", defaults.get("max_lines", None))
        write_checkpoint = bool(entry.get("write_checkpoint", defaults.get("write_checkpoint", True)))
        also_prune_output = bool(entry.get("also_prune_output", defaults.get("also_prune_output", False)))
        dtype = str(entry.get("dtype", defaults.get("dtype", "auto")))
        fill_to_top_k = bool(entry.get("fill_to_top_k", defaults.get("fill_to_top_k", True)))
        fill_strategy = str(entry.get("fill_strategy", defaults.get("fill_strategy", "spm_score")))

        out_dir = _resolve_out_dir(out_root_p, base_model, tag, top_k)
        out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(tool),
            "--model",
            base_model,
            "--out",
            str(out_dir),
            "--top-k",
            str(top_k),
            "--min-count",
            str(min_count),
            "--dtype",
            dtype,
        ]
        if fill_to_top_k:
            cmd += ["--fill-to-top-k", "--fill-strategy", fill_strategy]
        for t in texts:
            cmd += ["--text", t]
        if max_lines is not None:
            cmd += ["--max-lines", str(int(max_lines))]
        if write_checkpoint:
            cmd += ["--write-checkpoint"]
        if also_prune_output:
            cmd += ["--also-prune-output"]

        if args.dry_run:
            print(f"(dry-run) {out_dir}")
            print(f"+ {' '.join(cmd)}")
        else:
            _run(cmd)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
