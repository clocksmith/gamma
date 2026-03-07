#!/usr/bin/env python3
"""Restore the exact March 3, 2026 legacy 1280 dataset as an immutable gold artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
SOURCE_COMMIT = "b8f685aa1590cd02df8467914f5764943a59b7f5"
SOURCE_PATH = Path("projects/distillation/translation/training_data/translate_distill_pairs.jsonl")
DEFAULT_OUT = PROJECT_ROOT / "projects" / "distillation" / "translation" / "training_data" / "gold" / "translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl"
GOLD_LABEL = "Gold Legacy 1280"


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", default=SOURCE_COMMIT)
    ap.add_argument("--source-path", default=str(SOURCE_PATH))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--force", action="store_true", help="Overwrite the output file if it already exists with different contents.")
    return ap.parse_args()


def _git_show(repo_root: Path, commit: str, relpath: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{commit}:{relpath}"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "failed to restore legacy gold dataset\n"
            f"commit={commit}\n"
            f"path={relpath}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc.stdout


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _analyze_jsonl(text: str) -> dict[str, Any]:
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not rows:
        raise RuntimeError("restored gold dataset is empty")
    counts_by_pair = Counter(f"{row.get('src_lang', '')}-{row.get('tgt_lang', '')}" for row in rows)
    return {
        "rows": len(rows),
        "counts_by_pair": dict(sorted(counts_by_pair.items())),
        "avg_source_chars": round(sum(len(str(row.get("source", ""))) for row in rows) / len(rows), 4),
        "avg_target_pos_chars": round(sum(len(str(row.get("target_pos", ""))) for row in rows) / len(rows), 4),
        "avg_target_neg_chars": round(sum(len(str(row.get("target_neg", ""))) for row in rows) / len(rows), 4),
        "source_langs": sorted({str(row.get("src_lang", "")) for row in rows if str(row.get("src_lang", "")).strip()}),
        "target_langs": sorted({str(row.get("tgt_lang", "")) for row in rows if str(row.get("tgt_lang", "")).strip()}),
    }


def _write_text(path: Path, text: str, *, force: bool) -> tuple[str, bool]:
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "created"
    changed = False
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if current == text:
            return "unchanged", False
        if not force:
            raise RuntimeError(
                f"output already exists with different contents: {path}\n"
                "re-run with --force to overwrite it with the exact gold snapshot"
            )
        status = "overwritten"
        changed = True
    else:
        changed = True
    path.write_text(text, encoding="utf-8")
    return status, changed


def main() -> int:
    args = _parse_args()
    commit = str(args.commit).strip()
    relpath = str(args.source_path).strip()
    out_path = Path(str(args.out).strip())
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path

    text = _git_show(PROJECT_ROOT, commit, relpath)
    stats = _analyze_jsonl(text)
    sha256 = _sha256_text(text)
    data_status, _ = _write_text(out_path, text, force=bool(args.force))

    summary = {
        "dataset_label": GOLD_LABEL,
        "dataset_tier": "gold",
        "dataset_family": "legacy_1280",
        "notes": (
            "Exact snapshot of the legacy 1280 training set used by the strong March 3, 2026 run. "
            "Preserve this file as immutable provenance."
        ),
        "source_commit": commit,
        "source_path": relpath,
        "restored_path": str(out_path.relative_to(PROJECT_ROOT)),
        "sha256": sha256,
        "stats": stats,
    }
    summary_path = out_path.with_suffix(".summary.json")
    summary_status, _ = _write_text(
        summary_path,
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        force=True,
    )

    print(
        f"[gold-dataset] status={data_status} label={GOLD_LABEL} rows={stats['rows']} "
        f"path={out_path.relative_to(PROJECT_ROOT)} sha256={sha256}"
    )
    print(f"[gold-dataset] summary={summary_path.relative_to(PROJECT_ROOT)} summary_status={summary_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
