#!/usr/bin/env python3
"""Generate a compact best-results view from exact result JSONs only."""

from __future__ import annotations

import argparse
import pathlib

import enwiki9_evidence_matrix as evidence


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "docs" / "best_results.md"
SCOPES = [1_000_000_000, 100_000_000, 10_000_000, 1_000_000, 250_000]


def row_table(rows: list[evidence.Row]) -> list[str]:
    lines = [
        "| Program | Mechanism | Score | Archive | Program bytes | b/B | Determinism | Result |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        det = "true" if row.determinism_ok is True else "false" if row.determinism_ok is False else "not recorded"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.program_id}`",
                    evidence.mechanism_hint(row.program_id),
                    evidence.fmt_int(row.score),
                    evidence.fmt_int(row.compressed_size),
                    evidence.fmt_int(row.program_size),
                    evidence.fmt_float(row.archive_bpb),
                    det,
                    f"`{row.result_path}`",
                ]
            )
            + " |"
        )
    return lines


def section(rows: list[evidence.Row], scope: int, top_limit: int) -> list[str]:
    score_rows = evidence.top_rows(rows, scope, "score", top_limit)
    archive_rows = evidence.top_rows(rows, scope, "archive", top_limit)
    lines = ["", f"## Scope `{evidence.fmt_int(scope)}` Bytes", ""]
    if not score_rows and not archive_rows:
        lines.extend(
            [
                "No roundtrip-passing result JSONs are present for this scope in this checkout.",
                "",
            ]
        )
        return lines

    if score_rows:
        lines.extend(["### Best Local Scores", ""])
        lines.extend(row_table(score_rows))
        lines.append("")
    if archive_rows:
        lines.extend(["### Best Archives", ""])
        lines.extend(row_table(archive_rows))
        lines.append("")
    return lines


def render(rows: list[evidence.Row], top_limit: int) -> str:
    exact = [row for row in rows if row.roundtrip_ok]
    lines = [
        "# enwiki9 Best Results",
        "",
        "Generated from exact result JSON files present in this checkout.",
        "",
        "Claim rule:",
        "",
        "```text",
        "Rows here are artifact-backed only for their measured scope.",
        "No prefix row proves 10.80%.",
        "No forecast or metadata-inherited row is included.",
        "```",
        "",
        f"- Result JSON files scanned: `{len(rows)}`",
        f"- Roundtrip-passing rows: `{len(exact)}`",
    ]
    for scope in SCOPES:
        lines.extend(section(rows, scope, top_limit))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=pathlib.Path, default=evidence.RESULTS_DIR)
    parser.add_argument("--out", type=pathlib.Path, default=OUT_MD)
    parser.add_argument("--top-limit", type=int, default=3)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = evidence.iter_rows(args.results_dir)
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
