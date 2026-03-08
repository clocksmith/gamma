#!/usr/bin/env python3
"""Build four 640-row gold-quality shards from gold core, mined rows, and authored additions."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_GOLD = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold"
    / "translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl"
)
DEFAULT_MINED = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_expansion"
    / "gold_plus_1280.exact_mined.jsonl"
)
DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
)
ROW_ID_KEYS = ("src_lang", "tgt_lang", "source", "target_pos", "target_neg")
REQUIRED_KEYS = ("src_lang", "tgt_lang", "pair", "source", "target_pos", "target_neg")


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold", default=str(DEFAULT_GOLD))
    ap.add_argument("--mined", default=str(DEFAULT_MINED))
    ap.add_argument("--authored", default="", help="Optional authored JSONL rows for the fourth hybrid shard.")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--prefix", default="gold_quality_4x640")
    ap.add_argument("--shard-size", type=int, default=640)
    return ap.parse_args()


def _resolve(path_text: str) -> Path:
    path = Path(str(path_text).strip())
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _norm_text(text: Any) -> str:
    return " ".join(str(text or "").split()).strip().casefold()


def _row_id(row: dict[str, Any]) -> str:
    parts = [_safe_text(row.get(key)) for key in ROW_ID_KEYS]
    return hashlib.sha256("\t".join(parts).encode("utf-8")).hexdigest()


def _safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            text = line.strip()
            if not text:
                continue
            obj = json.loads(text)
            if not isinstance(obj, dict):
                raise RuntimeError(f"{path}:{lineno}: expected JSON object")
            missing = [key for key in REQUIRED_KEYS if not _safe_text(obj.get(key))]
            if missing:
                raise RuntimeError(f"{path}:{lineno}: missing keys: {','.join(missing)}")
            row = dict(obj)
            row["row_id"] = _row_id(row)
            rows.append(row)
    if not rows:
        raise RuntimeError(f"no rows loaded from {path}")
    return rows


def _counts_by_pair(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("pair", "")) for row in rows).items()))


def _loose_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        _safe_text(row.get("src_lang")),
        _safe_text(row.get("tgt_lang")),
        _norm_text(row.get("source")),
        _norm_text(row.get("target_pos")),
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_row_ids(path: Path, rows: list[dict[str, Any]]) -> str:
    text = "".join(f"{row['row_id']}\n" for row in rows)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bucket_summary(rows: list[dict[str, Any]], *, jsonl_path: Path, row_ids_path: Path) -> dict[str, Any]:
    scores = [float(row.get("curation_score", 0.0)) for row in rows if row.get("curation_score") is not None]
    return {
        "rows": len(rows),
        "counts_by_pair": _counts_by_pair(rows),
        "jsonl_path": _safe_rel(jsonl_path),
        "row_ids_path": _safe_rel(row_ids_path),
        "row_ids_sha256": _write_row_ids(row_ids_path, rows),
        "score_min": round(min(scores), 4) if scores else 0.0,
        "score_avg": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "score_max": round(max(scores), 4) if scores else 0.0,
    }


def _split_gold_core(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("pair", ""))].append(row)
    shard_a: list[dict[str, Any]] = []
    shard_b: list[dict[str, Any]] = []
    for pair in sorted(grouped):
        bucket = sorted(grouped[pair], key=lambda row: str(row["row_id"]))
        for idx, row in enumerate(bucket):
            if idx % 2 == 0:
                shard_a.append(row)
            else:
                shard_b.append(row)
    shard_a.sort(key=lambda row: (str(row.get("pair", "")), str(row["row_id"])))
    shard_b.sort(key=lambda row: (str(row.get("pair", "")), str(row["row_id"])))
    return shard_a, shard_b


def _split_mined(
    rows: list[dict[str, Any]],
    *,
    shard_size: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("pair", ""))].append(row)
    primary_target = shard_size // 2
    primary: list[dict[str, Any]] = []
    tail: list[dict[str, Any]] = []
    for pair in sorted(grouped):
        bucket = sorted(
            grouped[pair],
            key=lambda row: (-float(row.get("curation_score", 0.0)), str(row["row_id"])),
        )
        primary.extend(bucket[:primary_target])
        tail.extend(bucket[primary_target:])
    primary.sort(key=lambda row: (str(row.get("pair", "")), -float(row.get("curation_score", 0.0)), str(row["row_id"])))
    tail.sort(key=lambda row: (str(row.get("pair", "")), -float(row.get("curation_score", 0.0)), str(row["row_id"])))
    tail_counts = _counts_by_pair(tail)
    authored_requirements = {
        "en-es": primary_target - int(tail_counts.get("en-es", 0)),
        "es-en": primary_target - int(tail_counts.get("es-en", 0)),
    }
    if any(value < 0 for value in authored_requirements.values()):
        raise RuntimeError(f"negative authored requirement computed: {authored_requirements}")
    return primary, tail, authored_requirements


def _validate_authored(
    rows: list[dict[str, Any]],
    *,
    required_counts: dict[str, int],
    forbidden_row_ids: set[str],
    forbidden_loose_keys: set[tuple[str, str, str, str]],
) -> list[dict[str, Any]]:
    counts = _counts_by_pair(rows)
    for pair, required in required_counts.items():
        actual = int(counts.get(pair, 0))
        if actual != int(required):
            raise RuntimeError(f"authored rows for {pair}: expected {required}, found {actual}")
    row_ids = [str(row["row_id"]) for row in rows]
    if len(set(row_ids)) != len(row_ids):
        raise RuntimeError("authored rows contain duplicate full row ids")
    overlap = sorted(set(row_ids) & forbidden_row_ids)
    if overlap:
        raise RuntimeError(f"authored rows overlap existing rows: {len(overlap)} conflicts")
    loose_keys = [_loose_key(row) for row in rows]
    if len(set(loose_keys)) != len(loose_keys):
        raise RuntimeError("authored rows contain duplicate source+target_pos translation pairs")
    loose_overlap = sorted(set(loose_keys) & forbidden_loose_keys)
    if loose_overlap:
        raise RuntimeError(f"authored rows overlap existing translation pairs: {len(loose_overlap)} conflicts")
    return sorted(rows, key=lambda row: (str(row.get("pair", "")), str(row["row_id"])))


def _summary_md(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Gold Quality Shards",
        "",
        f"Gold core: `{manifest['gold_path']}`",
        f"Mined exact: `{manifest['mined_path']}`",
        "",
        "## Shards",
        "",
        "| shard | rows | counts_by_pair | path |",
        "| --- | --- | --- | --- |",
    ]
    for key in (
        "shard_01_gold_core_a",
        "shard_02_gold_core_b",
        "shard_03_mined_exact",
        "shard_04_hybrid_seed_tail",
        "shard_04_hybrid_full",
        "train_3x640",
        "train_4x640",
    ):
        item = manifest["artifacts"].get(key) or {}
        if not item:
            continue
        lines.append(
            f"| {key} | {item.get('rows', 0)} | {json.dumps(item.get('counts_by_pair', {}), sort_keys=True)} | {item.get('jsonl_path', '')} |"
        )
    lines.extend(
        [
            "",
            "## Authored Requirement",
            "",
            f"- Required authored rows total: `{manifest['authored_requirement']['rows_total']}`",
            f"- Required `en-es`: `{manifest['authored_requirement']['counts_by_pair'].get('en-es', 0)}`",
            f"- Required `es-en`: `{manifest['authored_requirement']['counts_by_pair'].get('es-en', 0)}`",
            "",
            "The hybrid fourth shard is built as the 330-row mined tail plus authored rows sized to restore a balanced 640-row shard.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = _parse_args()
    gold_path = _resolve(str(args.gold))
    mined_path = _resolve(str(args.mined))
    authored_text = str(args.authored).strip()
    authored_path = _resolve(authored_text) if authored_text else None
    out_dir = _resolve(str(args.out_dir))
    prefix = str(args.prefix).strip() or "gold_quality_4x640"
    shard_size = int(args.shard_size)
    if shard_size <= 0 or shard_size % 2 != 0:
        raise RuntimeError("--shard-size must be a positive even integer")

    gold_rows = _load_rows(gold_path)
    mined_rows = _load_rows(mined_path)
    authored_rows = _load_rows(authored_path) if authored_path and authored_path.is_file() else []

    gold_a, gold_b = _split_gold_core(gold_rows)
    if len(gold_a) != shard_size or len(gold_b) != shard_size:
        raise RuntimeError(f"gold core did not split into two {shard_size}-row shards")
    mined_primary, mined_tail, authored_required = _split_mined(mined_rows, shard_size=shard_size)
    if len(mined_primary) != shard_size:
        raise RuntimeError(f"mined primary shard is not {shard_size} rows")

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "shard_01_gold_core_a": out_dir / f"{prefix}.shard_01_gold_core_a.jsonl",
        "shard_02_gold_core_b": out_dir / f"{prefix}.shard_02_gold_core_b.jsonl",
        "shard_03_mined_exact": out_dir / f"{prefix}.shard_03_mined_exact.jsonl",
        "shard_04_hybrid_seed_tail": out_dir / f"{prefix}.shard_04_hybrid_seed_tail.jsonl",
        "shard_04_hybrid_full": out_dir / f"{prefix}.shard_04_hybrid_full.jsonl",
        "train_3x640": out_dir / f"{prefix}.train_3x640.jsonl",
        "train_4x640": out_dir / f"{prefix}.train_4x640.jsonl",
    }
    row_id_paths = {key: path.with_suffix(".row_ids.txt") for key, path in paths.items()}

    _write_jsonl(paths["shard_01_gold_core_a"], gold_a)
    _write_jsonl(paths["shard_02_gold_core_b"], gold_b)
    _write_jsonl(paths["shard_03_mined_exact"], mined_primary)
    _write_jsonl(paths["shard_04_hybrid_seed_tail"], mined_tail)
    _write_jsonl(paths["train_3x640"], [*gold_a, *gold_b, *mined_primary])

    artifacts = {
        "shard_01_gold_core_a": _bucket_summary(gold_a, jsonl_path=paths["shard_01_gold_core_a"], row_ids_path=row_id_paths["shard_01_gold_core_a"]),
        "shard_02_gold_core_b": _bucket_summary(gold_b, jsonl_path=paths["shard_02_gold_core_b"], row_ids_path=row_id_paths["shard_02_gold_core_b"]),
        "shard_03_mined_exact": _bucket_summary(mined_primary, jsonl_path=paths["shard_03_mined_exact"], row_ids_path=row_id_paths["shard_03_mined_exact"]),
        "shard_04_hybrid_seed_tail": _bucket_summary(mined_tail, jsonl_path=paths["shard_04_hybrid_seed_tail"], row_ids_path=row_id_paths["shard_04_hybrid_seed_tail"]),
        "train_3x640": _bucket_summary([*gold_a, *gold_b, *mined_primary], jsonl_path=paths["train_3x640"], row_ids_path=row_id_paths["train_3x640"]),
    }

    forbidden_row_ids = {str(row["row_id"]) for row in [*gold_rows, *mined_rows]}
    forbidden_loose_keys = {_loose_key(row) for row in [*gold_rows, *mined_rows]}
    if authored_rows:
        authored_validated = _validate_authored(
            authored_rows,
            required_counts=authored_required,
            forbidden_row_ids=forbidden_row_ids,
            forbidden_loose_keys=forbidden_loose_keys,
        )
        hybrid_full = [*mined_tail, *authored_validated]
        hybrid_full.sort(key=lambda row: (str(row.get("pair", "")), str(row["row_id"])))
        if len(hybrid_full) != shard_size:
            raise RuntimeError(f"hybrid shard is not {shard_size} rows after authored merge")
        train_4x640 = [*gold_a, *gold_b, *mined_primary, *hybrid_full]
        _write_jsonl(paths["shard_04_hybrid_full"], hybrid_full)
        _write_jsonl(paths["train_4x640"], train_4x640)
        artifacts["shard_04_hybrid_full"] = _bucket_summary(
            hybrid_full,
            jsonl_path=paths["shard_04_hybrid_full"],
            row_ids_path=row_id_paths["shard_04_hybrid_full"],
        )
        artifacts["train_4x640"] = _bucket_summary(
            train_4x640,
            jsonl_path=paths["train_4x640"],
            row_ids_path=row_id_paths["train_4x640"],
        )

    manifest = {
        "builder": _safe_rel(Path(__file__)),
        "gold_path": _safe_rel(gold_path),
        "gold_sha256": _sha256_path(gold_path),
        "mined_path": _safe_rel(mined_path),
        "mined_sha256": _sha256_path(mined_path),
        "authored_path": _safe_rel(authored_path) if authored_path and authored_path.exists() else "",
        "shard_size": shard_size,
        "authored_requirement": {
            "rows_total": int(sum(authored_required.values())),
            "counts_by_pair": authored_required,
        },
        "artifacts": artifacts,
    }

    manifest_path = out_dir / f"{prefix}.manifest.json"
    summary_path = out_dir / f"{prefix}.summary.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _summary_md(summary_path, manifest)

    print(f"[gold-shards] manifest={_safe_rel(manifest_path)}")
    for key in (
        "shard_01_gold_core_a",
        "shard_02_gold_core_b",
        "shard_03_mined_exact",
        "shard_04_hybrid_seed_tail",
        "train_3x640",
    ):
        item = artifacts.get(key) or {}
        print(
            f"[gold-shards] artifact={key} rows={item.get('rows', 0)} "
            f"counts={json.dumps(item.get('counts_by_pair', {}), sort_keys=True)} "
            f"path={item.get('jsonl_path', '')}"
        )
    print(
        "[gold-shards] authored_required="
        + json.dumps(manifest["authored_requirement"]["counts_by_pair"], sort_keys=True)
    )
    if "shard_04_hybrid_full" in artifacts:
        print(
            f"[gold-shards] artifact=shard_04_hybrid_full rows={artifacts['shard_04_hybrid_full']['rows']} "
            f"path={artifacts['shard_04_hybrid_full']['jsonl_path']}"
        )
    print(f"[gold-shards] summary={_safe_rel(summary_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
