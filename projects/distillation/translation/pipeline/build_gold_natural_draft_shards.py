#!/usr/bin/env python3
"""Build draft replacement shards that bias toward human-written and non-repetitive rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
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
DEFAULT_AUTHORED = [
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.authored_310.jsonl",
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.authored_balanced_310.jsonl",
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.authored_goldlike_32.jsonl",
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.authored_goldlike_50.jsonl",
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.authored_gapfill_best_16.jsonl",
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.authored_gapfill_best_15_round2.jsonl",
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.authored_gapfill_best_12_round3.jsonl",
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.authored_gapfill_best_18_round4.jsonl",
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards"
    / "gold_quality_4x640.authored_goldlike_80_round5.jsonl",
]
DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "gold_shards_draft"
)

REQUIRED_KEYS = ("src_lang", "tgt_lang", "source", "target_pos", "target_neg")
ROW_ID_KEYS = ("src_lang", "tgt_lang", "source", "target_pos", "target_neg")
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
BAD_SUBSTRINGS = (
    "5g connectivity",
    "smartphone features",
    "baggage allowance",
    "overhead costs",
    "inflation rate has increased",
    "startup raised",
    "new jobs in the city",
    "attend at least",
    "blood test will be ready",
    "candidate with at least",
)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold", default=str(DEFAULT_GOLD))
    ap.add_argument("--universe", default=str(DEFAULT_UNIVERSE))
    ap.add_argument(
        "--authored",
        action="append",
        default=[],
        help="Authored JSONL pool path. Can be supplied multiple times.",
    )
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--prefix", default="gold_natural_draft")
    ap.add_argument("--shard-size", type=int, default=640)
    ap.add_argument("--strict-naturalness", type=float, default=80.0)
    ap.add_argument("--review-naturalness", type=float, default=72.0)
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


def _pair(row: dict[str, Any]) -> str:
    pair = _safe_text(row.get("pair"))
    if pair:
        return pair
    return f"{_safe_text(row.get('src_lang'))}-{_safe_text(row.get('tgt_lang'))}"


def _row_id(row: dict[str, Any]) -> str:
    parts = [_safe_text(row.get(key)) for key in ROW_ID_KEYS]
    return hashlib.sha256("\t".join(parts).encode("utf-8")).hexdigest()


def _loose_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        _safe_text(row.get("src_lang")),
        _safe_text(row.get("tgt_lang")),
        _norm_text(row.get("source")),
        _norm_text(row.get("target_pos")),
    )


def _source_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _safe_text(row.get("src_lang")),
        _safe_text(row.get("tgt_lang")),
        _norm_text(row.get("source")),
    )


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
            row["pair"] = _pair(row)
            row["row_id"] = _row_id(row)
            rows.append(row)
    return rows


def _quantile(values: list[int], q: float) -> float:
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, round(q * (len(ordered) - 1))))
    return float(ordered[idx])


def _gold_stats(rows: list[dict[str, Any]]) -> dict[str, float]:
    src_lengths = [len(_safe_text(row["source"])) for row in rows]
    pos_lengths = [len(_safe_text(row["target_pos"])) for row in rows]
    return {
        "src_p10": _quantile(src_lengths, 0.10),
        "src_p90": _quantile(src_lengths, 0.90),
        "src_p95": _quantile(src_lengths, 0.95),
        "pos_p10": _quantile(pos_lengths, 0.10),
        "pos_p90": _quantile(pos_lengths, 0.90),
        "pos_p95": _quantile(pos_lengths, 0.95),
    }


def _band_score(value: int, *, p10: float, p90: float, p95: float) -> float:
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


def _naturalness(row: dict[str, Any], gold: dict[str, float]) -> float:
    src = _safe_text(row.get("source"))
    pos = _safe_text(row.get("target_pos"))
    src_len = len(src)
    pos_len = len(pos)
    length_score = (
        _band_score(src_len, p10=gold["src_p10"], p90=gold["src_p90"], p95=gold["src_p95"])
        + _band_score(pos_len, p10=gold["pos_p10"], p90=gold["pos_p90"], p95=gold["pos_p95"])
    ) / 2.0
    align_score = _ratio_score(src_len, pos_len)
    return round(0.45 * length_score + 0.35 * 100.0 + 0.20 * align_score, 4)


def _source_frame(text: str) -> str:
    return DIGITS_RE.sub("<NUM>", _norm_text(text))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _summary_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("pair", "")) for row in rows).items()))


def _sort_for_selection(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            -float(row.get("draft_score", 0.0)),
            bool(row.get("draft_has_digit")),
            str(row.get("source", "")),
            str(row.get("row_id", "")),
        ),
    )


def _interleave_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {"en-es": [], "es-en": []}
    for row in rows:
        buckets.setdefault(str(row.get("pair", "")), []).append(row)
    for pair in buckets:
        buckets[pair] = _sort_for_selection(buckets[pair])
    out: list[dict[str, Any]] = []
    while True:
        progressed = False
        for pair in ("en-es", "es-en"):
            bucket = buckets.get(pair, [])
            if bucket:
                out.append(bucket.pop(0))
                progressed = True
        if not progressed:
            break
    return out


def main() -> int:
    args = _parse_args()
    gold_path = _resolve(str(args.gold))
    universe_path = _resolve(str(args.universe))
    authored_paths = [_resolve(text) for text in (args.authored or [])]
    if not authored_paths:
        authored_paths = list(DEFAULT_AUTHORED)
    out_dir = _resolve(str(args.out_dir))
    prefix = str(args.prefix).strip() or "gold_natural_draft"

    gold_rows = _load_rows(gold_path)
    universe_rows = _load_rows(universe_path)
    authored_sources = [path for path in authored_paths if path.is_file()]
    authored_rows_raw: list[dict[str, Any]] = []
    for path in authored_sources:
        authored_rows_raw.extend(_load_rows(path))

    gold_stats = _gold_stats(gold_rows)
    gold_loose = {_loose_key(row) for row in gold_rows}

    human_by_loose: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in authored_rows_raw:
        loose = _loose_key(row)
        incumbent = human_by_loose.get(loose)
        if incumbent is None or str(row["row_id"]) < str(incumbent["row_id"]):
            row_copy = dict(row)
            row_copy["draft_origin"] = "authored_human_pool"
            row_copy["draft_score"] = 200.0
            row_copy["draft_has_digit"] = bool(re.search(r"\d", f"{row['source']} {row['target_pos']}"))
            human_by_loose[loose] = row_copy
    human_rows = _sort_for_selection(list(human_by_loose.values()))
    human_loose = set(human_by_loose)

    mined_raw: list[dict[str, Any]] = []
    for row in universe_rows:
        loose = _loose_key(row)
        if loose in gold_loose or loose in human_loose:
            continue
        combo = f"{_safe_text(row.get('source'))} {_safe_text(row.get('target_pos'))}".casefold()
        if YEAR_RE.search(combo) or TIME_RE.search(combo) or MONTH_OR_WEEKDAY_RE.search(combo):
            continue
        if ";" in combo or PLACEHOLDER_RE.search(combo):
            continue
        if any(bad in combo for bad in BAD_SUBSTRINGS):
            continue
        row_copy = dict(row)
        row_copy["draft_naturalness"] = _naturalness(row_copy, gold_stats)
        row_copy["draft_frame"] = _source_frame(_safe_text(row_copy.get("source")))
        row_copy["draft_has_digit"] = bool(re.search(r"\d", combo))
        mined_raw.append(row_copy)

    mined_by_loose: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in mined_raw:
        loose = _loose_key(row)
        incumbent = mined_by_loose.get(loose)
        if incumbent is None or float(row["draft_naturalness"]) > float(incumbent["draft_naturalness"]):
            mined_by_loose[loose] = row
    mined_by_source: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in mined_by_loose.values():
        source = _source_key(row)
        incumbent = mined_by_source.get(source)
        if incumbent is None or float(row["draft_naturalness"]) > float(incumbent["draft_naturalness"]):
            mined_by_source[source] = row
    mined_rows = list(mined_by_source.values())
    frame_counts = Counter(str(row["draft_frame"]) for row in mined_rows)

    strict_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    for row in mined_rows:
        frame_count = int(frame_counts[str(row["draft_frame"])])
        row["draft_frame_count"] = frame_count
        row["draft_origin"] = "mined_candidate"
        score = float(row["draft_naturalness"])
        if row["draft_has_digit"]:
            score -= 4.0
        if frame_count > 1:
            score -= 2.0 * min(4, frame_count - 1)
        row["draft_score"] = round(score, 4)
        if (
            float(row["draft_naturalness"]) >= float(args.strict_naturalness)
            and ((not row["draft_has_digit"]) or frame_count == 1)
        ):
            row["draft_origin"] = "strict_mined_pool"
            strict_rows.append(row)
        elif float(row["draft_naturalness"]) >= float(args.review_naturalness):
            row["draft_origin"] = "review_mined_pool"
            review_rows.append(row)

    strict_rows = _sort_for_selection(strict_rows)
    review_rows = _sort_for_selection(review_rows)

    target_per_pair = int(args.shard_size) // 2
    human_counts = Counter(str(row.get("pair", "")) for row in human_rows)
    strict_by_pair = {"en-es": [], "es-en": []}
    for row in strict_rows:
        strict_by_pair.setdefault(str(row.get("pair", "")), []).append(row)

    shard03_rows: list[dict[str, Any]] = list(human_rows)
    shard03_row_ids = {str(row["row_id"]) for row in shard03_rows}
    needed = {
        "en-es": max(0, target_per_pair - int(human_counts.get("en-es", 0))),
        "es-en": max(0, target_per_pair - int(human_counts.get("es-en", 0))),
    }
    for pair in ("en-es", "es-en"):
        shard03_rows.extend(strict_by_pair.get(pair, [])[: needed[pair]])

    shard03_rows = _interleave_rows(shard03_rows)
    shard03_row_ids = {str(row["row_id"]) for row in shard03_rows}
    shard04_seed_rows = _interleave_rows([row for row in strict_rows if str(row["row_id"]) not in shard03_row_ids])
    shard04_review_rows = _interleave_rows(
        [row for row in review_rows if str(row["row_id"]) not in shard03_row_ids]
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    human_pool_path = out_dir / f"{prefix}.human_pool.jsonl"
    strict_pool_path = out_dir / f"{prefix}.strict_mined_pool.jsonl"
    review_pool_path = out_dir / f"{prefix}.review_queue.jsonl"
    shard03_path = out_dir / f"{prefix}.shard_03_draft_full.jsonl"
    shard04_seed_path = out_dir / f"{prefix}.shard_04_seed.jsonl"
    manifest_path = out_dir / f"{prefix}.manifest.json"
    summary_path = out_dir / f"{prefix}.summary.md"

    _write_jsonl(human_pool_path, human_rows)
    _write_jsonl(strict_pool_path, strict_rows)
    _write_jsonl(review_pool_path, shard04_review_rows)
    _write_jsonl(shard03_path, shard03_rows)
    _write_jsonl(shard04_seed_path, shard04_seed_rows)

    manifest = {
        "builder": _safe_rel(Path(__file__)),
        "gold_path": _safe_rel(gold_path),
        "universe_path": _safe_rel(universe_path),
        "authored_paths": [_safe_rel(path) for path in authored_sources],
        "strict_naturalness": float(args.strict_naturalness),
        "review_naturalness": float(args.review_naturalness),
        "human_pool_rows": len(human_rows),
        "human_pool_counts_by_pair": _summary_counts(human_rows),
        "strict_mined_rows": len(strict_rows),
        "strict_mined_counts_by_pair": _summary_counts(strict_rows),
        "review_queue_rows": len(shard04_review_rows),
        "review_queue_counts_by_pair": _summary_counts(shard04_review_rows),
        "draft_shard_03_rows": len(shard03_rows),
        "draft_shard_03_counts_by_pair": _summary_counts(shard03_rows),
        "draft_shard_04_seed_rows": len(shard04_seed_rows),
        "draft_shard_04_seed_counts_by_pair": _summary_counts(shard04_seed_rows),
        "draft_shard_04_missing_rows": max(0, int(args.shard_size) - len(shard04_seed_rows)),
        "artifacts": {
            "human_pool": _safe_rel(human_pool_path),
            "strict_mined_pool": _safe_rel(strict_pool_path),
            "review_queue": _safe_rel(review_pool_path),
            "draft_shard_03": _safe_rel(shard03_path),
            "draft_shard_04_seed": _safe_rel(shard04_seed_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary_lines = [
        "# Gold Natural Draft Shards",
        "",
        f"Gold core: `{manifest['gold_path']}`",
        f"Universe: `{manifest['universe_path']}`",
        "",
        "## Pools",
        "",
        f"- Human pool: `{len(human_rows)}` rows {json.dumps(_summary_counts(human_rows), sort_keys=True)}",
        f"- Strict mined pool: `{len(strict_rows)}` rows {json.dumps(_summary_counts(strict_rows), sort_keys=True)}",
        f"- Review queue: `{len(shard04_review_rows)}` rows {json.dumps(_summary_counts(shard04_review_rows), sort_keys=True)}",
        "",
        "## Draft Shards",
        "",
        f"- `shard_03_draft_full`: `{len(shard03_rows)}` rows {json.dumps(_summary_counts(shard03_rows), sort_keys=True)}",
        f"- `shard_04_seed`: `{len(shard04_seed_rows)}` rows {json.dumps(_summary_counts(shard04_seed_rows), sort_keys=True)}",
        f"- Missing rows to finish `shard_04`: `{manifest['draft_shard_04_missing_rows']}`",
        "",
        "## Note",
        "",
        "This draft intentionally refuses to auto-fill the second shard with lower-confidence repetitive mined rows.",
        "The review queue is the next source for manual promotion or rewrite.",
        "",
    ]
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"[gold-natural-draft] summary={_safe_rel(summary_path)}")
    print(f"[gold-natural-draft] shard_03_rows={len(shard03_rows)}")
    print(f"[gold-natural-draft] shard_04_seed_rows={len(shard04_seed_rows)}")
    print(f"[gold-natural-draft] shard_04_missing_rows={manifest['draft_shard_04_missing_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
