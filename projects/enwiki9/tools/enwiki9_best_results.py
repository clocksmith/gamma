#!/usr/bin/env python3
"""Generate a compact best-results view from exact result JSONs only."""

from __future__ import annotations

import argparse
import pathlib

try:
    from projects.enwiki9.tools import enwiki9_evidence_matrix as evidence
except ModuleNotFoundError:
    import enwiki9_evidence_matrix as evidence


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "docs" / "best_results.md"
SCOPES = [1_000_000_000, 100_000_000, 10_000_000, 1_000_000, 250_000]


def row_table(rows: list[evidence.Row]) -> list[str]:
    lines = [
        "| Program / arm | Mechanism | Local subtotal | Archive | Program bytes | b/B | Determinism | Result |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        det = "true" if row.determinism_ok is True else "false" if row.determinism_ok is False else "not recorded"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.program_id}{':'+row.arm if row.arm else ''}`",
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


def population_section(rows: list[evidence.Row], scope: int, top_limit: int) -> list[str]:
    score_rows = evidence.top_rows(rows, scope, "score", top_limit)
    archive_rows = evidence.top_rows(rows, scope, "archive", top_limit)
    lines = []
    if not score_rows and not archive_rows:
        lines.extend(
            [
                "No eligible rows for this population.",
                "",
            ]
        )
        return lines

    if score_rows:
        lines.extend(["**Smallest known local subtotals**", ""])
        lines.extend(row_table(score_rows))
        lines.append("")
    if archive_rows:
        lines.extend(["**Smallest archives (package cost reported separately)**", ""])
        lines.extend(row_table(archive_rows))
        lines.append("")
    return lines


def section(rows: list[evidence.Row], scope: int, top_limit: int) -> list[str]:
    scoped = [r for r in rows if r.roundtrip_ok and r.data_size == scope]
    lines = ["", f"## Scope `{evidence.fmt_int(scope)}` Bytes", ""]
    if not scoped:
        return lines + ["No roundtrip-passing result JSONs are present for this scope in this checkout.", ""]
    for digest in sorted({r.data_sha256 for r in scoped}):
        lines += [f"### Population `{digest}`" if digest else "### Unidentified legacy population (not a matched comparison)", ""]
        lines += population_section([r for r in scoped if r.data_sha256 == digest], scope, top_limit)
    return lines


def render(rows: list[evidence.Row], top_limit: int, issues: list[str] | tuple[str, ...] = ()) -> str:
    exact = [row for row in rows if row.roundtrip_ok]
    lines = [
        "# enwiki9 Best Results",
        "",
        "Generated from tracked legacy results and reviewed terminal indexes in this checkout.",
        "",
        "Claim rule:",
        "",
        "```text",
        "Rows here are artifact-backed only for their measured scope.",
        f"No prefix row proves {evidence.TARGET_PERCENT:.7f}%.",
        "No forecast or metadata-inherited row is included.",
        "Unknown package cost stays unknown. Local subtotals are not complete submission scores.",
        "Populations are grouped by raw-input SHA256; compare matched controls in each receipt.",
        "```",
        "",
        f"- Result JSON files scanned: `{len(rows)}`",
        f"- Roundtrip-passing rows: `{len(exact)}`",
        f"- Active target score: `{evidence.TARGET_10_95:,}` bytes "
        f"(`{evidence.TARGET_PERCENT:.7f}%`)",
    ]
    for scope in SCOPES:
        lines.extend(section(rows, scope, top_limit))
    if issues:
        lines += ["", "## Unavailable terminal evidence", "", *[f"- {issue}" for issue in issues]]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=pathlib.Path, default=evidence.RESULTS_DIR)
    parser.add_argument("--out", type=pathlib.Path, default=OUT_MD)
    parser.add_argument("--top-limit", type=int, default=3)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    issues: list[str] = []
    rows = evidence.iter_rows(args.results_dir, issues)
    rendered = render(rows, max(1, args.top_limit), issues)
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
