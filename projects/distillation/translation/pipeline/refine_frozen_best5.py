#!/usr/bin/env python3
"""Audit and refine the frozen best-5 shard mix with controlled row-pruning variants."""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from build_gold_natural_draft_shards import (
    PROJECT_ROOT,
    _gold_stats,
    _load_rows,
    _loose_key,
    _naturalness,
    _norm_text,
    _row_id,
    _safe_text,
    _source_key,
)
from rebucket_gold_shard_sources import _canonical_row, _row_penalty, _source_frame, _source_tier


DEFAULT_RUN_ROOT = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "runs"
    / "translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_confirm_best5"
)
DEFAULT_REBUCKET_MANIFEST = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards_rebucketed"
    / "gold_rebucketed_320.manifest.json"
)
DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "frozen_best5_refine"
)
DEFAULT_GOLD = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold"
    / "translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl"
)

PACK_RE = re.compile(r"pack_(\d{2})")
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
PLACEHOLDER_RE = re.compile(r"\bdocument_\d+\b", re.IGNORECASE)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    ap.add_argument("--rebucket-manifest", default=str(DEFAULT_REBUCKET_MANIFEST))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--prefix", default="frozen_best5")
    ap.add_argument("--target-pack", action="append", default=["04", "06"])
    ap.add_argument("--prune-fraction", type=float, default=0.10)
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args()


def _resolve(path_text: str | Path) -> Path:
    path = Path(str(path_text).strip())
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def _pack_id_from_path(path: str | Path) -> str:
    match = PACK_RE.search(str(path))
    if not match:
        raise RuntimeError(f"cannot infer pack id from path: {path}")
    return match.group(1)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    canonical = _canonical_row(out)
    out.update(canonical)
    out["row_id"] = _row_id(out)
    return out


def _terminal_punctuation_mismatch(row: dict[str, Any]) -> bool:
    source = _safe_text(row.get("source"))
    target = _safe_text(row.get("target_pos"))
    if not source or not target:
        return False
    src_last = source[-1]
    tgt_last = target[-1]
    if src_last == "?":
        return tgt_last != "?"
    if src_last == "!":
        return tgt_last != "!"
    if src_last == ".":
        return tgt_last not in ".!?"
    return False


def _has_copied_source(row: dict[str, Any]) -> bool:
    return _norm_text(row.get("source")) == _norm_text(row.get("target_pos"))


def _flag_keys(row: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for key, value in row.items():
        text = str(key).lower()
        if not any(token in text for token in ("flag", "blocked", "reject", "admin", "hitl")):
            continue
        if value in ("", None, False, 0, "0", "false", "False"):
            continue
        keys.append(str(key))
    return sorted(keys)


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


def _write_row_ids(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(f"{row['row_id']}\n" for row in rows), encoding="utf-8")


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_selected_dataset(run_root: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    sources_path = run_root / "inputs" / "train_pairs.rows1600.merged.jsonl.sources.json"
    if not sources_path.is_file():
        raise RuntimeError(f"frozen best-5 sources manifest not found: {sources_path}")
    data = _read_json(sources_path)
    rows: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    by_pack: dict[str, list[dict[str, Any]]] = defaultdict(list)
    order_index = 0
    for source_entry in data.get("sources", []):
        source_path = _resolve(source_entry.get("path", ""))
        pack_id = _pack_id_from_path(source_path)
        for row in _load_rows(source_path):
            normalized = _normalize_row(row)
            payload = {
                "row": normalized,
                "row_id": normalized["row_id"],
                "pack_id": pack_id,
                "source_path": str(source_path),
                "order_index": order_index,
            }
            rows.append(payload)
            by_id[payload["row_id"]] = payload
            by_pack[pack_id].append(payload)
            order_index += 1
    return rows, by_id, by_pack


def _build_lineage_pool(rebucket_manifest_path: Path) -> dict[str, Any]:
    manifest = _read_json(rebucket_manifest_path)
    input_paths = [_resolve(path) for path in manifest.get("inputs", [])]
    gold_rows = _load_rows(DEFAULT_GOLD)
    gold_stats = _gold_stats(gold_rows)

    raw_candidates: list[dict[str, Any]] = []
    exact_counts: Counter[str] = Counter()
    loose_counts: Counter[tuple[str, str, str, str]] = Counter()
    source_counts: Counter[tuple[str, str, str]] = Counter()
    frame_counts: Counter[str] = Counter()

    for path in input_paths:
        rel = _safe_rel(path)
        tier = _source_tier(rel)
        for row in _load_rows(path):
            payload = _normalize_row(row)
            frame = _source_frame(payload["source"])
            raw_candidates.append(
                {
                    "row": payload,
                    "source_file": rel,
                    "source_tier": tier,
                    "frame": frame,
                }
            )
            exact_counts[payload["row_id"]] += 1
            loose_counts[_loose_key(payload)] += 1
            source_counts[_source_key(payload)] += 1
            frame_counts[frame] += 1

    winners_by_loose: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    winners_by_source: dict[tuple[str, str, str], dict[str, Any]] = {}
    winners_by_row_id: dict[str, dict[str, Any]] = {}
    for candidate in raw_candidates:
        row = candidate["row"]
        frame_count = int(frame_counts[candidate["frame"]])
        naturalness = float(_naturalness(row, gold_stats))
        row_quality = round(candidate["source_tier"] + naturalness - _row_penalty(row, frame_count), 4)
        upstream_score = row.get("curation_score")
        if upstream_score is None:
            upstream_score = row.get("draft_score")
        ranked = {
            "row": row,
            "row_id": row["row_id"],
            "source_file": candidate["source_file"],
            "source_tier": candidate["source_tier"],
            "frame": candidate["frame"],
            "frame_count": frame_count,
            "naturalness": naturalness,
            "row_quality": row_quality,
            "upstream_score": None if upstream_score is None else float(upstream_score),
            "upstream_flags": _flag_keys(row),
            "draft_origin": _safe_text(row.get("draft_origin")),
        }
        loose = _loose_key(row)
        incumbent = winners_by_loose.get(loose)
        if incumbent is None or float(ranked["row_quality"]) > float(incumbent["row_quality"]):
            winners_by_loose[loose] = ranked
        source_key = _source_key(row)
        incumbent = winners_by_source.get(source_key)
        if incumbent is None or float(ranked["row_quality"]) > float(incumbent["row_quality"]):
            winners_by_source[source_key] = ranked
        by_id = winners_by_row_id.get(row["row_id"])
        if by_id is None or float(ranked["row_quality"]) > float(by_id["row_quality"]):
            winners_by_row_id[row["row_id"]] = ranked

    pack_meta = {
        _pack_id_from_path(item["path"]): item
        for item in manifest.get("packs", [])
        if isinstance(item, dict) and item.get("path")
    }

    return {
        "manifest": manifest,
        "winners_by_row_id": winners_by_row_id,
        "winners_by_loose": winners_by_loose,
        "winners_by_source": winners_by_source,
        "winners": list(winners_by_loose.values()),
        "exact_counts": exact_counts,
        "loose_counts": loose_counts,
        "source_counts": source_counts,
        "frame_counts": frame_counts,
        "pack_meta": pack_meta,
    }


def _audit_row(
    row: dict[str, Any],
    *,
    pack_id: str,
    lineage: dict[str, Any],
) -> dict[str, Any]:
    winner = lineage["winners_by_row_id"].get(row["row_id"])
    if winner is None:
        winner = lineage["winners_by_loose"].get(_loose_key(row))
    if winner is None:
        winner = lineage["winners_by_source"].get(_source_key(row))
    frame = _source_frame(row["source"])
    exact_count = int(lineage["exact_counts"].get(row["row_id"], 1))
    loose_count = int(lineage["loose_counts"].get(_loose_key(row), 1))
    source_count = int(lineage["source_counts"].get(_source_key(row), 1))
    frame_count = int(lineage["frame_counts"].get(frame, 1))
    naturalness = float(winner["naturalness"]) if winner else 0.0
    row_quality = float(winner["row_quality"]) if winner else 0.0
    source_tier = int(winner["source_tier"]) if winner else 0
    upstream_score = winner.get("upstream_score") if winner else None
    upstream_flags = winner.get("upstream_flags", []) if winner else []
    source_file = winner.get("source_file", "") if winner else ""
    source_len = len(_safe_text(row.get("source")))
    target_len = len(_safe_text(row.get("target_pos")))
    ratio = max(source_len, target_len, 1) / max(1, min(source_len, target_len))
    has_digit = bool(re.search(r"\d", f"{row['source']} {row['target_pos']}"))
    has_time = bool(TIME_RE.search(f"{row['source']} {row['target_pos']}"))
    has_year = bool(YEAR_RE.search(f"{row['source']} {row['target_pos']}"))
    has_date_word = bool(MONTH_OR_WEEKDAY_RE.search(f"{row['source']} {row['target_pos']}"))
    has_semicolon = ";" in f"{row['source']} {row['target_pos']}"
    has_placeholder = bool(PLACEHOLDER_RE.search(f"{row['source']} {row['target_pos']}"))
    punctuation_mismatch = _terminal_punctuation_mismatch(row)
    copied_source = _has_copied_source(row)

    cluster_penalty = max(0, exact_count - 1) * 2.0
    cluster_penalty += max(0, loose_count - 1) * 4.0
    cluster_penalty += max(0, source_count - 1) * 4.0
    cluster_penalty += max(0, frame_count - 1) * 0.5

    template_penalty = 0.0
    template_penalty += 12.0 if has_digit else 0.0
    template_penalty += 10.0 if has_time else 0.0
    template_penalty += 10.0 if has_year else 0.0
    template_penalty += 6.0 if has_date_word else 0.0
    template_penalty += 6.0 if has_semicolon else 0.0
    template_penalty += 15.0 if has_placeholder else 0.0

    length_penalty = max(0.0, (ratio - 1.35) * 18.0)
    length_penalty += max(0.0, (100.0 - naturalness) * 0.25)

    punctuation_penalty = 10.0 if punctuation_mismatch else 0.0
    punctuation_penalty += 18.0 if copied_source else 0.0

    lineage_penalty = max(0.0, (980.0 - float(source_tier)) * 0.03)
    if upstream_score is not None:
        lineage_penalty += max(0.0, (95.0 - float(upstream_score)) * 0.35)
    lineage_penalty += 6.0 * len(upstream_flags)

    prune_score = round(
        cluster_penalty + template_penalty + length_penalty + punctuation_penalty + lineage_penalty,
        4,
    )
    return {
        "pack_id": pack_id,
        "pair": row["pair"],
        "row_id": row["row_id"],
        "source_file": source_file,
        "source_tier": source_tier,
        "draft_origin": winner.get("draft_origin", "") if winner else "",
        "upstream_score": "" if upstream_score is None else round(float(upstream_score), 4),
        "upstream_flags": ",".join(upstream_flags),
        "source_len": source_len,
        "target_len": target_len,
        "length_ratio": round(ratio, 4),
        "naturalness": round(naturalness, 4),
        "row_quality": round(row_quality, 4),
        "exact_count": exact_count,
        "loose_count": loose_count,
        "source_count": source_count,
        "frame_count": frame_count,
        "has_digit": int(has_digit),
        "has_time": int(has_time),
        "has_year": int(has_year),
        "has_date_word": int(has_date_word),
        "has_semicolon": int(has_semicolon),
        "has_placeholder": int(has_placeholder),
        "punctuation_mismatch": int(punctuation_mismatch),
        "copied_source": int(copied_source),
        "cluster_penalty": round(cluster_penalty, 4),
        "template_penalty": round(template_penalty, 4),
        "length_penalty": round(length_penalty, 4),
        "punctuation_penalty": round(punctuation_penalty, 4),
        "lineage_penalty": round(lineage_penalty, 4),
        "prune_score": prune_score,
        "source": row["source"],
        "target_pos": row["target_pos"],
    }


def _counts_to_remove(rows: list[dict[str, Any]], fraction: float) -> dict[str, int]:
    counts = Counter(str(item["row"]["pair"]) for item in rows)
    out: dict[str, int] = {}
    for pair, count in sorted(counts.items()):
        target = int(round(float(count) * float(fraction)))
        if float(fraction) > 0 and target == 0 and count > 0:
            target = 1
        out[pair] = min(target, count)
    return out


def _pick_prune_rows(audits: list[dict[str, Any]], counts_by_pair: dict[str, int]) -> list[str]:
    selected: list[str] = []
    for pair, count in sorted(counts_by_pair.items()):
        rows = [row for row in audits if row["pair"] == pair]
        rows.sort(key=lambda row: (-float(row["prune_score"]), row["row_id"]))
        selected.extend(row["row_id"] for row in rows[:count])
    return selected


def _pick_random_rows(rows: list[dict[str, Any]], counts_by_pair: dict[str, int], *, seed: int, pack_id: str) -> list[str]:
    picked: list[str] = []
    rng = random.Random(int(seed) + int(pack_id))
    for pair, count in sorted(counts_by_pair.items()):
        pool = sorted(
            [item["row_id"] for item in rows if str(item["row"]["pair"]) == pair],
            key=str,
        )
        if count > len(pool):
            raise RuntimeError(f"random control requested {count} rows from {pack_id}/{pair}, only {len(pool)} available")
        picked.extend(rng.sample(pool, count))
    return picked


def _select_replacements(
    *,
    target_pack_id: str,
    counts_by_pair: dict[str, int],
    selected_by_id: dict[str, dict[str, Any]],
    removal_ids: set[str],
    lineage: dict[str, Any],
) -> list[dict[str, Any]]:
    dominant_sources = set(lineage["pack_meta"].get(target_pack_id, {}).get("top_source_files", {}).keys())
    kept_ids = set(selected_by_id) - set(removal_ids)
    kept_loose = {_loose_key(item["row"]) for row_id, item in selected_by_id.items() if row_id in kept_ids}
    kept_source = {_source_key(item["row"]) for row_id, item in selected_by_id.items() if row_id in kept_ids}

    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in lineage["winners"]:
        row = candidate["row"]
        row_id = row["row_id"]
        if row_id in selected_by_id:
            continue
        if _loose_key(row) in kept_loose:
            continue
        if _source_key(row) in kept_source:
            continue
        source_bonus = 50.0 if candidate["source_file"] in dominant_sources else 0.0
        if candidate.get("upstream_score") is not None:
            source_bonus += min(25.0, float(candidate["upstream_score"]) * 0.1)
        rank_score = round(source_bonus + float(candidate["row_quality"]), 4)
        by_pair[str(row["pair"])].append(
            {
                "row": row,
                "row_id": row_id,
                "source_file": candidate["source_file"],
                "rank_score": rank_score,
                "row_quality": float(candidate["row_quality"]),
                "source_tier": int(candidate["source_tier"]),
            }
        )

    for pair in by_pair:
        by_pair[pair].sort(
            key=lambda item: (-float(item["rank_score"]), -float(item["row_quality"]), item["row_id"])
        )

    replacements: list[dict[str, Any]] = []
    for pair, count in sorted(counts_by_pair.items()):
        pool = by_pair.get(pair, [])
        if len(pool) < count:
            raise RuntimeError(
                f"not enough replacement rows for pack {target_pack_id} pair {pair}: need {count}, have {len(pool)}"
            )
        chosen = pool[:count]
        replacements.extend(chosen)
        for item in chosen:
            kept_loose.add(_loose_key(item["row"]))
            kept_source.add(_source_key(item["row"]))
    return replacements


def _build_pruned_rows(selected_rows: list[dict[str, Any]], remove_ids: set[str]) -> list[dict[str, Any]]:
    return [item["row"] for item in selected_rows if item["row_id"] not in remove_ids]


def _build_replaced_rows(
    selected_rows: list[dict[str, Any]],
    *,
    remove_ids: set[str],
    replacements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    queue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in replacements:
        queue[str(item["row"]["pair"])].append(item["row"])
    for pair in queue:
        queue[pair].sort(key=lambda row: row["row_id"])

    replaced: list[dict[str, Any]] = []
    for item in selected_rows:
        if item["row_id"] not in remove_ids:
            replaced.append(item["row"])
            continue
        pair = str(item["row"]["pair"])
        if not queue[pair]:
            raise RuntimeError(f"replacement queue exhausted for pair {pair}")
        replaced.append(queue[pair].pop(0))
    leftovers = sum(len(rows) for rows in queue.values())
    if leftovers:
        raise RuntimeError(f"unused replacements remained after fill: {leftovers}")
    return replaced


def _variant_source_counts(rows: list[dict[str, Any]], lineage: dict[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        winner = lineage["winners_by_row_id"].get(row["row_id"])
        if winner:
            counts[str(winner["source_file"])] += 1
    return dict(sorted(counts.items()))


def _manifest_for_variant(
    *,
    variant_name: str,
    dataset_path: Path,
    rows: list[dict[str, Any]],
    removed_ids: list[str],
    added_ids: list[str],
    target_pack_id: str,
    counts_removed: dict[str, int],
    lineage: dict[str, Any],
) -> dict[str, Any]:
    return {
        "variant_name": variant_name,
        "dataset_path": _safe_rel(dataset_path),
        "rows": len(rows),
        "counts_by_pair": dict(sorted(Counter(str(row["pair"]) for row in rows).items())),
        "target_pack_id": target_pack_id,
        "removed_counts_by_pair": counts_removed,
        "removed_row_ids": removed_ids,
        "added_row_ids": added_ids,
        "source_counts": _variant_source_counts(rows, lineage),
    }


def main() -> int:
    args = _parse_args()
    run_root = _resolve(str(args.run_root))
    rebucket_manifest_path = _resolve(str(args.rebucket_manifest))
    out_dir = _resolve(str(args.out_dir))
    prefix = str(args.prefix).strip() or "frozen_best5"
    prune_fraction = float(args.prune_fraction)
    if not (0.0 < prune_fraction < 1.0):
        raise RuntimeError("--prune-fraction must be between 0 and 1")

    target_packs = []
    seen = set()
    for item in args.target_pack:
        pack_id = str(item).strip().zfill(2)
        if pack_id in seen:
            continue
        seen.add(pack_id)
        target_packs.append(pack_id)
    if not target_packs:
        raise RuntimeError("at least one --target-pack is required")

    selected_rows, selected_by_id, selected_by_pack = _load_selected_dataset(run_root)
    lineage = _build_lineage_pool(rebucket_manifest_path)
    for pack_id in target_packs:
        if pack_id not in selected_by_pack:
            raise RuntimeError(f"target pack {pack_id} is not part of the frozen best-5 run")

    variant_root = out_dir / f"{prefix}.p{int(round(prune_fraction * 100)):02d}"
    variant_root.mkdir(parents=True, exist_ok=True)

    overall_manifest: dict[str, Any] = {
        "builder": _safe_rel(Path(__file__)),
        "run_root": _safe_rel(run_root),
        "rebucket_manifest": _safe_rel(rebucket_manifest_path),
        "target_packs": target_packs,
        "prune_fraction": prune_fraction,
        "seed": int(args.seed),
        "variants": [],
    }

    for pack_id in target_packs:
        pack_rows = selected_by_pack[pack_id]
        audits = [_audit_row(item["row"], pack_id=pack_id, lineage=lineage) for item in pack_rows]
        audit_rows = sorted(audits, key=lambda row: (-float(row["prune_score"]), row["row_id"]))
        counts_by_pair = _counts_to_remove(pack_rows, prune_fraction)
        prune_ids = _pick_prune_rows(audits, counts_by_pair)
        random_ids = _pick_random_rows(pack_rows, counts_by_pair, seed=int(args.seed), pack_id=pack_id)
        replacements = _select_replacements(
            target_pack_id=pack_id,
            counts_by_pair=counts_by_pair,
            selected_by_id=selected_by_id,
            removal_ids=set(prune_ids),
            lineage=lineage,
        )

        pack_dir = variant_root / f"pack_{pack_id}"
        pack_dir.mkdir(parents=True, exist_ok=True)
        audit_csv = pack_dir / f"{prefix}.pack_{pack_id}.audit.csv"
        _write_csv(
            audit_csv,
            audit_rows,
            [
                "pack_id",
                "pair",
                "row_id",
                "source_file",
                "source_tier",
                "draft_origin",
                "upstream_score",
                "upstream_flags",
                "source_len",
                "target_len",
                "length_ratio",
                "naturalness",
                "row_quality",
                "exact_count",
                "loose_count",
                "source_count",
                "frame_count",
                "has_digit",
                "has_time",
                "has_year",
                "has_date_word",
                "has_semicolon",
                "has_placeholder",
                "punctuation_mismatch",
                "copied_source",
                "cluster_penalty",
                "template_penalty",
                "length_penalty",
                "punctuation_penalty",
                "lineage_penalty",
                "prune_score",
                "source",
                "target_pos",
            ],
        )

        summary_md = pack_dir / f"{prefix}.pack_{pack_id}.summary.md"
        summary_lines = [
            f"# Frozen Best-5 Pack {pack_id} Audit",
            "",
            f"- run_root: `{_safe_rel(run_root)}`",
            f"- target_pack: `{pack_id}`",
            f"- prune_fraction: `{prune_fraction}`",
            f"- rows_in_pack: `{len(pack_rows)}`",
            f"- rows_to_remove: `{counts_by_pair}`",
            f"- audit_csv: `{_safe_rel(audit_csv)}`",
            "",
            "## Top Prune Candidates",
            "",
            "| rank | pair | prune_score | source_file | row_id |",
            "| --- | --- | --- | --- | --- |",
        ]
        for idx, row in enumerate(audit_rows[:15], start=1):
            summary_lines.append(
                f"| {idx} | {row['pair']} | {row['prune_score']} | `{row['source_file']}` | `{row['row_id']}` |"
            )
        summary_md.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

        variants = {
            "prune10": {
                "removed_ids": prune_ids,
                "rows": _build_pruned_rows(selected_rows, set(prune_ids)),
                "added_ids": [],
            },
            "random10": {
                "removed_ids": random_ids,
                "rows": _build_pruned_rows(selected_rows, set(random_ids)),
                "added_ids": [],
            },
            "replace10": {
                "removed_ids": prune_ids,
                "rows": _build_replaced_rows(selected_rows, remove_ids=set(prune_ids), replacements=replacements),
                "added_ids": [item["row_id"] for item in replacements],
            },
        }

        pack_manifest = {
            "pack_id": pack_id,
            "audit_csv": _safe_rel(audit_csv),
            "summary_md": _safe_rel(summary_md),
            "counts_to_remove": counts_by_pair,
            "variants": {},
        }

        for variant_name, payload in variants.items():
            dataset_path = pack_dir / f"{prefix}.pack_{pack_id}.{variant_name}.jsonl"
            _write_jsonl(dataset_path, payload["rows"])
            _write_row_ids(dataset_path.with_suffix(".row_ids.txt"), payload["rows"])
            manifest = _manifest_for_variant(
                variant_name=variant_name,
                dataset_path=dataset_path,
                rows=payload["rows"],
                removed_ids=payload["removed_ids"],
                added_ids=payload["added_ids"],
                target_pack_id=pack_id,
                counts_removed=counts_by_pair,
                lineage=lineage,
            )
            variant_manifest_path = pack_dir / f"{prefix}.pack_{pack_id}.{variant_name}.manifest.json"
            variant_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            manifest["manifest_path"] = _safe_rel(variant_manifest_path)
            pack_manifest["variants"][variant_name] = manifest
            overall_manifest["variants"].append(manifest)

        pack_manifest_path = pack_dir / f"{prefix}.pack_{pack_id}.manifest.json"
        pack_manifest_path.write_text(json.dumps(pack_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    overall_manifest_path = variant_root / f"{prefix}.manifest.json"
    overall_manifest_path.write_text(json.dumps(overall_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[refine-frozen-best5] out_dir={_safe_rel(variant_root)}")
    for variant in overall_manifest["variants"]:
        print(
            "[refine-frozen-best5] "
            f"pack={variant['target_pack_id']} "
            f"variant={variant['variant_name']} "
            f"rows={variant['rows']} "
            f"path={variant['dataset_path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
