#!/usr/bin/env python3
"""Generate an artifact-backed enwiki9 evidence matrix.

This report is deliberately narrower than ALGORITHMS.md. It only uses result
JSON files present in this checkout, and it labels every row by measured scope.
Forecasts, inherited metadata, and prose claims are excluded.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import subprocess
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
RESULTS_DIR = ROOT / "results"
OUT_MD = ROOT / "docs" / "evidence_matrix.md"
FULL_INPUT_BYTES = 1_000_000_000
TARGET_10_95 = 105_000_000  # Legacy schema name retained for compatibility.


@dataclass(frozen=True)
class Row:
    path: pathlib.Path
    program_id: str
    data_size: int
    compressed_size: int
    program_size: int
    score: int
    roundtrip_ok: bool
    determinism_ok: bool | None

    @property
    def archive_bpb(self) -> float:
        if self.data_size <= 0:
            return math.inf
        return 8.0 * self.compressed_size / self.data_size

    @property
    def percent(self) -> float:
        if self.data_size <= 0:
            return math.inf
        return 100.0 * self.score / self.data_size

    @property
    def result_path(self) -> str:
        return str(self.path.relative_to(ROOT))


def as_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def load_row(path: pathlib.Path) -> Row | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    program_id = data.get("program_id") or data.get("candidate_id")
    if not isinstance(program_id, str) or not program_id:
        return None

    data_size = as_int(data, "data_size")
    if not data_size and isinstance(data.get("restored"), dict):
        data_size = as_int(data["restored"], "bytes")
    if not data_size and isinstance(data.get("canonical"), dict):
        data_size = as_int(data["canonical"], "bytes")

    compressed_size = as_int(data, "compressed_size")
    if not compressed_size and isinstance(data.get("archive"), dict):
        compressed_size = as_int(data["archive"], "bytes")

    program_size = as_int(data, "program_size")
    if not program_size and isinstance(data.get("program"), dict):
        program_size = as_int(data["program"], "total_bytes")

    score = as_int(data, "hutter_score") or as_int(data, "counted_score_bytes")
    if score == 0 and (compressed_size or program_size):
        score = compressed_size + program_size

    roundtrip = (
        data.get("roundtrip_ok") is True
        or data.get("overall_pass") is True
        or (isinstance(data.get("gates"), dict) and data["gates"].get("raw_roundtrip_exact") is True)
        or (isinstance(data.get("restored"), dict) and data["restored"].get("byte_identical_to_canonical") is True)
    )
    det = data.get("determinism")
    determinism: bool | None = None
    if isinstance(det, dict) and isinstance(det.get("single_host_byte_equal"), bool):
        determinism = det["single_host_byte_equal"]

    return Row(
        path=path,
        program_id=program_id,
        data_size=data_size,
        compressed_size=compressed_size,
        program_size=program_size,
        score=score,
        roundtrip_ok=roundtrip,
        determinism_ok=determinism,
    )


def canonical_tracked_result_paths(
    results_dir: pathlib.Path,
) -> set[pathlib.Path] | None:
    """Return one Git snapshot for canonical result provenance.

    Temporary and explicitly supplied result directories retain the historical
    fixture behavior.  Canonical generated rankings fail closed if Git cannot
    identify durable result files.
    """

    try:
        canonical = results_dir.resolve() == RESULTS_DIR.resolve()
    except OSError:
        canonical = False
    if not canonical:
        return None
    try:
        result_prefix = RESULTS_DIR.relative_to(REPO_ROOT).as_posix()
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "ls-files",
                "-z",
                "--",
                result_prefix,
            ],
            capture_output=True,
            check=False,
        )
    except OSError:
        return set()
    if proc.returncode != 0:
        return set()
    return {
        (REPO_ROOT / pathlib.Path(os.fsdecode(raw))).resolve()
        for raw in proc.stdout.split(b"\0")
        if raw
    }


def iter_rows(results_dir: pathlib.Path) -> list[Row]:
    tracked_paths = canonical_tracked_result_paths(results_dir)
    rows: list[Row] = []
    for path in sorted(results_dir.glob("*/*.json")):
        if tracked_paths is not None and path.resolve() not in tracked_paths:
            continue
        row = load_row(path)
        if row is not None:
            rows.append(row)
    return rows


def mechanism_hint(program_id: str) -> str:
    pid = program_id.lower()
    if pid.startswith("cmix21_"):
        return "cmix21 memory-shaped context mixer"
    if pid.startswith("fx2_core_tune"):
        return "fx2/cmix tuned wrapper"
    if pid.startswith("fx2_geometry"):
        return "fx2 geometry/order wrapper"
    if pid.startswith("fx2_sidecar") or "sidecar" in pid:
        return "fx2 sidecar or stream split"
    if "lzma" in pid or pid.startswith("xz_") or pid.startswith("baseline_lzma"):
        return "LZMA/LZMA2 baseline or preprocessor"
    if "opcode" in pid:
        return "syntax opcode preprocessor"
    if pid.startswith("typed_anchor"):
        return "custom structural entropy backend"
    if pid.startswith("yellow_tucan"):
        return "custom structural range coder"
    if pid.startswith("baseline_"):
        return "baseline compressor"
    return "custom candidate"


def best_by_scope(rows: list[Row], key: str) -> list[Row]:
    best: dict[int, Row] = {}
    for row in rows:
        if not row.roundtrip_ok:
            continue
        current = best.get(row.data_size)
        if current is None:
            best[row.data_size] = row
            continue
        if key == "score" and row.score < current.score:
            best[row.data_size] = row
        elif key == "archive" and row.compressed_size < current.compressed_size:
            best[row.data_size] = row
    return [best[size] for size in sorted(best)]


def top_rows(rows: list[Row], data_size: int, key: str, limit: int) -> list[Row]:
    scoped = [row for row in rows if row.roundtrip_ok and row.data_size == data_size]
    if key == "score":
        return sorted(scoped, key=lambda row: (row.score, row.compressed_size, row.program_id))[:limit]
    if key == "archive":
        return sorted(scoped, key=lambda row: (row.compressed_size, row.score, row.program_id))[:limit]
    raise ValueError(key)


def fmt_int(value: int) -> str:
    return f"{value:,}"


def fmt_float(value: float) -> str:
    if math.isinf(value):
        return "n/a"
    return f"{value:.9g}"


def table(rows: list[Row]) -> list[str]:
    lines = [
        "| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        det = "true" if row.determinism_ok is True else "false" if row.determinism_ok is False else "not recorded"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.program_id}`",
                    mechanism_hint(row.program_id),
                    fmt_int(row.data_size),
                    fmt_int(row.score),
                    fmt_int(row.compressed_size),
                    fmt_int(row.program_size),
                    fmt_float(row.archive_bpb),
                    det,
                    f"`{row.result_path}`",
                ]
            )
            + " |"
        )
    return lines


def render(rows: list[Row], top_limit: int) -> str:
    exact = [row for row in rows if row.roundtrip_ok]
    full = [row for row in exact if row.data_size == FULL_INPUT_BYTES]
    best_full = min(full, key=lambda row: row.score, default=None)
    hit = best_full is not None and best_full.score <= TARGET_10_95

    lines: list[str] = [
        "# enwiki9 Evidence Matrix",
        "",
        "Generated from result JSON files present in this checkout.",
        "",
        "Claim rule:",
        "",
        "```text",
        "A row is artifact-backed only for its measured scope.",
        "No prefix row proves 10.5%.",
        "No forecast or inherited metadata is included here.",
        "```",
        "",
        "## Proof Boundary",
        "",
        f"- Result JSON files scanned: `{len(rows)}`",
        f"- Roundtrip-passing rows: `{len(exact)}`",
        f"- Verified full `1G` rows in this checkout: `{len(full)}`",
        f"- `10.5%` target reached by this matrix: `{str(hit)}`",
    ]
    if best_full is None:
        lines.append("- Best full `1G` score: `none present`")
    else:
        lines.append(f"- Best full `1G` score: `{fmt_int(best_full.score)}` from `{best_full.program_id}`")

    lines.extend(["", "## Best Exact Score By Scope", ""])
    lines.extend(table(best_by_scope(rows, "score")))
    lines.extend(["", "## Best Exact Archive By Scope", ""])
    lines.extend(table(best_by_scope(rows, "archive")))

    for scope in (10_000_000, 1_000_000, 250_000):
        score_rows = top_rows(rows, scope, "score", top_limit)
        archive_rows = top_rows(rows, scope, "archive", top_limit)
        if score_rows:
            lines.extend(["", f"## Top Score Rows At {fmt_int(scope)} Bytes", ""])
            lines.extend(table(score_rows))
        if archive_rows:
            lines.extend(["", f"## Top Archive Rows At {fmt_int(scope)} Bytes", ""])
            lines.extend(table(archive_rows))

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=pathlib.Path, default=RESULTS_DIR)
    parser.add_argument("--out", type=pathlib.Path, default=OUT_MD)
    parser.add_argument("--top-limit", type=int, default=8)
    parser.add_argument("--check", action="store_true", help="verify output is up to date")
    args = parser.parse_args()

    rows = iter_rows(args.results_dir)
    rendered = render(rows, max(1, args.top_limit))
    if args.check:
        try:
            current = args.out.read_text()
        except OSError:
            print(f"missing {args.out}")
            return 1
        if current != rendered:
            print(f"stale {args.out}")
            return 1
        print(f"up_to_date {args.out}")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
