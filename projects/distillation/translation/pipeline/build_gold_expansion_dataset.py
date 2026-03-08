#!/usr/bin/env python3
"""Build gold-aligned expansion buckets from a larger translation training universe."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
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
DEFAULT_UNIVERSE = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "translate_distill_pairs_en_es_2way.train.merged.jsonl"
)
DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_expansion"
)
WORD_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ']+", re.UNICODE)
YEAR_RE = re.compile(r"\b20\d{2}\b")
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")
MONTH_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december"
    r"|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b",
    re.IGNORECASE,
)
ADMIN_TERMS = [
    "analyst",
    "policy analyst",
    "bank analyst",
    "timeline",
    "budget",
    "variance",
    "launch",
    "permissions",
    "permission",
    "consent",
    "households",
    "regional hub",
    "task",
    "milestones",
    "milestone",
    "invoice",
    "compare the release",
    "tracking",
    "share the sheet",
    "access permissions",
    "hub",
]
REQUIRED_KEYS = (
    "src_lang",
    "tgt_lang",
    "source",
    "target_pos",
    "target_neg",
)
ROW_ID_KEYS = (
    "src_lang",
    "tgt_lang",
    "source",
    "target_pos",
    "target_neg",
)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold", default=str(DEFAULT_GOLD))
    ap.add_argument("--universe", default=str(DEFAULT_UNIVERSE))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--prefix", default="gold_expansion")
    ap.add_argument("--target-exact", type=int, default=512)
    ap.add_argument("--target-hard", type=int, default=256)
    ap.add_argument("--target-rewrite", type=int, default=1024)
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


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _norm_text(text: Any) -> str:
    return " ".join(str(text or "").split()).strip().casefold()


def _row_id(row: dict[str, Any]) -> str:
    parts = [_safe_text(row.get(key)) for key in ROW_ID_KEYS]
    return hashlib.sha256("\t".join(parts).encode("utf-8")).hexdigest()


def _pair_label(row: dict[str, Any]) -> str:
    pair = _safe_text(row.get("pair"))
    if pair:
        return pair
    src = _safe_text(row.get("src_lang"))
    tgt = _safe_text(row.get("tgt_lang"))
    return f"{src}-{tgt}" if src and tgt else ""


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _tokenize(text: Any) -> list[str]:
    return WORD_RE.findall(_norm_text(text))


def _quantile(values: list[int], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, round(q * (len(ordered) - 1))))
    return float(ordered[idx])


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
            row["pair"] = _pair_label(row)
            row["row_id"] = _row_id(row)
            rows.append(row)
    if not rows:
        raise RuntimeError(f"no rows loaded from {path}")
    return rows


def _gold_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    src_lengths = [len(_safe_text(row["source"])) for row in rows]
    pos_lengths = [len(_safe_text(row["target_pos"])) for row in rows]
    return {
        "rows": len(rows),
        "src_p10": _quantile(src_lengths, 0.10),
        "src_p25": _quantile(src_lengths, 0.25),
        "src_p50": _quantile(src_lengths, 0.50),
        "src_p75": _quantile(src_lengths, 0.75),
        "src_p90": _quantile(src_lengths, 0.90),
        "src_p95": _quantile(src_lengths, 0.95),
        "pos_p10": _quantile(pos_lengths, 0.10),
        "pos_p25": _quantile(pos_lengths, 0.25),
        "pos_p50": _quantile(pos_lengths, 0.50),
        "pos_p75": _quantile(pos_lengths, 0.75),
        "pos_p90": _quantile(pos_lengths, 0.90),
        "pos_p95": _quantile(pos_lengths, 0.95),
    }


def _exact_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        _safe_text(row.get("src_lang")),
        _safe_text(row.get("tgt_lang")),
        _norm_text(row.get("source")),
        _norm_text(row.get("target_pos")),
        _norm_text(row.get("target_neg")),
    )


def _loose_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        _safe_text(row.get("src_lang")),
        _safe_text(row.get("tgt_lang")),
        _norm_text(row.get("source")),
        _norm_text(row.get("target_pos")),
    )


def _band_score(value: int, *, p10: float, p50: float, p90: float, p95: float) -> float:
    if p10 <= value <= p90:
        return 100.0
    if value < p10:
        span = max(12.0, p10)
        return max(0.0, 100.0 - ((p10 - value) / span) * 100.0)
    if value <= p95:
        span = max(12.0, p95 - p90)
        return max(0.0, 100.0 - ((value - p90) / span) * 45.0)
    span = max(12.0, p95)
    return max(0.0, 55.0 - ((value - p95) / span) * 100.0)


def _ratio_score(src_len: int, pos_len: int) -> float:
    larger = max(src_len, pos_len, 1)
    smaller = max(1, min(src_len, pos_len))
    ratio = larger / smaller
    if ratio <= 1.20:
        return 100.0
    if ratio <= 1.40:
        return 85.0
    if ratio <= 1.70:
        return 60.0
    if ratio <= 2.00:
        return 35.0
    return 0.0


def _row_features(row: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    source = _safe_text(row.get("source"))
    target_pos = _safe_text(row.get("target_pos"))
    combo = f"{source} {target_pos}"
    combo_lc = combo.casefold()
    src_len = len(source)
    pos_len = len(target_pos)
    admin_hits = [term for term in ADMIN_TERMS if term in combo_lc]
    has_year = bool(YEAR_RE.search(combo))
    has_time = bool(TIME_RE.search(combo))
    has_month = bool(MONTH_RE.search(combo))
    has_semicolon = ";" in combo
    template_penalty = 0.0
    if has_year:
        template_penalty += 25.0
    if has_time:
        template_penalty += 20.0
    if has_month:
        template_penalty += 15.0
    if has_semicolon:
        template_penalty += 10.0
    template_penalty += min(30.0, 8.0 * len(admin_hits))
    template_score = max(0.0, 100.0 - template_penalty)
    src_score = _band_score(
        src_len,
        p10=gold["src_p10"],
        p50=gold["src_p50"],
        p90=gold["src_p90"],
        p95=gold["src_p95"],
    )
    pos_score = _band_score(
        pos_len,
        p10=gold["pos_p10"],
        p50=gold["pos_p50"],
        p90=gold["pos_p90"],
        p95=gold["pos_p95"],
    )
    length_score = (src_score + pos_score) / 2.0
    align_score = _ratio_score(src_len, pos_len)
    naturalness = 0.45 * length_score + 0.35 * template_score + 0.20 * align_score
    longer_than_gold = src_len > gold["src_p75"] or pos_len > gold["pos_p75"]
    much_longer = src_len > gold["src_p90"] or pos_len > gold["pos_p90"]
    return {
        "src_len": src_len,
        "pos_len": pos_len,
        "has_year": has_year,
        "has_time": has_time,
        "has_month": has_month,
        "has_semicolon": has_semicolon,
        "admin_hits": admin_hits,
        "template_score": round(template_score, 4),
        "length_score": round(length_score, 4),
        "align_score": round(align_score, 4),
        "naturalness": round(naturalness, 4),
        "longer_than_gold": longer_than_gold,
        "much_longer": much_longer,
    }


def _candidate_metadata(
    *,
    row: dict[str, Any],
    features: dict[str, Any],
    origin: str,
    bucket: str,
    bucket_score: float,
    reason: str,
    universe_rel: str,
) -> dict[str, Any]:
    meta = {
        "curation_origin": origin,
        "curation_bucket": bucket,
        "curation_score": round(bucket_score, 4),
        "curation_reason": reason,
        "curation_source_row_id": row["row_id"],
        "curation_source_universe": universe_rel,
        "curation_pair": row["pair"],
        "curation_template_score": features["template_score"],
        "curation_length_score": features["length_score"],
        "curation_align_score": features["align_score"],
        "curation_naturalness": features["naturalness"],
        "curation_src_len": features["src_len"],
        "curation_pos_len": features["pos_len"],
        "curation_admin_hits": features["admin_hits"],
        "curation_flags": {
            "has_year": features["has_year"],
            "has_time": features["has_time"],
            "has_month": features["has_month"],
            "has_semicolon": features["has_semicolon"],
            "longer_than_gold": features["longer_than_gold"],
            "much_longer": features["much_longer"],
        },
    }
    out = dict(row)
    out.update(meta)
    return out


def _decorate_gold_row(row: dict[str, Any], *, gold: dict[str, Any], gold_rel: str) -> dict[str, Any]:
    features = _row_features(row, gold)
    return _candidate_metadata(
        row=row,
        features=features,
        origin="gold_core",
        bucket="gold_exact_core",
        bucket_score=100.0,
        reason="restored gold legacy control row",
        universe_rel=gold_rel,
    )


def _balanced_select(rows: list[dict[str, Any]], target: int, score_key: str) -> list[dict[str, Any]]:
    if target <= 0 or not rows:
        return []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("pair", ""))].append(row)
    for pair in grouped:
        grouped[pair].sort(key=lambda item: (float(item.get(score_key, 0.0)), item.get("row_id", "")), reverse=True)
    pairs = sorted(grouped)
    selected: list[dict[str, Any]] = []
    base = target // max(1, len(pairs))
    remainder = target % max(1, len(pairs))
    leftovers: list[dict[str, Any]] = []
    for idx, pair in enumerate(pairs):
        take = base + (1 if idx < remainder else 0)
        bucket = grouped[pair]
        selected.extend(bucket[:take])
        leftovers.extend(bucket[take:])
    if len(selected) < target:
        leftovers.sort(key=lambda item: (float(item.get(score_key, 0.0)), item.get("row_id", "")), reverse=True)
        selected.extend(leftovers[: target - len(selected)])
    selected.sort(key=lambda item: (item.get("pair", ""), -float(item.get(score_key, 0.0)), item.get("row_id", "")))
    return selected[:target]


def _dedupe_candidates(rows: list[dict[str, Any]], *, score_key: str) -> list[dict[str, Any]]:
    """Keep one representative per loose translation pair for Stage A-facing datasets."""
    best_by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = _loose_key(row)
        incumbent = best_by_key.get(key)
        if incumbent is None:
            best_by_key[key] = row
            continue
        row_score = float(row.get(score_key, 0.0))
        incumbent_score = float(incumbent.get(score_key, 0.0))
        if row_score > incumbent_score:
            best_by_key[key] = row
            continue
        if row_score == incumbent_score and str(row.get("row_id", "")) < str(incumbent.get("row_id", "")):
            best_by_key[key] = row
    return list(best_by_key.values())


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
    scores = [float(row.get("curation_score", 0.0)) for row in rows] or [0.0]
    naturalness = [float(row.get("curation_naturalness", 0.0)) for row in rows] or [0.0]
    admin_rows = sum(1 for row in rows if row.get("curation_admin_hits"))
    flagged_rows = sum(
        1
        for row in rows
        if any(bool(v) for v in dict(row.get("curation_flags", {})).values())
    )
    counts_by_pair: dict[str, int] = defaultdict(int)
    for row in rows:
        counts_by_pair[str(row.get("pair", ""))] += 1
    return {
        "rows": len(rows),
        "jsonl_path": _safe_rel(jsonl_path),
        "row_ids_path": _safe_rel(row_ids_path),
        "row_ids_sha256": _write_row_ids(row_ids_path, rows),
        "counts_by_pair": dict(sorted(counts_by_pair.items())),
        "score_min": round(min(scores), 4),
        "score_avg": round(sum(scores) / len(scores), 4) if rows else 0.0,
        "score_max": round(max(scores), 4),
        "naturalness_avg": round(sum(naturalness) / len(naturalness), 4),
        "admin_hit_rows": admin_rows,
        "flagged_rows": flagged_rows,
    }


def _summary_md(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Gold Expansion Dataset Build",
        "",
        f"Gold core: `{manifest['gold_path']}`",
        f"Universe: `{manifest['universe_path']}`",
        "",
        "## Buckets",
        "",
        "| bucket | rows | score_avg | naturalness_avg | counts_by_pair |",
        "| --- | --- | --- | --- | --- |",
    ]
    for key in ("exact_mined", "hard_natural", "rewrite_queue", "candidate_exact_hard"):
        item = manifest["buckets"].get(key) or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    key,
                    str(item.get("rows", 0)),
                    str(item.get("score_avg", "")),
                    str(item.get("naturalness_avg", "")),
                    json.dumps(item.get("counts_by_pair", {}), sort_keys=True),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "- Train Stage A first on `candidate_exact_hard` before mixing any rewritten rows.",
            "- Use shorter checkpoint horizons around `2k-16k`; the gold control peaked externally at `8k`.",
            "- Treat `rewrite_queue` as a separate synthetic lane with explicit provenance.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = _parse_args()
    gold_path = _resolve(str(args.gold))
    universe_path = _resolve(str(args.universe))
    out_dir = _resolve(str(args.out_dir))
    prefix = str(args.prefix).strip() or "gold_expansion"
    if not gold_path.is_file():
        raise RuntimeError(f"gold dataset not found: {gold_path}")
    if not universe_path.is_file():
        raise RuntimeError(f"universe dataset not found: {universe_path}")

    gold_rows = _load_rows(gold_path)
    universe_rows = _load_rows(universe_path)
    gold_stats = _gold_stats(gold_rows)
    gold_rel = _safe_rel(gold_path)
    universe_rel = _safe_rel(universe_path)
    gold_row_ids = {str(row["row_id"]) for row in gold_rows}

    gold_exact = {_exact_key(row) for row in gold_rows}
    gold_loose = {_loose_key(row) for row in gold_rows}

    exact_candidates: list[dict[str, Any]] = []
    hard_candidates: list[dict[str, Any]] = []
    rewrite_candidates: list[dict[str, Any]] = []

    for row in universe_rows:
        if _exact_key(row) in gold_exact or _loose_key(row) in gold_loose:
            continue
        features = _row_features(row, gold_stats)
        admin_count = len(features["admin_hits"])
        template_free = (
            not features["has_year"]
            and not features["has_time"]
            and not features["has_month"]
            and not features["has_semicolon"]
            and admin_count == 0
        )

        exact_score = features["naturalness"]
        hard_score = features["naturalness"] + (12.0 if features["longer_than_gold"] else 0.0)
        rewrite_priority = (
            0.50 * features["naturalness"]
            + 0.50 * (
                (25.0 if features["has_year"] else 0.0)
                + (20.0 if features["has_time"] else 0.0)
                + (15.0 if features["has_month"] else 0.0)
                + (10.0 if features["has_semicolon"] else 0.0)
                + min(30.0, 8.0 * admin_count)
                + (10.0 if features["much_longer"] else 0.0)
            )
        )

        if (
            template_free
            and not features["longer_than_gold"]
            and features["naturalness"] >= 72.0
        ):
            exact_candidates.append(
                _candidate_metadata(
                    row=row,
                    features=features,
                    origin="gold_mined_exact",
                    bucket="exact_mined",
                    bucket_score=exact_score,
                    reason="gold-like natural exact row from merged universe",
                    universe_rel=universe_rel,
                )
            )
            continue

        if (
            template_free
            and features["longer_than_gold"]
            and not features["much_longer"]
            and features["naturalness"] >= 68.0
        ):
            hard_candidates.append(
                _candidate_metadata(
                    row=row,
                    features=features,
                    origin="gold_hard_natural",
                    bucket="hard_natural",
                    bucket_score=hard_score,
                    reason="natural row that is longer/harder than the gold core",
                    universe_rel=universe_rel,
                )
            )
            continue

        if features["naturalness"] >= 40.0 and (
            features["has_year"]
            or features["has_time"]
            or features["has_month"]
            or features["has_semicolon"]
            or admin_count > 0
            or features["much_longer"]
        ):
            rewrite_candidates.append(
                _candidate_metadata(
                    row=row,
                    features=features,
                    origin="gold_rewrite_queue",
                    bucket="rewrite_queue",
                    bucket_score=rewrite_priority,
                    reason="semantically useful but stylistically too templated or too long for gold exact use",
                    universe_rel=universe_rel,
                )
            )

    exact_candidates = _dedupe_candidates(exact_candidates, score_key="curation_score")
    hard_candidates = _dedupe_candidates(hard_candidates, score_key="curation_score")
    rewrite_candidates = _dedupe_candidates(rewrite_candidates, score_key="curation_score")

    exact_rows = _balanced_select(exact_candidates, int(args.target_exact), "curation_score")
    hard_rows = _balanced_select(hard_candidates, int(args.target_hard), "curation_score")
    rewrite_rows = _balanced_select(rewrite_candidates, int(args.target_rewrite), "curation_score")

    combined_rows = []
    combined_seen: set[str] = set()
    for row in [*gold_rows, *exact_rows, *hard_rows]:
        row_copy = (
            _decorate_gold_row(row, gold=gold_stats, gold_rel=gold_rel)
            if str(row.get("row_id", "")) in gold_row_ids
            else dict(row)
        )
        rid = str(row_copy["row_id"])
        if rid in combined_seen:
            continue
        combined_seen.add(rid)
        combined_rows.append(row_copy)

    out_dir.mkdir(parents=True, exist_ok=True)
    exact_path = out_dir / f"{prefix}.exact_mined.jsonl"
    exact_row_ids = out_dir / f"{prefix}.exact_mined.row_ids.txt"
    hard_path = out_dir / f"{prefix}.hard_natural.jsonl"
    hard_row_ids = out_dir / f"{prefix}.hard_natural.row_ids.txt"
    rewrite_path = out_dir / f"{prefix}.rewrite_queue.jsonl"
    rewrite_row_ids = out_dir / f"{prefix}.rewrite_queue.row_ids.txt"
    combined_path = out_dir / f"{prefix}.candidate_exact_hard.jsonl"
    combined_row_ids = out_dir / f"{prefix}.candidate_exact_hard.row_ids.txt"
    manifest_path = out_dir / f"{prefix}.manifest.json"
    summary_path = out_dir / f"{prefix}.summary.md"

    _write_jsonl(exact_path, exact_rows)
    _write_jsonl(hard_path, hard_rows)
    _write_jsonl(rewrite_path, rewrite_rows)
    _write_jsonl(combined_path, combined_rows)

    manifest = {
        "gold_path": _safe_rel(gold_path),
        "gold_sha256": _sha256_path(gold_path),
        "gold_stats": gold_stats,
        "universe_path": _safe_rel(universe_path),
        "universe_sha256": _sha256_path(universe_path),
        "universe_rows": len(universe_rows),
        "builder": _safe_rel(Path(__file__)),
        "targets": {
            "exact_mined": int(args.target_exact),
            "hard_natural": int(args.target_hard),
            "rewrite_queue": int(args.target_rewrite),
        },
        "candidate_pool_sizes": {
            "exact_mined": len(exact_candidates),
            "hard_natural": len(hard_candidates),
            "rewrite_queue": len(rewrite_candidates),
        },
        "buckets": {
            "exact_mined": _bucket_summary(exact_rows, jsonl_path=exact_path, row_ids_path=exact_row_ids),
            "hard_natural": _bucket_summary(hard_rows, jsonl_path=hard_path, row_ids_path=hard_row_ids),
            "rewrite_queue": _bucket_summary(rewrite_rows, jsonl_path=rewrite_path, row_ids_path=rewrite_row_ids),
            "candidate_exact_hard": _bucket_summary(combined_rows, jsonl_path=combined_path, row_ids_path=combined_row_ids),
        },
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _summary_md(summary_path, manifest)

    print(f"[gold-expansion] manifest={_safe_rel(manifest_path)}")
    for key in ("exact_mined", "hard_natural", "rewrite_queue", "candidate_exact_hard"):
        item = manifest["buckets"][key]
        print(
            f"[gold-expansion] bucket={key} rows={item['rows']} "
            f"score_avg={item['score_avg']:.4f} path={item['jsonl_path']}"
        )
    print(f"[gold-expansion] summary={_safe_rel(summary_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
