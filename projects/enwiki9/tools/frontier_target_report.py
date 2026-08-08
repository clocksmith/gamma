#!/usr/bin/env python3
"""Rank enwiki9 frontier candidates against a total-Hutter target.

`forecast_frontier.py` is archive-first. This report adds counted program size
and makes the target explicit, so packaging wins and archive wins land on the
same S ledger.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import forecast_frontier


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DEFAULT = ROOT / "results" / "frontier_target"
DEFAULT_TARGET_PERCENT = 10.5
HUTTER_RECORD_TARGET = 109_685_197


def forecast_basis_rank(basis: str, max_scope: int) -> int:
    if basis == "exact-measured":
        return 0
    if max_scope >= 100_000_000:
        return 3
    if max_scope >= 10_000_000:
        return 4
    return 6


def fx2_calibration_basis(f100: dict[str, Any], max_scope: int) -> tuple[str, int]:
    f100_basis = str(f100.get("basis") or "")
    if f100_basis == "exact-measured":
        return "fx2-calibrated-from-exact-100m", 1
    if max_scope >= 10_000_000:
        return "fx2-calibrated-from-10m", 2
    return "fx2-calibrated-speculative", 5


def projected_rows(target_percent: float) -> list[dict[str, Any]]:
    rows = forecast_frontier.collect_rows()
    by_program: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_program.setdefault(row["program_id"], []).append(row)

    target_bytes = int(round(1_000_000_000 * target_percent / 100.0))
    out: list[dict[str, Any]] = []
    for program_id, points in by_program.items():
        screen_points = [row for row in points if row["input_bytes"] <= 100_000_000]
        if not screen_points:
            continue
        per_scope = forecast_frontier.best_by_scope(screen_points)
        best_points = list(per_scope.values())
        tier_rank, tier_label, max_scope = forecast_frontier.evidence_tier(best_points)
        f100 = forecast_frontier.fit_forecast(best_points, 100_000_000) or {}
        f1g = forecast_frontier.fit_forecast(best_points, 1_000_000_000) or {}
        fcal = forecast_frontier.calibrated_fx2_forecast(program_id, f100) or {}
        program_size = forecast_frontier.counted_program_size(program_id)
        if not isinstance(program_size, int):
            continue

        candidates: list[tuple[str, dict[str, Any], int]] = []
        if fcal:
            cal_basis, cal_rank = fx2_calibration_basis(f100, max_scope)
            candidates.append((cal_basis, fcal, cal_rank))
        if f1g:
            basis = str(f1g.get("basis") or "forecast")
            rank = forecast_basis_rank(basis, max_scope)
            candidates.append((basis, f1g, rank))
        if not candidates:
            continue
        basis, chosen, basis_rank = sorted(
            candidates,
            key=lambda item: (
                item[2],
                int(item[1].get("projected_archive") or 10**18),
            ),
        )[0]
        archive = chosen.get("projected_archive")
        if not isinstance(archive, int):
            continue
        hutter_score = archive + program_size
        points_text = ", ".join(
            f"{point['input_bytes']}:{point['compressed_size']}"
            for point in sorted(best_points, key=lambda item: item["input_bytes"])
        )
        out.append(
            {
                "program_id": program_id,
                "basis": basis,
                "basis_rank": basis_rank,
                "evidence_tier": tier_label,
                "evidence_tier_rank": tier_rank,
                "max_measured_scope": max_scope,
                "measured_points": points_text,
                "projected_archive_1g": archive,
                "program_size": program_size,
                "projected_hutter_score_1g": hutter_score,
                "projected_percent_1g": hutter_score / 1_000_000_000 * 100.0,
                "gap_to_target_bytes": hutter_score - target_bytes,
                "gap_to_hutter_prize_bytes": hutter_score - HUTTER_RECORD_TARGET,
            }
        )

    out.sort(
        key=lambda row: (
            row["basis_rank"],
            row["evidence_tier_rank"],
            row["gap_to_target_bytes"],
            row["projected_hutter_score_1g"],
        )
    )
    return out


def write_report(rows: list[dict[str, Any]], out_dir: pathlib.Path, target_percent: float, top: int) -> None:
    target_bytes = int(round(1_000_000_000 * target_percent / 100.0))
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Frontier Target Report",
        "",
        f"Target: S <= {target_bytes} ({target_percent:.3f}% of enwik9).",
        f"Hutter prize threshold reference: S < {HUTTER_RECORD_TARGET}.",
        "",
        "| rank | program | basis | quality | tier | max scope | projected S | percent | gap to target | archive | program | prize gap | measured points |",
        "|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for rank, row in enumerate(rows[:top], 1):
        lines.append(
            f"| {rank} | `{row['program_id']}` | {row['basis']} | "
            f"{row['basis_rank']} | {row['evidence_tier']} | "
            f"{row['max_measured_scope']} | "
            f"{row['projected_hutter_score_1g']} | "
            f"{row['projected_percent_1g']:.6f} | "
            f"{row['gap_to_target_bytes']} | "
            f"{row['projected_archive_1g']} | {row['program_size']} | "
            f"{row['gap_to_hutter_prize_bytes']} | {row['measured_points']} |"
        )
    winners = [row for row in rows if row["gap_to_target_bytes"] <= 0]
    credible_winners = [
        row for row in winners if row["basis_rank"] <= 2
    ]
    lines.extend(
        [
            "",
            f"Rows at or below target: {len(winners)}.",
            f"Rows at or below target with quality <= 2: {len(credible_winners)}.",
            "Quality ranks: 0 exact 1G, 1 fx2 calibrated from exact 100M, "
            "2 fx2 calibrated from 10M, 3 forecast from 100M, "
            "4 forecast from 10M, 5 speculative fx2 calibration, "
            "6 speculative forecast.",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    with (out_dir / "rows.jsonl").open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-percent", type=float, default=DEFAULT_TARGET_PERCENT)
    parser.add_argument("--out-dir", type=pathlib.Path, default=OUT_DEFAULT)
    parser.add_argument("--top", type=int, default=40)
    args = parser.parse_args()
    rows = projected_rows(args.target_percent)
    write_report(rows, args.out_dir, args.target_percent, args.top)
    winners = sum(1 for row in rows if row["gap_to_target_bytes"] <= 0)
    credible_winners = sum(
        1
        for row in rows
        if row["gap_to_target_bytes"] <= 0 and row["basis_rank"] <= 2
    )
    print(
        f"[frontier-target] rows={len(rows)} winners={winners} "
        f"credible_winners={credible_winners} "
        f"summary={args.out_dir / 'summary.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
