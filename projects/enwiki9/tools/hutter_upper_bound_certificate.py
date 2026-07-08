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
import re
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DEFAULT = ROOT / "results"
OUT_JSON_DEFAULT = ROOT / "upper_bound_certificate.json"
OUT_MD_DEFAULT = ROOT / "UPPER_BOUND_CERTIFICATE.md"

FULL_INPUT_BYTES = 1_000_000_000
TARGET_10_95 = 109_500_000
CALIBRATED_BASELINE_SCORE = 110_181_114

METADATA_INHERITED_100M = {
    "program_id": "fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1",
    "scope_bytes": 100_000_000,
    "compressed_size": 14_857_781,
    "program_size": 183_008,
    "hutter_score": 15_040_789,
    "evidence": (
        "metadata-inherited from parent 100M geometry package; no result JSON "
        "for this row is present in this checkout"
    ),
    "source": (
        "programs/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/"
        "meta.json:measured:100m_inherited_from_parent"
    ),
}

BEST_FORECAST = {
    "program_id": "fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1",
    "projected_score": 110_181_114,
    "quality": "fx2-calibrated-from-exact-100m",
    "evidence": "forecast only; not a constructive proof",
    "source": "results/forecast_frontier/forecasts.jsonl",
}

ACTIVE_CANDIDATE_ID = (
    "cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_"
    "ppmdguard2_rcm32_bufthirtysecond_minmaps_v1"
)
RUNNING_CANDIDATE_GLOB = "cmix21_text_mmap_paq5_ppmd*fxcmrcm20*/*rss_guard.json"
GUARD_SCOPE_RE = re.compile(r"_(?P<scope>[0-9]+).*rss_guard[.]json$")


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


def next_scope(scope: int) -> int | None:
    if scope == 1_024:
        return 250_000
    if scope == 250_000:
        return 1_000_000
    if scope == 1_000_000:
        return 10_000_000
    if scope == 10_000_000:
        return 100_000_000
    if scope == 100_000_000:
        return FULL_INPUT_BYTES
    return None


def latest_constructive_result(rows: list[Result], program_id: str) -> Result | None:
    matches = [
        row
        for row in rows
        if row.program_id == program_id and row.is_constructive
    ]
    if not matches:
        return None
    return max(matches, key=lambda row: (row.data_size, row.path.stat().st_mtime))


def load_guard(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def latest_gate_guard(program_id: str, scope: int) -> tuple[pathlib.Path, dict[str, Any]] | None:
    result_dir = RESULTS_DEFAULT / program_id
    matches = sorted(result_dir.glob(f"*_{scope}*rss_guard.json"))
    loaded: list[tuple[pathlib.Path, dict[str, Any]]] = []
    for path in matches:
        guard = load_guard(path)
        if guard is not None:
            loaded.append((path, guard))
    if not loaded:
        return None
    return max(
        loaded,
        key=lambda item: (
            1 if "determinism" in item[0].name else 0,
            item[0].stat().st_mtime,
        ),
    )


def guard_scope_from_path(path: pathlib.Path) -> int | None:
    match = GUARD_SCOPE_RE.search(path.name)
    if match is None:
        return None
    try:
        return int(match.group("scope"))
    except ValueError:
        return None


def latest_running_gate() -> tuple[str, int, pathlib.Path, dict[str, Any]] | None:
    loaded: list[tuple[str, int, pathlib.Path, dict[str, Any]]] = []
    for path in sorted(RESULTS_DEFAULT.glob(RUNNING_CANDIDATE_GLOB)):
        guard = load_guard(path)
        scope = guard_scope_from_path(path)
        if guard is None or scope is None:
            continue
        if guard.get("status") != "running":
            continue
        loaded.append((path.parent.name, scope, path, guard))
    if not loaded:
        return None
    return max(
        loaded,
        key=lambda item: (
            1 if "determinism" in item[2].name else 0,
            item[2].stat().st_mtime,
        ),
    )


def active_candidate_context() -> tuple[str, int | None, str]:
    running = latest_running_gate()
    if running is not None:
        candidate, scope, path, _guard = running
        return candidate, scope, f"running RSS guard receipt: {path.relative_to(ROOT)}"
    return ACTIVE_CANDIDATE_ID, None, "fallback active candidate constant"


def active_gate_scope(program_id: str, active_result: Result | None) -> int | None:
    scopes = (FULL_INPUT_BYTES, 100_000_000, 10_000_000, 1_000_000, 250_000, 1_024)
    for scope in scopes:
        loaded = latest_gate_guard(program_id, scope)
        if loaded is not None and loaded[1].get("status") == "running":
            return scope
    if active_result is None:
        return None
    return next_scope(active_result.data_size)


def gate_evidence_text(scope: int) -> str:
    return f"unchanged {scope:,} byte RSS-guarded determinism replay; wait for terminal receipts"


def top_status_record(
    label: str,
    status: str,
    evidence: str,
    row: Result | None = None,
    **extra: Any,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "label": label,
        "status": status,
        "evidence": evidence,
    }
    if row is not None:
        record.update(result_record(row))
        record["scope_bytes"] = row.data_size
    record.update(extra)
    return record


def build_top_status(
    exact_best: list[Result],
    exact_archive_best: list[Result],
    all_rows: list[Result],
) -> list[dict[str, Any]]:
    exact_by_size = {row.data_size: row for row in exact_best}
    archive_by_size = {row.data_size: row for row in exact_archive_best}
    best_10m = exact_by_size.get(10_000_000)
    best_10m_archive = archive_by_size.get(10_000_000)
    best_100m = exact_by_size.get(100_000_000)
    best_1g = exact_by_size.get(FULL_INPUT_BYTES)

    rows: list[dict[str, Any]] = []
    if best_10m is not None:
        rows.append(
            top_status_record(
                "best exact 10M",
                "exact artifact-backed",
                "exact result JSON with roundtrip_ok true",
                best_10m,
            )
        )
    else:
        rows.append(
            top_status_record(
                "best exact 10M",
                "missing",
                "no exact 10M result JSON with roundtrip_ok true found",
                scope_bytes=10_000_000,
            )
        )

    if best_10m_archive is not None:
        rows.append(
            top_status_record(
                "best exact 10M archive",
                "exact artifact-backed",
                "exact result JSON with roundtrip_ok true; archive-slope reference only",
                best_10m_archive,
            )
        )
    else:
        rows.append(
            top_status_record(
                "best exact 10M archive",
                "missing",
                "no exact 10M archive result JSON with roundtrip_ok true found",
                scope_bytes=10_000_000,
            )
        )

    if best_100m is not None:
        rows.append(
            top_status_record(
                "best exact 100M",
                "exact artifact-backed",
                "exact result JSON with roundtrip_ok true",
                best_100m,
            )
        )
    else:
        inherited = {k: v for k, v in METADATA_INHERITED_100M.items() if k != "evidence"}
        rows.append(
            top_status_record(
                "best exact 100M",
                "metadata-inherited",
                METADATA_INHERITED_100M["evidence"],
                **inherited,
            )
        )

    if best_1g is not None:
        rows.append(
            top_status_record(
                "best full 1G",
                "exact artifact-backed",
                "exact full-corpus result JSON with roundtrip_ok true",
                best_1g,
            )
        )
    else:
        rows.append(
            top_status_record(
                "best full 1G",
                "not verified",
                "no verified full-corpus result JSON is present in this checkout",
                scope_bytes=FULL_INPUT_BYTES,
            )
        )

    rows.append(
        top_status_record(
            "best forecast",
            BEST_FORECAST["quality"],
            BEST_FORECAST["evidence"],
            program_id=BEST_FORECAST["program_id"],
            projected_score=BEST_FORECAST["projected_score"],
            source=BEST_FORECAST["source"],
        )
    )
    active_candidate_id, active_scope_override, active_source = active_candidate_context()
    active_result = latest_constructive_result(all_rows, active_candidate_id)
    active_scope = active_scope_override or active_gate_scope(active_candidate_id, active_result)
    if active_result is not None:
        rows.append(
            top_status_record(
                "active candidate",
                f"exact {active_result.data_size:,} byte gate passed",
                (
                    f"exact {active_result.data_size:,} byte replay passed with "
                    "roundtrip and determinism; promotion state is derived from "
                    "the latest guard receipt"
                ),
                active_result,
                active_source=active_source,
            )
        )
    elif active_scope_override is not None:
        rows.append(
            top_status_record(
                "active candidate",
                "running gate",
                (
                    f"active {active_scope_override:,} byte replay is running; "
                    "no constructive result is present for this candidate yet"
                ),
                program_id=active_candidate_id,
                scope_bytes=active_scope_override,
                active_source=active_source,
            )
        )
    else:
        rows.append(
            top_status_record(
                "active candidate",
                "not started",
                "no constructive result is present for the active candidate",
                program_id=active_candidate_id,
                active_source=active_source,
            )
        )
    if active_scope is not None:
        loaded_guard = latest_gate_guard(active_candidate_id, active_scope)
        guard_status = loaded_guard[1].get("status") if loaded_guard else None
        status = "running" if guard_status == "running" else "pending"
        rows.append(
            top_status_record(
                "blocker",
                "open",
                (
                    f"active {active_scope:,} byte deterministic replay has not "
                    "produced terminal driver and RSS receipts yet"
                ),
            )
        )
        rows.append(
            top_status_record(
                "active gate",
                status,
                gate_evidence_text(active_scope),
                program_id=active_candidate_id,
                scope_bytes=active_scope,
                active_source=active_source,
            )
        )
    return rows


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
        "top_status": build_top_status(exact_best, best_archive_by_size(rows), rows),
        "top_status_table": build_top_status(exact_best, best_archive_by_size(rows), rows),
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
    top_status = cert.get("top_status", [])
    if top_status:
        lines.extend(
            [
                "## Top Status",
                "",
                "| Claim | Program | Scope | Score | Evidence | Status |",
                "|---|---|---:|---:|---|---|",
            ]
        )
        for row in top_status:
            program = row.get("program_id") or "n/a"
            scope = row.get("scope_bytes") or row.get("data_size")
            score = row.get("hutter_score", row.get("projected_score"))
            scope_text = f"{scope:,}" if isinstance(scope, int) else "n/a"
            score_text = f"{score:,}" if isinstance(score, int) else "n/a"
            lines.append(
                f"| {row['label']} | `{program}` | {scope_text} | "
                f"{score_text} | {row['evidence']} | {row['status']} |"
            )
        lines.append("")

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
