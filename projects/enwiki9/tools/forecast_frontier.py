#!/usr/bin/env python3
"""Forecast archive-first enwiki9 frontiers from measured small-scope rows.

The frontier runner is exact-scope accounting. This tool is the efficient
screening layer: mine existing driver JSONL and program metadata, collect
1MB/10MB archive rows, fit a simple archive scaling curve, and rank programs by
projected distance to 10 percent at 100MB and 1GB.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from collections import defaultdict
from typing import Any, Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRAMS = ROOT / "programs"
RESULTS = ROOT / "results"
OUT_DEFAULT = ROOT / "results" / "forecast_frontier"
TARGETS = (100_000_000, 1_000_000_000)
SCREEN_SCOPES = (1_000_000, 10_000_000)


def counted_program_size(program_id: str) -> int | None:
    root = PROGRAMS / program_id
    if not root.exists():
        return None
    total = 0
    found = False
    for path in root.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
            found = True
    return total if found else None


def load_json(path: pathlib.Path) -> Any | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def iter_jsonl(path: pathlib.Path) -> Iterable[dict[str, Any]]:
    try:
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                if isinstance(row, dict):
                    yield row
    except Exception:
        return


def row_from_driver(row: dict[str, Any], source: str) -> dict[str, Any] | None:
    size = row.get("data_size") or row.get("input_bytes")
    archive = row.get("compressed_size") or row.get("archive")
    program_id = row.get("program_id")
    if not isinstance(size, int) or not isinstance(archive, int) or not program_id:
        return None
    if row.get("roundtrip_ok") is False:
        return None
    program_size = row.get("program_size")
    return {
        "program_id": str(program_id),
        "input_bytes": size,
        "compressed_size": archive,
        "program_size": program_size if isinstance(program_size, int) else None,
        "hutter_score": row.get("hutter_score"),
        "roundtrip_ok": row.get("roundtrip_ok"),
        "source": source,
    }


def detect_scope_key(key: str) -> int | None:
    text = key.lower()
    if "100m" in text or "100mb" in text:
        return 100_000_000
    if "10m" in text or "10mb" in text:
        return 10_000_000
    if "1m" in text or "1mb" in text:
        return 1_000_000
    if "250k" in text:
        return 250_000
    if "1k" in text:
        return 1_000
    return None


def iter_meta_rows(program_id: str, obj: Any, source: str, inherited_scope: int | None = None) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        scope = obj.get("input_bytes") or obj.get("data_size") or inherited_scope
        archive = obj.get("compressed_size") or obj.get("archive") or obj.get("archive_size")
        if isinstance(scope, int) and isinstance(archive, int):
            roundtrip = obj.get("roundtrip_ok")
            basis = obj.get("roundtrip_basis")
            if roundtrip is not False:
                program_size = obj.get("program_size")
                yield {
                    "program_id": program_id,
                    "input_bytes": scope,
                    "compressed_size": archive,
                    "program_size": program_size if isinstance(program_size, int) else None,
                    "hutter_score": obj.get("hutter_score"),
                    "roundtrip_ok": roundtrip if isinstance(roundtrip, bool) else bool(basis),
                    "source": source,
                }
        for key, value in obj.items():
            child_scope = detect_scope_key(str(key)) or scope if isinstance(scope, int) else detect_scope_key(str(key))
            yield from iter_meta_rows(program_id, value, f"{source}:{key}", child_scope)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from iter_meta_rows(program_id, value, f"{source}[{index}]", inherited_scope)


def collect_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in RESULTS.rglob("*.jsonl"):
        for row in iter_jsonl(path):
            parsed = row_from_driver(row, str(path.relative_to(ROOT)))
            if parsed:
                rows.append(parsed)
    for path in RESULTS.rglob("*.json"):
        obj = load_json(path)
        parsed = row_from_driver(obj, str(path.relative_to(ROOT))) if isinstance(obj, dict) else None
        if parsed:
            rows.append(parsed)
    for path in PROGRAMS.glob("*/meta.json"):
        obj = load_json(path)
        if obj is None:
            continue
        rows.extend(iter_meta_rows(path.parent.name, obj, str(path.relative_to(ROOT))))
    return dedupe_rows(rows)


def dedupe_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, int, int], dict[str, Any]] = {}
    for row in rows:
        if row.get("program_size") is None:
            row["program_size"] = counted_program_size(row["program_id"])
        key = (row["program_id"], row["input_bytes"], row["compressed_size"])
        old = best.get(key)
        if old is None:
            best[key] = row
            continue
        old_score = 0
        row_score = 0
        old_score += int(old.get("hutter_score") is not None)
        row_score += int(row.get("hutter_score") is not None)
        old_score += int(old.get("program_size") is not None)
        row_score += int(row.get("program_size") is not None)
        old_score += int(old.get("roundtrip_ok") is True)
        row_score += int(row.get("roundtrip_ok") is True)
        if row_score > old_score:
            best[key] = row
    return list(best.values())


def best_by_scope(rows: Iterable[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    best: dict[int, dict[str, Any]] = {}
    for row in rows:
        size = row["input_bytes"]
        old = best.get(size)
        if old is None or row["compressed_size"] < old["compressed_size"]:
            best[size] = row
    return best


def fit_forecast(points: list[dict[str, Any]], target: int) -> dict[str, Any] | None:
    usable = sorted({row["input_bytes"]: row for row in points}.values(), key=lambda row: row["input_bytes"])
    if not usable:
        return None
    exact = [row for row in usable if row["input_bytes"] == target]
    if exact:
        row = exact[0]
        return {
            "basis": "exact-measured",
            "alpha": 1.0,
            "projected_archive": row["compressed_size"],
            "projected_percent": row["compressed_size"] / target * 100,
            "distance_to_10_percent_archive": int(round(row["compressed_size"] - target * 0.10)),
        }
    usable = [row for row in usable if row["input_bytes"] <= target]
    if len(usable) > 2:
        usable = usable[-2:]
    if len(usable) == 1:
        row = usable[-1]
        alpha = 1.0
        projected_archive = row["compressed_size"] * target / row["input_bytes"]
        basis = "single-point-linear"
    else:
        xs = [math.log(row["input_bytes"]) for row in usable]
        ys = [math.log(row["compressed_size"]) for row in usable]
        x_bar = sum(xs) / len(xs)
        y_bar = sum(ys) / len(ys)
        denom = sum((x - x_bar) ** 2 for x in xs)
        alpha = 1.0 if denom == 0 else sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, ys)) / denom
        intercept = y_bar - alpha * x_bar
        projected_archive = math.exp(intercept + alpha * math.log(target))
        basis = "log-log-regression"
    return {
        "basis": basis,
        "alpha": alpha,
        "projected_archive": int(round(projected_archive)),
        "projected_percent": projected_archive / target * 100,
        "distance_to_10_percent_archive": int(round(projected_archive - target * 0.10)),
    }


def pareto(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    values = list(rows)
    out = []
    for row in values:
        dominated = False
        for other in values:
            if other is row:
                continue
            no_worse = (
                other["compressed_size"] <= row["compressed_size"]
                and (other.get("program_size") or 0) <= (row.get("program_size") or 0)
            )
            better = (
                other["compressed_size"] < row["compressed_size"]
                or (other.get("program_size") or 0) < (row.get("program_size") or 0)
            )
            if no_worse and better:
                dominated = True
                break
        if not dominated:
            out.append(row)
    return sorted(out, key=lambda row: (row["compressed_size"], row.get("program_size") or 0))


def summarize(rows: list[dict[str, Any]], out_dir: pathlib.Path, top: int) -> None:
    by_program: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_program[row["program_id"]].append(row)

    measured_scope_rows = {
        scope: sorted(
            [row for row in rows if row["input_bytes"] == scope],
            key=lambda row: (row["compressed_size"], row.get("program_size") or 0),
        )
        for scope in SCREEN_SCOPES
    }

    forecasts = []
    for program_id, points in by_program.items():
        screen_points = [row for row in points if row["input_bytes"] <= 100_000_000]
        if not screen_points:
            continue
        per_scope = best_by_scope(screen_points)
        best_points = list(per_scope.values())
        row = {
            "program_id": program_id,
            "points": sorted(best_points, key=lambda item: item["input_bytes"]),
            "forecast": {},
        }
        for target in TARGETS:
            projected = fit_forecast(best_points, target)
            if projected:
                row["forecast"][target] = projected
        forecasts.append(row)
    forecasts.sort(key=lambda row: row["forecast"].get(100_000_000, {}).get("projected_archive", 10**30))

    lines = ["# Forecast Frontier", ""]
    lines.append("Measured archive-first leaders:")
    for scope, scoped in measured_scope_rows.items():
        if not scoped:
            continue
        lines.append("")
        lines.append(f"## scope={scope}")
        lines.append("")
        lines.append("| rank | program | archive | program_size | b/B | source |")
        lines.append("|---:|---|---:|---:|---:|---|")
        for rank, row in enumerate(scoped[:top], 1):
            lines.append(
                f"| {rank} | `{row['program_id']}` | {row['compressed_size']} | "
                f"{row.get('program_size') or ''} | {row['compressed_size'] * 8 / scope:.6f} | "
                f"{row['source']} |"
            )
        frontier = pareto(scoped)
        lines.append("")
        lines.append("Pareto by archive/program size:")
        for row in frontier[:top]:
            lines.append(f"- `{row['program_id']}` archive={row['compressed_size']} program={row.get('program_size') or ''}")

    lines.append("")
    lines.append("## Forecasts")
    lines.append("")
    lines.append("| rank | program | measured points | 100MB proj | 100MB % | 100MB gap to 10% | 1GB proj | 1GB % | alpha |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|")
    for rank, row in enumerate(forecasts[:top], 1):
        f100 = row["forecast"].get(100_000_000, {})
        f1g = row["forecast"].get(1_000_000_000, {})
        points = ", ".join(f"{p['input_bytes']}:{p['compressed_size']}" for p in row["points"])
        lines.append(
            f"| {rank} | `{row['program_id']}` | {points} | "
            f"{f100.get('projected_archive', '')} | {f100.get('projected_percent', 0):.3f} | "
            f"{f100.get('distance_to_10_percent_archive', '')} | "
            f"{f1g.get('projected_archive', '')} | {f1g.get('projected_percent', 0):.3f} | "
            f"{f100.get('alpha', 0):.4f} |"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    with (out_dir / "rows.jsonl").open("w") as fh:
        for row in sorted(rows, key=lambda item: (item["input_bytes"], item["compressed_size"], item["program_id"])):
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    with (out_dir / "forecasts.jsonl").open("w") as fh:
        for row in forecasts:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=pathlib.Path, default=OUT_DEFAULT)
    parser.add_argument("--top", type=int, default=25)
    args = parser.parse_args()
    rows = collect_rows()
    summarize(rows, args.out_dir, args.top)
    print(f"[forecast] rows={len(rows)} summary={args.out_dir / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
