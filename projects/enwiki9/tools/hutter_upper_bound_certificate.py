#!/usr/bin/env python3
"""Emit constructive upper-bound certificates from saved enwiki9 results.

The certificate is intentionally conservative:

* A saved result is a proven upper bound only for the exact input size and hash
  in that result, and only when roundtrip verification succeeded.
* Forecasts and calibrated projections are reported separately. They are useful
  search evidence, but they are not constructive proofs for enwik9.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DEFAULT = ROOT / "results"
OUT_JSON_DEFAULT = ROOT / "upper_bound_certificate.json"
OUT_MD_DEFAULT = ROOT / "UPPER_BOUND_CERTIFICATE.md"

FULL_INPUT_BYTES = 1_000_000_000
TARGET_10_95 = 109_500_000
CALIBRATED_BASELINE_SCORE = 110_181_114


@dataclass(frozen=True)
class Result:
    path: pathlib.Path
    program_id: str
    data_size: int
    data_sha256: str
    compressed_size: int
    program_size: int
    hutter_score: int
    roundtrip_ok: bool | None
    determinism_ok: bool | None
    timestamp: str

    @property
    def percent(self) -> float:
        if self.data_size <= 0:
            return math.inf
        return 100.0 * self.hutter_score / self.data_size

    @property
    def archive_bpb(self) -> float:
        if self.data_size <= 0:
            return math.inf
        return 8.0 * self.compressed_size / self.data_size

    @property
    def is_constructive(self) -> bool:
        return self.roundtrip_ok is True

    @property
    def is_full_corpus_proof(self) -> bool:
        return self.is_constructive and self.data_size == FULL_INPUT_BYTES


def as_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def determinism_ok(data: dict[str, Any]) -> bool | None:
    det = data.get("determinism")
    if not isinstance(det, dict):
        return None
    value = det.get("single_host_byte_equal")
    if isinstance(value, bool):
        return value
    return None


def load_result(path: pathlib.Path) -> Result | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    program_id = data.get("program_id")
    if not isinstance(program_id, str) or not program_id:
        return None

    data_size = as_int(data, "data_size")
    compressed_size = as_int(data, "compressed_size")
    program_size = as_int(data, "program_size")
    hutter_score = as_int(data, "hutter_score")
    if hutter_score == 0 and (compressed_size or program_size):
        hutter_score = compressed_size + program_size

    roundtrip = data.get("roundtrip_ok")
    if not isinstance(roundtrip, bool):
        roundtrip = None

    return Result(
        path=path,
        program_id=program_id,
        data_size=data_size,
        data_sha256=str(data.get("data_sha256", "")),
        compressed_size=compressed_size,
        program_size=program_size,
        hutter_score=hutter_score,
        roundtrip_ok=roundtrip,
        determinism_ok=determinism_ok(data),
        timestamp=str(data.get("timestamp", "")),
    )


def iter_results(results_dir: pathlib.Path) -> list[Result]:
    rows: list[Result] = []
    for path in sorted(results_dir.glob("*/*.json")):
        result = load_result(path)
        if result is not None:
            rows.append(result)
    return rows


def best_by_size(rows: list[Result]) -> list[Result]:
    best: dict[int, Result] = {}
    for row in rows:
        if not row.is_constructive:
            continue
        current = best.get(row.data_size)
        if current is None or row.hutter_score < current.hutter_score:
            best[row.data_size] = row
    return [best[size] for size in sorted(best)]


def best_archive_by_size(rows: list[Result]) -> list[Result]:
    best: dict[int, Result] = {}
    for row in rows:
        if not row.is_constructive:
            continue
        current = best.get(row.data_size)
        if current is None or row.compressed_size < current.compressed_size:
            best[row.data_size] = row
    return [best[size] for size in sorted(best)]


def result_record(row: Result) -> dict[str, Any]:
    return {
        "program_id": row.program_id,
        "result_path": str(row.path.relative_to(ROOT)),
        "data_size": row.data_size,
        "data_sha256": row.data_sha256,
        "compressed_size": row.compressed_size,
        "program_size": row.program_size,
        "hutter_score": row.hutter_score,
        "score_percent": round(row.percent, 9),
        "archive_bpb": round(row.archive_bpb, 9),
        "roundtrip_ok": row.roundtrip_ok,
        "determinism_ok": row.determinism_ok,
        "timestamp": row.timestamp,
    }


def build_certificate(rows: list[Result]) -> dict[str, Any]:
    exact_best = best_by_size(rows)
    full_exact = [row for row in rows if row.is_full_corpus_proof]
    full_winners = [
        row for row in full_exact if row.hutter_score <= TARGET_10_95
    ]
    best_constructive = min(
        (row for row in rows if row.is_constructive),
        key=lambda row: (row.hutter_score / max(1, row.data_size), row.hutter_score),
        default=None,
    )
    required_net_gain = CALIBRATED_BASELINE_SCORE - TARGET_10_95

    return {
        "theorem": (
            "If roundtrip_ok is true for archive A and decoder D on target corpus x, "
            "then |A| + |D| is a constructive upper bound for x in this testbed."
        ),
        "target": {
            "input_size": FULL_INPUT_BYTES,
            "target_score_10_95": TARGET_10_95,
            "calibrated_baseline_score": CALIBRATED_BASELINE_SCORE,
            "required_net_gain_from_calibrated_baseline": required_net_gain,
            "required_bpb_gain_before_program_cost": round(
                required_net_gain * 8 / FULL_INPUT_BYTES, 9
            ),
        },
        "proof_status": {
            "has_full_corpus_constructive_result": bool(full_exact),
            "has_10_95_constructive_upper_bound": bool(full_winners),
            "best_full_corpus_result": result_record(
                min(full_exact, key=lambda row: row.hutter_score)
            )
            if full_exact
            else None,
            "best_10_95_result": result_record(
                min(full_winners, key=lambda row: row.hutter_score)
            )
            if full_winners
            else None,
            "best_constructive_ratio_any_scope": result_record(best_constructive)
            if best_constructive is not None
            else None,
        },
        "best_exact_upper_bounds_by_scope": [
            result_record(row) for row in exact_best
        ],
        "best_exact_archive_by_scope": [
            result_record(row) for row in best_archive_by_size(rows)
        ],
        "notes": [
            "Prefix results prove upper bounds only for that prefix, not for enwik9.",
            "Projected 1GB scores are search evidence and are excluded from proof_status.",
            "A 10.95 proof requires a full 1GB result with score <= 109500000.",
        ],
    }


def write_markdown(cert: dict[str, Any], path: pathlib.Path) -> None:
    target = cert["target"]
    status = cert["proof_status"]
    lines = [
        "# Hutter Upper-Bound Certificate",
        "",
        "## Constructive Theorem",
        "",
        cert["theorem"],
        "",
        "## Target",
        "",
        f"- Full input bytes: `{target['input_size']:,}`",
        f"- 10.95% target score: `{target['target_score_10_95']:,}`",
        f"- Calibrated baseline score: `{target['calibrated_baseline_score']:,}`",
        "- Required net gain from calibrated baseline: "
        f"`{target['required_net_gain_from_calibrated_baseline']:,}` bytes",
        "- Required archive slope before program cost: "
        f"`{target['required_bpb_gain_before_program_cost']}` bits/byte",
        "",
        "## Proof Status",
        "",
        "- Full-corpus constructive result present: "
        f"`{status['has_full_corpus_constructive_result']}`",
        "- 10.95 constructive upper bound present: "
        f"`{status['has_10_95_constructive_upper_bound']}`",
        "",
    ]
    if status["best_full_corpus_result"]:
        row = status["best_full_corpus_result"]
        lines.extend(
            [
                "## Best Full-Corpus Result",
                "",
                f"- Program: `{row['program_id']}`",
                f"- Score: `{row['hutter_score']:,}`",
                f"- Percent: `{row['score_percent']}`",
                f"- Result: `{row['result_path']}`",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Best Full-Corpus Result",
                "",
                "No verified full-corpus result JSON is present in this workspace.",
                "",
            ]
        )

    lines.extend(
        [
            "## Best Exact Upper Bounds By Scope",
            "",
            "| data_size | program | score | archive | program_size | percent | result |",
            "|---:|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in cert["best_exact_upper_bounds_by_scope"]:
        lines.append(
            f"| {row['data_size']:,} | `{row['program_id']}` | "
            f"{row['hutter_score']:,} | {row['compressed_size']:,} | "
            f"{row['program_size']:,} | {row['score_percent']} | "
            f"`{row['result_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Best Exact Archive By Scope",
            "",
            "| data_size | program | archive | score | program_size | archive_bpb | result |",
            "|---:|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in cert["best_exact_archive_by_scope"]:
        lines.append(
            f"| {row['data_size']:,} | `{row['program_id']}` | "
            f"{row['compressed_size']:,} | {row['hutter_score']:,} | "
            f"{row['program_size']:,} | {row['archive_bpb']} | "
            f"`{row['result_path']}` |"
        )
    lines.extend(["", "## Notes", ""])
    for note in cert["notes"]:
        lines.append(f"- {note}")
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=pathlib.Path, default=RESULTS_DEFAULT)
    parser.add_argument("--json-out", type=pathlib.Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--md-out", type=pathlib.Path, default=OUT_MD_DEFAULT)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    rows = iter_results(args.results_dir)
    cert = build_certificate(rows)
    args.json_out.write_text(json.dumps(cert, indent=2) + "\n")
    write_markdown(cert, args.md_out)

    if args.print_summary:
        status = cert["proof_status"]
        print(f"results_scanned={len(rows)}")
        print(
            "has_10_95_constructive_upper_bound="
            f"{status['has_10_95_constructive_upper_bound']}"
        )
        best = status["best_constructive_ratio_any_scope"]
        if best:
            print(
                "best_scope="
                f"{best['data_size']} {best['program_id']} "
                f"score={best['hutter_score']} "
                f"percent={best['score_percent']}"
            )
        print(f"wrote {args.json_out}")
        print(f"wrote {args.md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
