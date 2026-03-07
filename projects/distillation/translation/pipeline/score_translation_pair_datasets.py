#!/usr/bin/env python3
"""Score translation pair datasets for alignment hygiene, diversity, duplication, and drift."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
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
DEFAULT_EXTERNAL = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "translate_distill_pairs.eval2_wmt13_enes_128.jsonl"
)
DEFAULT_INDOMAIN = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl"
)
DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "qa"
)
WORD_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]+", re.UNICODE)
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")
DATE_WORD_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december"
    r"|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b",
    re.IGNORECASE,
)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("datasets", nargs="+", help="Candidate dataset JSONL paths to score.")
    ap.add_argument("--gold", default=str(DEFAULT_GOLD))
    ap.add_argument("--external-eval", default=str(DEFAULT_EXTERNAL))
    ap.add_argument("--indomain-eval", default=str(DEFAULT_INDOMAIN))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--prefix", default="dataset_quality")
    return ap.parse_args()


def _now_utc() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for idx, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"invalid JSONL at {path}:{idx}: {exc}") from exc
            if not isinstance(row, dict):
                raise RuntimeError(f"expected object rows at {path}:{idx}")
            rows.append(row)
    if not rows:
        raise RuntimeError(f"dataset is empty: {path}")
    return rows


def _normalize_text(text: Any) -> str:
    raw = str(text or "").strip().lower()
    raw = re.sub(r"\s+", " ", raw)
    return raw


def _tokenize(text: Any) -> list[str]:
    return WORD_RE.findall(_normalize_text(text))


def _exact_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("src_lang", "")).strip(),
        str(row.get("tgt_lang", "")).strip(),
        _normalize_text(row.get("source", "")),
        _normalize_text(row.get("target_pos", "")),
        _normalize_text(row.get("target_neg", row.get("neg", ""))),
    )


def _loose_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("src_lang", "")).strip(),
        str(row.get("tgt_lang", "")).strip(),
        _normalize_text(row.get("source", "")),
        _normalize_text(row.get("target_pos", "")),
    )


def _clip_0_100(value: float) -> float:
    return max(0.0, min(100.0, value))


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _ratio(part: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return float(part) / float(total)


def _length_bucket(length: int) -> str:
    if length < 32:
        return "<32"
    if length < 64:
        return "32-63"
    if length < 96:
        return "64-95"
    if length < 128:
        return "96-127"
    if length < 160:
        return "128-159"
    if length < 224:
        return "160-223"
    return "224+"


def _normalized_entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0 or len(counter) <= 1:
        return 0.0
    probs = [count / total for count in counter.values() if count > 0]
    entropy = -sum(p * math.log(p, 2) for p in probs)
    max_entropy = math.log(len(counter), 2)
    if max_entropy <= 0:
        return 0.0
    return entropy / max_entropy


def _js_divergence(counter_a: Counter[str], counter_b: Counter[str]) -> float:
    total_a = sum(counter_a.values())
    total_b = sum(counter_b.values())
    if total_a <= 0 or total_b <= 0:
        return 1.0
    keys = set(counter_a) | set(counter_b)
    if not keys:
        return 0.0
    probs_a = {key: counter_a.get(key, 0.0) / total_a for key in keys}
    probs_b = {key: counter_b.get(key, 0.0) / total_b for key in keys}
    divergence = 0.0
    for key in keys:
        pa = probs_a[key]
        pb = probs_b[key]
        m = 0.5 * (pa + pb)
        if pa > 0:
            divergence += 0.5 * pa * math.log(pa / m, 2)
        if pb > 0:
            divergence += 0.5 * pb * math.log(pb / m, 2)
    return max(0.0, min(1.0, divergence))


def _distribution_similarity(counter_a: Counter[str], counter_b: Counter[str]) -> float:
    return 100.0 * (1.0 - _js_divergence(counter_a, counter_b))


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _score_from_rate(rate: float, *, good: float, bad: float) -> float:
    if good == bad:
        return 100.0 if rate >= good else 0.0
    if good > bad:
        value = (rate - bad) / (good - bad)
    else:
        value = (bad - rate) / (bad - good)
    return _clip_0_100(100.0 * value)


def _analyze_dataset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    pair_counter: Counter[str] = Counter()
    exact_counter: Counter[tuple[str, str, str, str, str]] = Counter()
    loose_counter: Counter[tuple[str, str, str, str]] = Counter()
    source_counter: Counter[tuple[str, str]] = Counter()
    target_counter: Counter[tuple[str, str]] = Counter()
    source_token_counter: Counter[str] = Counter()
    target_token_counter: Counter[str] = Counter()
    combined_token_counter: Counter[str] = Counter()
    source_length_counter: Counter[str] = Counter()
    target_length_counter: Counter[str] = Counter()
    normalized_lengths: list[float] = []
    same_lang = 0
    missing_fields = 0
    same_text = 0
    pos_equals_neg = 0
    suspicious_length_ratio = 0
    digit_rows = 0
    time_rows = 0
    semicolon_rows = 0
    date_word_rows = 0

    for row in rows:
        src_lang = str(row.get("src_lang", "")).strip()
        tgt_lang = str(row.get("tgt_lang", "")).strip()
        source = _normalize_text(row.get("source", ""))
        target_pos = _normalize_text(row.get("target_pos", ""))
        target_neg = _normalize_text(row.get("target_neg", row.get("neg", "")))
        pair_counter[f"{src_lang}-{tgt_lang}"] += 1
        exact_counter[_exact_key(row)] += 1
        loose_counter[_loose_key(row)] += 1
        source_counter[(src_lang, source)] += 1
        target_counter[(tgt_lang, target_pos)] += 1

        if not src_lang or not tgt_lang or not source or not target_pos:
            missing_fields += 1
        if src_lang == tgt_lang and src_lang:
            same_lang += 1
        if source == target_pos and source:
            same_text += 1
        if target_neg and target_pos == target_neg:
            pos_equals_neg += 1

        src_len = len(source)
        tgt_len = len(target_pos)
        ratio = (max(src_len, 1) / max(tgt_len, 1)) if tgt_len else float(src_len > 0)
        ratio = max(ratio, 1.0 / max(ratio, 1e-6))
        normalized_lengths.append(ratio)
        if ratio > 2.5 or src_len < 4 or tgt_len < 4:
            suspicious_length_ratio += 1

        source_length_counter[_length_bucket(src_len)] += 1
        target_length_counter[_length_bucket(tgt_len)] += 1

        source_tokens = _tokenize(source)
        target_tokens = _tokenize(target_pos)
        source_token_counter.update(source_tokens)
        target_token_counter.update(target_tokens)
        combined_token_counter.update(source_tokens)
        combined_token_counter.update(target_tokens)

        raw_source = str(row.get("source", ""))
        raw_target = str(row.get("target_pos", ""))
        raw_combo = f"{raw_source} {raw_target}"
        if any(ch.isdigit() for ch in raw_combo):
            digit_rows += 1
        if TIME_RE.search(raw_combo):
            time_rows += 1
        if ";" in raw_combo:
            semicolon_rows += 1
        if DATE_WORD_RE.search(raw_combo):
            date_word_rows += 1

    unique_exact = len(exact_counter)
    unique_source = len(source_counter)
    unique_target = len(target_counter)
    exact_unique_ratio = _ratio(unique_exact, total)
    source_unique_ratio = _ratio(unique_source, total)
    target_unique_ratio = _ratio(unique_target, total)
    balance_score = 0.0
    if pair_counter:
        counts = list(pair_counter.values())
        balance_score = 100.0 * (1.0 - ((max(counts) - min(counts)) / max(sum(counts), 1)))

    reasonable_length_ratio = 1.0 - _ratio(suspicious_length_ratio, total)
    source_entropy = _normalized_entropy(source_token_counter)
    target_entropy = _normalized_entropy(target_token_counter)
    length_entropy = _normalized_entropy(source_length_counter + target_length_counter)

    alignment_quality = _clip_0_100(
        0.22 * _score_from_rate(exact_unique_ratio, good=0.995, bad=0.85)
        + 0.18 * _score_from_rate(reasonable_length_ratio, good=0.99, bad=0.80)
        + 0.15 * _score_from_rate(1.0 - _ratio(missing_fields, total), good=1.0, bad=0.90)
        + 0.10 * _score_from_rate(1.0 - _ratio(same_lang, total), good=1.0, bad=0.98)
        + 0.10 * _score_from_rate(1.0 - _ratio(same_text, total), good=1.0, bad=0.98)
        + 0.10 * _score_from_rate(1.0 - _ratio(pos_equals_neg, total), good=1.0, bad=0.98)
        + 0.15 * _score_from_rate(_mean([source_unique_ratio, target_unique_ratio]), good=0.995, bad=0.85)
    )
    duplication_hygiene = _clip_0_100(
        0.40 * _score_from_rate(exact_unique_ratio, good=0.995, bad=0.80)
        + 0.30 * _score_from_rate(source_unique_ratio, good=0.99, bad=0.75)
        + 0.30 * _score_from_rate(target_unique_ratio, good=0.99, bad=0.75)
    )
    diversity = _clip_0_100(
        0.25 * balance_score
        + 0.25 * (100.0 * source_entropy)
        + 0.25 * (100.0 * target_entropy)
        + 0.25 * (100.0 * length_entropy)
    )

    return {
        "rows": total,
        "counts_by_pair": dict(sorted(pair_counter.items())),
        "metrics": {
            "exact_unique_ratio": exact_unique_ratio,
            "source_unique_ratio": source_unique_ratio,
            "target_unique_ratio": target_unique_ratio,
            "missing_fields_ratio": _ratio(missing_fields, total),
            "same_language_ratio": _ratio(same_lang, total),
            "source_equals_target_ratio": _ratio(same_text, total),
            "target_pos_equals_neg_ratio": _ratio(pos_equals_neg, total),
            "suspicious_length_ratio": _ratio(suspicious_length_ratio, total),
            "reasonable_length_ratio": reasonable_length_ratio,
            "digit_row_ratio": _ratio(digit_rows, total),
            "time_marker_ratio": _ratio(time_rows, total),
            "semicolon_row_ratio": _ratio(semicolon_rows, total),
            "date_word_row_ratio": _ratio(date_word_rows, total),
            "source_token_entropy_norm": source_entropy,
            "target_token_entropy_norm": target_entropy,
            "length_bucket_entropy_norm": length_entropy,
            "direction_balance_score": balance_score / 100.0,
        },
        "scores": {
            "alignment_quality": alignment_quality,
            "duplication_hygiene": duplication_hygiene,
            "diversity": diversity,
        },
        "artifacts": {
            "exact_keys": set(exact_counter.keys()),
            "loose_keys": set(loose_counter.keys()),
            "source_token_counter": source_token_counter,
            "target_token_counter": target_token_counter,
            "combined_token_counter": combined_token_counter,
            "source_length_counter": source_length_counter,
            "target_length_counter": target_length_counter,
        },
    }


def _reference_similarity(candidate: dict[str, Any], reference: dict[str, Any]) -> dict[str, float]:
    cand_source = candidate["artifacts"]["source_token_counter"]
    ref_source = reference["artifacts"]["source_token_counter"]
    cand_target = candidate["artifacts"]["target_token_counter"]
    ref_target = reference["artifacts"]["target_token_counter"]
    cand_lengths = candidate["artifacts"]["source_length_counter"] + candidate["artifacts"]["target_length_counter"]
    ref_lengths = reference["artifacts"]["source_length_counter"] + reference["artifacts"]["target_length_counter"]
    source_sim = _distribution_similarity(cand_source, ref_source)
    target_sim = _distribution_similarity(cand_target, ref_target)
    length_sim = _distribution_similarity(cand_lengths, ref_lengths)
    return {
        "source_token_similarity": source_sim,
        "target_token_similarity": target_sim,
        "length_profile_similarity": length_sim,
        "style_similarity": _clip_0_100((source_sim + target_sim + length_sim) / 3.0),
    }


def _gold_similarity(candidate: dict[str, Any], gold: dict[str, Any]) -> dict[str, float]:
    exact_overlap = len(candidate["artifacts"]["exact_keys"] & gold["artifacts"]["exact_keys"])
    loose_overlap = len(candidate["artifacts"]["loose_keys"] & gold["artifacts"]["loose_keys"])
    rows = max(candidate["rows"], 1)
    style = _reference_similarity(candidate, gold)
    exact_pct = 100.0 * exact_overlap / rows
    loose_pct = 100.0 * loose_overlap / rows
    score = _clip_0_100(
        0.25 * exact_pct
        + 0.25 * loose_pct
        + 0.25 * style["source_token_similarity"]
        + 0.25 * style["target_token_similarity"]
    )
    return {
        "exact_overlap_rows": float(exact_overlap),
        "loose_overlap_rows": float(loose_overlap),
        "exact_overlap_pct": exact_pct,
        "loose_overlap_pct": loose_pct,
        "source_token_similarity": style["source_token_similarity"],
        "target_token_similarity": style["target_token_similarity"],
        "length_profile_similarity": style["length_profile_similarity"],
        "score": score,
    }


def _prune_artifacts(analysis: dict[str, Any]) -> dict[str, Any]:
    out = dict(analysis)
    out.pop("artifacts", None)
    return out


def _dataset_report(
    path: Path,
    analysis: dict[str, Any],
    *,
    gold_analysis: dict[str, Any],
    external_analysis: dict[str, Any],
    indomain_analysis: dict[str, Any],
) -> dict[str, Any]:
    gold_similarity = _gold_similarity(analysis, gold_analysis)
    external_match = _reference_similarity(analysis, external_analysis)
    indomain_match = _reference_similarity(analysis, indomain_analysis)
    overall = _clip_0_100(
        0.30 * analysis["scores"]["alignment_quality"]
        + 0.15 * analysis["scores"]["duplication_hygiene"]
        + 0.15 * analysis["scores"]["diversity"]
        + 0.20 * gold_similarity["score"]
        + 0.10 * external_match["style_similarity"]
        + 0.10 * indomain_match["style_similarity"]
    )
    return {
        "dataset_name": path.stem,
        "path": _safe_rel(path),
        "rows": analysis["rows"],
        "counts_by_pair": analysis["counts_by_pair"],
        "scores": {
            "overall": _round4(overall),
            "alignment_quality": _round4(analysis["scores"]["alignment_quality"]),
            "duplication_hygiene": _round4(analysis["scores"]["duplication_hygiene"]),
            "diversity": _round4(analysis["scores"]["diversity"]),
            "gold_similarity": _round4(gold_similarity["score"]),
            "external_match": _round4(external_match["style_similarity"]),
            "indomain_match": _round4(indomain_match["style_similarity"]),
        },
        "diagnostics": {key: _round4(value) for key, value in analysis["metrics"].items()},
        "reference_similarity": {
            "gold": {key: _round4(value) for key, value in gold_similarity.items()},
            "external_eval2": {key: _round4(value) for key, value in external_match.items()},
            "indomain_eval3": {key: _round4(value) for key, value in indomain_match.items()},
        },
    }


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _write_md(path: Path, summary: dict[str, Any], reports: list[dict[str, Any]]) -> None:
    lines = [
        "# Translation Dataset Quality Report",
        "",
        f"Generated: {summary['generated_utc']}",
        "",
        "## Score Legend",
        "",
        "- `alignment_quality`: field completeness, cross-language sanity, and length-ratio hygiene",
        "- `duplication_hygiene`: exact/source/target uniqueness",
        "- `diversity`: direction balance plus token and length entropy",
        "- `gold_similarity`: overlap and distribution closeness to the restored March 3 gold set",
        "- `external_match`: style similarity to eval2 external data",
        "- `indomain_match`: style similarity to eval3 indomain data",
        "",
        "## Summary",
        "",
        "| dataset | overall | alignment | duplication | diversity | gold | external | indomain | rows |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for report in reports:
        scores = report["scores"]
        lines.append(
            "| "
            + " | ".join(
                [
                    report["dataset_name"],
                    str(scores["overall"]),
                    str(scores["alignment_quality"]),
                    str(scores["duplication_hygiene"]),
                    str(scores["diversity"]),
                    str(scores["gold_similarity"]),
                    str(scores["external_match"]),
                    str(scores["indomain_match"]),
                    str(report["rows"]),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Dataset Notes", ""])
    for report in reports:
        diag = report["diagnostics"]
        gold = report["reference_similarity"]["gold"]
        lines.extend(
            [
                f"### {report['dataset_name']}",
                "",
                f"- path: `{report['path']}`",
                f"- counts_by_pair: `{json.dumps(report['counts_by_pair'], sort_keys=True)}`",
                f"- duplicate pressure: exact_unique_ratio={diag['exact_unique_ratio']}, source_unique_ratio={diag['source_unique_ratio']}, target_unique_ratio={diag['target_unique_ratio']}",
                f"- templated-signal: digit_row_ratio={diag['digit_row_ratio']}, time_marker_ratio={diag['time_marker_ratio']}, date_word_row_ratio={diag['date_word_row_ratio']}",
                f"- gold overlap: exact_overlap_pct={gold['exact_overlap_pct']}, loose_overlap_pct={gold['loose_overlap_pct']}",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = _parse_args()
    gold_path = _resolve(str(args.gold))
    external_path = _resolve(str(args.external_eval))
    indomain_path = _resolve(str(args.indomain_eval))
    out_dir = _resolve(str(args.out_dir))
    dataset_paths = [_resolve(path_text) for path_text in args.datasets]

    for path in [gold_path, external_path, indomain_path, *dataset_paths]:
        if not path.is_file():
            raise RuntimeError(f"dataset not found: {path}")

    gold_analysis = _analyze_dataset(_load_jsonl(gold_path))
    external_analysis = _analyze_dataset(_load_jsonl(external_path))
    indomain_analysis = _analyze_dataset(_load_jsonl(indomain_path))

    reports: list[dict[str, Any]] = []
    for path in dataset_paths:
        analysis = _analyze_dataset(_load_jsonl(path))
        reports.append(
            _dataset_report(
                path,
                analysis,
                gold_analysis=gold_analysis,
                external_analysis=external_analysis,
                indomain_analysis=indomain_analysis,
            )
        )
    reports.sort(key=lambda item: float(item["scores"]["overall"] or 0.0), reverse=True)

    summary = {
        "generated_utc": _now_utc(),
        "gold_reference": _safe_rel(gold_path),
        "external_reference": _safe_rel(external_path),
        "indomain_reference": _safe_rel(indomain_path),
        "dataset_count": len(reports),
    }

    prefix = str(args.prefix).strip() or "dataset_quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{prefix}.json"
    md_path = out_dir / f"{prefix}.md"
    csv_path = out_dir / f"{prefix}.csv"

    _write_json(json_path, {"summary": summary, "datasets": reports})
    _write_md(md_path, summary, reports)
    _write_csv(
        csv_path,
        [
            {
                "dataset_name": report["dataset_name"],
                "path": report["path"],
                "rows": report["rows"],
                "overall": report["scores"]["overall"],
                "alignment_quality": report["scores"]["alignment_quality"],
                "duplication_hygiene": report["scores"]["duplication_hygiene"],
                "diversity": report["scores"]["diversity"],
                "gold_similarity": report["scores"]["gold_similarity"],
                "external_match": report["scores"]["external_match"],
                "indomain_match": report["scores"]["indomain_match"],
                "exact_unique_ratio": report["diagnostics"]["exact_unique_ratio"],
                "source_unique_ratio": report["diagnostics"]["source_unique_ratio"],
                "target_unique_ratio": report["diagnostics"]["target_unique_ratio"],
                "digit_row_ratio": report["diagnostics"]["digit_row_ratio"],
                "time_marker_ratio": report["diagnostics"]["time_marker_ratio"],
                "date_word_row_ratio": report["diagnostics"]["date_word_row_ratio"],
                "gold_exact_overlap_pct": report["reference_similarity"]["gold"]["exact_overlap_pct"],
                "gold_loose_overlap_pct": report["reference_similarity"]["gold"]["loose_overlap_pct"],
            }
            for report in reports
        ],
        [
            "dataset_name",
            "path",
            "rows",
            "overall",
            "alignment_quality",
            "duplication_hygiene",
            "diversity",
            "gold_similarity",
            "external_match",
            "indomain_match",
            "exact_unique_ratio",
            "source_unique_ratio",
            "target_unique_ratio",
            "digit_row_ratio",
            "time_marker_ratio",
            "date_word_row_ratio",
            "gold_exact_overlap_pct",
            "gold_loose_overlap_pct",
        ],
    )

    for report in reports:
        scores = report["scores"]
        print(
            "[dataset-score] "
            f"name={report['dataset_name']} "
            f"overall={scores['overall']:.4f} "
            f"alignment={scores['alignment_quality']:.4f} "
            f"duplication={scores['duplication_hygiene']:.4f} "
            f"diversity={scores['diversity']:.4f} "
            f"gold={scores['gold_similarity']:.4f} "
            f"external={scores['external_match']:.4f} "
            f"indomain={scores['indomain_match']:.4f}"
        )
    print(f"[dataset-score] csv={_safe_rel(csv_path)}")
    print(f"[dataset-score] md={_safe_rel(md_path)}")
    print(f"[dataset-score] json={_safe_rel(json_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
