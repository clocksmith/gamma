#!/usr/bin/env python3
"""Combine one or more JSONL shards/files into a single JSONL file."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
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


def _safe_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


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
    return ap.parse_args()


def main() -> int:
    args = _parse_args()
    inputs = _resolve_jsonl_inputs(list(args.input))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    seen_lines: set[str] = set()
    total_in = 0
    total_out = 0
    total_deduped = 0
    per_file: list[dict[str, Any]] = []

    with out_path.open("w", encoding="utf-8") as out:
        for in_path in inputs:
            in_rows = 0
            kept_rows = 0
            deduped_rows = 0
            with in_path.open("r", encoding="utf-8") as src:
                for line_no, line in enumerate(src, start=1):
                    if not args.keep_empty and not line.strip():
                        continue
                    in_rows += 1
                    total_in += 1
                    try:
                        obj = json.loads(line)
                    except Exception as exc:
                        raise RuntimeError(f"{in_path}:{line_no}: invalid JSON row: {exc}") from exc
                    if not isinstance(obj, dict):
                        raise RuntimeError(f"{in_path}:{line_no}: expected JSON object row")
                    _validate_pair_contract(
                        obj,
                        path=in_path,
                        line_no=line_no,
                        allow_compat_mismatch=bool(args.allow_compat_mismatch),
                        allow_partial_contract=bool(args.allow_partial_contract),
                    )
                    if args.dedupe_lines:
                        key = line.rstrip("\n")
                        if key in seen_lines:
                            deduped_rows += 1
                            total_deduped += 1
                            continue
                        seen_lines.add(key)
                    out.write(line if line.endswith("\n") else line + "\n")
                    kept_rows += 1
                    total_out += 1
            per_file.append(
                {
                    "path": str(in_path),
                    "rows_in": in_rows,
                    "rows_out": kept_rows,
                    "rows_deduped": deduped_rows,
                    "sha256": _sha256_file(in_path),
                }
            )

    manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": [str(p) for p in inputs],
        "output": str(out_path),
        "dedupe_lines": bool(args.dedupe_lines),
        "allow_compat_mismatch": bool(args.allow_compat_mismatch),
        "allow_partial_contract": bool(args.allow_partial_contract),
        "rows_in": total_in,
        "rows_out": total_out,
        "rows_deduped": total_deduped,
        "output_sha256": _sha256_file(out_path),
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
