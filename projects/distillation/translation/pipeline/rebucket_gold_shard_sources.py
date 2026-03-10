#!/usr/bin/env python3
"""Deduplicate listed shard sources and emit balanced 320-row packs with quality in the filename."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from build_gold_natural_draft_shards import (
    PROJECT_ROOT,
    _gold_stats,
    _load_rows,
    _loose_key,
    _naturalness,
    _norm_text,
)
from score_translation_pair_datasets import (
    DEFAULT_GOLD,
    _analyze_dataset,
    _clip_0_100,
    _score_from_rate,
)


DEFAULT_INPUTS = [
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.train_3x640.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.train_4x640.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_03_mined_exact.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_04_hybrid_full.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_04_hybrid_seed_tail.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_gapfill_best_12_round3.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_gapfill_best_15_round2.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_gapfill_best_16.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_gapfill_best_18_round4.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_goldlike_32.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_goldlike_50.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_additional_en_es_52.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_balanced_310.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_current_258.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_310.jsonl",
    "projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.authored_overflow_es_en_52.jsonl",
    "projects/distillation/translation/training_data/gold_shards_draft/gold_natural_recommended.train_3x640.jsonl",
    "projects/distillation/translation/training_data/gold_shards_draft/gold_natural_curated_shard04.jsonl",
    "projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.human_pool.jsonl",
    "projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.review_promoted_manual.jsonl",
    "projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.review_queue.jsonl",
    "projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_03_draft_full.jsonl",
    "projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_04_seed.jsonl",
    "projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_04_seed_plus_manual.jsonl",
    "projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.strict_mined_pool.jsonl",
]

DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards_rebucketed"
)

YEAR_RE = re.compile(r"\b20\d{2}\b")
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")
MONTH_OR_WEEKDAY_RE = re.compile(
    r"\b("
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo"
    r")\b",
    re.IGNORECASE,
)
DIGITS_RE = re.compile(r"\d+(?:\.\d+)?")
PLACEHOLDER_RE = re.compile(r"\bdocument_\d+\b", re.IGNORECASE)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", action="append", default=[])
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--prefix", default="gold_rebucketed_320")
    ap.add_argument("--pack-size", type=int, default=320)
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


def _canonical_row(row: dict[str, Any]) -> dict[str, Any]:
    src_lang = str(row.get("src_lang", "")).strip()
    tgt_lang = str(row.get("tgt_lang", "")).strip()
    return {
        "src_lang": src_lang,
        "tgt_lang": tgt_lang,
        "pair": str(row.get("pair") or f"{src_lang}-{tgt_lang}").strip(),
        "source": str(row.get("source", "")).strip(),
        "target_pos": str(row.get("target_pos", "")).strip(),
        "target_neg": str(row.get("target_neg", row.get("neg", ""))).strip(),
    }


def _source_tier(rel_path: str) -> int:
    name = rel_path.replace("\\", "/")
    if "shard_01_gold_core_a" in name or "shard_02_gold_core_b" in name:
        return 1000
    if "gold_natural_curated_shard04" in name:
        return 970
    if "gold_natural_recommended.train_3x640" in name or "gold_natural_draft.shard_03_draft_full" in name:
        return 950
    if "gold_natural_draft.human_pool" in name or ".authored_" in name or "review_promoted_manual" in name:
        return 930
    if "strict_mined_pool" in name:
        return 840
    if "shard_03_mined_exact" in name:
        return 760
    if "shard_04_hybrid_full" in name or "shard_04_hybrid_seed_tail" in name:
        return 700
    if "review_queue" in name or "shard_04_seed" in name or "shard_04_seed_plus_manual" in name:
        return 660
    if ".train_" in name:
        return 620
    return 500


def _source_frame(text: str) -> str:
    return DIGITS_RE.sub("<NUM>", _norm_text(text))


def _row_penalty(row: dict[str, Any], frame_count: int) -> float:
    combo = f"{row.get('source', '')} {row.get('target_pos', '')}"
    penalty = 0.0
    if any(ch.isdigit() for ch in combo):
        penalty += 6.0
    if TIME_RE.search(combo):
        penalty += 10.0
    if YEAR_RE.search(combo):
        penalty += 10.0
    if MONTH_OR_WEEKDAY_RE.search(combo):
        penalty += 6.0
    if ";" in combo:
        penalty += 5.0
    if PLACEHOLDER_RE.search(combo):
        penalty += 20.0
    if frame_count > 1:
        penalty += min(12.0, 1.5 * (frame_count - 1))
    return penalty


def _sort_key(row: dict[str, Any]) -> tuple[float, str, str]:
    payload = row.get("row", row)
    return (
        -float(row["row_quality"]),
        str(payload["source"]),
        str(payload["target_pos"]),
    )


def _interleave_rows(en_rows: list[dict[str, Any]], es_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    limit = max(len(en_rows), len(es_rows))
    for idx in range(limit):
        if idx < len(en_rows):
            out.append(en_rows[idx])
        if idx < len(es_rows):
            out.append(es_rows[idx])
    return out


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _general_pack_report(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    analysis = _analyze_dataset(rows)
    scores = analysis["scores"]
    diag = analysis["metrics"]
    template_hygiene = _clip_0_100(
        0.35 * _score_from_rate(1.0 - float(diag["digit_row_ratio"]), good=1.0, bad=0.70)
        + 0.15 * _score_from_rate(1.0 - float(diag["time_marker_ratio"]), good=1.0, bad=0.97)
        + 0.15 * _score_from_rate(1.0 - float(diag["date_word_row_ratio"]), good=1.0, bad=0.97)
        + 0.10 * _score_from_rate(1.0 - float(diag["semicolon_row_ratio"]), good=1.0, bad=0.97)
        + 0.25 * _score_from_rate(float(diag["reasonable_length_ratio"]), good=0.99, bad=0.80)
    )
    overall = _clip_0_100(
        0.35 * float(scores["alignment_quality"])
        + 0.25 * float(scores["duplication_hygiene"])
        + 0.20 * float(scores["diversity"])
        + 0.20 * float(template_hygiene)
    )
    return {
        "dataset_name": path.stem,
        "path": _safe_rel(path),
        "rows": analysis["rows"],
        "counts_by_pair": analysis["counts_by_pair"],
        "scores": {
            "overall": round(overall, 4),
            "alignment_quality": round(float(scores["alignment_quality"]), 4),
            "duplication_hygiene": round(float(scores["duplication_hygiene"]), 4),
            "diversity": round(float(scores["diversity"]), 4),
            "template_hygiene": round(float(template_hygiene), 4),
        },
        "diagnostics": {
            key: round(float(value), 4)
            for key, value in analysis["metrics"].items()
            if key
            in {
                "exact_unique_ratio",
                "source_unique_ratio",
                "target_unique_ratio",
                "digit_row_ratio",
                "time_marker_ratio",
                "semicolon_row_ratio",
                "date_word_row_ratio",
                "reasonable_length_ratio",
                "direction_balance_score",
            }
        },
    }


def main() -> int:
    args = _parse_args()
    input_paths = [_resolve(item) for item in (args.input or DEFAULT_INPUTS)]
    out_dir = _resolve(str(args.out_dir))
    prefix = str(args.prefix).strip() or "gold_rebucketed_320"
    pack_size = int(args.pack_size)
    if pack_size <= 0 or pack_size % 2:
        raise RuntimeError("--pack-size must be a positive even number")
    per_pair = pack_size // 2

    for path in input_paths:
        if not path.is_file():
            raise RuntimeError(f"input file not found: {path}")

    gold_rows = _load_rows(DEFAULT_GOLD)
    gold_stats = _gold_stats(gold_rows)

    raw_candidates: list[dict[str, Any]] = []
    frame_counter: Counter[str] = Counter()
    for path in input_paths:
        rel = _safe_rel(path)
        tier = _source_tier(rel)
        for row in _load_rows(path):
            canonical = _canonical_row(row)
            frame = _source_frame(canonical["source"])
            frame_counter[frame] += 1
            raw_candidates.append(
                {
                    "row": canonical,
                    "source_file": rel,
                    "source_tier": tier,
                    "frame": frame,
                }
            )

    deduped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for candidate in raw_candidates:
        row = candidate["row"]
        frame_count = int(frame_counter[candidate["frame"]])
        naturalness = float(_naturalness(row, gold_stats))
        quality = round(candidate["source_tier"] + naturalness - _row_penalty(row, frame_count), 4)
        ranked = {
            "row": row,
            "source_file": candidate["source_file"],
            "source_tier": candidate["source_tier"],
            "frame": candidate["frame"],
            "frame_count": frame_count,
            "naturalness": naturalness,
            "row_quality": quality,
        }
        loose = _loose_key(row)
        incumbent = deduped.get(loose)
        if incumbent is None or float(ranked["row_quality"]) > float(incumbent["row_quality"]):
            deduped[loose] = ranked

    winners = list(deduped.values())
    by_pair = {"en-es": [], "es-en": []}
    for item in winners:
        pair = str(item["row"]["pair"])
        if pair in by_pair:
            by_pair[pair].append(item)

    for pair in by_pair:
        by_pair[pair].sort(key=_sort_key)

    full_pack_count = min(len(by_pair["en-es"]) // per_pair, len(by_pair["es-en"]) // per_pair)

    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{prefix}.pack_*.jsonl"):
        old.unlink()
    for old in out_dir.glob(f"{prefix}.pack_*.tmp.jsonl"):
        old.unlink()
    for old in out_dir.glob(f"{prefix}.remainder.jsonl"):
        old.unlink()
    manifests: list[dict[str, Any]] = []

    for idx in range(full_pack_count):
        en_slice = by_pair["en-es"][idx * per_pair : (idx + 1) * per_pair]
        es_slice = by_pair["es-en"][idx * per_pair : (idx + 1) * per_pair]
        ordered = _interleave_rows(en_slice, es_slice)
        canonical_rows = [item["row"] for item in ordered]
        temp_path = out_dir / f"{prefix}.pack_{idx + 1:02d}.rows{pack_size}.tmp.jsonl"
        _write_jsonl(temp_path, canonical_rows)
        report = _general_pack_report(temp_path, canonical_rows)
        overall = float(report["scores"]["overall"] or 0.0)
        manifests.append(
            {
                "selection_index": idx + 1,
                "temp_path": _safe_rel(temp_path),
                "rows": len(canonical_rows),
                "counts_by_pair": dict(sorted(Counter(row["pair"] for row in canonical_rows).items())),
                "quality_overall": round(overall, 4),
                "alignment_quality": report["scores"]["alignment_quality"],
                "duplication_hygiene": report["scores"]["duplication_hygiene"],
                "diversity": report["scores"]["diversity"],
                "template_hygiene": report["scores"]["template_hygiene"],
                "top_source_files": dict(Counter(item["source_file"] for item in ordered).most_common(10)),
                "avg_row_quality": round(sum(float(item["row_quality"]) for item in ordered) / len(ordered), 4),
                "avg_naturalness": round(sum(float(item["naturalness"]) for item in ordered) / len(ordered), 4),
                "diagnostics": report["diagnostics"],
            }
        )

    manifests.sort(key=lambda item: float(item["quality_overall"]), reverse=True)
    for idx, item in enumerate(manifests, start=1):
        temp_path = _resolve(item.pop("temp_path"))
        score_tag = f"{float(item['quality_overall']):.4f}".replace(".", "_")
        final_path = out_dir / f"{prefix}.pack_{idx:02d}.q{score_tag}.rows{pack_size}.jsonl"
        temp_path.rename(final_path)
        item["pack_index"] = idx
        item["path"] = _safe_rel(final_path)

    used_counts = {"en-es": full_pack_count * per_pair, "es-en": full_pack_count * per_pair}
    remainder_rows = _interleave_rows(
        by_pair["en-es"][used_counts["en-es"] :],
        by_pair["es-en"][used_counts["es-en"] :],
    )
    remainder_path = out_dir / f"{prefix}.remainder.jsonl"
    if remainder_rows:
        _write_jsonl(remainder_path, [item["row"] for item in remainder_rows if isinstance(item, dict) and "row" in item])

    manifest_path = out_dir / f"{prefix}.manifest.json"
    summary_md_path = out_dir / f"{prefix}.summary.md"
    score_csv_path = out_dir / f"{prefix}.packs.csv"

    manifest = {
        "builder": _safe_rel(Path(__file__)),
        "inputs": [_safe_rel(path) for path in input_paths],
        "raw_candidate_rows": len(raw_candidates),
        "deduped_unique_rows": len(winners),
        "counts_by_pair_after_dedupe": {
            "en-es": len(by_pair["en-es"]),
            "es-en": len(by_pair["es-en"]),
        },
        "pack_size": pack_size,
        "per_pair": per_pair,
        "full_pack_count": full_pack_count,
        "remainder_counts": {
            "en-es": len(by_pair["en-es"]) - used_counts["en-es"],
            "es-en": len(by_pair["es-en"]) - used_counts["es-en"],
        },
        "packs": manifests,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Rebucketed Gold Shard Packs",
        "",
        f"- inputs: `{len(input_paths)}` files",
        f"- raw_candidate_rows: `{len(raw_candidates)}`",
        f"- deduped_unique_rows: `{len(winners)}`",
        f"- counts_by_pair_after_dedupe: `{manifest['counts_by_pair_after_dedupe']}`",
        f"- emitted_full_packs: `{full_pack_count}`",
        f"- remainder_counts: `{manifest['remainder_counts']}`",
        "",
        "## Packs",
        "",
        "| pack | overall | rows | counts | path |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in manifests:
        lines.append(
            f"| {item['pack_index']} | {item['quality_overall']} | {item['rows']} | "
            f"`{json.dumps(item['counts_by_pair'], sort_keys=True)}` | `{item['path']}` |"
        )
    summary_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    _write_csv(
        score_csv_path,
        manifests,
        [
            "pack_index",
            "path",
            "rows",
            "quality_overall",
            "alignment_quality",
            "duplication_hygiene",
            "diversity",
            "template_hygiene",
            "avg_row_quality",
            "avg_naturalness",
        ],
    )

    print(f"[rebucket] packs={full_pack_count}")
    print(f"[rebucket] manifest={_safe_rel(manifest_path)}")
    print(f"[rebucket] summary={_safe_rel(summary_md_path)}")
    if remainder_rows:
        print(f"[rebucket] remainder={_safe_rel(remainder_path)}")
    for item in manifests:
        print(f"[rebucket-pack] idx={item['pack_index']} overall={item['quality_overall']:.4f} path={item['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
